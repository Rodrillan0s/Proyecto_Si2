# CU31: Gestionar Comercialización de Unidades Inmobiliarias — Implementación Frontend (HU143, HU144, HU145, HU146)

**Fecha:** 2026-11-22  
**Autores:** Equipo de Arquitectura OBRATEC / Antigravity  
**Estado:** Propuesto e Implementado (Frontend Angular Completo)  
**Historias de Usuario cubiertas:** HU143, HU144, HU145, HU146  
**Caso de Uso:** CU31 (Gestionar comercialización de unidades inmobiliarias)  
**Módulo SaaS / Plan:** `crm` (`CRM y clientes`)  
**Ruta Frontend:** `/comercializacion`  
**Endpoints Backend Consumidos:** `/api/comercializacion/*`  

---

## 1. Contexto y Objetivos

Con el backend de CU31 completamente implementado y verificado en la Fase 1 y Fase 2, se implementa la interfaz de usuario en Angular para la gestión integral de la comercialización de unidades inmobiliarias. La solución reutiliza estrictamente los contratos reales del backend, respetando los estándares visuales de OBRATEC (Tailwind CSS, diseño profesional inspirado en Procore, tema claro/oscuro, badges semánticos, loaders reactivos y modales interactivos).

### Historias de Usuario Satisfechas:
1. **HU143 — Publicar y actualizar unidades inmobiliarias:**
   - Visualización de precios, moneda (`BOB`, `USD`), estado comercial (`DISPONIBLE`, `RESERVADA`, `VENDIDA`, `NO_DISPONIBLE`) y estado constructivo físico (`PLANIFICADO`, `EN_CONSTRUCCION`, `FINALIZADO`, `SUSPENDIDO`).
   - Publicación y despublicación inmediata con switch/botón directo.
   - Modal de edición comercial para actualizar precio de venta, moneda, descripción y estado.
   - Modal de galería fotográfica: subida de archivos (validando formato `.jpg`, `.jpeg`, `.png`, `.webp` y tamaño máx. 10 MB), listado con miniaturas, eliminación y acción para marcar fotografía principal.
2. **HU144 — Registrar reservas de unidades inmobiliarias:**
   - Acción "Registrar reserva" disponible exclusivamente para unidades en estado `DISPONIBLE`.
   - Búsqueda y selección reactiva de clientes registrados en el CRM de la misma empresa (`CrmService.listarClientes`).
   - Formulario de reserva con montos (`monto_reserva`, `monto_pactado`), fecha de vencimiento (`fecha_vencimiento_reserva`) y observaciones.
   - Actualización automática de la unidad a `RESERVADA` tras confirmación y manejo de errores (409 en caso de conflicto).
3. **HU145 — Controlar disponibilidad y estado comercial de unidades:**
   - Visualización de badges diferenciados para estados comerciales y estado constructivo.
   - Acciones restringidas por máquina de estados:
     - Cancelar/liberar reserva (`RESERVADA → DISPONIBLE` con confirmación y motivo).
     - Confirmar venta (`RESERVADA/DISPONIBLE → VENDIDA` con cliente y monto).
     - Marcar no disponible / reactivar disponibilidad (`NO_DISPONIBLE ↔ DISPONIBLE`).
   - Tarjetas de resumen y KPIs comerciales (`total_unidades`, `publicadas`, `disponibles_efectivas`, `reservadas`, `vendidas`, valor de inventario) consumiendo `GET /api/comercializacion/resumen`.
4. **HU146 — Consultar historial comercial de unidades:**
   - Modal con línea de tiempo cronológica (timeline) ordenada del evento más reciente al más antiguo.
   - Detalle estructurado de cada evento: tipo de evento, estados anterior/nuevo, cliente asociado, usuario responsable, montos pactados/reserva, fecha formateada y observaciones.

---

## 2. Arquitectura Frontend Angular

### A. Capa de Servicios (`ComercializacionService`)
- Archivo: `frontend/src/app/services/comercializacion.service.ts`
- Modela estrictamente las interfaces según las respuestas de FastAPI:
  - `UnidadComercial`, `ResumenComercial`, `FotografiaUnidad`, `HistorialComercialUnidad`, `DisponibilidadUnidad`, `ReservaRequest`, `ConfirmarVentaRequest`, `ActualizarComercializacionRequest`.
- Expone métodos observables tipados hacia `/api/comercializacion`:
  - `listarUnidades(...)`, `obtenerResumen(...)`, `obtenerDetalle(...)`, `consultarDisponibilidad(...)`, `actualizarComercializacion(...)`, `cambiarPublicacion(...)`, `cambiarEstado(...)`, `registrarReserva(...)`, `cancelarReserva(...)`, `confirmarVenta(...)`, `listarFotografias(...)`, `subirFotografia(...)`, `marcarFotografiaPrincipal(...)`, `eliminarFotografia(...)`, `obtenerUrlFotografia(...)`.

### B. Componente Principal (`ComercializacionComponent`)
- Archivo: `frontend/src/app/pages/comercializacion/comercializacion.ts` (standalone component).
- Template: `frontend/src/app/pages/comercializacion/comercializacion.html`.
- Estilos: `frontend/src/app/pages/comercializacion/comercializacion.css`.
- Integración con `ContextoOperativo`, `ProyectosService` y `CrmService` para selección contextual de obra y clientes.
- Control de permisos RBAC con `AuthService` (`Visualizar_clientes`, `Modificar_clientes`).

### C. Navegación, Rutas y Matriz de Permisos RBAC
- Registro de ruta en `app.routes.ts`:
  ```typescript
  {
    path: 'comercializacion',
    loadComponent: () => import('./pages/comercializacion/comercializacion').then(m => m.ComercializacionComponent),
    canActivate: [roleGuard],
    data: { permissions: ['Visualizar_clientes', 'Registrar_obras'] }
  }
  ```
- Inclusión en `navegacion.ts` dentro de la sección `COMERCIAL & CLIENTES` con `label: 'Comercialización de Unidades'`, `route: '/comercializacion'` y `permissions: ['Visualizar_clientes', 'Registrar_obras']`.
- Sincronización de permisos en `frontend/src/app/services/auth.ts`:
  - El endpoint `/api/auth/login` retorna el objeto `usuario` con `nombre_rol` sin arreglo explícito de `permisos`, por lo que `AuthService.obtenerPermisosUsuario()` resuelve los permisos desde `MAPA_PERMISOS_POR_ROL`.
  - Se incorporan los permisos reales de CRM/Comercialización persistidos en PostgreSQL (`Visualizar_clientes`, `Registrar_clientes`, `Modificar_clientes`) en `PermisoNombre`, `PERMISOS_OFICIALES` y en `MAPA_PERMISOS_POR_ROL` para `ADMINISTRADOR`, `ADMINISTRADOR_EMPRESA` y `JEFE_DE_OBRA` (`JEFE DE OBRA`), garantizando visibilidad en el menú lateral y acceso por `roleGuard` para los tres roles autorizados.

---

## 3. Pruebas Automatizadas Frontend

Se implementa `frontend/src/app/pages/comercializacion/comercializacion.spec.ts` cubriendo 3 pruebas integrativas:
1. **Carga inicial, KPIs y filtros de búsqueda:** Carga de métricas, listado de unidades y aplicación reactiva de filtros por estado y proyecto.
2. **Registro exitoso de reserva y transición a RESERVADA:** Selección de cliente, envío de reserva y actualización del estado en la tabla.
3. **Consulta de historial cronológico y control de fotografías:** Apertura del modal de historial comercial y renderizado de la línea de tiempo.
