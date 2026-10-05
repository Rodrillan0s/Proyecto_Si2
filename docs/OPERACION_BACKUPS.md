# Operación de Backup/Restore

El usuario autorizó ignorar temporalmente las tres imágenes externas faltantes al respaldar **solo la base**. [Comportamiento y límites](decisiones/2026-10-04-backup-base-evidencias-ausentes.md). Las copias `base_datos` registran la omisión en el manifiesto y en la etapa/advertencias del trabajo; los registros de negocio se conservan. `sistema_completo` sigue exigiendo archivos. La nueva copia real quedó LISTO y pasó verificación de integridad/catálogo; seleccionar Solo base de datos en `/backup`. El bloqueo inicial del párrafo siguiente es histórico. Restauración y automatización continua siguen pendientes.

Actualización posterior a la habilitación del usuario: [prueba del entorno Ubuntu](PRUEBA_BACKUPS_UBUNTU_2026-10-04.md). Control instalado, conexión/herramientas/preflight correctos; creación aún bloqueada por tres evidencias ausentes del release local. Sin programación guardada ni worker continuo; restauración deshabilitada. Las observaciones de la entrega inicial siguientes son históricas.

Fecha: 2026-10-04. [Arquitectura](ARQUITECTURA_BACKUP_RESTORE.md). Código implementado; servidor no activado/migrado/restaurado durante esta entrega. No se editó .env ni se inició backend/worker oculto. Dependencias de cifrado/S3 instaladas en desarrollo; no se encontraron pg_dump/pg_restore en las rutas habituales del equipo.

El administrador global accede desde **Copias de respaldo**, `/backup`. Siempre afecta a todas las empresas. La UI indica qué falta para habilitar las operaciones.

El usuario confirmó acceso a PostgreSQL mediante **Ubuntu Server**. Para habilitarlo paso a paso, consultar [Habilitar backups con Ubuntu Server](HABILITAR_BACKUPS_UBUNTU_SERVER.md): distingue base remota, backend/worker Windows o Ubuntu y túnel SSH. Las herramientas y los paquetes están en el equipo del worker; la ubicación de la base no determina la del backend.

## Preparación

1. Designar servidor/entorno y volumen persistente externo al proyecto/release. Reservar espacio para dump, paquetes, cifrado, descifrado y ensayo; preflight estima seis veces base + archivos. Configurar ACL NTFS restrictivas en Windows: chmod no sustituye sus ACL.
2. Instalar herramientas PostgreSQL 17 y configurar BACKUP_PG_DUMP_PATH/BACKUP_PG_RESTORE_PATH si no están en PATH.
3. Crear una base independiente de control y su cuenta. Su nombre debe diferir de Config.DB_NAME. Designar cómo respaldar también el control.
4. Añadir variables de [backup.env.example](../backend/backup.env.example) a la configuración segura. Mantener BACKUP_ENABLED=false inicialmente; no usar credenciales de ejemplo.
5. Generar 32 bytes aleatorios, codificar Base64 y custodiar en depósito de secretos. Configurar BACKUP_KEY_ID y BACKUP_KEYS_JSON. No reutilizar TOKEN_KEY ni passwords. Conservar claves antiguas por key_id fuera de DB/archivos cifrados; sin ellas no se recupera el paquete.
6. Coordinar todos los escritores adicionales. Si no hay integraciones/SQL directo/otros workers, registrar esa condición y confirmar BACKUP_EXTERNAL_WRITERS_COORDINATED=true.

Desde backend, en terminal visible del operador:

```powershell
python -m pip install -r requirements.txt
python -m pip install -r requirements-backup.txt
python migrate_backups.py --environment desarrollo-designado
# Después de revisar el destino, SOLO escribe al control:
python migrate_backups.py --environment desarrollo-designado --apply
```

Tras verificar las siete tablas, completar claves/entorno/herramientas y establecer BACKUP_ENABLED=true y BACKUP_STORAGE_PERSISTENT=true. Todas las réplicas usan el mismo control y configuración de epoch/mantenimiento. Reiniciar el backend en la terminal del operador. Un módulo desconfigurado no impide el arranque general; una vez activado, caída del control bloquea escrituras y autenticación para evitar operar sin estado fiable.

