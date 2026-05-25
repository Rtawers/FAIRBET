# apps/wallet/serializers.py
from decimal import Decimal
from rest_framework import serializers


class RechargeSerializer(serializers.Serializer):
    amount = serializers.DecimalField(
        max_digits=18,
        decimal_places=4,
        min_value=Decimal('0.0001'),
    )


class WithdrawSerializer(serializers.Serializer):
    amount = serializers.DecimalField(
        max_digits=18,
        decimal_places=4,
        min_value=Decimal('0.0001'),
    )


class BalanceSerializer(serializers.Serializer):
    balance = serializers.DecimalField(
        max_digits=18,
        decimal_places=4,
        read_only=True,
    )


class TransactionResponseSerializer(serializers.Serializer):
    transaction_id = serializers.IntegerField(read_only=True)
    balance = serializers.DecimalField(
        max_digits=18,
        decimal_places=4,
        read_only=True,
    )