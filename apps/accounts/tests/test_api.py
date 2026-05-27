import datetime
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model

User = get_user_model()

class AccountsAPITestCase(APITestCase):

    def setUp(self):
        self.register_url = reverse('accounts-api:register')
        self.kyc_url = reverse('accounts-api:kyc')
        
        self.valid_register_data = {
            "username": "maicol_rafael",
            "email": "maicol@fairbet.lab",
            "password": "SecurePassword123*",
            "birth_date": "2000-05-23"
        }

    def test_red_registro_usuario_exitoso(self):
        """
        TEST RED 1: Validar que el endpoint de registro cree un usuario 
        e inicie su UserProfile en estado PENDING_VERIFICATION.
        """
        response = self.client.post(self.register_url, self.valid_register_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="maicol_rafael").exists())
        self.assertEqual(response.data["kyc_status"], "PENDING_VERIFICATION")

    def test_red_verificacion_kyc_modulo11_exitoso(self):
        """
        TEST RED 2: Validar que un usuario autenticado envíe su DNI 
        y pase de forma atómica a estado VERIFIED usando el algoritmo Módulo 11.
        """
        user = User.objects.create_user(
            username="tester_kyc", 
            email="tester@fairbet.lab", 
            password="Password123*"
        )
        profile = user.profile
        profile.birth_date = datetime.date(2000, 1, 1) # Mayor de edad
        profile.save()

        self.client.force_authenticate(user=user)

        kyc_payload = {
            "dni_number": "43567182",
            "verification_digit": "9"
        }

        response = self.client.post(self.kyc_url, kyc_payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["kyc_status"], "VERIFIED")
        
    def test_red_deteccion_multi_cuenta_por_ip_bloquea_cuarto_usuario(self):
        """
        TEST RED 3: Validar que si se registran más de 3 usuarios desde la misma IP,
        el cuarto usuario sea bloqueado automáticamente (BLOCKED) y se registre
        un evento en SuspiciousActivity.
        """
        ip_sospechosa = "192.168.1.50"
        
        for i in range(1, 4):
            data = {
                "username": f"usuario_ip_{i}",
                "email": f"user_ip_{i}@fairbet.lab",
                "password": "SecurePassword123*",
                "birth_date": "2000-05-23"
            }
            response = self.client.post(
                self.register_url, 
                data, 
                format='json', 
                REMOTE_ADDR=ip_sospechosa
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(response.data["kyc_status"], "PENDING_VERIFICATION")

        cuarto_usuario_data = {
            "username": "usuario_fraudulento_4",
            "email": "fraude4@fairbet.lab",
            "password": "SecurePassword123*",
            "birth_date": "2000-05-23"
        }
        
        response = self.client.post(
            self.register_url, 
            cuarto_usuario_data, 
            format='json', 
            REMOTE_ADDR=ip_sospechosa
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["kyc_status"], "BLOCKED")
        
        from apps.accounts.models import SuspiciousActivity
        
        alertas_ip = SuspiciousActivity.objects.filter(
            ip_address=ip_sospechosa, 
            trigger_type="MULTI_ACCOUNT_IP"
        )
        
        self.assertTrue(alertas_ip.exists())
        self.assertEqual(alertas_ip.count(), 1)
        self.assertEqual(alertas_ip.first().user.username, "usuario_fraudulento_4")