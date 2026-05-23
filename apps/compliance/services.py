import datetime
from django.utils import timezone
from .models import SelfExclusion

def apply_self_exclusion(user, duration_days=None):
    """
    Aplica una autoexclusión a un usuario. 
    Si duration_days es provisto, calcula la fecha de fin.
    """
    end_date = None
    if duration_days is not None:
        end_date = timezone.now() + datetime.timedelta(days=duration_days)
        
    exclusion = SelfExclusion.objects.create(
        user=user,
        end_date=end_date
    )
    return exclusion

def is_user_self_excluded(user):
    """
    Verifica si el usuario tiene alguna autoexclusión activa en este momento.
    Ignora el historial de exclusiones que ya expiraron.
    """
    exclusions = SelfExclusion.objects.filter(user=user)
 
    return any(excl.is_active() for excl in exclusions)