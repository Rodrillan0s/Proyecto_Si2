# Nota de Arquitectura: Resolución de conflictos de merge en Pagos SaaS e integración con rama Grover

**Fecha:** 2026-11-24  
**Solicitud y alcance:**  
Corregir los conflictos de merge remanentes en el módulo de Pagos SaaS (`backend` y `frontend`), ejecutar pruebas unitarias/de compilación para validar ambos proyectos y, una vez verificado, integrar los cambios con la rama de Grover (`origin/Grover`) desde `main`.

---

## 1. Contexto actual y archivos revisados

Al inspeccionar `git status` y buscar marcadores de conflicto (`<<<<<<<`, `>>>>>>>`), se detectaron conflictos pendientes originados en la integración entre `HEAD` (rediseño del ledger global `/api/pagos/global`) y `ff3f2ce` (`origin/Hassan`, dashboard global de transacciones `/api/pagos/transacciones`):

- **Backend:**
  - `backend/app/repos/pago_repos.py`: se eliminó accidentalmente `listar_todos_los_pagos()` al conservar solo `listar_transacciones()`, dejando roto el llamado desde `pago_services.listar_pagos_globales()`.
  - `backend/app/routes/pago_routes.py` y `backend/app/services/pago_services.py`: ya conservan ambos flujos (`/global` y `/transacciones`), solo requieren formato limpio.
  - `backend/tests/test_pagos.py`: contiene marcadores de conflicto alrededor de `test_listar_pagos_globales_solo_admin`.
- **Frontend (Angular):**
  - `frontend/src/app/services/pagos.ts`: conflicto entre `pagosGlobales()` y `transacciones(filtros)`.
  - `frontend/src/app/pages/pagos/pagos.ts`, `pagos.html`, `pagos.css`, `pagos.spec.ts`: conflicto entre las señales/secciones del ledger global de pagos (`transaccionesGlobales`, tarjetas KPI, filtros en línea y conciliación Stripe) y la sección `Actividad de suscripciones` (`transacciones`, filtros por empresa y rango de fechas).

---

## 2. Patrones, capas y aislamiento de tenants

- Se preserva intacto el flujo `routes → services → repos → PostgreSQL`.
- **Autorización y tenants:**
  - Tanto `GET /api/pagos/global` como `GET /api/pagos/transacciones` permanecen restringidos exclusivamente a `ADMINISTRADOR` global en ruta (`exigir_rol('ADMINISTRADOR')`) y en servicio (`usuario['nombre_rol'] != 'ADMINISTRADOR'` → HTTP 403).
  - `ADMINISTRADOR_EMPRESA` conserva únicamente acceso a su propia empresa (`/mi-empresa`, comprobantes propios, verificación propia) sin exposición del dashboard global ni del ledger global.
- No se modifican migraciones SQL, JWT, roles ni contratos existentes; ambos endpoints y vistas coexisten de forma aditiva.

---

## 3. Decisión y estrategia de integración

1. **Conservar ambas capacidades de forma aditiva:**
   - Restaurar `listar_todos_los_pagos()` en `pago_repos.py` manteniendo `listar_transacciones()`.
   - Exponer ambos métodos en `PagosService` (`pagosGlobales()` y `transacciones()`).
   - En `PagosComponent` (`esGlobal === true`), cargar ambos orígenes (`cargarGlobal()` y `cargarTransacciones()`), manteniendo las tarjetas KPI, la barra de búsqueda/inspección y el ledger global junto con la sección `Actividad de suscripciones` (filtros por empresa y fechas).
   - Unificar los estilos en `pagos.css` y resolver el mock en `pagos.spec.ts` para cubrir ambas suites de pruebas.
2. **Validación prevista:**
   - Backend: `pytest backend/tests/test_pagos.py` (y pruebas unitarias aisladas relevantes sin escritura a BD real).
   - Frontend: `npm test` (Vitest) y `npm run build` en `frontend/`.
3. **Merge con rama de Grover:**
   - Actualizar referencias remotas (`git fetch origin`) y hacer merge de `origin/Grover` en `main` (resolviendo cualquier conflicto si existiera y re-validando).

