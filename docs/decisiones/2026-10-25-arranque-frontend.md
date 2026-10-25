# Corrección del arranque del frontend

## Solicitud y alcance
Diagnosticar y corregir el fallo de arranque del frontend Angular.

## Contexto actual y archivos revisados
Se leyó ARQUITECTURA_Y_PATRONES.md, package.json, angular.json, tsconfig.app.json, app.routes.ts, CronogramaService y la pantalla cronogramas. Hay cambios previos del usuario en rutas, scripts y backend que se conservan.
La compilación de desarrollo reproduce NG8004 (pipe date ausente), NG2008 (cronogramas.css inexistente) y NG8103 (directivas sin importar) en CronogramasComponent. Aunque la ruta es diferida, Angular compila su componente y bloquea el arranque de toda la aplicación.

## Patrones, capas y tenants afectados
Cambio limitado a los metadatos de un componente standalone de presentación. Se conserva la ruta con roleGuard y Visualizar_cronograma, el servicio HTTP y el flujo routes → services → repos → PostgreSQL. No se alteran JWT, empresa autorizada, permisos, contratos, persistencia ni Flutter.

## Decisión y efectos sobre contratos/datos
Importar CommonModule, que proporciona NgIf, NgFor y DatePipe, y quitar la referencia a la hoja inexistente: la pantalla no dispone de estilos locales que recuperar. Mantener plantilla y comportamiento existentes. No requiere cambios de arquitectura ni migraciones.

## Implementación final y validación realizada
Se agregó CommonModule y se eliminó la referencia al CSS inexistente. `npm run build` terminó con código 0. `npm start -- --host 127.0.0.1 --port 4200` compiló en desarrollo y quedó en watch; GET http://127.0.0.1:4200/ devolvió HTTP 200 con app-root. `git diff --check` pasó. No se ejecutaron operaciones contra la base de datos.

## Limitaciones
Permanecen advertencias ajenas al bloqueo: importación no utilizada en ProyectoDetalleComponent, presupuestos de tamaño CSS y Leaflet CommonJS en producción. Node v25.9.0 emite advertencia de versión impar; no impidió las compilaciones ni el arranque. No se validó navegación autenticada ni endpoints de cronogramas; esta corrección resuelve el bloqueo del compilador.
