# Inventario verificado de PostgreSQL / esquema obras

Inspecci?n de solo lectura: 2026-10-04. Base obras, PostgreSQL 17.11. Fotograf?a de cat?logos; no incluye filas de usuarios, empresas, clientes, obras ni contrase?as.

An?lisis: [ARQUITECTURA_BASE_DATOS.md](ARQUITECTURA_BASE_DATOS.md). Rutinas: [BASE_DATOS_RUTINAS.md](BASE_DATOS_RUTINAS.md).

## Roles funcionales y matriz persistida

El bypass de ADMINISTRADOR y las excepciones de actor en el backend no forman parte de esta matriz.

| ID | Rol |
| --- | --- |
| 1 | ADMINISTRADOR |
| 2 | CLIENTE |
| 3 | ADMINISTRADOR_EMPRESA |
| 4 | JEFE DE OBRA |
| 5 | ELECTRICO |
| 6 | PLOMERO |
| 7 | MAESTROALBAÑIL |
| 8 | ALBAÑIL |


| Permiso | IDs registrados | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Anular_costos_ejecutados | 60 | ? | ? | S? | S? | ? | ? | ? | ? |
| Aprobar_ordenes_cambio | 62 | ? | ? | S? | S? | ? | ? | ? | ? |
| Aprobar_ordenes_compra | 48, 44 | ? | ? | S? | S? | ? | ? | ? | ? |
| Aprobar_presupuesto | 30 | S? | ? | S? | S? | ? | ? | ? | ? |
| Asignar_incidencias | 51 | ? | ? | S? | S? | ? | ? | ? | ? |
| Cerrar_incidencias | 54 | ? | ? | S? | S? | ? | ? | ? | ? |
| Desactivar_materiales | 17 | ? | ? | S? | S? | ? | ? | ? | ? |
| Eliminar_empresa | 10 | S? | ? | ? | S? | ? | ? | ? | ? |
| Eliminar_estimaciones | 36 | ? | ? | S? | S? | ? | ? | ? | ? |
| Eliminar_inventario | 16 | S? | ? | S? | S? | ? | ? | ? | ? |
| Eliminar_obras | 7 | S? | ? | S? | S? | ? | ? | ? | ? |
| Eliminar_usuarios | 4 | S? | ? | S? | S? | ? | ? | ? | ? |
| Modificar_clientes | 26 | S? | ? | S? | S? | ? | ? | ? | ? |
| Modificar_empresa | 11 | S? | ? | S? | S? | ? | ? | ? | ? |
| Modificar_estimaciones | 32 | ? | ? | S? | S? | ? | ? | ? | ? |
| Modificar_incidencias | 50 | ? | ? | S? | S? | ? | ? | ? | ? |
| Modificar_inventario | 14 | S? | ? | S? | S? | ? | ? | ? | ? |
| Modificar_materiales | 19 | S? | ? | S? | S? | ? | ? | ? | ? |
| Modificar_obras | 6 | S? | ? | S? | S? | ? | ? | ? | ? |
| Modificar_ordenes_cambio | 61 | ? | ? | S? | S? | ? | ? | ? | ? |
| Modificar_presupuesto | 29 | S? | ? | S? | S? | ? | ? | ? | ? |
| Modificar_proveedores | 22 | ? | ? | S? | S? | ? | ? | ? | ? |
| Modificar_usuarios | 3 | S? | ? | S? | S? | ? | ? | ? | ? |
| Recepcionar_ordenes_compra | 49, 45 | ? | ? | S? | S? | ? | ? | ? | ? |
| Registrar_avances | 56 | ? | ? | S? | S? | ? | ? | ? | ? |
| Registrar_clientes | 25 | S? | ? | S? | S? | ? | ? | ? | ? |
| Registrar_costo_ejecutado | 31 | S? | ? | S? | S? | ? | ? | ? | ? |
| Registrar_costos_ejecutados | 59 | ? | ? | S? | S? | ? | ? | ? | ? |
| Registrar_empresa | 9 | S? | ? | ? | S? | ? | ? | ? | ? |
| Registrar_estimaciones | 33 | ? | ? | S? | S? | ? | ? | ? | ? |
| Registrar_incidencias | 52 | ? | ? | S? | S? | ? | ? | ? | ? |
| Registrar_inventario | 15 | S? | ? | S? | S? | ? | ? | ? | ? |
| Registrar_mano_obra | 37 | ? | ? | S? | S? | ? | ? | ? | ? |
| Registrar_materiales | 18 | S? | ? | S? | S? | ? | ? | ? | ? |
| Registrar_obras | 8 | S? | ? | S? | S? | ? | ? | ? | ? |
| Registrar_ordenes_cambio | 58 | ? | ? | S? | S? | ? | ? | ? | ? |
| Registrar_ordenes_compra | 47, 43 | ? | ? | S? | S? | ? | ? | ? | ? |
| Registrar_presupuesto | 28 | S? | ? | S? | S? | ? | ? | ? | ? |
| Registrar_proveedores | 21 | ? | ? | S? | S? | ? | ? | ? | ? |
| Registrar_usuarios | 2 | S? | ? | S? | S? | ? | ? | ? | ? |
| Visualizar_avances | 55 | ? | S? | S? | S? | ? | ? | ? | ? |
| Visualizar_clientes | 24 | S? | ? | S? | S? | ? | ? | ? | ? |
| Visualizar_control_costos | 57 | ? | ? | S? | S? | ? | ? | ? | ? |
| Visualizar_empresa | 12 | S? | ? | S? | S? | ? | ? | ? | ? |
| Visualizar_estimaciones | 34 | ? | ? | S? | S? | ? | ? | ? | ? |
| Visualizar_incidencias | 53 | ? | ? | S? | S? | ? | ? | ? | ? |
| Visualizar_inventario | 13 | S? | ? | S? | S? | ? | ? | ? | ? |
| Visualizar_mano_obra | 35 | ? | ? | S? | S? | ? | ? | ? | ? |
| Visualizar_materiales | 20 | S? | ? | S? | S? | ? | ? | ? | ? |
| Visualizar_obras | 5 | S? | ? | S? | S? | ? | ? | ? | ? |
| Visualizar_ordenes_compra | 42, 46 | ? | ? | S? | S? | ? | ? | ? | ? |
| Visualizar_presupuesto | 27 | S? | ? | S? | S? | ? | ? | ? | ? |
| Visualizar_proveedores | 23 | ? | ? | S? | S? | ? | ? | ? | ? |
| Visualizar_usuarios | 1 | S? | ? | S? | S? | ? | ? | ? | ? |


## M?dulos y permisos


| ID | M?dulo |
| --- | --- |
| 1 | Modulo_usuarios |
| 2 | Modulo_inventario |
| 3 | Modulo_obras |
| 4 | Modulo_empresa |
| 5 | Modulo_crm |
| 6 | Modulo_presupuestos |


| ID | Permiso | M?dulo |
| --- | --- | --- |
| 26 | Modificar_clientes | Modulo_crm |
| 25 | Registrar_clientes | Modulo_crm |
| 24 | Visualizar_clientes | Modulo_crm |
| 10 | Eliminar_empresa | Modulo_empresa |
| 11 | Modificar_empresa | Modulo_empresa |
| 9 | Registrar_empresa | Modulo_empresa |
| 12 | Visualizar_empresa | Modulo_empresa |
| 16 | Eliminar_inventario | Modulo_inventario |
| 14 | Modificar_inventario | Modulo_inventario |
| 15 | Registrar_inventario | Modulo_inventario |
| 13 | Visualizar_inventario | Modulo_inventario |
| 7 | Eliminar_obras | Modulo_obras |
| 6 | Modificar_obras | Modulo_obras |
| 8 | Registrar_obras | Modulo_obras |
| 5 | Visualizar_obras | Modulo_obras |
| 30 | Aprobar_presupuesto | Modulo_presupuestos |
| 29 | Modificar_presupuesto | Modulo_presupuestos |
| 31 | Registrar_costo_ejecutado | Modulo_presupuestos |
| 28 | Registrar_presupuesto | Modulo_presupuestos |
| 27 | Visualizar_presupuesto | Modulo_presupuestos |
| 4 | Eliminar_usuarios | Modulo_usuarios |
| 3 | Modificar_usuarios | Modulo_usuarios |
| 2 | Registrar_usuarios | Modulo_usuarios |
| 1 | Visualizar_usuarios | Modulo_usuarios |
| 60 | Anular_costos_ejecutados | ? |
| 62 | Aprobar_ordenes_cambio | ? |
| 48 | Aprobar_ordenes_compra | ? |
| 44 | Aprobar_ordenes_compra | ? |
| 51 | Asignar_incidencias | ? |
| 54 | Cerrar_incidencias | ? |
| 17 | Desactivar_materiales | ? |
| 36 | Eliminar_estimaciones | ? |
| 32 | Modificar_estimaciones | ? |
| 50 | Modificar_incidencias | ? |
| 19 | Modificar_materiales | ? |
| 61 | Modificar_ordenes_cambio | ? |
| 22 | Modificar_proveedores | ? |
| 49 | Recepcionar_ordenes_compra | ? |
| 45 | Recepcionar_ordenes_compra | ? |
| 56 | Registrar_avances | ? |
| 59 | Registrar_costos_ejecutados | ? |
| 33 | Registrar_estimaciones | ? |
| 52 | Registrar_incidencias | ? |
| 37 | Registrar_mano_obra | ? |
| 18 | Registrar_materiales | ? |
| 58 | Registrar_ordenes_cambio | ? |
| 47 | Registrar_ordenes_compra | ? |
| 43 | Registrar_ordenes_compra | ? |
| 21 | Registrar_proveedores | ? |
| 55 | Visualizar_avances | ? |
| 57 | Visualizar_control_costos | ? |
| 34 | Visualizar_estimaciones | ? |
| 53 | Visualizar_incidencias | ? |
| 35 | Visualizar_mano_obra | ? |
| 20 | Visualizar_materiales | ? |
| 42 | Visualizar_ordenes_compra | ? |
| 46 | Visualizar_ordenes_compra | ? |
| 23 | Visualizar_proveedores | ? |


## Roles de PostgreSQL

| Rol | LOGIN | SUPERUSER | CREATEDB | CREATEROLE | BYPASSRLS | REPLICATION |
| --- | --- | --- | --- | --- | --- | --- |
| devpoppy | True | False | True | False | False | False |
| pg_checkpoint | False | False | False | False | False | False |
| pg_create_subscription | False | False | False | False | False | False |
| pg_database_owner | False | False | False | False | False | False |
| pg_execute_server_program | False | False | False | False | False | False |
| pg_maintain | False | False | False | False | False | False |
| pg_monitor | False | False | False | False | False | False |
| pg_read_all_data | False | False | False | False | False | False |
| pg_read_all_settings | False | False | False | False | False | False |
| pg_read_all_stats | False | False | False | False | False | False |
| pg_read_server_files | False | False | False | False | False | False |
| pg_signal_backend | False | False | False | False | False | False |
| pg_stat_scan_tables | False | False | False | False | False | False |
| pg_use_reserved_connections | False | False | False | False | False | False |
| pg_write_all_data | False | False | False | False | False | False |
| pg_write_server_files | False | False | False | False | False | False |
| postgres | True | True | True | True | True | True |


| Rol concedido | Miembro | ADMIN OPTION |
| --- | --- | --- |
| pg_read_all_settings | pg_monitor | False |
| pg_read_all_stats | pg_monitor | False |
| pg_stat_scan_tables | pg_monitor | False |


## Privilegios y extensiones

El rol conectado es propietario del esquema y de las 68 tablas. Tiene USAGE y CREATE en el esquema; su ACL expl?cita es NULL. Las vistas information_schema reflejan los grants visibles para la sesi?n.

| Beneficiario | Privilegio de tabla | Entradas |
| --- | --- | --- |
| devpoppy | DELETE | 68 |
| devpoppy | INSERT | 68 |
| devpoppy | REFERENCES | 68 |
| devpoppy | SELECT | 68 |
| devpoppy | TRIGGER | 68 |
| devpoppy | TRUNCATE | 68 |
| devpoppy | UPDATE | 68 |


| Beneficiario | EXECUTE en rutinas |
| --- | --- |
| PUBLIC | 74 |
| devpoppy | 74 |


EXECUTE para PUBLIC no demuestra acceso an?nimo por HTTP ni USAGE del esquema para todos los roles.

| Extensi?n | Versi?n |
| --- | --- |
| plpgsql | 1.0 |
| unaccent | 1.1 |


## Tablas, columnas, restricciones e ?ndices

Las 68 tablas son ordinarias y tienen RLS desactivado. No hay vistas, vistas materializadas, tablas particionadas ni foreign tables en este esquema.

### notificacion

Propietario: devpoppy. Sin id_empresa directo: revisar padre o condici?n de cat?logo global.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| id_notificacion | integer | NO | nextval('obras.notificacion_id_notificacion_seq'::regclass) |
| titulo | character varying(255) | NO | ? |
| cuerpo | text | NO | ? |
| tipo_referencia | character varying(100) | YES | ? |
| nro_usuario | integer | YES | ? |
| nro_emergencia | integer | YES | ? |
| leido | boolean | YES | false |
| fecha_creacion | timestamp without time zone | YES | CURRENT_TIMESTAMP |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| notificacion_pkey | PK | PRIMARY KEY (id_notificacion) |


| ?ndice | Definici?n |
| --- | --- |
| notificacion_pkey | CREATE UNIQUE INDEX notificacion_pkey ON obras.notificacion USING btree (id_notificacion) |


### t_analisi_precio_unitario_insumo

Propietario: devpoppy. Contiene id_empresa.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| id_analisis_precio_unitario_insumo | integer | NO | nextval('obras.t_analisi_precio_unitario_ins_id_analisis_precio_unitario_i_seq'::regclass) |
| id_analisis_precio_unitario | integer | NO | ? |
| tipo_insumo | character varying(20) | NO | 'MATERIAL'::character varying |
| id_material | integer | NO | ? |
| nombre | character varying(200) | NO | ? |
| id_unidad_medida | integer | NO | ? |
| cantidad | numeric(12,4) | NO | ? |
| precio_unitario | numeric(14,2) | NO | ? |
| orden | integer | NO | 1 |
| id_empresa | integer | NO | ? |
| created_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |
| updated_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |
| subtotal | numeric(14,2) | YES | GENERATED ALWAYS: round((cantidad * precio_unitario), 2) |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| chk_apu_detalle_solo_material | CHECK | CHECK (((tipo_insumo)::text = 'MATERIAL'::text)) |
| fk_apu_insumo_apu | FK | FOREIGN KEY (id_analisis_precio_unitario) REFERENCES obras.t_analisis_precio_unitario(id_analisis_precio_unitario) ON DELETE CASCADE |
| fk_apu_insumo_empresa | FK | FOREIGN KEY (id_empresa) REFERENCES obras.t_empresa(id_empresa) ON DELETE RESTRICT |
| fk_apu_insumo_material | FK | FOREIGN KEY (id_material) REFERENCES obras.t_material(id_material) ON DELETE RESTRICT |
| fk_apu_insumo_unidad | FK | FOREIGN KEY (id_unidad_medida) REFERENCES obras.t_unidad_medida(id_unidad_medida) ON DELETE RESTRICT |
| t_analisi_precio_unitario_insumo_cantidad_check | CHECK | CHECK ((cantidad >= (0)::numeric)) |
| t_analisi_precio_unitario_insumo_pkey | PK | PRIMARY KEY (id_analisis_precio_unitario_insumo) |
| t_analisi_precio_unitario_insumo_precio_unitario_check | CHECK | CHECK ((precio_unitario >= (0)::numeric)) |


| ?ndice | Definici?n |
| --- | --- |
| idx_apu_insumo_apu | CREATE INDEX idx_apu_insumo_apu ON obras.t_analisi_precio_unitario_insumo USING btree (id_analisis_precio_unitario) |
| t_analisi_precio_unitario_insumo_pkey | CREATE UNIQUE INDEX t_analisi_precio_unitario_insumo_pkey ON obras.t_analisi_precio_unitario_insumo USING btree (id_analisis_precio_unitario_insumo) |


### t_analisis_precio_unitario

Propietario: devpoppy. Contiene id_empresa.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| id_analisis_precio_unitario | integer | NO | nextval('obras.t_analisis_precio_unitario_id_analisis_precio_unitario_seq'::regclass) |
| id_obra | integer | YES | ? |
| id_padre | integer | YES | ? |
| id_estructura | integer | YES | ? |
| nombre | character varying(200) | NO | ? |
| descripcion | text | YES | ? |
| id_unidad_medida | integer | NO | ? |
| tipo_analisis_precio_unitario | character varying(20) | NO | 'OBRA_GRIS'::character varying |
| calidad | character varying(20) | YES | ? |
| activo | boolean | NO | true |
| id_empresa | integer | NO | ? |
| created_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |
| updated_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |
| codigo | character varying(40) | YES | ? |
| rendimiento | numeric(12,4) | YES | ? |
| costo_materiales | numeric(14,2) | NO | 0 |
| mano_de_obra | numeric(10,2) | NO | 0 |
| costo_directo | numeric(14,2) | NO | 0 |
| porcentaje_utilidad | numeric(7,3) | NO | 10 |
| precio_unitario_final | numeric(14,2) | NO | 0 |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| chk_apu_calidad | CHECK | CHECK (((calidad IS NULL) OR ((calidad)::text = ANY ((ARRAY['NORMAL'::character varying, 'LUJO'::character varying])::text[])))) |
| chk_apu_direct_labor_nonnegative | CHECK | CHECK ((mano_de_obra >= (0)::numeric)) |
| chk_apu_margin_nonnegative | CHECK | CHECK ((porcentaje_utilidad >= (0)::numeric)) |
| chk_apu_tipo | CHECK | CHECK (((tipo_analisis_precio_unitario)::text = ANY ((ARRAY['OBRA_GRIS'::character varying, 'EXCAVACION'::character varying, 'ACABADO'::character varying, 'SUBCONTRATO'::character varying])::text[]))) |
| chk_apu_yield_nonnegative | CHECK | CHECK (((rendimiento IS NULL) OR (rendimiento >= (0)::numeric))) |
| fk_apu_empresa | FK | FOREIGN KEY (id_empresa) REFERENCES obras.t_empresa(id_empresa) ON DELETE RESTRICT |
| fk_apu_estructura | FK | FOREIGN KEY (id_estructura) REFERENCES obras.t_estructura_obra(id_estructura) ON DELETE SET NULL |
| fk_apu_obra | FK | FOREIGN KEY (id_obra) REFERENCES obras.t_obra(id_obra) ON DELETE CASCADE |
| fk_apu_padre | FK | FOREIGN KEY (id_padre) REFERENCES obras.t_analisis_precio_unitario(id_analisis_precio_unitario) ON DELETE CASCADE |
| fk_apu_unidad | FK | FOREIGN KEY (id_unidad_medida) REFERENCES obras.t_unidad_medida(id_unidad_medida) ON DELETE RESTRICT |
| t_analisis_precio_unitario_pkey | PK | PRIMARY KEY (id_analisis_precio_unitario) |


| ?ndice | Definici?n |
| --- | --- |
| idx_apu_empresa_activo | CREATE INDEX idx_apu_empresa_activo ON obras.t_analisis_precio_unitario USING btree (id_empresa, activo) |
| idx_apu_estructura | CREATE INDEX idx_apu_estructura ON obras.t_analisis_precio_unitario USING btree (id_estructura) |
| t_analisis_precio_unitario_pkey | CREATE UNIQUE INDEX t_analisis_precio_unitario_pkey ON obras.t_analisis_precio_unitario USING btree (id_analisis_precio_unitario) |
| uq_apu_empresa_codigo | CREATE UNIQUE INDEX uq_apu_empresa_codigo ON obras.t_analisis_precio_unitario USING btree (id_empresa, codigo) |


