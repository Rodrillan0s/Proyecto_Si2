# Habilitar copias de respaldo con PostgreSQL en Ubuntu Server

Fecha: 2026-10-04. Guía para la implementación actual de OBRATEC.

**Tu base de datos se accede a través de Ubuntu Server.** Esto no significa que el backend o el worker estén ejecutándose allí: pueden funcionar desde Windows y conectarse a PostgreSQL de forma remota. Esta guía incluye ambas ubicaciones y la alternativa de túnel SSH.

El módulo está implementado, pero su configuración, base de control y ensayo real siguen pendientes. Los comandos de este documento son instrucciones para el operador; no se ejecutaron al redactarlo. Reemplaza todos los valores en mayúsculas por los de tu entorno antes de usarlos. No copies las credenciales de ejemplo.

Estado posterior a esta guía: control instalado y conexión Ubuntu verificada. El usuario autorizó respaldos de **solo base** con imágenes externas faltantes: se registran como ausentes en el manifiesto sin modificar sus filas; `sistema_completo` sigue exigiendo los archivos. Consultar [resultado actualizado](PRUEBA_BACKUPS_UBUNTU_2026-10-04.md) y [decisión](decisiones/2026-10-04-backup-base-evidencias-ausentes.md).

Referencias: [operación y recuperación](OPERACION_BACKUPS.md), [arquitectura implementada](ARQUITECTURA_BACKUP_RESTORE.md), [plantilla de variables](../backend/backup.env.example) y [decisión documental](decisiones/2026-10-04-guia-backups-ubuntu-server.md).

## 1. Dónde se ejecuta cada componente

| Componente | Ubicación y responsabilidad |
| --- | --- |
| PostgreSQL de negocio | Instancia a la que accedes mediante Ubuntu Server. Conservar su host, puerto y base actuales. |
| PostgreSQL de control | Otra base, por ejemplo `obratec_control`. Puede estar en la misma instancia de Ubuntu, pero debe tener nombre distinto del negocio. |
| Backend | Equipo donde ejecutas actualmente la API. Lee su configuración segura y expone `/backup`. |
| Worker | Ejecuta los respaldos y las programaciones. Para empezar, usar el mismo equipo y configuración del backend. |
| `pg_dump` y `pg_restore` | Instalar en el equipo del worker. Tenerlos solo en Ubuntu no basta si el worker corre en Windows. |
| Directorio de backups | Disco del equipo del worker, fuera del proyecto y del release, con permisos restringidos y espacio suficiente. |
| Evidencias y software | Deben estar disponibles para el worker en las rutas reales del despliegue cuando se elige ese alcance. |

Los respaldos son **globales**, sobre todas las empresas. Se accede con el rol `ADMINISTRADOR`; `ADMINISTRADOR_EMPRESA` no habilita este módulo.

Si trabajas desde Windows y la base está en Ubuntu, puedes respaldarla sin instalar otro servidor PostgreSQL local: necesitas las herramientas cliente y conectividad con la instancia existente. Los paquetes se guardarán en Windows, no automáticamente en Ubuntu.

## 2. Confirmar la instancia de PostgreSQL

Conserva los valores actuales de `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER` y `DB_PASSWORD` que ya permiten funcionar al backend. No reemplaces el puerto por `5432` sin comprobarlo: el puerto publicado puede diferir del interno.

La inspección anterior documentó PostgreSQL **17.11** y la base `obras`. Confirma la versión y el destino antes de aprovisionar el control; esa inspección no determina si tu entorno es desarrollo o producción.

Si administras una instalación nativa mediante SSH, abre una terminal visible:

```bash
ssh USUARIO_SSH@HOST_UBUNTU
sudo -u postgres psql -p PUERTO_INTERNO_REAL -d postgres
```

Dentro de `psql` puedes comprobar:

```sql
SELECT current_database(), version(), inet_server_addr(), inet_server_port();
SHOW port;
```

`inet_server_addr()` puede devolver NULL si accediste por socket local. Si PostgreSQL corre en Docker o tu cuenta no administra la instalación nativa, usa el método de administración existente y el puerto de esa instancia. No presupongas un nombre de contenedor o un clúster predeterminado.

## 3. Crear la base de control en Ubuntu

En la instancia designada, una cuenta con permisos de administración crea el usuario y la base independientes. Si ya existen, comprobarlos y reutilizarlos en vez de repetir la creación.

```sql
CREATE ROLE obratec_backup_control LOGIN;
\password obratec_backup_control
CREATE DATABASE obratec_control OWNER obratec_backup_control;
```

