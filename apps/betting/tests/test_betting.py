from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.core.exceptions import ValidationError
from apps.accounts.models import UserProfile
from apps.betting.services import place_bet
from django.utils import timezone
from datetime import timedelta
from apps.events.models import Event, Market, Selection, EventStatus
from decimal import Decimal
from apps.wallet.models import Account, Bet, LedgerEntry, Transaction
from apps.wallet.services import execute_recharge, execute_bet_settlement, execute_bet_lock
from apps.wallet.services import _get_balance
from hypothesis import given, strategies as st
from hypothesis.extra.django import TestCase as HypothesisTestCase
from apps.betting.combined_service import calculate_combined_odds, is_combined_won
from apps.betting.combined_service import validate_combined_selections
from apps.events.models import SelectionResult
from apps.betting.cashout_service import calculate_cashout




User = get_user_model()


class PlaceBetKycTestCase(TestCase):
    def test_1_usuario_kyc_no_verificado_no_puede_apostar(self):
        # ARRANGE: usuario con KYC PENDING (no verificado)
        user = User.objects.create_user(username="daniel", password="x")
        UserProfile.objects.create(user=user, dni="12345678")
        # por defecto el kyc_status es PENDING_VERIFICATION

        # ACT + ASSERT: apostar debe lanzar PermissionDenied
        with self.assertRaises(PermissionDenied):
            place_bet(user, None, Decimal("10.0000"))  # el segundo argumento no se usa en esta validación

class PlaceBetEventTestCase(TestCase):
    def setUp(self):
        # Usuario verificado (para que pase el KYC y lleguemos a la validación de evento)
        self.user = User.objects.create_user(username="ana", password="x")
        UserProfile.objects.create(user=self.user, dni="87654321", kyc_status="VERIFIED")

    def _crear_selection(self, event_status):
        evento = Event.objects.create(
            name="Final", home_team="A", away_team="B",
            starts_at=timezone.now() + timedelta(days=1),
            status=event_status,
        )
        market = Market.objects.create(event=evento, name="1X2", market_type="1x2")
        return Selection.objects.create(
            market=market, name="Local", outcome="LOCAL", odds="2.50"
        )

    def test_2_apuesta_sobre_evento_no_scheduled_es_rechazada(self):
        # ARRANGE: selección sobre un evento LIVE (ya empezó, no SCHEDULED)
        selection = self._crear_selection(EventStatus.LIVE)

        # ACT + ASSERT: apostar debe lanzar ValidationError
        with self.assertRaises(ValidationError):
            place_bet(self.user, selection, Decimal("10.0000"))
    
class PlaceBetCreatesBetTestCase(TestCase):
    def setUp(self):
        # Usuario verificado
        self.user = User.objects.create_user(username="luis", password="x")
        UserProfile.objects.create(user=self.user, dni="11111111", kyc_status="VERIFIED")

        # Cuentas del sistema (CASA y PENDING) — necesarias para la partida doble
        Account.objects.create(type=Account.AccountType.CASA)
        Account.objects.create(type=Account.AccountType.PENDING)
        # Wallet del usuario
        Account.objects.create(user=self.user, type=Account.AccountType.WALLET)

        # Recargar saldo para que tenga fondos suficientes
        execute_recharge(self.user, Decimal("100.0000"))

        # Selección sobre evento SCHEDULED
        evento = Event.objects.create(
            name="Final", home_team="A", away_team="B",
            starts_at=timezone.now() + timedelta(days=1),
            status=EventStatus.SCHEDULED,
        )
        market = Market.objects.create(event=evento, name="1X2", market_type="1x2")
        self.selection = Selection.objects.create(
            market=market, name="Local", outcome="LOCAL", odds="2.50"
        )

    def test_3_apuesta_simple_crea_bet_en_estado_accepted(self):
        # ACT: colocar una apuesta de 20 fichas
        bet = place_bet(self.user, self.selection, Decimal("20.0000"))

        # ASSERT: se creó una Bet en estado ACCEPTED
        self.assertEqual(bet.status, Bet.BetStatus.ACCEPTED)
        self.assertEqual(bet.amount, Decimal("20.0000"))
        self.assertEqual(bet.odds, Decimal("2.50"))
    
