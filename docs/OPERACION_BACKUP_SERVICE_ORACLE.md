# Operación del Backup Service Oracle

Fecha: 2026-10-05. [Arquitectura](ARQUITECTURA_BACKUP_RESTORE.md), [decisión](decisiones/2026-10-05-integracion-backup-service-oracle.md).

## Responsabilidades

FastAPI autoriza, inserta y consulta `obratec_control.public.backup_jobs`. El daemon existente `/opt/obratec-backup/backup_service.py`, servicio `obratec-backup.service`, es el único motor de BACKUP, PRE_RESTORE, RESTORE, SHA-256 y OCI Instance Principal. **No levantar el worker legacy ni crear un worker Render.** No instalar herramientas PostgreSQL o credenciales OCI/S3 en Render para este pipeline.

El daemon no se modificó desde este repositorio. El usuario implementó posteriormente en la VM el consumo de `public.backup_download_requests` y PAR ObjectRead de diez minutos para un objeto. Conserva sus usuarios locales, peer/ident, bucket privado `obratec_backups`, namespace `grdnljcz1opp` y restore transaccional. Su destino sigue siendo `obratec_restore_test2`, con protección explícita contra `obras` según confirmación del usuario. No se inspeccionó directamente su archivo.

Si el despliegue tenía un supervisor para el worker legacy, retirarlo de su configuración al desplegar este refactor: su entrada ahora rechaza ejecución. Conservar el servicio systemd Oracle existente; no sustituirlo.

## Estado y permisos del control

Se confirmó por catálogo de solo lectura: base `obratec_control`, PostgreSQL 17.11, puerto 5433, campos/constraints de backup_jobs compatibles. La revisión inicial encontró SELECT/INSERT pendientes; **posteriormente el usuario confirmó backup manual funcional y Job 7 completado**. La consulta actual confirma tabla de descargas existente y SELECT/INSERT/USAGE en su secuencia. El agente no cambió permisos ni aplicó migraciones.

El operador debe identificar el rol de aplicación y revisar sus permisos sin cambiar los roles del daemon. Ejemplo para su propietario/operador autorizado, sustituyendo ROL_APP:

```sql
GRANT USAGE ON SCHEMA public TO ROL_APP;
GRANT SELECT, INSERT ON public.backup_jobs TO ROL_APP;
GRANT USAGE ON SEQUENCE public.backup_jobs_id_seq TO ROL_APP;
```

La aplicación no reclama, actualiza ni elimina jobs; no requiere UPDATE/DELETE sobre la cola. Conservar permisos de `backup_control` para middleware, writers, epoch, programación y auditoría, incluida la secuencia del diario. Tras la migración auxiliar, la cuenta necesita SELECT/INSERT en `backup_control.t_backup_vm_request`; concederlos si otro propietario ejecutó el script.

La [migración preparada](../backend/database/20261005_backup_vm_integration.sql) añade únicamente una tabla de idempotencia. No crea/reemplaza backup_jobs ni system_state y no elimina tablas anteriores. Barrera/tablas legacy deben existir. Revisar destino y entorno antes de aplicar:

La referencia al ID físico es lógica: no se agregan FK/triggers que condicionen la futura limpieza de la cola por el daemon. Una clave cuyo job ya no existe no vuelve a crear trabajo silenciosamente; devuelve BACKUP_JOB_UNAVAILABLE.

```bash
cd backend
python migrate_backups.py --environment oracle-integracion-designada
# Después de revisar destino y permisos; este comando sí escribe:
python migrate_backups.py --environment oracle-integracion-designada --apply
```

El primero inspecciona; el segundo instala únicamente la integración auxiliar. La presencia del script no acredita instalación.

## Configuración y API

Usar [backup.env.example](../backend/backup.env.example), con DSN y entorno reales. Mantener BACKUP_ENABLED=false durante preparación; activarlo y reiniciar la API después de verificar migración, permisos, conectividad y coordinación de escritores. Conservar DB_* del negocio si ya son correctos. No incluir el `.env` local en el despliegue: Config carga dotenv con override y podría sustituir variables Render.

