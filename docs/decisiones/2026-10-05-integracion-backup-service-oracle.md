# Integración con el Backup Service existente en Oracle VM

Fecha: 2026-10-05 (America/La_Paz). Solicitud explícita: adaptar OBRATEC al daemon `/opt/obratec-backup/backup_service.py`, conservando `obratec-backup.service` y `obratec_control.public.backup_jobs`. El daemon es el único motor físico de BACKUP, PRE_RESTORE, RESTORE, SHA-256 y OCI Instance Principal.

## Inspección y contratos

Se leyeron arquitectura general, Backup/Restore, base de datos/inventario/rutinas, Reportes/operación y consumidores backend/Angular. `docs/OPERACION_BACKUPS.md` está eliminado por el usuario en el árbol actual: se conserva esa eliminación y se documenta la operación nueva en otro archivo. La guía anterior de worker Render queda obsoleta por la nueva instrucción. No hay fuente del daemon Oracle en el repositorio; se solicitó su ubicación para no inventar ni reemplazar su implementación.

El código local todavía encola UUID en `backup_control.t_backup_ejecucion`, descarga `.obratec` mediante FileResponse y exige disco/AES/herramientas/S3 en la API. Los IDs del contrato VM son enteros; sus estados son PENDIENTE/PROCESANDO/COMPLETADO/FALLIDO. Se comprobará el catálogo real mediante conexión de solo lectura, sin ejecutar funciones ni migraciones.

## Decisión previa a la implementación

Mantener `routes → services → repos → PostgreSQL`. Incorporar un adaptador SQL hacia la tabla pública existente, sin eliminarla o alterar el daemon. Conservar repositorio de control/barrera/writers/epoch/auditoría y middleware único. Retirar imports de motores físicos del servicio HTTP y bloquear los entrypoints legacy para impedir doble ejecución accidental.

Mantener ADMINISTRADOR global activo reconsultado y reautenticación con JWT distinto, reciente y de la misma cuenta. Ningún tenant se selecciona para backups: se captura exclusivamente el schema obras (todas sus empresas), sin comercio, evidencias ni software. RESTORE desde FastAPI queda bloqueado durante esta fase, incluso si se activa un flag antiguo. El daemon conserva su destino de prueba obratec_restore_test2 y la protección contra producción confirmados por el usuario.

Preservar rutas razonables y adaptar los IDs/estados de Angular. Descarga PAR queda pendiente, sin implementación o credenciales OCI en el repositorio. Programación inserta BACKUP/AUTOMATICO en la misma cola mediante un despachador finito invocable por un scheduler externo; no crear worker nuevo ni scheduler en cada API/daemon.

Heartbeat, coordinación de RESTORE con writers y PAR son integraciones posteriores directamente en la VM. Se preserva la barrera, sin liberación automática ante expiración/caída. No agregar OCI keys, boto3/S3 o herramientas PostgreSQL a Render.

## Validación prevista

Aclaración posterior del usuario: no acceder/recrear el daemon ni implementar ahora PAR o programación dentro de él. El refactor se limita al repositorio. Se conservará programación con un despachador de un solo ciclo que únicamente inserta trabajos (invocable por un scheduler externo); no se crea un motor o worker. Descarga temporal se muestra pendiente y no recibe credenciales OCI. Heartbeat y coordinación del daemon quedan explícitamente pendientes. Se pidió confirmar cómo RESTORE lee la fuente y cómo acredita su destino/heartbeat; hasta comprobarlo, el encolado destructivo permanece cerrado. BACKUP puede encolarse con disponibilidad de daemon no verificada, sin declarar ejecución exitosa.

El usuario confirmó el contrato exacto: RESTORE lee object_name/sha256 de su propia fila; job_relacionado_id representa PRE_RESTORE → RESTORE y no el backup fuente. No se cambia esta semántica ni se prepara una cola/tabla nueva de restauración. El control auxiliar conserva barrera/writers/auditoría/programación y añade únicamente una tabla de idempotencia para BACKUP. La migración se prepara sin aplicarla. Los IDs BIGINT se serializan como strings para no perder precisión en JavaScript.

