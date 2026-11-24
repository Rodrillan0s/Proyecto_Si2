# Plan de Implementación Aprobado: CU41 (Operación Offline y Sincronización) y CU42 (Garantías y Servicio Posventa)

**Fecha:** 2026-11-24  
**Estado:** Plan ajustado con decisiones confirmadas por el usuario — listo para iniciar Fase 3 por etapas.

---

## 1. Decisiones y Restricciones Aprobadas

| Tema | Decisión confirmada |
|---|---|
| **Categorías posventa (HU164)** | Catálogo inicial extensible: `ESTRUCTURAL`, `INSTALACION_ELECTRICA`, `INSTALACION_SANITARIA`, `ACABADOS`, `CARPINTERIA`, `IMPERMEABILIZACION`, `OTRO`. Sin clasificación automática; descripción original del cliente inmutable. |
| **Estados y transiciones (HU166)** | `REGISTRADA → CLASIFICADA → ASIGNADA → EN_ATENCION → RESUELTA → CERRADA`. Sin `RECHAZADA` (pendiente de definición de negocio). Todo cambio de estado exige registro en historial (`t_posventa_seguimiento`). No bloquear artificialmente escenarios válidos donde no se requiera clasificación previa o asignación previa (ej. `REGISTRADA → ASIGNADA` o `CLASIFICADA → EN_ATENCION` cuando el gestor atiende directamente, documentado explícitamente). |
| **Garantías (HU161 / HU163)** | `id_garantia` opcional en solicitudes posventa. Validación obligatoria: cliente asociado a la unidad (`t_crm_cliente_unidad`) y misma empresa (`id_empresa` desde JWT). No asumir duraciones estándar, no inventar fechas de vencimiento ni criterios de cobertura automática ni estados no definidos (`fecha_fin` opcional). |
| **Persistencia local Flutter (CU41)** | SQLite mediante `sqflite` (verificado en `mobile/pubspec.yaml`: no existe alternativa transaccional equivalente; solo `shared_preferences` y `path_provider`). Particionada por `(id_empresa, id_usuario)`, transaccional, resistente a cierres inesperados, con `client_operation_id` único y **sin almacenar credenciales ni tokens JWT**. |
| **Migraciones SQL** | Generar los archivos en `backend/database/` y dejarlos **preparados para revisión**; no ejecutarlos automáticamente sobre ninguna base de datos. |
| **Alcance por cliente** | **CU41:** Flutter + soporte aditivo de idempotencia en Backend. **CU42:** Backend + Angular únicamente (**no** implementar CU42 en Flutter). |
| **Protección del sistema** | No modificar CU30 ni CU31; no alterar contratos existentes de CU18 y CU19; implementación incremental por etapas con regresión tras cada etapa. |

---

## 2. Arquitectura y Alcance por Etapas (Fase 3)

### Etapa 1 — CU41 Backend (Idempotencia y marcas temporales aditivas)
- **Migración preparada (sin ejecutar):** `backend/database/20261124_cu41_offline_sync_idempotencia.sql`
  - Tabla `obras.t_sync_operacion_offline` con `UNIQUE (id_empresa, id_usuario, tipo_operacion, client_operation_id)` y columnas `fecha_ocurrencia_local`, `fecha_sincronizacion`, `id_recurso_creado`, `estado`, `respuesta_json`.
  - Columnas opcionales `NULL` en `obras.t_avance_obra` y `obras.t_incidencia`: `fecha_ocurrencia_local TIMESTAMPTZ NULL`, `fecha_sincronizacion TIMESTAMPTZ NULL`.
- **Archivos nuevos:**
  - `backend/app/repos/sync_offline_repos.py`
  - `backend/app/services/sync_offline_services.py`
  - `backend/tests/test_cu41_offline_sync.py`
- **Modificaciones mínimas (100% retrocompatibles):**
  - `backend/app/routes/avance_routes.py` y `backend/app/services/avance_services.py`: leer header opcional `Idempotency-Key` (o `client_operation_id` en body) y `fecha_ocurrencia_local`; si ya fue procesado para `(id_empresa, id_usuario, 'AVANCE_OBRA')`, retornar la respuesta almacenada sin duplicar.
  - `backend/app/routes/incidencia_routes.py` y `backend/app/services/incidencia_services.py`: mismo comportamiento opcional para `'INCIDENCIA'`.
