from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import SelfExclusionSerializer, DepositLimitUpdateSerializer
from .services import apply_self_exclusion, get_daily_limit, set_daily_limit

class SelfExclusionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = SelfExclusionSerializer(data=request.data)
        
        if serializer.is_valid():
            duration_days = serializer.validated_data.get('duration_days')
            apply_self_exclusion(user=request.user, duration_days=duration_days)
            
            return Response(
                {"message": "Autoexclusión aplicada exitosamente"}, 
                status=status.HTTP_201_CREATED
            )
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DepositLimitAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        limit_data = get_daily_limit(request.user)
        return Response(limit_data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = DepositLimitUpdateSerializer(data=request.data)
        
        if serializer.is_valid():
            amount = serializer.validated_data.get('amount')
            set_daily_limit(user=request.user, amount=amount)
            
            return Response(
                {"message": "Límite configurado exitosamente"}, 
                status=status.HTTP_200_OK
            )
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)