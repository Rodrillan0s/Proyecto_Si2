# Verificaci?n de CU19 en PostgreSQL real ? 2026-10-02

Migraci?n aplicada: `migration_cu19_validacion.sql`, sin editar el SQL ni el c?digo de negocio.
Servidor comprobado: PostgreSQL 17.11; base `obras`, esquema `obras`.

## An?lisis antes de ejecutar

- `t_incidencia`: 14 columnas; estado era VARCHAR(20), NOT NULL, DEFAULT ABIERTA. Fechas de inicio/fin son timestamptz opcionales. Responsable mantiene FK a t_usuario; obra y unidad mantienen sus FK.
- `t_incidencia_seguimiento`: 7 columnas; estado_anterior y estado_nuevo eran VARCHAR(20); solo estado_anterior admite NULL.
- Los CHECK existentes admit?an ABIERTA, ASIGNADA, EN_PROCESO, RESUELTA y CERRADA. Las cuatro restricciones que elimina la migraci?n exist?an y estaban validadas.
- Hab?a tres incidencias reales: #1 RESUELTA (responsable 6), #9 RESUELTA (responsable 14), #10 ASIGNADA (responsable 6). Todas eran compatibles con las nuevas restricciones de fechas. El seguimiento ten?a 13 registros, todos compatibles.
- Se revisaron dependencias y trigger: el ?nico trigger propio de incidencia actualiza updated_at al hacer UPDATE; el DDL no lo activa. No hay DML, CASCADE, cambios de FK, OT ni permisos en la migraci?n.
- La sintaxis se verific? ejecutando el cuerpo exacto del SQL sobre PostgreSQL real dentro de una transacci?n revertida. Todas las filas de las 66 tablas del esquema conservaron sus conteos y hashes.
- No se detect? necesidad de corregir la migraci?n. No elimina ni convierte estados hist?ricos; RESUELTA sigue v?lida. Los endpoints implementados reconocen PENDIENTE_VALIDACION.

## Respaldo y cambios aplicados

Respaldo l?gico focalizado de los datos de incidencia y seguimiento en `backend/.env.cu19-audit/backup_data.sql`; definiciones de restricciones originales en `constraints_before.json`; reversi?n estructural preparada en `rollback_structure.sql`. No es un dump completo de toda la base. La reversi?n estructural requiere que no existan registros PENDIENTE_VALIDACION.

Se guard? una comparaci?n de conteos y SHA-256 de todas las filas de cada una de las 66 tablas, antes, despu?s de la migraci?n y despu?s de las pruebas. Antes de aplicar, se comprob? que los datos segu?an coincidiendo con el respaldo. Se us? una transacci?n y lock_timeout de 5 segundos para el DDL.

Cambios persistentes exactos:
1. t_incidencia.estado: VARCHAR(20) ? VARCHAR(21).
2. t_incidencia_seguimiento.estado_anterior y estado_nuevo: VARCHAR(20) ? VARCHAR(21).
3. Tres CHECK de estados sustituidos para aceptar PENDIENTE_VALIDACION.
4. CHECK de fechas por estado sustituido: PENDIENTE_VALIDACION requiere inicio y fin presentes, igual que RESUELTA/CERRADA.

Estados disponibles: ABIERTA ? ASIGNADA ? EN_PROCESO ? PENDIENTE_VALIDACION ? RESUELTA ? CERRADA. La restricci?n cronol?gica de fechas original sigue vigente; PK, FK, defaults, nullabilidad y relaciones se conservan.

## Pruebas y alcance

Pruebas del router FastAPI real en proceso local conectado a PostgreSQL real. JWT firmados localmente para usuarios existentes; no se prob? el login ni un servidor HTTP desplegado. Un adaptador temporal de conexi?n suprimi? commits para ejecutar todo dentro de una ?nica transacci?n; no se modific? c?digo del sistema. Se suprimi? ?nicamente la escritura de bit?cora para no tocar t_bitacora. Se utilizaron IDs negativos expl?citos para la incidencia temporal y su seguimiento, sin consumir secuencias. Al finalizar se ejecut? ROLLBACK y se verific? igualdad de todas las tablas.

- Lectura de listado y detalle, seguimiento, OT relacionadas y evidencias de #1, #9 y #10: HTTP 200.
- Incidencia temporal ABIERTA; JULIAN asigna a JHON; JHON inicia y finaliza: ASIGNADA ? EN_PROCESO ? PENDIENTE_VALIDACION, HTTP 200.
- JHON ELECTRICO (#14) intenta aprobar: HTTP 403; sigue PENDIENTE_VALIDACION.
- ANDRES JEFE DE OBRA (#4), empresa 3, intenta validar incidencia de empresa 1: HTTP 404; sigue PENDIENTE_VALIDACION.
- JULIAN JEFE DE OBRA (#13) rechaza: HTTP 200, vuelve a EN_PROCESO, conserva fecha de inicio y responsable 14, borra fecha de fin para continuar atenci?n.
- JHON finaliza de nuevo y JULIAN aprueba: HTTP 200, RESUELTA, conserva inicio, responsable y fin de atenci?n.
- Comprobaci?n adicional: JULIAN no dispone del permiso actual de cierre; HTTP 403 al solicitar CERRADA. No se modificaron permisos. La aceptaci?n de CERRADA por PostgreSQL se prob? por SQL ?nicamente sobre la fila temporal, conservando fechas y responsable.

## Integridad final

Las incidencias #1, #9 y #10 conservan todas sus columnas sin cambios; #9 solo se ley?. Los 13 seguimientos, 2 evidencias y 2 v?nculos incidencia?OT permanecen iguales.

Las 4 OT y los 2 registros de t_orden_trabajo_usuario permanecen id?nticos, incluidos sus responsables. Tampoco cambiaron t_obra_usuario, usuarios, roles, permisos o relaciones. El flujo temporal no cambi? ninguna tabla fuera de incidencia y seguimiento, y el rollback elimin? todos sus cambios de prueba. Solo persiste la modificaci?n estructural autorizada.

Evidencia detallada: `backend/.env.cu19-audit/test_results.json`, `before.json`, `after_migration.json`, `after_tests.json` y `structure_after.json`.

Referencia de compatibilidad y validaci?n de CHECK en PostgreSQL: https://www.postgresql.org/docs/17/sql-altertable.html