- **Regresión Etapa 1:** `pytest tests/test_cu41_offline_sync.py tests/test_avance_services.py tests/test_incidencia_services.py tests/test_incidencia_authorization.py tests/test_security_rules.py`.

---

### Etapa 2 — CU41 Flutter (SQLite `sqflite` + Caché Offline + Motor de Sincronización + UI HU90–HU94)
- **Dependencia:** agregar `sqflite` (y `path` si es necesario) en `mobile/pubspec.yaml` (verificado que no existe alternativa SQLite/transaccional en el proyecto); para pruebas unitarias en host, `sqflite_common_ffi` en `dev_dependencies` si se requiere ejecutar SQLite en `flutter test`.
- **Esquema SQLite local (sin tokens ni contraseñas):**
  - `offline_cache(id_empresa, id_usuario, entidad, clave, payload_json, descargado_en)` con `PRIMARY KEY (id_empresa, id_usuario, entidad, clave)`.
  - `offline_queue(id_local, client_operation_id, id_empresa, id_usuario, tipo_operacion, id_obra, payload_json, fecha_ocurrencia_local, estado, intentos, ultimo_error, id_recurso_remoto, fecha_sincronizacion)` con `UNIQUE (id_empresa, id_usuario, tipo_operacion, client_operation_id)`.
- **Archivos nuevos en `mobile/lib/`:**
  - `services/offline_db_service.dart` (inicialización SQLite, transacciones atómicas, particionamiento estricto por empresa/usuario).
  - `services/offline_sync_service.dart` (`ChangeNotifier` + `connectivity_plus` + `WidgetsBindingObserver` para reanudar; lock anti-concurrencia; reintentos ante fallos de red/5xx; errores 4xx marcados como `ERROR` sin bloquear la cola; nunca elimina registros hasta recibir 2xx del backend).
  - `screens/sync_status_screen.dart` (HU94: filtros Pendientes / Sincronizados / Con error, detalle de cada registro, sincronización manual y reintento).
  - `widgets/offline_banner.dart` (HU90: indicador claro de modo sin conexión y fecha de copia local).
  - `mobile/test/offline_sync_test.dart`.
- **Modificaciones mínimas en `mobile/lib/`:**
  - `pubspec.yaml`, `main.dart`, `screens/home_screen.dart` (acceso a estado de sincronización solo para roles operativos).
  - `screens/proyectos_screen.dart` y `screens/proyecto_detalle_screen.dart` (HU90: caché local y consulta offline de obras autorizadas).
  - `services/avance_service.dart` y `screens/avances_obra_screen.dart` (HU91: registro online y encolado offline con `client_operation_id` y `fecha_ocurrencia_local`).
  - `services/incidencia_service.dart`, `screens/incidencias_screen.dart` y `screens/incidencia_form_screen.dart` (HU92: consulta offline de caché y registro offline encolado).
- **Regresión Etapa 2:** `flutter analyze` y `flutter test`.

---

### Etapa 3 — CU42 Backend (Garantías y Servicio Posventa, HU161–HU168)
- **Migración preparada (sin ejecutar):** `backend/database/20261124_cu42_garantias_posventa.sql`
  - `obras.t_garantia_inmobiliaria`: `id_garantia`, `id_empresa`, `id_unidad`, `codigo`, `tipo_garantia`, `descripcion`, `fecha_inicio`, `fecha_fin NULL`, `observaciones NULL`, `id_usuario_registro`, `creado_en` (sin asumir duración estándar ni criterios automáticos de cobertura).
  - `obras.t_solicitud_posventa`: `id_solicitud_posventa`, `id_empresa`, `id_unidad`, `id_cliente`, `id_garantia NULL`, `titulo`, `descripcion` (inmutable), `categoria NULL` (validada contra catálogo extensible), `estado` (`REGISTRADA`, `CLASIFICADA`, `ASIGNADA`, `EN_ATENCION`, `RESUELTA`, `CERRADA`), `id_responsable NULL`, `id_usuario_creacion`, `creado_en`, `actualizado_en`.
  - `obras.t_posventa_seguimiento`: historial append-only (`id_seguimiento`, `id_solicitud_posventa`, `id_usuario`, `accion`, `estado_anterior`, `estado_nuevo`, `observacion`, `creado_en`).
