# ADR-0013: Estrategia Unificada Antifraude - Control de Multi-Cuentas por IP y Velocidad Transaccional

## Contexto
En el desarrollo de FairBet Lab, bajo las directrices del cumplimiento normativo (Ley 31557 y DS 005-2023-MINCETUR), es un requisito de seguridad indispensable mitigar patrones de fraude financiero, suplantación de identidad, lavado de activos o ataques automatizados por bots (como ráfagas de micro-recargas o registros masivos desde infraestructuras únicas). 

En el módulo de Compliance y Cuentas, enfrentamos la necesidad de implementar dos políticas estrictas de control sin perjudicar la experiencia de usuarios legítimos:
1. *Control de Multi-Cuentas:* Evitar que un atacante cree redes de cuentas sintéticas para abusar de bonos o simular identidades, limitando el registro a un máximo de 3 usuarios por dirección IP. El cuarto registro debe nacer penalizado.
2. *Control de Velocidad Transaccional:* Detectar ráfagas anómalas de depósitos/recargas fijando un umbral máximo de 5 transacciones en una ventana móvil de 60 minutos.

Se requería definir una arquitectura limpia que evalúe estos disparadores en tiempo real, persistiendo alarmas inmutables para auditoría y tomando acciones automáticas sobre el estado operativo del cliente.

## Opciones consideradas
1. *Opción A - Procesamiento reactivo mediante tareas programadas (Cronjobs asíncronos):* * Pros: Minimiza la latencia en las solicitudes HTTP de registro y de recarga en el monedero al no inyectar consultas agregadas complejas (COUNT) en caliente sobre las tablas principales.
   * Contras: Nula capacidad de respuesta inmediata. Un atacante podría registrar decenas de cuentas o procesar múltiples micro-transacciones fraudulentas en pocos minutos antes de que el proceso en lote nocturno detecte la anomalía, anulando el propósito de la mitigación de riesgos.
2. *Opción B - Evaluación transaccional en tiempo real mediante interceptación basada en eventos y lógica de negocio unificada:* * Pros: Permite reaccionar al instante (Acción Atómica Inmediata). Si se detecta un cuarto registro desde la misma IP, el perfil se marca inmediatamente como BLOCKED dentro de la base de datos de cuentas. Centraliza además todas las alertas en un modelo inmutable compartido (SuspiciousActivity), capturando descripciones técnicas detalladas legibles por operadores y entes reguladores. Facilita la construcción de suites de pruebas unitarias bajo metodología TDD sólidas.
   * Contras: Introduce una penalización leve en el rendimiento debido al uso de consultas relacionales agregadas directas (filter().count()) durante los ciclos de registro de cuentas y ejecución de transacciones.

## Decision
Se eligió la *Opción B*. La integridad operativa y el cumplimiento regulatorio en tiempo real son prioridades críticas para FairBet Lab. 

La arquitectura unificada se implementó mediante dos componentes clave:
* *Control Temprano en Registro (Cuentas):* En apps.accounts.signals, se intercepta la creación del usuario a través de una señal reactiva que extrae la dirección IP (REMOTE_ADDR) del contexto de la petición de la API mediante inspección de hilos. Si la IP supera el umbral máximo de 3 cuentas, el estado de KYC del perfil se altera inmediatamente a BLOCKED y se guarda una alerta del tipo MULTI_ACCOUNT_IP.
* *Control de Velocidad (Compliance/Wallet):* El servicio check_transaction_velocity dentro de apps.compliance calcula las transacciones únicas asociadas al usuario en los últimos 60 minutos utilizando el ORM de Django (entries__account__user). Al exceder el umbral de 5 transacciones, registra de forma inmediata una alerta de tipo VELOCITY.

Ambos controles fueron validados exitosamente bajo la metodología TDD con las suites AccountsAPITestCase y AntiFraudVelocityTests, cubriendo los casos límite donde la cuarta cuenta nace bloqueada y la sexta transacción gatilla el registro inmutable de fraude.

## Consecuencias
* *Qué se vuelve más fácil:* La centralización y visualización de alertas antifraude se simplifica drásticamente para los operadores del sistema a través de la tabla SuspiciousActivity, la cual almacena marcas de tiempo inmutables (created_at).
* *Qué se vuelve más difícil:* El control basado en la IP del cliente puede verse afectado por entornos de red compartidos legítimos (ej. redes corporativas, instituciones o redes de un mismo hogar), lo que requerirá el desarrollo futuro de un flujo administrativo de desbloqueo manual por parte de un operador de soporte.
* *Qué deuda técnica se asume:* Las operaciones de conteo directo sobre las tablas del ORM en la base de datos relacional son lineales. Si el volumen de usuarios o transacciones se escala masivamente (x10 o x100), se asumirá la tarea de migrar estas consultas directas hacia una arquitectura de almacenamiento en caché en memoria y estructuras de ventanas deslizantes basadas en Redis.

## Fecha y autor
2026-05-26 - Pamela (Compliance) & Maicol (Accounts)