### t_apu_detalle_mano_obra_archivo

Propietario: devpoppy. Sin id_empresa directo: revisar padre o condici?n de cat?logo global.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| id_archivo | bigint | NO | nextval('obras.t_apu_detalle_mano_obra_archivo_id_archivo_seq'::regclass) |
| id_detalle_origen | integer | NO | ? |
| registro | jsonb | NO | ? |
| archivado_en | timestamp with time zone | NO | CURRENT_TIMESTAMP |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| t_apu_detalle_mano_obra_archivo_id_detalle_origen_key | UNIQUE | UNIQUE (id_detalle_origen) |
| t_apu_detalle_mano_obra_archivo_pkey | PK | PRIMARY KEY (id_archivo) |


| ?ndice | Definici?n |
| --- | --- |
| t_apu_detalle_mano_obra_archivo_id_detalle_origen_key | CREATE UNIQUE INDEX t_apu_detalle_mano_obra_archivo_id_detalle_origen_key ON obras.t_apu_detalle_mano_obra_archivo USING btree (id_detalle_origen) |
| t_apu_detalle_mano_obra_archivo_pkey | CREATE UNIQUE INDEX t_apu_detalle_mano_obra_archivo_pkey ON obras.t_apu_detalle_mano_obra_archivo USING btree (id_archivo) |


### t_apu_legacy_archive

Propietario: devpoppy. Sin id_empresa directo: revisar padre o condici?n de cat?logo global.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| id_archivo | bigint | NO | nextval('obras.t_apu_legacy_archive_id_archivo_seq'::regclass) |
| tabla_origen | character varying(80) | NO | ? |
| id_origen | text | NO | ? |
| registro | jsonb | NO | ? |
| archivado_en | timestamp with time zone | NO | CURRENT_TIMESTAMP |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| t_apu_legacy_archive_pkey | PK | PRIMARY KEY (id_archivo) |
| uq_apu_legacy_archive | UNIQUE | UNIQUE (tabla_origen, id_origen) |


| ?ndice | Definici?n |
| --- | --- |
| t_apu_legacy_archive_pkey | CREATE UNIQUE INDEX t_apu_legacy_archive_pkey ON obras.t_apu_legacy_archive USING btree (id_archivo) |
| uq_apu_legacy_archive | CREATE UNIQUE INDEX uq_apu_legacy_archive ON obras.t_apu_legacy_archive USING btree (tabla_origen, id_origen) |


### t_avance_obra

Propietario: devpoppy. Sin id_empresa directo: revisar padre o condici?n de cat?logo global.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| id_avance | integer | NO | nextval('obras.t_avance_obra_id_avance_seq'::regclass) |
| id_obra | integer | NO | ? |
| id_unidad | integer | NO | ? |
| porcentaje_avance | numeric(5,2) | NO | 0 |
| fecha_registro | date | NO | CURRENT_DATE |
| observacion | text | YES | ? |
| id_usuario | integer | NO | ? |
| created_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| chk_avance_porcentaje | CHECK | CHECK (((porcentaje_avance >= (0)::numeric) AND (porcentaje_avance <= (100)::numeric))) |
| fk_avance_obra | FK | FOREIGN KEY (id_obra) REFERENCES obras.t_obra(id_obra) ON DELETE CASCADE |
| fk_avance_unidad | FK | FOREIGN KEY (id_unidad) REFERENCES obras.t_unidad_construccion(id_unidad) ON DELETE CASCADE |
| fk_avance_usuario | FK | FOREIGN KEY (id_usuario) REFERENCES obras.t_usuario(id_usuario) ON DELETE RESTRICT |
| t_avance_obra_pkey | PK | PRIMARY KEY (id_avance) |


| ?ndice | Definici?n |
| --- | --- |
| idx_avance_obra_fecha | CREATE INDEX idx_avance_obra_fecha ON obras.t_avance_obra USING btree (fecha_registro DESC) |
| idx_avance_obra_id_obra | CREATE INDEX idx_avance_obra_id_obra ON obras.t_avance_obra USING btree (id_obra) |
| idx_avance_obra_id_unidad | CREATE INDEX idx_avance_obra_id_unidad ON obras.t_avance_obra USING btree (id_unidad) |
| t_avance_obra_pkey | CREATE UNIQUE INDEX t_avance_obra_pkey ON obras.t_avance_obra USING btree (id_avance) |


### t_bitacora

Propietario: devpoppy. Sin id_empresa directo: revisar padre o condici?n de cat?logo global.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| id_bitacora | integer | NO | nextval('obras.t_bitacora_id_bitacora_seq'::regclass) |
| id_usuario | bigint | NO | ? |
| modulo | character varying(50) | NO | ? |
| accion | character varying(50) | NO | ? |
| descripcion | character varying(256) | NO | ? |
| ip | character varying(20) | NO | ? |
| estado | character varying(30) | NO | ? |
| fecha_accion | timestamp without time zone | YES | CURRENT_TIMESTAMP |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| t_bitacora_id_usuario_fkey | FK | FOREIGN KEY (id_usuario) REFERENCES obras.t_usuario(id_usuario) ON UPDATE CASCADE ON DELETE CASCADE |
| t_bitacora_pkey | PK | PRIMARY KEY (id_bitacora) |


| ?ndice | Definici?n |
| --- | --- |
| t_bitacora_pkey | CREATE UNIQUE INDEX t_bitacora_pkey ON obras.t_bitacora USING btree (id_bitacora) |


### t_categoria_material

Propietario: devpoppy. Sin id_empresa directo: revisar padre o condici?n de cat?logo global.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| id_categoria | integer | NO | nextval('obras.t_categoria_material_id_categoria_seq'::regclass) |
| nombre | character varying(120) | NO | ? |
| descripcion | text | YES | ? |
| estado | character varying(10) | NO | 'ACTIVO'::character varying |
| created_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |
| updated_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| chk_categoria_material_estado | CHECK | CHECK (((estado)::text = ANY ((ARRAY['ACTIVO'::character varying, 'INACTIVO'::character varying])::text[]))) |
| chk_categoria_material_nombre | CHECK | CHECK ((btrim((nombre)::text) <> ''::text)) |
| t_categoria_material_pkey | PK | PRIMARY KEY (id_categoria) |


| ?ndice | Definici?n |
| --- | --- |
| t_categoria_material_pkey | CREATE UNIQUE INDEX t_categoria_material_pkey ON obras.t_categoria_material USING btree (id_categoria) |
| uq_categoria_material_nombre_activo | CREATE UNIQUE INDEX uq_categoria_material_nombre_activo ON obras.t_categoria_material USING btree (lower(btrim((nombre)::text))) WHERE ((estado)::text = 'ACTIVO'::text) |


### t_control_costo_obra

Propietario: devpoppy. Contiene id_empresa.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| id_control_costo | bigint | NO | nextval('obras.t_control_costo_obra_id_control_costo_seq'::regclass) |
| id_empresa | integer | NO | ? |
| id_obra | integer | NO | ? |
| id_estimacion_base | integer | NO | ? |
| version_presupuesto | integer | NO | ? |
| moneda | character varying(10) | NO | ? |
| estado | character varying(10) | NO | 'ACTIVO'::character varying |
| seleccionado_por | integer | NO | ? |
| seleccionado_en | timestamp with time zone | NO | CURRENT_TIMESTAMP |
| created_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |
| updated_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| chk_control_costo_estado | CHECK | CHECK (((estado)::text = ANY ((ARRAY['ACTIVO'::character varying, 'CERRADO'::character varying])::text[]))) |
| chk_control_costo_moneda | CHECK | CHECK ((btrim((moneda)::text) <> ''::text)) |
| fk_control_costo_empresa | FK | FOREIGN KEY (id_empresa) REFERENCES obras.t_empresa(id_empresa) ON DELETE RESTRICT |
| fk_control_costo_estimacion | FK | FOREIGN KEY (id_estimacion_base) REFERENCES obras.t_estimacion(id_estimacion) ON DELETE RESTRICT |
| fk_control_costo_obra | FK | FOREIGN KEY (id_obra) REFERENCES obras.t_obra(id_obra) ON DELETE RESTRICT |
| fk_control_costo_usuario | FK | FOREIGN KEY (seleccionado_por) REFERENCES obras.t_usuario(id_usuario) ON DELETE RESTRICT |
| t_control_costo_obra_pkey | PK | PRIMARY KEY (id_control_costo) |


| ?ndice | Definici?n |
| --- | --- |
| idx_control_costo_estimacion | CREATE INDEX idx_control_costo_estimacion ON obras.t_control_costo_obra USING btree (id_estimacion_base) |
| t_control_costo_obra_pkey | CREATE UNIQUE INDEX t_control_costo_obra_pkey ON obras.t_control_costo_obra USING btree (id_control_costo) |
| uq_control_costo_obra_activo | CREATE UNIQUE INDEX uq_control_costo_obra_activo ON obras.t_control_costo_obra USING btree (id_empresa, id_obra) WHERE ((estado)::text = 'ACTIVO'::text) |


### t_costo_ejecutado

Propietario: devpoppy. Contiene id_empresa.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| id_costo_ejecutado | bigint | NO | nextval('obras.t_costo_ejecutado_id_costo_ejecutado_seq'::regclass) |
| id_control_costo | bigint | NO | ? |
| id_empresa | integer | NO | ? |
| id_obra | integer | NO | ? |
| id_partida_presupuestaria | integer | NO | ? |
| fecha | date | NO | ? |
| concepto | character varying(250) | NO | ? |
| categoria | character varying(20) | NO | ? |
| cantidad | numeric(14,4) | NO | ? |
| costo_unitario | numeric(16,2) | NO | ? |
| monto | numeric(16,2) | NO | ? |
| documento | character varying(120) | YES | ? |
| observacion | text | YES | ? |
| estado | character varying(12) | NO | 'REGISTRADO'::character varying |
| registrado_por | integer | NO | ? |
| anulado_por | integer | YES | ? |
| anulado_en | timestamp with time zone | YES | ? |
| motivo_anulacion | text | YES | ? |
| created_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |
| updated_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| chk_costo_ejecutado_anulacion | CHECK | CHECK (((((estado)::text = 'REGISTRADO'::text) AND (anulado_por IS NULL) AND (anulado_en IS NULL) AND (motivo_anulacion IS NULL)) OR (((estado)::text = 'ANULADO'::text) AND (anulado_por IS NOT NULL) AND (anulado_en IS NOT NULL) AND (motivo_anulacion IS NOT NULL) AND (btrim(motivo_anulacion) <> ''::text)))) |
| chk_costo_ejecutado_cantidad | CHECK | CHECK ((cantidad >= (0)::numeric)) |
| chk_costo_ejecutado_categoria | CHECK | CHECK (((categoria)::text = ANY ((ARRAY['MATERIAL'::character varying, 'MANO_OBRA'::character varying, 'EQUIPO'::character varying, 'SUBCONTRATO'::character varying, 'OTRO'::character varying])::text[]))) |
| chk_costo_ejecutado_concepto | CHECK | CHECK ((btrim((concepto)::text) <> ''::text)) |
| chk_costo_ejecutado_estado | CHECK | CHECK (((estado)::text = ANY ((ARRAY['REGISTRADO'::character varying, 'ANULADO'::character varying])::text[]))) |
| chk_costo_ejecutado_monto | CHECK | CHECK (((monto >= (0)::numeric) AND (monto = round((cantidad * costo_unitario), 2)))) |
| chk_costo_ejecutado_unitario | CHECK | CHECK ((costo_unitario >= (0)::numeric)) |
| fk_costo_ejecutado_anulado_por | FK | FOREIGN KEY (anulado_por) REFERENCES obras.t_usuario(id_usuario) ON DELETE RESTRICT |
| fk_costo_ejecutado_control | FK | FOREIGN KEY (id_control_costo) REFERENCES obras.t_control_costo_obra(id_control_costo) ON DELETE RESTRICT |
| fk_costo_ejecutado_empresa | FK | FOREIGN KEY (id_empresa) REFERENCES obras.t_empresa(id_empresa) ON DELETE RESTRICT |
| fk_costo_ejecutado_obra | FK | FOREIGN KEY (id_obra) REFERENCES obras.t_obra(id_obra) ON DELETE RESTRICT |
| fk_costo_ejecutado_partida | FK | FOREIGN KEY (id_partida_presupuestaria) REFERENCES obras.t_estimacion_analisis_precio_unitario(id_estimacion_analisis_precio_unitario) ON DELETE RESTRICT |
| fk_costo_ejecutado_registrado_por | FK | FOREIGN KEY (registrado_por) REFERENCES obras.t_usuario(id_usuario) ON DELETE RESTRICT |
| t_costo_ejecutado_pkey | PK | PRIMARY KEY (id_costo_ejecutado) |


| ?ndice | Definici?n |
| --- | --- |
| idx_costo_ejecutado_control_fecha | CREATE INDEX idx_costo_ejecutado_control_fecha ON obras.t_costo_ejecutado USING btree (id_control_costo, fecha) |
| idx_costo_ejecutado_empresa_obra | CREATE INDEX idx_costo_ejecutado_empresa_obra ON obras.t_costo_ejecutado USING btree (id_empresa, id_obra) |
| idx_costo_ejecutado_partida_estado | CREATE INDEX idx_costo_ejecutado_partida_estado ON obras.t_costo_ejecutado USING btree (id_partida_presupuestaria, estado) |
| t_costo_ejecutado_pkey | CREATE UNIQUE INDEX t_costo_ejecutado_pkey ON obras.t_costo_ejecutado USING btree (id_costo_ejecutado) |


### t_costo_ejecutado_legacy

Propietario: devpoppy. Sin id_empresa directo: revisar padre o condici?n de cat?logo global.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| id_costo_ejecutado | integer | NO | nextval('obras.t_costo_ejecutado_legacy_id_costo_ejecutado_seq'::regclass) |
| id_obra | integer | NO | ? |
| id_partida | integer | YES | ? |
| codigo_costo | character varying(50) | YES | ? |
| origen_costo | character varying(30) | NO | 'REGISTRO_MANUAL'::character varying |
| tipo_recurso | character varying(20) | NO | 'MATERIAL'::character varying |
| descripcion | character varying(250) | NO | ? |
| id_unidad_medida | integer | YES | ? |
| cantidad | numeric(14,4) | NO | 1.0000 |
| costo_unitario | numeric(15,2) | NO | 0.00 |
| importe_total | numeric(15,2) | NO | 0.00 |
| fecha | date | NO | CURRENT_DATE |
| observacion | text | YES | ? |
| id_usuario_registro | integer | NO | ? |
| created_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| chk_costo_ejec_cant_pos | CHECK | CHECK ((cantidad >= (0)::numeric)) |
| chk_costo_ejec_origen | CHECK | CHECK (((origen_costo)::text = ANY ((ARRAY['REGISTRO_MANUAL'::character varying, 'ALMACEN'::character varying, 'COMPRA'::character varying, 'MANO_OBRA'::character varying, 'EQUIPO'::character varying, 'SUBCONTRATO'::character varying, 'OTRO'::character varying])::text[]))) |
| chk_costo_ejec_tipo | CHECK | CHECK (((tipo_recurso)::text = ANY ((ARRAY['MATERIAL'::character varying, 'MANO_OBRA'::character varying, 'EQUIPO'::character varying, 'OTRO'::character varying])::text[]))) |
| chk_costo_ejec_unit_pos | CHECK | CHECK ((costo_unitario >= (0)::numeric)) |
| t_costo_ejecutado_id_obra_fkey | FK | FOREIGN KEY (id_obra) REFERENCES obras.t_obra(id_obra) ON DELETE CASCADE |
| t_costo_ejecutado_id_partida_fkey | FK | FOREIGN KEY (id_partida) REFERENCES obras.t_partida_presupuesto(id_partida) ON DELETE SET NULL |
| t_costo_ejecutado_id_unidad_medida_fkey | FK | FOREIGN KEY (id_unidad_medida) REFERENCES obras.t_unidad_medida(id_unidad_medida) |
| t_costo_ejecutado_id_usuario_registro_fkey | FK | FOREIGN KEY (id_usuario_registro) REFERENCES obras.t_usuario(id_usuario) |
| t_costo_ejecutado_legacy_pkey | PK | PRIMARY KEY (id_costo_ejecutado) |


| ?ndice | Definici?n |
| --- | --- |
| idx_costo_ejecutado_obra | CREATE INDEX idx_costo_ejecutado_obra ON obras.t_costo_ejecutado_legacy USING btree (id_obra) |
| idx_costo_ejecutado_partida | CREATE INDEX idx_costo_ejecutado_partida ON obras.t_costo_ejecutado_legacy USING btree (id_partida) |
| t_costo_ejecutado_legacy_pkey | CREATE UNIQUE INDEX t_costo_ejecutado_legacy_pkey ON obras.t_costo_ejecutado_legacy USING btree (id_costo_ejecutado) |


### t_crm_cliente

Propietario: devpoppy. Contiene id_empresa.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| id_cliente | integer | NO | nextval('obras.t_crm_cliente_id_cliente_seq'::regclass) |
| id_empresa | integer | NO | ? |
| id_persona | integer | NO | ? |
| email | character varying(150) | YES | ? |
| tipo_cliente | character varying(20) | NO | 'PROSPECTO'::character varying |
| estado | character varying(30) | NO | 'NUEVO'::character varying |
| origen | character varying(50) | YES | 'DIRECTO'::character varying |
| presupuesto_estimado | numeric(15,2) | YES | NULL::numeric |
| notas | text | YES | ? |
| id_usuario_asignado | integer | YES | ? |
| created_at | timestamp with time zone | YES | CURRENT_TIMESTAMP |
| updated_at | timestamp with time zone | YES | CURRENT_TIMESTAMP |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| chk_crm_tipo_estado | CHECK | CHECK (((((tipo_cliente)::text = 'PROSPECTO'::text) AND ((estado)::text = ANY ((ARRAY['NUEVO'::character varying, 'CONTACTADO'::character varying, 'INTERESADO'::character varying, 'NEGOCIACION'::character varying, 'EN_NEGOCIACION'::character varying, 'RESERVADO'::character varying, 'VENDIDO'::character varying, 'CONVERTIDO'::character varying, 'PERDIDO'::character varying])::text[]))) OR (((tipo_cliente)::text = 'CLIENTE'::text) AND ((estado)::text = ANY ((ARRAY['ACTIVO'::character varying, 'INACTIVO'::character varying, 'NUEVO'::character varying, 'CONTACTADO'::character varying, 'INTERESADO'::character varying, 'NEGOCIACION'::character varying, 'EN_NEGOCIACION'::character varying, 'RESERVADO'::character varying, 'VENDIDO'::character varying])::text[]))))) |
| t_crm_cliente_id_empresa_fkey | FK | FOREIGN KEY (id_empresa) REFERENCES obras.t_empresa(id_empresa) ON DELETE CASCADE |
| t_crm_cliente_id_persona_fkey | FK | FOREIGN KEY (id_persona) REFERENCES obras.t_persona(id_persona) ON DELETE RESTRICT |
| t_crm_cliente_id_usuario_asignado_fkey | FK | FOREIGN KEY (id_usuario_asignado) REFERENCES obras.t_usuario(id_usuario) ON DELETE SET NULL |
| t_crm_cliente_pkey | PK | PRIMARY KEY (id_cliente) |
| uq_crm_empresa_persona | UNIQUE | UNIQUE (id_empresa, id_persona) |


| ?ndice | Definici?n |
| --- | --- |
| t_crm_cliente_pkey | CREATE UNIQUE INDEX t_crm_cliente_pkey ON obras.t_crm_cliente USING btree (id_cliente) |
| uq_crm_empresa_persona | CREATE UNIQUE INDEX uq_crm_empresa_persona ON obras.t_crm_cliente USING btree (id_empresa, id_persona) |


