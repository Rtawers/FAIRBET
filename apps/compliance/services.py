import datetime
from decimal import Decimal
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from .models import SelfExclusion, DepositLimit

def apply_self_exclusion(user, duration_days=None):
    end_date = None
    if duration_days is not None:
        end_date = timezone.now() + datetime.timedelta(days=duration_days)
        
    exclusion = SelfExclusion.objects.create(
        user=user,
        end_date=end_date
    )
    return exclusion

def is_user_self_excluded(user):
    exclusions = SelfExclusion.objects.filter(user=user)
    return any(excl.is_active() for excl in exclusions)

def execute_bet_lock(user):
    if is_user_self_excluded(user):
        raise PermissionDenied("Usuario autoexcluido no puede operar")
    return True


def get_daily_limit(user):
    try:
        limit_obj = user.depositlimit
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