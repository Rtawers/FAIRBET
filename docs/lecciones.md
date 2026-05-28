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

## Lección: Señales de Django y efectos secundarios en tests

**Problema:** Al agregar una señal `post_save` en `accounts/models.py` para crear 
automáticamente la cuenta WALLET al registrar un usuario, los tests empezaron a fallar 
con `MultipleObjectsReturned`. 

**Causa:** Los tests crean usuarios manualmente en su `setUp` y también crean la cuenta 
WALLET explícitamente. La señal disparaba adicionalmente creando una segunda cuenta 
WALLET — resultando en 2 cuentas por usuario.

**Solución:** Quitar la señal y manejar la creación de la cuenta WALLET directamente 
en el `register_user` view con `get_or_create`. Las señales son potentes pero tienen 
efectos secundarios difíciles de controlar en tests — mejor ser explícito.

**Regla:** Si una señal rompe tests existentes, preferir lógica explícita en el servicio 
o vista correspondiente.

### Intento fallido: Error de campo inexistente al filtrar historial para regla de varianza

- **Contexto:** Desarrollo de la regla de Varianza (ADR-0014) en el módulo de Compliance, intentando obtener las últimas 10 transacciones del usuario desde `LedgerEntry` para calcular su promedio histórico.
- **Error:** `FieldError: Cannot resolve keyword 'created_at' into field. Choices are: account, amount, direction, id, transaction...`
- **Causa raiz:** Intentamos ordenar el historial usando `.order_by('-created_at')` asumiendo que el campo existía. Sin embargo, el modelo `LedgerEntry` (diseñado por Wallet) no tenía ese campo directamente, ya que la fecha se guardaba en el modelo padre (`Transaction`).
- **Solucion:** Reemplazar `-created_at` por `-id` en el método `order_by()`. Como los IDs son autoincrementales en la base de datos relacional, el ID más alto siempre corresponde al registro más nuevo, logrando el mismo orden cronológico sin hacer *joins*.
- **Leccion:** Al aplicar el principio de "Solo Lectura" sobre modelos de otros módulos, SIEMPRE se debe revisar el Diagrama ER final de los compañeros. Además, aprovechar las propiedades de las bases de datos relacionales (como IDs secuenciales) evita consultas complejas y errores del ORM.