### t_crm_cliente_unidad

Propietario: devpoppy. Sin id_empresa directo: revisar padre o condici?n de cat?logo global.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| id_cliente_unidad | integer | NO | nextval('obras.t_crm_cliente_unidad_id_cliente_unidad_seq'::regclass) |
| id_cliente | integer | NO | ? |
| id_unidad | integer | NO | ? |
| estado_asociacion | character varying(30) | NO | 'INTERESADO'::character varying |
| monto_pactado | numeric(15,2) | YES | NULL::numeric |
| fecha_asociacion | timestamp with time zone | NO | CURRENT_TIMESTAMP |
| observaciones | text | YES | ? |
| created_at | timestamp with time zone | YES | CURRENT_TIMESTAMP |
| updated_at | timestamp with time zone | YES | CURRENT_TIMESTAMP |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| chk_crm_estado_asociacion | CHECK | CHECK (((estado_asociacion)::text = ANY ((ARRAY['INTERESADO'::character varying, 'RESERVADO'::character varying, 'VENDIDO'::character varying, 'ENTREGADO'::character varying, 'CANCELADO'::character varying])::text[]))) |
| t_crm_cliente_unidad_id_cliente_fkey | FK | FOREIGN KEY (id_cliente) REFERENCES obras.t_crm_cliente(id_cliente) ON DELETE CASCADE |
| t_crm_cliente_unidad_id_unidad_fkey | FK | FOREIGN KEY (id_unidad) REFERENCES obras.t_unidad_construccion(id_unidad) ON DELETE RESTRICT |
| t_crm_cliente_unidad_pkey | PK | PRIMARY KEY (id_cliente_unidad) |


| ?ndice | Definici?n |
| --- | --- |
| t_crm_cliente_unidad_pkey | CREATE UNIQUE INDEX t_crm_cliente_unidad_pkey ON obras.t_crm_cliente_unidad USING btree (id_cliente_unidad) |
| uq_crm_cliente_unidad_activa | CREATE UNIQUE INDEX uq_crm_cliente_unidad_activa ON obras.t_crm_cliente_unidad USING btree (id_cliente, id_unidad) WHERE ((estado_asociacion)::text = ANY ((ARRAY['INTERESADO'::character varying, 'RESERVADO'::character varying, 'VENDIDO'::character varying])::text[])) |
| uq_crm_unidad_reservada_vendida | CREATE UNIQUE INDEX uq_crm_unidad_reservada_vendida ON obras.t_crm_cliente_unidad USING btree (id_unidad) WHERE ((estado_asociacion)::text = ANY ((ARRAY['RESERVADO'::character varying, 'VENDIDO'::character varying])::text[])) |


### t_crm_interaccion

Propietario: devpoppy. Sin id_empresa directo: revisar padre o condici?n de cat?logo global.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| id_interaccion | integer | NO | nextval('obras.t_crm_interaccion_id_interaccion_seq'::regclass) |
| id_cliente | integer | NO | ? |
| id_usuario | integer | NO | ? |
| tipo | character varying(30) | NO | ? |
| asunto | character varying(200) | NO | ? |
| detalle | text | NO | ? |
| fecha_interaccion | timestamp with time zone | NO | CURRENT_TIMESTAMP |
| fecha_proximo_contacto | timestamp with time zone | YES | ? |
| created_at | timestamp with time zone | YES | CURRENT_TIMESTAMP |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| t_crm_interaccion_id_cliente_fkey | FK | FOREIGN KEY (id_cliente) REFERENCES obras.t_crm_cliente(id_cliente) ON DELETE CASCADE |
| t_crm_interaccion_id_usuario_fkey | FK | FOREIGN KEY (id_usuario) REFERENCES obras.t_usuario(id_usuario) ON DELETE RESTRICT |
| t_crm_interaccion_pkey | PK | PRIMARY KEY (id_interaccion) |


| ?ndice | Definici?n |
| --- | --- |
| t_crm_interaccion_pkey | CREATE UNIQUE INDEX t_crm_interaccion_pkey ON obras.t_crm_interaccion USING btree (id_interaccion) |


### t_detalle_obra

Propietario: devpoppy. Sin id_empresa directo: revisar padre o condici?n de cat?logo global.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| id_detalle | integer | NO | nextval('obras.t_detalle_obra_id_detalle_seq'::regclass) |
| id_obra | integer | YES | ? |
| ubicacion | character varying(250) | YES | ? |
| latitud | numeric(10,7) | YES | ? |
| longitud | numeric(10,7) | YES | ? |
| id_supervisor | integer | YES | ? |
| id_cliente | integer | YES | ? |
| descripcion_cliente | text | YES | ? |
| observacion | text | YES | ? |
| cotizacion_inicial | numeric(15,2) | YES | ? |
| zona | character varying(100) | YES | ? |
| distrito | character varying(50) | YES | ? |
| uv | character varying(50) | YES | ? |
| manzana | character varying(50) | YES | ? |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| t_detalle_obra_id_cliente_fkey | FK | FOREIGN KEY (id_cliente) REFERENCES obras.t_persona(id_persona) |
| t_detalle_obra_id_obra_fkey | FK | FOREIGN KEY (id_obra) REFERENCES obras.t_obra(id_obra) ON DELETE CASCADE |
| t_detalle_obra_id_supervisor_fkey | FK | FOREIGN KEY (id_supervisor) REFERENCES obras.t_persona(id_persona) |
| t_detalle_obra_pkey | PK | PRIMARY KEY (id_detalle) |


| ?ndice | Definici?n |
| --- | --- |
| idx_detalle_obra_id_cliente | CREATE INDEX idx_detalle_obra_id_cliente ON obras.t_detalle_obra USING btree (id_cliente) |
| idx_detalle_obra_id_obra | CREATE INDEX idx_detalle_obra_id_obra ON obras.t_detalle_obra USING btree (id_obra) |
| idx_detalle_obra_id_supervisor | CREATE INDEX idx_detalle_obra_id_supervisor ON obras.t_detalle_obra USING btree (id_supervisor) |
| t_detalle_obra_pkey | CREATE UNIQUE INDEX t_detalle_obra_pkey ON obras.t_detalle_obra USING btree (id_detalle) |


### t_empresa

Propietario: devpoppy. Contiene id_empresa.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| id_empresa | integer | NO | nextval('obras.t_empresa_id_empresa_seq'::regclass) |
| nombre_empresa | character varying(150) | YES | ? |
| nit | bigint | YES | ? |
| descripcion | text | YES | ? |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| t_empresa_pkey | PK | PRIMARY KEY (id_empresa) |


| ?ndice | Definici?n |
| --- | --- |
| t_empresa_pkey | CREATE UNIQUE INDEX t_empresa_pkey ON obras.t_empresa USING btree (id_empresa) |


### t_equipo

Propietario: devpoppy. Contiene id_empresa.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| id_equipo | integer | NO | nextval('obras.t_equipo_id_equipo_seq'::regclass) |
| id_empresa | integer | NO | ? |
| codigo | character varying(50) | NO | ? |
| nombre | character varying(200) | NO | ? |
| descripcion | text | YES | ? |
| id_unidad_medida | integer | NO | ? |
| costo_unitario | numeric(15,2) | NO | 0.00 |
| activo | boolean | NO | true |
| created_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |
| updated_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| chk_equipo_costo_pos | CHECK | CHECK ((costo_unitario >= (0)::numeric)) |
| t_equipo_id_empresa_fkey | FK | FOREIGN KEY (id_empresa) REFERENCES obras.t_empresa(id_empresa) ON DELETE CASCADE |
| t_equipo_id_unidad_medida_fkey | FK | FOREIGN KEY (id_unidad_medida) REFERENCES obras.t_unidad_medida(id_unidad_medida) |
| t_equipo_pkey | PK | PRIMARY KEY (id_equipo) |
| uq_equipo_empresa_codigo | UNIQUE | UNIQUE (id_empresa, codigo) |


| ?ndice | Definici?n |
| --- | --- |
| idx_equipo_empresa | CREATE INDEX idx_equipo_empresa ON obras.t_equipo USING btree (id_empresa) |
| t_equipo_pkey | CREATE UNIQUE INDEX t_equipo_pkey ON obras.t_equipo USING btree (id_equipo) |
| uq_equipo_empresa_codigo | CREATE UNIQUE INDEX uq_equipo_empresa_codigo ON obras.t_equipo USING btree (id_empresa, codigo) |


### t_equipo_maquinaria

Propietario: devpoppy. Contiene id_empresa.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| id_equipo_maquinaria | integer | NO | nextval('obras.t_equipo_maquinaria_id_equipo_maquinaria_seq'::regclass) |
| codigo | character varying(50) | NO | ? |
| nombre | character varying(150) | NO | ? |
| tipo | character varying(30) | YES | ? |
| marca | character varying(100) | YES | ? |
| modelo | character varying(100) | YES | ? |
| numero_serie | character varying(100) | YES | ? |
| descripcion | text | YES | ? |
| estado | character varying(20) | NO | 'DISPONIBLE'::character varying |
| id_empresa | integer | NO | ? |
| created_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |
| updated_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| fk_equipo_maquinaria_empresa | FK | FOREIGN KEY (id_empresa) REFERENCES obras.t_empresa(id_empresa) ON DELETE RESTRICT |
| t_equipo_maquinaria_pkey | PK | PRIMARY KEY (id_equipo_maquinaria) |
| uq_equipo_maquinaria_empresa_codigo | UNIQUE | UNIQUE (id_empresa, codigo) |


| ?ndice | Definici?n |
| --- | --- |
| t_equipo_maquinaria_pkey | CREATE UNIQUE INDEX t_equipo_maquinaria_pkey ON obras.t_equipo_maquinaria USING btree (id_equipo_maquinaria) |
| uq_equipo_maquinaria_empresa_codigo | CREATE UNIQUE INDEX uq_equipo_maquinaria_empresa_codigo ON obras.t_equipo_maquinaria USING btree (id_empresa, codigo) |


### t_equipo_maquinaria_obra

Propietario: devpoppy. Sin id_empresa directo: revisar padre o condici?n de cat?logo global.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| id_asignacion | integer | NO | nextval('obras.t_equipo_maquinaria_obra_id_asignacion_seq'::regclass) |
| id_equipo_maquinaria | integer | NO | ? |
| id_obra | integer | NO | ? |
| fecha_asignacion | date | NO | CURRENT_DATE |
| fecha_retiro | date | YES | ? |
| estado | character varying(20) | NO | 'ASIGNADO'::character varying |
| observacion | text | YES | ? |
| created_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |
| updated_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| fk_equipo_maquinaria_obra_equipo | FK | FOREIGN KEY (id_equipo_maquinaria) REFERENCES obras.t_equipo_maquinaria(id_equipo_maquinaria) ON DELETE RESTRICT |
| fk_equipo_maquinaria_obra_obra | FK | FOREIGN KEY (id_obra) REFERENCES obras.t_obra(id_obra) ON DELETE RESTRICT |
| t_equipo_maquinaria_obra_pkey | PK | PRIMARY KEY (id_asignacion) |


| ?ndice | Definici?n |
| --- | --- |
| t_equipo_maquinaria_obra_pkey | CREATE UNIQUE INDEX t_equipo_maquinaria_obra_pkey ON obras.t_equipo_maquinaria_obra USING btree (id_asignacion) |


### t_estimacion

Propietario: devpoppy. Contiene id_empresa.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| id_estimacion | integer | NO | nextval('obras.t_estimacion_id_estimacion_seq'::regclass) |
| id_obra | integer | NO | ? |
| nombre | character varying(150) | NO | ? |
| version | integer | NO | 1 |
| estado | character varying(20) | NO | 'BORRADOR'::character varying |
| descripcion | text | YES | ? |
| factor_indirectos | numeric(8,4) | YES | ? |
| factor_utilidad | numeric(8,4) | YES | ? |
| monto_total | numeric(16,2) | YES | ? |
| id_empresa | integer | NO | ? |
| created_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |
| updated_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |
| cliente | character varying(200) | NO | ''::character varying |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| chk_estimacion_estado | CHECK | CHECK (((estado)::text = ANY ((ARRAY['BORRADOR'::character varying, 'APROBADA'::character varying, 'ARCHIVADA'::character varying])::text[]))) |
| chk_estimacion_factores | CHECK | CHECK ((((factor_indirectos IS NULL) OR (factor_indirectos >= (0)::numeric)) AND ((factor_utilidad IS NULL) OR (factor_utilidad >= (0)::numeric)))) |
| fk_estimacion_empresa | FK | FOREIGN KEY (id_empresa) REFERENCES obras.t_empresa(id_empresa) ON DELETE RESTRICT |
| fk_estimacion_obra | FK | FOREIGN KEY (id_obra) REFERENCES obras.t_obra(id_obra) ON DELETE CASCADE |
| t_estimacion_pkey | PK | PRIMARY KEY (id_estimacion) |


| ?ndice | Definici?n |
| --- | --- |
| idx_estimacion_obra | CREATE INDEX idx_estimacion_obra ON obras.t_estimacion USING btree (id_obra) |
| t_estimacion_pkey | CREATE UNIQUE INDEX t_estimacion_pkey ON obras.t_estimacion USING btree (id_estimacion) |


### t_estimacion_analisis_precio_unitario

Propietario: devpoppy. Sin id_empresa directo: revisar padre o condici?n de cat?logo global.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| id_estimacion_analisis_precio_unitario | integer | NO | nextval('obras.t_estimacion_analisis_precio__id_estimacion_analisis_precio_seq'::regclass) |
| id_estimacion | integer | NO | ? |
| id_analisis_precio_unitario | integer | NO | ? |
| cantidad | numeric(12,3) | NO | ? |
| orden | integer | NO | 1 |
| observacion | text | YES | ? |
| item_codigo | character varying(40) | NO | ? |
| precio_unitario | numeric(14,2) | NO | ? |
| precio_total | numeric(16,2) | YES | GENERATED ALWAYS: round((cantidad * COALESCE(precio_unitario, (0)::numeric)), 2) |
| costo_directo_unitario | numeric(14,2) | NO | ? |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| fk_estimacion_apu_apu | FK | FOREIGN KEY (id_analisis_precio_unitario) REFERENCES obras.t_analisis_precio_unitario(id_analisis_precio_unitario) ON DELETE RESTRICT |
| fk_estimacion_apu_estimacion | FK | FOREIGN KEY (id_estimacion) REFERENCES obras.t_estimacion(id_estimacion) ON DELETE CASCADE |
| t_estimacion_analisis_precio_unitario_cantidad_check | CHECK | CHECK ((cantidad >= (0)::numeric)) |
| t_estimacion_analisis_precio_unitario_pkey | PK | PRIMARY KEY (id_estimacion_analisis_precio_unitario) |
| uq_estimacion_apu | UNIQUE | UNIQUE (id_estimacion, id_analisis_precio_unitario) |
| uq_estimacion_apu_orden | UNIQUE | UNIQUE (id_estimacion, orden) |


| ?ndice | Definici?n |
| --- | --- |
| t_estimacion_analisis_precio_unitario_pkey | CREATE UNIQUE INDEX t_estimacion_analisis_precio_unitario_pkey ON obras.t_estimacion_analisis_precio_unitario USING btree (id_estimacion_analisis_precio_unitario) |
| uq_estimacion_apu | CREATE UNIQUE INDEX uq_estimacion_apu ON obras.t_estimacion_analisis_precio_unitario USING btree (id_estimacion, id_analisis_precio_unitario) |
| uq_estimacion_apu_orden | CREATE UNIQUE INDEX uq_estimacion_apu_orden ON obras.t_estimacion_analisis_precio_unitario USING btree (id_estimacion, orden) |
| uq_estimacion_item_codigo | CREATE UNIQUE INDEX uq_estimacion_item_codigo ON obras.t_estimacion_analisis_precio_unitario USING btree (id_estimacion, item_codigo) |


### t_estructura_obra

Propietario: devpoppy. Sin id_empresa directo: revisar padre o condici?n de cat?logo global.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| id_estructura | integer | NO | nextval('obras.t_estructura_obra_id_estructura_seq'::regclass) |
| id_obra | integer | NO | ? |
| id_padre | integer | YES | ? |
| nombre | character varying(150) | NO | ? |
| tipo | character varying(50) | NO | 'Sector'::character varying |
| descripcion | text | YES | ? |
| orden | integer | NO | 1 |
| created_at | timestamp with time zone | YES | CURRENT_TIMESTAMP |
| updated_at | timestamp with time zone | YES | CURRENT_TIMESTAMP |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| fk_estructura_obra | FK | FOREIGN KEY (id_obra) REFERENCES obras.t_obra(id_obra) ON DELETE CASCADE |
| fk_estructura_padre | FK | FOREIGN KEY (id_padre) REFERENCES obras.t_estructura_obra(id_estructura) ON DELETE CASCADE |
| t_estructura_obra_pkey | PK | PRIMARY KEY (id_estructura) |


| ?ndice | Definici?n |
| --- | --- |
| idx_estructura_obra_id_obra | CREATE INDEX idx_estructura_obra_id_obra ON obras.t_estructura_obra USING btree (id_obra) |
| idx_estructura_obra_id_padre | CREATE INDEX idx_estructura_obra_id_padre ON obras.t_estructura_obra USING btree (id_padre) |
| t_estructura_obra_pkey | CREATE UNIQUE INDEX t_estructura_obra_pkey ON obras.t_estructura_obra USING btree (id_estructura) |


### t_incidencia

Propietario: devpoppy. Sin id_empresa directo: revisar padre o condici?n de cat?logo global.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| id_incidencia | integer | NO | nextval('obras.t_incidencia_id_incidencia_seq'::regclass) |
| id_obra | integer | NO | ? |
| id_unidad | integer | YES | ? |
| id_usuario_registro | integer | NO | ? |
| id_responsable | integer | YES | ? |
| titulo | character varying(200) | NO | ? |
| descripcion | text | NO | ? |
| prioridad | character varying(10) | NO | ? |
| estado | character varying(21) | NO | 'ABIERTA'::character varying |
| created_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |
| updated_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |
| ubicacion | character varying(255) | YES | ? |
| fecha_inicio_atencion | timestamp with time zone | YES | ? |
| fecha_fin_atencion | timestamp with time zone | YES | ? |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| chk_incidencia_descripcion | CHECK | CHECK ((btrim(descripcion) <> ''::text)) |
| chk_incidencia_estado | CHECK | CHECK (((estado)::text = ANY ((ARRAY['ABIERTA'::character varying, 'ASIGNADA'::character varying, 'EN_PROCESO'::character varying, 'PENDIENTE_VALIDACION'::character varying, 'RESUELTA'::character varying, 'CERRADA'::character varying])::text[]))) |
| chk_incidencia_fechas_atencion | CHECK | CHECK (((fecha_fin_atencion IS NULL) OR ((fecha_inicio_atencion IS NOT NULL) AND (fecha_fin_atencion >= fecha_inicio_atencion)))) |
| chk_incidencia_fechas_estado | CHECK | CHECK (((((estado)::text = ANY ((ARRAY['ABIERTA'::character varying, 'ASIGNADA'::character varying])::text[])) AND (fecha_inicio_atencion IS NULL) AND (fecha_fin_atencion IS NULL)) OR (((estado)::text = 'EN_PROCESO'::text) AND (fecha_inicio_atencion IS NOT NULL) AND (fecha_fin_atencion IS NULL)) OR (((estado)::text = ANY ((ARRAY['PENDIENTE_VALIDACION'::character varying, 'RESUELTA'::character varying, 'CERRADA'::character varying])::text[])) AND (fecha_inicio_atencion IS NOT NULL) AND (fecha_fin_atencion IS NOT NULL)))) |
| chk_incidencia_prioridad | CHECK | CHECK (((prioridad)::text = ANY ((ARRAY['BAJA'::character varying, 'MEDIA'::character varying, 'ALTA'::character varying, 'CRITICA'::character varying])::text[]))) |
| chk_incidencia_titulo | CHECK | CHECK ((btrim((titulo)::text) <> ''::text)) |
| fk_incidencia_obra | FK | FOREIGN KEY (id_obra) REFERENCES obras.t_obra(id_obra) ON DELETE RESTRICT |
| fk_incidencia_responsable | FK | FOREIGN KEY (id_responsable) REFERENCES obras.t_usuario(id_usuario) ON DELETE SET NULL |
| fk_incidencia_unidad | FK | FOREIGN KEY (id_unidad) REFERENCES obras.t_unidad_construccion(id_unidad) ON DELETE SET NULL |
| fk_incidencia_usuario_registro | FK | FOREIGN KEY (id_usuario_registro) REFERENCES obras.t_usuario(id_usuario) ON DELETE RESTRICT |
| t_incidencia_pkey | PK | PRIMARY KEY (id_incidencia) |