## Worker, programación y descarga

```powershell
python backup_recovery.py --environment desarrollo-designado --preflight
python backup_worker.py --once
# Visible; en producción instalar como servicio supervisado:
python backup_worker.py --interval 15
```

Uvicorn no inicia el worker. Guardar programación persiste frecuencia, hora, zona IANA, día y retención; no significa que opere: comprobar latido. Para promover software, instalar el worker y su Python fuera de BACKUP_RELEASE_TARGET. El coordinador no puede ejecutarse desde el código que sustituye.

Crear devuelve trabajo 202, cuyas etapas y errores aparecen en historial. La captura bloquea acceso de negocio brevemente; cifrado posterior puede seguir sin esa barrera. Descargar produce .obratec cifrado; se importa/ensaya con este módulo o consola, no como SQL plano.

Para pérdida de host, configurar S3 compatible con bucket privado, prefijo/endpoint y credenciales por cadena estándar de AWS. Verificar política sin acceso público y permisos de subir, leer y borrar. Con S3 configurado, el job no llega a LISTO hasta completar subida. La UI indica configuración; certificar protección externa verificando el objeto concreto y recuperándolo desde otro host. Un disco local persistente no sustituye esa prueba.

## Habilitar restauración

Designar entorno y activar BACKUP_RESTORE_ENABLED. BACKUP_RESTORE_DSN debe apuntar a postgres en el mismo host/puerto del negocio, con permisos de crear bases, ser miembro de owners/grantors necesarios, terminar conexiones correspondientes y restaurar objetos/grants. No se presupone superusuario. Aprovisionar roles/tablespaces del paquete por separado, sin archivar contraseñas de roles.

BACKUP_RELEASE_TARGET identifica el root backend/frontend. BACKUP_WORKER_EXTERNAL=true debe corresponder a una instalación realmente externa. Definir hooks como arreglos JSON de ejecutable y argumentos, en paths externos al release, sin shell ni comandos desde la API:

| Hook | Contrato |
| --- | --- |
| BACKUP_STOP_HOOK | Detener todas las API/réplicas/workers con pools o escrituras, coordinar frontend/SSR y escritores externos. No detener coordinador/control. Salir 0 solo al confirmar cierre. |
| BACKUP_START_HOOK | Ajustar propietarios/ACL según cuenta del servicio, arrancar réplicas desde release promovido con dependencias compatibles/config externa conservada. Reinicio completo vacía pools/cachés. |
| BACKUP_HEALTH_HOOK | Comprobar procesos, DB, permisos/login, compatibilidad frontend/API y evidencias. Durante barrera HTTP de negocio responde mantenimiento: verificar internamente respetando esa condición. Cualquier fallo retorna distinto de 0. |

Reciben OBRATEC_RESTORE_ID, OBRATEC_BACKUP_ENVIRONMENT, OBRATEC_MAINTENANCE=1 y OBRATEC_RELEASE_TARGET. Salida visible en consola del worker; no imprimir secretos. Si API se detiene durante promoción, UI puede perder conexión: control/consola conservan proceso. Al terminar se requiere nuevo login por epoch revocado.

Desde /backup: elegir/importar, ensayar en base temporal, revisar corte/entorno/alcance/huella. Solo-base no aporta archivos: exige evidencias actuales compatibles. Si VALIDADA, escribir frase exacta y confirmar contraseña de la misma cuenta. Desafío válido una hora, nueva autenticación cinco minutos. Aplicar genera preventiva ensayada, mantenimiento, promoción y salud. Reportes restaurados quedan pausados/en cuarentena; revisar antes de reactivar, porque Brevo no revierte envíos.

Se preservan obratec_old_<id> y .obratec_restore_<id>/previous_release al lado del release. No eliminarlos hasta verificar funcionalidad por actores/tenants/evidencias y nuevas copias fuera del host. La retención no borra estas generaciones. Se prepara en el mismo filesystem del release para renames; el volumen de backups puede ser distinto. PostgreSQL/archivos/software tienen diario y compensación, no transacción común.

## Ensayos y pruebas

