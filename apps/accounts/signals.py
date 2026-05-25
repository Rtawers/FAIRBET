from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from apps.accounts.models import UserProfile

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):

    if created:

        UserProfile.objects.get_or_create(
            user=instance,
            defaults={
                "dni": f"PENDING-{instance.id}",
                "kyc_status": "PENDING_VERIFICATION",
            }
<<<<<<< HEAD
        )
=======
        ) 

        
>>>>>>> feature/app-MaicolRafael
