from rest_framework import viewsets  
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import PermissionDenied, ValidationError

from apps.events.models import Selection
from apps.betting.services import place_bet
from apps.betting.serializers import PlaceBetSerializer

from apps.wallet.models import Bet
from apps.betting.cashout_service import execute_cashout
from apps.betting.serializers import CashoutSerializer

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def place_bet_view(request):
    serializer = PlaceBetSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)   # valida; si falla, devuelve 400 solo

    selection = Selection.objects.get(pk=serializer.validated_data["selection_id"])
    try:
        bet = place_bet(request.user, selection, serializer.validated_data["amount"])
    except PermissionDenied as e:
        return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)
    except (ValidationError, ValueError) as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        "id": bet.id,
        "status": bet.status,
        "amount": str(bet.amount),
        "odds": str(bet.odds),
    }, status=status.HTTP_201_CREATED)

# este es el Endpoint cash-out, que permite a los usuarios cobrar una apuesta antes de que se resuelva el evento :)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def cashout_view(request):
    serializer = CashoutSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    bet = Bet.objects.get(pk=serializer.validated_data["bet_id"])
    # Seguridad: solo el dueño de la apuesta puede cobrarla
    if bet.user != request.user:
        return Response({"error": "No es tu apuesta"}, status=status.HTTP_403_FORBIDDEN)

    try:
        tx = execute_cashout(
            bet,
            odds_actual=serializer.validated_data["odds_actual"],
            factor_casa=serializer.validated_data["factor_casa"],
        )
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    return Response({"transaction_id": tx.id, "bet_status": "CANCELLED"}, status=status.HTTP_200_OK)

# este es el Endpoint listar mis apuestas, que devuelve todas las apuestas del usuario autenticado, ordenadas por fecha de creación (más recientes primero)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_bets_view(request):
    bets = Bet.objects.filter(user=request.user).order_by("-created_at")
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