from rest_framework import serializers  

class PlaceBetSerializer(serializers.Serializer):
    selection_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=18, decimal_places=4)

class CashoutSerializer(serializers.Serializer):
    bet_id = serializers.IntegerField()
    odds_actual = serializers.DecimalField(max_digits=6, decimal_places=2)
    factor_casa = serializers.DecimalField(max_digits=5, decimal_places=4)