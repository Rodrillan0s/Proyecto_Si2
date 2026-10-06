# Resolución de conflictos de integración (Merge origin/main en anghy)

## Solicitud y alcance

Resolver los conflictos de integración tras la ejecución de `git merge origin/main` en la rama de trabajo `anghy`, preservando tanto las funcionalidades desarrolladas en la rama local (CU18 - Avances de Obra, robustez de reconexión de PostgreSQL y pestañas de proyecto) como las nuevas funcionalidades integradas en `main` (Reportes, IA, Incidencias CU19, Control de Costos CU17, Personal de Obra, Inventario, Compras y mejoras móviles).

## Capas y contratos afectados

1. **Backend (`backend/app/__init__.py`)**:
   - Capa de composición (`create_app` y registro de enrutadores).
   - Se unifican todas las importaciones de rutas de `main` (`estimacion_routes`, `control_costos_routes`, `compras_routes`, `inventario_routes`, `equipos_maquinaria_routes`, `incidencia_routes`, `reportes_routes`) junto con `avance_routes` de la rama de trabajo.
   - Se asegura la preservación del flujo `routes → services → repos` sin modificar contratos HTTP ni dependencias de seguridad.

2. **Infraestructura de datos (`backend/app/classes/postgres.py`)**:
   - Se preserva el algoritmo de reintentos (hasta 3 intentos de obtención y prueba con `SELECT 1;`) y fallback a conexión directa si el pool está agotado, consolidando la solución implementada para evitar conexiones caídas por inactividad.

3. **Frontend Web (`frontend/src/app/pages/proyectos/detalle/proyecto-detalle.*`)**:
   - Se integran en el HTML y TypeScript los botones de acceso rápido y pestañas para Presupuesto & APU (CU16) y Avances de Obra (CU18).
   - Se mantiene intacto el modal de asignación de trabajadores (`PersonalObra`, `candidatosPersonal`, `mostrarModalPersonal`) traído de `main`.
   - Se importan `ProyectoPresupuestoComponent` y `ProyectoAvancesComponent` de forma compatible.

4. **Cliente Móvil (`mobile/lib/config/app_config.dart` y `mobile/lib/screens/proyecto_detalle_screen.dart`)**:
   - En configuración se conserva la compatibilidad con desarrollo web y red local (`kIsWeb`).
   - En la vista de detalle de obra se integran los filtros por chips, menú de acciones contextuales y la interactividad táctil para inspección de unidades.

## Contexto de tenant y permisos

- No se alteran los roles ni los permisos de base de datos ni los decoradores `exigir_permiso` o `exigir_rol`.
- La pertenencia a empresa y el aislamiento por `id_empresa` se mantienen inalterados en todas las capas.

## Validación prevista

- Comprobación de ausencia de marcadores de conflicto (`<<<<<<<`, `=======`, `>>>>>>>`).
- Verificación sintáctica de Python (`python -m py_compile backend/app/__init__.py backend/app/classes/postgres.py`).
- Verificación de tipos y linting en archivos modificados.
- Preparación del estado del árbol para que el usuario pueda completar o verificar el commit de merge.
