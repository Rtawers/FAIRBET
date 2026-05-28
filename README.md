
Esta versión unifica textualmente todo lo que tenías en tu archivo base, pero incorporando al 100% las sutilezas técnicas, regulaciones de la Ley 31557 peruana, el control de concurrencia y las pautas estrictas sobre el historial de Git e Inteligencia Artificial que exige la rúbrica del reto **FairBet Lab**.

```markdown
# FairBet

> Plataforma educativa con moneda virtual. **No constituye una casa de apuestas.**

Simulador de apuestas con fichas virtuales. Stack: Django 5.x + DRF + PostgreSQL +
Redis + Celery + Channels. Enfocado en la integridad financiera, la reactividad en tiempo real, el juego responsable y el cumplimiento normativo institucional conforme a la **Ley 31557** y su reglamento **DS 005-2023-MINCETUR**.

## Levantar el entorno

```bash
cp .env.example .env
docker compose build
docker compose up

```

* API REST (WSGI / Gunicorn): http://localhost:8000
* Admin Django:                http://localhost:8000/admin

```bash
# Migrar la base de datos antes de interactuar con el entorno
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
docker compose exec web python scripts/seed.py     # seed de eventos y usuarios

```

---

## Apps

### 🔹 accounts
* **Responsabilidad (a implementar):** Registro, KYC simulado, estados de cuenta. Validación de mayoría de edad ($\ge 18$ años) cruzando fecha de nacimiento con el algoritmo del dígito verificador Módulo 11 para DNI peruano. Estados: `pendiente_verificacion`, `verificado`, `bloqueado`, `autoexcluido`.
* **Estado / Requisito:** Obligatorio

### 🔹 wallet
* **Responsabilidad (a implementar):** Ledger de partida doble, saldo derivado. El saldo es una métrica estrictamente derivada del histórico; está prohibido guardar el saldo como columna estática. Bloqueos pesimistas contra condiciones de carrera.
* **Estado / Requisito:** Crítico (Mínimo 80% Cobertura)

### 🔹 events
* **Responsabilidad (a implementar):** Eventos, mercados, cuotas (odds) (real-time). Catálogo jerárquico de eventos (`programado`, `en_vivo`, `finalizado`, `suspendido`, `anulado`) y mercados mínimos (1X2, Over/Under 2.5, BTTS, Hándicap).
* **Estado / Requisito:** Tiempo Real (Channels)

### 🔹 betting
* **Responsabilidad (a implementar):** Apuestas, maquina de estados, liquidacion. Control transaccional de estados de apuestas simples y combinadas (`accepted`, `settled`, `cancelled`). Retención temporal en cuenta puente y cálculo matemático exacto de Payout.
* **Estado / Requisito:** Crítico (Mínimo 80% Cobertura)

### 🔹 compliance
* **Responsabilidad (a implementar):** Anti-fraude, reporte MINCETUR, juego responsable. Motores de límites financieros (diarios, semanales, mensuales) con cooldown obligatorio de 24h para incrementos. Gestión de autoexclusiones irreversibles.
* **Estado / Requisito:** Obligatorio

### 🔹 audit
* **Responsabilidad (a implementar):** Auditoria inmutable encadenada por hash. Bitácora *append-only* criptográfica ($Hash_n = SHA256(Hash_{n-1} + Payload_n)$). Almacena de forma indeleble cada apuesta, re-cotización y movimiento de saldo.
* **Estado / Requisito:** Criptográfico

### 🔹 dashboard
* **Responsabilidad (a implementar):** Metricas operador (GGR, exposure). Panel de control en vivo para calcular el GGR ($stakes - payouts$), la exposición financiera por selección en riesgo y exportación periódica estilo MINCETUR (CSV).
* **Estado / Requisito:** Operaciones
---

## Dinero

Todo monto usa `config.fields.MoneyField` (`max_digits=18`, `decimal_places=4`).
**Prohibido `float`.**

### Invariantes y Reglas Contables Inquebrantables

1. **Invariante Contable de Partida Doble:** Cada operación financiera genera una transacción compuesta obligatoriamente por un mínimo de dos registros `LedgerEntry` perfectamente balanceados (Débito y Crédito) asociados a un identificador transaccional único global (`transaction_id`). Una transacción se considera inválida si su suma algebraica neta no es exactamente cero ($\sum \text{Monto} = 0$).
2. **Cuentas Contables Clave del Sistema:**
* `wallet_usuario`: El dinero/fichas virtuales de libre disponibilidad del jugador.
* `casa`: Arcas centrales de la plataforma educativa (donde se consolidan pérdidas de apuestas liquidadas).
* `apuestas_pendientes`: Cuenta puente transitoria donde se retiene el *stake* en garantía mientras los eventos se resuelven.
* `bonos`: Saldo promocional sujeto a tracking algorítmico de condiciones de *rollover*.



---

## 🧪 Pruebas Automatizadas y Calidad de Código

El núcleo financiero de la plataforma (`wallet` y `betting`) está resguardado por una suite intensiva de pruebas que valida el comportamiento ante fallas concurrentes:

```bash
# Ejecutar todas las pruebas automatizadas con reporte de cobertura integrado
docker compose exec web pytest --cov --cov-report=html