Pruebas aisladas de permisos, DTO, idempotencia, SQL de encolado, fuente conocida, expiración de reautenticación/desafío, heartbeat, bloqueo de producción, programación, descargas y mantenimiento; pruebas Angular y compilación. Registrar separado catálogo leído, migración preparada y pruebas reales contra daemon. No iniciar workers/daemon, modificar roles, restaurar ni encolar trabajos reales durante esta implementación sin entorno de ensayo designado y contrato del daemon comprobado.

## Implementación final

- `backup_routes → backup_services → backup_jobs_repos → public.backup_jobs`: manuales 202, detalle/historial/estados/metadatos reales y auditoría del ID físico. Idempotencia mediante una tabla auxiliar con referencia lógica, sin FK/triggers nuevos sobre la cola del daemon y sin modificar sus estados.
- Configuración lógica en `oracle_settings.py`, sin requerir herramientas, paquetes, claves AES, volumen o S3. El preflight comprueba control/cola/permisos/migración auxiliar/mantenimiento. Heartbeat no conectado se muestra como no verificado; conectado y vencido bloquea operaciones con BACKUP_SERVICE_UNAVAILABLE.
- Programación existente y despachador finito de ocurrencias a BACKUP/AUTOMATICO, con revalidación de ADMINISTRADOR, deduplicación y avance transaccional. Endpoint protegido o consola existente invocable por scheduler externo; no se creó worker/scheduler dentro de FastAPI o del daemon. Retención no activa.
- RESTORE cerrado en código, incluso con flag legacy true; conserva reautenticación, confirmación, permisos y consultas. No se inserta RESTORE ni se añade contrato físico. Descarga 501 pendiente de PAR, importación legacy 410 sin escritura. Middleware/barrera/writers/epoch permanecen y nunca se libera mantenimiento por caída.
- Entradas worker/diagnósticos físicos legacy bloqueadas; adaptadores antiguos temporalmente conservados fuera del flujo HTTP y sus pruebas mantienen revisión de artefactos previos. Eliminada dependencia cryptography del requirements general; requirements-backup identificado como legacy.
- Angular conserva la pantalla y presenta alcance schema obras, IDs completos, cuatro estados VM, objeto/checksum/tamaño, programación y capacidades pendientes. No se encontraron consumidores Flutter de `/api/backup`. Actualizadas arquitectura general/BD/Backup/Reportes y referencia operativa en AGENTS.md. Se respetaron eliminaciones de documentos/imágenes previas del usuario y no se editaron .env, claves o artefactos.

## Validación realizada

Consulta de catálogos en transacción de solo lectura: obratec_control, PostgreSQL 17.11 Ubuntu, puerto 5433. Confirmados ID BIGINT/default secuencia, los trece campos del contrato, constraints de tipo/origen/estado y FK existente de job_relacionado_id. system_state y barrera existentes se observaron solo por metadata. El rol de control configurado no tiene SELECT ni INSERT sobre backup_jobs; no se pudo leer su historial real ni se modificaron grants. No se inspeccionó el código del daemon, cuyos detalles físicos proceden de las confirmaciones del usuario.

- Backend: `python -m unittest tests.test_backup_vm tests.test_backups tests.test_backups_engine -q`, **73 pruebas correctas** (26 nuevas del contrato VM y 47 aisladas previas). Mock de conexiones/casos de uso físicos; no PostgreSQL, restauración o correo reales.
- Angular: `npm.cmd run test:backups`, **16 pruebas correctas** en servicio/componente; controles retirados, datos VM, ID BIGINT, RBAC de backend, idempotencia cliente y programación.
- Producción Angular: `npm.cmd run build`, correcto sobre el código final, 1.72 MB inicial. El sandbox bloqueó Google Fonts; la repetición autorizada con acceso de red completó. Persisten advertencias de presupuesto CSS/Leaflet de archivos ajenos al cambio.
- `git diff --check`, correcto; enlaces locales de los nuevos Markdown comprobados. Sin instalación de nuevas dependencias para este trabajo.

**Pendiente de operación:** permisos del rol de aplicación, aplicar la única migración auxiliar en el control designado, desplegar/reiniciar API, configurar un scheduler externo y ejecutar el recorrido Angular → cola → VM → OCI. No se insertaron jobs, se aplicaron migraciones, se arrancaron procesos persistentes, se generaron PAR o se habilitó restauración. La entrega acredita código/contratos y comprobaciones aisladas; no acredita integración extremo a extremo.
