# Decisión Arquitectónica: HU117 – Consultar estado de solicitudes enviadas (Frontend Flutter)

**Fecha:** 2026-11-23  
**Estado:** Aprobada / En implementación  
**Contexto:** CU30 – Consultar proyectos y unidades como cliente (Etapa 5 - HU117 Final)  

---

## 1. Contexto y Objetivos

Habiendo implementado la navegación base de `CLIENTE` (Etapa 1), avance físico (HU114), fotografías de unidad (HU115) y comunicaciones directas (HU116), se aborda la última historia de usuario de CU30: **HU117 – Consultar estado de solicitudes enviadas**.

Flujo del usuario:
```text
CLIENTE (autenticado)
  └── HomeScreen ("Mis Proyectos y Unidades")
        └── ClienteUnidadesScreen (Portal Cliente)
              ├── Acceso directo: "Mis solicitudes" (con badge HU117)
              │     └── ClienteSolicitudesScreen (listado)
              │           ├── Selector/Filtro por estado (opcional o vista completa)
              │           ├── Tarjetas con: título, obra, unidad, fecha, badge de estado
              │           └── Tap en tarjeta → ClienteSolicitudDetalleScreen
              │                 ├── Cabecera con datos de la solicitud y estado
              │                 ├── Obra y Unidad inmobiliaria vinculada
              │                 ├── Descripción del requerimiento enviado
              │                 ├── Respuesta oficial de la constructora (si existe)
              │                 ├── Fecha de respuesta (si existe)
              │                 └── Aviso claro si aún no ha sido respondida
              └── Estados de carga, vacío y error con reintento
```

---

## 2. Contratos y Endpoints del Backend

Se verificaron en `backend/app/routes/crm_routes.py`, `backend/app/services/crm_services.py` y `backend/app/repos/crm_repos.py`:

1. **Listado de solicitudes del cliente:**
   - **Método HTTP:** `GET`
   - **Ruta:** `/api/crm/cliente/solicitudes`
   - **Autenticación:** Bearer Token JWT (Rol `CLIENTE`).
   - **Validación backend:** Resuelve identidad (`id_cliente`, `id_usuario`) y tenant (`id_empresa`) desde el token.
   - **Campos devueltos:** `id_solicitud`, `id_cliente`, `id_usuario`, `id_empresa`, `id_obra`, `nombre_obra`, `codigo_obra`, `id_unidad`, `codigo_unidad`, `tipo_unidad`, `titulo`, `descripcion`, `estado`, `respuesta`, `fecha_creacion`, `fecha_respuesta`.

2. **Detalle de solicitud del cliente:**
   - **Método HTTP:** `GET`
   - **Ruta:** `/api/crm/cliente/solicitudes/{id_solicitud}`
   - **Autenticación:** Bearer Token JWT (Rol `CLIENTE`).
   - **Validación backend:** Si `id_solicitud` no pertenece a `id_cliente` o `id_empresa`, retorna 404 (aislamiento seguro).
   - **Campos devueltos:** Mismos campos que el listado, más metadatos de `evidencia_fotografia` si estuviera asociada.

---

## 3. Estados Oficiales y Representación Semántica

Los 4 estados oficiales del backend son:
1. `PENDIENTE`: Color Ámbar (`Color(0xFFF59E0B)` / `0xFFFFFBEB`), icono `hourglass_top_rounded`.
2. `EN_PROCESO`: Color Azul/Sky (`Color(0xFF0284C7)` / `0xFFF0F9FF`), icono `sync_rounded`.
3. `ATENDIDA`: Color Esmeralda/Verde (`Color(0xFF10B981)` / `0xFFECFDF5`), icono `check_circle_rounded`.
4. `RECHAZADA`: Color Rojo (`Color(0xFFEF4444)` / `0xFFFEF2F2`), icono `cancel_rounded`.

---

## 4. Capas y Responsabilidades

1. **Capa de Servicios (`CrmService` / `mobile/lib/services/crm_service.dart`):**
   - Método `listarSolicitudesCliente()`: Invoca `GET /api/crm/cliente/solicitudes`.
   - Método `obtenerDetalleSolicitudCliente(int idSolicitud)`: Invoca `GET /api/crm/cliente/solicitudes/{id_solicitud}`.
2. **Capa de Presentación:**
   - **`ClienteUnidadesScreen` (`mobile/lib/screens/cliente_unidades_screen.dart`):**
     - Añade tarjeta de acceso directo a **"Mis solicitudes"** con badge `HU117`.
   - **`ClienteSolicitudesScreen` (`mobile/lib/screens/cliente_solicitudes_screen.dart`):**
     - Listado de solicitudes del cliente, pull-to-refresh, estados de carga, vacío y error.
   - **`ClienteSolicitudDetalleScreen` (`mobile/lib/screens/cliente_solicitud_detalle_screen.dart`):**
     - Detalle exhaustivo de la solicitud, descripción, obra/unidad y sección destacada de la **Respuesta oficial de la constructora**.
     - **Restricción estricta:** Solo lectura y seguimiento. Sin campos de texto, sin botones de responder, sin chat, sin creación de solicitudes desde esta HU.

---

## 5. Delimitación de Alcance

- **Incluido en esta etapa (HU117):**
  - Consulta del listado de solicitudes del cliente.
  - Consulta del detalle con respuesta oficial y fecha.
  - Indicadores visuales de estado oficial (`PENDIENTE`, `EN_PROCESO`, `ATENDIDA`, `RECHAZADA`).
  - Navegación desde el Portal Cliente.
  - Soporte de temas Claro y Oscuro.
- **Excluido deliberadamente:**
  - Respuestas o mensajes del cliente.
  - Chat o mensajería bidireccional.
  - Edición o cambio de estado de solicitudes.
  - Modificaciones en backend o base de datos.

---

## 6. Plan de Validación

1. Análisis estático con `flutter analyze` asegurando 0 issues.
2. Pruebas de widgets y unitarias en `mobile/test/cliente_solicitudes_test.dart` y suite de CU30:
   - Visualización de acceso a solicitudes en `ClienteUnidadesScreen`.
   - Navegación hacia `ClienteSolicitudesScreen`.
   - Renderizado de solicitudes con título, estado, obra, unidad y fecha.
   - Apertura de `ClienteSolicitudDetalleScreen`.
   - Visualización de respuesta oficial cuando exista y aviso cuando no exista.
   - Verificación de ausencia de controles de chat o respuesta.
   - No regresión de HU114, HU115 y HU116.
3. Ejecución de la suite completa `flutter test`.
4. Comprobación `git diff --check`.