BACKUP_REHEARSAL_ENABLED=false por defecto. Habilitar con staging/credenciales designados; intervalo BACKUP_REHEARSAL_INTERVAL_DAYS=7. El worker ensaya una copia reciente después de una creación cuando vence intervalo, sin promover y limpiando staging. El ensayo manual conserva recursos para confirmar o descartar explícitamente.

```powershell
# Backend:
python -m unittest discover -s tests -p "test_backups*.py"
python -m unittest discover -s tests -p "test_reportes*.py"
# Frontend:
npm.cmd run test:backups
npm.cmd run test:reportes
npm.cmd run build
```

Ensayo PostgreSQL real: clúster desechable DIFERENTE del host/puerto de negocio, PostgreSQL 17, herramientas y BACKUP_TEST_ADMIN_DSN seguro hacia postgres con CREATEDB:

```powershell
python tests/backups_disposable_check.py --environment pruebas-desechables --allow-create-disposable-databases
```

Crea/limpia solo sus obratec_test_*/obratec_stage_*, prueba dos tenants, datos, funciones/procedimiento/trigger, FK, secuencias y evidencias. No se ejecutó en esta entrega sin clúster/herramientas designados. Ensayar adicionalmente promoción con hooks reales y recuperación S3 en staging antes de producción.

## Recuperación independiente

Si falla login/negocio, usar consola externa con control, claves y credenciales operativas. Sustituir IDs/entorno; comandos mutantes requieren confirmación específica:

```powershell
python backup_recovery.py --environment desarrollo-designado --status
python backup_recovery.py --environment desarrollo-designado --register D:/copias/archivo.obratec
python backup_recovery.py --environment desarrollo-designado --validate ID_ARCHIVO
python backup_recovery.py --environment desarrollo-designado --apply ID_RESTAURACION --confirm "RESTAURAR TODOS LOS TENANTS ID_RESTAURACION"
python backup_recovery.py --environment desarrollo-designado --rollback ID_RESTAURACION --confirm "RESTAURAR TODOS LOS TENANTS ID_RESTAURACION"
python backup_recovery.py --environment desarrollo-designado --discard-validation ID_RESTAURACION --confirm "DESCARTAR ENSAYO ID_RESTAURACION"
```

Tras pérdida completa, primero aprovisionar PostgreSQL/roles/tablespaces/secretos/control y root de release con directorios backend/frontend. Recuperar ciphertext externo, reconstruir catálogo y ensayar. `--apply ... --disaster` admite ausencia comprobada de la base original y registra preventiva imposible. No permite saltarla de una base existente. Si todo el clúster está inaccesible, recuperar infraestructura/conectividad primero.

Lease expirada no libera barrera/escritores. Inspeccionar procesos, queries, archivos y diario, detener escritores huérfanos, y solo entonces:

```powershell
python backup_recovery.py --environment desarrollo-designado --clear-writer ID_ESCRITOR --confirm "ESCRITOR TERMINADO ID_ESCRITOR"
# Solo SIN promociones y SIN escritores:
python backup_recovery.py --environment desarrollo-designado --release-maintenance ID_PROPIETARIO --confirm "RESTAURAR TODOS LOS TENANTS ID_PROPIETARIO"
```

Si hay diario, compensar; no liberar arbitrariamente. Mantener REQUIERE_INTERVENCION cuando recursos no concuerdan. No importar SQL de terceros mediante la UI.

`--rollback` sirve para promociones interrumpidas; no revierte un diario COMPLETADA histórico, que podría descartar modificaciones nuevas sin preventiva. Para recuperar la generación de una restauración ya completada, validar y aplicar su copia preventiva mediante el flujo normal.

## Custodia adicional

Respaldar control independientemente con herramientas PostgreSQL, cifrando su artefacto según operación designada y sin passwords en argumentos/logs. Custodiar fuera: claves por key_id, configuración, roles/grants sin passwords, mapping owners/tablespaces, hooks, IAM/S3 y dependencias. Eso permite recrear control y registrar paquetes cuando se pierde catálogo.

No incluye PITR/WAL, restauración por tenant ni aprovisionamiento automático de DNS/IAM/red/clúster/cuentas externas o apps móviles instaladas. El corte recuperable es un snapshot completo validado; infraestructura depende del runbook del entorno.
