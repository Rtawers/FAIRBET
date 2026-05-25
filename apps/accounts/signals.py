from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from apps.accounts.models import UserProfile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        # Usamos get_or_create para que si el test o endpoint intenta gestionar el perfil 
        # antes o en paralelo, no se genere una colisión en la llave primaria de user_id
        UserProfile.objects.get_or_create(
            user=instance,
            defaults={
                'dni': None,  # Permite que se cree vacío sin violar restricciones unique
                'kyc_status': 'PENDING_VERIFICATION'
            }
        )