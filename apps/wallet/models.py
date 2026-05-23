# apps/wallet/models.py
"""
Modelos del sistema contable de FairBet Lab.

Arquitectura de partida doble:
  - Account: una cuenta contable (WALLET, CASA, PENDING, BONUS).
  - Transaction: cabecera de un movimiento (RECHARGE, BET_LOCK, SETTLEMENT).
  - LedgerEntry: cada asiento contable (DEBIT o CREDIT).

Invariantes que SIEMPRE se cumplen:
  - Por cada Transaction, la suma firmada de sus LedgerEntries es cero.
  - El saldo de un Account se calcula SUM(credits) - SUM(debits).
  - Nunca se almacena el saldo en una columna — siempre es derivado.
"""
from django.contrib.auth.models import User
from django.db import models

from config.fields import MoneyField


class Account(models.Model):
    """
    Una cuenta del ledger de partida doble.

    Tipos:
      WALLET  — billetera del usuario (saldo disponible para apostar).
      CASA    — cuenta central de la plataforma.
      PENDING — bolsa transitoria de fondos bloqueados por apuestas activas.
      BONUS   — billetera de bonos (Nivel 2, implementación futura).
    """

    class AccountType(models.TextChoices):
        WALLET = 'WALLET', 'Billetera de usuario'
        CASA = 'CASA', 'Cuenta central de la casa'
        PENDING = 'PENDING', 'Apuestas pendientes'
        BONUS = 'BONUS', 'Billetera de bonos'

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='accounts',
    )
    type = models.CharField(
        max_length=10,
        choices=AccountType.choices,
    )
    currency = models.CharField(max_length=3, default='PEN')

    class Meta:
        verbose_name = 'Cuenta'
        verbose_name_plural = 'Cuentas'

    def __str__(self):
        owner = self.user.username if self.user else 'sistema'
        return f'Account [{self.type}] — {owner}'


class Transaction(models.Model):
    """
    Cabecera de un movimiento contable.

    Tipos:
      RECHARGE   — recarga de fichas virtuales.
      BET_LOCK   — bloqueo de fondos al confirmar una apuesta.
      SETTLEMENT — liquidación de apuesta (ganada o perdida).
    """

    class Kind(models.TextChoices):
        RECHARGE = 'RECHARGE', 'Recarga de fichas'
        BET_LOCK = 'BET_LOCK', 'Bloqueo por apuesta'
        SETTLEMENT = 'SETTLEMENT', 'Liquidación de apuesta'

    kind = models.CharField(max_length=15, choices=Kind.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    idempotency_key = models.CharField(
        max_length=64,
        unique=True,
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = 'Transacción'
        verbose_name_plural = 'Transacciones'

    def __str__(self):
        return f'Tx {self.pk} [{self.kind}]'


class LedgerEntry(models.Model):
    """
    Un asiento contable individual.

    Cada Transaction tiene minimo 2 LedgerEntries que suman cero.
    Nunca se crea una LedgerEntry suelta — siempre en pares balanceados.
    """

    class Direction(models.TextChoices):
        DEBIT = 'DEBIT', 'Débito (-)'
        CREDIT = 'CREDIT', 'Crédito (+)'

    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.CASCADE,
        related_name='entries',
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='entries',
    )
    amount = MoneyField()
    direction = models.CharField(max_length=6, choices=Direction.choices)

    class Meta:
        verbose_name = 'Asiento contable'
        verbose_name_plural = 'Asientos contables'

    def __str__(self):
        return f'Entry {self.pk} | {self.direction} {self.amount} → {self.account}'