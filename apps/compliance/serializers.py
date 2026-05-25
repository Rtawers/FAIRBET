from rest_framework import serializers

class SelfExclusionSerializer(serializers.Serializer):
    duration_days = serializers.IntegerField(
        required=False, 
        allow_null=True,
        help_text="Número de días de exclusión. Si es null, es indefinida."
    )

    def validate_duration_days(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError("La duración debe ser un número positivo.")
        return value


class DepositLimitUpdateSerializer(serializers.Serializer):
    amount = serializers.DecimalField(
        max_digits=18, 
        decimal_places=4, 
        required=True,
        help_text="Monto del límite diario."
    )

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("El monto debe ser mayor a cero.")
        return value