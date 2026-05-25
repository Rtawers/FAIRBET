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