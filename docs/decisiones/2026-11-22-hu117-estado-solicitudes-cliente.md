# Decisión de Diseño: HU117 – Consultar estado de solicitudes enviadas

## Contexto y Alcance
La HU117 permite que el **CLIENTE consulte las solicitudes que él mismo realizó a la constructora, visualice su estado actual y la respuesta de la empresa constructora**, junto con sus evidencias/fotografías si fueron adjuntadas.

### Diagnóstico de la situación previa:
1. En la versión previa de CU30 (2026-11-21), se mapeó de manera provisional la consulta de solicitudes a `obras.t_incidencia` en `incidencia_repos.py`.
2. Esta aproximación presenta incompatibilidades estructurales:
   - `t_incidencia` pertenece al ciclo técnico de fallas de obra (CU19 / HU73), con roles operativos (albañiles, electricistas, jefes de obra, órdenes de trabajo).
   - Sus restricciones `CHECK (estado IN ('ABIERTA', 'ASIGNADA', 'EN_PROCESO', 'PENDIENTE_VALIDACION', 'RESUELTA', 'CERRADA'))` no corresponden al ciclo de vida de solicitudes de clientes (`PENDIENTE`, `EN_PROCESO`, `ATENDIDA`, `RECHAZADA`).
   - `t_incidencia` no posee campos para registrar la `respuesta` de la constructora ni la `fecha_respuesta`.
   - `incidencia_repos.listar_solicitudes_cliente_cu30` no devolvía código de unidad, ni respuesta, ni fecha de atención, ni evidencias.
   - No existía endpoint para consultar el detalle de una solicitud (`GET /api/crm/cliente/solicitudes/{id_solicitud}`).
   - No existía mecanismo para registrar solicitudes de cliente ni registrar la respuesta de la constructora.
   - En el frontend (`panel.html`), la tarjeta de solicitudes no mostraba la unidad asociada, carecía de botón `[Ver detalle]`, no mostraba la respuesta de la constructora ni evidencias.

## Separación Estricta de Responsabilidades
- **HU114:** Consulta de avance físico de obra y unidad (`t_avance_obra`, `avances.service.ts`).
- **HU115:** Consulta de fotografías actualizadas de la unidad (`t_unidad_fotografia`, carga por personal técnico).
- **HU116:** Comunicaciones oficiales unidireccionales de la constructora al cliente (`obras.notificacion`).
- **HU117:** Consultas/solicitudes realizadas por el cliente sobre su unidad, seguimiento de estado (`PENDIENTE`, `EN_PROCESO`, `ATENDIDA`, `RECHAZADA`), respuesta oficial de la empresa y evidencias adjuntas.
- **NO CHAT:** No es un chat ni mensajería de conversación. El cliente consulta la solicitud y la respuesta recibida.

## Capas y Contratos

### 1. Base de datos (`obras.t_cliente_solicitud`)
Se define una tabla aditiva dedicada:
- `id_solicitud` (SERIAL PRIMARY KEY)
- `id_cliente` (INTEGER NOT NULL FK -> `obras.t_crm_cliente(id_cliente)`)
- `id_usuario` (INTEGER NOT NULL FK -> `obras.t_usuario(id_usuario)`) -- cliente autor
- `id_empresa` (INTEGER NOT NULL FK -> `obras.t_empresa(id_empresa)`) -- tenant
- `id_obra` (INTEGER NOT NULL FK -> `obras.t_obra(id_obra)`)
- `id_unidad` (INTEGER NULL FK -> `obras.t_unidad_construccion(id_unidad)`)
- `titulo` (VARCHAR(200) NOT NULL)
- `descripcion` (TEXT NOT NULL)
- `estado` (VARCHAR(20) NOT NULL DEFAULT 'PENDIENTE' CHECK (estado IN ('PENDIENTE', 'EN_PROCESO', 'ATENDIDA', 'RECHAZADA')))
- `respuesta` (TEXT NULL)
- `id_usuario_respuesta` (INTEGER NULL FK -> `obras.t_usuario(id_usuario)`) -- personal constructora
- `id_fotografia_evidencia` (INTEGER NULL FK -> `obras.t_unidad_fotografia(id_fotografia)`) -- reutilización de fotografías de unidad como evidencia
- `fecha_creacion` (TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)
- `fecha_actualizacion` (TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)
- `fecha_respuesta` (TIMESTAMPTZ NULL)

### 2. Repositorio (`crm_repos.py`)
Se centraliza el acceso a datos en `crm_repos.py`:
- `listar_solicitudes_cliente_cu30(id_cliente, id_usuario, id_empresa)`:
  Consulta `t_cliente_solicitud` unida con `t_unidad_construccion` y `t_obra`, filtrando estrictamente por `id_cliente = %s`, `id_usuario = %s` e `id_empresa = %s`.
  Orden: `fecha_creacion DESC, id_solicitud DESC`.
- `obtener_solicitud_cliente_cu30(id_cliente, id_usuario, id_solicitud, id_empresa)`:
  Obtiene el detalle completo de la solicitud garantizando pertenencia de cliente y tenant. Si la solicitud pertenece a otro cliente u otro tenant, retorna `None`.
  Incluye metadatos de la evidencia adjunta si `id_fotografia_evidencia` está presente.
- `crear_solicitud_cliente_db(id_cliente, id_usuario, id_empresa, id_obra, id_unidad, titulo, descripcion)`:
  Inserta una nueva solicitud en estado `PENDIENTE`.
