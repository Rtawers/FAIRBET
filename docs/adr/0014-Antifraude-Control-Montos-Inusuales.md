# ADR-0014: Estrategia Unificada Antifraude - Control de Montos Inusuales (Varianza)

## Contexto
En el desarrollo de FairBet Lab, bajo las directrices del cumplimiento normativo (Ley 31557 y DS 005-2023-MINCETUR), es un requisito de seguridad indispensable mitigar patrones de fraude financiero y posible lavado de activos.

En el módulo de Compliance, enfrentamos la necesidad de implementar una política estricta de control de montos sin perjudicar la experiencia del usuario ni interferir con la lógica interna de otros módulos:
1. *Control de Montos Inusuales (Varianza):* Detectar si un usuario realiza una recarga o apuesta que rompa exageradamente su patrón histórico, indicando un comportamiento anómalo. Se fija el umbral de alerta si una nueva transacción supera en más de un 300% el monto promedio de sus transacciones anteriores.

Existe una restricción arquitectónica innegociable: este detector debe operar en modo *SOLO LECTURA*. No debe modificar, alterar ni bloquear los modelos de transacciones ni apuestas nativas.

## Opciones consideradas
1. *Opción A - Bloqueo transaccional duro (Acoplamiento fuerte):*
   * Pros: Impide físicamente que el dinero sospechoso ingrese al ecosistema de la billetera.
   * Contras: Requiere modificar directamente los servicios centrales de `wallet`, violando la regla de arquitectura de solo lectura y arriesgando romper el código base del flujo de recargas.
2. *Opción B - Evaluación pasiva en tiempo real con alertas inmutables:*
   * Pros: Respeta el aislamiento. El módulo lee el historial reciente del usuario utilizando el ORM de Django (limmitando la lectura para no saturar la base de datos). Si detecta que la nueva recarga supera el umbral del 300%, registra silenciosamente una alerta en la tabla `SuspiciousActivity` del tipo `VARIANCE`, permitiendo que la transacción original siga su curso normal.
   * Contras: Exige que los operadores de la plataforma monitoreen el panel de alertas para tomar acciones manuales posteriores sobre la cuenta.

## Decision
Se eligió la *Opción B*. Cumplir estrictamente con la regla de solo lectura asegura que el módulo de Compliance sea un observador no destructivo.

La regla se implementa mediante el servicio `check_unusual_amount` dentro de `apps.compliance.services`. Este servicio extrae el promedio del historial transaccional del usuario. Al momento de registrarse una desviación superior al 300%, se gatilla la creación del registro inmutable de fraude, garantizando la trazabilidad sin romper el principio de responsabilidad única (SRP).

## Consecuencias
* *Qué se vuelve más fácil:* La auditoría y generación de reportes regulatorios sobre comportamientos financieros erráticos sin interrumpir las conversiones de la plataforma.
* *Qué se vuelve más difícil:* El sistema sufre de "arranque en frío" (Cold Start). Los usuarios completamente nuevos no tienen un historial base para calcular un promedio, por lo que esta regla se vuelve efectiva recién a partir de su tercera transacción.
* *Qué deuda técnica se asume:* Calcular promedios matemáticos al vuelo consume más recursos de CPU y base de datos. En el futuro, si el volumen de usuarios crece drásticamente, se deberá migrar este cálculo matemático a tareas asíncronas con Celery.

## Fecha y autor
2026-05-27 - Pamela Chavez 