| ?ndice | Definici?n |
| --- | --- |
| idx_incidencia_estado | CREATE INDEX idx_incidencia_estado ON obras.t_incidencia USING btree (estado) |
| idx_incidencia_obra | CREATE INDEX idx_incidencia_obra ON obras.t_incidencia USING btree (id_obra) |
| idx_incidencia_obra_estado | CREATE INDEX idx_incidencia_obra_estado ON obras.t_incidencia USING btree (id_obra, estado) |
| idx_incidencia_prioridad | CREATE INDEX idx_incidencia_prioridad ON obras.t_incidencia USING btree (prioridad) |
| idx_incidencia_responsable | CREATE INDEX idx_incidencia_responsable ON obras.t_incidencia USING btree (id_responsable) |
| idx_incidencia_unidad | CREATE INDEX idx_incidencia_unidad ON obras.t_incidencia USING btree (id_unidad) |
| t_incidencia_pkey | CREATE UNIQUE INDEX t_incidencia_pkey ON obras.t_incidencia USING btree (id_incidencia) |


### t_incidencia_evidencia

Propietario: devpoppy. Sin id_empresa directo: revisar padre o condici?n de cat?logo global.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| id_evidencia | integer | NO | nextval('obras.t_incidencia_evidencia_id_evidencia_seq'::regclass) |
| id_incidencia | integer | NO | ? |
| id_usuario | integer | YES | ? |
| ruta_archivo | character varying(500) | NO | ? |
| nombre_archivo | character varying(255) | NO | ? |
| tipo_mime | character varying(100) | YES | ? |
| tamano_bytes | integer | YES | ? |
| fecha | timestamp with time zone | NO | CURRENT_TIMESTAMP |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| fk_incidencia_evidencia_incidencia | FK | FOREIGN KEY (id_incidencia) REFERENCES obras.t_incidencia(id_incidencia) ON DELETE CASCADE |
| fk_incidencia_evidencia_usuario | FK | FOREIGN KEY (id_usuario) REFERENCES obras.t_usuario(id_usuario) ON DELETE SET NULL |
| t_incidencia_evidencia_pkey | PK | PRIMARY KEY (id_evidencia) |


| ?ndice | Definici?n |
| --- | --- |
| idx_incidencia_evidencia_incidencia | CREATE INDEX idx_incidencia_evidencia_incidencia ON obras.t_incidencia_evidencia USING btree (id_incidencia) |
| t_incidencia_evidencia_pkey | CREATE UNIQUE INDEX t_incidencia_evidencia_pkey ON obras.t_incidencia_evidencia USING btree (id_evidencia) |


### t_incidencia_orden_trabajo

Propietario: devpoppy. Sin id_empresa directo: revisar padre o condici?n de cat?logo global.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| id_incidencia | integer | NO | ? |
| orden_nro | integer | NO | ? |
| id_usuario | integer | YES | ? |
| fecha_registro | timestamp with time zone | NO | CURRENT_TIMESTAMP |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| fk_incidencia_ot_incidencia | FK | FOREIGN KEY (id_incidencia) REFERENCES obras.t_incidencia(id_incidencia) ON DELETE CASCADE |
| fk_incidencia_ot_orden | FK | FOREIGN KEY (orden_nro) REFERENCES obras.t_orden_trabajo(orden_nro) ON DELETE CASCADE |
| fk_incidencia_ot_usuario | FK | FOREIGN KEY (id_usuario) REFERENCES obras.t_usuario(id_usuario) ON DELETE SET NULL |
| pk_incidencia_orden_trabajo | PK | PRIMARY KEY (id_incidencia, orden_nro) |


| ?ndice | Definici?n |
| --- | --- |
| idx_incidencia_ot_orden | CREATE INDEX idx_incidencia_ot_orden ON obras.t_incidencia_orden_trabajo USING btree (orden_nro) |
| pk_incidencia_orden_trabajo | CREATE UNIQUE INDEX pk_incidencia_orden_trabajo ON obras.t_incidencia_orden_trabajo USING btree (id_incidencia, orden_nro) |


### t_incidencia_seguimiento

Propietario: devpoppy. Sin id_empresa directo: revisar padre o condici?n de cat?logo global.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| id_seguimiento | integer | NO | nextval('obras.t_incidencia_seguimiento_id_seguimiento_seq'::regclass) |
| id_incidencia | integer | NO | ? |
| id_usuario | integer | YES | ? |
| estado_anterior | character varying(21) | YES | ? |
| estado_nuevo | character varying(21) | NO | ? |
| observacion | text | YES | ? |
| fecha | timestamp with time zone | NO | CURRENT_TIMESTAMP |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| chk_incidencia_seg_estado_anterior | CHECK | CHECK (((estado_anterior IS NULL) OR ((estado_anterior)::text = ANY ((ARRAY['ABIERTA'::character varying, 'ASIGNADA'::character varying, 'EN_PROCESO'::character varying, 'PENDIENTE_VALIDACION'::character varying, 'RESUELTA'::character varying, 'CERRADA'::character varying])::text[])))) |
| chk_incidencia_seg_estado_nuevo | CHECK | CHECK (((estado_nuevo)::text = ANY ((ARRAY['ABIERTA'::character varying, 'ASIGNADA'::character varying, 'EN_PROCESO'::character varying, 'PENDIENTE_VALIDACION'::character varying, 'RESUELTA'::character varying, 'CERRADA'::character varying])::text[]))) |
| fk_incidencia_seguimiento_incidencia | FK | FOREIGN KEY (id_incidencia) REFERENCES obras.t_incidencia(id_incidencia) ON DELETE CASCADE |
| fk_incidencia_seguimiento_usuario | FK | FOREIGN KEY (id_usuario) REFERENCES obras.t_usuario(id_usuario) ON DELETE SET NULL |
| t_incidencia_seguimiento_pkey | PK | PRIMARY KEY (id_seguimiento) |


| ?ndice | Definici?n |
| --- | --- |
| idx_incidencia_seguimiento_incidencia_fecha | CREATE INDEX idx_incidencia_seguimiento_incidencia_fecha ON obras.t_incidencia_seguimiento USING btree (id_incidencia, fecha DESC) |
| t_incidencia_seguimiento_pkey | CREATE UNIQUE INDEX t_incidencia_seguimiento_pkey ON obras.t_incidencia_seguimiento USING btree (id_seguimiento) |


### t_mano_obra

Propietario: devpoppy. Contiene id_empresa.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| id_mano_obra | integer | NO | nextval('obras.t_mano_obra_id_mano_obra_seq'::regclass) |
| nombre | character varying(150) | NO | ? |
| descripcion | text | YES | ? |
| id_unidad_medida | integer | NO | ? |
| costo_unitario | numeric(14,2) | NO | ? |
| activo | boolean | NO | true |
| id_empresa | integer | NO | ? |
| created_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |
| updated_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| fk_mano_obra_empresa | FK | FOREIGN KEY (id_empresa) REFERENCES obras.t_empresa(id_empresa) ON DELETE RESTRICT |
| fk_mano_obra_unidad | FK | FOREIGN KEY (id_unidad_medida) REFERENCES obras.t_unidad_medida(id_unidad_medida) ON DELETE RESTRICT |
| t_mano_obra_costo_unitario_check | CHECK | CHECK ((costo_unitario >= (0)::numeric)) |
| t_mano_obra_pkey | PK | PRIMARY KEY (id_mano_obra) |


| ?ndice | Definici?n |
| --- | --- |
| t_mano_obra_pkey | CREATE UNIQUE INDEX t_mano_obra_pkey ON obras.t_mano_obra USING btree (id_mano_obra) |
| uq_mano_obra_empresa_nombre_activo | CREATE UNIQUE INDEX uq_mano_obra_empresa_nombre_activo ON obras.t_mano_obra USING btree (id_empresa, lower(btrim((nombre)::text))) WHERE activo |


### t_material

Propietario: devpoppy. Contiene id_empresa.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| id_material | integer | NO | nextval('obras.t_material_id_material_seq'::regclass) |
| nombre_material | character varying(150) | YES | ? |
| precio | numeric(15,2) | YES | ? |
| id_proveedor | integer | YES | ? |
| codigo | character varying(50) | NO | ? |
| descripcion | text | YES | ? |
| id_categoria | integer | NO | ? |
| id_unidad_medida | integer | NO | ? |
| estado | character varying(10) | NO | 'ACTIVO'::character varying |
| id_empresa | integer | NO | ? |
| created_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |
| updated_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |
| id_material_base | integer | YES | ? |
| es_propio | boolean | NO | false |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| chk_material_estado | CHECK | CHECK (((estado)::text = ANY ((ARRAY['ACTIVO'::character varying, 'INACTIVO'::character varying])::text[]))) |
| chk_material_precio | CHECK | CHECK (((precio IS NULL) OR (precio >= (0)::numeric))) |
| fk_material_categoria | FK | FOREIGN KEY (id_categoria) REFERENCES obras.t_categoria_material(id_categoria) ON DELETE RESTRICT |
| fk_material_empresa | FK | FOREIGN KEY (id_empresa) REFERENCES obras.t_empresa(id_empresa) ON DELETE RESTRICT |
| fk_material_unidad_medida | FK | FOREIGN KEY (id_unidad_medida) REFERENCES obras.t_unidad_medida(id_unidad_medida) ON DELETE RESTRICT |
| t_material_id_material_base_fkey | FK | FOREIGN KEY (id_material_base) REFERENCES obras.t_material_base(id_material_base) ON DELETE SET NULL |
| t_material_pkey | PK | PRIMARY KEY (id_material) |
| uq_material_empresa_codigo | UNIQUE | UNIQUE (id_empresa, codigo) |


| ?ndice | Definici?n |
| --- | --- |
| idx_material_base | CREATE INDEX idx_material_base ON obras.t_material USING btree (id_material_base) |
| idx_material_categoria | CREATE INDEX idx_material_categoria ON obras.t_material USING btree (id_categoria) |
| idx_material_empresa_estado | CREATE INDEX idx_material_empresa_estado ON obras.t_material USING btree (id_empresa, estado) |
| t_material_pkey | CREATE UNIQUE INDEX t_material_pkey ON obras.t_material USING btree (id_material) |
| uq_empresa_material_base | CREATE UNIQUE INDEX uq_empresa_material_base ON obras.t_material USING btree (id_empresa, id_material_base) WHERE (id_material_base IS NOT NULL) |
| uq_material_empresa_codigo | CREATE UNIQUE INDEX uq_material_empresa_codigo ON obras.t_material USING btree (id_empresa, codigo) |


### t_material_base

Propietario: devpoppy. Sin id_empresa directo: revisar padre o condici?n de cat?logo global.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| id_material_base | integer | NO | nextval('obras.t_material_base_id_material_base_seq'::regclass) |
| codigo | character varying(50) | NO | ? |
| nombre_material | character varying(200) | NO | ? |
| descripcion | text | YES | ? |
| id_categoria | integer | NO | ? |
| id_unidad_medida | integer | NO | ? |
| precio_referencial | numeric(15,2) | YES | NULL::numeric |
| estado | character varying(20) | NO | 'ACTIVO'::character varying |
| created_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |
| updated_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| chk_material_base_estado | CHECK | CHECK (((estado)::text = ANY ((ARRAY['ACTIVO'::character varying, 'INACTIVO'::character varying])::text[]))) |
| t_material_base_id_categoria_fkey | FK | FOREIGN KEY (id_categoria) REFERENCES obras.t_categoria_material(id_categoria) |
| t_material_base_id_unidad_medida_fkey | FK | FOREIGN KEY (id_unidad_medida) REFERENCES obras.t_unidad_medida(id_unidad_medida) |
| t_material_base_pkey | PK | PRIMARY KEY (id_material_base) |
| uq_material_base_codigo | UNIQUE | UNIQUE (codigo) |


| ?ndice | Definici?n |
| --- | --- |
| idx_material_base_cat | CREATE INDEX idx_material_base_cat ON obras.t_material_base USING btree (id_categoria) |
| idx_material_base_um | CREATE INDEX idx_material_base_um ON obras.t_material_base USING btree (id_unidad_medida) |
| t_material_base_pkey | CREATE UNIQUE INDEX t_material_base_pkey ON obras.t_material_base USING btree (id_material_base) |
| uq_material_base_codigo | CREATE UNIQUE INDEX uq_material_base_codigo ON obras.t_material_base USING btree (codigo) |


### t_material_caracteristica

Propietario: devpoppy. Sin id_empresa directo: revisar padre o condici?n de cat?logo global.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| id_caracteristica | integer | NO | nextval('obras.t_material_caracteristica_id_caracteristica_seq'::regclass) |
| id_material | integer | NO | ? |
| nombre | character varying(100) | NO | ? |
| valor | character varying(250) | NO | ? |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| chk_material_caracteristica_nombre | CHECK | CHECK ((btrim((nombre)::text) <> ''::text)) |
| chk_material_caracteristica_valor | CHECK | CHECK ((btrim((valor)::text) <> ''::text)) |
| fk_material_caracteristica_material | FK | FOREIGN KEY (id_material) REFERENCES obras.t_material(id_material) ON DELETE CASCADE |
| t_material_caracteristica_pkey | PK | PRIMARY KEY (id_caracteristica) |


| ?ndice | Definici?n |
| --- | --- |
| t_material_caracteristica_pkey | CREATE UNIQUE INDEX t_material_caracteristica_pkey ON obras.t_material_caracteristica USING btree (id_caracteristica) |
| uq_material_caracteristica_nombre | CREATE UNIQUE INDEX uq_material_caracteristica_nombre ON obras.t_material_caracteristica USING btree (id_material, lower(btrim((nombre)::text))) |


### t_materiales_almacen

Propietario: devpoppy. Sin id_empresa directo: revisar padre o condici?n de cat?logo global.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| id_lote | integer | NO | nextval('obras.t_materiales_almacen_id_lote_seq'::regclass) |
| id_material | integer | YES | ? |
| cantidad_inicial | numeric(15,2) | YES | ? |
| cantidad_actual | numeric(15,2) | YES | ? |
| precio_venta | numeric(15,2) | YES | ? |
| fecha_ingreso | date | YES | ? |
| stock_minimo | numeric(14,3) | NO | 0 |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| chk_almacen_cantidad_actual | CHECK | CHECK ((cantidad_actual >= (0)::numeric)) |
| chk_almacen_cantidad_inicial | CHECK | CHECK ((cantidad_inicial >= (0)::numeric)) |
| chk_almacen_stock_minimo | CHECK | CHECK ((stock_minimo >= (0)::numeric)) |
| t_materiales_almacen_id_material_fkey | FK | FOREIGN KEY (id_material) REFERENCES obras.t_material(id_material) |
| t_materiales_almacen_pkey | PK | PRIMARY KEY (id_lote) |


| ?ndice | Definici?n |
| --- | --- |
| idx_materiales_almacen_material | CREATE INDEX idx_materiales_almacen_material ON obras.t_materiales_almacen USING btree (id_material) |
| t_materiales_almacen_pkey | CREATE UNIQUE INDEX t_materiales_almacen_pkey ON obras.t_materiales_almacen USING btree (id_lote) |


### t_modelo_caracteristica

Propietario: devpoppy. Sin id_empresa directo: revisar padre o condici?n de cat?logo global.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| id_modelo_caracteristica | integer | NO | nextval('obras.t_modelo_caracteristica_id_modelo_caracteristica_seq'::regclass) |
| id_modelo | integer | NO | ? |
| nombre | character varying(100) | NO | ? |
| valor | character varying(250) | NO | ? |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| fk_modelo_caracteristica_modelo | FK | FOREIGN KEY (id_modelo) REFERENCES obras.t_modelo_unidad(id_modelo) ON DELETE CASCADE |
| t_modelo_caracteristica_pkey | PK | PRIMARY KEY (id_modelo_caracteristica) |


| ?ndice | Definici?n |
| --- | --- |
| t_modelo_caracteristica_pkey | CREATE UNIQUE INDEX t_modelo_caracteristica_pkey ON obras.t_modelo_caracteristica USING btree (id_modelo_caracteristica) |
| uq_modelo_caracteristica_nombre | CREATE UNIQUE INDEX uq_modelo_caracteristica_nombre ON obras.t_modelo_caracteristica USING btree (id_modelo, lower((nombre)::text)) |


### t_modelo_unidad

Propietario: devpoppy. Contiene id_empresa.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| id_modelo | integer | NO | nextval('obras.t_modelo_unidad_id_modelo_seq'::regclass) |
| id_empresa | integer | NO | ? |
| nombre | character varying(120) | NO | ? |
| descripcion | text | YES | ? |
| tipo_unidad | character varying(30) | NO | 'OTRO'::character varying |
| superficie_base | numeric(12,2) | YES | ? |
| cantidad_plantas_base | integer | YES | ? |
| activo | boolean | NO | true |
| created_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |
| updated_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| chk_modelo_plantas | CHECK | CHECK (((cantidad_plantas_base IS NULL) OR (cantidad_plantas_base >= 0))) |
| chk_modelo_superficie | CHECK | CHECK (((superficie_base IS NULL) OR (superficie_base >= (0)::numeric))) |
| chk_modelo_tipo_unidad | CHECK | CHECK (((tipo_unidad)::text = ANY ((ARRAY['VIVIENDA'::character varying, 'DEPARTAMENTO'::character varying, 'LOCAL'::character varying, 'LOTE'::character varying, 'OFICINA'::character varying, 'OTRO'::character varying])::text[]))) |
| fk_modelo_unidad_empresa | FK | FOREIGN KEY (id_empresa) REFERENCES obras.t_empresa(id_empresa) ON DELETE RESTRICT |
| t_modelo_unidad_pkey | PK | PRIMARY KEY (id_modelo) |
| uq_modelo_unidad_empresa_nombre | UNIQUE | UNIQUE (id_empresa, nombre) |


| ?ndice | Definici?n |
| --- | --- |
| idx_modelo_unidad_empresa | CREATE INDEX idx_modelo_unidad_empresa ON obras.t_modelo_unidad USING btree (id_empresa) |
| t_modelo_unidad_pkey | CREATE UNIQUE INDEX t_modelo_unidad_pkey ON obras.t_modelo_unidad USING btree (id_modelo) |
| uq_modelo_unidad_empresa_nombre | CREATE UNIQUE INDEX uq_modelo_unidad_empresa_nombre ON obras.t_modelo_unidad USING btree (id_empresa, nombre) |


### t_modulo

Propietario: devpoppy. Sin id_empresa directo: revisar padre o condici?n de cat?logo global.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| id_modulo | integer | NO | nextval('obras.t_modulo_id_modulo_seq'::regclass) |
| nombre_modulo | character varying(50) | YES | ? |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| t_modulo_pkey | PK | PRIMARY KEY (id_modulo) |


