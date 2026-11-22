# CU31: Gestionar Comercialización de Unidades Inmobiliarias — Implementación Completa Backend (HU143, HU144, HU145, HU146)

**Fecha:** 2026-11-22  
**Autores:** Equipo de Arquitectura OBRATEC / Antigravity  
**Estado:** Implementado y Validado (Backend Completo: HU143, HU144, HU145, HU146)  
**Historias de Usuario cubiertas:** HU143, HU144, HU145, HU146  
**Caso de Uso:** CU31 (Gestionar comercialización de unidades inmobiliarias)  
**Módulo SaaS / Plan:** `crm` (`CRM y clientes`)  
**Prefijo HTTP:** `/api/comercializacion`  

---

## 1. Contexto y Alcance Completo

Sobre la base de datos y estructura de la Fase 1, se completa la implementación backend del **CU31 — Gestionar comercialización de unidades inmobiliarias**, abarcando todas sus historias de usuario sin alterar el ciclo constructivo (`obras.t_unidad_construccion.estado`) ni romper CU12 (Unidades de Construcción) o CU21 (CRM).

### Historias de Usuario Implementadas:
1. **HU143 — Publicar y actualizar unidades inmobiliarias:**
   - Publicación y despublicación comercial (`publicado_comercial`).
   - Actualización de `precio_venta`, `moneda_comercial` (`BOB`, `USD`) y `descripcion_comercial`.
   - Gestión completa de galería fotográfica por unidad (`obras.t_unidad_fotografia`): listar, subir con validación binaria (magic bytes y MIME `image/jpeg`, `image/png`, `image/webp`, límite 10 MB), marcar como principal, eliminar y servir archivo protegido por empresa y contra *path traversal*.
   - Registro automático de cambios significativos en `obras.t_unidad_historial_comercial`.
2. **HU144 — Registrar reservas de unidades inmobiliarias:**
   - Registro atómico y transaccional de reservas para clientes existentes (`obras.t_crm_cliente`).
   - Validación cruzada de pertenencia a la misma empresa tanto de la unidad (`unidad → estructura → obra → empresa`) como del cliente (`t_crm_cliente.id_empresa`).
   - Bloqueo pesimista (`FOR UPDATE`) y validación de unicidad para impedir dobles reservas o reserva de unidades vendidas/no disponibles.
   - Persistencia de `monto_reserva`, `monto_pactado`, `fecha_vencimiento_reserva` e `id_usuario_registro` en `obras.t_crm_cliente_unidad`.
   - Transición automática a `estado_comercial = 'RESERVADA'` y registro en `obras.t_unidad_historial_comercial` (`tipo_evento = 'RESERVA'`).
3. **HU145 — Controlar disponibilidad y estado comercial de unidades:**
   - Máquina de estados comercial estricta entre `DISPONIBLE`, `RESERVADA`, `VENDIDA` y `NO_DISPONIBLE`.
   - Cancelación/liberación transaccional de reservas (`RESERVADA → DISPONIBLE`), sincronizando `t_crm_cliente_unidad` (`estado_asociacion = 'CANCELADO'`) e historial (`tipo_evento = 'CANCELACION'`).
   - Confirmación transaccional de ventas (`RESERVADA/DISPONIBLE → VENDIDA`), sincronizando `t_crm_cliente_unidad` (`estado_asociacion = 'VENDIDO'`) e historial (`tipo_evento = 'VENTA'`).
   - Listado con filtros avanzados y endpoint de resumen/KPIs comerciales del inventario.
4. **HU146 — Consultar historial comercial de unidades:**
   - Consulta cronológica detallada de todos los eventos comerciales de la unidad (`PUBLICACION`, `DESPUBLICACION`, `ACTUALIZACION_PRECIO`, `ACTUALIZACION_COMERCIAL`, `FOTOGRAFIA_AGREGADA`, `FOTOGRAFIA_ELIMINADA`, `RESERVA`, `CANCELACION`, `VENTA`, `CAMBIO_ESTADO`), incluyendo cliente, usuario responsable, fechas, montos y transición de estados.

---

## 2. Arquitectura por Capas y Patrones

Se preserva estrictamente el patrón `routes → services → repos → PostgreSQL`:

### A. Capa de Rutas (`backend/app/routes/comercializacion_routes.py`)
- Prefijo `/api/comercializacion` registrado en `planes_catalog.py` bajo el módulo `crm`.
- Control de acceso RBAC compatible con `ADMINISTRADOR`, `ADMINISTRADOR_EMPRESA` y `JEFE DE OBRA` mediante permisos del módulo CRM (`Visualizar_clientes`, `Registrar_clientes`, `Modificar_clientes`, `Gestionar_comercializacion`).
- Endpoints organizados por historia de usuario:
  - **HU143:**
    - `PATCH /api/comercializacion/unidades/{id_unidad}`
    - `PATCH /api/comercializacion/unidades/{id_unidad}/publicacion`
    - `GET /api/comercializacion/unidades/{id_unidad}/fotografias`
    - `POST /api/comercializacion/unidades/{id_unidad}/fotografias`
    - `PATCH /api/comercializacion/unidades/{id_unidad}/fotografias/{id_fotografia}/principal`
    - `DELETE /api/comercializacion/unidades/{id_unidad}/fotografias/{id_fotografia}`
    - `GET /api/comercializacion/unidades/{id_unidad}/fotografias/{id_fotografia}/archivo`
  - **HU144:**
    - `POST /api/comercializacion/unidades/{id_unidad}/reservas`
  - **HU145:**
    - `GET /api/comercializacion/unidades`
    - `GET /api/comercializacion/resumen`
    - `GET /api/comercializacion/unidades/{id_unidad}`
    - `GET /api/comercializacion/unidades/{id_unidad}/disponibilidad`
    - `PATCH /api/comercializacion/unidades/{id_unidad}/estado`
    - `POST /api/comercializacion/unidades/{id_unidad}/cancelar-reserva`
    - `POST /api/comercializacion/unidades/{id_unidad}/confirmar-venta`
  - **HU146:**
    - `GET /api/comercializacion/unidades/{id_unidad}/historial`

