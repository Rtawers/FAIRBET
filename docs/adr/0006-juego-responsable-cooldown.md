# ADR-0006: Políticas de Juego Responsable y Cooldown

## Contexto
Necesitamos implementar un módulo de Juego Responsable (Compliance) que proteja activamente al jugador de comportamientos compulsivos. Debemos definir cómo el sistema maneja la aplicación de autoexclusiones y las modificaciones a los límites de depósito, asegurando que actúe como un freno real ante la impulsividad financiera.

## Opciones consideradas

1. **Gestión simétrica y revocable (Todo al instante)**
   - Pros: Implementación técnica muy sencilla. El usuario tiene control total y sin fricciones sobre su cuenta en todo momento.
   - Contras: Falla en proteger al usuario. Un jugador podría subir su límite de recarga o cancelar su autoexclusión en un momento de desesperación, contraviniendo las normativas de apuestas.

2. **Gestión asimétrica con Cooldown y Bloqueo Estricto**
   - Pros: Cumple con los más altos estándares regulatorios de la industria. Frena la impulsividad al imponer tiempos de espera (cooldowns) y bloqueos que no se pueden saltar.
   - Contras: Mayor complejidad técnica de estado. Requiere guardar límites "pendientes", consultar historiales por ventanas de tiempo y procesos automatizados para actualizar estados.

## Decision
Adoptamos la **Opción 2**. La protección psicológica y financiera del usuario es innegociable frente a la conveniencia técnica. Esta arquitectura se sostiene bajo tres pilares que defenderemos a nivel de código:

* **Bajar el límite es instantáneo, pero subirlo tarda 24h:** Si el usuario decide protegerse reduciendo su límite de depósito, el sistema asume esa regla de inmediato. Sin embargo, si decide subirlo, el monto queda en estado "pending" durante un *cooldown* de 24 horas. Esto garantiza que la decisión sea premeditada y no producto de la impulsividad por "perseguir pérdidas" (chasing losses).
* **Sin métodos de revocación de autoexclusión:** No existe ni existirá un endpoint o función en los servicios para revocar una autoexclusión activa. Si el jugador se bloquea, el candado es absoluto hasta que la fecha expire de forma natural. Permitir su cancelación manual destruiría el propósito de la herramienta de contención.
* **Implementación de Ventana Móvil de 24h:** El límite diario no se reinicia a la medianoche (lo cual permitiría depositar el máximo a las 11:59 PM y nuevamente a las 12:01 AM). Las recargas se validan contra una "ventana móvil", sumando dinámicamente los depósitos de las últimas 24 horas exactas desde el intento de recarga actual.

## Consecuencias
- Más fácil: Superar auditorías de *compliance* y asegurar la integridad ética de la plataforma al garantizar un entorno de Juego Responsable.
- Más difícil: La interfaz de usuario (Front-end) requerirá lógica adicional para mostrarle al jugador que su nuevo límite superior está en cola de espera, indicando la hora exacta de activación.
- Deuda técnica: La promoción de límites requiere un demonio o tarea programada (ej. Celery/Cron) ejecutando `promote_pending_limits()` regularmente. Además, la validación de la ventana móvil de 24h obliga a sumar transacciones recientes en cada recarga, lo que requerirá buenos índices de base de datos en las fechas de las transacciones a medida que la plataforma escale.

## Fecha y autor
2026-05-23 - Pamela Chavez