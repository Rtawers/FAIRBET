from django.db import models
from django.conf import settings

class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="profile"
    )
    dni = models.CharField(max_length=9, unique=True)
    
    KYC_STATUS_CHOICES = [
        ("PENDING_VERIFICATION", "Pending Verification"),
        ("VERIFIED", "Verified"),
        ("REJECTED", "Rejected"),
    ]
    
    kyc_status = models.CharField(
        max_length=25,
        choices=KYC_STATUS_CHOICES,
        default="PENDING_VERIFICATION" 
    )

    def __str__(self):
        return f"Profile of {self.user.username} - {self.kyc_status}"