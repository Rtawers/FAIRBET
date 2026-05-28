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


def crear_mercados(event, odds, jugadores_locales, jugadores_visitantes):
    tipos_existentes = list(event.markets.values_list('market_type', flat=True))

    if '1x2' not in tipos_existentes:
        Market.create_1x2_market(
            event=event,
            odds_home=Decimal(str(odds[0])),
            odds_draw=Decimal(str(odds[1])),
            odds_away=Decimal(str(odds[2])),
        )
        print(f'  [ok] 1X2 para {event.name}')
    else:
        print(f'  [skip] 1X2 {event.name}')

    if 'over_under' not in tipos_existentes:
        Market.create_overunder_market(
            event=event,
            line=Decimal('2.5'),
            odds_over=Decimal(str(odds[3])),
            odds_under=Decimal(str(odds[4])),
        )
        print(f'  [ok] Over/Under para {event.name}')
    else:
        print(f'  [skip] O/U {event.name}')

    if 'btts' not in tipos_existentes:
        Market.create_btts_market(
            event=event,
            odds_yes=Decimal(str(odds[5])),
            odds_no=Decimal(str(odds[6])),
        )
        print(f'  [ok] BTTS para {event.name}')
    else:
        print(f'  [skip] BTTS {event.name}')

    if 'handicap' not in tipos_existentes:
        Market.create_handicap_market(
            event=event,
            handicap=Decimal('-1.5'),
            odds_home=Decimal(str(odds[7])),
            odds_away=Decimal(str(odds[8])),
        )
        print(f'  [ok] Handicap para {event.name}')
    else:
        print(f'  [skip] Handicap {event.name}')

    if 'goleador_exacto' not in tipos_existentes:
        jugadores = []
        for j in jugadores_locales + jugadores_visitantes:
            jugadores.append({'nombre': j[0], 'odds': Decimal(str(j[1]))})
        Market.create_goleador_exacto_market(
            event=event,
            jugadores=jugadores,
            odds_sin_goleador=Decimal('3.20'),
        )
        print(f'  [ok] Goleador exacto para {event.name}')
    else:
        print(f'  [skip] Goleador {event.name}')


