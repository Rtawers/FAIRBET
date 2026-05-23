# ADR-0002: Uso de Decimal en lugar de float para montos

## Contexto
Todo monto del sistema (fichas, odds, payouts) debe ser exacto.
Necesitamos elegir el tipo numerico para representarlos.

## Opciones consideradas

1. **float (Python nativo)**
   - Pros: sintaxis directa, rendimiento mayor.
   - Contras: errores de representacion binaria. En Python,
     0.1 + 0.2 = 0.30000000000000004. Inaceptable para dinero.

2. **Decimal con max_digits=18, decimal_places=4**
   - Pros: aritmetica exacta. Cuantizacion explicita con
     .quantize(Decimal('0.0001')) evita ambiguedad en redondeo.
     Compatible con DecimalField de Django y PostgreSQL NUMERIC.
   - Contras: sintaxis mas verbosa. Operaciones requieren
     cuantizacion explicita.

## Decision
Adoptamos **Decimal** en todos los montos. El campo `MoneyField`
en `config/fields.py` centraliza la configuracion (max_digits=18,
decimal_places=4) para toda la plataforma.

## Consecuencias
- Mas facil: garantizar "el payout siempre es stake x odds exacto".
- Mas dificil: mezclar Decimal con int/float requiere conversion
  explicita en cada operacion.
- Deuda tecnica: odds usan decimal_places=2, amounts usan 4.
  La multiplicacion produce hasta 6 decimales que cuantizamos a 4.

## Fecha y autor
2026-05-23 - Lennart Fustamante