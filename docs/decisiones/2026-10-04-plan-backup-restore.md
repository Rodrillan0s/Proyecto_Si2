# Decisión aprobada: respaldo y recuperación globales

Estado: aprobado e implementado en código; consultar la evolución y validación enlazadas al final. Durante el análisis inicial no hubo cambios de código, base, credenciales, servicios o programación.

El análisis del módulo y el plan íntegro están en [PLAN_BACKUP_RESTORE.md](../PLAN_BACKUP_RESTORE.md). Se conserva la arquitectura por capas y se proponen adaptadores para las operaciones externas, worker durable y coordinación de recuperación por etapas.

Las decisiones principales son: alcance global reservado al administrador de plataforma; dump completo de base y paquete con evidencias/versiones; programación real; catálogo y auditoría fuera de la base restaurada; validación en staging; mantenimiento, copia previa y reversión; revocación de sesiones y cuarentena de colas recuperadas para no repetir efectos externos.

La próxima modificación deberá leer primero la arquitectura general, el plan aprobado y las instrucciones del proyecto. Verificar el entorno real antes de concretar la persistencia de control, migraciones y promoción; ninguna configuración histórica de EC2/Render acredita esas capacidades. Registrar por fase qué quedó preparado, aplicado y probado.

## Evolución aprobada

El usuario aprobó la implementación con «procede». Consultar [decisión de implementación](2026-10-04-implementacion-backup-restore.md), [arquitectura real](../ARQUITECTURA_BACKUP_RESTORE.md) y [operación](../OPERACION_BACKUPS.md). La migración de control está preparada y el despliegue real no se activó/restauró durante el desarrollo.
