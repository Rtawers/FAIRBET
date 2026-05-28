from decimal import Decimal
from django.db.models import Q, Sum
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.wallet.models import Account, LedgerEntry, Transaction
from apps.wallet.serializers import RechargeSerializer, WithdrawSerializer
from apps.wallet.services import execute_recharge, get_monto_bono


def _get_user_balance(user) -> Decimal:
    """Calcula el saldo derivado del usuario."""
    try:
        wallet = Account.objects.get(
            user=user, type=Account.AccountType.WALLET
        )
    except Account.DoesNotExist:
        return Decimal('0.0000')

    result = LedgerEntry.objects.filter(account=wallet).aggregate(
        credits=Sum('amount', filter=Q(direction=LedgerEntry.Direction.CREDIT)),
        debits=Sum('amount', filter=Q(direction=LedgerEntry.Direction.DEBIT)),
    )
    credits = result['credits'] or Decimal('0.0000')
    debits = result['debits'] or Decimal('0.0000')
    return credits - debits


def _get_or_check_idempotency(idempotency_key):
    """
    Verifica si ya existe una transaccion con este idempotency_key.
    Retorna (transaction, is_new).
    """
    try:
        tx = Transaction.objects.get(idempotency_key=idempotency_key)
        return tx, False
    except Transaction.DoesNotExist:
        return None, True


class BalanceView(APIView):
    """GET /api/wallet/balance/ — retorna el saldo actual del usuario."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        balance = _get_user_balance(request.user)
        return Response({'balance': balance}, status=status.HTTP_200_OK)


class RechargeView(APIView):
    """POST /api/wallet/recharge/ — recarga fichas al wallet."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        idempotency_key = request.headers.get('Idempotency-Key')
        if not idempotency_key:
            return Response(
                {'error': 'Header Idempotency-Key es requerido.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        existing_tx, is_new = _get_or_check_idempotency(idempotency_key)
        if not is_new:
            balance = _get_user_balance(request.user)
            return Response(
                {'transaction_id': existing_tx.id, 'balance': balance},
                status=status.HTTP_200_OK,
            )

        serializer = RechargeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        amount = serializer.validated_data['amount']

        try:
            tx = execute_recharge(user=request.user, amount=amount)
            tx.idempotency_key = idempotency_key
            tx.save(update_fields=['idempotency_key'])
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        balance = _get_user_balance(request.user)
        return Response(
            {'transaction_id': tx.id, 'balance': balance},
            status=status.HTTP_201_CREATED,
        )


class WithdrawView(APIView):
    """POST /api/wallet/withdraw/ — retiro simulado de fichas."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        idempotency_key = request.headers.get('Idempotency-Key')
        if not idempotency_key:
            return Response(
                {'error': 'Header Idempotency-Key es requerido.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        existing_tx, is_new = _get_or_check_idempotency(idempotency_key)
        if not is_new:
            balance = _get_user_balance(request.user)
            return Response(
                {'transaction_id': existing_tx.id, 'balance': balance},
                status=status.HTTP_200_OK,
            )

        serializer = WithdrawSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        amount = serializer.validated_data['amount']
        balance = _get_user_balance(request.user)

        if balance < amount:
            return Response(
                {'error': f'Saldo insuficiente. Disponible: {balance}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Fix Bug 2: rollover solo bloquea si toca saldo BONUS
        monto_bono = get_monto_bono(request.user)
        if monto_bono > 0 and amount > (balance - monto_bono):
            from apps.betting.rollover_service import rollover_cumplido
            if not rollover_cumplido(request.user):
                return Response(
                    {'error': 'Debe cumplir el rollover de 5x el bono antes de retirar saldo de bono.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Fix Bug 1: usar Transaction.Kind.WITHDRAW en lugar de RECHARGE
        from django.db import transaction as db_transaction
        with db_transaction.atomic():
            wallet = Account.objects.select_for_update().get(
                user=request.user,
                type=Account.AccountType.WALLET,
            )
            casa = Account.objects.get(type=Account.AccountType.CASA)
            tx = Transaction.objects.create(
                kind=Transaction.Kind.WITHDRAW,
                idempotency_key=idempotency_key,
            )
            LedgerEntry.objects.create(
                transaction=tx, account=wallet,
                amount=amount, direction=LedgerEntry.Direction.DEBIT,
            )
            LedgerEntry.objects.create(
                transaction=tx, account=casa,
                amount=amount, direction=LedgerEntry.Direction.CREDIT,
            )

        new_balance = _get_user_balance(request.user)
        return Response(
            {'transaction_id': tx.id, 'balance': new_balance},
            status=status.HTTP_201_CREATED,
        )
class TransactionHistoryView(APIView):
    """GET /api/wallet/transactions/ — historial de transacciones del usuario."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            wallet = Account.objects.get(
                user=request.user,
                type=Account.AccountType.WALLET
            )
        except Account.DoesNotExist:
            return Response([], status=status.HTTP_200_OK)

        entries = LedgerEntry.objects.filter(
            account=wallet
        ).select_related('transaction').order_by('-transaction__created_at')[:50]

        data = []
        seen_transactions = set()
        for entry in entries:
            tx = entry.transaction
            if tx.id in seen_transactions:
                continue
            seen_transactions.add(tx.id)

            tipo = {
                'RECHARGE': 'Recarga',
                'BET_LOCK': 'Apuesta',
                'SETTLEMENT': 'Liquidacion',
                'WITHDRAW': 'Retiro',
            }.get(tx.kind, tx.kind)

            data.append({
                'id': tx.id,
                'tipo': tipo,
                'kind': tx.kind,
                'amount': str(entry.amount),
                'direction': entry.direction,
                'created_at': tx.created_at.isoformat(),
            })

        return Response(data, status=status.HTTP_200_OK)