---

## 4. Implementación final y validación realizada

1. **Resolución de conflictos de Pagos SaaS (commit `3e53c1f` en `main`):**
   - Restaurado `listar_todos_los_pagos()` en `backend/app/repos/pago_repos.py` junto a `listar_transacciones()`.
   - Limpiados los marcadores de conflicto en `backend/tests/test_pagos.py`, `frontend/src/app/services/pagos.ts`, `frontend/src/app/pages/pagos/pagos.ts`, `pagos.html`, `pagos.css` y `pagos.spec.ts`, conservando tanto el ledger global (`/api/pagos/global`) como el dashboard `Actividad de suscripciones` (`/api/pagos/transacciones`).
   - Instalada la dependencia `jspdf` declarada en `frontend/package.json` para habilitar `npm run build`.
2. **Integración con `origin/Grover` (commit `cc02ed0` en `main`):**
   - Resueltos los 8 conflictos de merge: se conservaron los archivos más recientes de CU32 de `main` (`trabajadores_costos_repos.py`, `gastos_operativos_services.py`, `trabajadores_costos_services.py`, `control-costos.html`, `control-costos.ts`, `tsconfig.cu32.spec.json`), se combinaron los scripts de `frontend/package.json` (`test:cu30`, `test:pagos`, `test:cu31`) y se integró el soporte de `ADMINISTRADOR` y alertas CU22 en `backend/app/services/control_costos_services.py`.
3. **Validación ejecutada post-merge:**
   - **Conflictos:** `git grep` confirma cero marcadores `<<<<<<<` / `>>>>>>>` en el repositorio.
   - **Backend (`pytest`):** `130 passed, 10 subtests passed` (`test_pagos.py`, `test_control_costos_services.py`, `test_cu22_notificaciones.py`, `test_cu31_comercializacion.py`, `test_avance_hu114.py`, `test_crm_cliente_hu115_hu117.py`, `test_crm_cliente_unidades.py`, `test_security_rules.py`). Sin escritura a base de datos productiva.
   - **Frontend (`npm run test:pagos`):** `17 passed` (3 archivos spec).
   - **Frontend (`npm run test:cu30`):** `12 passed` (1 archivo spec).
   - **Frontend (`npm run build`):** Compilación completa exitosa (`frontend/dist/frontend`).

> Nota: Los cambios quedaron integrados en la rama local `main` (sin `git push` automático).

---

## 5. Ajuste posterior en Panel de Cliente (CU30)

- **Hallazgo en ejecución local:** Al ingresar con rol `CLIENTE`:
  1. `panel.ts` invocaba `GET /api/proyectos/` porque el mapa local de permisos en `auth.ts` incluye `Visualizar_obras` para `CLIENTE`, mientras el backend valida permisos contra BD (`t_rol_permiso`) y devuelve `403 Forbidden`.
  2. Los endpoints `/api/crm/cliente/unidades`, `/api/crm/cliente/comunicaciones` y `/api/crm/cliente/solicitudes` devuelven `404 Not Found` cuando el usuario `CLIENTE` autenticado no tiene un registro vinculado en `t_crm_cliente` (`tipo_cliente = 'CLIENTE'`) para su `(id_persona, id_empresa)` (o si el servidor Uvicorn no fue reiniciado tras el merge).
- **Ajuste en `frontend/src/app/pages/panel/panel.ts`:**
  - En `cargarDatosPorRol()`, omitir `cargarObras()` cuando `this.rolUsuario === 'CLIENTE'` (el portal de cliente consume exclusivamente los endpoints CU30).
  - Mostrar el mensaje `err?.error?.detail` devuelto por el backend en los manejadores de error de `cargarUnidadesCliente`, `cargarComunicacionesCliente` y `cargarSolicitudesCliente` para diagnosticar de inmediato si falta vinculación CRM.
- **Sin cambios en backend ni contratos:** se preserva el aislamiento multi-tenant y las pruebas unitarias CU30 existentes.
