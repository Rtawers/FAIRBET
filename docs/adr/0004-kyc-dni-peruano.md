# ADR-0004 — Arquitectura de Registro y KYC con Validación de DNI Peruano (Módulo 11)

**Fecha:** 2026-05-23  
**Autor:** MaicolRafael  
**Estado:** Aceptado (GREEN)  

---

## Contexto

El sistema FairBet requiere cumplir con las normativas de la Ley 31557 y su reglamento DS 005-2023-MINCETUR en el Perú. Esto exige validar la mayoría de edad (>= 18 años) y comprobar la identidad mediante el algoritmo matemático oficial del DNI peruano antes de aprobar un usuario.

---

## Opciones consideradas

### A — Validación básica por longitud (descartada)
Validar solo que el DNI tenga 9 caracteres alfabéticos o numéricos cualesquiera.
- **Pros:** Muy simple de programar.
- **Contras:** Permite que cualquier usuario invente un DNI aleatorio y se registre falsamente, violando las normas anti-fraude.

### B — Algoritmo Oficial Módulo 11 Integrado en Servicios ✓ (elegida)
Implementar la lógica del dígito verificador oficial del padrón peruano acompañado de una máquina de estados para el perfil de usuario.
- **Pros:** Garantiza la legitimidad matemática del documento sin llamadas lentas a APIs externas durante los tests.
- **Contras:** Requiere programar y testear manualmente matrices de pesos y conversiones de residuos.

---

## Ciclo TDD: Especificación e Implementación de la API

La implementación técnica de los componentes se rigió estrictamente bajo la metodología TDD (Test-Driven Development), dividida en las siguientes fases operativas:

### 1. Fase RED (Fallas Iniciales en la Suite)
Los requerimientos fueron validados mediante dos pruebas unitarias automatizadas en `apps/accounts/tests/test_api.py`. En el estado inicial, la suite fallaba debido a:
* **`test_red_registro_usuario_exitoso` (Falla 401 Unauthorized y KeyError):** El endpoint rechazaba las peticiones anónimas debido a políticas globales restrictivas y carecía de la estructura en el diccionario de respuesta para evaluar el estado inicial de verificación.
* **`test_red_verificacion_kyc_modulo11_exitoso` (Falla 501 Not Implemented y KeyError):** La ruta no procesaba la lógica del algoritmo ni mapeaba los campos exactos del payload enviado por el test (`dni_number` y `verification_digit`).

### 2. Fase GREEN (Resolución y Aserción Exitosa)
Se codificaron las respuestas en `apps/accounts/views.py` usando las abstracciones de Django REST Framework, logrando que los tests pasaran limpiamente (`2 passed`):
* Se aplicó `@permission_classes([AllowAny])` en el registro para permitir accesos públicos controlados.
* Se estructuró el JSON de respuesta para inyectar explícitamente la propiedad `"kyc_status"`, resolviendo los fallos de aserción de la suite global de manera atómica.

---

## Decisiones Técnicas y Defensa Oral (Respuestas Clave para el Profesor)

### 1. ¿Qué es el algoritmo Módulo 11?
Es un mecanismo de detección de errores por suma de verificación por pesos. Toma los primeros 8 dígitos del DNI, multiplica cada uno por un peso fijo asignado de derecha a izquierda `[3, 2, 7, 6, 5, 4, 3, 2]`, suma los resultados, calcula el residuo al dividir entre 11 (`Suma % 11`) y resta `11 - Residuo` para obtener el dígito de control. Si el resultado es idéntico al noveno carácter introducido por el usuario, el DNI es matemáticamente válido.

### 2. ¿Por qué el dígito verificador puede ser K?
Cuando la operación matemática `11 - Residuo` da como resultado exactamente **10**, no se puede colocar un número de dos dígitos en un espacio destinado a un solo carácter. Por lo tanto, el estándar del algoritmo del DNI peruano reemplaza el valor numérico 10 por la letra **"K"** para mantener el diseño de un solo carácter verificador. (Nota de implementación: el algoritmo mapea también el residuo 11 a `"0"` y 10 a `"1"` según variantes del padrón de Reniec).

### 3. ¿Qué estados puede tener un UserProfile y por qué?
Nuestro modelo implementa tres estados obligatorios en su ciclo de vida:
- **`PENDING_VERIFICATION` (Pendiente):** Es el estado nativo y seguro con el que nacen todos los usuarios al registrarse. Evita que un perfil opere o gaste saldo antes de ser evaluado.
- **`VERIFIED` (Verificado):** El usuario pasa automáticamente aquí si es mayor de edad exacto al día de hoy, su DNI supera el filtro matemático Módulo 11 y es único en el sistema.
- **`REJECTED` (Rechazado):** Estado de bloqueo preventivo si se detecta un intento de fraude de identidad, documentos inválidos o alteración de datos.

---

## Consecuencias
- **Más fácil:** Bloquear accesos ilegales en la capa de servicios antes de tocar el balance de dinero.
- **Más fácil (Aislamiento):** Validar la consistencia de datos de identidad en los tests sin depender de llamadas HTTP a APIs gubernamentales externas propensas a latencias o caídas.
- **Más difícil:** Asegurar que las fechas se calculen de forma dinámica sin quemar años fijos en los tests.
- **Deuda técnica global:** Debido a restricciones en el archivo `pytest.ini` general del proyecto, la suite exige un `fail-under=80`. Aunque el módulo `accounts` cuenta con cobertura óptima, la aprobación completa de la integración continua está sujeta a que los demás módulos (`betting`, `wallet`) completen sus fases de TDD individuales.