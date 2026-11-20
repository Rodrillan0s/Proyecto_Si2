# Descarga de backups mediante PAR OCI existente

Fecha: 2026-10-05 (America/La_Paz). El usuario confirma BACKUP manual funcional (Job 7) y extensión del daemon Oracle para generar PAR ObjectRead de un solo objeto por diez minutos. No se modifica daemon, bucket privado, Instance Principal ni RESTORE.

## Contexto y decisión previa

Se revisaron arquitectura general, Backup/Restore, operación Oracle, BD/inventario/rutinas y código routes/services/repos/Angular. Antes de editar código se consultó el catálogo de control en modo de solo lectura: `public.backup_download_requests` existe en obratec_control/5433; id/job_id BIGINT, estado (PENDIENTE/PROCESANDO/COMPLETADO/FALLIDO), par_url, expira_en, solicitado_por, error y tres fechas. FK job_id → backup_jobs(id) con ON DELETE CASCADE. La cuenta actual dispone de SELECT/INSERT y USAGE en su secuencia; no se ejecutó migración ni se concedieron permisos.

Conservar `routes → services → repos → PostgreSQL`. Reutilizar la tabla y daemon existentes: insertar solamente job_id y actor después de validar BACKUP COMPLETADO conocido. La VM genera el PAR; FastAPI consulta resultado y no accede físicamente a OCI ni acepta objeto/checksum/URL del cliente. Respaldos globales del schema obras requieren ADMINISTRADOR activo reconsultado; ADMINISTRADOR_EMPRESA no accede. Consultas de solicitudes se restringen al actor solicitante y fuente conocida, sin reutilizar enlaces de otros administradores.

Mantener `/ejecuciones/{id}/archivo` como entrada: POST canónico para crear/reutilizar solicitud; GET compatible con la entrada anterior. Devolver 202 mientras el daemon prepara la URL; agregar consulta autorizada de solicitud para polling acotado de Angular. El HTTP del resultado completado es 200; estados expirados/fallidos no entregan URL. No devolver datos sensibles en pendientes, errores o auditoría; respuestas con Cache-Control no-store. Validar enlace HTTPS OCI, objeto/bucket/namespace y vigencia antes de entregarlo.

Angular habilita Descargar para BACKUP COMPLETADO cuando tabla/permisos están listos; muestra preparación, espera con límite y cancela navegación al destruir el componente. El enlace llega solo a memoria y se abre directamente en el navegador, sin enviar JWT a OCI ni persistirlo en almacenamiento local. Disponer de enlace manual si el navegador bloquea apertura automática. Repetir solicitud reutiliza una pendiente o PAR vigente del mismo actor; expirada genera una nueva solicitud bajo lock transaccional.

## Validación prevista

Pruebas aisladas de inserción/mapeo del contrato existente, permisos/actor/fuente, expiración, URLs inválidas, error sin secretos, reutilización, respuestas 202/200 y cancelación/timeout/polling en Angular. Ejecutar suites de backup y compilación web. Separar metadata leída/prueba declarada por usuario de prueba real: no imprimir PAR, iniciar API/daemon o generar copias/restauraciones. No crear tablas/worker/SDK OCI o credenciales nuevas. Revisar consumidores Flutter (no se encontraron previamente) y actualizar arquitectura/operación con resultados reales.

## Implementación y validación realizada

- `backup_jobs_repos`: detección independiente de tabla/grants, encolado con job_id/actor y estado PENDIENTE por defecto, reutilización de solicitudes del mismo actor bajo advisory lock transaccional, lectura restringida al propietario y auditoría sin URL. No requiere UPDATE para locks de filas ni modifica estado del daemon.
- `backup_services` y rutas: habilitación de capacidad, POST/GET compatible de archivo y GET de solicitud, estados reales y EXPIRADO derivado sin escribir. Liberación de URL solo COMPLETADO vigente, HTTPS/host OCI, sin userinfo/query/fragmento/caracteres de control, namespace/bucket/objeto exactos. IDs BIGINT strings, resultados no-store y errores saneados. RESTORE y sus garantías conservados.
- Configuración: BACKUP_VM_OCI_NAMESPACE y BACKUP_VM_OCI_BUCKET opcionales con valores existentes por defecto. No son credenciales ni requieren editar .env para este entorno.
- Angular: solicitud POST y polling GET, espera acotada a dos minutos con peticiones de quince segundos, cancelación al destruir, apertura directa sin HttpClient/JWT a OCI y enlace manual con vencimiento. Sin persistencia local ni exposición del PAR en mensajes. Descarga habilitada únicamente para trabajos COMPLETADO cuando capacidad está lista.
- Flutter: búsqueda en mobile/lib no encontró consumidores de backups; no se modificó.

Comprobación adicional de solo lectura confirmó solicitud 2/Job 7 COMPLETADO, host `objectstorage.sa-saopaulo-1.oraclecloud.com` y objeto coincidente. Se inspeccionó el enlace únicamente en memoria para comparar host/objeto: no se imprimió PAR, se navegó a él, se insertaron solicitudes o se descargó el objeto. El [formato y alcance de PAR](https://docs.oracle.com/en-us/iaas/Content/Object/Tasks/usingpreauthenticatedrequests_topic-Working_with_PreAuthenticated_Requests.htm) se contrastó con documentación oficial Oracle.

Resultados sobre el código final:

- `python -m unittest tests.test_backup_downloads tests.test_backup_vm tests.test_backups tests.test_backups_engine -q`: **90 pruebas OK**, todas aisladas. Incluyen rechazo de destinos alternativos/URL inválida, URL expirada o incompleta, permisos, actor, fuente, reintentos y respuestas HTTP.
- `npm.cmd run test:backups`: **21 pruebas OK**, incluyendo preparación/polling, enlace alternativo, retiro al vencer, cancelación, timeout y rechazo de otro job.
- `npm.cmd run build`: **compilación de producción OK**. Primer intento bloqueado por acceso de red a fuentes existentes; segundo con autorización completó. Advertencias de tamaños CSS existentes y dependencia CommonJS Leaflet; sin errores de compilación.
- `git diff --check`: sin errores de whitespace; advertencias de normalización LF/CRLF de Windows.

La generación del PAR fue probada previamente por el usuario; estas pruebas no certifican una nueva descarga completa Angular → daemon → OCI. Tras reiniciar/desplegar API y web, verificarla con Descargar. No se inició backend/worker, se aplicó migración, se cambió el daemon, se concedieron permisos o se restauró producción. Arquitectura general, BD, Backup y operación Oracle actualizadas.
