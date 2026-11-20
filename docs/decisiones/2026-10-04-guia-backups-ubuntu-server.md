# Guía de habilitación de backups con PostgreSQL en Ubuntu Server

Fecha: 2026-10-04. Cambio exclusivamente documental.

El usuario confirmó que el acceso a su base se realiza a través de Ubuntu Server. No confirmó que el backend/worker estén desplegados allí ni si utiliza conexión directa, túnel SSH o PostgreSQL en contenedor. La guía distingue esos escenarios y conserva el host/puerto que ya utiliza el backend. No se inspeccionó nuevamente el servidor.

Se revisaron las referencias de arquitectura general, PostgreSQL y Backup/Restore, el runbook, la plantilla de configuración, el migrador y los adaptadores actuales. Se mantienen `routes → services → repos`, control PostgreSQL independiente, herramientas nativas ejecutadas desde el worker, almacenamiento externo al release y restauración con ensayo y compensaciones. No cambia ningún contrato HTTP, esquema, patrón ni permiso: los backups siguen siendo globales para ADMINISTRADOR, sobre todos los tenants.

La [guía de habilitación](../HABILITAR_BACKUPS_UBUNTU_SERVER.md) explica aprovisionamiento del control en la instancia correcta, configuración local Windows o Ubuntu, claves, migración explícita, worker visible, automatización y condiciones de restauración. El servidor de PostgreSQL y el equipo que almacena los paquetes son responsabilidades distintas. Una conexión SSH no reemplaza las credenciales PostgreSQL ni configura por sí sola TLS de PostgreSQL.

Se enlaza la guía desde operación y arquitectura, y se registra Ubuntu Server como contexto comunicado por el usuario en la referencia de base de datos. La versión 17.11 continúa siendo la fotografía de la inspección anterior, no una comprobación nueva.

Validación: revisión de comandos y variables contra el código; comprobación local de enlaces relativos y formato. No se editó `.env`, no se conectó a Ubuntu, no se instaló software, no se creó la base de control ni se aplicaron migraciones. No se arrancó backend/worker ni se ejecutaron backups o restauraciones reales.
