# Nota de Arquitectura: Diagramas de Estado y de Tiempo — CU41 (Operación Offline y Sincronización)

**Fecha:** 2026-11-22  
**Contexto del Sistema — Modelado Dinámico y Temporal:**  
- Caso de Uso: **CU41M – Gestionar operación offline y sincronización**
- Diagramas requeridos: **Diagrama de Estados UML (State Machine)** y **Diagrama de Tiempos UML (Timing Diagram)**.
- Referencia de estilo: Ejemplos visuales provistos por el usuario (estilo académico en blanco y negro, estados en rectángulos redondeados con transiciones etiquetadas, cronogramas temporales con carriles, niveles de estado y cotas de duración `T > 0 seg`, `{1 - 5 seg}`, `{< 2 seg}`).

---

## 1. Análisis del Diagrama de Estados (Lifecycle de la Entidad de Sincronización)

El ciclo de vida del paquete/registro de datos capturado en faena sin conectividad atraviesa las siguientes etapas de estado:

1. **`CREADO_LOCAL` (Almacenado en SQLite):** El operario registra avances físicos o incidencias en la app móvil. Se persiste en la tabla local SQLite con estado `PENDIENTE_SYNC` y UUID idempotente.
2. **`EN_ESPERA_RED`:** El registro permanece en cola local hasta que el servicio de background de conectividad detecta disponibilidad de red (Wi-Fi o 4G).
3. **`EMPAQUETANDO_LOTE`:** La aplicación compila los registros pendientes en un payload estructurado JSON con checksum y credencial JWT.
4. **`EN_SINCRONIZACIÓN` (Transmitiendo):** Envío HTTP POST `/api/v1/sync/batch` hacia el API Gateway central.
5. **`EVALUANDO_CONCURRENCIA`:** El servidor valida la idempotencia y analiza marcas temporales contra la base de datos central PostgreSQL:
   - **Bifurcación (Conflicto detectado):** Pasa a `RESOLVIENDO_CONFLICTO` (aplicación de política determinista *Last-Write-Wins* o registro en auditoría para arbitraje manual).
   - **Bifurcación (Sin conflicto):** Pasa directamente a `CONSOLIDANDO`.
6. **`CONSOLIDADO / PERSISTIDO`:** La transacción se aplica con éxito en PostgreSQL (`COMMIT`) y el servidor responde `HTTP 200 (ACK)`.
7. **`SINCRONIZADO_LOCAL`:** La app móvil recibe el acuse, marca los registros locales como `SINCRONIZADO` y libera memoria.
8. **`HISTÓRICO` (Concluido):** Estado terminal del ciclo de sincronización.

---

## 2. Análisis del Diagrama de Tiempos (Timing Diagram)

El diagrama de tiempos descompone la interacción temporal a lo largo de 4 líneas de vida (carriles/tracks) durante un ciclo completo de trabajo en campo y sincronización:

1. **Track 1: `APP MÓVIL (SQLITE LOCAL)`**
   - *En espera / Online* (Nivel bajo)
   - *Captura offline en SQLite* (`T > 0 min`) (Nivel alto)
   - *Empaquetando lote JSON* (`{1 - 3 seg}`) (Nivel medio)
   - *Actualizando registros a SINCRONIZADO* (`{< 1 seg}`) (Nivel alto)
   - *En reposo / Sincronizado* (Nivel bajo)

2. **Track 2: `CONECTIVIDAD / RED`**
   - *Sin cobertura (Offline)* (`T > 0 min`) (Nivel bajo)
   - *Señal detectada (Detección de red)* (`{1 - 2 seg}`) (Nivel medio)
   - *Canal HTTPS activo (Transmisión)* (`{1 - 4 seg}`) (Nivel alto)
   - *Canal en espera (Inactivo)* (Nivel bajo)

3. **Track 3: `BACKEND API / SYNC WORKER`**
   - *Inactivo / En escucha* (Nivel bajo)
   - *Validación JWT e idempotencia* (`{< 1 seg}`) (Nivel alto)
   - *Resolución de concurrencia y reglas de negocio* (`{1 - 3 seg}`) (Nivel medio)
   - *Emisión de confirmación (HTTP 200 ACK)* (`{< 1 seg}`) (Nivel alto)
   - *En espera* (Nivel bajo)

4. **Track 4: `BASE DE DATOS CENTRAL (POSTGRESQL)`**
   - *En reposo* (Nivel bajo)
   - *Transacción abierta (BEGIN)* (`{< 0.5 seg}`) (Nivel alto)
   - *Persistencia atómica y auditoría (COMMIT)* (`{1 - 2 seg}`) (Nivel alto)
   - *Concluido / Persistido* (Nivel bajo)

---

## 3. Entregables
- Scripts de renderizado vectorial y PNG 2x: `scripts/generate_cu41_state_timing.py`.
- Formato nativo Draw.io: `docs/diagramas/diagramas_cu41_estado_tiempo.drawio`.
- Vistas previas en alta resolución:
  - `diag_estado_cu41.png` / `.svg`
  - `diag_tiempo_cu41.png` / `.svg`