- `responder_solicitud_cliente_db(id_solicitud, id_empresa, estado, respuesta, id_usuario_respuesta, id_fotografia_evidencia)`:
  Actualiza el estado (`EN_PROCESO`, `ATENDIDA`, `RECHAZADA`), la respuesta y la fecha de atención.

### 3. Servicios (`crm_services.py`)
- `listar_solicitudes_cliente_autenticado(token: dict)`:
  Resuelve identidad de cliente (`id_cliente, id_usuario, id_empresa`) desde el JWT usando `_contexto_cliente_cu30` y delega a `crm_repos`.
- `obtener_detalle_solicitud_cliente_autenticado(id_solicitud: int, token: dict)`:
  Resuelve identidad del cliente y valida pertenencia. Si no existe o pertenece a otro cliente/tenant, lanza error 404.
- `registrar_solicitud_cliente_autenticado(data: dict, token: dict, ip: str = None)`:
  Valida campos obligatorios (`titulo`, `descripcion`), valida que la unidad indicada esté asociada al cliente en `t_crm_cliente_unidad`, deriva la obra y tenant, persiste e inserta en bitácora.
- `responder_solicitud_constructora(id_solicitud: int, data: dict, token: dict, ip: str = None)`:
  Exige rol constructora (`ADMINISTRADOR`, `ADMINISTRADOR_EMPRESA`, `JEFE DE OBRA`, `RESPONSABLE`), valida que la solicitud pertenezca al tenant de la constructora, aplica transición de estado y guarda respuesta.

### 4. Rutas (`crm_routes.py`)
- `GET /api/crm/cliente/solicitudes`: Exige rol `CLIENTE`.
- `GET /api/crm/cliente/solicitudes/{id_solicitud}`: Exige rol `CLIENTE`.
- `POST /api/crm/cliente/solicitudes`: Exige rol `CLIENTE` (status 201).
- `POST /api/crm/solicitudes/{id_solicitud}/responder`: Exige roles constructora (`ADMINISTRADOR`, `ADMINISTRADOR_EMPRESA`, `JEFE DE OBRA`, `RESPONSABLE`).

### 5. Frontend Cliente (`crm.service.ts`, `panel.ts`, `panel.html`)
- `crm.service.ts`:
  - Modelo `SolicitudClienteCu30` completo (con `codigo_unidad`, `nombre_obra`, `respuesta`, `fecha_respuesta`, `evidencias`).
  - Métodos `listarSolicitudesCliente()`, `obtenerDetalleSolicitud(id)` y `registrarSolicitudCliente(payload)`.
- `panel.ts`:
  - Gestión de estado: `solicitudesCliente`, `solicitudSeleccionada`, `mostrarModalDetalleSolicitud`, `cargandoDetalleSolicitud`, `errorDetalleSolicitud`.
  - Acciones: `abrirDetalleSolicitud(sol)`, `cerrarModalDetalleSolicitud()`.
- `panel.html`:
  - Tarjetas de lista mostrando Título, Unidad (`UNI-000009`), Fecha y Estado badge.
  - Botón `[Ver detalle]`.
  - Modal de Detalle con layout limpio: Asunto, Unidad y Obra, Fecha de creación, Estado badge, Descripción del cliente, Bloque destacado "Respuesta de la Constructora" (con fecha de respuesta y texto de la respuesta), galería/preview de evidencias si existen.
  - Sin botones de chat ni respuesta por parte del cliente.

### 6. Frontend Constructora (`crm.service.ts`, `crm.ts`, `crm.html`)
- `crm.service.ts`:
  - Método `listarSolicitudesConstructora(filtros)` (`GET /api/crm/solicitudes`).
  - Método `responderSolicitudConstructora(idSolicitud, payload)` (`POST /api/crm/solicitudes/{id_solicitud}/responder`).
- `crm.ts`:
  - Pestaña `pestanaActiva = 'solicitudes'`.
  - Estado reactivo para `solicitudesConstructora`, conteo de pendientes, filtros de búsqueda y estado.
  - Gestión de modal para responder con validación de flujo de estados: `PENDIENTE -> EN_PROCESO -> ATENDIDA` o `RECHAZADA`.
  - Exigencia de texto de respuesta si el estado es `ATENDIDA` o `RECHAZADA`.
- `crm.html`:
  - Pestaña "📋 Solicitudes de Clientes" con badge de pendientes.
  - Vista de tabla con filtros, badges de estado y botón "Gestionar / Responder".
  - Modal de gestión mostrando los datos del cliente, unidad, obra y solicitud, y formulario para asignar estado y redactar la respuesta oficial.


## Seguridad y Aislamiento Multi-Tenant
1. El `id_cliente`, `id_usuario` e `id_empresa` se derivan exclusivamente del JWT validado.
2. Un cliente no puede consultar solicitudes de otro cliente: si envía el `id_solicitud` de otro cliente en la URL, el repositorio filtra por `id_cliente = %s AND id_empresa = %s` y el servicio responde HTTP 404.
3. Si el cliente registra una solicitud para una unidad que no le pertenece, se rechaza con error 400.

## Validación Prevista
1. Pruebas unitarias para:
   - Cliente consulta sus propias solicitudes.
   - Cliente consulta el detalle de su solicitud.
   - Cliente recibe 404 al intentar consultar solicitud de otro cliente o de otro tenant.
   - Validación de estados `PENDIENTE`, `EN_PROCESO`, `ATENDIDA`, `RECHAZADA`.
   - Visualización de respuesta y fecha de atención cuando está atendida.
   - No regresión en HU114, HU115 y HU116.
2. Compilación y suite completa de pruebas.
