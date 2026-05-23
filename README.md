# FairBet

> Plataforma educativa con moneda virtual. **No constituye una casa de apuestas.**

Simulador de apuestas con fichas virtuales. Stack: Django 5.x + DRF + PostgreSQL +
Redis + Celery + Channels.

## Levantar el entorno

```bash
cp .env.example .env
docker compose build
docker compose up
```

- API REST (WSGI / Gunicorn): http://localhost:8000
- WebSockets (ASGI / Daphne):  ws://localhost:8001
- Admin Django:                http://localhost:8000/admin

```bash
docker compose exec web python manage.py createsuperuser
docker compose exec web python scripts/seed.py     # seed de eventos y usuarios
```

## Apps

| App          | Responsabilidad (a implementar)                         |
|--------------|----------------------------------------------------------|
| `accounts`   | Registro, KYC simulado, estados de cuenta                |
| `wallet`     | Ledger de partida doble, saldo derivado  (critico 80%)   |
| `events`     | Eventos, mercados, cuotas (odds)  (real-time)            |
| `betting`    | Apuestas, maquina de estados, liquidacion  (critico 80%) |
| `compliance` | Anti-fraude, reporte MINCETUR, juego responsable         |
| `audit`      | Auditoria inmutable encadenada por hash                  |
| `dashboard`  | Metricas operador (GGR, exposure)                        |

## Dinero

Todo monto usa `config.fields.MoneyField` (`max_digits=18`, `decimal_places=4`).
**Prohibido `float`.**

## docs/

Entregables de proceso (ADRs, bitacora, lecciones, compliance, OpenAPI). El
contenido lo escribes tu.