- **Archivos nuevos:**
  - `backend/app/repos/garantia_posventa_repos.py`
  - `backend/app/services/garantia_posventa_services.py`
  - `backend/app/routes/garantia_posventa_routes.py`
  - `backend/tests/test_cu42_garantias_posventa.py`
- **Modificación mínima:**
  - `backend/app/__init__.py` (registrar `garantia_posventa_routes.router` bajo `/api/posventa`).
- **Endpoints (`/api/posventa`):**
  - `POST /api/posventa/garantias` (HU161) y `GET /api/posventa/garantias` (HU162).
  - `POST /api/posventa/solicitudes` (HU163 — `CLIENTE`, valida `t_crm_cliente_unidad` y misma empresa; `id_garantia` opcional).
  - `PATCH /api/posventa/solicitudes/{id}/clasificar` (HU164 — categoría del catálogo extensible, sin modificar `titulo`/`descripcion`).
  - `PATCH /api/posventa/solicitudes/{id}/asignar` (HU165 — responsable autorizado de la misma empresa).
  - `PATCH /api/posventa/solicitudes/{id}/atencion` (HU166 — transición válida y registro obligatorio en `t_posventa_seguimiento`).
  - `GET /api/posventa/solicitudes` y `GET /api/posventa/solicitudes/{id}` (HU167 — seguimiento por rol/tenant).
  - `GET /api/posventa/unidades/{id_unidad}/historial` (HU168 — historial consolidado de garantías, solicitudes y atenciones).
- **Regresión Etapa 3:** `pytest tests/test_cu42_garantias_posventa.py tests/test_crm_cliente_unidades.py tests/test_crm_cliente_hu115_hu117.py tests/test_cu31_comercializacion.py tests/test_security_rules.py`.

---

### Etapa 4 — CU42 Frontend Web (Angular únicamente)
- **Archivos nuevos:**
  - `frontend/src/app/services/posventa.service.ts`
  - `frontend/src/app/pages/posventa/posventa.{ts,html,css,spec.ts}`
  - `frontend/tsconfig.posventa.spec.json`
- **Modificaciones mínimas:**
  - `frontend/src/app/app.routes.ts` (ruta lazy `/posventa`).
  - `frontend/src/app/layouts/admin-layout/navegacion.ts` (ítem **Garantías y Posventa** respetando roles/permisos).
  - `frontend/package.json` (script `test:posventa`).
- **Funcionalidades UI:**
  - **Vista Empresa (Admin / Admin Empresa / Jefe de Obra / Supervisor / Responsables):** registro y consulta de garantías por unidad (HU161/162), bandeja de solicitudes posventa con clasificación (HU164), asignación de responsable (HU165), gestión de atención y bitácora de seguimiento (HU166/167), e historial consolidado por unidad (HU168).
  - **Vista Cliente (`CLIENTE`):** consulta de garantías de sus unidades (HU162), registro de solicitud posventa sobre sus unidades con garantía opcional (HU163), seguimiento de sus solicitudes con responsable y línea de tiempo (HU167), e historial de su unidad (HU168).
- **Regresión Etapa 4:** `npm run test:posventa`, `npm run test:pagos`, `npm run test:cu30`, `npm run test:cu31` y `npm run build`.

---

## 3. Reglas pendientes de definición (documentadas sin asumir)
- Transición `RECHAZADA` en solicitudes posventa (no se implementa hasta aprobación de sus reglas).
- Estados automáticos y criterios de cobertura/vigencia de garantías (`VIGENTE` / `VENCIDA` / `ANULADA`): no se calcularán ni bloquearán solicitudes automáticamente hasta definición formal.