```

### Verificaciones mediante Property-Based Testing (`hypothesis`)

* **Consistencia del Libro Mayor:** Se generan aleatoriamente miles de transacciones complejas para verificar matemáticamente que la suma de todos los débitos y créditos del sistema sea perpetuamente cero.
* **Invariante de Billetera:** Validación estricta de que bajo ningún flujo de transacciones paralelas concurrentes una billetera virtual finalice con saldo negativo.
* **Cálculo de Payout Matemático Exacto:** Confirmación de que el retorno de apuestas ganadoras se ejecute con precisión pura mediante la fórmula $\text{payout} = \text{stake} \times \text{odds}$, neutralizando errores por redondeo.

### Control de Concurrencia y Anti-Fraude

* **Prevención de Doble Gasto:** Combinación de sentencias de bloqueo a nivel de registros de base de datos (`select_for_update`) con el uso obligatorio de **Idempotency Keys** en las cabeceras HTTP de los endpoints de procesamiento de apuestas.
* **Detección de Fraude Simulado:** Generación de alertas en tiempo real (`SuspiciousActivity`) al detectar comportamientos anómalos automatizados, como apuestas simultáneas idénticas en grupo o accesos masivos paralelos usando una misma dirección IP.

---

## ⚡ Reactividad y Tiempo Real (`Django Channels`)

* **Sincronización In-Play:** Consumo e inyección continua de cuotas actualizadas en vivo hacia el cliente mediante WebSockets a través de canales asíncronos distribuidos con Redis.
* **Política Estricta de Re-Cotización:** Si una cuota cambia en el servidor mientras el usuario mantiene abierto el boleto de apuestas y el momento en que confirma la operación, el backend aborta la transacción automáticamente, refresca visualmente la nueva cuota y fuerza una confirmación manual explícita.
* **Bloqueo por Evento Crítico:** Suspensión automática temporal de mercados por $N$ segundos ante sucesos de alta sensibilidad competitiva (goles, tarjetas rojas, revisiones VAR).

---

## docs/

Entregables de proceso (ADRs, bitacora, lecciones, compliance, OpenAPI). El contenido lo escribes tu.

* **`docs/adr/`**: Repositorio histórico que documenta un **mínimo de 10 Architectural Decision Records (ADRs)** numerados. Incluye las justificaciones del diseño contable en partida doble, mitigación de condiciones de carrera mediante exclusión pesimista, máquina de estados de tickets de apuesta e inmutabilidad de la auditoría.
* **`docs/sketches/`**: Almacena los diagramas y bocetos conceptuales hechos a mano: Modelo Entidad-Relación de la contabilidad, la máquina de estados de una apuesta (`Bet`) y los diagramas de secuencia para los flujos complejos de liquidación, re-cotización y *cash-out*.
* **`docs/lecciones.md`**: Bitácora de desarrollo que registra un **mínimo de 4 bloqueos técnicos significativos o intentos fallidos superados por cada sprint**, detallando la causa raíz del error, alternativas evaluadas y la solución definitiva implementada.
* **`docs/anti-ai-disclosure.md`**: Declaración individual transparente firmada por los integrantes que detalla rigurosamente el alcance, el contexto pedagógico y las consultas/prompts delegados a herramientas de Inteligencia Artificial Generativa.

---

## 📜 Reglas de Contribución y Git (Gobernanza del Repositorio)

Para asegurar la autoría del código y la transparencia del proceso académico, el historial de Git se audita bajo los siguientes criterios:

1. **Conventional Commits:** Todos los mensajes de commit deben seguir obligatoriamente el estándar semántico (`feat:`, `fix:`, `test:`, `docs:`, `refactor:`, `chore:`, `perf:`).
2. **Evidencia Cronológica de TDD:** El historial de Git para las aplicaciones core (`wallet` y `betting`) debe demostrar orgánicamente la metodología de Desarrollo Guiado por Pruebas, evidenciando que los commits de tipo `test:` preceden temporalmente a los commits de tipo `feat:` asociados.
3. **Sufijo Obligatorio para Inteligencia Artificial:** Cuando un commit contenga código cuya estructura lógica o algoritmos hayan sido asistidos o generados significativamente mediante IA, **deberá incluir obligatoriamente el sufijo `[ai-assisted]**` en el título o en el cuerpo del mensaje.
4. **Atomicidad de Cambios:** Quedan estrictamente prohibidos los macro-commits masivos (ej. *"implementación del módulo wallet completo"* con alteraciones superiores a 1000 líneas de código). Cada commit debe contener una sola unidad lógica y atómica de trabajo.

```

```