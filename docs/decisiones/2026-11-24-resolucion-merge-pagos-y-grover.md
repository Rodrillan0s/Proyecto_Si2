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

*(Pendiente de completar tras resolución y ejecución de pruebas).*