| ?ndice | Definici?n |
| --- | --- |
| t_modulo_pkey | CREATE UNIQUE INDEX t_modulo_pkey ON obras.t_modulo USING btree (id_modulo) |


### t_movimiento_almacen

Propietario: devpoppy. Contiene id_empresa.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| id_movimiento | integer | NO | nextval('obras.t_movimiento_almacen_id_movimiento_seq'::regclass) |
| id_lote | integer | YES | ? |
| id_material | integer | YES | ? |
| orden_nro | integer | YES | ? |
| cantidad_asignada | numeric(15,2) | YES | ? |
| fecha_movimiento | date | YES | ? |
| tipo_movimiento | character varying(20) | YES | 'ENTRADA'::character varying |
| id_empresa | integer | YES | ? |
| id_orden_compra | integer | YES | ? |
| id_usuario | integer | YES | ? |
| observaciones | text | YES | ? |
| created_at | timestamp with time zone | YES | CURRENT_TIMESTAMP |
| id_recepcion | integer | YES | ? |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| t_movimiento_almacen_id_empresa_fkey | FK | FOREIGN KEY (id_empresa) REFERENCES obras.t_empresa(id_empresa) |
| t_movimiento_almacen_id_lote_fkey | FK | FOREIGN KEY (id_lote) REFERENCES obras.t_materiales_almacen(id_lote) |
| t_movimiento_almacen_id_material_fkey | FK | FOREIGN KEY (id_material) REFERENCES obras.t_material(id_material) |
| t_movimiento_almacen_id_orden_compra_fkey | FK | FOREIGN KEY (id_orden_compra) REFERENCES obras.t_orden_compra(id_orden_compra) |
| t_movimiento_almacen_id_recepcion_fkey | FK | FOREIGN KEY (id_recepcion) REFERENCES obras.t_recepcion_compra(id_recepcion) |
| t_movimiento_almacen_id_usuario_fkey | FK | FOREIGN KEY (id_usuario) REFERENCES obras.t_usuario(id_usuario) |
| t_movimiento_almacen_orden_nro_fkey | FK | FOREIGN KEY (orden_nro) REFERENCES obras.t_orden_trabajo(orden_nro) |
| t_movimiento_almacen_pkey | PK | PRIMARY KEY (id_movimiento) |


| ?ndice | Definici?n |
| --- | --- |
| idx_movimiento_almacen_empresa | CREATE INDEX idx_movimiento_almacen_empresa ON obras.t_movimiento_almacen USING btree (id_empresa, fecha_movimiento DESC) |
| idx_movimiento_almacen_material | CREATE INDEX idx_movimiento_almacen_material ON obras.t_movimiento_almacen USING btree (id_material) |
| idx_movimiento_almacen_orden | CREATE INDEX idx_movimiento_almacen_orden ON obras.t_movimiento_almacen USING btree (id_orden_compra) |
| t_movimiento_almacen_pkey | CREATE UNIQUE INDEX t_movimiento_almacen_pkey ON obras.t_movimiento_almacen USING btree (id_movimiento) |


### t_obra

Propietario: devpoppy. Contiene id_empresa.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| id_obra | integer | NO | nextval('obras.t_obra_id_obra_seq'::regclass) |
| id_tipo_obra | integer | YES | ? |
| estado_obra | character varying(50) | YES | ? |
| fecha_inicio | date | YES | ? |
| fecha_fin | date | YES | ? |
| id_empresa | integer | NO | ? |
| codigo | character varying(50) | YES | ? |
| nombre | character varying(100) | YES | ? |
| moneda | character varying(10) | YES | 'BOB'::character varying |
| created_at | timestamp with time zone | YES | CURRENT_TIMESTAMP |
| updated_at | timestamp with time zone | YES | CURRENT_TIMESTAMP |
| descripcion | text | YES | ? |
| presupuesto_objetivo | numeric(14,2) | YES | ? |
| estado_estimacion | character varying(20) | NO | 'SIN_ESTIMAR'::character varying |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| chk_obra_estado_estimacion | CHECK | CHECK (((estado_estimacion)::text = ANY ((ARRAY['SIN_ESTIMAR'::character varying, 'EN_ESTIMACION'::character varying, 'ESTIMADA'::character varying, 'APROBADA'::character varying])::text[]))) |
| chk_obra_fechas | CHECK | CHECK (((fecha_fin IS NULL) OR (fecha_fin >= fecha_inicio))) |
| t_obra_id_empresa_fkey | FK | FOREIGN KEY (id_empresa) REFERENCES obras.t_empresa(id_empresa) |
| t_obra_id_tipo_obra_fkey | FK | FOREIGN KEY (id_tipo_obra) REFERENCES obras.t_tipo_obra(id_tipo_obra) |
| t_obra_pkey | PK | PRIMARY KEY (id_obra) |
| uq_obra_empresa_codigo | UNIQUE | UNIQUE (id_empresa, codigo) |


| ?ndice | Definici?n |
| --- | --- |
| idx_obra_id_empresa | CREATE INDEX idx_obra_id_empresa ON obras.t_obra USING btree (id_empresa) |
| idx_obra_id_tipo_obra | CREATE INDEX idx_obra_id_tipo_obra ON obras.t_obra USING btree (id_tipo_obra) |
| t_obra_pkey | CREATE UNIQUE INDEX t_obra_pkey ON obras.t_obra USING btree (id_obra) |
| uq_obra_empresa_codigo | CREATE UNIQUE INDEX uq_obra_empresa_codigo ON obras.t_obra USING btree (id_empresa, codigo) |


### t_obra_estimacion

Propietario: devpoppy. Sin id_empresa directo: revisar padre o condici?n de cat?logo global.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| id_estimacion | integer | NO | nextval('obras.t_obra_estimacion_id_estimacion_seq'::regclass) |
| id_obra | integer | NO | ? |
| tipo_obra | character varying(100) | NO | ? |
| superficie_m2 | numeric(12,2) | NO | ? |
| niveles | integer | NO | 1 |
| tipo_terreno | character varying(100) | NO | ? |
| complejidad | character varying(50) | NO | ? |
| ubicacion | character varying(255) | YES | ? |
| caracteristicas_generales | text | YES | ? |
| costo_referencial_m2 | numeric(15,2) | NO | ? |
| factor_niveles | numeric(8,4) | NO | ? |
| factor_terreno | numeric(8,4) | NO | ? |
| factor_complejidad | numeric(8,4) | NO | ? |
| costo_base | numeric(15,2) | NO | ? |
| monto_estimado | numeric(15,2) | NO | ? |
| moneda | character varying(10) | NO | 'BOB'::character varying |
| fecha_estimacion | timestamp with time zone | NO | CURRENT_TIMESTAMP |
| created_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| t_obra_estimacion_id_obra_fkey | FK | FOREIGN KEY (id_obra) REFERENCES obras.t_obra(id_obra) ON DELETE CASCADE |
| t_obra_estimacion_pkey | PK | PRIMARY KEY (id_estimacion) |


| ?ndice | Definici?n |
| --- | --- |
| idx_obra_estimacion_obra | CREATE INDEX idx_obra_estimacion_obra ON obras.t_obra_estimacion USING btree (id_obra) |
| t_obra_estimacion_pkey | CREATE UNIQUE INDEX t_obra_estimacion_pkey ON obras.t_obra_estimacion USING btree (id_estimacion) |


### t_obra_usuario

Propietario: devpoppy. Sin id_empresa directo: revisar padre o condici?n de cat?logo global.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| id_obra | integer | NO | ? |
| id_usuario | integer | NO | ? |
| fecha_asignacion | timestamp with time zone | YES | CURRENT_TIMESTAMP |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| fk_obra_usuario_obra | FK | FOREIGN KEY (id_obra) REFERENCES obras.t_obra(id_obra) ON DELETE CASCADE |
| fk_obra_usuario_usuario | FK | FOREIGN KEY (id_usuario) REFERENCES obras.t_usuario(id_usuario) ON DELETE CASCADE |
| t_obra_usuario_pkey | PK | PRIMARY KEY (id_obra, id_usuario) |


| ?ndice | Definici?n |
| --- | --- |
| idx_obra_usuario_id_usuario | CREATE INDEX idx_obra_usuario_id_usuario ON obras.t_obra_usuario USING btree (id_usuario) |
| t_obra_usuario_pkey | CREATE UNIQUE INDEX t_obra_usuario_pkey ON obras.t_obra_usuario USING btree (id_obra, id_usuario) |


### t_orden_cambio

Propietario: devpoppy. Contiene id_empresa.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| id_orden_cambio | bigint | NO | nextval('obras.t_orden_cambio_id_orden_cambio_seq'::regclass) |
| codigo | character varying(40) | NO | ? |
| id_control_costo | bigint | NO | ? |
| id_empresa | integer | NO | ? |
| id_obra | integer | NO | ? |
| id_estimacion_base | integer | NO | ? |
| titulo | character varying(200) | NO | ? |
| descripcion | text | YES | ? |
| justificacion | text | NO | ? |
| fecha | date | NO | ? |
| impacto_costo | numeric(16,2) | NO | 0 |
| impacto_plazo_dias | integer | NO | 0 |
| estado | character varying(12) | NO | 'PENDIENTE'::character varying |
| solicitado_por | integer | NO | ? |
| decidido_por | integer | YES | ? |
| fecha_decision | timestamp with time zone | YES | ? |
| motivo_decision | text | YES | ? |
| created_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |
| updated_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| chk_orden_cambio_codigo | CHECK | CHECK ((btrim((codigo)::text) <> ''::text)) |
| chk_orden_cambio_decision | CHECK | CHECK (((((estado)::text = 'PENDIENTE'::text) AND (decidido_por IS NULL) AND (fecha_decision IS NULL) AND (motivo_decision IS NULL)) OR (((estado)::text = 'APROBADA'::text) AND (decidido_por IS NOT NULL) AND (fecha_decision IS NOT NULL)) OR (((estado)::text = 'RECHAZADA'::text) AND (decidido_por IS NOT NULL) AND (fecha_decision IS NOT NULL) AND (motivo_decision IS NOT NULL) AND (btrim(motivo_decision) <> ''::text)))) |
| chk_orden_cambio_estado | CHECK | CHECK (((estado)::text = ANY ((ARRAY['PENDIENTE'::character varying, 'APROBADA'::character varying, 'RECHAZADA'::character varying])::text[]))) |
| chk_orden_cambio_justificacion | CHECK | CHECK ((btrim(justificacion) <> ''::text)) |
| chk_orden_cambio_titulo | CHECK | CHECK ((btrim((titulo)::text) <> ''::text)) |
| fk_orden_cambio_control | FK | FOREIGN KEY (id_control_costo) REFERENCES obras.t_control_costo_obra(id_control_costo) ON DELETE RESTRICT |
| fk_orden_cambio_decidido_por | FK | FOREIGN KEY (decidido_por) REFERENCES obras.t_usuario(id_usuario) ON DELETE RESTRICT |
| fk_orden_cambio_empresa | FK | FOREIGN KEY (id_empresa) REFERENCES obras.t_empresa(id_empresa) ON DELETE RESTRICT |
| fk_orden_cambio_estimacion | FK | FOREIGN KEY (id_estimacion_base) REFERENCES obras.t_estimacion(id_estimacion) ON DELETE RESTRICT |
| fk_orden_cambio_obra | FK | FOREIGN KEY (id_obra) REFERENCES obras.t_obra(id_obra) ON DELETE RESTRICT |
| fk_orden_cambio_solicitado_por | FK | FOREIGN KEY (solicitado_por) REFERENCES obras.t_usuario(id_usuario) ON DELETE RESTRICT |
| t_orden_cambio_pkey | PK | PRIMARY KEY (id_orden_cambio) |
| uq_orden_cambio_codigo | UNIQUE | UNIQUE (id_empresa, id_obra, codigo) |


| ?ndice | Definici?n |
| --- | --- |
| idx_orden_cambio_control_estado | CREATE INDEX idx_orden_cambio_control_estado ON obras.t_orden_cambio USING btree (id_control_costo, estado) |
| idx_orden_cambio_empresa_obra | CREATE INDEX idx_orden_cambio_empresa_obra ON obras.t_orden_cambio USING btree (id_empresa, id_obra) |
| t_orden_cambio_pkey | CREATE UNIQUE INDEX t_orden_cambio_pkey ON obras.t_orden_cambio USING btree (id_orden_cambio) |
| uq_orden_cambio_codigo | CREATE UNIQUE INDEX uq_orden_cambio_codigo ON obras.t_orden_cambio USING btree (id_empresa, id_obra, codigo) |


### t_orden_cambio_detalle

Propietario: devpoppy. Sin id_empresa directo: revisar padre o condici?n de cat?logo global.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| id_orden_cambio_detalle | bigint | NO | nextval('obras.t_orden_cambio_detalle_id_orden_cambio_detalle_seq'::regclass) |
| id_orden_cambio | bigint | NO | ? |
| id_partida_presupuestaria | integer | YES | ? |
| id_analisis_precio_unitario | integer | YES | ? |
| tipo_cambio | character varying(30) | NO | ? |
| item_codigo_snapshot | character varying(40) | NO | ? |
| descripcion_snapshot | character varying(250) | NO | ? |
| unidad_snapshot | character varying(30) | NO | ? |
| cantidad_anterior | numeric(14,3) | NO | 0 |
| cantidad_delta | numeric(14,3) | NO | 0 |
| cantidad_revisada | numeric(14,3) | NO | 0 |
| costo_anterior | numeric(16,2) | NO | 0 |
| costo_nuevo | numeric(16,2) | NO | 0 |
| impacto_costo | numeric(16,2) | NO | ? |
| observacion | text | YES | ? |
| created_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| chk_orden_cambio_detalle_cantidades | CHECK | CHECK (((cantidad_anterior >= (0)::numeric) AND (cantidad_revisada >= (0)::numeric))) |
| chk_orden_cambio_detalle_costos | CHECK | CHECK (((costo_anterior >= (0)::numeric) AND (costo_nuevo >= (0)::numeric))) |
| chk_orden_cambio_detalle_origen | CHECK | CHECK (((((tipo_cambio)::text = 'NUEVA_PARTIDA'::text) AND (id_partida_presupuestaria IS NULL)) OR (((tipo_cambio)::text <> 'NUEVA_PARTIDA'::text) AND (id_partida_presupuestaria IS NOT NULL)))) |
| chk_orden_cambio_detalle_snapshot | CHECK | CHECK (((btrim((item_codigo_snapshot)::text) <> ''::text) AND (btrim((descripcion_snapshot)::text) <> ''::text) AND (btrim((unidad_snapshot)::text) <> ''::text))) |
| chk_orden_cambio_detalle_tipo | CHECK | CHECK (((tipo_cambio)::text = ANY ((ARRAY['AUMENTO_CANTIDAD'::character varying, 'DISMINUCION_CANTIDAD'::character varying, 'CAMBIO_COSTO'::character varying, 'NUEVA_PARTIDA'::character varying, 'ELIMINACION_PARTIDA'::character varying])::text[]))) |
| fk_orden_cambio_detalle_apu | FK | FOREIGN KEY (id_analisis_precio_unitario) REFERENCES obras.t_analisis_precio_unitario(id_analisis_precio_unitario) ON DELETE RESTRICT |
| fk_orden_cambio_detalle_orden | FK | FOREIGN KEY (id_orden_cambio) REFERENCES obras.t_orden_cambio(id_orden_cambio) ON DELETE CASCADE |
| fk_orden_cambio_detalle_partida | FK | FOREIGN KEY (id_partida_presupuestaria) REFERENCES obras.t_estimacion_analisis_precio_unitario(id_estimacion_analisis_precio_unitario) ON DELETE RESTRICT |
| t_orden_cambio_detalle_pkey | PK | PRIMARY KEY (id_orden_cambio_detalle) |


| ?ndice | Definici?n |
| --- | --- |
| idx_orden_cambio_detalle_orden | CREATE INDEX idx_orden_cambio_detalle_orden ON obras.t_orden_cambio_detalle USING btree (id_orden_cambio) |
| idx_orden_cambio_detalle_partida | CREATE INDEX idx_orden_cambio_detalle_partida ON obras.t_orden_cambio_detalle USING btree (id_partida_presupuestaria) |
| t_orden_cambio_detalle_pkey | CREATE UNIQUE INDEX t_orden_cambio_detalle_pkey ON obras.t_orden_cambio_detalle USING btree (id_orden_cambio_detalle) |


### t_orden_cambio_historial

Propietario: devpoppy. Sin id_empresa directo: revisar padre o condici?n de cat?logo global.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| id_orden_cambio_historial | bigint | NO | nextval('obras.t_orden_cambio_historial_id_orden_cambio_historial_seq'::regclass) |
| id_orden_cambio | bigint | NO | ? |
| estado_anterior | character varying(12) | YES | ? |
| estado_nuevo | character varying(12) | NO | ? |
| accion | character varying(30) | NO | ? |
| comentario | text | YES | ? |
| id_usuario | integer | NO | ? |
| fecha_evento | timestamp with time zone | NO | CURRENT_TIMESTAMP |
| ip_origen | character varying(64) | YES | ? |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| chk_orden_cambio_historial_accion | CHECK | CHECK (((accion)::text = ANY ((ARRAY['CREACION'::character varying, 'MODIFICACION'::character varying, 'APROBACION'::character varying, 'RECHAZO'::character varying])::text[]))) |
| chk_orden_cambio_historial_estados | CHECK | CHECK ((((estado_anterior IS NULL) OR ((estado_anterior)::text = ANY ((ARRAY['PENDIENTE'::character varying, 'APROBADA'::character varying, 'RECHAZADA'::character varying])::text[]))) AND ((estado_nuevo)::text = ANY ((ARRAY['PENDIENTE'::character varying, 'APROBADA'::character varying, 'RECHAZADA'::character varying])::text[])))) |
| fk_orden_cambio_historial_orden | FK | FOREIGN KEY (id_orden_cambio) REFERENCES obras.t_orden_cambio(id_orden_cambio) ON DELETE RESTRICT |
| fk_orden_cambio_historial_usuario | FK | FOREIGN KEY (id_usuario) REFERENCES obras.t_usuario(id_usuario) ON DELETE RESTRICT |
| t_orden_cambio_historial_pkey | PK | PRIMARY KEY (id_orden_cambio_historial) |


| ?ndice | Definici?n |
| --- | --- |
| idx_orden_cambio_historial_orden_fecha | CREATE INDEX idx_orden_cambio_historial_orden_fecha ON obras.t_orden_cambio_historial USING btree (id_orden_cambio, fecha_evento DESC) |
| t_orden_cambio_historial_pkey | CREATE UNIQUE INDEX t_orden_cambio_historial_pkey ON obras.t_orden_cambio_historial USING btree (id_orden_cambio_historial) |


### t_orden_compra

