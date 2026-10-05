# Corrección de tablas pendientes en Reportes

El registro del usuario contiene dos fallos raíz `UndefinedTable`: `obras.t_reporte_ejecucion` y `obras.t_reporte_programacion`. Catálogo y destinatarios funcionan porque consultan objetos anteriores. El código nuevo de persistencia requiere la migración incremental existente `20261004_reportes.sql`.

Se revisaron arquitectura general, arquitectura/operación de Reportes, arquitectura de PostgreSQL y migración. Se preserva `routes → services → repos`. La petición actual de corregir los errores implica completar la instalación del módulo: comprobar precondiciones sobre la conexión configurada y aplicar la migración aditiva existente, en transacción e idempotente. No borra tablas/datos existentes; agrega siete tablas, índices, módulo, permisos y asociaciones por nombre, según el diseño aprobado. No se inicia worker ni backend adicional; el servidor del usuario permanece en su terminal.

Se añade traducción explícita del error de tabla ausente en la frontera del repositorio: respuesta HTTP 503 con indicación de migración requerida, sin devolver SQL ni ocultar otros errores de esquema. No se devuelven listas vacías simulando una instalación correcta y no se ejecuta DDL desde la API.

Validación prevista: preflight y postflight reales de metadatos, pruebas de rollback/traducción de tablas ausentes y suite aislada existente. Registrar por separado aplicación real y ensayos de negocio; no enviar correos ni invocar IA externa.

## Resultado

Preflight real: las siete tablas estaban ausentes y las precondiciones del esquema se cumplieron. Migración aplicada correctamente a la base `obras`, SHA256 `720c2265132f5e64c314c75ce93035bc776edd0260ede05be63c0d052ecb0ee2`. Postflight real de solo lectura: ninguna tabla pendiente. Se conservó el script SQL existente, con BEGIN/COMMIT y lock transaccional.

57 pruebas aisladas pasan, incluidas nuevas pruebas de respuesta 503 sin SQL, cierre de conexión sin commit tras error y propagación de tablas ajenas. Se amplió la comprobación SQL a historial, programaciones, ejecución, archivo, envíos y conversación: 47 consultas aceptadas por PostgreSQL mediante EXPLAIN sin ANALYZE, en conexión de solo lectura. No se leyeron filas de negocio, no se crearon ejecuciones/reportes de prueba reales ni se enviaron correos. La API del usuario permanece bajo su terminal; no se inició otro proceso ni se detuvo el suyo.
