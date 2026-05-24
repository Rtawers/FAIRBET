# ADR-0004: Arquitectura de Registro y KYC con Validación de DNI Peruano (Módulo 11)

## Contexto
El sistema FairBet requiere cumplir con la Ley 31557 y el reglamento
DS 005-2023-MINCETUR para operar apuestas deportivas en Perú. Esto exige
dos controles críticos antes de permitir que un usuario posea saldo o realice
apuestas: validación estricta de mayoría de edad (≥18 años) con precisión
de días, y validación del DNI peruano mediante el algoritmo Módulo 11
(8 dígitos numéricos + 1 carácter de control), con restricción de unicidad
en base de datos.

## Opciones consideradas

1. **Validación por Expresiones Regulares fijas** — validar solo que el DNI
   tenga 8 números.
   - Pro: implementación rápida con validadores nativos de Django.
   - Contra: incapaz de detectar DNIs inventados. Permite registros falsos
     masivos evadiendo consistencia gubernamental.

2. **Consumo directo del API de RENEC en cada test** — llamadas HTTP a
   servicios externos durante el ciclo de vida del modelo.
   - Pro: datos 100% reales de ciudadanos peruanos.
   - Contra: introduce latencia, rompe el aislamiento de pruebas unitarias
     y detiene el pipeline de CI/CD si el API gubernamental se cae.

3. **Algoritmo puro Módulo 11 + aislamiento en capa de servicios** —
   implementar de forma nativa el algoritmo de suma de verificación por
   pesos oficial del DNI peruano.
   - Pro: autónomo y ultra-rápido sin llamadas externas. Facilita TDD puro.
     Permite pruebas con Hypothesis para validar invariantes sin ejemplos
     estáticos fijos.
   - Contra: requiere mantener matrices de pesos `[3, 2, 7, 6, 5, 4, 3, 2]`
     y diccionarios de conversión manuales. Obliga a controlar finamente
     excepciones de unicidad en base de datos.

## Decision
**Algoritmo puro Módulo 11 aislado en `apps/accounts/dni.py`** acoplado
al flujo atómico de `apps/accounts/services.py`.

La razón principal es blindar el sistema ante fraude de identidad y
auditorías del MINCETUR, garantizando que todo perfil nazca en estado
`PENDING_VERIFICATION` y solo transite a `VERIFIED` si el DNI es
matemáticamente íntegro, el titular es mayor de edad exacto al día de hoy,
y no existe duplicidad en el sistema.

## Consecuencias
Más fácil:
- La suite completa corre de forma homogénea en cualquier máquina con
  `docker compose run --rm web pytest apps/ -v`.
- El algoritmo del DNI soporta cualquier volumen de mutaciones aleatorias
  gracias a Hypothesis, garantizando cobertura matemática libre de
  excepciones inesperadas.

Más difícil:
- Las pruebas asíncronas imponen que cualquier modificación futura en
  dependencias requiera reconstruir las imágenes de Docker.
- El control de fechas con precisión de días exige uso continuo de
  `date.today()` dinámico, evitando quemar años fijos en pruebas temporales.

Deuda técnica:
- Mapeo manual estricto del carácter "K" en el algoritmo. Si la RENEC
  cambia su convención de asignación para nuevos ciudadanos, el código de
  `dni.py` debe ser actualizado.

## Fecha y autor
2026-05-23 - MaicolRafael