Propietario: devpoppy. Contiene id_empresa.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| id_orden_compra | integer | NO | nextval('obras.t_orden_compra_id_orden_compra_seq'::regclass) |
| id_empresa | integer | NO | ? |
| id_proveedor | integer | NO | ? |
| numero_orden | character varying(50) | NO | ? |
| fecha | date | NO | CURRENT_DATE |
| observaciones | text | YES | ? |
| estado | character varying(30) | NO | 'BORRADOR'::character varying |
| id_usuario_solicitante | integer | NO | ? |
| subtotal | numeric(15,2) | NO | 0.00 |
| total | numeric(15,2) | NO | 0.00 |
| id_usuario_aprobacion | integer | YES | ? |
| fecha_aprobacion | timestamp with time zone | YES | ? |
| observacion_aprobacion | text | YES | ? |
| created_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |
| updated_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| chk_orden_compra_estado | CHECK | CHECK (((estado)::text = ANY ((ARRAY['BORRADOR'::character varying, 'PENDIENTE_APROBACION'::character varying, 'APROBADA'::character varying, 'RECHAZADA'::character varying, 'CANCELADA'::character varying, 'RECIBIDA_PARCIAL'::character varying, 'RECIBIDA'::character varying])::text[]))) |
| t_orden_compra_id_empresa_fkey | FK | FOREIGN KEY (id_empresa) REFERENCES obras.t_empresa(id_empresa) ON DELETE RESTRICT |
| t_orden_compra_id_proveedor_fkey | FK | FOREIGN KEY (id_proveedor) REFERENCES obras.t_proveedor(id_proveedor) ON DELETE RESTRICT |
| t_orden_compra_id_usuario_aprobacion_fkey | FK | FOREIGN KEY (id_usuario_aprobacion) REFERENCES obras.t_usuario(id_usuario) ON DELETE SET NULL |
| t_orden_compra_id_usuario_solicitante_fkey | FK | FOREIGN KEY (id_usuario_solicitante) REFERENCES obras.t_usuario(id_usuario) ON DELETE RESTRICT |
| t_orden_compra_pkey | PK | PRIMARY KEY (id_orden_compra) |
| uq_orden_compra_empresa_numero | UNIQUE | UNIQUE (id_empresa, numero_orden) |


| ?ndice | Definici?n |
| --- | --- |
| idx_orden_compra_empresa | CREATE INDEX idx_orden_compra_empresa ON obras.t_orden_compra USING btree (id_empresa) |
| idx_orden_compra_estado | CREATE INDEX idx_orden_compra_estado ON obras.t_orden_compra USING btree (id_empresa, estado) |
| idx_orden_compra_proveedor | CREATE INDEX idx_orden_compra_proveedor ON obras.t_orden_compra USING btree (id_proveedor) |
| t_orden_compra_pkey | CREATE UNIQUE INDEX t_orden_compra_pkey ON obras.t_orden_compra USING btree (id_orden_compra) |
| uq_orden_compra_empresa_numero | CREATE UNIQUE INDEX uq_orden_compra_empresa_numero ON obras.t_orden_compra USING btree (id_empresa, numero_orden) |


### t_orden_compra_detalle

Propietario: devpoppy. Sin id_empresa directo: revisar padre o condici?n de cat?logo global.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| id_detalle | integer | NO | nextval('obras.t_orden_compra_detalle_id_detalle_seq'::regclass) |
| id_orden_compra | integer | NO | ? |
| id_material | integer | NO | ? |
| cantidad_solicitada | numeric(14,3) | NO | ? |
| precio_unitario | numeric(15,2) | NO | ? |
| subtotal | numeric(15,2) | NO | ? |
| cantidad_recibida | numeric(14,3) | NO | 0.00 |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| chk_detalle_recibida_le_solicitada | CHECK | CHECK ((cantidad_recibida <= cantidad_solicitada)) |
| t_orden_compra_detalle_cantidad_recibida_check | CHECK | CHECK ((cantidad_recibida >= (0)::numeric)) |
| t_orden_compra_detalle_cantidad_solicitada_check | CHECK | CHECK ((cantidad_solicitada > (0)::numeric)) |
| t_orden_compra_detalle_id_material_fkey | FK | FOREIGN KEY (id_material) REFERENCES obras.t_material(id_material) ON DELETE RESTRICT |
| t_orden_compra_detalle_id_orden_compra_fkey | FK | FOREIGN KEY (id_orden_compra) REFERENCES obras.t_orden_compra(id_orden_compra) ON DELETE CASCADE |
| t_orden_compra_detalle_pkey | PK | PRIMARY KEY (id_detalle) |
| t_orden_compra_detalle_precio_unitario_check | CHECK | CHECK ((precio_unitario >= (0)::numeric)) |
| t_orden_compra_detalle_subtotal_check | CHECK | CHECK ((subtotal >= (0)::numeric)) |
| uq_orden_compra_material | UNIQUE | UNIQUE (id_orden_compra, id_material) |


| ?ndice | Definici?n |
| --- | --- |
| idx_orden_compra_detalle_material | CREATE INDEX idx_orden_compra_detalle_material ON obras.t_orden_compra_detalle USING btree (id_material) |
| idx_orden_compra_detalle_orden | CREATE INDEX idx_orden_compra_detalle_orden ON obras.t_orden_compra_detalle USING btree (id_orden_compra) |
| t_orden_compra_detalle_pkey | CREATE UNIQUE INDEX t_orden_compra_detalle_pkey ON obras.t_orden_compra_detalle USING btree (id_detalle) |
| uq_orden_compra_material | CREATE UNIQUE INDEX uq_orden_compra_material ON obras.t_orden_compra_detalle USING btree (id_orden_compra, id_material) |


### t_orden_trabajo

Propietario: devpoppy. Sin id_empresa directo: revisar padre o condici?n de cat?logo global.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| orden_nro | integer | NO | nextval('obras.t_orden_trabajo_orden_nro_seq'::regclass) |
| id_obra | integer | YES | ? |
| tipo_trab | character varying(100) | YES | ? |
| cuadrilla | integer | YES | ? |
| estado | character varying(50) | YES | ? |
| fecha_inicio | date | YES | ? |
| fecha_fin | date | YES | ? |
| observacion | text | YES | ? |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| t_orden_trabajo_id_obra_fkey | FK | FOREIGN KEY (id_obra) REFERENCES obras.t_obra(id_obra) |
| t_orden_trabajo_pkey | PK | PRIMARY KEY (orden_nro) |


| ?ndice | Definici?n |
| --- | --- |
| t_orden_trabajo_pkey | CREATE UNIQUE INDEX t_orden_trabajo_pkey ON obras.t_orden_trabajo USING btree (orden_nro) |


### t_orden_trabajo_permiso

Propietario: devpoppy. Sin id_empresa directo: revisar padre o condici?n de cat?logo global.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| id_permiso_orden_trabajo | integer | NO | nextval('obras.t_orden_trabajo_permiso_id_permiso_orden_trabajo_seq'::regclass) |
| nombre_permiso | character varying(100) | NO | ? |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| t_orden_trabajo_permiso_pkey | PK | PRIMARY KEY (id_permiso_orden_trabajo) |


| ?ndice | Definici?n |
| --- | --- |
| t_orden_trabajo_permiso_pkey | CREATE UNIQUE INDEX t_orden_trabajo_permiso_pkey ON obras.t_orden_trabajo_permiso USING btree (id_permiso_orden_trabajo) |


### t_orden_trabajo_usuario

Propietario: devpoppy. Sin id_empresa directo: revisar padre o condici?n de cat?logo global.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| id_orden_trabajo | integer | NO | ? |
| id_usuario | integer | NO | ? |
| fecha_asignacion | timestamp with time zone | YES | CURRENT_TIMESTAMP |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| fk_obra_usuario_usuario | FK | FOREIGN KEY (id_usuario) REFERENCES obras.t_usuario(id_usuario) ON DELETE CASCADE |
| t_orden_trabajo_usuario_id_orden_trabajo_fkey | FK | FOREIGN KEY (id_orden_trabajo) REFERENCES obras.t_orden_trabajo(orden_nro) ON DELETE CASCADE |
| t_orden_trabajo_usuario_pkey | PK | PRIMARY KEY (id_orden_trabajo, id_usuario) |


| ?ndice | Definici?n |
| --- | --- |
| t_orden_trabajo_usuario_pkey | CREATE UNIQUE INDEX t_orden_trabajo_usuario_pkey ON obras.t_orden_trabajo_usuario USING btree (id_orden_trabajo, id_usuario) |


### t_parametro_estimacion

Propietario: devpoppy. Contiene id_empresa.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| id_parametro | integer | NO | nextval('obras.t_parametro_estimacion_id_parametro_seq'::regclass) |
| id_empresa | integer | YES | ? |
| categoria | character varying(50) | NO | ? |
| codigo_clave | character varying(50) | NO | ? |
| nombre | character varying(100) | NO | ? |
| valor_numerico | numeric(15,4) | NO | ? |
| descripcion | text | YES | ? |
| activo | boolean | NO | true |
| created_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |
| updated_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| t_parametro_estimacion_id_empresa_fkey | FK | FOREIGN KEY (id_empresa) REFERENCES obras.t_empresa(id_empresa) ON DELETE CASCADE |
| t_parametro_estimacion_pkey | PK | PRIMARY KEY (id_parametro) |


| ?ndice | Definici?n |
| --- | --- |
| idx_parametro_cat_clave | CREATE INDEX idx_parametro_cat_clave ON obras.t_parametro_estimacion USING btree (categoria, codigo_clave, activo) |
| t_parametro_estimacion_pkey | CREATE UNIQUE INDEX t_parametro_estimacion_pkey ON obras.t_parametro_estimacion USING btree (id_parametro) |
| uq_param_empresa_categoria_clave | CREATE UNIQUE INDEX uq_param_empresa_categoria_clave ON obras.t_parametro_estimacion USING btree (COALESCE(id_empresa, 0), categoria, codigo_clave) |


### t_partida_presupuesto

Propietario: devpoppy. Sin id_empresa directo: revisar padre o condici?n de cat?logo global.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| id_partida | integer | NO | nextval('obras.t_partida_presupuesto_id_partida_seq'::regclass) |
| id_presupuesto | integer | NO | ? |
| codigo | character varying(50) | NO | ? |
| nombre | character varying(200) | NO | ? |
| descripcion | text | YES | ? |
| id_unidad_medida | integer | NO | ? |
| cantidad | numeric(14,4) | NO | 1.0000 |
| precio_unitario | numeric(15,2) | NO | 0.00 |
| importe_total | numeric(15,2) | NO | 0.00 |
| orden | integer | NO | 0 |
| id_estructura | integer | YES | ? |
| id_unidad_construccion | integer | YES | ? |
| created_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |
| updated_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| chk_partida_cant_pos | CHECK | CHECK ((cantidad >= (0)::numeric)) |
| chk_partida_precio_pos | CHECK | CHECK ((precio_unitario >= (0)::numeric)) |
| t_partida_presupuesto_id_estructura_fkey | FK | FOREIGN KEY (id_estructura) REFERENCES obras.t_estructura_obra(id_estructura) ON DELETE SET NULL |
| t_partida_presupuesto_id_presupuesto_fkey | FK | FOREIGN KEY (id_presupuesto) REFERENCES obras.t_presupuesto(id_presupuesto) ON DELETE CASCADE |
| t_partida_presupuesto_id_unidad_construccion_fkey | FK | FOREIGN KEY (id_unidad_construccion) REFERENCES obras.t_unidad_construccion(id_unidad) ON DELETE SET NULL |
| t_partida_presupuesto_id_unidad_medida_fkey | FK | FOREIGN KEY (id_unidad_medida) REFERENCES obras.t_unidad_medida(id_unidad_medida) |
| t_partida_presupuesto_pkey | PK | PRIMARY KEY (id_partida) |


| ?ndice | Definici?n |
| --- | --- |
| idx_partida_presupuesto | CREATE INDEX idx_partida_presupuesto ON obras.t_partida_presupuesto USING btree (id_presupuesto) |
| t_partida_presupuesto_pkey | CREATE UNIQUE INDEX t_partida_presupuesto_pkey ON obras.t_partida_presupuesto USING btree (id_partida) |


### t_permiso

Propietario: devpoppy. Sin id_empresa directo: revisar padre o condici?n de cat?logo global.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| id_permiso | integer | NO | nextval('obras.t_permiso_id_permiso_seq'::regclass) |
| nombre_permiso | character varying(100) | YES | ? |
| id_modulo | bigint | YES | ? |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| t_permiso_id_modulo_fkey | FK | FOREIGN KEY (id_modulo) REFERENCES obras.t_modulo(id_modulo) |
| t_permiso_pkey | PK | PRIMARY KEY (id_permiso) |


| ?ndice | Definici?n |
| --- | --- |
| t_permiso_pkey | CREATE UNIQUE INDEX t_permiso_pkey ON obras.t_permiso USING btree (id_permiso) |


### t_persona

Propietario: devpoppy. Sin id_empresa directo: revisar padre o condici?n de cat?logo global.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| id_persona | integer | NO | nextval('obras.t_persona_id_persona_seq'::regclass) |
| nombre_completo | character varying(150) | YES | ? |
| fecha_nacimiento | date | YES | ? |
| ci | character varying(30) | YES | ? |
| direccion | character varying(250) | YES | ? |
| telefono | character varying(30) | YES | ? |
| telefono_ref | character varying(30) | YES | ? |
| ubicacion | character varying(250) | YES | ? |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| t_persona_pkey | PK | PRIMARY KEY (id_persona) |


| ?ndice | Definici?n |
| --- | --- |
| t_persona_pkey | CREATE UNIQUE INDEX t_persona_pkey ON obras.t_persona USING btree (id_persona) |


### t_presupuesto

Propietario: devpoppy. Sin id_empresa directo: revisar padre o condici?n de cat?logo global.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| id_presupuesto | integer | NO | nextval('obras.t_presupuesto_id_presupuesto_seq'::regclass) |
| id_obra | integer | NO | ? |
| codigo | character varying(50) | NO | ? |
| nombre | character varying(200) | NO | ? |
| descripcion | text | YES | ? |
| version | integer | NO | 1 |
| estado | character varying(30) | NO | 'BORRADOR'::character varying |
| es_vigente | boolean | NO | false |
| fecha | date | NO | CURRENT_DATE |
| superficie_m2 | numeric(12,2) | YES | NULL::numeric |
| tipo_suelo | character varying(100) | YES | NULL::character varying |
| costo_m2_estimado | numeric(15,2) | YES | NULL::numeric |
| monto_estimado_inicial | numeric(15,2) | YES | NULL::numeric |
| total_presupuesto | numeric(15,2) | NO | 0.00 |
| observaciones | text | YES | ? |
| created_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |
| updated_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| chk_presupuesto_estado | CHECK | CHECK (((estado)::text = ANY ((ARRAY['BORRADOR'::character varying, 'EN_REVISION'::character varying, 'APROBADO'::character varying, 'CERRADO'::character varying])::text[]))) |
| chk_presupuesto_version_pos | CHECK | CHECK ((version >= 1)) |
| t_presupuesto_id_obra_fkey | FK | FOREIGN KEY (id_obra) REFERENCES obras.t_obra(id_obra) ON DELETE CASCADE |
| t_presupuesto_pkey | PK | PRIMARY KEY (id_presupuesto) |
| uq_presupuesto_obra_version | UNIQUE | UNIQUE (id_obra, version) |


| ?ndice | Definici?n |
| --- | --- |
| idx_presupuesto_obra | CREATE INDEX idx_presupuesto_obra ON obras.t_presupuesto USING btree (id_obra) |
| t_presupuesto_pkey | CREATE UNIQUE INDEX t_presupuesto_pkey ON obras.t_presupuesto USING btree (id_presupuesto) |
| uq_presupuesto_obra_version | CREATE UNIQUE INDEX uq_presupuesto_obra_version ON obras.t_presupuesto USING btree (id_obra, version) |
| uq_presupuesto_obra_vigente | CREATE UNIQUE INDEX uq_presupuesto_obra_vigente ON obras.t_presupuesto USING btree (id_obra) WHERE (es_vigente = true) |


### t_proveedor

Propietario: devpoppy. Contiene id_empresa.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| id_proveedor | integer | NO | nextval('obras.t_proveedor_id_proveedor_seq'::regclass) |
| nombre | character varying(200) | NO | ? |
| nit | character varying(50) | NO | ? |
| telefono | character varying(30) | YES | ? |
| email | character varying(150) | YES | ? |
| direccion | text | YES | ? |
| contacto | character varying(150) | YES | ? |
| estado | character varying(10) | NO | 'ACTIVO'::character varying |
| id_empresa | integer | NO | ? |
| created_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |
| updated_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| chk_proveedor_estado | CHECK | CHECK (((estado)::text = ANY ((ARRAY['ACTIVO'::character varying, 'INACTIVO'::character varying])::text[]))) |
| chk_proveedor_nit | CHECK | CHECK ((btrim((nit)::text) <> ''::text)) |
| chk_proveedor_nombre | CHECK | CHECK ((btrim((nombre)::text) <> ''::text)) |
| fk_proveedor_empresa | FK | FOREIGN KEY (id_empresa) REFERENCES obras.t_empresa(id_empresa) ON DELETE RESTRICT |
| t_proveedor_pkey | PK | PRIMARY KEY (id_proveedor) |


| ?ndice | Definici?n |
| --- | --- |
| idx_proveedor_empresa_estado | CREATE INDEX idx_proveedor_empresa_estado ON obras.t_proveedor USING btree (id_empresa, estado) |
| t_proveedor_pkey | CREATE UNIQUE INDEX t_proveedor_pkey ON obras.t_proveedor USING btree (id_proveedor) |
| uq_proveedor_empresa_nit | CREATE UNIQUE INDEX uq_proveedor_empresa_nit ON obras.t_proveedor USING btree (id_empresa, lower(btrim((nit)::text))) |


### t_proveedor_material

Propietario: devpoppy. Sin id_empresa directo: revisar padre o condici?n de cat?logo global.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| id_proveedor_material | integer | NO | nextval('obras.t_proveedor_material_id_proveedor_material_seq'::regclass) |
| id_proveedor | integer | NO | ? |
| id_material | integer | NO | ? |
| created_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| fk_pm_material | FK | FOREIGN KEY (id_material) REFERENCES obras.t_material(id_material) ON DELETE CASCADE |
| fk_pm_proveedor | FK | FOREIGN KEY (id_proveedor) REFERENCES obras.t_proveedor(id_proveedor) ON DELETE CASCADE |
| t_proveedor_material_pkey | PK | PRIMARY KEY (id_proveedor_material) |
| uq_proveedor_material | UNIQUE | UNIQUE (id_proveedor, id_material) |


| ?ndice | Definici?n |
| --- | --- |
| idx_pm_material | CREATE INDEX idx_pm_material ON obras.t_proveedor_material USING btree (id_material) |
| idx_pm_proveedor | CREATE INDEX idx_pm_proveedor ON obras.t_proveedor_material USING btree (id_proveedor) |
| t_proveedor_material_pkey | CREATE UNIQUE INDEX t_proveedor_material_pkey ON obras.t_proveedor_material USING btree (id_proveedor_material) |
| uq_proveedor_material | CREATE UNIQUE INDEX uq_proveedor_material ON obras.t_proveedor_material USING btree (id_proveedor, id_material) |


### t_recepcion_compra

Propietario: devpoppy. Contiene id_empresa.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| id_recepcion | integer | NO | nextval('obras.t_recepcion_compra_id_recepcion_seq'::regclass) |
| id_orden_compra | integer | NO | ? |
| id_empresa | integer | NO | ? |
| numero_recepcion | character varying(50) | NO | ? |
| fecha_recepcion | timestamp with time zone | NO | CURRENT_TIMESTAMP |
| id_usuario_recepcion | integer | NO | ? |
| observaciones | text | YES | ? |
| created_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| t_recepcion_compra_id_empresa_fkey | FK | FOREIGN KEY (id_empresa) REFERENCES obras.t_empresa(id_empresa) ON DELETE RESTRICT |
| t_recepcion_compra_id_orden_compra_fkey | FK | FOREIGN KEY (id_orden_compra) REFERENCES obras.t_orden_compra(id_orden_compra) ON DELETE RESTRICT |
| t_recepcion_compra_id_usuario_recepcion_fkey | FK | FOREIGN KEY (id_usuario_recepcion) REFERENCES obras.t_usuario(id_usuario) ON DELETE RESTRICT |
| t_recepcion_compra_pkey | PK | PRIMARY KEY (id_recepcion) |
| uq_recepcion_empresa_numero | UNIQUE | UNIQUE (id_empresa, numero_recepcion) |