`\password` solicita la contraseña interactivamente. Este usuario administra los objetos de su base de control; no necesita convertirse en superusuario ni ser el usuario SSH.

El backend y el worker deben poder conectar a `obratec_control`. Revisa las reglas existentes de `pg_hba.conf`, el firewall y la ruta de acceso para autorizar específicamente esa base, usuario y origen. Que la cuenta de negocio conecte no demuestra que la nueva cuenta esté admitida. Mantén las restricciones actuales de red y autenticación.

El migrador de OBRATEC crea las tablas dentro del control; **no crea la base ni el usuario**. No aplicar su SQL a `obras`.

## 4. Preparar el equipo del backend y worker

### Si los ejecutas desde Windows

Instala herramientas cliente PostgreSQL 17 y comprueba las rutas. Desde PowerShell:

```powershell
& 'C:\Program Files\PostgreSQL\17\bin\pg_dump.exe' --version
& 'C:\Program Files\PostgreSQL\17\bin\pg_restore.exe' --version
```

Si la instalación está en otro directorio, usar su ruta real. Crea un directorio externo para los paquetes:

```powershell
New-Item -ItemType Directory -Force -Path 'D:\OBRATEC_DATA\backups'
```

Restringe sus ACL NTFS a la cuenta que ejecuta backend/worker y a los administradores responsables. `BACKUP_STORAGE_PERSISTENT=true` requiere un volumen realmente persistente y accesible; no basta con cambiar la variable.

Desde el directorio del proyecto:

```powershell
cd backend
# Activar primero el entorno virtual que utiliza el proyecto.
python -m pip install -r requirements.txt
python -m pip install -r requirements-backup.txt
```

### Si los ejecutas desde Ubuntu

Esta alternativa aplica cuando backend y worker están desplegados en Ubuntu con el release y las evidencias reales. Un worker aislado en Ubuntu sin los archivos del backend de Windows no puede producir una copia completa de esos archivos.

Verifica las herramientas donde se ejecutará el worker:

```bash
/usr/lib/postgresql/17/bin/pg_dump --version
/usr/lib/postgresql/17/bin/pg_restore --version
apt-cache policy postgresql-client-17
```

Si faltan y el paquete tiene candidato en tus repositorios:

```bash
sudo apt update
sudo apt install postgresql-client-17
```

