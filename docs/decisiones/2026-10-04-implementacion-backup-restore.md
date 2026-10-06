# Implementación de Backup/Restore

Estado: plan aprobado e implementado en código; activación y ensayo del despliegue pendientes de entorno designado.

Se revisaron AGENTS.md, arquitectura general, base de datos, inventario/rutinas y los flujos actuales de backup, autenticación, evidencias y worker de Reportes antes de modificar código. El contrato aprobado está en [el plan](../PLAN_BACKUP_RESTORE.md).

Se mantiene `routes → services → repos`. El repositorio de control utiliza una base PostgreSQL independiente y migración explícita; no se crean objetos durante el arranque HTTP. Backup/Restore es global, sin filtro de empresa, con comprobación del rol ADMINISTRADOR activo en la base actual. Trabajos, leases, mantenimiento, sesiones y diario de promoción sobreviven a la restauración de la base de negocio.

Los adaptadores separan PostgreSQL, paquetes, cifrado, almacenamiento y coordinación de restauración. La restauración primero crea una base temporal y compara el inventario; luego exige confirmación vinculada al artefacto, reautenticación y hooks operativos configurados. Base, archivos y software requieren pasos compensables; no se declara atomicidad entre ellos.

Los respaldos completos coordinan escritores HTTP y workers mediante control compartido y conservan evidencias y software sin secretos. La activación requiere coordinar también escritores externos. La ausencia de configuración se presenta como condición de instalación; no como éxito simulado. Con control activado, un fallo del control no permite escrituras ni autenticación silenciosamente.

Validación prevista: pruebas aisladas de autorización, contratos, programación, cifrado, archivos maliciosos, mantenimiento, cola y recuperación; pruebas Angular y compilación. No se restaura la base configurada ni se inicia un backend/worker oculto. La integración PostgreSQL destructiva queda limitada a un entorno desechable designado explícitamente.

## Resultado implementado

Se sustituyeron backend y pantalla `/backup`. Se agregaron cola/leases/eventos/control independientes, siete tablas y migrador explícito, preflight de herramientas/versiones/cuotas, calendario IANA, cifrado streaming AES-256-GCM, paquetes con inventario/hashes, volumen persistente y adaptador S3, validación en staging, confirmación con nueva autenticación, preventiva ensayada, promoción con diario/compensación y consola independiente de recuperación. El ensayo periódico es opcional y queda desactivado por defecto.

Autorización fresca sin selección de empresa; guard exclusivo ADMINISTRADOR. La barrera registra HTTP y worker Reportes, fail-closed cuando el control activado falla. Epoch revoca JWT después de promoción, y hooks deben reiniciar todas las réplicas/pools/cachés. Reportes restaurados se pausan/ponen en cuarentena para evitar repetir efectos de Brevo. Reautenticación errónea conserva una sesión válida mediante código diferenciado en el interceptor.

La preparación de archivos se hace en un directorio hermano del release para renames en su mismo filesystem. Se conserva software/base anteriores y secretos externos; el worker debe estar instalado fuera del release. La copia preventiva es obligatoria para una base existente. La consola `--disaster` contempla únicamente una base ya ausente y registra esa excepción; la compensación no revierte un diario histórico completado.

Referencias de mantenimiento actualizadas: [arquitectura de backups](../ARQUITECTURA_BACKUP_RESTORE.md), [operación](../OPERACION_BACKUPS.md), arquitectura general/base y arquitectura/operación de Reportes. El plan conserva el diseño aprobado y enlaza la implementación real.

## Validación ejecutada

- Backend Backup/Restore: **43 pruebas aisladas aprobadas**, sin conexión a PostgreSQL ni emails. Cubren autorización fresca/epoch, contratos/calendario, cifrado real con alteraciones, extracción insegura, publicación de paquetes, inventario discrepante, barrera y compensación.
- Backend Reportes: **54 pruebas aprobadas**, regresión del módulo y fábrica.
- Frontend Backup/Restore: **13 pruebas aprobadas**, contratos HTTP y operaciones/estados de página.
- Frontend Reportes/asistente: **21 pruebas aprobadas**.
- Compilación Python y entradas CLI `--help`: correctas.
- Angular producción: compilación correcta. Persisten avisos anteriores de presupuesto CSS/fuentes y Leaflet CommonJS; los estilos de Backup no añaden exceso de presupuesto.
- Ensayo de PostgreSQL 17 con dos tenants y objetos/evidencias preparado en `backups_disposable_check.py`, no ejecutado: faltan herramientas/clúster desechable designados. Promoción con hooks reales, ACL del host y recuperación S3 requieren aceptación en staging.

No se modificó .env, no se aplicó la migración al servidor actual, no se generó/restauró una copia real ni se dejó backend/worker oculto. Dependencias cryptography 50.0.2 y boto3 instaladas para pruebas locales. La UI muestra requisitos concretos antes de habilitar operaciones; no declara automáticamente un servidor protegido.
