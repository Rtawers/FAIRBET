from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
import inspect

from apps.accounts.models import UserProfile, SuspiciousActivity

User = get_user_model()

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        profile, profile_created = UserProfile.objects.get_or_create(
            user=instance,
            defaults={
                "dni": f"PENDING-{instance.id}",
                "kyc_status": "PENDING_VERIFICATION",
            }
        )
        
        ip_address = None
        
        for frame_record in inspect.stack():
            frame = frame_record.frame
            if 'request' in frame.f_locals:
                request = frame.f_locals['request']
                if hasattr(request, 'META'):
                    ip_address = request.META.get('REMOTE_ADDR')
                    break

        if ip_address:
            profile.registration_ip = ip_address
            profile.save()
            
            cuentas_con_misma_ip = UserProfile.objects.filter(registration_ip=ip_address).count()
            
            if cuentas_con_misma_ip > 3:
                profile.kyc_status = "BLOCKED"
                profile.save()
                
                SuspiciousActivity.objects.create(
                    user=instance,
                    trigger_type="MULTI_ACCOUNT_IP",
                    description=f"Alerta Anti-Fraude: Se superó el umbral de registros. Cuenta N° {cuentas_con_misma_ip} desde la IP {ip_address}.",
                    ip_address=ip_address
                )