### B. Capa de Servicios (`backend/app/services/comercializacion_services.py`)
- **Resolución segura de Tenant (`_resolver_empresa`):**
  - Nunca confía en `id_empresa` enviado por el frontend para usuarios de empresa; utiliza exclusivamente `token['id_empresa']`.
  - Solo el rol global `ADMINISTRADOR` puede especificar `id_empresa` tras validar su existencia en `obras.t_empresa`.
- **Seguridad de Archivos y Prevención de Path Traversal:**
  - Validación de extensión (`.jpg`, `.jpeg`, `.png`, `.webp`), tipo MIME y *magic bytes* binarios (`\xff\xd8\xff` para JPEG, `\x89PNG\r\n\x1a\n` para PNG, `RIFF....WEBP` para WEBP).
  - Sanitización del nombre de archivo original con `Path(filename).name` y almacenamiento con identificador único UUID.
  - Verificación mediante `.resolve()` de que toda ruta de lectura o eliminación de fotografías esté estrictamente contenida dentro del directorio raíz `backend/uploads/comercializacion`.
- **Máquina de Estados Comercial:**
  - `DISPONIBLE`: Puede pasar a `RESERVADA` (vía flujo de reserva con cliente), `VENDIDA` (vía flujo de venta con cliente) o `NO_DISPONIBLE`.
  - `RESERVADA`: Solo puede pasar a `DISPONIBLE` (cancelando la reserva activa) o a `VENDIDA` (confirmando la venta). No puede forzarse a `DISPONIBLE` ni `NO_DISPONIBLE` si mantiene una reserva activa sin cancelar.
  - `NO_DISPONIBLE`: Puede rehabilitarse a `DISPONIBLE` siempre que no posea reserva o venta activa en CRM.
  - `VENDIDA`: Estado terminal comercial; bloquea reversiones directas para preservar la integridad de ventas cerradas.

### C. Capa de Repositorio (`backend/app/repos/comercializacion_repos.py`)
- **Transacciones Atómicas:**
  - Las operaciones compuestas (`registrar_reserva_transaccional`, `cancelar_reserva_transaccional`, `confirmar_venta_transaccional`, `actualizar_unidad_comercial_transaccional`) utilizan una única conexión PostgreSQL con `FOR UPDATE` sobre la unidad, ejecutando `conn.commit()` solo al completar todos los pasos (`t_unidad_construccion`, `t_crm_cliente_unidad`, `t_unidad_historial_comercial`) y `conn.rollback()` ante cualquier excepción.

---

## 3. Validación y Pruebas Integrativas

Se definen **3 pruebas integrativas clave** en `backend/tests/test_cu31_comercializacion.py`:
1. **Reserva exitosa + cambio a `RESERVADA` + historial (`test_1_reserva_exitosa_cambio_estado_e_historial`):**
   - Verifica que al reservar una unidad disponible con un cliente de la misma empresa se actualice el estado comercial a `RESERVADA`, se persista la asociación `RESERVADO` en `t_crm_cliente_unidad` con `monto_reserva`, `fecha_vencimiento_reserva` e `id_usuario_registro`, y se registre el evento `RESERVA` en `t_unidad_historial_comercial` de forma atómica.
2. **Doble reserva o acceso de otro tenant rechazado (`test_2_doble_reserva_y_acceso_otro_tenant_rechazado`):**
   - Verifica que intentar reservar una unidad ya reservada/vendida sea rechazado con código 409 (`ComercializacionError`), que intentar reservar con un cliente de otra empresa o desde un token de otra empresa sea rechazado (403/404) sin confiar en `id_empresa` externo, y que ante fallo se ejecute `rollback`.
3. **Cancelación/venta + sincronización correcta con CRM e historial (`test_3_cancelacion_y_venta_sincronizacion_crm_e_historial`):**
   - Verifica el ciclo completo de liberación de reserva (`RESERVADA → DISPONIBLE`, `t_crm_cliente_unidad → CANCELADO`, evento `CANCELACION` en historial) y confirmación de venta (`RESERVADA → VENDIDA`, `t_crm_cliente_unidad → VENDIDO`, evento `VENTA` en historial), además de bloquear estados inconsistentes (como revertir una unidad `VENDIDA` a `DISPONIBLE`).

---

## 4. Aplicación de Migración en Base de Datos Configurada (`obras`)

- Se detectó que `backend/database/20261122_cu31_fase1_comercializacion.sql` estaba preparada en el repositorio pero no había sido aplicada aún en la base de datos configurada (`obras`), provocando `UndefinedColumn: column u.estado_comercial does not exist` y `column u.publicado_comercial does not exist` (HTTP 500) al consultar `GET /api/comercializacion/unidades` y `GET /api/comercializacion/resumen`.
- Se completó la migración con una sincronización idempotente de las asociaciones reales existentes en `obras.t_crm_cliente_unidad` (`RESERVADO → RESERVADA`, `VENDIDO/ENTREGADO → VENDIDA` y `precio_venta` desde `monto_pactado` cuando `precio_venta IS NULL`) y se aplicó transaccionalmente sobre `obras`.
