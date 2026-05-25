# ADR-0004 — Arquitectura de Registro y KYC con Validación de DNI Peruano (Módulo 11)

**Fecha:** 2026-05-23  
**Autor:** MaicolRafael  
**Estado:** Aceptado  

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

## Decisiones Técnicas y Defensa Oral (Respuestas Clave para el Profesor)

### 1. ¿Qué es el algoritmo Módulo 11?
Es un mecanismo de detección de errores por suma de verificación por pesos. Toma los primeros 8 dígitos del DNI, multiplica cada uno por un peso fijo asignado de derecha a izquierda `[3, 2, 7, 6, 5, 4, 3, 2]`, suma los resultados, calcula el residuo al dividir entre 11 (`Suma % 11`) y resta `11 - Residuo` para obtener el dígito de control. Si el resultado es idéntico al noveno carácter introducido por el usuario, el DNI es matemáticamente válido.

### 2. ¿Por qué el dígito verificador puede ser K?
Cuando la operación matemática `11 - Residuo` da como resultado exactamente **10**, no se puede colocar un número de dos dígitos en un espacio destinado a un solo carácter. Por lo tanto, el estándar del algoritmo del DNI peruano reemplaza el valor numérico 10 por la letra **"K"** para mantener el diseño de un solo carácter verificador.

### 3. ¿Qué estados puede tener un UserProfile y por qué?
Nuestro modelo implementa tres estados obligatorios en su ciclo de vida:
- **`PENDING_VERIFICATION` (Pendiente):** Es el estado nativo y seguro con el que nacen todos los usuarios al registrarse. Evita que un perfil opere o gaste saldo antes de ser evaluado.
- **`VERIFIED` (Verificado):** El usuario pasa automáticamente aquí si es mayor de edad exacto al día de hoy, su DNI supera el filtro matemático Módulo 11 y es único en el sistema.
- **`REJECTED` (Rechazado):** Estado de bloqueo preventivo si se detecta un intento de fraude de identidad, documentos inválidos o alteración de datos.

---

## Consecuencias
- **Más fácil:** Bloquear accesos ilegales en la capa de servicios antes de tocar el balance de dinero.
- **Más difícil:** Asegurar que las fechas se calculen de forma dinámica sin quemar años fijos en los tests.
- **Deuda técnica:** El mapeo manual de la letra "K" debe mantenerse inalterado en el código fuente.