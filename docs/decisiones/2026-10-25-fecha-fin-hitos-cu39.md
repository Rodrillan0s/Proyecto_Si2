# CU39: una sola fecha prevista en hitos

## Solicitud y contexto
El usuario reportó inicialmente que no podía editar fin previsto de un hito y aclaró después que desea una sola fecha. Se revisaron arquitectura general, formularios y pruebas CU39 de Angular y Flutter. La implementación inicial mostraba dos fechas y deshabilitaba fin, causando confusión.

## Capas, contratos y tenant
Ajuste de interacción en los borradores Web/Móvil: mostrar únicamente Fecha prevista para hitos. Internamente sincronizar inicio/fin previstos para conservar el contrato de un hito de un día. Las actividades comunes mantienen fechas independientes. No se cambian contratos, permisos, autorización por empresa, backend, persistencia ni el patrón routes → services → repos.

## Decisión y validación prevista
Mostrar una sola fecha prevista editable en hitos; al cambiarla actualizar ambos campos del payload. Mantener inicio/fin visibles en actividades comunes. Probar interacción real, ausencia de un campo fin de hito y payload sincronizado, además del selector móvil. Ejecutar suite CU39 Angular, build y pruebas/análisis Flutter proporcionales. No ejecutar migraciones ni escrituras de prueba en la base de negocio.

## Implementación y validación
Implementado en Web y Flutter: un único campo Fecha prevista para hitos, con sincronización interna del contrato; actividades comunes conservan inicio y fin. La prueba Web verifica ausencia de campos duplicados, cambios hacia adelante/atrás y envío de ambas fechas iguales. La prueba móvil abre el calendario de la fecha única, elige un día anterior y comprueba su conservación al aceptar el hito.

Validación final: 9 pruebas Angular CU39 aprobadas; build de producción código 0 con advertencias previas ajenas al cambio; 4 pruebas Flutter aprobadas; análisis Dart de archivos afectados sin incidencias; git diff --check correcto. Las pruebas iniciales se ajustaron a la aclaración del usuario y a los controles reales antes de esta verificación final. No se realizaron migraciones ni escrituras en la base de datos.