El cliente nuevo ignora directorios persistentes, AES, claves/S3, hooks, release y restore DSN legacy. No se editó .env ni se borraron claves/artefactos antiguos. Instalar solo las dependencias normales del backend; requirements-backup.txt queda identificado como legacy.

ADMINISTRADOR global accede a `/backup`. POST `/api/backup/ejecuciones` con `{"alcance":"base_datos"}` e Idempotency-Key devuelve inmediatamente 202/ID/estado. El contenido real es exclusivamente **schema obras**, todas sus empresas, excluyendo comercio, archivos y software. Angular usa PENDIENTE/PROCESANDO/COMPLETADO/FALLIDO y metadatos object_name/sha256/size_bytes. Los IDs BIGINT se serializan como strings sin truncar.

## Heartbeat, barrera y programación

Mantener BACKUP_VM_HEARTBEAT_CONNECTED=false: el daemon actual no publica heartbeat compatible. El backend ignora latidos legacy y muestra disponibilidad no verificada; encolar/guardar horario no acredita ejecución. Cuando se integre en la VM, acordar su publicación en backup_control.t_backup_control.heartbeat antes de activar el flag. Si está conectado pero vencido, el preflight devuelve BACKUP_SERVICE_UNAVAILABLE.

Se conservan MaintenanceMiddleware, barrier, enter/renew/leave_writer, active_writers y session_epoch. Control habilitado caído bloquea negocio/autenticación. No se limpian escritores vencidos ni mantenimiento automáticamente. La coordinación RESTORE del daemon con esta barrera está pendiente; no se declara instalada. El worker Reportes conserva su participación en writers y no se inicia en esta prueba, porque puede enviar correos.

La programación guarda frecuencia/hora/zona en la tabla existente. Un despachador finito inserta BACKUP/AUTOMATICO/PENDIENTE en la misma cola, deduplica y avanza calendario en una transacción, revalidando el administrador propietario. Recupera una ocurrencia reciente y registra las omitidas. No hay scheduler dentro del daemon ni de cada proceso HTTP.

Se puede invocar con ADMINISTRADOR autenticado mediante POST `/api/backup/programacion/ejecutar` o el botón **Encolar ejecución vencida**. Un scheduler externo del entorno designado puede ejecutar periódicamente, desde backend:

```bash
python backup_recovery.py --environment oracle-integracion-designada --dispatch-schedule
```

El comando termina tras un ciclo y únicamente inserta trabajos; no ejecuta backups ni crea otro motor. No se configuró cron ni se inició automatización. Una programación legacy de sistema completo se presenta pausada y debe revisarse/guardarse con alcance base_datos. Retención_dias se conserva como configuración compatible; integración DELETE/retención pendiente, sin eliminación de objetos.

## Capacidades pendientes

RESTORE desde FastAPI está bloqueado en código y devuelve BACKUP_RESTORE_MIGRATION/503, incluso con BACKUP_RESTORE_ENABLED=true. Permanecen sus rutas, ADMINISTRADOR, reautenticación, frase exacta, JWT reciente/distinto/mismo actor y consultas del historial existente. job_relacionado_id conserva PRE_RESTORE → RESTORE; no se usa como fuente. No se añade un contrato nuevo de restore.

La descarga ya utiliza el PAR generado por el daemon: ver el procedimiento siguiente. No hay FileResponse, SDK ni acceso OCI desde Render. Importación `.obratec` devuelve BACKUP_IMPORT_RETIRED/410 sin escribir/consumir el stream.

Adaptadores físicos legacy y sus pruebas aisladas permanecen temporalmente para revisión histórica, desconectados del servicio HTTP. Las entradas worker y diagnósticos que operaban sobre bases reales están bloqueadas. backup_recovery solo admite estado, preflight lógico y despacho de calendario. No usar paquetes antiguos como vía de restauración Oracle ni borrar sus claves/artefactos.

