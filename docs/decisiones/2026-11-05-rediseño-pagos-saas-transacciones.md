# Rediseño UX/UI y Ledger Global de Pagos SaaS y Transacciones

**Fecha:** 2026-11-05  
**Autores:** Equipo de Arquitectura OBRATEC / Antigravity  
**Estado:** Implementado y Validado (Backend + Frontend Angular + Datos Multi-Empresa Sembrados)  
**Caso de Uso:** CU37 (Pagos SaaS y Ledger de Transacciones)  
**Alcance:** Frontend Angular (`PagosComponent`), Backend FastAPI (`pago_routes.py`, `pago_services.py`, `pago_repos.py`)

---

## 1. Problema Identificado

Al acceder a la sección de **ADMINISTRACIÓN → Pagos SaaS / Transacciones** (`/pagos`) con el rol de `ADMINISTRADOR` (Super Admin global), la interfaz presentaba una experiencia deficiente y desfasada:
1. Mostraba la etiqueta técnica `"CU37"` directamente en el encabezado.
2. La vista global para `ADMINISTRADOR` solo renderizaba un formulario aislado con un único campo numérico (`"ID de pago: Ej. 4"`), forzando al usuario a adivinar IDs de pago en una pantalla vacía.
3. No existía visualización tabular del historial de cobros de las empresas cliente, ni métricas ejecutivas de recaudación (total recaudado, transacciones confirmadas, pagos pendientes), ni buscador ni filtros por estado.
4. En backend no existía un endpoint de consulta global para listar el ledger completo de transacciones multi-tenant para el Super Admin.

---

## 2. Solución Arquitectónica por Capas

### A. Capa de Datos y Repositorio (`backend/app/repos/pago_repos.py`)
- Incorporar `listar_todos_los_pagos()`: Realiza una consulta sobre `obras.t_pago_suscripcion` con `LEFT JOIN obras.t_empresa` y `LEFT JOIN obras.t_plan_suscripcion`, devolviendo el ledger completo ordenado cronológicamente por `creado_en DESC`.

### B. Capa de Servicios (`backend/app/services/pago_services.py`)
- Incorporar `listar_pagos_globales(token)`: Valida la sesión activa y exige estrictamente que el rol sea `ADMINISTRADOR` global, garantizando que administradores de empresa no puedan acceder a transacciones de otros tenants.

### C. Capa de Controladores HTTP (`backend/app/routes/pago_routes.py`)
- Incorporar `GET /api/pagos/global` con guard `Depends(exigir_rol('ADMINISTRADOR'))`, posicionado antes de las rutas parametrizadas `/{id_pago}` para prevenir colisiones de enrutamiento.

### D. Capa de Frontend Angular (`frontend/src/app/pages/pagos/` y `services/pagos.ts`)
- `PagosService`: Añadir método `pagosGlobales()`.
- `PagosComponent` (`pagos.ts`, `pagos.html`, `pagos.css`):
  1. **Eliminar etiqueta técnica "CU37"** del encabezado.
  2. **Dashboard Ejecutivo de Métricas:** Tarjetas KPI de recaudación acumulada (BOB y USD), total de transacciones, porcentaje de pagos confirmados y pagos pendientes de verificación.
  3. **Barra de Herramientas y Búsqueda Reactiva:** Filtrado en vivo por empresa, plan, ID o identificador de Stripe, selector de estado (`TODOS`, `CONFIRMADO`, `PENDIENTE`, `FALLIDO`, `CANCELADO`) y botón para recargar transacciones.
  4. **Tabla de Transacciones Globales:** Vista moderna, responsiva y contrastada que detalla ID, Empresa, Plan, Monto formateado, Estado con badge de semáforo, fechas de creación y confirmación, y botones directos para `"⚡ Verificar con Stripe"` (en pendientes) y `"📄 Ver Comprobante"`.
  5. **Modal de Comprobante / Detalle Técnico:** Desglose del checkout session ID, payment intent, timestamps y enlace directo al recibo de Stripe cuando esté disponible.
  6. **Vista de Empresa (`ADMINISTRADOR_EMPRESA`):** Limpieza de etiquetas técnicas y mejoras de contraste y ergonomía visual para planes e historial.

---

## 3. Plan de Validación
1. Compilar frontend con `npm run build` certificando cero errores de templates o TypeScript.
2. Ejecutar suite de pruebas unitarias y de integración backend (`pytest`).
3. Verificar la carga del ledger global con las 9 transacciones existentes en PostgreSQL.
