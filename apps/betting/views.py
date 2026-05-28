from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.throttling import ScopedRateThrottle
from django.core.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from apps.events.models import Selection
from apps.betting.services import place_bet
from apps.betting.serializers import PlaceBetSerializer

from apps.wallet.models import Bet, Transaction
from apps.betting.cashout_service import execute_cashout
from apps.betting.serializers import CashoutSerializer


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def place_bet_view(request):
    place_bet_view.throttle_scope = "bet"  # Usamos el throttle específico para apuestas

    # 1. Header obligatorio
    idempotency_key = request.headers.get("Idempotency-Key")

    if not idempotency_key:
        return Response(
            {"error": "Header Idempotency-Key es requerido."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # 2. Verificar si ya existe una transacción con esa llave
    existing = Transaction.objects.filter(
        idempotency_key=idempotency_key
    ).first()

    if existing:
        bet = Bet.objects.filter(lock_transaction=existing).first()

        return Response(
            {
                "id": bet.id if bet else None,
                "status": bet.status if bet else None,
                "detail": "Operación ya procesada (idempotente)",
            },
            status=status.HTTP_200_OK,
        )

    # 3. Validar entrada
    serializer = PlaceBetSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    selection = Selection.objects.get(
        pk=serializer.validated_data["selection_id"]
    )

    try:
        bet = place_bet(
            request.user,
            selection,
            serializer.validated_data["amount"],
        )

    except PermissionDenied as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_403_FORBIDDEN,
        )

    except (ValidationError, ValueError) as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # 4. Guardar la llave en la transacción de bloqueo
    bet.lock_transaction.idempotency_key = idempotency_key
    bet.lock_transaction.save(update_fields=["idempotency_key"])

    return Response(
        {
            "id": bet.id,
            "status": bet.status,
            "amount": str(bet.amount),
            "odds": str(bet.odds),
        },
        status=status.HTTP_201_CREATED,
    )


# Endpoint cash-out
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def cashout_view(request):
    serializer = CashoutSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    bet = Bet.objects.get(pk=serializer.validated_data["bet_id"])

    # Seguridad: solo el dueño puede cobrarla
    if bet.user != request.user:
        return Response(
            {"error": "No es tu apuesta"},
            status=status.HTTP_403_FORBIDDEN,
        )

    try:
        tx = execute_cashout(
            bet,
            odds_actual=serializer.validated_data["odds_actual"],
            factor_casa=serializer.validated_data["factor_casa"],
        )

    except ValueError as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response(
        {
            "transaction_id": tx.id,
            "bet_status": "CANCELLED",
        },
        status=status.HTTP_200_OK,
    )


# Endpoint listar mis apuestas
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_bets_view(request):

    bets = Bet.objects.filter(
        user=request.user
    ).order_by("-created_at")

    data = [
        {
            "id": b.id,
            "amount": str(b.amount),
            "odds": str(b.odds),
            "status": b.status,
            "potential_payout": str(b.potential_payout),
        }
        for b in bets
    ]

    return Response(data)
# Endpoint liquidar apuesta (solo admin)
@api_view(["POST"])
@permission_classes([IsAdminUser])
def settle_bet_view(request):
    from apps.wallet.models import Bet
    from apps.wallet.services import execute_bet_settlement

    bet_id = request.data.get("bet_id")
    won = request.data.get("won")

    if bet_id is None or won is None:
        return Response(
            {"error": "Se requieren bet_id y won (true/false)"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        bet = Bet.objects.get(pk=bet_id)
        execute_bet_settlement(bet, won=bool(won))
        return Response(
            {"detail": f"Apuesta #{bet_id} liquidada. Resultado: {'ganada' if won else 'perdida'}"},
            status=status.HTTP_200_OK,
        )
    except Bet.DoesNotExist:
        return Response({"error": "Apuesta no encontrada"}, status=status.HTTP_404_NOT_FOUND)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me_view(request):
    return Response({
        'username': request.user.username,
        'email': request.user.email,
        'kyc_status': request.user.profile.kyc_status,
    })