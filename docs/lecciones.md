## Sprint 2 — Wallet concurrencia

### Intento fallido: test de concurrencia con TestCase normal

- **Fecha:** 2026-05-23
- **Contexto:** primer intento del test de concurrencia usando
  `django.test.TestCase`.
- **Error:** `Account.DoesNotExist` en todos los threads secundarios.
  El contador de exitos quedaba en 0.
- **Causa raiz:** `TestCase` envuelve cada test en una transaccion
  que nunca se commitea. Los threads secundarios tienen sus propias
  conexiones a la BD y no pueden ver datos no commiteados.
- **Solucion:** usar `TransactionTestCase` que hace commits reales,
  y cerrar la conexion de cada thread con `connection.close()` en
  el bloque `finally`.
- **Leccion:** tests de concurrencia con threads SIEMPRE requieren
  `TransactionTestCase`, no `TestCase`.


  ### Intento fallido: tests de WebSockets fallaban por configuración faltante en pytest.ini

- **Fecha:** 2026-05-25
- **Contexto:** al integrar el trabajo del equipo, 2 tests de
  WebSockets fallaban con "async def functions are not natively supported".
- **Error:** pytest no ejecutaba funciones async aunque pytest-asyncio
  estaba instalado en requirements-dev.txt.
- **Causa raíz:** faltaba `asyncio_mode = auto` en pytest.ini.
  Sin esa línea, pytest-asyncio no activa el modo automático y
  rechaza las funciones async.
- **Solución:** agregar `asyncio_mode = auto` en pytest.ini.
- **Lección:** instalar pytest-asyncio no es suficiente — hay que
  configurarlo en pytest.ini con asyncio_mode = auto.