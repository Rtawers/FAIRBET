from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
import inspect

from apps.accounts.models import UserProfile, SuspiciousActivity

User = get_user_model()

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        # 1. Creamos o recuperamos de forma segura el perfil básico (Lógica Bloque 2)
        profile, profile_created = UserProfile.objects.get_or_create(
            user=instance,
            defaults={
                "dni": f"PENDING-{instance.id}",
                "kyc_status": "PENDING_VERIFICATION",
            }
        )
        
        # 2. LÓGICA DEL BLOQUE 3 (Anti-fraude): Buscar la IP en el contexto de la request
        ip_address = None
        
        # Buscamos de manera dinámica la request en la pila de ejecución (compatible con DRF y los tests de API)
        for frame_record in inspect.stack():
            frame = frame_record.frame
            if 'request' in frame.f_locals:
                request = frame.f_locals['request']
                if hasattr(request, 'META'):
                    ip_address = request.META.get('REMOTE_ADDR')
                    break

        if ip_address:
            # Guardamos la IP en el perfil del usuario actual
            profile.registration_ip = ip_address
            profile.save()
            
            # Contamos cuántos usuarios se han registrado con esta misma IP
            cuentas_con_misma_ip = UserProfile.objects.filter(registration_ip=ip_address).count()
            
            # Si supera el umbral definido por Pamela (más de 3 cuentas)
            if cuentas_con_misma_ip > 3:
                # Cambiamos el estado del KYC del perfil a BLOCKED
                profile.kyc_status = "BLOCKED"
                profile.save()
                
                # Creamos el registro en el modelo SuspiciousActivity para auditoría
                SuspiciousActivity.objects.create(
                    user=instance,
                    trigger_type="MULTI_ACCOUNT_IP",
                    description=f"Alerta Anti-Fraude: Se superó el umbral de registros. Cuenta N° {cuentas_con_misma_ip} desde la IP {ip_address}.",
                    ip_address=ip_address
                )