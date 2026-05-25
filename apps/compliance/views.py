from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import SelfExclusionSerializer
from .services import apply_self_exclusion

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