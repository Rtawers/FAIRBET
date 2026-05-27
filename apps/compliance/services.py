import datetime
from decimal import Decimal
from django.utils import timezone
from django.core.exceptions import PermissionDenied, ValidationError
from .models import SelfExclusion, DepositLimit
from datetime import timedelta
from apps.compliance.models import SuspiciousActivity
from apps.wallet.models import Transaction


def apply_self_exclusion(user, duration_days=None):
    end_date = None
    if duration_days is not None:
        end_date = timezone.now() + datetime.timedelta(days=duration_days)
    return SelfExclusion.objects.create(user=user, end_date=end_date)

def is_user_self_excluded(user):
    exclusions = SelfExclusion.objects.filter(user=user)
    return any(excl.is_active() for excl in exclusions)

def execute_bet_lock(user):
    if is_user_self_excluded(user):
        raise PermissionDenied("Usuario autoexcluido no puede operar")
    return True


def get_daily_limit(user):
    try:
        limit_obj = DepositLimit.objects.get(user=user)
        return {
            'active_limit': limit_obj.active_limit,
            'pending_limit': limit_obj.pending_limit
        }
    except DepositLimit.DoesNotExist:
        return {
            'active_limit': None,
            'pending_limit': None
        }

def set_daily_limit(user, amount):
    limit_obj, created = DepositLimit.objects.get_or_create(
        user=user,
        defaults={'active_limit': amount}
    )
    if created:
        return limit_obj

    if amount < limit_obj.active_limit:
        limit_obj.active_limit = amount
        limit_obj.pending_limit = None
        limit_obj.pending_since = None
    else:
        limit_obj.pending_limit = amount
        limit_obj.pending_since = timezone.now()
    
    limit_obj.save()
    return limit_obj

def promote_pending_limits():
    cutoff = timezone.now() - datetime.timedelta(hours=24)
    pending_limits = DepositLimit.objects.filter(
        pending_limit__isnull=False,
        pending_since__lte=cutoff
    )
    for limit in pending_limits:
        limit.active_limit = limit.pending_limit
        limit.pending_limit = None
        limit.pending_since = None
        limit.save()


def validate_deposit(user, amount):
    limit_data = get_daily_limit(user)
    active_limit = limit_data.get('active_limit')
    if active_limit is not None and amount > active_limit:
        raise ValidationError("El monto de recarga excede el límite diario configurado")  
    return True

#Antifraud
def check_transaction_velocity(user):
    """
    Revisa si el usuario ha excedido el límite de 5 transacciones en la última hora.
    Si lo excede, registra una alerta de actividad sospechosa.
    """
    time_threshold = timezone.now() - timedelta(minutes=60)

    recent_transactions_count = Transaction.objects.filter(
        entries__account__user=user,
        created_at__gte=time_threshold
    ).distinct().count()

    if recent_transactions_count > 5:
        SuspiciousActivity.objects.create(
            user=user,
            activity_type='VELOCITY',
            description=f"Alerta de Velocidad: El usuario realizó {recent_transactions_count} transacciones en los últimos 60 minutos. Umbral: 5."
        )