## Verificación operativa pendiente

Después de permisos/migración en el entorno designado: crear manual desde Angular, repetir la misma clave y comprobar mismo ID; observar el reclamo/completado en VM/OCI y metadatos en Angular; guardar calendario y verificar BACKUP/AUTOMATICO con el despachador; comprobar que restauración sigue bloqueada y ADMINISTRADOR_EMPRESA no opera el módulo. Para descarga, comprobar el flujo de PAR descrito abajo.

Logs del daemon: `sudo journalctl -u obratec-backup -n 100 --no-pager`. Las pruebas locales no certifican este recorrido: no se insertaron trabajos reales, se ejecutaron migraciones o se contactó OCI durante el refactor.

## Descargar desde Angular

Reiniciar/desplegar el backend y la web actualizados. No hace falta aplicar una migración de este repositorio para descargas: la tabla ya existe en la VM. Conservar BACKUP_ENABLED, DSN y entorno que ya permiten crear respaldos. `BACKUP_VM_OCI_NAMESPACE=grdnljcz1opp` y `BACKUP_VM_OCI_BUCKET=obratec_backups` son metadatos públicos opcionales, con esos valores por defecto; no son credenciales. No activar heartbeat ni RESTORE para habilitar descarga.

En `/backup`, como ADMINISTRADOR global, seleccionar **Descargar** en una fila COMPLETADO. Angular solicita un PAR, muestra Preparando y consulta cada dos segundos durante hasta dos minutos (cada llamada tiene timeout de quince segundos). Al completar, intenta abrir la descarga y muestra un enlace alternativo con su fecha de vencimiento. El enlace se retira al vencer o abandonar la pantalla. Si sigue pendiente, volver a pulsar Descargar reutiliza la solicitud del mismo actor; si expiró o falló, se crea una nueva. La web no persiste el PAR ni envía Authorization a OCI.

| API | Resultado |
| --- | --- |
| POST `/api/backup/ejecuciones/{job_id}/archivo`, cuerpo `{}` | Crea/reutiliza solicitud para BACKUP COMPLETADO; 202 PENDIENTE/PROCESANDO, 200 resultado terminal. |
| GET `/api/backup/ejecuciones/{job_id}/archivo` | Compatibilidad con la entrada anterior; mismo contrato JSON, puede encolar. Usar POST en clientes nuevos. |
| GET `/api/backup/descargas/{request_id}` | Consulta sin crear; restringida al administrador solicitante, 404 si no le pertenece. |
| GET `/api/backup/estado` | descarga_habilitada y requisitos_descarga, independientes de requisitos de creación. |

El JSON contiene id/job_id como strings, estado, nombre, expira_en, error y url. url es null para pendientes/fallidos/expirados; solo COMPLETADO vigente con host HTTPS OCI y objeto/bucket/namespace coincidentes entrega el PAR. EXPIRADO se calcula sin actualizar la tabla. Respuestas de resultado: Cache-Control no-store. URL inválida/incompleta devuelve BACKUP_DOWNLOAD_INVALID/502 sin revelar el enlace. Fallos de tabla/permisos deshabilitan descarga sin deshabilitar backups manuales.

No copiar PAR en tickets/logs: quien tenga el enlace puede leer el objeto hasta su expiración ([documentación Oracle](https://docs.oracle.com/en-us/iaas/Content/Object/Tasks/usingpreauthenticatedrequests_topic-Working_with_PreAuthenticated_Requests.htm)). La aplicación no hace público el bucket ni renueva el PAR; la generación y vigencia corresponden a la VM existente.

Verificación de esta entrega: catálogo y solicitud 2/Job 7 consultados en modo de solo lectura; COMPLETADO y host/objeto coincidentes, sin imprimir el PAR. La prueba de generación fue realizada por el usuario. Pruebas locales usan dobles y no acreditan una nueva descarga completa desde navegador a OCI; verificarla después de desplegar pulsando Descargar.