Si no aparece candidato, consulta el [repositorio oficial de PostgreSQL para Ubuntu](https://www.postgresql.org/download/linux/ubuntu/) y configura el repositorio adecuado a tu versión de Ubuntu. Instala el cliente 17; no sustituir ni actualizar el servidor existente para habilitar este módulo.

Prepara un volumen externo propiedad de la cuenta del servicio. Sustituye `USUARIO_APP` y `GRUPO_APP` por los reales:

```bash
sudo install -d -m 0700 -o USUARIO_APP -g GRUPO_APP /var/lib/obratec-backups
cd /RUTA_REAL/Proyecto_Si2/backend
# Usar el entorno virtual existente; si no existe, crear uno compatible con el proyecto:
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install -r requirements-backup.txt
```

Usa en la configuración las rutas `/var/lib/obratec-backups`, `/usr/lib/postgresql/17/bin/pg_dump` y `/usr/lib/postgresql/17/bin/pg_restore` en lugar de las rutas Windows del siguiente ejemplo.

## 5. Configuración inicial y clave de cifrado

En la terminal del equipo del worker, usando el entorno virtual del proyecto, genera una clave:

```text
python -c "import secrets,base64; print(base64.b64encode(secrets.token_bytes(32)).decode())"
```

Custódiala fuera de los paquetes y del repositorio. Mantén las claves antiguas mientras conserves copias que las usen. Una copia cifrada no puede recuperarse si se pierde su clave.

Añade estas variables al `.env` que carga el backend o a su configuración segura de despliegue. Backend y worker deben usar los mismos valores de control, entorno y claves. Conserva las variables `DB_*` existentes.

Ejemplo para worker en Windows y conexión directa al PostgreSQL de Ubuntu:

```dotenv
BACKUP_ENABLED=false
BACKUP_ENVIRONMENT=ubuntu-desarrollo-designado
BACKUP_CONTROL_DSN=postgresql://obratec_backup_control:CLAVE_URL_CODIFICADA@HOST_ACTUAL:PUERTO_ACTUAL/obratec_control?sslmode=require
BACKUP_DIRECTORY=D:/OBRATEC_DATA/backups
BACKUP_STORAGE_PERSISTENT=false
BACKUP_EXTERNAL_WRITERS_COORDINATED=false
BACKUP_KEY_ID=local-2026
BACKUP_KEYS_JSON='{"local-2026":"PEGAR_CLAVE_BASE64"}'
BACKUP_PG_DUMP_PATH=C:/Program Files/PostgreSQL/17/bin/pg_dump.exe
BACKUP_PG_RESTORE_PATH=C:/Program Files/PostgreSQL/17/bin/pg_restore.exe
DB_SSLMODE=require
BACKUP_RESTORE_ENABLED=false
BACKUP_REHEARSAL_ENABLED=false
```

`HOST_ACTUAL` y `PUERTO_ACTUAL` son el destino alcanzable desde el worker. La contraseña de una URI PostgreSQL debe codificar caracteres reservados como `@`, `:`, `/`, `#` o `%`. No pegar una contraseña sin codificar dentro de esa URI si contiene esos caracteres.

El nombre de entorno es una etiqueta que eliges para el despliegue; no garantiza que la base sea de desarrollo. Si designas otro entorno, cambia también los argumentos `--environment` de los comandos siguientes.

El ejemplo asume PostgreSQL con TLS habilitado. `DB_SSLMODE` controla la conexión de negocio del adaptador de backups; la conexión de control utiliza su propio `sslmode` en la URI. Conserva la política de TLS validada para tu despliegue. Si usas certificados y verificación de identidad, revisa su configuración antes de sustituirla por este ejemplo. [Modos SSL de PostgreSQL](https://www.postgresql.org/docs/17/libpq-ssl.html).

## 6. Aplicar la migración solamente al control

Desde `backend`, en el equipo del backend/worker y con el entorno virtual activo:

```text
python migrate_backups.py --environment ubuntu-desarrollo-designado
```

Comprueba el destino configurado. Si el control está recién creado, es esperable que informe que no hay tablas. Para instalar los objetos allí:

```text
python migrate_backups.py --environment ubuntu-desarrollo-designado --apply
python migrate_backups.py --environment ubuntu-desarrollo-designado
```

La verificación debe listar siete tablas del esquema `backup_control`. La presencia del [script SQL](../backend/database/20261004_backup_control.sql) en el proyecto no significa que la migración esté aplicada. Puede ejecutarse con `BACKUP_ENABLED=false` durante la preparación.

## 7. Activar backups manuales y automáticos

Antes de activarlos, comprueba herramientas, claves, tablas de control, permisos y espacio. La cuenta PostgreSQL de negocio debe poder respaldar toda la base, incluidos sus esquemas y objetos; no solo las tablas de una empresa. Coordina además otros procesos que escriban, integraciones y SQL directo.

Cuando esas condiciones se cumplan, actualizar:

```dotenv
BACKUP_ENABLED=true
BACKUP_STORAGE_PERSISTENT=true
BACKUP_EXTERNAL_WRITERS_COORDINATED=true
```

Reinicia el backend en tu terminal habitual para cargar la configuración. En **otra terminal visible**, desde `backend` y con el mismo entorno virtual/configuración:

```text
python backup_recovery.py --environment ubuntu-desarrollo-designado --preflight
python backup_worker.py --interval 15
```

Si todavía no configuraste restauración, sus requisitos pendientes en el preflight son esperables: manuales y programación pueden operar con `BACKUP_RESTORE_ENABLED=false`. Los requisitos pendientes de creación sí deben resolverse.

En la web:

1. Inicia sesión como administrador global.
2. Abre **Copias de respaldo**, ruta `/backup`.
3. Comprueba configuración y latido del worker.
4. Crea una copia manual y verifica que llegue a `LISTO` en el historial.
5. Descarga el archivo `.obratec`, que es un paquete cifrado.
6. Guarda una programación con frecuencia, hora, zona horaria y retención. Mantén el worker operativo para que se ejecute.

La API no inicia el worker automáticamente. Si corre en tu Windows, las programaciones requieren que ese equipo esté encendido, conectado a Ubuntu y con el worker activo. Para operación continua, instalarlo como servicio supervisado en el equipo elegido; los nombres y comandos del servicio dependen del despliegue real.

El alcance de una copia completa incluye las evidencias y el software disponibles en el despliegue del worker. Un dump PostgreSQL no respalda por sí solo los roles globales y tablespaces del clúster: su aprovisionamiento se conserva por separado. [Alcance de pg_dump](https://www.postgresql.org/docs/17/app-pgdump.html).

Para protección ante pérdida del equipo que almacena los backups, configura y verifica la réplica privada S3 compatible descrita en [operación](OPERACION_BACKUPS.md). Guardar en un disco local no acredita una copia fuera de ese equipo.

## 8. Si accedes a PostgreSQL por túnel SSH

Usa esta alternativa solo si es tu método de acceso real. El módulo no abre ni mantiene túneles automáticamente. Desde una terminal que permanecerá abierta en el equipo del backend/worker:

```text
ssh -N -L 127.0.0.1:15433:127.0.0.1:PUERTO_PG_INTERNO USUARIO_SSH@HOST_UBUNTU
```

Este ejemplo supone que PostgreSQL es accesible desde Ubuntu en `127.0.0.1:PUERTO_PG_INTERNO`. Si está en otra máquina o red de contenedores, el destino del túnel debe ser el que realmente alcanza el servidor SSH. `15433` debe estar libre en tu equipo.

Para usar ese túnel, backend y worker deben conectar al mismo extremo local:

```dotenv
DB_HOST=127.0.0.1
DB_PORT=15433
BACKUP_CONTROL_DSN=postgresql://obratec_backup_control:CLAVE_URL_CODIFICADA@127.0.0.1:15433/obratec_control?sslmode=require
```

Mantén el resto de las credenciales y nombre de negocio. La cuenta SSH y la cuenta PostgreSQL son distintas. SSH cifra su transporte, pero no habilita TLS dentro de PostgreSQL: `sslmode=require` sigue requiriendo TLS PostgreSQL real. Si tu despliegue utiliza otra política para PostgreSQL dentro del túnel, alinea ambos clientes con esa política comprobada; no cambies el modo a ciegas para ocultar un error. [OpenSSH en Ubuntu](https://ubuntu.com/server/docs/how-to/security/openssh-server/).

Cuando el túnel se cierre, backend y worker perderán acceso al negocio y al control. La automatización necesita también que esta conexión se mantenga disponible.

## 9. Habilitar restauración después de preparar el despliegue

Crear copias y restaurar son capacidades separadas. Mantén `BACKUP_RESTORE_ENABLED=false` hasta contar con un entorno designado para ensayos y con estos requisitos:

- Cuenta de restauración con permisos para crear bases, restaurar propietarios/grants y administrar las conexiones correspondientes.
- `BACKUP_RESTORE_DSN` hacia la base `postgres`, usando **exactamente el mismo host y puerto** que `DB_HOST` y `DB_PORT`. Con túnel, también debe usar `127.0.0.1:15433`.
- `BACKUP_RELEASE_TARGET` apuntando al release real con `backend` y `frontend`.
- Worker y su Python instalados realmente fuera del release que se reemplazará; entonces `BACKUP_WORKER_EXTERNAL=true`.
- Hooks reales de detener servicios, arrancarlos y comprobar salud. Se ejecutan en el equipo del worker y deben coordinar las ubicaciones reales de los servicios.
- Roles, extensiones y tablespaces requeridos disponibles en PostgreSQL, y ensayo exitoso del paquete en una base temporal.

Si backend está en Windows y PostgreSQL en Ubuntu, los hooks deben coordinar los procesos Windows; no basta con escribir comandos `systemctl` para Ubuntu. PostgreSQL y la base de control deben seguir disponibles durante la restauración.

No usar hooks de ejemplo que devuelvan éxito sin comprobar los servicios. El flujo de restauración exige ensayo, confirmación explícita, nueva autenticación y copia preventiva. Consulta [habilitación y recuperación operativa](OPERACION_BACKUPS.md) para ejecutarlo y para recuperación desde consola si la API está detenida.

## 10. Diagnóstico rápido

| Situación | Qué comprobar |
| --- | --- |
| No se encuentra `pg_dump` / `pg_restore` | Instalación y rutas en el equipo del worker, no solo en Ubuntu. |
| No conecta a negocio o control | Host/puerto, ruta de red/túnel, cuenta, contraseña, TLS y autorización específica en PostgreSQL. |
| Negocio conecta y control falla | Existencia de `obratec_control`, su usuario y reglas de acceso; URI con contraseña codificada. |
| Control sin tablas | Ejecutar y verificar el migrador sobre la base independiente designada. |
| Clave inválida | Clave Base64 de 32 bytes, JSON válido y `BACKUP_KEY_ID` presente en ese JSON. |
| Carpeta rechazada | Directorio externo al proyecto/release, sin usar la raíz del disco, con permisos y espacio suficientes. |
| Copia queda pendiente | Worker activo, misma configuración y latido reciente; revisar su terminal visible. |
| Programación guardada sin ejecuciones | Worker continuo, equipo encendido, conectividad y zona/hora programadas. |
| Restauración deshabilitada | Completar sus requisitos adicionales; no se habilita solo activando backups. |

Una copia `LISTO` acredita creación del paquete. La recuperación completa requiere además un ensayo real con el despliegue y las credenciales designadas.
