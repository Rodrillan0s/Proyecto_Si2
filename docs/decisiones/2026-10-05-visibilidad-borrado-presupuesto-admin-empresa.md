# Visibilidad del borrado de presupuesto para administrador de empresa

## Problema observado

El botón «Eliminar borrador» dependía simultáneamente del permiso frontend, de que la pantalla no estuviera cargando y de que la versión seleccionada fuera `BORRADOR`. Aunque se añadió `Modificar_presupuesto` al mapa local de `ADMINISTRADOR_EMPRESA`, `AuthService` prefiere una lista explícita de permisos de sesión y puede ocultar el botón si esa lista está desactualizada. Además, al abrir la pantalla se selecciona primero el presupuesto vigente, que normalmente no está en `BORRADOR`.

## Capas y decisión

- **Frontend:** hacer visible la acción para `ADMINISTRADOR_EMPRESA` cuando la obra tiene presupuestos; dejarla deshabilitada mientras carga o la versión elegida no esté en `BORRADOR`, e indicar que se seleccione un borrador. El rol solo controla presentación: no concede acceso en servidor.
- **Backend:** no cambiar rutas ni ampliar autorizaciones. `DELETE` sigue exigiendo `Modificar_presupuesto`; el servicio conserva las validaciones de empresa, obra y estado `BORRADOR`.
- **Persistencia:** no se modifica el esquema, roles ni asignaciones de base de datos. La base es compartida y `ADMINISTRADOR_EMPRESA` no es un rol global.

## Validación prevista

- Comprobar que el permiso local del rol incluye `Modificar_presupuesto`.
- Ejecutar el build de Angular y las pruebas unitarias aisladas existentes del borrado.
- No ejecutar migraciones ni pruebas contra PostgreSQL.

## Ajuste de visibilidad

La cabecera ahora muestra la acción para administradores de empresa y globales cuando existen presupuestos, incluso si la versión seleccionada no es borrador. En ese caso queda deshabilitada con una indicación para seleccionar un `BORRADOR`. El servidor continúa siendo la autoridad final al borrar.
