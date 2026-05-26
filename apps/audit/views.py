from rest_framework import viewsets

# ViewSets / APIViews de la app.
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from apps.audit.services import verify_chain


@api_view(["GET"])
@permission_classes([IsAdminUser])   # solo admin puede verificar la cadena
def verify_chain_view(request):
    # Ejecuta la verificación y devuelve el resultado
    integra = verify_chain()
    return Response({
        "integra": integra,
        "mensaje": "Cadena íntegra" if integra else "Cadena corrupta - se detectó manipulación",
    })