def main():
    print('\n=== FairBet Lab — Seed de datos ===\n')

    print('>> Cuentas del sistema...')
    crear_cuentas_sistema()

    print('\n>> Usuarios...')
    admin = crear_usuario('admin', 'admin123', None, es_admin=True)
    user1 = crear_usuario('carlos', 'carlos123', dni='12345678')
    user2 = crear_usuario('maria', 'maria123', dni='87654321')
    user3 = crear_usuario('pedro', 'pedro123', dni='45678901')
    user4 = crear_usuario('ana', 'ana12345', dni='56789012')

    for user in [user1, user2, user3, user4]:
        Account.objects.get_or_create(
            user=user,
            type=Account.AccountType.WALLET,
            defaults={'currency': 'PEN'},
        )

    print('\n>> Recargando saldo inicial...')
    for user, monto in [
        (user1, Decimal('500.0000')),
        (user2, Decimal('300.0000')),
        (user3, Decimal('1000.0000')),
        (user4, Decimal('250.0000')),
    ]:
        try:
            execute_recharge(user=user, amount=monto)
            print(f'  [ok] {user.username} recargado con S/ {monto}')
        except Exception as e:
            print(f'  [skip] {user.username}: {e}')

    print('\n>> Eliminando eventos anteriores...')
    Event.objects.all().delete()
    print('  [ok] Eventos eliminados')

    print('\n>> Creando eventos deportivos...')
    e1 = crear_evento('Peru vs Brasil', 'Peru', 'Brasil', horas_desde_ahora=0)
    e2 = crear_evento('Argentina vs Chile', 'Argentina', 'Chile', horas_desde_ahora=2)
    e3 = crear_evento('Colombia vs Ecuador', 'Colombia', 'Ecuador', horas_desde_ahora=5)
    e4 = crear_evento('Uruguay vs Bolivia', 'Uruguay', 'Bolivia', horas_desde_ahora=24)
    e5 = crear_evento('Venezuela vs Paraguay', 'Venezuela', 'Paraguay', horas_desde_ahora=48)
    e6 = crear_evento('Mexico vs Costa Rica', 'Mexico', 'Costa Rica', horas_desde_ahora=72)

    # Peru vs Brasil en LIVE para el demo
    e1.status = EventStatus.LIVE
    e1.save()
    print('  [ok] Peru vs Brasil -> LIVE')

    print('\n>> Mercados...')
    mercados_config = [
        (e1, (2.50, 3.20, 2.80, 1.85, 1.95, 1.75, 2.05, 2.20, 1.65),
         [('Guerrero', 4.50), ('Lapadula', 5.00), ('Cueva', 7.00)],
         [('Neymar', 3.50), ('Vinicius', 4.00), ('Rodrygo', 5.50)]),

        (e2, (1.90, 3.50, 3.80, 2.00, 1.80, 1.65, 2.20, 1.80, 2.10),
         [('Messi', 2.50), ('Di Maria', 5.00), ('Lautaro', 4.00)],
         [('Alexis', 5.50), ('Vidal', 7.00), ('Vargas', 6.00)]),

        (e3, (2.10, 3.00, 3.40, 1.90, 1.90, 1.80, 2.00, 2.10, 1.70),
         [('Falcao', 4.00), ('Cuadrado', 6.00), ('James', 5.00)],
         [('Valencia', 5.50), ('Caicedo', 6.50), ('Plata', 7.00)]),

        (e4, (1.75, 3.80, 4.20, 1.75, 2.05, 1.70, 2.10, 1.75, 2.20),
         [('Suarez', 3.50), ('Cavani', 4.00), ('Bentancur', 7.00)],
         [('Marcelo', 8.00), ('Algaranaz', 9.00), ('Saucedo', 8.50)]),

        (e5, (2.80, 3.10, 2.50, 1.95, 1.85, 1.85, 1.95, 2.30, 1.60),
         [('Soteldo', 5.00), ('Rondon', 4.50), ('Herrera', 7.00)],
         [('Sanabria', 4.00), ('Almiron', 3.50), ('Enciso', 6.00)]),

        (e6, (1.60, 3.90, 5.00, 1.70, 2.10, 1.65, 2.25, 1.55, 2.60),
         [('Lozano', 3.00), ('Raul', 5.00), ('Herrera', 6.00)],
         [('Campbell', 5.50), ('Tejeda', 7.00), ('Venegas', 8.00)]),
    ]

    for event, odds, jug_local, jug_visitante in mercados_config:
        try:
            crear_mercados(event, odds, jug_local, jug_visitante)
        except Exception as e:
            print(f'  [error] {event.name}: {e}')

    print('\n>> Verificando KYC...')
    for username in ['carlos', 'maria', 'pedro', 'ana']:
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

    print('\n=== Seed completado ===')
    print('\nCredenciales de demo:')
    print('  Admin:  admin / admin123')
    print('  User 1: carlos / carlos123 (S/ 500)')
    print('  User 2: maria  / maria123  (S/ 300)')
    print('  User 3: pedro  / pedro123  (S/ 1000)')
    print('  User 4: ana    / ana12345  (S/ 250)')
    print('\nEventos LIVE: Peru vs Brasil')
    print('Eventos proximos: Argentina vs Chile, Colombia vs Ecuador')
    print('Eventos futuros:  Uruguay vs Bolivia, Venezuela vs Paraguay, Mexico vs Costa Rica')
    print('\nSwagger UI: http://localhost:8000/api/schema/swagger-ui/')
    print('Admin:      http://localhost:8000/admin/')
    print('Login:      http://localhost:8000/')


if __name__ == '__main__':
    main()