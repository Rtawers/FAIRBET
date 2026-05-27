# Bitacora semanal (individual)

| Semana | Que hice | Bloqueos | Decisiones |
|--------|----------|----------|------------|
| Semana 3 (26-05-2026) | Endpoints REST de betting (apostar, cash-out, listar), dashboard operador (GGR, exposure, volumen y CSV MINCETUR), logica rollover 5x derivada excluyendo apuestas CANCELLED, liquidacion de goleador exacto con caso SIN_GOLEADOR, adaptacion de tests al patron self.user.profile.save(). | Integracion del rollover depende de cuenta BONUS (wallet/Lennart). Integracion del goleador depende del mercado creado en events (Lucrecia). | GGR calculado solo sobre SETTLEMENT. Rollover derivado (no almacenado). Goleador usa seleccion especial SIN_GOLEADOR para empate tecnico 0-0. |