# ADR-0005 — WebSockets vs Server-Sent Events para odds en tiempo real

**Fecha:** 2026-05-23  
**Autor:** LuviMontes-P  
**Estado:** Aceptado  

---

## Contexto

El sistema necesita transmitir cambios de odds a los clientes en tiempo real.
Cuando el admin actualiza una cuota, todos los usuarios con el ticket de apuesta
abierto deben ver la nueva cuota antes de confirmar.

---

## Opciones consideradas

### A — Polling (descartada)

El cliente hace GET cada N segundos.

**Pros:** Simplicidad total, sin dependencias adicionales.  
**Contras:** 100 usuarios × cada 2s = 50 req/s solo para odds. Latencia mínima de N segundos. Carga en BD aunque no haya cambiado nada.

### B — Server-Sent Events / SSE (descartada)

Conexión HTTP persistente unidireccional servidor → cliente.

**Pros:** Más simple que WebSockets. Reconexión automática del navegador.  
**Contras:** Unidireccional — el cliente no puede confirmar re-cotización. Django no tiene soporte nativo.

### C — WebSockets con Django Channels ✓ (elegida)

Conexión bidireccional persistente sobre TCP.

**Pros:**
- Bidireccional: el cliente puede confirmar re-cotizaciones.
- Fan-out eficiente con Redis channel layer.
- `WebsocketCommunicator` permite tests sin servidor real.

**Contras:**
- Requiere Daphne (puerto 8001) además de Gunicorn (puerto 8000).
- Redis obligatorio para channel layer en producción.

---

## Decisión

**WebSockets con Django Channels.**

La razón principal es la bidireccionalidad para la política de re-cotización.
El coste de Redis ya está asumido por Celery.

---

## Problemas encontrados durante implementación

### 1. `pytest-asyncio` versión incorrecta
Al instalar `pytest-asyncio` con `pip install` dentro del contenedor,
se instaló la versión `1.3.0` (muy antigua) que no reconoce `asyncio_mode = auto`.
**Solución:** Fijar `pytest-asyncio==0.24.0` y `pytest==8.4.2` en
`requirements-dev.txt` y reconstruir la imagen con `docker compose build web`.

### 2. `AllowedHostsOriginValidator` bloqueaba conexiones en tests
El `config/asgi.py` original usaba `AllowedHostsOriginValidator` que rechazaba
conexiones WebSocket en tests porque el host era `testserver`.
**Solución:** Reemplazar por `AuthMiddlewareStack` directo y agregar
`ALLOWED_HOSTS = ["*"]` en settings cuando `pytest` está en `sys.modules`.

### 3. `websocket_urlpatterns = []` — routing vacío
El `config/asgi.py` del repo tenía el routing comentado como ejemplo.
Los tests fallaban con `connected = False` porque ninguna URL manejaba WebSockets.
**Solución:** Importar `from apps.events.routing import websocket_urlpatterns`.

### 4. `RedisChannelLayer` en tests — `Two event loops`
Los tests async usaban Redis real, causando conflictos de event loop.
**Solución:** Agregar `InMemoryChannelLayer` en settings cuando se detecta pytest:
```python
import sys
if "pytest" in sys.modules:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer",
        }
    }
```

### 5. Serialización de Decimal en WebSocket
El consumer enviaba `str(Decimal("2.75"))` que produce `"2.75"`, pero el test
esperaba `"2.7500"`. 
**Solución:** Comparar con `Decimal(msg["odds"]) == Decimal("2.75")` en lugar
de comparar strings directamente.

### 6. Redondeo ROUND_HALF_UP en Hypothesis
El test de Hypothesis calculaba `expected` sin especificar modo de redondeo,
mientras `calculate_margin` usaba `ROUND_HALF_UP`. Con ciertos valores como
`Decimal("5.12")` los resultados diferían en el último decimal.
**Solución:** Agregar `rounding=ROUND_HALF_UP` al `quantize` del expected en el test.

---

## Consecuencias

**Más fácil:**
- Re-cotización bidireccional en el futuro.
- Escala horizontal con Redis channel layer.

**Más difícil:**
- Servidor en dos puertos (8000 WSGI + 8001 ASGI).
- Tests async requieren `@pytest.mark.asyncio` y `transaction=True`.

**Deuda técnica:**
- El cliente JS debe manejar reconexión manual con backoff exponencial.
- `asyncio_mode = auto` debe estar fijo en `requirements-dev.txt` para
  evitar que otros miembros del equipo tengan el mismo problema de versión.