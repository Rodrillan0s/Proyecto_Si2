# Prueba del entorno de backups habilitado

Fecha: 2026-10-04 (America/La_Paz). Solicitada por el usuario tras habilitar la configuración.

Se revisaron arquitectura general, Backup/Restore, operación y referencias de PostgreSQL, además de servicios, repositorio, worker, coordinación, paquetes y pruebas. La configuración cargada identifica `ubuntu-desarrollo-designado`, backups habilitados, claves válidas y herramientas cliente PostgreSQL 17 en Windows. La conexión real de solo lectura confirmó PostgreSQL 17.11 en Ubuntu, negocio `obras` y las siete tablas de control en `obratec_control`. No constituye autorización para promover una restauración ni cambiar la programación.

Se mantienen las capas, permisos ADMINISTRADOR global y alcance de todos los tenants. La comprobación operativa se realizará desde consola visible usando los servicios existentes, sin backend/worker ocultos, sin ejecutar la cola de restauraciones, sin migraciones ni correos. El diagnóstico no imprime DSN, contraseñas, claves ni datos de negocio. La creación manual está autorizada por la solicitud de prueba; puede activar brevemente la barrera habitual de captura y escribir el paquete en el directorio configurado. La restauración está deshabilitada y no se promoverá la base actual.

La primera ejecución de pruebas aisladas encontró una dependencia indebida de `BACKUP_ENABLED` real en el caso de reautenticación: intentaba registrar un escritor en el control. Se aislará la configuración de la clase API para que estas pruebas no accedan al entorno real; el caso dedicado de mantenimiento seguirá probando explícitamente la barrera habilitada.

Validación prevista: repetir pruebas de Backup backend tras corregir aislamiento, ejecutar pruebas Angular, inspeccionar historial/worker real, preflight y, si es viable, copia manual con comprobación de ciphertext, manifiesto y lectura del catálogo del dump. Registrar los resultados reales y los límites al finalizar. No iniciar el worker general, que puede procesar otros trabajos, ni activar programación/retención durante el ensayo.

## Incompatibilidad encontrada en la captura real

La pasada acotada `backup_worker.py --once` procesó únicamente la copia manual pendiente: no había restauraciones ni programación. El volcado se completó, pero el inventario de evidencias rechazó una ruta. Incidencias usa `os.path.join` para persistir rutas relativas y en Windows genera separadores inversos; el formato del paquete exige `/`.

Se normalizarán exclusivamente las referencias de evidencias leídas del negocio antes de resolverlas bajo `backend/uploads` y registrarlas en el manifiesto. Se conservan sin modificación las referencias originales dentro del inventario de base para comparar el ensayo PostgreSQL. No se flexibiliza el parser de nombres de archivos del paquete: siguen prohibidos rutas absolutas, UNC, letras de unidad, segmentos `..` y salidas del árbol uploads. No cambia el esquema ni se actualizan registros de negocio. Se añadirán pruebas con archivo real, referencia Windows y traversal.

## Resultado y validación

Corrección implementada; 45 pruebas backend y 13 Angular aprobadas. Las siete tablas de control están realmente presentes en el servidor, sin ejecutar migración durante esta prueba. La pasada acotada completó el dump y falló antes de publicar el paquete. Tras normalizar rutas, un diagnóstico específico confirmó tres referencias válidas cuyos tres archivos no están en el release local. El usuario indica que están en Windows; pendiente la ruta exacta. No se suprimió esa validación ni se modificaron filas de negocio.

Se agregó una consola de diagnóstico explícita, con comparación obligatoria de entorno, consultas de solo lectura y salida sin secretos. `--preflight` prepara el directorio existente y valida evidencias; `--verify-job` verifica un artefacto LISTO en un temporal limpiado al terminar, sin crear/restaurar bases. No ejecuta la cola, programa envíos ni fuerza estados. [Resultados y repetición](../PRUEBA_BACKUPS_UBUNTU_2026-10-04.md).

Mantenimiento liberado, sin escritores registrados; no se dejaron procesos propios persistentes. Automatización no probada contra calendario real porque no hay programación guardada ni worker continuo. Restauración está deshabilitada; no se ejecutó promoción ni ensayo PostgreSQL real. La corrección no cambia contratos HTTP, roles globales, esquema o el flujo de compensación. La declaración histórica de migración preparada se actualiza con la observación actual del control instalado.
