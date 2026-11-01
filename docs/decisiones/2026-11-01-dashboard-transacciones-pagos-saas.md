# Dashboard de transacciones de suscripciones SaaS

## Solicitud y alcance

Agregar al módulo Pagos SaaS, visible solo para `ADMINISTRADOR`, un dashboard con movimientos recientes de suscripciones por empresa y filtros por rango de fechas y nombre de empresa. Conservar la consulta/verificación de pagos por ID y el flujo de checkout de `ADMINISTRADOR_EMPRESA`.

## Contexto actual y archivos revisados

El backend ya conserva pagos confirmados en `t_pago_suscripcion` y cambios de suscripción en `t_suscripcion_historial`. Las cancelaciones se registran como historial con estado `CANCELADA`; las compras aplicadas se relacionan con historial por `id_historial_suscripcion`. El vencimiento efectivo se determina comparando `fecha_fin` con la fecha actual de `America/La_Paz`; no se registra como transacción ni hay un worker que lo genere.

La fotografía de `BASE_DATOS_INVENTARIO.md` y `BASE_DATOS_RUTINAS.md` es anterior a las tablas de suscripciones y pagos. Las migraciones y decisiones vigentes documentan las columnas utilizadas; no se consultará una base desplegada ni se asumirá que una migración pendiente está aplicada.

## Patrones, capas y tenants afectados

- Mantener `routes → services → repos → PostgreSQL`; SQL parametrizado en `pago_repos`, autorización y validaciones en `pago_services`.
- Agregar consulta global solo para `ADMINISTRADOR` (superadministrador). Revalidar en servicio el usuario activo y su rol desde la base; no confiar en empresa elegida en la interfaz ni aceptar `id_empresa` del cliente.
- El resultado cruza `t_empresa`, `t_plan_suscripcion`, `t_pago_suscripcion` y `t_suscripcion_historial`. La consulta global no cambia las reglas existentes de aislamiento para administradores de empresa.
- Angular usará el mismo módulo y separará la experiencia global de la vista actual de empresa.

## Decisión y efectos sobre contratos/datos

Agregar `GET /api/pagos/transacciones` con filtros opcionales `fecha_desde`, `fecha_hasta` y `nombre_empresa`, más un límite acotado de resultados. Las compras/renovaciones/cambios de plan proceden de pagos confirmados y aplicados; las cancelaciones proceden del historial administrativo.

Mostrar vencimientos derivados solo para períodos históricos activos cuya fecha de fin ya pasó y que no fueron renovados, reemplazados o cancelados antes del vencimiento. El evento se fechará en el primer día posterior a `fecha_fin`, según `America/La_Paz`, y se marcará explícitamente como calculado. No añadir tablas, migraciones, escritura durante consultas ni workers.

## Implementación final y validación realizada

- Se agregó `GET /api/pagos/transacciones`, con autorización de ruta y revalidación del usuario/rol activo en el servicio. Acepta filtros opcionales de fecha y coincidencia parcial del nombre, con rango validado y máximo de 100 filas (50 por defecto).
- El repositorio une pagos confirmados y aplicados, historial de cancelaciones y vencimientos derivados. Evita duplicar pagos e historial `PAGO_STRIPE`; el vencimiento se fecha el día posterior a `fecha_fin` en `America/La_Paz` y excluye períodos con cobertura o cambios posteriores anteriores al vencimiento.
- Angular carga los 50 movimientos recientes al abrir Pagos SaaS, filtra por empresa/fechas y conserva la consulta por ID/verificación. La vista global sigue restringida a `ADMINISTRADOR`; no se encontraron consumidores del módulo en Flutter.
- Backend: `30 passed` en `backend/tests/test_pagos.py`; compilación Python correcta. Frontend: `16 passed` en `npm run test:pagos`; `npm run build` correcto. `git diff --check` correcto.
- El build reportó advertencias de presupuesto CSS en varios estilos, incluido `pagos.css`, y advertencias CommonJS/fuentes; no impidieron la compilación. Pytest reportó dos advertencias deprecadas de Starlette/httpx.
- No se consultó PostgreSQL, no se ejecutaron migraciones, no se invocó Stripe ni se inició ningún worker.

## Limitaciones o trabajo pendiente

Los vencimientos son inferidos del historial existente, no eventos auditados ni una garantía de que un proceso haya notificado o materializado el vencimiento. La consulta mostrará hasta el límite solicitado, ordenada de más reciente a más antigua.
