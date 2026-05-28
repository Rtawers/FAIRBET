# Intentos Fallidos, Diagnósticos y Lecciones Aprendidas

## Módulo 1: Concurrencia, Canales Asíncronos y Wallet

### 1. Intento fallido: Test de concurrencia con TestCase normal
- **Fecha:** 2026-05-23
- **Contexto:** Primer intento del test de concurrencia usando `django.test.TestCase`.
- **Error:** `Account.DoesNotExist` en todos los threads secundarios. El contador de éxitos quedaba en 0.
- **Causa raíz:** `TestCase` envuelve cada caso de prueba en una transacción de base de datos aislada que nunca realiza un commit explícito. Los hilos (threads) secundarios invocados abren sus propias conexiones independientes a la base de datos y, por aislamiento relacional, son incapaces de ver registros no confirmados (uncommitted data).
- **Solución:** Cambiar la herencia a `TransactionTestCase`, el cual ejecuta commits reales en la BD durante el ciclo de vida del test, y garantizar el cierre de flujos en hilos limpiando la conexión mediante `connection.close()` en un bloque `finally`.
- **Lección:** Las pruebas automatizadas que involucren paralelismo, concurrencia o hilos nativos SIEMPRE requieren heredar de `TransactionTestCase`.

### 2. Intento fallido: Tests de WebSockets fallaban por configuración faltante en pytest.ini
- **Fecha:** 2026-05-25
- **Contexto:** Al integrar las ramas del equipo de desarrollo, los tests asíncronos distribuidos de WebSockets empezaron a colapsar.
- **Error:** `async def functions are not natively supported` en la consola de pytest.
- **Causa raíz:** Aunque la extensión `pytest-asyncio` se encontraba declarada correctamente en el archivo `requirements-dev.txt`, el motor de ejecución pytest no tenía activado el modo de resolución automática de corrutinas.
- **Solución:** Se añadió la instrucción explícita `asyncio_mode = auto` dentro del bloque de configuración de `pytest.ini`.
- **Lección:** La instalación de dependencias asíncronas requiere obligatoriamente su correspondiente activación en las directivas de configuración global del framework de testing.

---

## Módulo 2: Arquitectura de Software, ORM y Señales Distribuidas

### 3. Lección: Señales de Django y efectos secundarios en cascada dentro de pruebas unitarias
- **Problema:** Al agregar una señal `post_save` en `apps/accounts/models.py` para crear automáticamente la entidad `WALLET` al registrar un nuevo usuario, los tests existentes de integración comenzaron a arrojar errores críticos.
- **Error:** `MultipleObjectsReturned: get() returned more than one Wallet -- it returned 2!`
- **Causa raíz:** Varios tests del sistema creaban usuarios de manera explícita en su bloque `setUp()` o factorías y, acto seguido, instanciaban manualmente la cuenta `WALLET` requerida para el escenario de prueba. Al activarse la señal `post_save` en segundo plano, se ejecutaba una inserción oculta redundante, generando dos billeteras para un mismo usuario de forma inválida.
- **Solución:** Se removió la señal implícita del modelo y se centralizó la inicialización segura dentro de la capa del servicio de registro (`register_user`) utilizando el método de control atómico `get_or_create`.
- **Lección/Regla:** Si una señal mágica e implícita rompe la suite de pruebas unitarias preexistente, se debe preferir siempre una lógica explícita de creación controlada en la capa de servicios o controladores.

### 4. Intento fallido: Error de campo inexistente al filtrar historial para regla de varianza
- **Contexto:** Desarrollo de la regla de control de montos inusuales (ADR-0014) en el módulo de Compliance, intentando extraer los últimos 10 movimientos monetarios desde `LedgerEntry`.
- **Error:** `FieldError: Cannot resolve keyword 'created_at' into field. Choices are: account, amount, direction, id, transaction...`
- **Causa raíz:** Se intentó realizar una ordenación del set de datos mediante la instrucción `.order_by('-created_at')` asumiendo erróneamente la existencia del atributo. Sin embargo, el modelo `LedgerEntry` delegaba la estampa de tiempo a su modelo padre/relacionado (`Transaction`).
- **Solución:** Se sustituyó la ordenación compleja por el campo secuencial nativo de la base de datos relacional: `.order_by('-id')`. Dado que los identificadores primarios son autoincrementales, el ID más alto siempre es equivalente al registro cronológicamente más reciente, evitando la necesidad de ineficientes operaciones de *JOIN*.
- **Lección:** Al operar en modo "Solo Lectura" sobre modelos diseñados por otros miembros del equipo, es indispensable auditar el diagrama de entidad-relación o reutilizar propiedades autoincrementales nativas para optimizar las consultas.

---

## Módulo 3: Compliance de Identidad, Reglas KYC e Integridad Forense

### 5. Intento fallido: Error MultipleObjectsReturned en tests de API KYC
- **Fecha:** 2026-05-24
- **Contexto:** Durante el testeo del ciclo de vida del usuario con la suite `APITestCase`, se verificaba el estado de mutación de cuentas recién creadas.
- **Error:** `MultipleObjectsReturned: get() returned more than one UserProfile` al invocar los endpoints de registro.
- **Causa raíz:** La persistencia repetida en el método `setUp()` disparaba señales fantasmas que duplicaban la entidad uno a uno (`OneToOneField`) del perfil de usuario durante llamadas concurrentes falsas de la API de pruebas.
- **Solución:** Sustituir inserciones directas por el uso estricto de cláusulas de actualización y verificación seguras como `UserProfile.objects.update_or_create(user=usuario, defaults=...)`.
- **Lección:** En entornos de API REST con Django, la persistencia de relaciones uno a uno debe blindarse usando métodos idempotentes del ORM para mitigar duplicidades no deseadas.

### 6. Intento fallido: Falsos positivos en pruebas KYC de Minoría de Edad en límites de fecha
- **Fecha:** 2026-05-26
- **Contexto:** Control de la restricción obligatoria de mayoría de edad ($\ge 18$ años) de acuerdo con los requerimientos técnicos exigidos por el MINCETUR (Ley 31557).
- **Error:** `AssertionError: False is not True` al ejecutar `test_usuario_que_cumple_18_anos_hoy_mismo_es_aceptado_en_kyc`. El motor rechazaba a los usuarios nacidos exactamente el mismo día del año límite.
- **Causa raíz:** La aproximación matemática inicial restaba únicamente los años calendario: `edad = date.today().year - fecha_nacimiento.year`, omitiendo validar si el mes y el día en curso ya habían alcanzado formalmente el aniversario de nacimiento de la persona.
- **Solución:** Se implementó una evaluación booleana robusta por tuplas nativas de comparación en Python, penalizando el año completo solo si la fecha actual es anterior al día de cumpleaños real:
  ```python
  hoy = date.today()
  edad = hoy.year - fecha_nacimiento.year - ((hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day))