| ?ndice | Definici?n |
| --- | --- |
| idx_recepcion_compra_empresa | CREATE INDEX idx_recepcion_compra_empresa ON obras.t_recepcion_compra USING btree (id_empresa) |
| idx_recepcion_compra_orden | CREATE INDEX idx_recepcion_compra_orden ON obras.t_recepcion_compra USING btree (id_orden_compra) |
| t_recepcion_compra_pkey | CREATE UNIQUE INDEX t_recepcion_compra_pkey ON obras.t_recepcion_compra USING btree (id_recepcion) |
| uq_recepcion_empresa_numero | CREATE UNIQUE INDEX uq_recepcion_empresa_numero ON obras.t_recepcion_compra USING btree (id_empresa, numero_recepcion) |


### t_recepcion_compra_detalle

Propietario: devpoppy. Sin id_empresa directo: revisar padre o condici?n de cat?logo global.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| id_recepcion_detalle | integer | NO | nextval('obras.t_recepcion_compra_detalle_id_recepcion_detalle_seq'::regclass) |
| id_recepcion | integer | NO | ? |
| id_orden_compra_detalle | integer | NO | ? |
| id_material | integer | NO | ? |
| cantidad_recibida | numeric(14,3) | NO | ? |
| precio_unitario | numeric(15,2) | NO | 0.00 |
| id_movimiento_almacen | integer | YES | ? |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| t_recepcion_compra_detalle_cantidad_recibida_check | CHECK | CHECK ((cantidad_recibida > (0)::numeric)) |
| t_recepcion_compra_detalle_id_material_fkey | FK | FOREIGN KEY (id_material) REFERENCES obras.t_material(id_material) ON DELETE RESTRICT |
| t_recepcion_compra_detalle_id_movimiento_almacen_fkey | FK | FOREIGN KEY (id_movimiento_almacen) REFERENCES obras.t_movimiento_almacen(id_movimiento) ON DELETE SET NULL |
| t_recepcion_compra_detalle_id_orden_compra_detalle_fkey | FK | FOREIGN KEY (id_orden_compra_detalle) REFERENCES obras.t_orden_compra_detalle(id_detalle) ON DELETE RESTRICT |
| t_recepcion_compra_detalle_id_recepcion_fkey | FK | FOREIGN KEY (id_recepcion) REFERENCES obras.t_recepcion_compra(id_recepcion) ON DELETE CASCADE |
| t_recepcion_compra_detalle_pkey | PK | PRIMARY KEY (id_recepcion_detalle) |


| ?ndice | Definici?n |
| --- | --- |
| idx_recepcion_detalle_oc_detalle | CREATE INDEX idx_recepcion_detalle_oc_detalle ON obras.t_recepcion_compra_detalle USING btree (id_orden_compra_detalle) |
| idx_recepcion_detalle_recepcion | CREATE INDEX idx_recepcion_detalle_recepcion ON obras.t_recepcion_compra_detalle USING btree (id_recepcion) |
| t_recepcion_compra_detalle_pkey | CREATE UNIQUE INDEX t_recepcion_compra_detalle_pkey ON obras.t_recepcion_compra_detalle USING btree (id_recepcion_detalle) |


### t_rol

Propietario: devpoppy. Sin id_empresa directo: revisar padre o condici?n de cat?logo global.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| id_rol | integer | NO | nextval('obras.t_rol_id_rol_seq'::regclass) |
| nombre_rol | character varying(80) | YES | ? |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| t_rol_pkey | PK | PRIMARY KEY (id_rol) |


| ?ndice | Definici?n |
| --- | --- |
| t_rol_pkey | CREATE UNIQUE INDEX t_rol_pkey ON obras.t_rol USING btree (id_rol) |


### t_rol_permiso

Propietario: devpoppy. Sin id_empresa directo: revisar padre o condici?n de cat?logo global.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| id_rol | integer | NO | ? |
| id_permiso | integer | NO | ? |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| t_rol_permiso_id_permiso_fkey | FK | FOREIGN KEY (id_permiso) REFERENCES obras.t_permiso(id_permiso) |
| t_rol_permiso_id_rol_fkey | FK | FOREIGN KEY (id_rol) REFERENCES obras.t_rol(id_rol) |
| t_rol_permiso_pkey | PK | PRIMARY KEY (id_rol, id_permiso) |


| ?ndice | Definici?n |
| --- | --- |
| idx_rol_permiso_id_permiso | CREATE INDEX idx_rol_permiso_id_permiso ON obras.t_rol_permiso USING btree (id_permiso) |
| t_rol_permiso_pkey | CREATE UNIQUE INDEX t_rol_permiso_pkey ON obras.t_rol_permiso USING btree (id_rol, id_permiso) |


### t_seguridad_usuario

Propietario: devpoppy. Sin id_empresa directo: revisar padre o condici?n de cat?logo global.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| id_usuario | integer | NO | ? |
| intentos_fallidos | integer | YES | 0 |
| bloqueado_hasta | timestamp without time zone | YES | ? |
| dispositivos_conocidos | _text | YES | '{}'::text[] |
| ultima_actualizacion | timestamp without time zone | YES | CURRENT_TIMESTAMP |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| t_seguridad_usuario_id_usuario_fkey | FK | FOREIGN KEY (id_usuario) REFERENCES obras.t_usuario(id_usuario) ON DELETE CASCADE |
| t_seguridad_usuario_pkey | PK | PRIMARY KEY (id_usuario) |


| ?ndice | Definici?n |
| --- | --- |
| t_seguridad_usuario_pkey | CREATE UNIQUE INDEX t_seguridad_usuario_pkey ON obras.t_seguridad_usuario USING btree (id_usuario) |


### t_tipo_obra

Propietario: devpoppy. Sin id_empresa directo: revisar padre o condici?n de cat?logo global.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| id_tipo_obra | integer | NO | nextval('obras.t_tipo_obra_id_tipo_obra_seq'::regclass) |
| nombre_obra | character varying(100) | YES | ? |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| t_tipo_obra_pkey | PK | PRIMARY KEY (id_tipo_obra) |


| ?ndice | Definici?n |
| --- | --- |
| t_tipo_obra_pkey | CREATE UNIQUE INDEX t_tipo_obra_pkey ON obras.t_tipo_obra USING btree (id_tipo_obra) |


### t_unidad_ambiente

Propietario: devpoppy. Sin id_empresa directo: revisar padre o condici?n de cat?logo global.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| id_ambiente | integer | NO | nextval('obras.t_unidad_ambiente_id_ambiente_seq'::regclass) |
| id_unidad | integer | NO | ? |
| nombre | character varying(100) | NO | ? |
| cantidad | integer | NO | 1 |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| chk_unidad_ambiente_cantidad | CHECK | CHECK ((cantidad > 0)) |
| fk_unidad_ambiente_unidad | FK | FOREIGN KEY (id_unidad) REFERENCES obras.t_unidad_construccion(id_unidad) ON DELETE CASCADE |
| t_unidad_ambiente_pkey | PK | PRIMARY KEY (id_ambiente) |


| ?ndice | Definici?n |
| --- | --- |
| idx_unidad_ambiente_unidad | CREATE INDEX idx_unidad_ambiente_unidad ON obras.t_unidad_ambiente USING btree (id_unidad) |
| t_unidad_ambiente_pkey | CREATE UNIQUE INDEX t_unidad_ambiente_pkey ON obras.t_unidad_ambiente USING btree (id_ambiente) |
| uq_unidad_ambiente_nombre | CREATE UNIQUE INDEX uq_unidad_ambiente_nombre ON obras.t_unidad_ambiente USING btree (id_unidad, lower((nombre)::text)) |


### t_unidad_caracteristica

Propietario: devpoppy. Sin id_empresa directo: revisar padre o condici?n de cat?logo global.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| id_caracteristica | integer | NO | nextval('obras.t_unidad_caracteristica_id_caracteristica_seq'::regclass) |
| id_unidad | integer | NO | ? |
| nombre | character varying(100) | NO | ? |
| valor | character varying(250) | NO | ? |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| fk_unidad_caracteristica_unidad | FK | FOREIGN KEY (id_unidad) REFERENCES obras.t_unidad_construccion(id_unidad) ON DELETE CASCADE |
| t_unidad_caracteristica_pkey | PK | PRIMARY KEY (id_caracteristica) |


| ?ndice | Definici?n |
| --- | --- |
| idx_unidad_caracteristica_unidad | CREATE INDEX idx_unidad_caracteristica_unidad ON obras.t_unidad_caracteristica USING btree (id_unidad) |
| t_unidad_caracteristica_pkey | CREATE UNIQUE INDEX t_unidad_caracteristica_pkey ON obras.t_unidad_caracteristica USING btree (id_caracteristica) |
| uq_unidad_caracteristica_nombre | CREATE UNIQUE INDEX uq_unidad_caracteristica_nombre ON obras.t_unidad_caracteristica USING btree (id_unidad, lower((nombre)::text)) |


### t_unidad_construccion

Propietario: devpoppy. Sin id_empresa directo: revisar padre o condici?n de cat?logo global.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| id_unidad | integer | NO | nextval('obras.t_unidad_construccion_id_unidad_seq'::regclass) |
| id_estructura | integer | NO | ? |
| codigo | character varying(20) | NO | obras.fn_generar_codigo_unidad() |
| tipo_unidad | character varying(30) | NO | 'OTRO'::character varying |
| superficie | numeric(12,2) | NO | 0 |
| cantidad_plantas | integer | NO | 0 |
| estado | character varying(30) | NO | 'PLANIFICADO'::character varying |
| id_modelo | integer | YES | ? |
| created_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |
| updated_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |
| especificacion_acabado | character varying(20) | NO | 'NORMAL'::character varying |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| chk_unidad_especificacion_acabado | CHECK | CHECK (((especificacion_acabado)::text = ANY ((ARRAY['NORMAL'::character varying, 'LUJO'::character varying])::text[]))) |
| chk_unidad_estado | CHECK | CHECK (((estado)::text = ANY ((ARRAY['PLANIFICADO'::character varying, 'EN_CONSTRUCCION'::character varying, 'FINALIZADO'::character varying, 'SUSPENDIDO'::character varying])::text[]))) |
| chk_unidad_plantas | CHECK | CHECK ((cantidad_plantas >= 0)) |
| chk_unidad_superficie | CHECK | CHECK ((superficie >= (0)::numeric)) |
| chk_unidad_tipo | CHECK | CHECK (((tipo_unidad)::text = ANY ((ARRAY['VIVIENDA'::character varying, 'DEPARTAMENTO'::character varying, 'LOCAL'::character varying, 'LOTE'::character varying, 'OFICINA'::character varying, 'OTRO'::character varying])::text[]))) |
| fk_unidad_estructura | FK | FOREIGN KEY (id_estructura) REFERENCES obras.t_estructura_obra(id_estructura) ON DELETE RESTRICT |
| fk_unidad_modelo | FK | FOREIGN KEY (id_modelo) REFERENCES obras.t_modelo_unidad(id_modelo) ON DELETE SET NULL |
| t_unidad_construccion_pkey | PK | PRIMARY KEY (id_unidad) |
| uq_unidad_codigo | UNIQUE | UNIQUE (codigo) |
| uq_unidad_estructura | UNIQUE | UNIQUE (id_estructura) |


| ?ndice | Definici?n |
| --- | --- |
| idx_unidad_modelo | CREATE INDEX idx_unidad_modelo ON obras.t_unidad_construccion USING btree (id_modelo) |
| t_unidad_construccion_pkey | CREATE UNIQUE INDEX t_unidad_construccion_pkey ON obras.t_unidad_construccion USING btree (id_unidad) |
| uq_unidad_codigo | CREATE UNIQUE INDEX uq_unidad_codigo ON obras.t_unidad_construccion USING btree (codigo) |
| uq_unidad_estructura | CREATE UNIQUE INDEX uq_unidad_estructura ON obras.t_unidad_construccion USING btree (id_estructura) |


### t_unidad_material

Propietario: devpoppy. Sin id_empresa directo: revisar padre o condici?n de cat?logo global.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| id_unidad_material | integer | NO | nextval('obras.t_unidad_material_id_unidad_material_seq'::regclass) |
| id_unidad | integer | NO | ? |
| id_material | integer | NO | ? |
| cantidad | numeric(14,3) | NO | 1 |
| unidad_medida | character varying(30) | YES | ? |
| uso_ubicacion | character varying(150) | YES | ? |
| acabado | character varying(150) | YES | ? |
| observacion | text | YES | ? |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| chk_unidad_material_cantidad | CHECK | CHECK ((cantidad > (0)::numeric)) |
| fk_unidad_material_material | FK | FOREIGN KEY (id_material) REFERENCES obras.t_material(id_material) ON DELETE RESTRICT |
| fk_unidad_material_unidad | FK | FOREIGN KEY (id_unidad) REFERENCES obras.t_unidad_construccion(id_unidad) ON DELETE CASCADE |
| t_unidad_material_pkey | PK | PRIMARY KEY (id_unidad_material) |
| uq_unidad_material_uso | UNIQUE | UNIQUE (id_unidad, id_material, uso_ubicacion) |


| ?ndice | Definici?n |
| --- | --- |
| idx_unidad_material_material | CREATE INDEX idx_unidad_material_material ON obras.t_unidad_material USING btree (id_material) |
| idx_unidad_material_unidad | CREATE INDEX idx_unidad_material_unidad ON obras.t_unidad_material USING btree (id_unidad) |
| t_unidad_material_pkey | CREATE UNIQUE INDEX t_unidad_material_pkey ON obras.t_unidad_material USING btree (id_unidad_material) |
| uq_unidad_material_uso | CREATE UNIQUE INDEX uq_unidad_material_uso ON obras.t_unidad_material USING btree (id_unidad, id_material, uso_ubicacion) |


### t_unidad_medida

Propietario: devpoppy. Sin id_empresa directo: revisar padre o condici?n de cat?logo global.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| id_unidad_medida | integer | NO | nextval('obras.t_unidad_medida_id_unidad_medida_seq'::regclass) |
| nombre | character varying(100) | NO | ? |
| abreviatura | character varying(20) | NO | ? |
| estado | character varying(10) | NO | 'ACTIVO'::character varying |
| created_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |
| updated_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |
| tipo | character varying(20) | NO | 'INSUMO'::character varying |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| chk_unidad_medida_abreviatura | CHECK | CHECK ((btrim((abreviatura)::text) <> ''::text)) |
| chk_unidad_medida_estado | CHECK | CHECK (((estado)::text = ANY ((ARRAY['ACTIVO'::character varying, 'INACTIVO'::character varying])::text[]))) |
| chk_unidad_medida_nombre | CHECK | CHECK ((btrim((nombre)::text) <> ''::text)) |
| chk_unidad_medida_tipo_apu | CHECK | CHECK (((tipo)::text = ANY ((ARRAY['GEOMETRICA'::character varying, 'INSUMO'::character varying, 'CONCEPTUAL'::character varying])::text[]))) |
| t_unidad_medida_pkey | PK | PRIMARY KEY (id_unidad_medida) |


| ?ndice | Definici?n |
| --- | --- |
| t_unidad_medida_pkey | CREATE UNIQUE INDEX t_unidad_medida_pkey ON obras.t_unidad_medida USING btree (id_unidad_medida) |
| uq_unidad_medida_abreviatura_activo | CREATE UNIQUE INDEX uq_unidad_medida_abreviatura_activo ON obras.t_unidad_medida USING btree (lower(btrim((abreviatura)::text))) WHERE ((estado)::text = 'ACTIVO'::text) |
| uq_unidad_medida_nombre_activo | CREATE UNIQUE INDEX uq_unidad_medida_nombre_activo ON obras.t_unidad_medida USING btree (lower(btrim((nombre)::text))) WHERE ((estado)::text = 'ACTIVO'::text) |


### t_unidad_personalizacion

Propietario: devpoppy. Sin id_empresa directo: revisar padre o condici?n de cat?logo global.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| id_personalizacion | integer | NO | nextval('obras.t_unidad_personalizacion_id_personalizacion_seq'::regclass) |
| id_unidad | integer | NO | ? |
| tipo | character varying(50) | NO | ? |
| descripcion | text | NO | ? |
| created_at | timestamp with time zone | NO | CURRENT_TIMESTAMP |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| fk_unidad_personalizacion_unidad | FK | FOREIGN KEY (id_unidad) REFERENCES obras.t_unidad_construccion(id_unidad) ON DELETE CASCADE |
| t_unidad_personalizacion_pkey | PK | PRIMARY KEY (id_personalizacion) |


| ?ndice | Definici?n |
| --- | --- |
| idx_unidad_personalizacion_unidad | CREATE INDEX idx_unidad_personalizacion_unidad ON obras.t_unidad_personalizacion USING btree (id_unidad) |
| t_unidad_personalizacion_pkey | CREATE UNIQUE INDEX t_unidad_personalizacion_pkey ON obras.t_unidad_personalizacion USING btree (id_personalizacion) |


### t_unidad_seguimiento

Propietario: devpoppy. Sin id_empresa directo: revisar padre o condici?n de cat?logo global.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| id_seguimiento | integer | NO | nextval('obras.t_unidad_seguimiento_id_seguimiento_seq'::regclass) |
| id_unidad | integer | NO | ? |
| estado_anterior | character varying(30) | YES | ? |
| estado_nuevo | character varying(30) | NO | ? |
| id_usuario | integer | YES | ? |
| observacion | text | YES | ? |
| fecha | timestamp with time zone | NO | CURRENT_TIMESTAMP |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| chk_seguimiento_estado_anterior | CHECK | CHECK (((estado_anterior IS NULL) OR ((estado_anterior)::text = ANY ((ARRAY['PLANIFICADO'::character varying, 'EN_CONSTRUCCION'::character varying, 'FINALIZADO'::character varying, 'SUSPENDIDO'::character varying])::text[])))) |
| chk_seguimiento_estado_nuevo | CHECK | CHECK (((estado_nuevo)::text = ANY ((ARRAY['PLANIFICADO'::character varying, 'EN_CONSTRUCCION'::character varying, 'FINALIZADO'::character varying, 'SUSPENDIDO'::character varying])::text[]))) |
| fk_unidad_seguimiento_unidad | FK | FOREIGN KEY (id_unidad) REFERENCES obras.t_unidad_construccion(id_unidad) ON DELETE CASCADE |
| fk_unidad_seguimiento_usuario | FK | FOREIGN KEY (id_usuario) REFERENCES obras.t_usuario(id_usuario) ON DELETE SET NULL |
| t_unidad_seguimiento_pkey | PK | PRIMARY KEY (id_seguimiento) |


| ?ndice | Definici?n |
| --- | --- |
| idx_unidad_seguimiento_unidad_fecha | CREATE INDEX idx_unidad_seguimiento_unidad_fecha ON obras.t_unidad_seguimiento USING btree (id_unidad, fecha DESC) |
| t_unidad_seguimiento_pkey | CREATE UNIQUE INDEX t_unidad_seguimiento_pkey ON obras.t_unidad_seguimiento USING btree (id_seguimiento) |


### t_usuario

Propietario: devpoppy. Contiene id_empresa.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| id_usuario | integer | NO | nextval('obras.t_usuario_id_usuario_seq'::regclass) |
| username | character varying(80) | YES | ? |
| password | character varying(255) | YES | ? |
| correo | character varying(150) | YES | ? |
| id_empresa | integer | NO | ? |
| id_persona | integer | YES | ? |
| id_rol | integer | YES | ? |
| estado | character varying(50) | YES | 'ACTIVO'::character varying |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| t_usuario_id_empresa_fkey | FK | FOREIGN KEY (id_empresa) REFERENCES obras.t_empresa(id_empresa) |
| t_usuario_id_persona_fkey | FK | FOREIGN KEY (id_persona) REFERENCES obras.t_persona(id_persona) |
| t_usuario_id_rol_fkey | FK | FOREIGN KEY (id_rol) REFERENCES obras.t_rol(id_rol) |
| t_usuario_pkey | PK | PRIMARY KEY (id_usuario) |


