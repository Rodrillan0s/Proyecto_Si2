# Corrección de compilación en Frontend tras integración de rama

## Solicitud y alcance

Resolver el error de compilación en el frontend de Angular generado tras la integración de la rama `origin/hassan`, donde se detectó una implementación duplicada de la función `irAPresupuesto()` en `frontend/src/app/pages/proyectos/detalle/proyecto-detalle.ts` (error TS2393).

## Capas y contratos afectados

1. **Frontend Web (`frontend/src/app/pages/proyectos/detalle/proyecto-detalle.ts`)**:
   - Capa de presentación (componente standalone `ProyectoDetalleComponent`).
   - Se elimina la definición redundante del método `irAPresupuesto()`, manteniendo una única implementación limpia que ejecuta `this.seleccionarTab('presupuesto')`.
   - Se preservan las importaciones y la interfaz de componentes hijos (`ProyectoPresupuestoComponent`, `ProyectoAvancesComponent`, `ProyectoEstructuraComponent`).

## Contexto de tenant y permisos

- No se modifican contratos de API, permisos, roles ni el aislamiento multiempresa.
- La pertenencia a empresa y autenticación no sufren alteraciones.

## Validación prevista

- Ejecutar `npm run build` en el frontend para confirmar que el bundle se genera sin advertencias de miembros duplicados ni errores TS2393.
