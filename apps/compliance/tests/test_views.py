from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from apps.compliance.models import SelfExclusion

User = get_user_model()

class ComplianceViewsTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="api_user", password="password123")
        self.client.force_authenticate(user=self.user)
        self.exclusion_url = '/api/compliance/self-exclusion/'

    def test_1_crear_autoexclusion_via_api(self):
        """El usuario puede aplicar una autoexclusión mediante POST RED → GREEN"""
        data = {'duration_days': 7}
        response = self.client.post(self.exclusion_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        self.assertEqual(response.data['message'], "Autoexclusión aplicada exitosamente")
        
        self.assertTrue(SelfExclusion.objects.filter(user=self.user).exists())

    def test_2_obtener_limite_deposito_via_api(self):
        """El usuario puede ver sus límites de depósito actuales mediante GET RED → GREEN"""
        limit_url = '/api/compliance/deposit-limit/'
        response = self.client.get(limit_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('active_limit', response.data)
        self.assertIn('pending_limit', response.data)

    def test_3_configurar_limite_deposito_via_api(self):
        """El usuario puede configurar un nuevo límite de depósito mediante POST RED → GREEN"""
        limit_url = '/api/compliance/deposit-limit/'
        data = {'amount': '500.0000'}
        response = self.client.post(limit_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], "Límite configurado exitosamente")