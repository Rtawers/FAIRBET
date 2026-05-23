import datetime
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.compliance.services import (
    get_daily_limit, 
    set_daily_limit, 
    promote_pending_limits
)

User = get_user_model()

class DepositLimitTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="limit_user")
        set_daily_limit(self.user, Decimal('1000.0000'))

    def test_7_8_9_gestion_limites_deposito(self):
        """7, 8 y 9: Bajar es instantáneo, subir es pending, se promueve a las 24h RED → GREEN"""

        set_daily_limit(self.user, Decimal('500.0000'))
        limit_data = get_daily_limit(self.user)
        self.assertEqual(limit_data['active_limit'], Decimal('500.0000'))
        self.assertIsNone(limit_data['pending_limit'])

        set_daily_limit(self.user, Decimal('2000.0000'))
        limit_data = get_daily_limit(self.user)
        self.assertEqual(limit_data['active_limit'], Decimal('500.0000')) 
        # Los 2000 se quedan en cola de espera
        self.assertEqual(limit_data['pending_limit'], Decimal('2000.0000'))
        
        limit_obj = self.user.depositlimit 
        limit_obj.pending_since = timezone.now() - datetime.timedelta(hours=25)
        limit_obj.save()


        promote_pending_limits() 

        limit_data = get_daily_limit(self.user)
        self.assertEqual(limit_data['active_limit'], Decimal('2000.0000'))
        self.assertIsNone(limit_data['pending_limit'])