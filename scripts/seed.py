"""
Seed de datos para FairBet Lab.
Crea usuarios, eventos, mercados y saldo inicial para el demo.

Uso:
  docker compose run --rm web python scripts/seed.py
"""
import os
import sys
import django
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone

# Setup Django
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from apps.accounts.models import UserProfile
from apps.wallet.models import Account
from apps.wallet.services import execute_recharge
from apps.events.models import Event, Market, Selection, EventStatus


def crear_usuario(username, password, dni, es_admin=False):
    if User.objects.filter(username=username).exists():
        print(f'  [skip] Usuario {username} ya existe')
        return User.objects.get(username=username)

    user = User.objects.create_user(
        username=username,
        password=password,
        email=f'{username}@fairbet.pe',
    )

    if es_admin:
        user.is_staff = True
        user.is_superuser = True
        user.save()
        print(f'  [ok] Superusuario {username} creado')
        return user

    profile = UserProfile.objects.get(user=user)
    profile.dni = dni
    profile.kyc_status = 'VERIFIED'
    profile.save()

    Account.objects.get_or_create(
        user=user,
        type=Account.AccountType.WALLET,
        defaults={'currency': 'PEN'},
    )

    print(f'  [ok] Usuario {username} creado y verificado')
    return user


def crear_cuentas_sistema():
    Account.objects.get_or_create(
        type=Account.AccountType.CASA,
        user=None,
        defaults={'currency': 'PEN'},
    )
    Account.objects.get_or_create(
        type=Account.AccountType.PENDING,
        user=None,
        defaults={'currency': 'PEN'},
    )
    print('  [ok] Cuentas sistema (CASA, PENDING) listas')


def crear_evento(nombre, local, visitante, horas_desde_ahora=24):
    if Event.objects.filter(name=nombre).exists():
        print(f'  [skip] Evento {nombre} ya existe')
        return Event.objects.get(name=nombre)

    event = Event.objects.create(
        name=nombre,
        sport='football',
        home_team=local,
        away_team=visitante,
        starts_at=timezone.now() + timedelta(hours=horas_desde_ahora),
        status=EventStatus.SCHEDULED,
    )
    print(f'  [ok] Evento {nombre} creado')
    return event


def main():
    print('\n=== FairBet Lab — Seed de datos ===\n')

    print('>> Cuentas del sistema...')
    crear_cuentas_sistema()

    print('\n>> Usuarios...')
    admin = crear_usuario('admin', 'admin123', None, es_admin=True)
    user1 = crear_usuario('carlos', 'carlos123', dni='12345678')
    user2 = crear_usuario('maria', 'maria123', dni='87654321')

    # Asegurar cuentas WALLET para usuarios que ya existían
    for user in [user1, user2]:
        Account.objects.get_or_create(
            user=user,
            type=Account.AccountType.WALLET,
            defaults={'currency': 'PEN'},
        )

    print('\n>> Recargando saldo inicial...')
    for user, monto in [(user1, Decimal('500.0000')), (user2, Decimal('300.0000'))]:
        try:
            execute_recharge(user=user, amount=monto)
            print(f'  [ok] {user.username} recargado con S/ {monto}')
        except Exception as e:
            print(f'  [skip] {user.username}: {e}')

    print('\n>> Eventos deportivos...')
    e1 = crear_evento('Peru vs Brasil', 'Peru', 'Brasil', horas_desde_ahora=24)
    e2 = crear_evento('Argentina vs Chile', 'Argentina', 'Chile', horas_desde_ahora=48)
    e3 = crear_evento('Colombia vs Ecuador', 'Colombia', 'Ecuador', horas_desde_ahora=72)

    print('\n>> Mercados 1X2...')
    for event, odds in [
        (e1, (2.50, 3.20, 2.80)),
        (e2, (1.90, 3.50, 3.80)),
        (e3, (2.10, 3.00, 3.40)),
    ]:
        try:
            if not event.markets.exists():
                Market.create_1x2_market(
                    event=event,
                    odds_home=Decimal(str(odds[0])),
                    odds_draw=Decimal(str(odds[1])),
                    odds_away=Decimal(str(odds[2])),
                )
                print(f'  [ok] Mercado 1X2 para {event.name}')
            else:
                print(f'  [skip] {event.name} ya tiene mercado')
        except Exception as e:
            print(f'  [error] {event.name}: {e}')

    print('\n=== Seed completado ===')
    print('\nCredenciales de demo:')
    print('  Admin:  admin / admin123')
    print('  User 1: carlos / carlos123 (S/ 500)')
    print('  User 2: maria / maria123 (S/ 300)')
    print('\nSwagger UI: http://localhost:8000/api/schema/swagger-ui/')
    print('Admin:      http://localhost:8000/admin/')
    print('Login:      http://localhost:8000/')

    print('\n>> Verificando KYC...')
from apps.accounts.models import UserProfile
for username in ['carlos', 'maria']:
    try:
        user = User.objects.get(username=username)
        profile = UserProfile.objects.get(user=user)
        if profile.kyc_status != 'VERIFIED':
            profile.kyc_status = 'VERIFIED'
            profile.save()
            print(f'  [ok] KYC de {username} actualizado a VERIFIED')
        else:
            print(f'  [skip] {username} ya tiene KYC VERIFIED')
    except Exception as e:
        print(f'  [error] {username}: {e}')
if __name__ == '__main__':
    main()