# Cumplimiento Ley 31557 / DS 005-2023-MINCETUR

## Que cubre el sistema
- **Verificación KYC (Art. 23):** Bloqueo estricto de registro a menores de edad calculando la diferencia exacta en días respecto a la fecha del servidor, y validación algorítmica de DNI peruano mediante criptografía de Módulo 11.
- **Protección SPLAFT y Anti-Fraude:** Motor pasivo de solo lectura que registra alertas inmutables (`SuspiciousActivity`) ante ráfagas de transacciones (regla de Velocidad: >5 tx/hora) y montos anómalos (regla de Varianza: recargas >300% del promedio histórico del usuario) según ADR-0013 y ADR-0014.
- **Prevención de multi-cuentas:** Restricción a un máximo de 3 cuentas registradas bajo la misma dirección IP (mitigación de abuso de bonos).
- **Juego Responsable:** Límites autoimpuestos de recarga (diario, semanal, mensual) y bloqueos operativos absolutos para usuarios que solicitan la autoexclusión temporal (7 días) o indefinida.
- **Trazabilidad y Transparencia:** Historial inmutable de cambios de cuotas (`OddsHistory`) con timestamp y autor, y cálculo de saldos y cuotas con precisión exacta (`Decimal`, prohibido el uso de floats).
- **Bloqueo de apuestas en vivo:** Suspensión automática de mercados ante eventos críticos in-play para proteger a los usuarios de cuotas desactualizadas.

## Que NO cubre (autocritica honesta)
- **Cruce de datos con entidades oficiales:** El sistema valida la integridad estructural del DNI mediante Módulo 11, pero en un entorno de producción real requeriría integración con la API de RENIEC o Migraciones para validar la existencia física del ciudadano.
- **Reporte Automático a la UIF-Perú:** Las alertas SPLAFT (varianza y velocidad) se registran localmente en la base de datos de auditoría. No se ha implementado el endpoint para el envío automático del Reporte de Operaciones Sospechosas (ROS) a la Unidad de Inteligencia Financiera.
- **Proveedores de Cuotas Certificados:** La ley exige el uso de cuotas provistas por laboratorios/proveedores internacionales certificados. En este MVP, las cuotas son administradas manualmente (o vía seed) por la casa de apuestas.
- **Re-cotización de cuotas en frontend:** Aunque el backend de WebSockets detecta los cambios en vivo y los transmite, el frontend actual no pide al usuario una confirmación explícita si la cuota cambia justo en el milisegundo en que intenta apostar.

## Mapeo requisito -> implementacion
| Requisito normativo | Donde se implementa | Estado |
|---------------------|---------------------|--------|
| Verificación de mayoría de edad (18+) | `apps.accounts` (Interceptación en registro) | Implementado |
| Validación de identidad (DNI) | `apps.accounts` (Algoritmo Módulo 11) | Implementado |
| Monitoreo SPLAFT (Lavado de activos) | `apps.compliance` (Alertas de Varianza >300% y Velocidad) | Implementado |
| Herramientas de Juego Responsable | `apps.compliance` (Autoexclusión y límites de depósito) | Implementado |
| Inmutabilidad de eventos y cuotas | `apps.events.models.OddsHistory` | Implementado |
| Mensajes de advertencia ludopatía | Frontend (`base.html` footer y vista de apuestas) | Implementado |
| Integración RENIEC / MINCETUR | N/A | No cubierto (MVP) |