class CombinedOddsTestCase(HypothesisTestCase):
    @given(
        st.lists(
            st.decimals(min_value=Decimal("1.01"), max_value=Decimal("100.00"), places=2),
            min_size=2, max_size=5,
        )
    )
    def test_4_cuota_combinada_es_producto_de_individuales(self, odds_list):
        # ACT: calcular la cuota combinada
        result = calculate_combined_odds(odds_list)

        # ASSERT: debe ser igual al producto de todas las cuotas
        expected = Decimal("1")
        for odd in odds_list:
            expected *= odd

        self.assertEqual(result, expected)

class CombinedResultTestCase(TestCase):
    def test_5_si_una_seleccion_pierde_toda_la_combinada_pierde(self):
        # ARRANGE: tres resultados, una de ellas perdió
        resultados = [
            SelectionResult.WON,
            SelectionResult.LOST,   # <- esta rompe la combinada
            SelectionResult.WON,
        ]

        # ACT + ASSERT: la combinada NO ganó
        self.assertFalse(is_combined_won(resultados))

    def test_5b_combinada_gana_solo_si_todas_ganan(self):
        # Caso complementario: todas ganaron -> la combinada gana
        resultados = [SelectionResult.WON, SelectionResult.WON, SelectionResult.WON]
        self.assertTrue(is_combined_won(resultados))

class CombinedValidationTestCase(TestCase):
    def _selection(self, event, outcome):
        market = Market.objects.create(event=event, name="1X2", market_type=f"1x2-{outcome}")
        return Selection.objects.create(market=market, name=outcome, outcome=outcome, odds="2.0")

    def test_6_no_se_puede_combinar_selecciones_del_mismo_evento(self):
        evento = Event.objects.create(
            name="A vs B", home_team="A", away_team="B",
            starts_at=timezone.now() + timedelta(days=1), status=EventStatus.SCHEDULED,
        )
        sel_local = self._selection(evento, "LOCAL")
        sel_away = self._selection(evento, "AWAY")  # mismo evento -> conflicto

        with self.assertRaises(ValidationError):
            validate_combined_selections([sel_local, sel_away])
        
class CombinedSettlementTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="combo", password="x")
        UserProfile.objects.create(user=self.user, dni="22222222", kyc_status="VERIFIED")
        Account.objects.create(type=Account.AccountType.CASA)
        Account.objects.create(type=Account.AccountType.PENDING)
        self.wallet = Account.objects.create(user=self.user, type=Account.AccountType.WALLET)
        execute_recharge(self.user, Decimal("100.0000"))

    def test_7_liquidacion_combinada_ganadora_paga_correctamente(self):
        # ARRANGE: combinada de cuotas 2.0 y 3.0 -> cuota combinada = 6.0
        odds_individuales = [Decimal("2.0"), Decimal("3.0")]
        cuota_combinada = calculate_combined_odds(odds_individuales)  # 6.0
        stake = Decimal("10.0000")

        # Bloquear fondos y crear la Bet combinada con la cuota combinada como odds
        lock_tx = execute_bet_lock(self.user, stake)
        bet = Bet.objects.create(
            user=self.user, amount=stake, odds=cuota_combinada,
            lock_transaction=lock_tx,
        )

        # ACT: liquidar como ganadora
        execute_bet_settlement(bet, won=True)

        # ASSERT: la Bet quedó WON y el payout fue stake * cuota_combinada = 60
        bet.refresh_from_db()
        self.assertEqual(bet.status, Bet.BetStatus.WON)
        # saldo final = 100 - 10 (bloqueo) + 60 (payout) = 150
        self.assertEqual(_get_balance(self.wallet), Decimal("150.0000"))

class CashoutFormulaTestCase(TestCase):
    def test_8_formula_cashout(self):
        # stake=10, odds_original=2.0, odds_actual=1.5, factor_casa=0.95
        # cashout = 10 * 2.0 / 1.5 * 0.95 = 12.6666... -> 12.6667 (4 decimales)
        result = calculate_cashout(
            stake=Decimal("10.0000"),
            odds_original=Decimal("2.0"),
            odds_actual=Decimal("1.5"),
            factor_casa=Decimal("0.95"),
        )
        self.assertEqual(result, Decimal("12.6667"))