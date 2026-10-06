# Corrección de carga de Ver obras

Fecha: 2026-10-05. Alcance: frontend web; backend intacto.

## Análisis previo

Se leyó la arquitectura general y el flujo `ProyectosComponent → ProyectosService → GET /api/proyectos/` y `/api/proyectos/tipos`. La página registra ambas consultas independientes con la misma clave `proyectos` de `LecturasVigentes`. Al iniciar el catálogo de tipos, se cancela el listado antes de recibir respuesta; no se ejecuta su callback y `cargando` permanece activo. Es una regresión de la refactorización frontend.

El patrón de cancelación sigue siendo por recurso: listado y catálogo deben usar claves distintas. No cambian endpoints, permisos, JWT, filtrado de empresa ni la deduplicación de GET simultáneos del servicio. La empresa visual conserva su función de filtro sobre las obras autorizadas por el backend.

## Cambio y validación prevista

Separar la clave del catálogo de tipos. Añadir pruebas HTTP controladas con ambas consultas pendientes y respuestas en distinto orden: ninguna cancela a la otra, las obras se muestran y el spinner termina también cuando el listado falla. Ejecutar la suite focalizada y comprobar que backend permanezca sin cambios. No acceder a la base ni iniciar servicios reales.

## Resultado

Implementado: catálogo con clave `tipos-proyecto` y listado con clave `proyectos`. `npm run test:navigation` aprobó sus 19 pruebas, incluyendo tres regresiones nuevas: catálogo primero, listado primero y error HTTP del listado. Se comprueba que ninguna consulta cancela a la otra, se reciben las obras, se actualiza el conteo y termina la carga. Pruebas con HTTP simulado; sin base real ni cambios backend.
