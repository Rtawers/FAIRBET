"""
Vista del dashboard de operador.

Expone las métricas de negocio (GGR, exposure, volumen) en un único
endpoint, restringido a usuarios administradores (operadores).
"""
from rest_framework import viewsets  
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

import csv
from datetime import datetime

from django.http import HttpResponse


from apps.dashboard.services import (
    calculate_ggr,
    calculate_exposure,
    calculate_bet_volume,
)


@api_view(["GET"])
@permission_classes([IsAdminUser])
def metrics_view(request):
    """
    GET /api/dashboard/metrics/

    Devuelve las métricas clave del operador. Solo accesible por admin.
    """
    volumen = calculate_bet_volume()

    return Response({
        "ggr": str(calculate_ggr()),
        "exposure": str(calculate_exposure()),
        "volumen": {
            "total_apostado": str(volumen["total_apostado"]),
            "numero_apuestas": volumen["numero_apuestas"],
        },
    })

@api_view(["GET"])
@permission_classes([IsAdminUser])
def report_csv_view(request):
    """
    GET /api/dashboard/report/csv/

    Genera el reporte regulatorio (estilo MINCETUR) en formato CSV
    descargable con las métricas del operador. Solo accesible por admin.
    """
    volumen = calculate_bet_volume()

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = (
        'attachment; filename="reporte_mincetur.csv"'
    )

    writer = csv.writer(response)
    writer.writerow(["Reporte de Operador — FairBet Lab"])
    writer.writerow(["Fecha de generacion", datetime.now().strftime("%Y-%m-%d %H:%M")])
    writer.writerow([])  # fila vacía separadora
    writer.writerow(["Metrica", "Valor"])
    writer.writerow(["GGR (Ganancia Bruta de Juego)", str(calculate_ggr())])
    writer.writerow(["Exposure (Riesgo Vivo)", str(calculate_exposure())])
    writer.writerow(["Total Apostado", str(volumen["total_apostado"])])
    writer.writerow(["Numero de Apuestas Activas", volumen["numero_apuestas"]])

    return response