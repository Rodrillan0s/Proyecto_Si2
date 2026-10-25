# CU39: selección y deselección de predecesoras

## Solicitud y contexto
El usuario no puede deseleccionar fácilmente una predecesora en Web. Se revisaron arquitectura general, plantilla/componente/estilos/pruebas de cronogramas, contrato HTTP y selector móvil. Angular usa select multiple nativo: un clic normal sobre la opción seleccionada no alterna su estado y depende de modificadores de teclado. Flutter ya utiliza casillas con altas/bajas explícitas.

## Capas, contratos y tenant
Cambio limitado a presentación Angular y estado del borrador. Sustituir el select múltiple por casillas independientes accesibles, con instrucciones visibles. Conservar claves estables, otras selecciones, exclusión de la propia actividad y lista vacía al quitar todas. No cambia contrato de dependencias, autorización/JWT/tenant, rutas → servicios → repositorios, base de datos ni Flutter.

## Decisión y validación prevista
Cada clic marca/desmarca una predecesora sin Ctrl/Cmd. El campo queda deshabilitado durante guardado por el fieldset exterior. Verificar la interacción real de casillas, selecciones existentes, preservación de las restantes y envío de dependencias vacías; ejecutar suite CU39 Angular y build.

## Implementación y validación
Se sustituyó el selector múltiple por casillas con etiquetas pulsables y foco visible. El componente agrega claves sin duplicarlas y elimina solo la desmarcada. La regresión usa clics reales sobre casillas de la plantilla: carga selección existente, marca otra, desmarca conservando la restante, quita todas, repite el ciclo y comprueba que el PUT envía dependencias: [].

Suite Angular CU39: 7 pruebas aprobadas. `npm run build`: código 0, con las advertencias previas de CSS, Leaflet e importación no utilizada de otro componente. `git diff --check` pasó. No se accedió a la base de datos ni se realizaron migraciones.
