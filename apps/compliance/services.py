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