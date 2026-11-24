# Nota de Arquitectura: CU41 — Operación Offline y Sincronización (HU90 - HU94)

**Fecha:** 2026-11-22  
**Caso de Uso:** CU41 — Gestionar operación offline y sincronización  
**Actores:** Supervisor / Personal de Campo (Canal Móvil Flutter) | Administrador de Obra (Seguimiento Web Angular opcional)  
**Historias de Usuario Cubiertas:**
- **HU90:** Consultar información de obra sin conexión (12 SP)
- **HU91:** Registrar avances de obra sin conexión (16 SP)
- **HU92:** Registrar incidencias sin conexión (12 SP)
- **HU93:** Sincronizar automáticamente datos pendientes (32 SP)
- **HU94:** Consultar estado de sincronización (8 SP)

---

## 1. Patrón Arquitectónico y Estrategia Técnica

### 1.1 Modelo Desconectado en Cliente Móvil (Flutter + SQLite)
1. **Cache Local de Lectura (`cache_obra_local`):**
   - Cuando el dispositivo cuenta con red, descarga un snapshot ligero de las obras asignadas al supervisor (`t_obra`, `t_frente_obra`, `t_actividad_obra`, catálogo esencial).
   - Permite que el Personal de Campo consulte cronogramas y especificaciones sin requerir señal celular en faena (HU90).
2. **Cola Transaccional de Salida (`cola_pendientes_sync`):**
   - Los registros de avance físico (HU91) e incidencias técnicas con fotos locales (HU92) se insertan de inmediato en la base SQLite local con estado `PENDIENTE` y UUID local (`id_local`).
   - El usuario recibe retroalimentación inmediata sin bloqueos ni errores de timeout de red.
3. **Monitor de Estado Local (HU94):**
   - Exposición reactiva del estado del almacén local (`SINCRONIZADO`, `PENDIENTE_SYNC`, `ERROR_SYNC`) mediante badge y panel de diagnóstico en la UI móvil.

### 1.2 Mecanismo de Sincronización Automática (HU93)
1. **Detección de Conectividad:**
   - Un listener de conectividad en Flutter detecta el cambio de estado de red (`offline -> online`).
2. **Despacho Idempotente en Lote:**
   - Empaquetado de registros pendientes en formato JSON enviado a `POST /api/v1/sync/batch`.
   - Cada elemento incluye `uuid_local`, `tipo_entidad`, `payload`, `timestamp_creacion_local` y `id_empresa`.
3. **Procesamiento Atómico en Backend FastAPI:**
   - `sync_routes.py` valida la sesión JWT y pertenencia a empresa (`id_empresa`).
   - `sync_services.py` ejecuta la transacción en PostgreSQL dentro del esquema `obras`.
   - Si un registro ya fue recibido previamente (idempotencia por UUID), se descarta el duplicado y se confirma éxito.
   - Si existen discrepancias de versión (conflictos), se aplica regla de dominio *Last-Write-Wins* o se registra en `t_sincronizacion_log` para resolución manual.
4. **Confirmación y Limpieza Local:**
   - El backend retorna los IDs asignados en PostgreSQL.
   - El cliente móvil actualiza la cola SQLite a estado `SINCRONIZADO` y notifica a la interfaz gráfica.

---

## 2. Contratos y Endpoints Previstos

### `POST /api/v1/sync/batch`
- **Headers:** `Authorization: Bearer <JWT>`, `X-Empresa-Id: <id>`
- **Request Body:**
  ```json
  {
    "id_dispositivo": "uuid-movil-01",
    "fecha_envio": "2026-11-22T14:40:00Z",
    "lote": [
      {
        "id_local": "d3b07384-d113-4662-8700-111111111111",
        "tipo": "AVANCE",
        "id_obra": 12,
        "id_actividad": 45,
        "porcentaje": 35.5,
        "observaciones": "Avance de enfierradura sin conectividad",
        "fecha_registro_local": "2026-11-22T11:15:00Z"
      },
      {
        "id_local": "e4c18495-e224-4773-9811-222222222222",
        "tipo": "INCIDENCIA",
        "id_obra": 12,
        "descripcion": "Falta de suministro de cemento",
        "severidad": "ALTA",
        "fecha_registro_local": "2026-11-22T12:00:00Z"
      }
    ]
  }
  ```
- **Response Body (200 OK):**
  ```json
  {
    "estado": "COMPLETADO",
    "lote_id": 104,
    "procesados": 2,
    "errores": 0,
    "resultados": [
      {"id_local": "d3b07384...", "id_remoto": 1502, "estado": "SINCRONIZADO"},
      {"id_local": "e4c18495...", "id_remoto": 308, "estado": "SINCRONIZADO"}
    ]
  }
  ```

---

## 3. Artefactos de Modelado Generados

1. **Diagrama de Análisis de Clases (BCE Completo con Avances e Incidencias):**
   - Editable Draw.io: [`docs/diagramas/analisis_clases_cu41_offline_sync.drawio`](../diagramas/analisis_clases_cu41_offline_sync.drawio)
   - Vectorial SVG: [`docs/diagramas/analisis_clases_cu41_offline_sync.svg`](../diagramas/analisis_clases_cu41_offline_sync.svg)
   - Imagen de alta resolución: [`docs/diagramas/analisis_clases_cu41_offline_sync.png`](../diagramas/analisis_clases_cu41_offline_sync.png)
   - *Entidades modeladas:* `Form_Operacion_Offline`, `Sync_Manager_Control`, `COLA_SINCRONIZACION` (local), `AVANCE_OBRA` (`obras.t_avance_obra`), `INCIDENCIA` (`obras.t_incidencia`), `OBRA` (`obras.t_obra`) y `SINCRONIZACION_LOG` (`obras.t_sincronizacion_log`).
2. **Diagrama de Comunicación (Análisis de Robustez BCE):**
   - Editable Draw.io: [`docs/diagramas/comunicacion_cu41_offline_sync.drawio`](../diagramas/comunicacion_cu41_offline_sync.drawio)
   - Vectorial SVG: [`docs/diagramas/comunicacion_cu41_offline_sync.svg`](../diagramas/comunicacion_cu41_offline_sync.svg)
   - Imagen de alta resolución: [`docs/diagramas/comunicacion_cu41_offline_sync.png`](../diagramas/comunicacion_cu41_offline_sync.png)
3. **Diagrama de Secuencia:**
   - Editable Draw.io: [`docs/diagramas/secuencia_cu41_offline_sync.drawio`](../diagramas/secuencia_cu41_offline_sync.drawio)
   - Lifelines sincronizadas: `user`, `ui`, `sync_mgr`, `sqlite`, `router`, `service`, `t_avance_obra`, `t_incidencia`, `t_sincronizacion_log`.
