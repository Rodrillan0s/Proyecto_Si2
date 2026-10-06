# Resultado de la prueba de backups en Ubuntu Server

Fecha: 2026-10-04 (America/La_Paz). Entorno cargado: `ubuntu-desarrollo-designado`.

## Resultado

**La copia de solo base llegó a `LISTO` y su integridad se verificó correctamente.** El usuario autorizó ignorar temporalmente tres imágenes ausentes que atribuye a su colega. Sus filas originales permanecen en el dump y la ausencia está registrada explícitamente en el manifiesto; no se certifica recuperación de esas imágenes. `sistema_completo` continúa exigiendo archivos.

Trabajo: `e0077463-1e21-41c2-939a-1d548baeb267`. Archivo: `obratec_e0077463-1e21-41c2-939a-1d548baeb267.obratec`, **978864 bytes**, inventario de **132 tablas**. SHA256: `83b95fdd96f4a47c711208354fcb4582e5cea114159cce7a3dd5c9f862a301de`. Se comprobó el archivo mediante el servicio de descarga, descifrado autenticado, comparación de manifiesto/control y `pg_restore --list`. Se puede descargar desde `/backup`, historial del trabajo LISTO.

No se restauró ni sustituyó la base de negocio. La pasada de prueba terminó, se liberó el mantenimiento y no dejó escritores registrados. No se dejó backend/worker adicional en segundo plano.

## Comprobaciones reales

| Comprobación | Resultado |
| --- | --- |
| Negocio en Ubuntu | Conexión de solo lectura a `obras`, PostgreSQL `17.11 (Ubuntu 17.11-1.pgdg22.04+2)`. |
| Control independiente | Conexión a `obratec_control`; siete tablas presentes y fila de control inicializada. |
| Configuración de creación | `BACKUP_ENABLED`, volumen persistente y coordinación declarados activos; clave de 32 bytes válida. |
| Herramientas Windows | `pg_dump` y `pg_restore` 17.11, compatibles con el servidor. |
| Preflight de creación | Conexión, versiones, cuota y espacio disponibles: correcto. |
| Primera copia manual pendiente | Falló después del volcado al validar las rutas de evidencias Windows; se corrigió esa incompatibilidad. |
| Nueva copia manual de solo base | Procesada con una pasada visible de `backup_worker.py --once`, terminó LISTO y verificada. |
| Volcado PostgreSQL | Catálogo legible, inventario de 132 tablas y registros originales preservados. |
| Evidencias | Tres archivos ausentes registrados en el manifiesto por autorización del usuario, sin borrar sus filas. |
| Estado posterior | Mantenimiento desactivado; sin escritores registrados ni restauraciones en cola. |
| Automatización | No hay programación guardada ni proceso continuo iniciado por esta prueba. El latido reciente puede mostrarse activo dos minutos tras acabar la pasada. |
| Restauración | Deshabilitada; faltan DSN de restauración, hooks, release objetivo e instalación externa del worker. |
| Réplica externa | S3 no configurado; no se verificó recuperación fuera del equipo. |

Los dos trabajos fallidos del historial se conservaron como evidencia. No se actualizó su estado a éxito ni se eliminaron referencias o archivos de negocio.

## Correcciones realizadas

Incidencias guarda `ruta_archivo` usando `os.path.join`, con `\` en Windows. Backup exigía exclusivamente `/` antes de interpretar esa referencia y rechazaba la captura. Ahora el adaptador de evidencias normaliza la ruta relativa para resolverla bajo `backend/uploads` y usarla en el manifiesto; el inventario PostgreSQL conserva el valor original. El parser del paquete sigue rechazando rutas absolutas, UNC, unidades y traversal.

La ausencia de archivos se identifica con `BACKUP_EVIDENCE_UNAVAILABLE` en copias completas. Por autorización posterior del usuario, las de solo base permiten esa ausencia y la registran en `evidencias_no_disponibles`; el ensayo/promoción existente rechaza certificar recuperación completa de esos paquetes. [Decisión y alcance](decisiones/2026-10-04-backup-base-evidencias-ausentes.md).

Se aisló `BACKUP_ENABLED` en las pruebas API para que la configuración real habilitada no las hiciera conectar al control durante el caso de reautenticación.

Validación ejecutada: **47 pruebas backend aprobadas** tras el ajuste de omisión; **13 frontend aprobadas** en la prueba previa del mismo entorno (sin cambios frontend posteriores). Casos nuevos cubren ruta Windows, rechazo de traversal, paquete cifrado de solo base con ausencia registrada y advertencia/bloqueo de certificación completa. La nueva copia real LISTO pasó verificación de cifrado, huella y catálogo; no se ejecutó restauración real en staging ni promoción.

## Cómo repetir el diagnóstico

Desde `backend`, con la configuración actual y el entorno Python del proyecto:

```text
python tests/backups_configured_check.py --environment ubuntu-desarrollo-designado
python tests/backups_configured_check.py --environment ubuntu-desarrollo-designado --preflight --scope base_datos
```

El primer comando consulta estado y comprueba existencia de archivos sin imprimir credenciales ni referencias de imágenes. `--preflight` además prepara/verifica el directorio configurado y calcula las huellas de las evidencias disponibles; `--scope base_datos` informa las ausentes sin bloquear. Estos comandos no ejecutan la cola ni migran/restauran PostgreSQL. El argumento explícito `--retry-manual ID_FALLIDO` puede encolar una copia nueva de solo base revalidando al actor original; conserva el trabajo fallido y no ejecuta el worker.

Después de conseguir una copia `LISTO`, su identificador permite comprobar almacenamiento, SHA256, cifrado autenticado, manifiesto, evidencias y lectura del catálogo del dump sin promover una restauración:

```text
python tests/backups_configured_check.py --environment ubuntu-desarrollo-designado --verify-job ID_EJECUCION
```

La verificación usa un temporal bajo el directorio de trabajo configurado y lo limpia al terminar. No equivale a un ensayo de restauración en staging.

## Paso pendiente

Para continuar con copias de PostgreSQL, elegir **Solo base de datos** en `/backup`. Para certificar una copia completa, recuperar los tres archivos originales y hacerlos accesibles al worker en el release designado. Para automatización continua, guardar la programación y ejecutar un worker supervisado con conectividad permanente hacia Ubuntu. Restauración sigue requiriendo su configuración y ensayo independientes.

Referencias: [arquitectura](ARQUITECTURA_BACKUP_RESTORE.md), [operación](OPERACION_BACKUPS.md), [guía Ubuntu](HABILITAR_BACKUPS_UBUNTU_SERVER.md), [decisión y análisis de la corrección](decisiones/2026-10-04-prueba-backups-configurados.md).