| ?ndice | Definici?n |
| --- | --- |
| idx_usuario_id_empresa | CREATE INDEX idx_usuario_id_empresa ON obras.t_usuario USING btree (id_empresa) |
| idx_usuario_id_persona | CREATE INDEX idx_usuario_id_persona ON obras.t_usuario USING btree (id_persona) |
| idx_usuario_id_rol | CREATE INDEX idx_usuario_id_rol ON obras.t_usuario USING btree (id_rol) |
| t_usuario_pkey | CREATE UNIQUE INDEX t_usuario_pkey ON obras.t_usuario USING btree (id_usuario) |


### t_usuario_orden_trabajo_permiso

Propietario: devpoppy. Sin id_empresa directo: revisar padre o condici?n de cat?logo global.

| Columna | Tipo | Admite NULL | Default / generaci?n |
| --- | --- | --- | --- |
| id_orden_trabajo_permiso | bigint | NO | ? |
| id_usuario | bigint | NO | ? |
| id_orden_trabajo | bigint | NO | ? |


| Restricci?n | Tipo | Definici?n |
| --- | --- | --- |
| t_usario_orden_trabajo_permiso_id_orden_trabajo_fkey | FK | FOREIGN KEY (id_orden_trabajo) REFERENCES obras.t_orden_trabajo(orden_nro) ON UPDATE CASCADE ON DELETE CASCADE |
| t_usario_orden_trabajo_permiso_id_orden_trabajo_permiso_fkey | FK | FOREIGN KEY (id_orden_trabajo_permiso) REFERENCES obras.t_orden_trabajo_permiso(id_permiso_orden_trabajo) ON UPDATE CASCADE ON DELETE CASCADE |
| t_usario_orden_trabajo_permiso_id_usuario_fkey | FK | FOREIGN KEY (id_usuario) REFERENCES obras.t_usuario(id_usuario) ON UPDATE CASCADE ON DELETE CASCADE |


| ?ndice | Definici?n |
| --- | --- |


## Triggers

| Tabla | Trigger | Estado | Definici?n |
| --- | --- | --- | --- |
| t_analisi_precio_unitario_insumo | tg_apu_insumo_updated_at | O | CREATE TRIGGER tg_apu_insumo_updated_at BEFORE UPDATE ON obras.t_analisi_precio_unitario_insumo FOR EACH ROW EXECUTE FUNCTION obras.fn_actualizar_updated_at_estimacion_apu() |
| t_analisi_precio_unitario_insumo | tg_recalcular_apu_materiales | O | CREATE TRIGGER tg_recalcular_apu_materiales AFTER INSERT OR DELETE OR UPDATE ON obras.t_analisi_precio_unitario_insumo FOR EACH ROW EXECUTE FUNCTION obras.fn_recalcular_apu_materiales() |
| t_analisis_precio_unitario | tg_apu_updated_at | O | CREATE TRIGGER tg_apu_updated_at BEFORE UPDATE ON obras.t_analisis_precio_unitario FOR EACH ROW EXECUTE FUNCTION obras.fn_actualizar_updated_at_estimacion_apu() |
| t_analisis_precio_unitario | tg_sync_apu_precio | O | CREATE TRIGGER tg_sync_apu_precio BEFORE INSERT OR UPDATE OF codigo, id_empresa, costo_materiales, mano_de_obra, porcentaje_utilidad ON obras.t_analisis_precio_unitario FOR EACH ROW EXECUTE FUNCTION obras.fn_sync_apu_precio() |
| t_categoria_material | tg_cu14_actualizar_categoria_material | O | CREATE TRIGGER tg_cu14_actualizar_categoria_material BEFORE UPDATE ON obras.t_categoria_material FOR EACH ROW EXECUTE FUNCTION obras.fn_actualizar_updated_at_cu14() |
| t_control_costo_obra | tg_cu17_control_updated_at | O | CREATE TRIGGER tg_cu17_control_updated_at BEFORE UPDATE ON obras.t_control_costo_obra FOR EACH ROW EXECUTE FUNCTION obras.fn_cu17_actualizar_updated_at() |
| t_control_costo_obra | tg_cu17_linea_base_identidad_inmutable | O | CREATE TRIGGER tg_cu17_linea_base_identidad_inmutable BEFORE UPDATE OF id_empresa, id_obra, id_estimacion_base ON obras.t_control_costo_obra FOR EACH ROW EXECUTE FUNCTION obras.fn_cu17_linea_base_identidad_inmutable() |
| t_control_costo_obra | tg_cu17_validar_linea_base | O | CREATE TRIGGER tg_cu17_validar_linea_base BEFORE INSERT OR UPDATE OF id_empresa, id_obra, id_estimacion_base ON obras.t_control_costo_obra FOR EACH ROW EXECUTE FUNCTION obras.fn_cu17_validar_linea_base() |
| t_costo_ejecutado | tg_cu17_costo_updated_at | O | CREATE TRIGGER tg_cu17_costo_updated_at BEFORE UPDATE ON obras.t_costo_ejecutado FOR EACH ROW EXECUTE FUNCTION obras.fn_cu17_actualizar_updated_at() |
| t_costo_ejecutado | tg_cu17_impedir_borrado_costo | O | CREATE TRIGGER tg_cu17_impedir_borrado_costo BEFORE DELETE ON obras.t_costo_ejecutado FOR EACH ROW EXECUTE FUNCTION obras.fn_cu17_impedir_borrado_costo() |
| t_costo_ejecutado | tg_cu17_validar_costo | O | CREATE TRIGGER tg_cu17_validar_costo BEFORE INSERT OR UPDATE OF id_control_costo, id_empresa, id_obra, id_partida_presupuestaria ON obras.t_costo_ejecutado FOR EACH ROW EXECUTE FUNCTION obras.fn_cu17_validar_costo() |
| t_crm_cliente | tg_crm_actualizar_cliente | O | CREATE TRIGGER tg_crm_actualizar_cliente BEFORE UPDATE ON obras.t_crm_cliente FOR EACH ROW EXECUTE FUNCTION obras.fn_actualizar_updated_at() |
| t_crm_cliente_unidad | tg_crm_actualizar_cliente_unidad | O | CREATE TRIGGER tg_crm_actualizar_cliente_unidad BEFORE UPDATE ON obras.t_crm_cliente_unidad FOR EACH ROW EXECUTE FUNCTION obras.fn_actualizar_updated_at() |
| t_estimacion | tg_estimacion_updated_at | O | CREATE TRIGGER tg_estimacion_updated_at BEFORE UPDATE ON obras.t_estimacion FOR EACH ROW EXECUTE FUNCTION obras.fn_actualizar_updated_at_estimacion_apu() |
| t_estimacion_analisis_precio_unitario | tg_recalcular_monto_estimacion | O | CREATE TRIGGER tg_recalcular_monto_estimacion AFTER INSERT OR DELETE OR UPDATE ON obras.t_estimacion_analisis_precio_unitario FOR EACH ROW EXECUTE FUNCTION obras.fn_recalcular_monto_estimacion() |
| t_estimacion_analisis_precio_unitario | tg_snapshot_precio_partida | O | CREATE TRIGGER tg_snapshot_precio_partida BEFORE INSERT OR UPDATE OF precio_unitario, costo_directo_unitario, item_codigo, orden ON obras.t_estimacion_analisis_precio_unitario FOR EACH ROW EXECUTE FUNCTION obras.fn_snapshot_precio_partida() |
| t_estructura_obra | tg_actualizar_updated_at_estructura | O | CREATE TRIGGER tg_actualizar_updated_at_estructura BEFORE UPDATE ON obras.t_estructura_obra FOR EACH ROW EXECUTE FUNCTION obras.fn_actualizar_updated_at_estructura() |
| t_estructura_obra | tg_proteger_unidades_estructura | O | CREATE TRIGGER tg_proteger_unidades_estructura BEFORE DELETE ON obras.t_estructura_obra FOR EACH ROW EXECUTE FUNCTION obras.fn_proteger_unidades_estructura() |
| t_incidencia | tg_cu19_actualizar_incidencia | O | CREATE TRIGGER tg_cu19_actualizar_incidencia BEFORE UPDATE ON obras.t_incidencia FOR EACH ROW EXECUTE FUNCTION obras.fn_actualizar_updated_at_cu19() |
| t_incidencia_orden_trabajo | tg_cu19_validar_incidencia_ot | O | CREATE TRIGGER tg_cu19_validar_incidencia_ot BEFORE INSERT OR UPDATE ON obras.t_incidencia_orden_trabajo FOR EACH ROW EXECUTE FUNCTION obras.fn_validar_incidencia_ot_cu19() |
| t_mano_obra | tg_mano_obra_updated_at | O | CREATE TRIGGER tg_mano_obra_updated_at BEFORE UPDATE ON obras.t_mano_obra FOR EACH ROW EXECUTE FUNCTION obras.fn_actualizar_updated_at_estimacion_apu() |
| t_material | tg_cu14_actualizar_material | O | CREATE TRIGGER tg_cu14_actualizar_material BEFORE UPDATE ON obras.t_material FOR EACH ROW EXECUTE FUNCTION obras.fn_actualizar_updated_at_cu14() |
| t_material | tg_material_updated_at | O | CREATE TRIGGER tg_material_updated_at BEFORE UPDATE ON obras.t_material FOR EACH ROW EXECUTE FUNCTION obras.fn_material_updated_at() |
| t_material_base | tg_material_base_updated_at | O | CREATE TRIGGER tg_material_base_updated_at BEFORE UPDATE ON obras.t_material_base FOR EACH ROW EXECUTE FUNCTION obras.fn_material_updated_at() |
| t_modelo_unidad | tg_actualizar_modelo_unidad | O | CREATE TRIGGER tg_actualizar_modelo_unidad BEFORE UPDATE ON obras.t_modelo_unidad FOR EACH ROW EXECUTE FUNCTION obras.fn_actualizar_updated_at_cu12() |
| t_obra | tg_actualizar_updated_at | O | CREATE TRIGGER tg_actualizar_updated_at BEFORE UPDATE ON obras.t_obra FOR EACH ROW EXECUTE FUNCTION obras.fn_actualizar_updated_at() |
| t_orden_cambio | tg_cu17_orden_solo_pendiente | O | CREATE TRIGGER tg_cu17_orden_solo_pendiente BEFORE UPDATE ON obras.t_orden_cambio FOR EACH ROW EXECUTE FUNCTION obras.fn_cu17_orden_solo_pendiente() |
| t_orden_cambio | tg_cu17_orden_updated_at | O | CREATE TRIGGER tg_cu17_orden_updated_at BEFORE UPDATE ON obras.t_orden_cambio FOR EACH ROW EXECUTE FUNCTION obras.fn_cu17_actualizar_updated_at() |
| t_orden_cambio | tg_cu17_validar_orden | O | CREATE TRIGGER tg_cu17_validar_orden BEFORE INSERT OR UPDATE OF id_control_costo, id_empresa, id_obra, id_estimacion_base ON obras.t_orden_cambio FOR EACH ROW EXECUTE FUNCTION obras.fn_cu17_validar_orden() |
| t_orden_cambio_detalle | tg_cu17_detalle_solo_pendiente | O | CREATE TRIGGER tg_cu17_detalle_solo_pendiente BEFORE INSERT OR DELETE OR UPDATE ON obras.t_orden_cambio_detalle FOR EACH ROW EXECUTE FUNCTION obras.fn_cu17_detalle_solo_pendiente() |
| t_orden_cambio_detalle | tg_cu17_validar_detalle_orden | O | CREATE TRIGGER tg_cu17_validar_detalle_orden BEFORE INSERT OR UPDATE ON obras.t_orden_cambio_detalle FOR EACH ROW EXECUTE FUNCTION obras.fn_cu17_validar_detalle_orden() |
| t_orden_cambio_historial | tg_cu17_historial_append_only | O | CREATE TRIGGER tg_cu17_historial_append_only BEFORE DELETE OR UPDATE ON obras.t_orden_cambio_historial FOR EACH ROW EXECUTE FUNCTION obras.fn_cu17_historial_append_only() |
| t_orden_compra | tg_orden_compra_updated_at | O | CREATE TRIGGER tg_orden_compra_updated_at BEFORE UPDATE ON obras.t_orden_compra FOR EACH ROW EXECUTE FUNCTION obras.fn_orden_compra_updated_at() |
| t_partida_presupuesto | tg_partida_actualizar | O | CREATE TRIGGER tg_partida_actualizar BEFORE UPDATE ON obras.t_partida_presupuesto FOR EACH ROW EXECUTE FUNCTION obras.fn_actualizar_updated_at() |
| t_presupuesto | tg_presupuesto_actualizar | O | CREATE TRIGGER tg_presupuesto_actualizar BEFORE UPDATE ON obras.t_presupuesto FOR EACH ROW EXECUTE FUNCTION obras.fn_actualizar_updated_at() |
| t_proveedor | tg_cu15_actualizar_proveedor | O | CREATE TRIGGER tg_cu15_actualizar_proveedor BEFORE UPDATE ON obras.t_proveedor FOR EACH ROW EXECUTE FUNCTION obras.fn_actualizar_updated_at_cu15() |
| t_unidad_construccion | tg_actualizar_unidad_construccion | O | CREATE TRIGGER tg_actualizar_unidad_construccion BEFORE UPDATE ON obras.t_unidad_construccion FOR EACH ROW EXECUTE FUNCTION obras.fn_actualizar_updated_at_cu12() |
| t_unidad_medida | tg_cu14_actualizar_unidad_medida | O | CREATE TRIGGER tg_cu14_actualizar_unidad_medida BEFORE UPDATE ON obras.t_unidad_medida FOR EACH ROW EXECUTE FUNCTION obras.fn_actualizar_updated_at_cu14() |


O significa habilitado para ejecuci?n ordinaria. Se excluyen triggers internos de FK.

## Secuencias

| Secuencia | Tipo | Inicio | Incremento | C?clica |
| --- | --- | --- | --- | --- |
| notificacion_id_notificacion_seq | integer | 1 | 1 | False |
| seq_apu_codigo | bigint | 1 | 1 | False |
| seq_codigo_unidad | bigint | 1 | 1 | False |
| t_analisi_precio_unitario_ins_id_analisis_precio_unitario_i_seq | integer | 1 | 1 | False |
| t_analisis_precio_unitario_id_analisis_precio_unitario_seq | integer | 1 | 1 | False |
| t_apu_detalle_mano_obra_archivo_id_archivo_seq | bigint | 1 | 1 | False |
| t_apu_legacy_archive_id_archivo_seq | bigint | 1 | 1 | False |
| t_avance_obra_id_avance_seq | integer | 1 | 1 | False |
| t_bitacora_id_bitacora_seq | integer | 1 | 1 | False |
| t_categoria_material_id_categoria_seq | integer | 1 | 1 | False |
| t_control_costo_obra_id_control_costo_seq | bigint | 1 | 1 | False |
| t_costo_ejecutado_id_costo_ejecutado_seq | bigint | 1 | 1 | False |
| t_costo_ejecutado_legacy_id_costo_ejecutado_seq | integer | 1 | 1 | False |
| t_crm_cliente_id_cliente_seq | integer | 1 | 1 | False |
| t_crm_cliente_unidad_id_cliente_unidad_seq | integer | 1 | 1 | False |
| t_crm_interaccion_id_interaccion_seq | integer | 1 | 1 | False |
| t_detalle_obra_id_detalle_seq | integer | 1 | 1 | False |
| t_empresa_id_empresa_seq | integer | 1 | 1 | False |
| t_equipo_id_equipo_seq | integer | 1 | 1 | False |
| t_equipo_maquinaria_id_equipo_maquinaria_seq | integer | 1 | 1 | False |
| t_equipo_maquinaria_obra_id_asignacion_seq | integer | 1 | 1 | False |
| t_estimacion_analisis_precio__id_estimacion_analisis_precio_seq | integer | 1 | 1 | False |
| t_estimacion_id_estimacion_seq | integer | 1 | 1 | False |
| t_estructura_obra_id_estructura_seq | integer | 1 | 1 | False |
| t_incidencia_evidencia_id_evidencia_seq | integer | 1 | 1 | False |
| t_incidencia_id_incidencia_seq | integer | 1 | 1 | False |
| t_incidencia_seguimiento_id_seguimiento_seq | integer | 1 | 1 | False |
| t_mano_obra_id_mano_obra_seq | integer | 1 | 1 | False |
| t_material_base_id_material_base_seq | integer | 1 | 1 | False |
| t_material_caracteristica_id_caracteristica_seq | integer | 1 | 1 | False |
| t_material_id_material_seq | integer | 1 | 1 | False |
| t_materiales_almacen_id_lote_seq | integer | 1 | 1 | False |
| t_modelo_caracteristica_id_modelo_caracteristica_seq | integer | 1 | 1 | False |
| t_modelo_unidad_id_modelo_seq | integer | 1 | 1 | False |
| t_modulo_id_modulo_seq | integer | 1 | 1 | False |
| t_movimiento_almacen_id_movimiento_seq | integer | 1 | 1 | False |
| t_obra_estimacion_id_estimacion_seq | integer | 1 | 1 | False |
| t_obra_id_obra_seq | integer | 1 | 1 | False |
| t_orden_cambio_detalle_id_orden_cambio_detalle_seq | bigint | 1 | 1 | False |
| t_orden_cambio_historial_id_orden_cambio_historial_seq | bigint | 1 | 1 | False |
| t_orden_cambio_id_orden_cambio_seq | bigint | 1 | 1 | False |
| t_orden_compra_detalle_id_detalle_seq | integer | 1 | 1 | False |
| t_orden_compra_id_orden_compra_seq | integer | 1 | 1 | False |
| t_orden_trabajo_orden_nro_seq | integer | 1 | 1 | False |
| t_orden_trabajo_permiso_id_permiso_orden_trabajo_seq | integer | 1 | 1 | False |
| t_parametro_estimacion_id_parametro_seq | integer | 1 | 1 | False |
| t_partida_presupuesto_id_partida_seq | integer | 1 | 1 | False |
| t_permiso_id_permiso_seq | integer | 1 | 1 | False |
| t_persona_id_persona_seq | integer | 1 | 1 | False |
| t_presupuesto_id_presupuesto_seq | integer | 1 | 1 | False |
| t_proveedor_id_proveedor_seq | integer | 1 | 1 | False |
| t_proveedor_material_id_proveedor_material_seq | integer | 1 | 1 | False |
| t_recepcion_compra_detalle_id_recepcion_detalle_seq | integer | 1 | 1 | False |
| t_recepcion_compra_id_recepcion_seq | integer | 1 | 1 | False |
| t_rol_id_rol_seq | integer | 1 | 1 | False |
| t_tipo_obra_id_tipo_obra_seq | integer | 1 | 1 | False |
| t_unidad_ambiente_id_ambiente_seq | integer | 1 | 1 | False |
| t_unidad_caracteristica_id_caracteristica_seq | integer | 1 | 1 | False |
| t_unidad_construccion_id_unidad_seq | integer | 1 | 1 | False |
| t_unidad_material_id_unidad_material_seq | integer | 1 | 1 | False |
| t_unidad_medida_id_unidad_medida_seq | integer | 1 | 1 | False |
| t_unidad_personalizacion_id_personalizacion_seq | integer | 1 | 1 | False |
| t_unidad_seguimiento_id_seguimiento_seq | integer | 1 | 1 | False |
| t_usuario_id_usuario_seq | integer | 1 | 1 | False |


## Validez estructural

Las 316 restricciones est?n validadas y no son diferibles; los 177 ?ndices son v?lidos y est?n listos. No hay enums ni domains propios. No se midi? rendimiento ni se validaron datos hist?ricos contra reglas externas.
