# Rutinas verificadas de PostgreSQL / esquema obras

Inspecci?n: 2026-10-04. Incluye las 73 funciones y el procedimiento real le?dos con pg_get_functiondef, sin ejecutarlos. Las 25 funciones de trigger est?n incluidas entre las funciones.

An?lisis: [ARQUITECTURA_BASE_DATOS.md](ARQUITECTURA_BASE_DATOS.md). Tablas: [BASE_DATOS_INVENTARIO.md](BASE_DATOS_INVENTARIO.md).

Todas son SECURITY INVOKER. Referencias de archivos son coincidencias textuales de nombre: no demuestran uso, equivalencia del cuerpo ni migraciones aplicadas.

| Rutina | Tipo | Argumentos de identidad | Retorno |
| --- | --- | --- | --- |
| fn_actualizar_estructura_obra | FUNCTION | p_id_estructura integer, p_id_obra integer, p_nombre character varying, p_tipo character varying, p_descripcion text, p_orden integer, p_id_empresa integer | json |
| fn_actualizar_unidad_construccion | FUNCTION | p_id_obra integer, p_id_unidad integer, p_id_empresa integer, p_nombre character varying, p_descripcion text, p_tipo_unidad character varying, p_superficie numeric, p_cantidad_plantas integer, p_id_modelo integer, p_ambientes json, p_caracteristicas json | json |
| fn_actualizar_updated_at | FUNCTION |  | trigger |
| fn_actualizar_updated_at_cu12 | FUNCTION |  | trigger |
| fn_actualizar_updated_at_cu14 | FUNCTION |  | trigger |
| fn_actualizar_updated_at_cu15 | FUNCTION |  | trigger |
| fn_actualizar_updated_at_cu19 | FUNCTION |  | trigger |
| fn_actualizar_updated_at_estimacion_apu | FUNCTION |  | trigger |
| fn_actualizar_updated_at_estructura | FUNCTION |  | trigger |
| fn_aprobar_rechazar_orden_compra | FUNCTION | p_id_empresa integer, p_id_orden_compra integer, p_id_usuario integer, p_aprobar boolean, p_observacion text | boolean |
| fn_calcular_analisis_precio_unitario | FUNCTION | p_id_analisis_precio_unitario integer, p_id_empresa integer | json |
| fn_calcular_estimacion | FUNCTION | p_id_estimacion integer, p_id_empresa integer | json |
| fn_cambiar_estado_orden_compra | FUNCTION | p_id_empresa integer, p_id_orden_compra integer, p_nuevo_estado character varying | boolean |
| fn_cambiar_estado_unidad | FUNCTION | p_id_obra integer, p_id_unidad integer, p_id_empresa integer, p_estado_nuevo character varying, p_id_usuario integer, p_observacion text | json |
| fn_consultar_material | FUNCTION | p_id_empresa integer, p_id_material integer | TABLE(id_material integer, codigo character varying, nombre_material character varying, descripcion text, id_categoria integer, categoria_nombre character varying, id_unidad_medida integer, unidad_nombre character varying, unidad_abreviatura character varying, precio numeric, estado character varying, id_empresa integer, nombre_empresa character varying, id_material_base integer, es_propio boolean, created_at timestamp with time zone, updated_at timestamp with time zone) |
| fn_consultar_orden_compra | FUNCTION | p_id_empresa integer, p_id_orden_compra integer | TABLE(id_orden_compra integer, numero_orden character varying, fecha date, observaciones text, estado character varying, id_empresa integer, nombre_empresa character varying, id_proveedor integer, nombre_proveedor character varying, nit_proveedor character varying, id_usuario_solicitante integer, nombre_solicitante character varying, subtotal numeric, total numeric, id_usuario_aprobacion integer, nombre_aprobador character varying, fecha_aprobacion timestamp with time zone, observacion_aprobacion text, created_at timestamp with time zone, updated_at timestamp with time zone) |
| fn_copiar_catalogo_base_empresa | FUNCTION | p_id_empresa integer | integer |
| fn_cu17_actualizar_updated_at | FUNCTION |  | trigger |
| fn_cu17_detalle_solo_pendiente | FUNCTION |  | trigger |
| fn_cu17_historial_append_only | FUNCTION |  | trigger |
| fn_cu17_impedir_borrado_costo | FUNCTION |  | trigger |
| fn_cu17_linea_base_identidad_inmutable | FUNCTION |  | trigger |
| fn_cu17_orden_solo_pendiente | FUNCTION |  | trigger |
| fn_cu17_validar_costo | FUNCTION |  | trigger |
| fn_cu17_validar_detalle_orden | FUNCTION |  | trigger |
| fn_cu17_validar_linea_base | FUNCTION |  | trigger |
| fn_cu17_validar_orden | FUNCTION |  | trigger |
| fn_desactivar_material | FUNCTION | p_id_empresa integer, p_id_material integer, p_nuevo_estado character varying | boolean |
| fn_eliminar_avance_obra | FUNCTION | p_id_avance integer, p_id_obra integer, p_id_empresa integer | json |
| fn_eliminar_estructura_obra | FUNCTION | p_id_estructura integer, p_id_obra integer, p_id_empresa integer | json |
| fn_eliminar_unidad_construccion | FUNCTION | p_id_obra integer, p_id_unidad integer, p_id_empresa integer | json |
| fn_generar_codigo_unidad | FUNCTION |  | character varying |
| fn_generar_numero_orden_compra | FUNCTION | p_id_empresa integer | character varying |
| fn_generar_numero_recepcion | FUNCTION | p_id_empresa integer | character varying |
| fn_listar_avances_obra | FUNCTION | p_id_obra integer, p_id_empresa integer, p_estado character varying | json |
| fn_listar_avances_obra | FUNCTION | p_id_obra integer, p_id_empresa integer, p_id_unidad integer | json |
| fn_listar_detalles_orden_compra | FUNCTION | p_id_orden_compra integer | TABLE(id_detalle integer, id_material integer, codigo_material character varying, nombre_material character varying, unidad_abreviatura character varying, cantidad_solicitada numeric, precio_unitario numeric, subtotal numeric, cantidad_recibida numeric, cantidad_pendiente numeric) |
| fn_listar_estructura_obra | FUNCTION | p_id_obra integer, p_id_empresa integer | json |
| fn_listar_inventario_empresa | FUNCTION | p_id_empresa integer, p_id_categoria integer, p_estado_stock character varying, p_q character varying, p_limit integer, p_offset integer | TABLE(id_material integer, codigo character varying, nombre_material character varying, descripcion text, id_categoria integer, categoria_nombre character varying, id_unidad_medida integer, unidad_nombre character varying, unidad_abreviatura character varying, precio numeric, stock_actual numeric, stock_minimo numeric, valor_total numeric, estado_stock character varying, id_empresa integer, nombre_empresa character varying, total_count bigint) |
| fn_listar_materiales_empresa | FUNCTION | p_id_empresa integer, p_q character varying, p_id_categoria integer, p_estado character varying, p_limit integer, p_offset integer | TABLE(id_material integer, codigo character varying, nombre_material character varying, descripcion text, id_categoria integer, categoria_nombre character varying, id_unidad_medida integer, unidad_nombre character varying, unidad_abreviatura character varying, precio numeric, estado character varying, id_empresa integer, nombre_empresa character varying, id_material_base integer, es_propio boolean, created_at timestamp with time zone, updated_at timestamp with time zone, total_count bigint) |
| fn_listar_movimientos_almacen | FUNCTION | p_id_empresa integer, p_id_material integer, p_tipo_movimiento character varying, p_limit integer, p_offset integer | TABLE(id_movimiento integer, fecha_movimiento date, created_at timestamp with time zone, tipo_movimiento character varying, cantidad_asignada numeric, id_material integer, material_codigo character varying, material_nombre character varying, unidad_abreviatura character varying, id_orden_compra integer, numero_orden character varying, id_recepcion integer, numero_recepcion character varying, id_usuario integer, nombre_usuario character varying, observaciones text, total_count bigint) |
| fn_listar_ordenes_compra | FUNCTION | p_id_empresa integer, p_q character varying, p_estado character varying, p_id_proveedor integer, p_limit integer, p_offset integer | TABLE(id_orden_compra integer, numero_orden character varying, fecha date, observaciones text, estado character varying, id_empresa integer, nombre_empresa character varying, id_proveedor integer, nombre_proveedor character varying, id_usuario_solicitante integer, nombre_solicitante character varying, subtotal numeric, total numeric, items_count bigint, items_recibidos_count bigint, created_at timestamp with time zone, updated_at timestamp with time zone, total_count bigint) |
| fn_listar_recepciones_orden | FUNCTION | p_id_orden_compra integer | TABLE(id_recepcion integer, numero_recepcion character varying, fecha_recepcion timestamp with time zone, id_usuario_recepcion integer, nombre_usuario_recepcion character varying, observaciones text, total_items_recibidos bigint) |
| fn_material_updated_at | FUNCTION |  | trigger |
| fn_modificar_material | FUNCTION | p_id_empresa integer, p_id_material integer, p_codigo character varying, p_nombre_material character varying, p_descripcion text, p_id_categoria integer, p_id_unidad_medida integer, p_precio numeric | boolean |
| fn_orden_compra_updated_at | FUNCTION |  | trigger |
| fn_proteger_unidades_estructura | FUNCTION |  | trigger |
| fn_recalcular_apu_materiales | FUNCTION |  | trigger |
| fn_recalcular_monto_estimacion | FUNCTION |  | trigger |
| fn_registrar_ajuste_inventario | FUNCTION | p_id_empresa integer, p_id_material integer, p_cantidad numeric, p_tipo_movimiento character varying, p_id_usuario integer, p_observaciones text, p_stock_minimo numeric | TABLE(id_material integer, nuevo_stock numeric, stock_minimo numeric, id_movimiento integer) |
| fn_registrar_avance_obra | FUNCTION | p_id_obra integer, p_id_unidad integer, p_id_empresa integer, p_porcentaje numeric, p_fecha_registro date, p_observacion text, p_id_usuario integer | json |
| fn_registrar_bitacora | FUNCTION | p_id_usuario bigint, p_modulo character varying, p_accion character varying, p_descripcion character varying, p_ip character varying, p_estado character varying | void |
| fn_registrar_estructura_obra | FUNCTION | p_id_obra integer, p_id_padre integer, p_nombre character varying, p_tipo character varying, p_descripcion text, p_orden integer, p_id_empresa integer | json |
| fn_registrar_material | FUNCTION | p_id_empresa integer, p_codigo character varying, p_nombre_material character varying, p_descripcion text, p_id_categoria integer, p_id_unidad_medida integer, p_precio numeric, p_id_material_base integer, p_es_propio boolean | integer |
| fn_registrar_orden_compra | FUNCTION | p_id_empresa integer, p_id_proveedor integer, p_id_usuario integer, p_fecha date, p_observaciones text, p_estado character varying, p_items_json jsonb | integer |
| fn_registrar_recepcion_compra | FUNCTION | p_id_empresa integer, p_id_orden_compra integer, p_id_usuario integer, p_observaciones text, p_items_json jsonb | integer |
| fn_registrar_unidad_construccion | FUNCTION | p_id_obra integer, p_id_empresa integer, p_id_usuario integer, p_id_estructura integer, p_id_padre integer, p_nombre character varying, p_tipo_estructura character varying, p_descripcion text, p_tipo_unidad character varying, p_superficie numeric, p_cantidad_plantas integer, p_estado character varying, p_id_modelo integer, p_ambientes json, p_caracteristicas json | json |
| fn_reordenar_estructura_obra | FUNCTION | p_id_estructura integer, p_id_obra integer, p_direccion character varying, p_id_empresa integer | json |
| fn_resumen_avances_obra | FUNCTION | p_id_obra integer, p_id_empresa integer | json |
| fn_resumen_kpis_inventario | FUNCTION | p_id_empresa integer | TABLE(total_materiales integer, total_con_stock integer, total_sin_stock integer, total_stock_bajo integer, valor_total_inventario numeric, total_movimientos_mes integer) |
| fn_snapshot_precio_partida | FUNCTION |  | trigger |
| fn_sync_apu_precio | FUNCTION |  | trigger |
| fn_validar_incidencia_ot_cu19 | FUNCTION |  | trigger |
| p_registrar_usuario | PROCEDURE | IN p_username character varying, IN p_password character varying, IN p_correo character varying, IN p_id_empresa integer, IN p_id_rol integer, IN p_nombre_completo character varying, IN p_fecha_nacimiento date, IN p_ci character varying, IN p_direccion character varying, IN p_telefono character varying, IN p_telefono_ref character varying, IN p_ubicacion character varying | ? |
| sp_actualizar_estado_obra | FUNCTION | p_id_obra integer, p_id_empresa integer, p_nuevo_estado character varying | json |
| sp_actualizar_obra | FUNCTION | p_id_obra integer, p_id_empresa integer, p_id_tipo_obra integer, p_fecha_inicio date, p_fecha_fin date, p_nombre character varying, p_descripcion text, p_moneda character varying, p_ubicacion character varying, p_zona character varying, p_distrito character varying, p_uv character varying, p_manzana character varying, p_latitud numeric, p_longitud numeric, p_id_supervisor integer, p_id_cliente integer, p_cotizacion_inicial numeric, p_descripcion_cliente text, p_observacion text | json |
| sp_asignar_responsable_obra | FUNCTION | p_id_obra integer, p_id_usuario integer, p_id_empresa integer | json |
| sp_listar_obras | FUNCTION | p_id_empresa integer | json |
| sp_login_exitoso | FUNCTION | p_id_usuario integer, p_dispositivo_hash character varying | void |
| sp_login_usuario | FUNCTION | p_identificador character varying | json |
| sp_obtener_obra_detalle | FUNCTION | p_id_obra integer, p_id_empresa integer | json |
| sp_registrar_intento_fallido | FUNCTION | p_id_usuario integer | json |
| sp_registrar_obra | FUNCTION | p_codigo character varying, p_nombre character varying, p_descripcion text, p_id_tipo_obra integer, p_estado_obra character varying, p_fecha_inicio date, p_fecha_fin date, p_id_empresa integer, p_moneda character varying, p_ubicacion character varying, p_zona character varying, p_distrito character varying, p_uv character varying, p_manzana character varying, p_latitud numeric, p_longitud numeric, p_id_supervisor integer, p_id_cliente integer, p_cotizacion_inicial numeric, p_descripcion_cliente text, p_observacion text | json |
| sp_retirar_responsable_obra | FUNCTION | p_id_obra integer, p_id_usuario integer, p_id_empresa integer | json |


## 1. fn_actualizar_estructura_obra

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: t_estructura_obra, t_obra.
- Referencias Python: backend\app\repos\estructura_repos.py.
- Scripts con CREATE del nombre: backend\database\migration_hu35_estructura.sql.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.fn_actualizar_estructura_obra(p_id_estructura integer, p_id_obra integer, p_nombre character varying, p_tipo character varying, p_descripcion text, p_orden integer, p_id_empresa integer)
 RETURNS json
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_filas integer;
BEGIN
    UPDATE obras.t_estructura_obra e
    SET nombre = TRIM(p_nombre),
        tipo = COALESCE(TRIM(p_tipo), e.tipo),
        descripcion = TRIM(p_descripcion),
        orden = COALESCE(p_orden, e.orden)
    FROM obras.t_obra o
    WHERE e.id_estructura = p_id_estructura
      AND e.id_obra = p_id_obra
      AND o.id_obra = e.id_obra
      AND (o.id_empresa = p_id_empresa OR p_id_empresa IS NULL);

    GET DIAGNOSTICS v_filas = ROW_COUNT;

    IF v_filas = 0 THEN
        RETURN json_build_object(
            'success', false,
            'error', 'El elemento no existe o no tiene permisos sobre el proyecto.'
        );
    END IF;

    RETURN json_build_object(
        'success', true,
        'message', 'Elemento de estructura actualizado exitosamente.'
    );
EXCEPTION WHEN OTHERS THEN
    RETURN json_build_object(
        'success', false,
        'error', SQLERRM
    );
END;
$function$
```

</details>

## 2. fn_actualizar_unidad_construccion

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: t_estructura_obra, t_modelo_unidad, t_obra, t_unidad_ambiente, t_unidad_caracteristica, t_unidad_construccion.
- Referencias Python: backend\app\repos\unidad_repos.py.
- Scripts con CREATE del nombre: backend\database\migration_cu12_unidades_construccion.sql.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.fn_actualizar_unidad_construccion(p_id_obra integer, p_id_unidad integer, p_id_empresa integer, p_nombre character varying, p_descripcion text, p_tipo_unidad character varying, p_superficie numeric, p_cantidad_plantas integer, p_id_modelo integer, p_ambientes json, p_caracteristicas json)
 RETURNS json
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_id_estructura INTEGER;
    v_item JSON;
BEGIN
    SELECT u.id_estructura INTO v_id_estructura
    FROM obras.t_unidad_construccion u
    JOIN obras.t_estructura_obra e ON e.id_estructura = u.id_estructura
    JOIN obras.t_obra o ON o.id_obra = e.id_obra
    WHERE u.id_unidad = p_id_unidad AND o.id_obra = p_id_obra
      AND (o.id_empresa = p_id_empresa OR p_id_empresa IS NULL);
    IF v_id_estructura IS NULL THEN
        RETURN json_build_object('success', false, 'error', 'La unidad no existe o no pertenece a su empresa.');
    END IF;
    IF TRIM(COALESCE(p_nombre, '')) = '' THEN
        RETURN json_build_object('success', false, 'error', 'El nombre de la unidad es obligatorio.');
    END IF;
    IF UPPER(p_tipo_unidad) NOT IN ('VIVIENDA', 'DEPARTAMENTO', 'LOCAL', 'LOTE', 'OFICINA', 'OTRO') THEN
        RETURN json_build_object('success', false, 'error', 'Tipo de unidad no válido.');
    END IF;
    IF p_superficie < 0 OR p_cantidad_plantas < 0 THEN
        RETURN json_build_object('success', false, 'error', 'Superficie y cantidad de plantas no pueden ser negativas.');
    END IF;
    IF p_id_modelo IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM obras.t_modelo_unidad m JOIN obras.t_obra o ON o.id_obra = p_id_obra
        WHERE m.id_modelo = p_id_modelo AND m.id_empresa = o.id_empresa AND m.activo = TRUE
    ) THEN
        RETURN json_build_object('success', false, 'error', 'El modelo no existe o pertenece a otra empresa.');
    END IF;

    UPDATE obras.t_estructura_obra
    SET nombre = TRIM(p_nombre), descripcion = TRIM(p_descripcion)
    WHERE id_estructura = v_id_estructura;
    UPDATE obras.t_unidad_construccion
    SET tipo_unidad = UPPER(p_tipo_unidad), superficie = p_superficie,
        cantidad_plantas = p_cantidad_plantas, id_modelo = p_id_modelo
    WHERE id_unidad = p_id_unidad;

    DELETE FROM obras.t_unidad_ambiente WHERE id_unidad = p_id_unidad;
    FOR v_item IN SELECT * FROM json_array_elements(COALESCE(p_ambientes, '[]'::json)) LOOP
        IF TRIM(COALESCE(v_item->>'nombre', '')) <> '' AND COALESCE((v_item->>'cantidad')::INTEGER, 0) > 0 THEN
            INSERT INTO obras.t_unidad_ambiente(id_unidad, nombre, cantidad)
            VALUES (p_id_unidad, TRIM(v_item->>'nombre'), (v_item->>'cantidad')::INTEGER);
        END IF;
    END LOOP;

    DELETE FROM obras.t_unidad_caracteristica WHERE id_unidad = p_id_unidad;
    FOR v_item IN SELECT * FROM json_array_elements(COALESCE(p_caracteristicas, '[]'::json)) LOOP
        IF TRIM(COALESCE(v_item->>'nombre', '')) <> '' AND TRIM(COALESCE(v_item->>'valor', '')) <> '' THEN
            INSERT INTO obras.t_unidad_caracteristica(id_unidad, nombre, valor)
            VALUES (p_id_unidad, TRIM(v_item->>'nombre'), TRIM(v_item->>'valor'));
        END IF;
    END LOOP;

    RETURN json_build_object('success', true, 'message', 'Unidad actualizada exitosamente.');
EXCEPTION WHEN OTHERS THEN
    RETURN json_build_object('success', false, 'error', SQLERRM);
END;
$function$
```

</details>

## 3. fn_actualizar_updated_at

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: ninguna coincidencia.
- Referencias Python: sin coincidencia.
- Scripts con CREATE del nombre: **no localizado en los SQL versionados revisados**.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.fn_actualizar_updated_at()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$function$
```

</details>

## 4. fn_actualizar_updated_at_cu12

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: ninguna coincidencia.
- Referencias Python: sin coincidencia.
- Scripts con CREATE del nombre: backend\database\migration_cu12_unidades_construccion.sql.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.fn_actualizar_updated_at_cu12()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$function$
```

</details>

## 5. fn_actualizar_updated_at_cu14

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: ninguna coincidencia.
- Referencias Python: sin coincidencia.
- Scripts con CREATE del nombre: backend\database\migration_cu14_materiales.sql.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.fn_actualizar_updated_at_cu14()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN NEW.updated_at = CURRENT_TIMESTAMP; RETURN NEW; END;
$function$
```

</details>

## 6. fn_actualizar_updated_at_cu15

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: ninguna coincidencia.
- Referencias Python: sin coincidencia.
- Scripts con CREATE del nombre: backend\database\migration_cu15_proveedores.sql.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.fn_actualizar_updated_at_cu15()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$function$
```

</details>

## 7. fn_actualizar_updated_at_cu19

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: ninguna coincidencia.
- Referencias Python: sin coincidencia.
- Scripts con CREATE del nombre: backend\database\migration_cu19_incidencias.sql.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.fn_actualizar_updated_at_cu19()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$function$
```

</details>

## 8. fn_actualizar_updated_at_estimacion_apu

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: ninguna coincidencia.
- Referencias Python: sin coincidencia.
- Scripts con CREATE del nombre: backend\database\migration_estimacion_apu.sql.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.fn_actualizar_updated_at_estimacion_apu()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$ BEGIN NEW.updated_at = CURRENT_TIMESTAMP; RETURN NEW; END; $function$
```

</details>

## 9. fn_actualizar_updated_at_estructura

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: ninguna coincidencia.
- Referencias Python: sin coincidencia.
- Scripts con CREATE del nombre: backend\database\migration_hu35_estructura.sql.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.fn_actualizar_updated_at_estructura()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$function$
```

</details>

## 10. fn_aprobar_rechazar_orden_compra

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: t_orden_compra.
- Referencias Python: backend\app\repos\compras_repos.py.
- Scripts con CREATE del nombre: backend\database\migration_compras_recepcion.sql.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.fn_aprobar_rechazar_orden_compra(p_id_empresa integer, p_id_orden_compra integer, p_id_usuario integer, p_aprobar boolean, p_observacion text)
 RETURNS boolean
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_estado_actual VARCHAR(30);
    v_nuevo_estado VARCHAR(30);
BEGIN
    SELECT estado INTO v_estado_actual
    FROM obras.t_orden_compra
    WHERE id_orden_compra = p_id_orden_compra
      AND (p_id_empresa IS NULL OR id_empresa = p_id_empresa);

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Orden de compra no encontrada o no pertenece a la empresa';
    END IF;

    IF v_estado_actual <> 'PENDIENTE_APROBACION' THEN
        RAISE EXCEPTION 'Solo se pueden aprobar o rechazar órdenes en estado PENDIENTE_APROBACION';
    END IF;

    v_nuevo_estado := CASE WHEN p_aprobar THEN 'APROBADA' ELSE 'RECHAZADA' END;

    IF NOT p_aprobar AND TRIM(COALESCE(p_observacion, '')) = '' THEN
        RAISE EXCEPTION 'Debe registrar una observación con el motivo del rechazo';
    END IF;

    UPDATE obras.t_orden_compra
    SET estado = v_nuevo_estado,
        id_usuario_aprobacion = p_id_usuario,
        fecha_aprobacion = CURRENT_TIMESTAMP,
        observacion_aprobacion = NULLIF(TRIM(p_observacion), ''),
        updated_at = CURRENT_TIMESTAMP
    WHERE id_orden_compra = p_id_orden_compra;

    RETURN TRUE;
END;
$function$
```

</details>

## 11. fn_calcular_analisis_precio_unitario

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: t_analisi_precio_unitario_insumo, t_analisis_precio_unitario.
- Referencias Python: backend\app\repos\estimacion_repos.py.
- Scripts con CREATE del nombre: backend\database\migration_apu_materiales_y_presupuestos.sql, backend\database\migration_estimacion_apu.sql.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.fn_calcular_analisis_precio_unitario(p_id_analisis_precio_unitario integer, p_id_empresa integer)
 RETURNS json
 LANGUAGE plpgsql
AS $function$
DECLARE v_apu JSON; v_insumos JSON; v_materiales NUMERIC; v_mano_obra NUMERIC; v_directo NUMERIC; v_utilidad NUMERIC; v_final NUMERIC;
BEGIN
    SELECT a.costo_materiales, a.mano_de_obra, a.costo_directo,
           ROUND(a.costo_directo * a.porcentaje_utilidad / 100, 2), a.precio_unitario_final
    INTO v_materiales, v_mano_obra, v_directo, v_utilidad, v_final
    FROM obras.t_analisis_precio_unitario a
    WHERE a.id_analisis_precio_unitario = p_id_analisis_precio_unitario AND a.id_empresa = p_id_empresa;
    IF NOT FOUND THEN
        RETURN json_build_object('success', false, 'error', 'La partida no existe o no pertenece a su empresa.');
    END IF;
    SELECT COALESCE(json_agg(json_build_object(
        'id_analisis_precio_unitario_insumo', i.id_analisis_precio_unitario_insumo,
        'id_material', i.id_material, 'nombre', i.nombre,
        'cantidad', i.cantidad, 'precio_unitario', i.precio_unitario,
        'subtotal', i.subtotal, 'id_unidad_medida', i.id_unidad_medida
    ) ORDER BY i.orden, i.id_analisis_precio_unitario_insumo), '[]'::json)
    INTO v_insumos
    FROM obras.t_analisi_precio_unitario_insumo i
    WHERE i.id_analisis_precio_unitario = p_id_analisis_precio_unitario AND i.id_empresa = p_id_empresa;
    SELECT json_build_object(
        'success', true,
        'costo_materiales', v_materiales,
        'mano_de_obra', v_mano_obra,
        'costo_directo', v_directo,
        'porcentaje_utilidad', a.porcentaje_utilidad,
        'utilidad', v_utilidad,
        'precio_unitario_final', v_final,
        'costo_directo_unitario', v_directo,
        'insumos', v_insumos
    ) INTO v_apu
    FROM obras.t_analisis_precio_unitario a
    WHERE a.id_analisis_precio_unitario = p_id_analisis_precio_unitario;
    RETURN v_apu;
END;
$function$
```

</details>

## 12. fn_calcular_estimacion

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: t_analisis_precio_unitario, t_estimacion, t_estimacion_analisis_precio_unitario, t_unidad_medida.
- Referencias Python: backend\app\repos\estimacion_repos.py.
- Scripts con CREATE del nombre: backend\database\migration_apu_materiales_y_presupuestos.sql, backend\database\migration_estimacion_apu.sql.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.fn_calcular_estimacion(p_id_estimacion integer, p_id_empresa integer)
 RETURNS json
 LANGUAGE plpgsql
AS $function$
DECLARE v_detalle JSON; v_directo NUMERIC; v_utilidad NUMERIC; v_total NUMERIC;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM obras.t_estimacion WHERE id_estimacion = p_id_estimacion AND id_empresa = p_id_empresa) THEN
        RETURN json_build_object('success', false, 'error', 'La estimación no existe o no pertenece a su empresa.');
    END IF;
        SELECT COALESCE(SUM(ROUND(COALESCE(d.costo_directo_unitario, a.costo_directo) * d.cantidad, 2)), 0),
            COALESCE(SUM(ROUND((COALESCE(d.precio_unitario, a.precio_unitario_final) - COALESCE(d.costo_directo_unitario, a.costo_directo)) * d.cantidad, 2)), 0),
           COALESCE(SUM(d.precio_total), 0),
           COALESCE(json_agg(json_build_object(
               'id_analisis_precio_unitario', a.id_analisis_precio_unitario,
               'id_estimacion_analisis_precio_unitario', d.id_estimacion_analisis_precio_unitario,
               'item_codigo', d.item_codigo, 'nombre', a.nombre,
               'unidad', um.abreviatura,
               'costo_directo_unitario', COALESCE(d.costo_directo_unitario, a.costo_directo),
               'costo_unitario', COALESCE(d.precio_unitario, a.precio_unitario_final),
               'cantidad', d.cantidad, 'subtotal', d.precio_total
           ) ORDER BY d.orden), '[]'::json)
    INTO v_directo, v_utilidad, v_total, v_detalle
    FROM obras.t_estimacion_analisis_precio_unitario d
    JOIN obras.t_estimacion e ON e.id_estimacion = d.id_estimacion
    JOIN obras.t_analisis_precio_unitario a ON a.id_analisis_precio_unitario = d.id_analisis_precio_unitario
    JOIN obras.t_unidad_medida um ON um.id_unidad_medida = a.id_unidad_medida
    WHERE d.id_estimacion = p_id_estimacion AND e.id_empresa = p_id_empresa AND a.id_empresa = p_id_empresa;
    RETURN json_build_object(
        'success', true, 'detalle', v_detalle,
        'subtotal_directo', ROUND(v_directo, 2), 'utilidad', ROUND(v_utilidad, 2),
        'monto_total', ROUND(v_total, 2)
    );
END;
$function$
```

</details>

## 13. fn_cambiar_estado_orden_compra

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: t_orden_compra.
- Referencias Python: backend\app\repos\compras_repos.py.
- Scripts con CREATE del nombre: backend\database\migration_compras_recepcion.sql.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.fn_cambiar_estado_orden_compra(p_id_empresa integer, p_id_orden_compra integer, p_nuevo_estado character varying)
 RETURNS boolean
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_estado_actual VARCHAR(30);
BEGIN
    SELECT estado INTO v_estado_actual
    FROM obras.t_orden_compra
    WHERE id_orden_compra = p_id_orden_compra
      AND (p_id_empresa IS NULL OR id_empresa = p_id_empresa);

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Orden de compra no encontrada o no pertenece a la empresa';
    END IF;

    IF p_nuevo_estado = 'PENDIENTE_APROBACION' THEN
        IF v_estado_actual <> 'BORRADOR' THEN
            RAISE EXCEPTION 'Solo las órdenes en BORRADOR pueden enviarse a aprobación';
        END IF;
    ELSIF p_nuevo_estado = 'CANCELADA' THEN
        IF v_estado_actual IN ('RECIBIDA', 'RECIBIDA_PARCIAL') THEN
            RAISE EXCEPTION 'No se puede cancelar una orden que ya tiene recepciones';
        END IF;
    ELSE
        RAISE EXCEPTION 'Transición de estado no permitida con esta función';
    END IF;

    UPDATE obras.t_orden_compra
    SET estado = p_nuevo_estado,
        updated_at = CURRENT_TIMESTAMP
    WHERE id_orden_compra = p_id_orden_compra;

    RETURN TRUE;
END;
$function$
```

</details>

## 14. fn_cambiar_estado_unidad

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: t_estructura_obra, t_obra, t_unidad_construccion, t_unidad_seguimiento.
- Referencias Python: backend\app\repos\unidad_repos.py.
- Scripts con CREATE del nombre: backend\database\migration_cu12_unidades_construccion.sql.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.fn_cambiar_estado_unidad(p_id_obra integer, p_id_unidad integer, p_id_empresa integer, p_estado_nuevo character varying, p_id_usuario integer, p_observacion text)
 RETURNS json
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_estado_anterior VARCHAR;
BEGIN
    IF UPPER(p_estado_nuevo) NOT IN ('PLANIFICADO', 'EN_CONSTRUCCION', 'FINALIZADO', 'SUSPENDIDO') THEN
        RETURN json_build_object('success', false, 'error', 'Estado de unidad no válido.');
    END IF;
    SELECT u.estado INTO v_estado_anterior
    FROM obras.t_unidad_construccion u
    JOIN obras.t_estructura_obra e ON e.id_estructura = u.id_estructura
    JOIN obras.t_obra o ON o.id_obra = e.id_obra
    WHERE u.id_unidad = p_id_unidad AND o.id_obra = p_id_obra
      AND (o.id_empresa = p_id_empresa OR p_id_empresa IS NULL)
    FOR UPDATE;
    IF v_estado_anterior IS NULL THEN
        RETURN json_build_object('success', false, 'error', 'La unidad no existe o no pertenece a su empresa.');
    END IF;
    IF v_estado_anterior <> UPPER(p_estado_nuevo) THEN
        UPDATE obras.t_unidad_construccion SET estado = UPPER(p_estado_nuevo) WHERE id_unidad = p_id_unidad;
        INSERT INTO obras.t_unidad_seguimiento(
            id_unidad, estado_anterior, estado_nuevo, id_usuario, observacion
        ) VALUES (
            p_id_unidad, v_estado_anterior, UPPER(p_estado_nuevo), p_id_usuario, TRIM(p_observacion)
        );
    END IF;
    RETURN json_build_object('success', true, 'message', 'Estado actualizado exitosamente.');
EXCEPTION WHEN OTHERS THEN
    RETURN json_build_object('success', false, 'error', SQLERRM);
END;
$function$
```

</details>

## 15. fn_consultar_material

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: t_categoria_material, t_empresa, t_material, t_unidad_medida.
- Referencias Python: backend\app\repos\material_repos.py.
- Scripts con CREATE del nombre: backend\database\migration_refactor_materiales.sql.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.fn_consultar_material(p_id_empresa integer, p_id_material integer)
 RETURNS TABLE(id_material integer, codigo character varying, nombre_material character varying, descripcion text, id_categoria integer, categoria_nombre character varying, id_unidad_medida integer, unidad_nombre character varying, unidad_abreviatura character varying, precio numeric, estado character varying, id_empresa integer, nombre_empresa character varying, id_material_base integer, es_propio boolean, created_at timestamp with time zone, updated_at timestamp with time zone)
 LANGUAGE plpgsql
AS $function$
BEGIN
    RETURN QUERY
    SELECT 
        m.id_material,
        m.codigo,
        m.nombre_material,
        m.descripcion,
        m.id_categoria,
        c.nombre AS categoria_nombre,
        m.id_unidad_medida,
        um.nombre AS unidad_nombre,
        um.abreviatura AS unidad_abreviatura,
        m.precio,
        m.estado,
        m.id_empresa,
        e.nombre_empresa,
        m.id_material_base,
        m.es_propio,
        m.created_at,
        m.updated_at
    FROM obras.t_material m
    JOIN obras.t_categoria_material c ON c.id_categoria = m.id_categoria
    JOIN obras.t_unidad_medida um ON um.id_unidad_medida = m.id_unidad_medida
    JOIN obras.t_empresa e ON e.id_empresa = m.id_empresa
    WHERE m.id_material = p_id_material
      AND (p_id_empresa IS NULL OR m.id_empresa = p_id_empresa);
END;
$function$
```

</details>

## 16. fn_consultar_orden_compra

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: t_empresa, t_orden_compra, t_persona, t_proveedor, t_usuario.
- Referencias Python: backend\app\repos\compras_repos.py.
- Scripts con CREATE del nombre: backend\database\migration_compras_recepcion.sql.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.fn_consultar_orden_compra(p_id_empresa integer, p_id_orden_compra integer)
 RETURNS TABLE(id_orden_compra integer, numero_orden character varying, fecha date, observaciones text, estado character varying, id_empresa integer, nombre_empresa character varying, id_proveedor integer, nombre_proveedor character varying, nit_proveedor character varying, id_usuario_solicitante integer, nombre_solicitante character varying, subtotal numeric, total numeric, id_usuario_aprobacion integer, nombre_aprobador character varying, fecha_aprobacion timestamp with time zone, observacion_aprobacion text, created_at timestamp with time zone, updated_at timestamp with time zone)
 LANGUAGE plpgsql
AS $function$
BEGIN
    RETURN QUERY
    SELECT 
        oc.id_orden_compra,
        oc.numero_orden,
        oc.fecha,
        oc.observaciones,
        oc.estado,
        oc.id_empresa,
        e.nombre_empresa,
        oc.id_proveedor,
        p.nombre AS nombre_proveedor,
        p.nit AS nit_proveedor,
        oc.id_usuario_solicitante,
        COALESCE(pers_sol.nombre_completo, u_sol.username)::VARCHAR AS nombre_solicitante,
        oc.subtotal,
        oc.total,
        oc.id_usuario_aprobacion,
        CASE WHEN u_aprob.id_usuario IS NOT NULL 
             THEN COALESCE(pers_aprob.nombre_completo, u_aprob.username)::VARCHAR 
             ELSE NULL END AS nombre_aprobador,
        oc.fecha_aprobacion,
        oc.observacion_aprobacion,
        oc.created_at,
        oc.updated_at
    FROM obras.t_orden_compra oc
    JOIN obras.t_empresa e ON e.id_empresa = oc.id_empresa
    JOIN obras.t_proveedor p ON p.id_proveedor = oc.id_proveedor
    JOIN obras.t_usuario u_sol ON u_sol.id_usuario = oc.id_usuario_solicitante
    LEFT JOIN obras.t_persona pers_sol ON pers_sol.id_persona = u_sol.id_persona
    LEFT JOIN obras.t_usuario u_aprob ON u_aprob.id_usuario = oc.id_usuario_aprobacion
    LEFT JOIN obras.t_persona pers_aprob ON pers_aprob.id_persona = u_aprob.id_persona
    WHERE oc.id_orden_compra = p_id_orden_compra
      AND (p_id_empresa IS NULL OR oc.id_empresa = p_id_empresa);
END;
$function$
```

</details>

## 17. fn_copiar_catalogo_base_empresa

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: t_empresa, t_material, t_material_base.
- Referencias Python: backend\app\repos\material_repos.py.
- Scripts con CREATE del nombre: backend\database\migration_refactor_materiales.sql.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.fn_copiar_catalogo_base_empresa(p_id_empresa integer)
 RETURNS integer
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_insertados INT := 0;
BEGIN
    IF p_id_empresa IS NULL THEN
        RAISE EXCEPTION 'El id_empresa es obligatorio para inicializar el catálogo';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM obras.t_empresa WHERE id_empresa = p_id_empresa) THEN
        RAISE EXCEPTION 'La empresa % no existe', p_id_empresa;
    END IF;

    INSERT INTO obras.t_material (
        id_empresa,
        id_material_base,
        codigo,
        nombre_material,
        descripcion,
        id_categoria,
        id_unidad_medida,
        precio,
        estado,
        es_propio,
        created_at,
        updated_at
    )
    SELECT 
        p_id_empresa,
        mb.id_material_base,
        mb.codigo,
        mb.nombre_material,
        mb.descripcion,
        mb.id_categoria,
        mb.id_unidad_medida,
        COALESCE(mb.precio_referencial, 0),
        'ACTIVO',
        FALSE,
        CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP
    FROM obras.t_material_base mb
    WHERE mb.estado = 'ACTIVO'
      AND NOT EXISTS (
          SELECT 1 FROM obras.t_material m 
          WHERE m.id_empresa = p_id_empresa 
            AND m.id_material_base = mb.id_material_base
      )
      AND NOT EXISTS (
          SELECT 1 FROM obras.t_material m
          WHERE m.id_empresa = p_id_empresa
            AND LOWER(TRIM(m.codigo)) = LOWER(TRIM(mb.codigo))
      );

    GET DIAGNOSTICS v_insertados = ROW_COUNT;
    RETURN v_insertados;
END;
$function$
```

</details>

## 18. fn_cu17_actualizar_updated_at

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: ninguna coincidencia.
- Referencias Python: sin coincidencia.
- Scripts con CREATE del nombre: backend\database\migration_cu17_control_costos_ordenes_cambio.sql.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.fn_cu17_actualizar_updated_at()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
    NEW.updated_at := CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$function$
```

</details>

## 19. fn_cu17_detalle_solo_pendiente

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: t_orden_cambio.
- Referencias Python: sin coincidencia.
- Scripts con CREATE del nombre: backend\database\migration_cu17_control_costos_ordenes_cambio.sql.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.fn_cu17_detalle_solo_pendiente()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_orden BIGINT;
    v_estado VARCHAR(12);
BEGIN
    v_orden := CASE WHEN TG_OP = 'DELETE' THEN OLD.id_orden_cambio ELSE NEW.id_orden_cambio END;
    SELECT estado INTO v_estado
    FROM obras.t_orden_cambio
    WHERE id_orden_cambio = v_orden;
    IF v_estado IS DISTINCT FROM 'PENDIENTE' THEN
        RAISE EXCEPTION 'Los detalles solo pueden cambiar mientras la orden esta PENDIENTE.';
    END IF;
    RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
END;
$function$
```

</details>

## 20. fn_cu17_historial_append_only

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: ninguna coincidencia.
- Referencias Python: sin coincidencia.
- Scripts con CREATE del nombre: backend\database\migration_cu17_control_costos_ordenes_cambio.sql.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.fn_cu17_historial_append_only()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
    RAISE EXCEPTION 'El historial de ordenes de cambio es inmutable.';
END;
$function$
```

</details>

## 21. fn_cu17_impedir_borrado_costo

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: ninguna coincidencia.
- Referencias Python: sin coincidencia.
- Scripts con CREATE del nombre: backend\database\migration_cu17_control_costos_ordenes_cambio.sql.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.fn_cu17_impedir_borrado_costo()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
    RAISE EXCEPTION 'Los costos ejecutados no se eliminan; deben anularse.';
END;
$function$
```

</details>

## 22. fn_cu17_linea_base_identidad_inmutable

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: ninguna coincidencia.
- Referencias Python: sin coincidencia.
- Scripts con CREATE del nombre: backend\database\migration_cu17_control_costos_ordenes_cambio.sql.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.fn_cu17_linea_base_identidad_inmutable()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
    IF NEW.id_empresa IS DISTINCT FROM OLD.id_empresa
       OR NEW.id_obra IS DISTINCT FROM OLD.id_obra
       OR NEW.id_estimacion_base IS DISTINCT FROM OLD.id_estimacion_base THEN
        RAISE EXCEPTION
            'La empresa, obra y estimacion base no pueden modificarse despues de crear la linea base.';
    END IF;
    RETURN NEW;
END;
$function$
```

</details>

## 23. fn_cu17_orden_solo_pendiente

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: ninguna coincidencia.
- Referencias Python: sin coincidencia.
- Scripts con CREATE del nombre: backend\database\migration_cu17_control_costos_ordenes_cambio.sql.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.fn_cu17_orden_solo_pendiente()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
    IF OLD.estado <> 'PENDIENTE' THEN
        RAISE EXCEPTION 'Solo una orden PENDIENTE puede modificarse.';
    END IF;
    RETURN NEW;
END;
$function$
```

</details>

## 24. fn_cu17_validar_costo

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: t_control_costo_obra, t_estimacion_analisis_precio_unitario.
- Referencias Python: sin coincidencia.
- Scripts con CREATE del nombre: backend\database\migration_cu17_control_costos_ordenes_cambio.sql.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.fn_cu17_validar_costo()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_empresa INTEGER;
    v_obra INTEGER;
    v_estimacion INTEGER;
    v_estado VARCHAR(10);
BEGIN
    SELECT id_empresa, id_obra, id_estimacion_base, estado
      INTO v_empresa, v_obra, v_estimacion, v_estado
      FROM obras.t_control_costo_obra
     WHERE id_control_costo = NEW.id_control_costo;

    IF NOT FOUND OR v_estado <> 'ACTIVO' THEN
        RAISE EXCEPTION 'La linea base no existe o no esta activa.';
    END IF;
    IF NEW.id_empresa <> v_empresa OR NEW.id_obra <> v_obra THEN
        RAISE EXCEPTION 'El costo no pertenece a la empresa y obra de su linea base.';
    END IF;
    IF NOT EXISTS (
        SELECT 1
          FROM obras.t_estimacion_analisis_precio_unitario d
         WHERE d.id_estimacion_analisis_precio_unitario = NEW.id_partida_presupuestaria
           AND d.id_estimacion = v_estimacion
    ) THEN
        RAISE EXCEPTION 'La partida no pertenece exactamente a la estimacion base.';
    END IF;
    RETURN NEW;
END;
$function$
```

</details>

## 25. fn_cu17_validar_detalle_orden

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: t_analisis_precio_unitario, t_estimacion_analisis_precio_unitario, t_orden_cambio.
- Referencias Python: sin coincidencia.
- Scripts con CREATE del nombre: backend\database\migration_cu17_control_costos_ordenes_cambio.sql.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.fn_cu17_validar_detalle_orden()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_estimacion INTEGER;
    v_empresa INTEGER;
    v_obra INTEGER;
BEGIN
    SELECT id_estimacion_base, id_empresa, id_obra
      INTO v_estimacion, v_empresa, v_obra
      FROM obras.t_orden_cambio
     WHERE id_orden_cambio = NEW.id_orden_cambio;

    IF NEW.id_partida_presupuestaria IS NOT NULL AND NOT EXISTS (
        SELECT 1
          FROM obras.t_estimacion_analisis_precio_unitario d
         WHERE d.id_estimacion_analisis_precio_unitario = NEW.id_partida_presupuestaria
           AND d.id_estimacion = v_estimacion
    ) THEN
        RAISE EXCEPTION 'La partida del cambio no pertenece a la estimacion base.';
    END IF;

    IF NEW.id_analisis_precio_unitario IS NOT NULL AND NOT EXISTS (
        SELECT 1
          FROM obras.t_analisis_precio_unitario a
         WHERE a.id_analisis_precio_unitario = NEW.id_analisis_precio_unitario
           AND a.id_empresa = v_empresa
           AND (a.id_obra IS NULL OR a.id_obra = v_obra)
    ) THEN
        RAISE EXCEPTION 'El APU no pertenece a la empresa o a la obra de la orden.';
    END IF;
    RETURN NEW;
END;
$function$
```

</details>

## 26. fn_cu17_validar_linea_base

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: t_estimacion, t_obra.
- Referencias Python: sin coincidencia.
- Scripts con CREATE del nombre: backend\database\migration_cu17_control_costos_ordenes_cambio.sql.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.fn_cu17_validar_linea_base()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_version INTEGER;
    v_moneda VARCHAR(10);
BEGIN
    SELECT e.version, o.moneda
      INTO v_version, v_moneda
      FROM obras.t_estimacion e
      JOIN obras.t_obra o ON o.id_obra = e.id_obra
     WHERE e.id_estimacion = NEW.id_estimacion_base
       AND e.id_obra = NEW.id_obra
       AND e.id_empresa = NEW.id_empresa
       AND o.id_empresa = NEW.id_empresa
       AND e.estado = 'APROBADA'
       AND o.moneda IS NOT NULL
       AND BTRIM(o.moneda) <> '';

    IF NOT FOUND THEN
        RAISE EXCEPTION 'La linea base debe ser un presupuesto APROBADO de la misma obra y empresa, con moneda valida.';
    END IF;

    NEW.version_presupuesto := v_version;
    NEW.moneda := v_moneda;
    RETURN NEW;
END;
$function$
```

</details>

## 27. fn_cu17_validar_orden

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: t_control_costo_obra.
- Referencias Python: sin coincidencia.
- Scripts con CREATE del nombre: backend\database\migration_cu17_control_costos_ordenes_cambio.sql.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.fn_cu17_validar_orden()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_empresa INTEGER;
    v_obra INTEGER;
    v_estimacion INTEGER;
BEGIN
    SELECT id_empresa, id_obra, id_estimacion_base
      INTO v_empresa, v_obra, v_estimacion
      FROM obras.t_control_costo_obra
     WHERE id_control_costo = NEW.id_control_costo;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'La linea base indicada no existe.';
    END IF;
    IF NEW.id_empresa <> v_empresa OR NEW.id_obra <> v_obra
       OR NEW.id_estimacion_base <> v_estimacion THEN
        RAISE EXCEPTION 'La orden no coincide con la empresa, obra y estimacion de su linea base.';
    END IF;
    RETURN NEW;
END;
$function$
```

</details>

## 28. fn_desactivar_material

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: t_material.
- Referencias Python: backend\app\repos\material_repos.py.
- Scripts con CREATE del nombre: backend\database\migration_refactor_materiales.sql.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.fn_desactivar_material(p_id_empresa integer, p_id_material integer, p_nuevo_estado character varying DEFAULT 'INACTIVO'::character varying)
 RETURNS boolean
 LANGUAGE plpgsql
AS $function$
BEGIN
    IF p_nuevo_estado NOT IN ('ACTIVO', 'INACTIVO') THEN
        RAISE EXCEPTION 'Estado no válido: %', p_nuevo_estado;
    END IF;

    UPDATE obras.t_material
    SET estado = p_nuevo_estado,
        updated_at = CURRENT_TIMESTAMP
    WHERE id_material = p_id_material
      AND (p_id_empresa IS NULL OR id_empresa = p_id_empresa);

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Material no encontrado o no pertenece a la empresa';
    END IF;

    RETURN TRUE;
END;
$function$
```

</details>

## 29. fn_eliminar_avance_obra

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: t_avance_obra, t_obra.
- Referencias Python: sin coincidencia.
- Scripts con CREATE del nombre: **no localizado en los SQL versionados revisados**.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.fn_eliminar_avance_obra(p_id_avance integer, p_id_obra integer, p_id_empresa integer)
 RETURNS json
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_filas INTEGER;
BEGIN
    DELETE FROM obras.t_avance_obra a
    USING obras.t_obra o
    WHERE a.id_avance = p_id_avance
      AND a.id_obra = p_id_obra
      AND o.id_obra = a.id_obra
      AND (o.id_empresa = p_id_empresa OR p_id_empresa IS NULL);

    GET DIAGNOSTICS v_filas = ROW_COUNT;

    IF v_filas = 0 THEN
        RETURN json_build_object('success', false,
            'error', 'El avance no existe o no tiene permisos para eliminarlo.');
    END IF;

    RETURN json_build_object('success', true, 'message', 'Avance eliminado exitosamente.');
EXCEPTION WHEN OTHERS THEN
    RETURN json_build_object('success', false, 'error', SQLERRM);
END;
$function$
```

</details>

## 30. fn_eliminar_estructura_obra

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: t_estructura_obra, t_obra.
- Referencias Python: backend\app\repos\estructura_repos.py.
- Scripts con CREATE del nombre: backend\database\migration_hu35_estructura.sql.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.fn_eliminar_estructura_obra(p_id_estructura integer, p_id_obra integer, p_id_empresa integer)
 RETURNS json
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_filas integer;
BEGIN
    DELETE FROM obras.t_estructura_obra e
    USING obras.t_obra o
    WHERE e.id_estructura = p_id_estructura
      AND e.id_obra = p_id_obra
      AND o.id_obra = e.id_obra
      AND (o.id_empresa = p_id_empresa OR p_id_empresa IS NULL);

    GET DIAGNOSTICS v_filas = ROW_COUNT;

    IF v_filas = 0 THEN
        RETURN json_build_object(
            'success', false,
            'error', 'El elemento no existe o no tiene permisos sobre el proyecto.'
        );
    END IF;

    RETURN json_build_object(
        'success', true,
        'message', 'Elemento y subelementos eliminados exitosamente.'
    );
EXCEPTION WHEN OTHERS THEN
    RETURN json_build_object(
        'success', false,
        'error', SQLERRM
    );
END;
$function$
```

</details>

## 31. fn_eliminar_unidad_construccion

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: t_estructura_obra, t_obra, t_unidad_construccion.
- Referencias Python: backend\app\repos\unidad_repos.py.
- Scripts con CREATE del nombre: backend\database\migration_cu12_eliminar_unidad.sql.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.fn_eliminar_unidad_construccion(p_id_obra integer, p_id_unidad integer, p_id_empresa integer)
 RETURNS json
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_id_estructura INTEGER;
    v_codigo VARCHAR;
    v_nombre VARCHAR;
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM obras.t_obra
        WHERE id_obra = p_id_obra
          AND (id_empresa = p_id_empresa OR p_id_empresa IS NULL)
    ) THEN
        RETURN json_build_object(
            'success', false,
            'error', 'El proyecto no existe o no pertenece a su empresa.'
        );
    END IF;

    SELECT e.id_estructura, u.codigo, e.nombre
    INTO v_id_estructura, v_codigo, v_nombre
    FROM obras.t_unidad_construccion u
    JOIN obras.t_estructura_obra e ON e.id_estructura = u.id_estructura
    JOIN obras.t_obra o ON o.id_obra = e.id_obra
    WHERE u.id_unidad = p_id_unidad
      AND o.id_obra = p_id_obra
      AND (o.id_empresa = p_id_empresa OR p_id_empresa IS NULL)
    FOR UPDATE OF u, e;

    IF v_id_estructura IS NULL THEN
        RETURN json_build_object(
            'success', false,
            'error', 'La unidad no existe o no pertenece al proyecto solicitado.'
        );
    END IF;

    IF EXISTS (
        SELECT 1
        FROM obras.t_estructura_obra
        WHERE id_padre = v_id_estructura
    ) THEN
        RETURN json_build_object(
            'success', false,
            'error', 'No se puede eliminar la unidad porque contiene elementos dentro.'
        );
    END IF;

    -- Las relaciones propias de CU12 usan ON DELETE CASCADE.
    DELETE FROM obras.t_unidad_construccion
    WHERE id_unidad = p_id_unidad;

    -- El trigger protector permanece activo. En este punto ya no existe la
    -- unidad asociada y se verificó que el nodo no contiene hijos.
    DELETE FROM obras.t_estructura_obra
    WHERE id_estructura = v_id_estructura
      AND id_obra = p_id_obra;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'No se pudo eliminar el nodo estructural asociado a la unidad.';
    END IF;

    RETURN json_build_object(
        'success', true,
        'id_unidad', p_id_unidad,
        'id_estructura', v_id_estructura,
        'codigo', v_codigo,
        'nombre', v_nombre,
        'message', 'Unidad eliminada exitosamente.'
    );
EXCEPTION WHEN OTHERS THEN
    RETURN json_build_object('success', false, 'error', SQLERRM);
END;
$function$
```

</details>

## 32. fn_generar_codigo_unidad

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: ninguna coincidencia.
- Referencias Python: sin coincidencia.
- Scripts con CREATE del nombre: backend\database\migration_cu12_unidades_construccion.sql.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.fn_generar_codigo_unidad()
 RETURNS character varying
 LANGUAGE plpgsql
AS $function$
BEGIN
    RETURN 'UNI-' || LPAD(nextval('obras.seq_codigo_unidad')::text, 6, '0');
END;
$function$
```

</details>

## 33. fn_generar_numero_orden_compra

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: t_orden_compra.
- Referencias Python: sin coincidencia.
- Scripts con CREATE del nombre: backend\database\migration_compras_recepcion.sql.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.fn_generar_numero_orden_compra(p_id_empresa integer)
 RETURNS character varying
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_anio VARCHAR(4);
    v_correlativo INT;
    v_numero VARCHAR(50);
BEGIN
    v_anio := TO_CHAR(CURRENT_DATE, 'YYYY');
    SELECT COALESCE(COUNT(*), 0) + 1 INTO v_correlativo
    FROM obras.t_orden_compra
    WHERE id_empresa = p_id_empresa
      AND TO_CHAR(fecha, 'YYYY') = v_anio;

    v_numero := 'OC-' || v_anio || '-' || LPAD(v_correlativo::TEXT, 4, '0');

    WHILE EXISTS (SELECT 1 FROM obras.t_orden_compra WHERE id_empresa = p_id_empresa AND numero_orden = v_numero) LOOP
        v_correlativo := v_correlativo + 1;
        v_numero := 'OC-' || v_anio || '-' || LPAD(v_correlativo::TEXT, 4, '0');
    END LOOP;

    RETURN v_numero;
END;
$function$
```

</details>

## 34. fn_generar_numero_recepcion

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: t_recepcion_compra.
- Referencias Python: sin coincidencia.
- Scripts con CREATE del nombre: backend\database\migration_compras_recepcion.sql.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.fn_generar_numero_recepcion(p_id_empresa integer)
 RETURNS character varying
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_anio VARCHAR(4);
    v_correlativo INT;
    v_numero VARCHAR(50);
BEGIN
    v_anio := TO_CHAR(CURRENT_DATE, 'YYYY');
    SELECT COALESCE(COUNT(*), 0) + 1 INTO v_correlativo
    FROM obras.t_recepcion_compra
    WHERE id_empresa = p_id_empresa
      AND TO_CHAR(fecha_recepcion, 'YYYY') = v_anio;

    v_numero := 'REC-' || v_anio || '-' || LPAD(v_correlativo::TEXT, 4, '0');

    WHILE EXISTS (SELECT 1 FROM obras.t_recepcion_compra WHERE id_empresa = p_id_empresa AND numero_recepcion = v_numero) LOOP
        v_correlativo := v_correlativo + 1;
        v_numero := 'REC-' || v_anio || '-' || LPAD(v_correlativo::TEXT, 4, '0');
    END LOOP;

    RETURN v_numero;
END;
$function$
```

</details>

## 35. fn_listar_avances_obra

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: t_obra, t_orden_trabajo, t_orden_trabajo_usuario, t_persona, t_usuario.
- Referencias Python: sin coincidencia.
- Scripts con CREATE del nombre: **no localizado en los SQL versionados revisados**.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.fn_listar_avances_obra(p_id_obra integer, p_id_empresa integer, p_estado character varying DEFAULT NULL::character varying)
 RETURNS json
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_obra_valida   BOOLEAN;
    v_total_ordenes INTEGER := 0;
    v_ordenes_json  JSON;
BEGIN
    -- Validar obra
    SELECT EXISTS(
        SELECT 1 FROM obras.t_obra
        WHERE id_obra = p_id_obra
          AND (id_empresa = p_id_empresa OR p_id_empresa IS NULL)
    ) INTO v_obra_valida;

    IF NOT v_obra_valida THEN
        RETURN json_build_object(
            'success', false,
            'error', 'El proyecto no existe o no pertenece a su empresa.'
        );
    END IF;

    -- Conteo total para calcular peso porcentual
    SELECT COUNT(*) INTO v_total_ordenes
    FROM obras.t_orden_trabajo
    WHERE id_obra = p_id_obra;

    SELECT COALESCE(json_agg(
        json_build_object(
            'orden_nro',         sub.orden_nro,
            'id_obra',           sub.id_obra,
            'tipo_trab',         sub.tipo_trab,
            'cuadrilla',         sub.cuadrilla,
            'estado',            sub.estado,
            'es_cumplida',       (UPPER(sub.estado) = 'FINALIZADO'),
            'fecha_inicio',      sub.fecha_inicio,
            'fecha_fin',         sub.fecha_fin,
            'observacion',       sub.observacion,
            'peso_porcentual',   CASE 
                                     WHEN v_total_ordenes > 0 
                                     THEN ROUND(100.0 / v_total_ordenes::NUMERIC, 2) 
                                     ELSE 0 
                                 END,
            'responsables',      sub.responsables
        )
        ORDER BY 
            CASE WHEN UPPER(sub.estado) = 'FINALIZADO' THEN 1 ELSE 0 END ASC,
            sub.orden_nro ASC
    ), '[]'::json)
    INTO v_ordenes_json
    FROM (
        SELECT
            ot.orden_nro,
            ot.id_obra,
            ot.tipo_trab,
            ot.cuadrilla,
            ot.estado,
            ot.fecha_inicio,
            ot.fecha_fin,
            ot.observacion,
            COALESCE(
                json_agg(
                    json_build_object(
                        'id_usuario',      u.id_usuario,
                        'username',        u.username,
                        'nombre_completo', COALESCE(p.nombre_completo, u.username)
                    )
                ) FILTER (WHERE u.id_usuario IS NOT NULL),
                '[]'::json
            ) AS responsables
        FROM obras.t_orden_trabajo ot
        LEFT JOIN obras.t_orden_trabajo_usuario otu ON otu.id_orden_trabajo = ot.orden_nro
        LEFT JOIN obras.t_usuario u                 ON u.id_usuario = otu.id_usuario
        LEFT JOIN obras.t_persona p                 ON p.id_persona = u.id_persona
        WHERE ot.id_obra = p_id_obra
          AND (
              p_estado IS NULL 
              OR (UPPER(p_estado) = 'FINALIZADO' AND UPPER(ot.estado) = 'FINALIZADO')
              OR (UPPER(p_estado) = 'PENDIENTE'  AND UPPER(ot.estado) != 'FINALIZADO')
          )
        GROUP BY ot.orden_nro, ot.id_obra, ot.tipo_trab, ot.cuadrilla, ot.estado, ot.fecha_inicio, ot.fecha_fin, ot.observacion
    ) sub;

    RETURN json_build_object(
        'success', true,
        'data',    v_ordenes_json
    );
END;
$function$
```

</details>

## 36. fn_listar_avances_obra

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: t_avance_obra, t_estructura_obra, t_obra, t_persona, t_unidad_construccion, t_usuario.
- Referencias Python: sin coincidencia.
- Scripts con CREATE del nombre: **no localizado en los SQL versionados revisados**.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.fn_listar_avances_obra(p_id_obra integer, p_id_empresa integer, p_id_unidad integer DEFAULT NULL::integer)
 RETURNS json
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_obra_valida BOOLEAN;
    v_avances     JSON;
BEGIN
    -- Validar obra
    SELECT EXISTS(
        SELECT 1 FROM obras.t_obra
        WHERE id_obra = p_id_obra
          AND (id_empresa = p_id_empresa OR p_id_empresa IS NULL)
    ) INTO v_obra_valida;

    IF NOT v_obra_valida THEN
        RETURN json_build_object(
            'success', false,
            'error', 'El proyecto no existe o no pertenece a su empresa.'
        );
    END IF;

    SELECT COALESCE(json_agg(
        json_build_object(
            'id_avance',          a.id_avance,
            'id_obra',            a.id_obra,
            'id_unidad',          a.id_unidad,
            'codigo_unidad',      u.codigo,
            'nombre_unidad',      e.nombre,
            'tipo_unidad',        u.tipo_unidad,
            'estado_unidad',      u.estado,
            'porcentaje_avance',  a.porcentaje_avance,
            'fecha_registro',     a.fecha_registro,
            'observacion',        a.observacion,
            'id_usuario',         a.id_usuario,
            'usuario_nombre',     COALESCE(
                                      p.nombre_completo,
                                      us.username,
                                      'Usuario ' || a.id_usuario::text
                                  ),
            'created_at',         a.created_at
        )
        ORDER BY a.created_at DESC
    ), '[]'::json)
    INTO v_avances
    FROM obras.t_avance_obra a
    INNER JOIN obras.t_unidad_construccion u ON u.id_unidad = a.id_unidad
    INNER JOIN obras.t_estructura_obra e ON e.id_estructura = u.id_estructura
    LEFT  JOIN obras.t_usuario us ON us.id_usuario = a.id_usuario
    LEFT  JOIN obras.t_persona p  ON p.id_persona = us.id_persona
    WHERE a.id_obra = p_id_obra
      AND (p_id_unidad IS NULL OR a.id_unidad = p_id_unidad);

    RETURN json_build_object(
        'success', true,
        'data',    v_avances
    );
END;
$function$
```

</details>

## 37. fn_listar_detalles_orden_compra

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: t_material, t_orden_compra_detalle, t_unidad_medida.
- Referencias Python: backend\app\repos\compras_repos.py.
- Scripts con CREATE del nombre: backend\database\migration_compras_recepcion.sql.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.fn_listar_detalles_orden_compra(p_id_orden_compra integer)
 RETURNS TABLE(id_detalle integer, id_material integer, codigo_material character varying, nombre_material character varying, unidad_abreviatura character varying, cantidad_solicitada numeric, precio_unitario numeric, subtotal numeric, cantidad_recibida numeric, cantidad_pendiente numeric)
 LANGUAGE plpgsql
AS $function$
BEGIN
    RETURN QUERY
    SELECT 
        d.id_detalle,
        d.id_material,
        m.codigo AS codigo_material,
        m.nombre_material,
        um.abreviatura AS unidad_abreviatura,
        d.cantidad_solicitada,
        d.precio_unitario,
        d.subtotal,
        d.cantidad_recibida,
        (d.cantidad_solicitada - d.cantidad_recibida)::NUMERIC AS cantidad_pendiente
    FROM obras.t_orden_compra_detalle d
    JOIN obras.t_material m ON m.id_material = d.id_material
    JOIN obras.t_unidad_medida um ON um.id_unidad_medida = m.id_unidad_medida
    WHERE d.id_orden_compra = p_id_orden_compra
    ORDER BY d.id_detalle ASC;
END;
$function$
```

</details>

## 38. fn_listar_estructura_obra

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: t_estructura_obra, t_obra.
- Referencias Python: backend\app\repos\estructura_repos.py.
- Scripts con CREATE del nombre: backend\database\migration_hu35_estructura.sql.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.fn_listar_estructura_obra(p_id_obra integer, p_id_empresa integer)
 RETURNS json
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_nodos json;
    v_obra_valida boolean;
BEGIN
    -- Validar que la obra exista y pertenezca al Tenant
    SELECT EXISTS(
        SELECT 1 FROM obras.t_obra 
        WHERE id_obra = p_id_obra AND (id_empresa = p_id_empresa OR p_id_empresa IS NULL)
    ) INTO v_obra_valida;

    IF NOT v_obra_valida THEN
        RETURN json_build_object(
            'success', false,
            'error', 'El proyecto no existe o no pertenece a su empresa.'
        );
    END IF;

    SELECT COALESCE(json_agg(
        json_build_object(
            'id_estructura', sub.id_estructura,
            'id_obra', sub.id_obra,
            'id_padre', sub.id_padre,
            'nombre', sub.nombre,
            'tipo', sub.tipo,
            'descripcion', sub.descripcion,
            'orden', sub.orden,
            'created_at', sub.created_at,
            'updated_at', sub.updated_at
        )
    ), '[]'::json)
    INTO v_nodos
    FROM (
        SELECT id_estructura, id_obra, id_padre, nombre, tipo, descripcion, orden, created_at, updated_at
        FROM obras.t_estructura_obra
        WHERE id_obra = p_id_obra
        ORDER BY id_padre ASC NULLS FIRST, orden ASC, id_estructura ASC
    ) sub;

    RETURN json_build_object(
        'success', true,
        'data', v_nodos
    );
END;
$function$
```

</details>

## 39. fn_listar_inventario_empresa

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: t_categoria_material, t_empresa, t_material, t_materiales_almacen, t_unidad_medida.
- Referencias Python: backend\app\repos\inventario_repos.py.
- Scripts con CREATE del nombre: backend\database\migration_inventario.sql.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.fn_listar_inventario_empresa(p_id_empresa integer, p_id_categoria integer DEFAULT NULL::integer, p_estado_stock character varying DEFAULT NULL::character varying, p_q character varying DEFAULT NULL::character varying, p_limit integer DEFAULT 50, p_offset integer DEFAULT 0)
 RETURNS TABLE(id_material integer, codigo character varying, nombre_material character varying, descripcion text, id_categoria integer, categoria_nombre character varying, id_unidad_medida integer, unidad_nombre character varying, unidad_abreviatura character varying, precio numeric, stock_actual numeric, stock_minimo numeric, valor_total numeric, estado_stock character varying, id_empresa integer, nombre_empresa character varying, total_count bigint)
 LANGUAGE plpgsql
AS $function$
BEGIN
    RETURN QUERY
    WITH base_materiales AS (
        SELECT 
            m.id_material,
            m.codigo,
            m.nombre_material,
            m.descripcion,
            m.id_categoria,
            c.nombre AS categoria_nombre,
            m.id_unidad_medida,
            um.nombre AS unidad_nombre,
            um.abreviatura AS unidad_abreviatura,
            m.precio,
            COALESCE(SUM(ma.cantidad_actual), 0.00)::NUMERIC(15,3) AS stock_actual,
            COALESCE(MAX(ma.stock_minimo), 0.00)::NUMERIC(15,3) AS stock_minimo,
            ROUND(COALESCE(SUM(ma.cantidad_actual), 0.00) * m.precio, 2)::NUMERIC(15,2) AS valor_total,
            CASE 
                WHEN COALESCE(SUM(ma.cantidad_actual), 0.00) <= 0 THEN 'SIN_STOCK'
                WHEN COALESCE(SUM(ma.cantidad_actual), 0.00) <= COALESCE(MAX(ma.stock_minimo), 0.00) THEN 'STOCK_BAJO'
                ELSE 'EN_STOCK'
            END::VARCHAR(20) AS estado_stock,
            m.id_empresa,
            e.nombre_empresa
        FROM obras.t_material m
        JOIN obras.t_categoria_material c ON c.id_categoria = m.id_categoria
        JOIN obras.t_unidad_medida um ON um.id_unidad_medida = m.id_unidad_medida
        JOIN obras.t_empresa e ON e.id_empresa = m.id_empresa
        LEFT JOIN obras.t_materiales_almacen ma ON ma.id_material = m.id_material
        WHERE (p_id_empresa IS NULL OR m.id_empresa = p_id_empresa)
          AND m.estado = 'ACTIVO'
          AND (p_id_categoria IS NULL OR m.id_categoria = p_id_categoria)
          AND (
              p_q IS NULL 
              OR m.codigo ILIKE '%' || p_q || '%' 
              OR m.nombre_material ILIKE '%' || p_q || '%'
          )
        GROUP BY m.id_material, m.codigo, m.nombre_material, m.descripcion,
                 m.id_categoria, c.nombre, m.id_unidad_medida, um.nombre,
                 um.abreviatura, m.precio, m.id_empresa, e.nombre_empresa
    ),
    filtrados AS (
        SELECT * FROM base_materiales bm
        WHERE (
            p_estado_stock IS NULL 
            OR p_estado_stock = 'TODOS' 
            OR bm.estado_stock = p_estado_stock
        )
    )
    SELECT 
        f.id_material,
        f.codigo,
        f.nombre_material,
        f.descripcion,
        f.id_categoria,
        f.categoria_nombre,
        f.id_unidad_medida,
        f.unidad_nombre,
        f.unidad_abreviatura,
        f.precio,
        f.stock_actual,
        f.stock_minimo,
        f.valor_total,
        f.estado_stock,
        f.id_empresa,
        f.nombre_empresa,
        COUNT(*) OVER() AS total_count
    FROM filtrados f
    ORDER BY 
        CASE f.estado_stock
            WHEN 'STOCK_BAJO' THEN 1
            WHEN 'EN_STOCK' THEN 2
            ELSE 3
        END,
        f.stock_actual DESC,
        f.nombre_material ASC
    LIMIT p_limit OFFSET p_offset;
END;
$function$
```

</details>

## 40. fn_listar_materiales_empresa

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: t_categoria_material, t_empresa, t_material, t_unidad_medida.
- Referencias Python: backend\app\repos\material_repos.py.
- Scripts con CREATE del nombre: backend\database\migration_refactor_materiales.sql.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.fn_listar_materiales_empresa(p_id_empresa integer, p_q character varying DEFAULT NULL::character varying, p_id_categoria integer DEFAULT NULL::integer, p_estado character varying DEFAULT NULL::character varying, p_limit integer DEFAULT 50, p_offset integer DEFAULT 0)
 RETURNS TABLE(id_material integer, codigo character varying, nombre_material character varying, descripcion text, id_categoria integer, categoria_nombre character varying, id_unidad_medida integer, unidad_nombre character varying, unidad_abreviatura character varying, precio numeric, estado character varying, id_empresa integer, nombre_empresa character varying, id_material_base integer, es_propio boolean, created_at timestamp with time zone, updated_at timestamp with time zone, total_count bigint)
 LANGUAGE plpgsql
AS $function$
BEGIN
    RETURN QUERY
    WITH filtrados AS (
        SELECT 
            m.id_material,
            m.codigo,
            m.nombre_material,
            m.descripcion,
            m.id_categoria,
            c.nombre AS categoria_nombre,
            m.id_unidad_medida,
            um.nombre AS unidad_nombre,
            um.abreviatura AS unidad_abreviatura,
            m.precio,
            m.estado,
            m.id_empresa,
            e.nombre_empresa,
            m.id_material_base,
            m.es_propio,
            m.created_at,
            m.updated_at
        FROM obras.t_material m
        JOIN obras.t_categoria_material c ON c.id_categoria = m.id_categoria
        JOIN obras.t_unidad_medida um ON um.id_unidad_medida = m.id_unidad_medida
        JOIN obras.t_empresa e ON e.id_empresa = m.id_empresa
        WHERE (p_id_empresa IS NULL OR m.id_empresa = p_id_empresa)
          AND (p_id_categoria IS NULL OR m.id_categoria = p_id_categoria)
          AND (p_estado IS NULL OR m.estado = p_estado)
          AND (
              p_q IS NULL 
              OR m.codigo ILIKE '%' || p_q || '%' 
              OR m.nombre_material ILIKE '%' || p_q || '%'
          )
    )
    SELECT 
        f.*,
        COUNT(*) OVER() AS total_count
    FROM filtrados f
    ORDER BY f.nombre_material ASC, f.id_material ASC
    LIMIT p_limit OFFSET p_offset;
END;
$function$
```

</details>

## 41. fn_listar_movimientos_almacen

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: t_material, t_movimiento_almacen, t_orden_compra, t_persona, t_recepcion_compra, t_unidad_medida, t_usuario.
- Referencias Python: backend\app\repos\inventario_repos.py.
- Scripts con CREATE del nombre: backend\database\migration_inventario.sql.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.fn_listar_movimientos_almacen(p_id_empresa integer, p_id_material integer DEFAULT NULL::integer, p_tipo_movimiento character varying DEFAULT NULL::character varying, p_limit integer DEFAULT 50, p_offset integer DEFAULT 0)
 RETURNS TABLE(id_movimiento integer, fecha_movimiento date, created_at timestamp with time zone, tipo_movimiento character varying, cantidad_asignada numeric, id_material integer, material_codigo character varying, material_nombre character varying, unidad_abreviatura character varying, id_orden_compra integer, numero_orden character varying, id_recepcion integer, numero_recepcion character varying, id_usuario integer, nombre_usuario character varying, observaciones text, total_count bigint)
 LANGUAGE plpgsql
AS $function$
BEGIN
    RETURN QUERY
    WITH base_movs AS (
        SELECT 
            mov.id_movimiento,
            mov.fecha_movimiento,
            mov.created_at,
            mov.tipo_movimiento,
            mov.cantidad_asignada,
            mov.id_material,
            m.codigo AS material_codigo,
            m.nombre_material AS material_nombre,
            um.abreviatura AS unidad_abreviatura,
            mov.id_orden_compra,
            oc.numero_orden,
            mov.id_recepcion,
            rc.numero_recepcion,
            mov.id_usuario,
            COALESCE(p.nombre_completo, u.username, 'Sistema')::VARCHAR AS nombre_usuario,
            mov.observaciones
        FROM obras.t_movimiento_almacen mov
        JOIN obras.t_material m ON m.id_material = mov.id_material
        JOIN obras.t_unidad_medida um ON um.id_unidad_medida = m.id_unidad_medida
        LEFT JOIN obras.t_orden_compra oc ON oc.id_orden_compra = mov.id_orden_compra
        LEFT JOIN obras.t_recepcion_compra rc ON rc.id_recepcion = mov.id_recepcion
        LEFT JOIN obras.t_usuario u ON u.id_usuario = mov.id_usuario
        LEFT JOIN obras.t_persona p ON p.id_persona = u.id_persona
        WHERE mov.id_empresa = p_id_empresa
          AND (p_id_material IS NULL OR mov.id_material = p_id_material)
          AND (p_tipo_movimiento IS NULL OR mov.tipo_movimiento = p_tipo_movimiento)
    )
    SELECT 
        bm.*,
        COUNT(*) OVER() AS total_count
    FROM base_movs bm
    ORDER BY bm.created_at DESC, bm.id_movimiento DESC
    LIMIT p_limit OFFSET p_offset;
END;
$function$
```

</details>

## 42. fn_listar_ordenes_compra

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: t_empresa, t_orden_compra, t_orden_compra_detalle, t_persona, t_proveedor, t_usuario.
- Referencias Python: backend\app\repos\compras_repos.py.
- Scripts con CREATE del nombre: backend\database\migration_compras_recepcion.sql.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.fn_listar_ordenes_compra(p_id_empresa integer, p_q character varying DEFAULT NULL::character varying, p_estado character varying DEFAULT NULL::character varying, p_id_proveedor integer DEFAULT NULL::integer, p_limit integer DEFAULT 20, p_offset integer DEFAULT 0)
 RETURNS TABLE(id_orden_compra integer, numero_orden character varying, fecha date, observaciones text, estado character varying, id_empresa integer, nombre_empresa character varying, id_proveedor integer, nombre_proveedor character varying, id_usuario_solicitante integer, nombre_solicitante character varying, subtotal numeric, total numeric, items_count bigint, items_recibidos_count bigint, created_at timestamp with time zone, updated_at timestamp with time zone, total_count bigint)
 LANGUAGE plpgsql
AS $function$
BEGIN
    RETURN QUERY
    WITH filtrados AS (
        SELECT 
            oc.id_orden_compra,
            oc.numero_orden,
            oc.fecha,
            oc.observaciones,
            oc.estado,
            oc.id_empresa,
            e.nombre_empresa,
            oc.id_proveedor,
            p.nombre AS nombre_proveedor,
            oc.id_usuario_solicitante,
            COALESCE(pers_sol.nombre_completo, u_sol.username)::VARCHAR AS nombre_solicitante,
            oc.subtotal,
            oc.total,
            COUNT(d.id_detalle) AS items_count,
            COUNT(CASE WHEN d.cantidad_recibida >= d.cantidad_solicitada THEN 1 ELSE NULL END) AS items_recibidos_count,
            oc.created_at,
            oc.updated_at
        FROM obras.t_orden_compra oc
        JOIN obras.t_empresa e ON e.id_empresa = oc.id_empresa
        JOIN obras.t_proveedor p ON p.id_proveedor = oc.id_proveedor
        JOIN obras.t_usuario u_sol ON u_sol.id_usuario = oc.id_usuario_solicitante
        LEFT JOIN obras.t_persona pers_sol ON pers_sol.id_persona = u_sol.id_persona
        LEFT JOIN obras.t_orden_compra_detalle d ON d.id_orden_compra = oc.id_orden_compra
        WHERE (p_id_empresa IS NULL OR oc.id_empresa = p_id_empresa)
          AND (p_estado IS NULL OR oc.estado = p_estado)
          AND (p_id_proveedor IS NULL OR oc.id_proveedor = p_id_proveedor)
          AND (
              p_q IS NULL 
              OR oc.numero_orden ILIKE '%' || p_q || '%' 
              OR p.nombre ILIKE '%' || p_q || '%'
          )
        GROUP BY oc.id_orden_compra, oc.numero_orden, oc.fecha, oc.observaciones, oc.estado,
                 oc.id_empresa, e.nombre_empresa, oc.id_proveedor, p.nombre,
                 oc.id_usuario_solicitante, pers_sol.nombre_completo, u_sol.username,
                 oc.subtotal, oc.total, oc.created_at, oc.updated_at
    )
    SELECT 
        f.*,
        COUNT(*) OVER() AS total_count
    FROM filtrados f
    ORDER BY f.id_orden_compra DESC
    LIMIT p_limit OFFSET p_offset;
END;
$function$
```

</details>

## 43. fn_listar_recepciones_orden

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: t_persona, t_recepcion_compra, t_recepcion_compra_detalle, t_usuario.
- Referencias Python: backend\app\repos\compras_repos.py.
- Scripts con CREATE del nombre: backend\database\migration_compras_recepcion.sql.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.fn_listar_recepciones_orden(p_id_orden_compra integer)
 RETURNS TABLE(id_recepcion integer, numero_recepcion character varying, fecha_recepcion timestamp with time zone, id_usuario_recepcion integer, nombre_usuario_recepcion character varying, observaciones text, total_items_recibidos bigint)
 LANGUAGE plpgsql
AS $function$
BEGIN
    RETURN QUERY
    SELECT 
        r.id_recepcion,
        r.numero_recepcion,
        r.fecha_recepcion,
        r.id_usuario_recepcion,
        COALESCE(pers.nombre_completo, u.username)::VARCHAR AS nombre_usuario_recepcion,
        r.observaciones,
        COUNT(rd.id_recepcion_detalle) AS total_items_recibidos
    FROM obras.t_recepcion_compra r
    JOIN obras.t_usuario u ON u.id_usuario = r.id_usuario_recepcion
    LEFT JOIN obras.t_persona pers ON pers.id_persona = u.id_persona
    LEFT JOIN obras.t_recepcion_compra_detalle rd ON rd.id_recepcion = r.id_recepcion
    WHERE r.id_orden_compra = p_id_orden_compra
    GROUP BY r.id_recepcion, r.numero_recepcion, r.fecha_recepcion, r.id_usuario_recepcion, pers.nombre_completo, u.username, r.observaciones
    ORDER BY r.fecha_recepcion DESC;
END;
$function$
```

</details>

## 44. fn_material_updated_at

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: ninguna coincidencia.
- Referencias Python: sin coincidencia.
- Scripts con CREATE del nombre: backend\database\migration_refactor_materiales.sql.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.fn_material_updated_at()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$function$
```

</details>

## 45. fn_modificar_material

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: t_material.
- Referencias Python: backend\app\repos\material_repos.py.
- Scripts con CREATE del nombre: backend\database\migration_refactor_materiales.sql.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.fn_modificar_material(p_id_empresa integer, p_id_material integer, p_codigo character varying, p_nombre_material character varying, p_descripcion text, p_id_categoria integer, p_id_unidad_medida integer, p_precio numeric)
 RETURNS boolean
 LANGUAGE plpgsql
AS $function$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM obras.t_material WHERE id_material = p_id_material AND id_empresa = p_id_empresa) THEN
        RAISE EXCEPTION 'Material no encontrado o no pertenece a la empresa %', p_id_empresa;
    END IF;

    IF TRIM(COALESCE(p_codigo, '')) = '' THEN
        RAISE EXCEPTION 'El código del material es obligatorio';
    END IF;

    IF TRIM(COALESCE(p_nombre_material, '')) = '' THEN
        RAISE EXCEPTION 'El nombre del material es obligatorio';
    END IF;

    IF EXISTS (
        SELECT 1 FROM obras.t_material 
        WHERE id_empresa = p_id_empresa 
          AND LOWER(TRIM(codigo)) = LOWER(TRIM(p_codigo)) 
          AND id_material <> p_id_material
    ) THEN
        RAISE EXCEPTION 'El código % ya está asignado a otro material en esta empresa', p_codigo;
    END IF;

    UPDATE obras.t_material
    SET codigo = TRIM(p_codigo),
        nombre_material = TRIM(p_nombre_material),
        descripcion = NULLIF(TRIM(p_descripcion), ''),
        id_categoria = p_id_categoria,
        id_unidad_medida = p_id_unidad_medida,
        precio = COALESCE(p_precio, precio),
        updated_at = CURRENT_TIMESTAMP
    WHERE id_material = p_id_material
      AND id_empresa = p_id_empresa;

    RETURN TRUE;
END;
$function$
```

</details>

## 46. fn_orden_compra_updated_at

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: ninguna coincidencia.
- Referencias Python: sin coincidencia.
- Scripts con CREATE del nombre: backend\database\migration_compras_recepcion.sql.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.fn_orden_compra_updated_at()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$function$
```

</details>

## 47. fn_proteger_unidades_estructura

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: t_estructura_obra, t_unidad_construccion.
- Referencias Python: sin coincidencia.
- Scripts con CREATE del nombre: backend\database\migration_cu12_unidades_construccion.sql.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.fn_proteger_unidades_estructura()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
    IF EXISTS (
        WITH RECURSIVE descendientes AS (
            SELECT OLD.id_estructura AS id_estructura
            UNION ALL
            SELECT e.id_estructura
            FROM obras.t_estructura_obra e
            JOIN descendientes d ON e.id_padre = d.id_estructura
        )
        SELECT 1 FROM descendientes d
        JOIN obras.t_unidad_construccion u ON u.id_estructura = d.id_estructura
    ) THEN
        RAISE EXCEPTION 'No se puede eliminar: el elemento o uno de sus descendientes representa una unidad de construcción.';
    END IF;
    RETURN OLD;
END;
$function$
```

</details>

## 48. fn_recalcular_apu_materiales

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: t_analisi_precio_unitario_insumo, t_analisis_precio_unitario.
- Referencias Python: sin coincidencia.
- Scripts con CREATE del nombre: backend\database\migration_apu_materiales_y_presupuestos.sql.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.fn_recalcular_apu_materiales()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
DECLARE v_apu INTEGER;
BEGIN
    IF TG_OP = 'DELETE' THEN
        v_apu := OLD.id_analisis_precio_unitario;
    ELSE
        v_apu := NEW.id_analisis_precio_unitario;
    END IF;
    UPDATE obras.t_analisis_precio_unitario a
    SET costo_materiales = COALESCE((
        SELECT SUM(i.subtotal)
        FROM obras.t_analisi_precio_unitario_insumo i
        WHERE i.id_analisis_precio_unitario = v_apu
    ), 0)
    WHERE a.id_analisis_precio_unitario = v_apu;
    RETURN COALESCE(NEW, OLD);
END;
$function$
```

</details>

## 49. fn_recalcular_monto_estimacion

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: t_estimacion, t_estimacion_analisis_precio_unitario.
- Referencias Python: sin coincidencia.
- Scripts con CREATE del nombre: backend\database\migration_apu_materiales_y_presupuestos.sql.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.fn_recalcular_monto_estimacion()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
DECLARE v_estimacion INTEGER;
BEGIN
    IF TG_OP = 'DELETE' THEN
        v_estimacion := OLD.id_estimacion;
    ELSE
        v_estimacion := NEW.id_estimacion;
    END IF;
    UPDATE obras.t_estimacion e
    SET monto_total = COALESCE((
        SELECT SUM(d.precio_total)
        FROM obras.t_estimacion_analisis_precio_unitario d
        WHERE d.id_estimacion = v_estimacion
    ), 0)
    WHERE e.id_estimacion = v_estimacion;
    RETURN COALESCE(NEW, OLD);
END;
$function$
```

</details>

## 50. fn_registrar_ajuste_inventario

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: t_material, t_materiales_almacen, t_movimiento_almacen.
- Referencias Python: backend\app\repos\inventario_repos.py.
- Scripts con CREATE del nombre: backend\database\migration_inventario.sql.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.fn_registrar_ajuste_inventario(p_id_empresa integer, p_id_material integer, p_cantidad numeric, p_tipo_movimiento character varying, p_id_usuario integer, p_observaciones text, p_stock_minimo numeric DEFAULT NULL::numeric)
 RETURNS TABLE(id_material integer, nuevo_stock numeric, stock_minimo numeric, id_movimiento integer)
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_lote_id INT;
    v_stock_actual NUMERIC(15,3) := 0.00;
    v_nuevo_stock NUMERIC(15,3) := 0.00;
    v_stock_min NUMERIC(15,3) := 0.00;
    v_mov_id INT := NULL;
    v_mat_empresa INT;
BEGIN
    -- Verificar que el material pertenezca a la empresa
    SELECT id_empresa INTO v_mat_empresa
    FROM obras.t_material
    WHERE obras.t_material.id_material = p_id_material;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'El material ID % no existe.', p_id_material;
    END IF;

    IF v_mat_empresa <> p_id_empresa THEN
        RAISE EXCEPTION 'El material no pertenece a la empresa indicada.';
    END IF;

    -- Buscar lote existente
    SELECT id_lote, cantidad_actual, obras.t_materiales_almacen.stock_minimo
    INTO v_lote_id, v_stock_actual, v_stock_min
    FROM obras.t_materiales_almacen
    WHERE obras.t_materiales_almacen.id_material = p_id_material
    LIMIT 1;

    -- Actualizar stock_minimo si fue provisto
    IF p_stock_minimo IS NOT NULL THEN
        v_stock_min := p_stock_minimo;
    END IF;

    IF v_lote_id IS NOT NULL THEN
        -- Calcular nuevo stock según tipo de ajuste
        IF p_tipo_movimiento = 'CONTEO_FISICO' THEN
            v_nuevo_stock := GREATEST(0.00, p_cantidad);
        ELSIF p_tipo_movimiento LIKE 'SALIDA%' THEN
            v_nuevo_stock := GREATEST(0.00, v_stock_actual - ABS(p_cantidad));
        ELSE -- ENTRADA o incremento
            v_nuevo_stock := v_stock_actual + ABS(p_cantidad);
        END IF;

        UPDATE obras.t_materiales_almacen
        SET cantidad_actual = v_nuevo_stock,
            stock_minimo = v_stock_min
        WHERE id_lote = v_lote_id;
    ELSE
        -- Crear lote inicial
        IF p_tipo_movimiento LIKE 'SALIDA%' THEN
            v_nuevo_stock := 0.00;
        ELSE
            v_nuevo_stock := GREATEST(0.00, p_cantidad);
        END IF;

        INSERT INTO obras.t_materiales_almacen (
            id_material,
            cantidad_inicial,
            cantidad_actual,
            precio_venta,
            fecha_ingreso,
            stock_minimo
        ) VALUES (
            p_id_material,
            v_nuevo_stock,
            v_nuevo_stock,
            0.00,
            CURRENT_DATE,
            v_stock_min
        ) RETURNING id_lote INTO v_lote_id;
    END IF;

    -- Registrar movimiento auditado si la cantidad es diferente de 0
    IF p_cantidad <> 0 THEN
        INSERT INTO obras.t_movimiento_almacen (
            id_lote,
            id_material,
            orden_nro,
            cantidad_asignada,
            fecha_movimiento,
            tipo_movimiento,
            id_empresa,
            id_usuario,
            observaciones,
            created_at
        ) VALUES (
            v_lote_id,
            p_id_material,
            NULL,
            p_cantidad,
            CURRENT_DATE,
            COALESCE(p_tipo_movimiento, 'AJUSTE_MANUAL'),
            p_id_empresa,
            p_id_usuario,
            p_observaciones,
            CURRENT_TIMESTAMP
        ) RETURNING obras.t_movimiento_almacen.id_movimiento INTO v_mov_id;
    END IF;

    RETURN QUERY
    SELECT p_id_material, v_nuevo_stock, v_stock_min, v_mov_id;
END;
$function$
```

</details>

## 51. fn_registrar_avance_obra

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: t_avance_obra, t_estructura_obra, t_obra, t_unidad_construccion.
- Referencias Python: sin coincidencia.
- Scripts con CREATE del nombre: **no localizado en los SQL versionados revisados**.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.fn_registrar_avance_obra(p_id_obra integer, p_id_unidad integer, p_id_empresa integer, p_porcentaje numeric, p_fecha_registro date, p_observacion text, p_id_usuario integer)
 RETURNS json
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_obra_valida   BOOLEAN;
    v_unidad_valida BOOLEAN;
    v_id_avance     INTEGER;
    v_nuevo_estado  VARCHAR(30);
BEGIN
    -- Validar que la obra exista y pertenezca a la empresa
    SELECT EXISTS(
        SELECT 1 FROM obras.t_obra
        WHERE id_obra = p_id_obra
          AND (id_empresa = p_id_empresa OR p_id_empresa IS NULL)
    ) INTO v_obra_valida;

    IF NOT v_obra_valida THEN
        RETURN json_build_object(
            'success', false,
            'error', 'El proyecto no existe o no pertenece a su empresa.'
        );
    END IF;

    -- Validar que la unidad pertenezca a la obra
    SELECT EXISTS(
        SELECT 1
        FROM obras.t_unidad_construccion u
        INNER JOIN obras.t_estructura_obra e ON e.id_estructura = u.id_estructura
        WHERE u.id_unidad = p_id_unidad AND e.id_obra = p_id_obra
    ) INTO v_unidad_valida;

    IF NOT v_unidad_valida THEN
        RETURN json_build_object(
            'success', false,
            'error', 'La unidad de construcción no pertenece al proyecto especificado.'
        );
    END IF;

    -- Validar rango de porcentaje
    IF p_porcentaje < 0 OR p_porcentaje > 100 THEN
        RETURN json_build_object(
            'success', false,
            'error', 'El porcentaje de avance debe estar entre 0 y 100.'
        );
    END IF;

    -- Insertar el avance
    INSERT INTO obras.t_avance_obra (
        id_obra, id_unidad, porcentaje_avance, fecha_registro, observacion, id_usuario
    ) VALUES (
        p_id_obra, p_id_unidad, p_porcentaje, COALESCE(p_fecha_registro, CURRENT_DATE),
        TRIM(COALESCE(p_observacion, '')), p_id_usuario
    ) RETURNING id_avance INTO v_id_avance;

    -- Actualizar automáticamente el estado de la unidad según el porcentaje
    IF p_porcentaje = 100 THEN
        v_nuevo_estado := 'FINALIZADO';
    ELSIF p_porcentaje > 0 THEN
        v_nuevo_estado := 'EN_CONSTRUCCION';
    ELSE
        v_nuevo_estado := 'PLANIFICADO';
    END IF;

    UPDATE obras.t_unidad_construccion
    SET estado = v_nuevo_estado, updated_at = CURRENT_TIMESTAMP
    WHERE id_unidad = p_id_unidad;

    RETURN json_build_object(
        'success',    true,
        'id_avance',  v_id_avance,
        'message',    'Avance de obra registrado exitosamente.'
    );
EXCEPTION WHEN OTHERS THEN
    RETURN json_build_object('success', false, 'error', SQLERRM);
END;
$function$
```

</details>

## 52. fn_registrar_bitacora

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: t_bitacora.
- Referencias Python: backend\app\repos\bitacora_repos.py.
- Scripts con CREATE del nombre: **no localizado en los SQL versionados revisados**.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.fn_registrar_bitacora(p_id_usuario bigint, p_modulo character varying, p_accion character varying, p_descripcion character varying, p_ip character varying, p_estado character varying)
 RETURNS void
 LANGUAGE plpgsql
AS $function$
BEGIN
    INSERT INTO obras.t_bitacora
    (
        id_usuario,
        modulo,
        accion,
        descripcion,
        ip,
        estado,
        fecha_accion
    )
    VALUES
    (
        p_id_usuario,
        UPPER(p_modulo),
        UPPER(p_accion),
        p_descripcion,
        p_ip,
        UPPER(p_estado),
        CURRENT_TIMESTAMP
    );
END;
$function$
```

</details>

## 53. fn_registrar_estructura_obra

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: t_estructura_obra, t_obra.
- Referencias Python: backend\app\repos\estructura_repos.py.
- Scripts con CREATE del nombre: backend\database\migration_hu35_estructura.sql.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.fn_registrar_estructura_obra(p_id_obra integer, p_id_padre integer, p_nombre character varying, p_tipo character varying, p_descripcion text, p_orden integer, p_id_empresa integer)
 RETURNS json
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_obra_valida boolean;
    v_padre_valido boolean;
    v_orden_calculado integer;
    v_id_estructura integer;
BEGIN
    -- Validar obra
    SELECT EXISTS(
        SELECT 1 FROM obras.t_obra 
        WHERE id_obra = p_id_obra AND (id_empresa = p_id_empresa OR p_id_empresa IS NULL)
    ) INTO v_obra_valida;

    IF NOT v_obra_valida THEN
        RETURN json_build_object(
            'success', false,
            'error', 'El proyecto no existe o no pertenece a su empresa.'
        );
    END IF;

    -- Validar padre si fue suministrado
    IF p_id_padre IS NOT NULL THEN
        SELECT EXISTS(
            SELECT 1 FROM obras.t_estructura_obra
            WHERE id_estructura = p_id_padre AND id_obra = p_id_obra
        ) INTO v_padre_valido;

        IF NOT v_padre_valido THEN
            RETURN json_build_object(
                'success', false,
                'error', 'El elemento padre seleccionado no pertenece a este proyecto.'
            );
        END IF;
    END IF;

    -- Calcular orden si no viene especificado
    IF p_orden IS NULL OR p_orden <= 0 THEN
        SELECT COALESCE(MAX(orden), 0) + 1
        INTO v_orden_calculado
        FROM obras.t_estructura_obra
        WHERE id_obra = p_id_obra AND (
            (p_id_padre IS NULL AND id_padre IS NULL) OR 
            (p_id_padre IS NOT NULL AND id_padre = p_id_padre)
        );
    ELSE
        v_orden_calculado := p_orden;
    END IF;

    INSERT INTO obras.t_estructura_obra (
        id_obra, id_padre, nombre, tipo, descripcion, orden
    ) VALUES (
        p_id_obra, p_id_padre, TRIM(p_nombre), COALESCE(TRIM(p_tipo), 'Sector'), TRIM(p_descripcion), v_orden_calculado
    ) RETURNING id_estructura INTO v_id_estructura;

    RETURN json_build_object(
        'success', true,
        'id_estructura', v_id_estructura,
        'message', 'Elemento de estructura creado exitosamente.'
    );
EXCEPTION WHEN OTHERS THEN
    RETURN json_build_object(
        'success', false,
        'error', SQLERRM
    );
END;
$function$
```

</details>

## 54. fn_registrar_material

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: t_categoria_material, t_empresa, t_material, t_unidad_medida.
- Referencias Python: backend\app\repos\material_repos.py.
- Scripts con CREATE del nombre: backend\database\migration_refactor_materiales.sql.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.fn_registrar_material(p_id_empresa integer, p_codigo character varying, p_nombre_material character varying, p_descripcion text, p_id_categoria integer, p_id_unidad_medida integer, p_precio numeric, p_id_material_base integer DEFAULT NULL::integer, p_es_propio boolean DEFAULT true)
 RETURNS integer
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_id_material INT;
    v_es_propio BOOLEAN;
BEGIN
    IF p_id_empresa IS NULL THEN
        RAISE EXCEPTION 'El id_empresa es obligatorio';
    END IF;

    IF TRIM(COALESCE(p_codigo, '')) = '' THEN
        RAISE EXCEPTION 'El código del material es obligatorio';
    END IF;

    IF TRIM(COALESCE(p_nombre_material, '')) = '' THEN
        RAISE EXCEPTION 'El nombre del material es obligatorio';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM obras.t_empresa WHERE id_empresa = p_id_empresa) THEN
        RAISE EXCEPTION 'La empresa % no existe', p_id_empresa;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM obras.t_categoria_material WHERE id_categoria = p_id_categoria AND estado = 'ACTIVO') THEN
        RAISE EXCEPTION 'La categoría % no existe o no está activa', p_id_categoria;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM obras.t_unidad_medida WHERE id_unidad_medida = p_id_unidad_medida AND estado = 'ACTIVO') THEN
        RAISE EXCEPTION 'La unidad de medida % no existe o no está activa', p_id_unidad_medida;
    END IF;

    IF EXISTS (SELECT 1 FROM obras.t_material WHERE id_empresa = p_id_empresa AND LOWER(TRIM(codigo)) = LOWER(TRIM(p_codigo))) THEN
        RAISE EXCEPTION 'El código % ya existe en la empresa %', p_codigo, p_id_empresa;
    END IF;

    v_es_propio := CASE WHEN p_id_material_base IS NOT NULL THEN FALSE ELSE COALESCE(p_es_propio, TRUE) END;

    INSERT INTO obras.t_material (
        id_empresa,
        id_material_base,
        codigo,
        nombre_material,
        descripcion,
        id_categoria,
        id_unidad_medida,
        precio,
        estado,
        es_propio,
        created_at,
        updated_at
    ) VALUES (
        p_id_empresa,
        p_id_material_base,
        TRIM(p_codigo),
        TRIM(p_nombre_material),
        NULLIF(TRIM(p_descripcion), ''),
        p_id_categoria,
        p_id_unidad_medida,
        COALESCE(p_precio, 0),
        'ACTIVO',
        v_es_propio,
        CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP
    )
    RETURNING id_material INTO v_id_material;

    RETURN v_id_material;
END;
$function$
```

</details>

## 55. fn_registrar_orden_compra

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: t_empresa, t_material, t_orden_compra, t_orden_compra_detalle, t_proveedor.
- Referencias Python: backend\app\repos\compras_repos.py.
- Scripts con CREATE del nombre: backend\database\migration_compras_recepcion.sql.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.fn_registrar_orden_compra(p_id_empresa integer, p_id_proveedor integer, p_id_usuario integer, p_fecha date, p_observaciones text, p_estado character varying, p_items_json jsonb)
 RETURNS integer
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_id_orden INT;
    v_numero_orden VARCHAR(50);
    v_total NUMERIC(15,2) := 0.00;
    v_item RECORD;
    v_estado VARCHAR(30);
BEGIN
    IF p_id_empresa IS NULL THEN
        RAISE EXCEPTION 'El id_empresa es obligatorio';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM obras.t_empresa WHERE id_empresa = p_id_empresa) THEN
        RAISE EXCEPTION 'La empresa % no existe', p_id_empresa;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM obras.t_proveedor 
        WHERE id_proveedor = p_id_proveedor AND id_empresa = p_id_empresa AND estado = 'ACTIVO'
    ) THEN
        RAISE EXCEPTION 'El proveedor no existe, no pertenece a su empresa o está inactivo';
    END IF;

    IF p_items_json IS NULL OR jsonb_array_length(p_items_json) = 0 THEN
        RAISE EXCEPTION 'La orden de compra debe contener al menos un material';
    END IF;

    v_estado := COALESCE(NULLIF(TRIM(p_estado), ''), 'BORRADOR');
    IF v_estado NOT IN ('BORRADOR', 'PENDIENTE_APROBACION') THEN
        v_estado := 'BORRADOR';
    END IF;

    v_numero_orden := obras.fn_generar_numero_orden_compra(p_id_empresa);

    INSERT INTO obras.t_orden_compra (
        id_empresa,
        id_proveedor,
        numero_orden,
        fecha,
        observaciones,
        estado,
        id_usuario_solicitante,
        subtotal,
        total,
        created_at,
        updated_at
    ) VALUES (
        p_id_empresa,
        p_id_proveedor,
        v_numero_orden,
        COALESCE(p_fecha, CURRENT_DATE),
        NULLIF(TRIM(p_observaciones), ''),
        v_estado,
        p_id_usuario,
        0.00,
        0.00,
        CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP
    )
    RETURNING id_orden_compra INTO v_id_orden;

    FOR v_item IN 
        SELECT 
            (elem->>'id_material')::INT AS id_material,
            (elem->>'cantidad')::NUMERIC AS cantidad,
            (elem->>'precio_unitario')::NUMERIC AS precio_unitario
        FROM jsonb_array_elements(p_items_json) AS elem
    LOOP
        IF NOT EXISTS (
            SELECT 1 FROM obras.t_material 
            WHERE id_material = v_item.id_material AND id_empresa = p_id_empresa AND estado = 'ACTIVO'
        ) THEN
            RAISE EXCEPTION 'El material ID % no existe, no pertenece a la empresa o está inactivo', v_item.id_material;
        END IF;

        IF v_item.cantidad <= 0 THEN
            RAISE EXCEPTION 'La cantidad solicitada debe ser mayor a cero';
        END IF;

        IF v_item.precio_unitario < 0 THEN
            RAISE EXCEPTION 'El precio unitario no puede ser negativo';
        END IF;

        INSERT INTO obras.t_orden_compra_detalle (
            id_orden_compra,
            id_material,
            cantidad_solicitada,
            precio_unitario,
            subtotal,
            cantidad_recibida
        ) VALUES (
            v_id_orden,
            v_item.id_material,
            v_item.cantidad,
            v_item.precio_unitario,
            ROUND(v_item.cantidad * v_item.precio_unitario, 2),
            0.00
        );

        v_total := v_total + ROUND(v_item.cantidad * v_item.precio_unitario, 2);
    END LOOP;

    UPDATE obras.t_orden_compra
    SET subtotal = v_total, total = v_total
    WHERE id_orden_compra = v_id_orden;

    RETURN v_id_orden;
END;
$function$
```

</details>

## 56. fn_registrar_recepcion_compra

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: t_materiales_almacen, t_movimiento_almacen, t_orden_compra, t_orden_compra_detalle, t_recepcion_compra, t_recepcion_compra_detalle.
- Referencias Python: backend\app\repos\compras_repos.py.
- Scripts con CREATE del nombre: backend\database\migration_compras_recepcion.sql.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.fn_registrar_recepcion_compra(p_id_empresa integer, p_id_orden_compra integer, p_id_usuario integer, p_observaciones text, p_items_json jsonb)
 RETURNS integer
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_id_empresa_oc INT;
    v_estado_actual VARCHAR(30);
    v_numero_recepcion VARCHAR(50);
    v_id_recepcion INT;
    v_item RECORD;
    v_detalle RECORD;
    v_pendiente NUMERIC(14,3);
    v_id_lote INT;
    v_id_movimiento INT;
    v_pendientes_totales INT := 0;
BEGIN
    SELECT id_empresa, estado INTO v_id_empresa_oc, v_estado_actual
    FROM obras.t_orden_compra
    WHERE id_orden_compra = p_id_orden_compra
      AND (p_id_empresa IS NULL OR id_empresa = p_id_empresa);

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Orden de compra no encontrada o no pertenece a la empresa';
    END IF;

    IF v_estado_actual NOT IN ('APROBADA', 'RECIBIDA_PARCIAL') THEN
        RAISE EXCEPTION 'Solo se pueden registrar recepciones en órdenes APROBADA o RECIBIDA_PARCIAL';
    END IF;

    IF p_items_json IS NULL OR jsonb_array_length(p_items_json) = 0 THEN
        RAISE EXCEPTION 'Debe registrar al menos un material en la recepción';
    END IF;

    v_numero_recepcion := obras.fn_generar_numero_recepcion(v_id_empresa_oc);

    INSERT INTO obras.t_recepcion_compra (
        id_orden_compra,
        id_empresa,
        numero_recepcion,
        fecha_recepcion,
        id_usuario_recepcion,
        observaciones,
        created_at
    ) VALUES (
        p_id_orden_compra,
        v_id_empresa_oc,
        v_numero_recepcion,
        CURRENT_TIMESTAMP,
        p_id_usuario,
        NULLIF(TRIM(p_observaciones), ''),
        CURRENT_TIMESTAMP
    )
    RETURNING id_recepcion INTO v_id_recepcion;

    FOR v_item IN 
        SELECT 
            (elem->>'id_detalle')::INT AS id_detalle,
            (elem->>'cantidad')::NUMERIC AS cantidad
        FROM jsonb_array_elements(p_items_json) AS elem
    LOOP
        IF v_item.cantidad <= 0 THEN
            CONTINUE;
        END IF;

        SELECT id_material, cantidad_solicitada, cantidad_recibida, precio_unitario
        INTO v_detalle
        FROM obras.t_orden_compra_detalle
        WHERE id_detalle = v_item.id_detalle
          AND id_orden_compra = p_id_orden_compra;

        IF NOT FOUND THEN
            RAISE EXCEPTION 'Detalle de orden de compra ID % no válido', v_item.id_detalle;
        END IF;

        v_pendiente := v_detalle.cantidad_solicitada - v_detalle.cantidad_recibida;
        IF v_item.cantidad > v_pendiente THEN
            RAISE EXCEPTION 'La cantidad a recibir (%) supera la cantidad pendiente (%) para el material ID %',
                v_item.cantidad, v_pendiente, v_detalle.id_material;
        END IF;

        -- Entrada en inventario / almacén:
        SELECT id_lote INTO v_id_lote
        FROM obras.t_materiales_almacen
        WHERE id_material = v_detalle.id_material
        ORDER BY id_lote DESC LIMIT 1;

        IF v_id_lote IS NOT NULL THEN
            UPDATE obras.t_materiales_almacen
            SET cantidad_actual = cantidad_actual + v_item.cantidad
            WHERE id_lote = v_id_lote;
        ELSE
            INSERT INTO obras.t_materiales_almacen (
                id_material,
                cantidad_inicial,
                cantidad_actual,
                precio_venta,
                fecha_ingreso,
                stock_minimo
            ) VALUES (
                v_detalle.id_material,
                v_item.cantidad,
                v_item.cantidad,
                v_detalle.precio_unitario,
                CURRENT_DATE,
                0.00
            )
            RETURNING id_lote INTO v_id_lote;
        END IF;

        -- Movimiento de inventario para trazabilidad:
        INSERT INTO obras.t_movimiento_almacen (
            id_lote,
            id_material,
            orden_nro,
            cantidad_asignada,
            fecha_movimiento,
            tipo_movimiento,
            id_empresa,
            id_orden_compra,
            id_recepcion,
            id_usuario,
            observaciones,
            created_at
        ) VALUES (
            v_id_lote,
            v_detalle.id_material,
            NULL,
            v_item.cantidad,
            CURRENT_DATE,
            'ENTRADA',
            v_id_empresa_oc,
            p_id_orden_compra,
            v_id_recepcion,
            p_id_usuario,
            'Recepción ' || v_numero_recepcion || ' de OC #' || p_id_orden_compra,
            CURRENT_TIMESTAMP
        )
        RETURNING id_movimiento INTO v_id_movimiento;

        -- Detalle de recepción con enlace al movimiento:
        INSERT INTO obras.t_recepcion_compra_detalle (
            id_recepcion,
            id_orden_compra_detalle,
            id_material,
            cantidad_recibida,
            precio_unitario,
            id_movimiento_almacen
        ) VALUES (
            v_id_recepcion,
            v_item.id_detalle,
            v_detalle.id_material,
            v_item.cantidad,
            v_detalle.precio_unitario,
            v_id_movimiento
        );

        -- Actualizar cantidad recibida en la OC
        UPDATE obras.t_orden_compra_detalle
        SET cantidad_recibida = cantidad_recibida + v_item.cantidad
        WHERE id_detalle = v_item.id_detalle;
    END LOOP;

    -- Verificar si quedan saldos pendientes en la OC
    SELECT COUNT(*) INTO v_pendientes_totales
    FROM obras.t_orden_compra_detalle
    WHERE id_orden_compra = p_id_orden_compra
      AND cantidad_recibida < cantidad_solicitada;

    IF v_pendientes_totales = 0 THEN
        UPDATE obras.t_orden_compra
        SET estado = 'RECIBIDA',
            updated_at = CURRENT_TIMESTAMP
        WHERE id_orden_compra = p_id_orden_compra;
    ELSE
        UPDATE obras.t_orden_compra
        SET estado = 'RECIBIDA_PARCIAL',
            updated_at = CURRENT_TIMESTAMP
        WHERE id_orden_compra = p_id_orden_compra;
    END IF;

    RETURN v_id_recepcion;
END;
$function$
```

</details>

## 57. fn_registrar_unidad_construccion

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: t_estructura_obra, t_modelo_caracteristica, t_modelo_unidad, t_obra, t_unidad_ambiente, t_unidad_caracteristica, t_unidad_construccion, t_unidad_seguimiento, t_usuario.
- Referencias Python: backend\app\repos\unidad_repos.py.
- Scripts con CREATE del nombre: backend\database\migration_cu12_unidades_construccion.sql.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.fn_registrar_unidad_construccion(p_id_obra integer, p_id_empresa integer, p_id_usuario integer, p_id_estructura integer, p_id_padre integer, p_nombre character varying, p_tipo_estructura character varying, p_descripcion text, p_tipo_unidad character varying, p_superficie numeric, p_cantidad_plantas integer, p_estado character varying, p_id_modelo integer, p_ambientes json, p_caracteristicas json)
 RETURNS json
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_id_estructura INTEGER;
    v_id_unidad INTEGER;
    v_codigo VARCHAR;
    v_orden INTEGER;
    v_superficie NUMERIC;
    v_plantas INTEGER;
    v_tipo VARCHAR;
    v_item JSON;
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM obras.t_obra
        WHERE id_obra = p_id_obra AND (id_empresa = p_id_empresa OR p_id_empresa IS NULL)
    ) THEN
        RETURN json_build_object('success', false, 'error', 'El proyecto no existe o no pertenece a su empresa.');
    END IF;

    v_tipo := UPPER(COALESCE(NULLIF(TRIM(p_tipo_unidad), ''), 'OTRO'));
    IF v_tipo NOT IN ('VIVIENDA', 'DEPARTAMENTO', 'LOCAL', 'LOTE', 'OFICINA', 'OTRO') THEN
        RETURN json_build_object('success', false, 'error', 'Tipo de unidad no válido.');
    END IF;
    IF UPPER(COALESCE(p_estado, 'PLANIFICADO')) NOT IN ('PLANIFICADO', 'EN_CONSTRUCCION', 'FINALIZADO', 'SUSPENDIDO') THEN
        RETURN json_build_object('success', false, 'error', 'Estado de unidad no válido.');
    END IF;
    IF p_id_modelo IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM obras.t_modelo_unidad m
        JOIN obras.t_obra o ON o.id_obra = p_id_obra
        WHERE m.id_modelo = p_id_modelo AND m.activo = TRUE AND m.id_empresa = o.id_empresa
    ) THEN
        RETURN json_build_object('success', false, 'error', 'El modelo no existe o pertenece a otra empresa.');
    END IF;

    IF p_id_usuario IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM obras.t_usuario WHERE id_usuario = p_id_usuario
    ) THEN
        RETURN json_build_object('success', false, 'error', 'El usuario autenticado no existe.');
    END IF;

    SELECT COALESCE(p_superficie, m.superficie_base, 0),
           COALESCE(p_cantidad_plantas, m.cantidad_plantas_base, 0)
    INTO v_superficie, v_plantas
    FROM (SELECT 1) x
    LEFT JOIN obras.t_modelo_unidad m ON m.id_modelo = p_id_modelo;

    IF v_superficie < 0 OR v_plantas < 0 OR v_superficie >= 10000000000 THEN
        RETURN json_build_object('success', false, 'error', 'Superficie o cantidad de plantas fuera del rango permitido.');
    END IF;

    IF json_typeof(COALESCE(p_ambientes, '[]'::json)) <> 'array'
       OR json_typeof(COALESCE(p_caracteristicas, '[]'::json)) <> 'array' THEN
        RETURN json_build_object('success', false, 'error', 'Ambientes y características deben ser listas.');
    END IF;

    IF EXISTS (
        SELECT 1
        FROM json_array_elements(COALESCE(p_ambientes, '[]'::json)) item
        WHERE TRIM(COALESCE(item->>'nombre', '')) = ''
           OR LENGTH(TRIM(COALESCE(item->>'nombre', ''))) > 100
           OR NOT CASE
               WHEN COALESCE(item->>'cantidad', '') ~ '^[0-9]+$'
               THEN (item->>'cantidad')::NUMERIC BETWEEN 1 AND 2147483647
               ELSE FALSE
           END
    ) THEN
        RETURN json_build_object('success', false, 'error', 'Cada ambiente debe tener nombre y una cantidad entera mayor que cero.');
    END IF;

    IF EXISTS (
        SELECT 1
        FROM json_array_elements(COALESCE(p_ambientes, '[]'::json)) item
        GROUP BY LOWER(TRIM(item->>'nombre'))
        HAVING COUNT(*) > 1
    ) THEN
        RETURN json_build_object('success', false, 'error', 'No se permiten ambientes duplicados.');
    END IF;

    IF EXISTS (
        SELECT 1
        FROM json_array_elements(COALESCE(p_caracteristicas, '[]'::json)) item
        WHERE TRIM(COALESCE(item->>'nombre', '')) = ''
           OR TRIM(COALESCE(item->>'valor', '')) = ''
           OR LENGTH(TRIM(COALESCE(item->>'nombre', ''))) > 100
           OR LENGTH(TRIM(COALESCE(item->>'valor', ''))) > 250
    ) THEN
        RETURN json_build_object('success', false, 'error', 'Cada característica debe tener nombre y valor.');
    END IF;

    IF EXISTS (
        SELECT 1
        FROM json_array_elements(COALESCE(p_caracteristicas, '[]'::json)) item
        GROUP BY LOWER(TRIM(item->>'nombre'))
        HAVING COUNT(*) > 1
    ) THEN
        RETURN json_build_object('success', false, 'error', 'No se permiten características duplicadas.');
    END IF;

    IF p_id_padre IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM obras.t_estructura_obra
        WHERE id_estructura = p_id_padre AND id_obra = p_id_obra
    ) THEN
        RETURN json_build_object('success', false, 'error', 'El elemento padre no pertenece al proyecto.');
    END IF;

    IF p_id_estructura IS NOT NULL THEN
        SELECT id_estructura INTO v_id_estructura
        FROM obras.t_estructura_obra
        WHERE id_estructura = p_id_estructura AND id_obra = p_id_obra;
        IF v_id_estructura IS NULL THEN
            RETURN json_build_object('success', false, 'error', 'El nodo no existe o no pertenece al proyecto.');
        END IF;
        IF EXISTS (SELECT 1 FROM obras.t_unidad_construccion WHERE id_estructura = v_id_estructura) THEN
            RETURN json_build_object('success', false, 'error', 'El nodo ya representa una unidad de construcción.');
        END IF;
    END IF;

    IF p_id_estructura IS NULL THEN
        IF TRIM(COALESCE(p_nombre, '')) = '' THEN
            RETURN json_build_object('success', false, 'error', 'El nombre de la unidad es obligatorio.');
        END IF;
        IF LENGTH(TRIM(p_nombre)) > 150
           OR LENGTH(COALESCE(NULLIF(TRIM(p_tipo_estructura), ''), INITCAP(v_tipo))) > 50 THEN
            RETURN json_build_object('success', false, 'error', 'Nombre o tipo de estructura fuera del rango permitido.');
        END IF;
        SELECT COALESCE(MAX(orden), 0) + 1 INTO v_orden
        FROM obras.t_estructura_obra
        WHERE id_obra = p_id_obra
          AND ((p_id_padre IS NULL AND id_padre IS NULL) OR id_padre = p_id_padre);
        INSERT INTO obras.t_estructura_obra(id_obra, id_padre, nombre, tipo, descripcion, orden)
        VALUES (p_id_obra, p_id_padre, TRIM(p_nombre), COALESCE(NULLIF(TRIM(p_tipo_estructura), ''), INITCAP(v_tipo)), TRIM(p_descripcion), v_orden)
        RETURNING id_estructura INTO v_id_estructura;
    END IF;

    INSERT INTO obras.t_unidad_construccion(
        id_estructura, tipo_unidad, superficie, cantidad_plantas, estado, id_modelo
    ) VALUES (
        v_id_estructura, v_tipo, v_superficie, v_plantas, UPPER(COALESCE(p_estado, 'PLANIFICADO')), p_id_modelo
    ) RETURNING id_unidad, codigo INTO v_id_unidad, v_codigo;

    INSERT INTO obras.t_unidad_caracteristica(id_unidad, nombre, valor)
    SELECT v_id_unidad, nombre, valor
    FROM obras.t_modelo_caracteristica
    WHERE id_modelo = p_id_modelo;

    FOR v_item IN SELECT * FROM json_array_elements(COALESCE(p_ambientes, '[]'::json)) LOOP
        IF TRIM(COALESCE(v_item->>'nombre', '')) <> '' AND COALESCE((v_item->>'cantidad')::INTEGER, 0) > 0 THEN
            INSERT INTO obras.t_unidad_ambiente(id_unidad, nombre, cantidad)
            VALUES (v_id_unidad, TRIM(v_item->>'nombre'), (v_item->>'cantidad')::INTEGER)
            ON CONFLICT (id_unidad, LOWER(nombre)) DO UPDATE SET cantidad = EXCLUDED.cantidad;
        END IF;
    END LOOP;

    FOR v_item IN SELECT * FROM json_array_elements(COALESCE(p_caracteristicas, '[]'::json)) LOOP
        IF TRIM(COALESCE(v_item->>'nombre', '')) <> '' AND TRIM(COALESCE(v_item->>'valor', '')) <> '' THEN
            INSERT INTO obras.t_unidad_caracteristica(id_unidad, nombre, valor)
            VALUES (v_id_unidad, TRIM(v_item->>'nombre'), TRIM(v_item->>'valor'))
            ON CONFLICT (id_unidad, LOWER(nombre)) DO UPDATE SET valor = EXCLUDED.valor;
        END IF;
    END LOOP;

    INSERT INTO obras.t_unidad_seguimiento(
        id_unidad, estado_anterior, estado_nuevo, id_usuario, observacion
    ) VALUES (
        v_id_unidad, NULL, UPPER(COALESCE(p_estado, 'PLANIFICADO')),
        p_id_usuario, 'Registro inicial de la unidad.'
    );

    RETURN json_build_object('success', true, 'id_unidad', v_id_unidad,
        'id_estructura', v_id_estructura, 'codigo', v_codigo,
        'message', 'Unidad de construcción registrada exitosamente.');
EXCEPTION WHEN OTHERS THEN
    RETURN json_build_object('success', false, 'error', SQLERRM);
END;
$function$
```

</details>

## 58. fn_reordenar_estructura_obra

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: t_estructura_obra, t_obra.
- Referencias Python: backend\app\repos\estructura_repos.py.
- Scripts con CREATE del nombre: backend\database\migration_hu35_estructura.sql.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.fn_reordenar_estructura_obra(p_id_estructura integer, p_id_obra integer, p_direccion character varying, p_id_empresa integer)
 RETURNS json
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_padre integer;
    v_orden_actual integer;
    v_hermano_id integer;
    v_hermano_orden integer;
BEGIN
    -- Validar elemento y obtener su orden y padre
    SELECT e.id_padre, e.orden
    INTO v_padre, v_orden_actual
    FROM obras.t_estructura_obra e
    INNER JOIN obras.t_obra o ON e.id_obra = o.id_obra
    WHERE e.id_estructura = p_id_estructura
      AND e.id_obra = p_id_obra
      AND (o.id_empresa = p_id_empresa OR p_id_empresa IS NULL);

    IF NOT FOUND THEN
        RETURN json_build_object(
            'success', false,
            'error', 'El elemento no existe o no pertenece a su empresa.'
        );
    END IF;

    IF UPPER(p_direccion) = 'UP' THEN
        -- Buscar hermano inmediatamente anterior
        SELECT id_estructura, orden
        INTO v_hermano_id, v_hermano_orden
        FROM obras.t_estructura_obra
        WHERE id_obra = p_id_obra
          AND ((v_padre IS NULL AND id_padre IS NULL) OR (v_padre IS NOT NULL AND id_padre = v_padre))
          AND orden < v_orden_actual
        ORDER BY orden DESC, id_estructura DESC
        LIMIT 1;
    ELSE
        -- Buscar hermano inmediatamente posterior
        SELECT id_estructura, orden
        INTO v_hermano_id, v_hermano_orden
        FROM obras.t_estructura_obra
        WHERE id_obra = p_id_obra
          AND ((v_padre IS NULL AND id_padre IS NULL) OR (v_padre IS NOT NULL AND id_padre = v_padre))
          AND orden > v_orden_actual
        ORDER BY orden ASC, id_estructura ASC
        LIMIT 1;
    END IF;

    -- Si hay hermano con el cual intercambiar
    IF v_hermano_id IS NOT NULL THEN
        UPDATE obras.t_estructura_obra
        SET orden = v_hermano_orden
        WHERE id_estructura = p_id_estructura;

        UPDATE obras.t_estructura_obra
        SET orden = v_orden_actual
        WHERE id_estructura = v_hermano_id;
    END IF;

    RETURN json_build_object(
        'success', true,
        'message', 'Orden actualizado exitosamente.'
    );
EXCEPTION WHEN OTHERS THEN
    RETURN json_build_object(
        'success', false,
        'error', SQLERRM
    );
END;
$function$
```

</details>

## 59. fn_resumen_avances_obra

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: t_obra, t_orden_trabajo.
- Referencias Python: sin coincidencia.
- Scripts con CREATE del nombre: **no localizado en los SQL versionados revisados**.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.fn_resumen_avances_obra(p_id_obra integer, p_id_empresa integer)
 RETURNS json
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_obra_valida         BOOLEAN;
    v_total_ordenes       INTEGER := 0;
    v_ordenes_cumplidas   INTEGER := 0;
    v_ordenes_pendientes  INTEGER := 0;
    v_porcentaje_avance   NUMERIC := 0.0;
    v_ordenes_json        JSON;
    v_cuadrillas_json     JSON;
BEGIN
    -- Validar existencia de obra y pertenencia a empresa
    SELECT EXISTS(
        SELECT 1 FROM obras.t_obra
        WHERE id_obra = p_id_obra
          AND (id_empresa = p_id_empresa OR p_id_empresa IS NULL)
    ) INTO v_obra_valida;

    IF NOT v_obra_valida THEN
        RETURN json_build_object(
            'success', false,
            'error', 'El proyecto no existe o no pertenece a su empresa.'
        );
    END IF;

    -- Conteo de órdenes
    SELECT
        COUNT(*),
        COUNT(*) FILTER (WHERE UPPER(ot.estado) = 'FINALIZADO'),
        COUNT(*) FILTER (WHERE UPPER(ot.estado) != 'FINALIZADO' OR ot.estado IS NULL)
    INTO
        v_total_ordenes,
        v_ordenes_cumplidas,
        v_ordenes_pendientes
    FROM obras.t_orden_trabajo ot
    WHERE ot.id_obra = p_id_obra;

    -- Cálculo del porcentaje global
    IF v_total_ordenes > 0 THEN
        v_porcentaje_avance := ROUND((v_ordenes_cumplidas::NUMERIC / v_total_ordenes::NUMERIC) * 100, 2);
    ELSE
        v_porcentaje_avance := 0.0;
    END IF;

    -- Lista de cuadrillas involucradas con su conteo
    SELECT COALESCE(json_agg(
        json_build_object(
            'cuadrilla', c.cuadrilla,
            'total_ordenes', c.total,
            'cumplidas', c.cumplidas,
            'pendientes', c.pendientes
        )
    ), '[]'::json)
    INTO v_cuadrillas_json
    FROM (
        SELECT
            ot.cuadrilla,
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE UPPER(ot.estado) = 'FINALIZADO') as cumplidas,
            COUNT(*) FILTER (WHERE UPPER(ot.estado) != 'FINALIZADO' OR ot.estado IS NULL) as pendientes
        FROM obras.t_orden_trabajo ot
        WHERE ot.id_obra = p_id_obra AND ot.cuadrilla IS NOT NULL
        GROUP BY ot.cuadrilla
        ORDER BY ot.cuadrilla ASC
    ) c;

    RETURN json_build_object(
        'success',              true,
        'id_obra',              p_id_obra,
        'total_ordenes',        v_total_ordenes,
        'ordenes_cumplidas',    v_ordenes_cumplidas,
        'ordenes_pendientes',   v_ordenes_pendientes,
        'porcentaje_avance',    v_porcentaje_avance,
        'cuadrillas',           v_cuadrillas_json
    );
END;
$function$
```

</details>

## 60. fn_resumen_kpis_inventario

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: t_material, t_materiales_almacen, t_movimiento_almacen.
- Referencias Python: backend\app\repos\inventario_repos.py.
- Scripts con CREATE del nombre: backend\database\migration_inventario.sql.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.fn_resumen_kpis_inventario(p_id_empresa integer)
 RETURNS TABLE(total_materiales integer, total_con_stock integer, total_sin_stock integer, total_stock_bajo integer, valor_total_inventario numeric, total_movimientos_mes integer)
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_total_mat INT := 0;
    v_con_stock INT := 0;
    v_sin_stock INT := 0;
    v_stock_bajo INT := 0;
    v_valor_total NUMERIC(15,2) := 0.00;
    v_movs_mes INT := 0;
BEGIN
    -- Agrupado de existencias por material
    WITH stock_calc AS (
        SELECT 
            m.id_material,
            m.precio,
            COALESCE(SUM(ma.cantidad_actual), 0.00) AS stock_actual,
            COALESCE(MAX(ma.stock_minimo), 0.00) AS stock_minimo
        FROM obras.t_material m
        LEFT JOIN obras.t_materiales_almacen ma ON ma.id_material = m.id_material
        WHERE m.id_empresa = p_id_empresa AND m.estado = 'ACTIVO'
        GROUP BY m.id_material, m.precio
    )
    SELECT 
        COUNT(*)::INT,
        COUNT(CASE WHEN stock_actual > 0 THEN 1 END)::INT,
        COUNT(CASE WHEN stock_actual <= 0 THEN 1 END)::INT,
        COUNT(CASE WHEN stock_actual > 0 AND stock_actual <= stock_minimo THEN 1 END)::INT,
        COALESCE(SUM(stock_actual * precio), 0.00)::NUMERIC(15,2)
    INTO v_total_mat, v_con_stock, v_sin_stock, v_stock_bajo, v_valor_total
    FROM stock_calc;

    -- Movimientos registrados en el mes actual
    SELECT COUNT(*)::INT INTO v_movs_mes
    FROM obras.t_movimiento_almacen
    WHERE id_empresa = p_id_empresa
      AND fecha_movimiento >= DATE_TRUNC('month', CURRENT_DATE);

    RETURN QUERY
    SELECT v_total_mat, v_con_stock, v_sin_stock, v_stock_bajo, v_valor_total, v_movs_mes;
END;
$function$
```

</details>

## 61. fn_snapshot_precio_partida

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: t_analisis_precio_unitario, t_estimacion.
- Referencias Python: sin coincidencia.
- Scripts con CREATE del nombre: backend\database\migration_apu_materiales_y_presupuestos.sql.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.fn_snapshot_precio_partida()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
DECLARE v_precio NUMERIC; v_directo NUMERIC;
BEGIN
    IF NEW.precio_unitario IS NULL OR NEW.costo_directo_unitario IS NULL THEN
        SELECT a.precio_unitario_final, a.costo_directo INTO v_precio, v_directo
        FROM obras.t_analisis_precio_unitario a
        JOIN obras.t_estimacion e ON e.id_empresa = a.id_empresa
        WHERE e.id_estimacion = NEW.id_estimacion
          AND a.id_analisis_precio_unitario = NEW.id_analisis_precio_unitario;
        NEW.precio_unitario := COALESCE(NEW.precio_unitario, v_precio, 0);
        NEW.costo_directo_unitario := COALESCE(NEW.costo_directo_unitario, v_directo, 0);
    END IF;
    IF NEW.item_codigo IS NULL OR BTRIM(NEW.item_codigo) = '' THEN
        NEW.item_codigo := '01.' || LPAD(NEW.orden::text, 2, '0');
    END IF;
    RETURN NEW;
END;
$function$
```

</details>

## 62. fn_sync_apu_precio

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: t_analisi_precio_unitario_insumo.
- Referencias Python: sin coincidencia.
- Scripts con CREATE del nombre: backend\database\migration_apu_materiales_y_presupuestos.sql.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.fn_sync_apu_precio()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
    IF NEW.codigo IS NULL OR BTRIM(NEW.codigo) = '' THEN
        NEW.codigo := 'APU-' || NEW.id_empresa::text || '-' || LPAD(nextval('obras.seq_apu_codigo')::text, 5, '0');
    END IF;
    NEW.costo_materiales := COALESCE((
        SELECT SUM(i.subtotal)
        FROM obras.t_analisi_precio_unitario_insumo i
        WHERE i.id_analisis_precio_unitario = NEW.id_analisis_precio_unitario
    ), 0);
    NEW.mano_de_obra := COALESCE(NEW.mano_de_obra, 0);
    NEW.porcentaje_utilidad := COALESCE(NEW.porcentaje_utilidad, 0);
    NEW.costo_directo := ROUND(NEW.costo_materiales + NEW.mano_de_obra, 2);
    NEW.precio_unitario_final := ROUND(NEW.costo_directo * (1 + NEW.porcentaje_utilidad / 100), 2);
    RETURN NEW;
END;
$function$
```

</details>

## 63. fn_validar_incidencia_ot_cu19

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: t_incidencia, t_orden_trabajo.
- Referencias Python: sin coincidencia.
- Scripts con CREATE del nombre: backend\database\migration_cu19_incidencias_ot_tiempos.sql.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.fn_validar_incidencia_ot_cu19()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_obra_incidencia INTEGER;
    v_obra_orden      INTEGER;
BEGIN
    SELECT id_obra INTO v_obra_incidencia FROM obras.t_incidencia WHERE id_incidencia = NEW.id_incidencia;
    SELECT id_obra INTO v_obra_orden      FROM obras.t_orden_trabajo WHERE orden_nro = NEW.orden_nro;
    IF v_obra_incidencia IS NULL OR v_obra_orden IS NULL OR v_obra_incidencia <> v_obra_orden THEN
        RAISE EXCEPTION 'La orden de trabajo % no pertenece a la obra de la incidencia %.',
            NEW.orden_nro, NEW.id_incidencia;
    END IF;
    RETURN NEW;
END;
$function$
```

</details>

## 64. p_registrar_usuario

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: t_persona, t_usuario.
- Referencias Python: sin coincidencia.
- Scripts con CREATE del nombre: **no localizado en los SQL versionados revisados**.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE PROCEDURE obras.p_registrar_usuario(IN p_username character varying, IN p_password character varying, IN p_correo character varying, IN p_id_empresa integer, IN p_id_rol integer, IN p_nombre_completo character varying, IN p_fecha_nacimiento date, IN p_ci character varying, IN p_direccion character varying, IN p_telefono character varying, IN p_telefono_ref character varying, IN p_ubicacion character varying)
 LANGUAGE plpgsql
AS $procedure$
DECLARE
    v_id_persona INTEGER;
BEGIN
    IF EXISTS (
        SELECT 1
        FROM obras.t_usuario
        WHERE correo = p_correo
    ) THEN
        RAISE EXCEPTION 'El correo % ya está registrado', p_correo;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM obras.t_persona
        WHERE ci = p_ci
    ) THEN
        RAISE EXCEPTION 'El CI % ya está registrado', p_ci;
    END IF;
    INSERT INTO obras.t_persona (nombre_completo,fecha_nacimiento,
	ci,direccion,telefono,telefono_ref,ubicacion)
    VALUES (p_nombre_completo,p_fecha_nacimiento
	,p_ci,p_direccion,p_telefono,p_telefono_ref,p_ubicacion)
    RETURNING id_persona INTO v_id_persona;
	
    INSERT INTO obras.t_usuario (username,password,correo,
	id_empresa,id_rol,id_persona)
    VALUES (p_username,p_password,p_correo,
	p_id_empresa,p_id_rol,v_id_persona);
END;
$procedure$
```

</details>

## 65. sp_actualizar_estado_obra

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: t_obra.
- Referencias Python: backend\app\repos\obra_repos.py.
- Scripts con CREATE del nombre: **no localizado en los SQL versionados revisados**.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.sp_actualizar_estado_obra(p_id_obra integer, p_id_empresa integer, p_nuevo_estado character varying)
 RETURNS json
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_filas_actualizadas integer;
BEGIN
    IF p_nuevo_estado NOT IN ('PLANIFICACION', 'ACTIVO', 'PAUSADO', 'FINALIZADO', 'CANCELADO') THEN
        RETURN json_build_object(
            'success', false,
            'error', 'Estado de obra no válido.'
        );
    END IF;

    UPDATE obras.t_obra
    SET estado_obra = p_nuevo_estado
    WHERE id_obra = p_id_obra AND (id_empresa = p_id_empresa OR p_id_empresa IS NULL);

    GET DIAGNOSTICS v_filas_actualizadas = ROW_COUNT;

    IF v_filas_actualizadas = 0 THEN
        RETURN json_build_object(
            'success', false,
            'error', 'La obra no existe o no pertenece a esta empresa.'
        );
    END IF;

    RETURN json_build_object(
        'success', true,
        'message', 'Estado de obra actualizado exitosamente.'
    );
EXCEPTION WHEN OTHERS THEN
    RETURN json_build_object(
        'success', false,
        'error', SQLERRM
    );
END;
$function$
```

</details>

## 66. sp_actualizar_obra

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: t_detalle_obra, t_obra.
- Referencias Python: backend\app\repos\obra_repos.py.
- Scripts con CREATE del nombre: **no localizado en los SQL versionados revisados**.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.sp_actualizar_obra(p_id_obra integer, p_id_empresa integer, p_id_tipo_obra integer, p_fecha_inicio date, p_fecha_fin date, p_nombre character varying, p_descripcion text, p_moneda character varying, p_ubicacion character varying, p_zona character varying, p_distrito character varying, p_uv character varying, p_manzana character varying, p_latitud numeric, p_longitud numeric, p_id_supervisor integer, p_id_cliente integer, p_cotizacion_inicial numeric, p_descripcion_cliente text, p_observacion text)
 RETURNS json
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_filas_actualizadas integer;
BEGIN
    UPDATE obras.t_obra
    SET id_tipo_obra = p_id_tipo_obra,
        fecha_inicio = p_fecha_inicio,
        fecha_fin = p_fecha_fin,
        nombre = p_nombre,
        descripcion = p_descripcion,
        moneda = p_moneda
    WHERE id_obra = p_id_obra AND id_empresa = p_id_empresa;

    GET DIAGNOSTICS v_filas_actualizadas = ROW_COUNT;

    IF v_filas_actualizadas = 0 THEN
        RETURN json_build_object(
            'success', false,
            'error', 'La obra no existe o no pertenece a esta empresa.'
        );
    END IF;

    UPDATE obras.t_detalle_obra
    SET ubicacion = p_ubicacion,
        latitud = p_latitud,
        longitud = p_longitud,
        id_supervisor = p_id_supervisor,
        id_cliente = p_id_cliente,
        descripcion_cliente = p_descripcion_cliente,
        observacion = p_observacion,
        cotizacion_inicial = p_cotizacion_inicial,
        zona = p_zona,
        distrito = p_distrito,
        uv = p_uv,
        manzana = p_manzana
    WHERE id_obra = p_id_obra;

    RETURN json_build_object(
        'success', true,
        'message', 'Obra actualizada exitosamente'
    );
EXCEPTION WHEN OTHERS THEN
    RETURN json_build_object(
        'success', false,
        'error', SQLERRM
    );
END;
$function$
```

</details>

## 67. sp_asignar_responsable_obra

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: t_detalle_obra, t_obra, t_obra_usuario, t_rol, t_usuario.
- Referencias Python: backend\app\repos\obra_repos.py.
- Scripts con CREATE del nombre: **no localizado en los SQL versionados revisados**.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.sp_asignar_responsable_obra(p_id_obra integer, p_id_usuario integer, p_id_empresa integer)
 RETURNS json
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_obra_valida boolean;
    v_usuario_valido boolean;
BEGIN
    -- 1. Validar que la obra pertenece al Tenant
    SELECT EXISTS(
        SELECT 1 FROM obras.t_obra 
        WHERE id_obra = p_id_obra AND (id_empresa = p_id_empresa OR p_id_empresa IS NULL)
    ) INTO v_obra_valida;

    IF NOT v_obra_valida THEN
        RETURN json_build_object(
            'success', false,
            'error', 'La obra no pertenece a su empresa o no existe.'
        );
    END IF;

    -- 2. Validar que el usuario pertenece a la empresa Y tiene el rol JEFE DE OBRA
    SELECT EXISTS(
        SELECT 1 
        FROM obras.t_usuario u
        INNER JOIN obras.t_rol r ON u.id_rol = r.id_rol
        WHERE u.id_usuario = p_id_usuario 
          AND (u.id_empresa = p_id_empresa OR p_id_empresa IS NULL)
          AND r.nombre_rol = 'JEFE DE OBRA'
    ) INTO v_usuario_valido;

    IF NOT v_usuario_valido THEN
        RETURN json_build_object(
            'success', false,
            'error', 'Solo se permite asignar como responsable a usuarios con el rol JEFE DE OBRA.'
        );
    END IF;

    -- 3. Asignar en t_obra_usuario
    INSERT INTO obras.t_obra_usuario (id_obra, id_usuario)
    VALUES (p_id_obra, p_id_usuario)
    ON CONFLICT (id_obra, id_usuario) DO NOTHING;

    -- 4. Actualizar id_supervisor en t_detalle_obra si no hay uno asignado
    UPDATE obras.t_detalle_obra
    SET id_supervisor = p_id_usuario
    WHERE id_obra = p_id_obra AND (id_supervisor IS NULL OR id_supervisor = p_id_usuario);

    RETURN json_build_object(
        'success', true,
        'message', 'Jefe de Obra asignado como responsable exitosamente.'
    );
EXCEPTION WHEN OTHERS THEN
    RETURN json_build_object(
        'success', false,
        'error', SQLERRM
    );
END;
$function$
```

</details>

## 68. sp_listar_obras

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: t_detalle_obra, t_obra, t_tipo_obra.
- Referencias Python: backend\app\repos\obra_repos.py.
- Scripts con CREATE del nombre: **no localizado en los SQL versionados revisados**.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.sp_listar_obras(p_id_empresa integer)
 RETURNS json
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_obras json;
BEGIN
    SELECT COALESCE(json_agg(
        json_build_object(
            'id_obra', sub.id_obra,
            'codigo', sub.codigo,
            'nombre', sub.nombre,
            'descripcion', sub.descripcion,
            'id_tipo_obra', sub.id_tipo_obra,
            'tipo_obra_nombre', sub.tipo_obra_nombre,
            'estado_obra', sub.estado_obra,
            'fecha_inicio', sub.fecha_inicio,
            'fecha_fin', sub.fecha_fin,
            'id_empresa', sub.id_empresa,
            'moneda', sub.moneda,
            'created_at', sub.created_at,
            'updated_at', sub.updated_at,
            'ubicacion', sub.ubicacion,
            'zona', sub.zona,
            'distrito', sub.distrito,
            'uv', sub.uv,
            'manzana', sub.manzana,
            'valor_estimado', sub.cotizacion_inicial
        )
    ), '[]'::json)
    INTO v_obras
    FROM (
        SELECT 
            o.id_obra, o.codigo, o.nombre, o.descripcion, o.id_tipo_obra, t.nombre_obra AS tipo_obra_nombre,
            o.estado_obra, o.fecha_inicio, o.fecha_fin, o.id_empresa, o.moneda, o.created_at, o.updated_at,
            d.ubicacion, d.zona, d.distrito, d.uv, d.manzana, d.cotizacion_inicial
        FROM obras.t_obra o
        LEFT JOIN obras.t_detalle_obra d ON o.id_obra = d.id_obra
        LEFT JOIN obras.t_tipo_obra t ON o.id_tipo_obra = t.id_tipo_obra
        WHERE (o.id_empresa = p_id_empresa OR p_id_empresa IS NULL)
        ORDER BY o.created_at DESC
    ) sub;

    RETURN json_build_object(
        'success', true,
        'data', v_obras
    );
END;
$function$
```

</details>

## 69. sp_login_exitoso

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: t_seguridad_usuario.
- Referencias Python: backend\app\repos\auth_repos.py.
- Scripts con CREATE del nombre: **no localizado en los SQL versionados revisados**.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.sp_login_exitoso(p_id_usuario integer, p_dispositivo_hash character varying)
 RETURNS void
 LANGUAGE plpgsql
AS $function$
        BEGIN
            -- Reiniciar intentos
            UPDATE obras.t_seguridad_usuario
            SET intentos_fallidos = 0,
                bloqueado_hasta = NULL,
                ultima_actualizacion = CURRENT_TIMESTAMP
            WHERE id_usuario = p_id_usuario;

            -- Registrar dispositivo si no existe en el array
            UPDATE obras.t_seguridad_usuario
            SET dispositivos_conocidos = array_append(dispositivos_conocidos, p_dispositivo_hash),
                ultima_actualizacion = CURRENT_TIMESTAMP
            WHERE id_usuario = p_id_usuario
              AND NOT (p_dispositivo_hash = ANY(coalesce(dispositivos_conocidos, '{}'::text[])));
        END;
        $function$
```

</details>

## 70. sp_login_usuario

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: t_empresa, t_persona, t_rol, t_seguridad_usuario, t_usuario.
- Referencias Python: backend\app\repos\auth_repos.py.
- Scripts con CREATE del nombre: **no localizado en los SQL versionados revisados**.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.sp_login_usuario(p_identificador character varying)
 RETURNS json
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_usuario RECORD;
    v_seguridad RECORD;
    v_identificador_clean text := TRIM(p_identificador);
BEGIN
    -- 1. Buscar usuario (case-insensitive para username, correo y CI)
    SELECT a.id_usuario, a.password, a.username, a.correo, b.ci, b.nombre_completo, b.telefono, c.nombre_rol, a.id_empresa, d.nombre_empresa
    INTO v_usuario
    FROM obras.t_usuario a
    INNER JOIN obras.t_persona b ON a.id_persona = b.id_persona
    INNER JOIN obras.t_rol c ON a.id_rol = c.id_rol
    LEFT JOIN obras.t_empresa d ON a.id_empresa = d.id_empresa
    WHERE (
        LOWER(a.username) = LOWER(v_identificador_clean)
        OR LOWER(a.correo) = LOWER(v_identificador_clean)
        OR UPPER(b.ci) = UPPER(v_identificador_clean)
    );

    IF NOT FOUND THEN
        RETURN json_build_object('success', false, 'error', 'El usuario o contraseña ingresados son incorrectos.');
    END IF;

    -- 2. Obtener o crear seguridad
    SELECT intentos_fallidos, bloqueado_hasta, dispositivos_conocidos
    INTO v_seguridad
    FROM obras.t_seguridad_usuario
    WHERE id_usuario = v_usuario.id_usuario;

    IF NOT FOUND THEN
        INSERT INTO obras.t_seguridad_usuario (id_usuario, intentos_fallidos, bloqueado_hasta, dispositivos_conocidos)
        VALUES (v_usuario.id_usuario, 0, NULL, '{}')
        RETURNING intentos_fallidos, bloqueado_hasta, dispositivos_conocidos
        INTO v_seguridad;
    END IF;

    -- 3. Verificar si está bloqueado
    IF v_seguridad.bloqueado_hasta IS NOT NULL AND v_seguridad.bloqueado_hasta > CURRENT_TIMESTAMP THEN
        RETURN json_build_object(
            'success', false,
            'error', 'Tu cuenta está temporalmente bloqueada.',
            'bloqueado_hasta', v_seguridad.bloqueado_hasta
        );
    END IF;

    -- Si el bloqueo ya expiró en tiempo, pero sigue con intentos > 0, lo reiniciamos en el SP
    IF v_seguridad.bloqueado_hasta IS NOT NULL AND v_seguridad.bloqueado_hasta <= CURRENT_TIMESTAMP THEN
        UPDATE obras.t_seguridad_usuario
        SET intentos_fallidos = 0, bloqueado_hasta = NULL, ultima_actualizacion = CURRENT_TIMESTAMP
        WHERE id_usuario = v_usuario.id_usuario;
        v_seguridad.intentos_fallidos := 0;
        v_seguridad.bloqueado_hasta := NULL;
    END IF;

    -- Retornar los datos del usuario y la seguridad para validar la contraseña en el backend
    RETURN json_build_object(
        'success', true,
        'id_usuario', v_usuario.id_usuario,
        'password_hash', v_usuario.password,
        'username', v_usuario.username,
        'correo', v_usuario.correo,
        'ci', v_usuario.ci,
        'nombre_completo', v_usuario.nombre_completo,
        'telefono', v_usuario.telefono,
        'nombre_rol', v_usuario.nombre_rol,
        'id_empresa', v_usuario.id_empresa,
        'nombre_empresa', v_usuario.nombre_empresa,
        'intentos_fallidos', v_seguridad.intentos_fallidos,
        'dispositivos_conocidos', v_seguridad.dispositivos_conocidos
    );
END;
$function$
```

</details>

## 71. sp_obtener_obra_detalle

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: t_detalle_obra, t_obra, t_obra_usuario, t_persona, t_rol, t_tipo_obra, t_usuario.
- Referencias Python: backend\app\repos\obra_repos.py.
- Scripts con CREATE del nombre: backend\database\migration_personal_obra.sql, backend\database\migration_personal_obra_rollback.sql.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.sp_obtener_obra_detalle(p_id_obra integer, p_id_empresa integer)
 RETURNS json
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_obra record;
    v_responsables json;
BEGIN
    SELECT 
        o.id_obra, o.codigo, o.nombre, o.descripcion, o.estado_obra, o.fecha_inicio, o.fecha_fin, o.id_empresa, o.moneda, o.created_at, o.updated_at,
        t.id_tipo_obra, t.nombre_obra AS tipo_obra_nombre,
        d.ubicacion, d.latitud, d.longitud, d.zona, d.distrito, d.uv, d.manzana, d.cotizacion_inicial AS valor_estimado,
        d.descripcion_cliente, d.observacion,
        d.id_supervisor, p_sup.nombre_completo AS supervisor_nombre,
        d.id_cliente, p_cli.nombre_completo AS cliente_nombre
    INTO v_obra
    FROM obras.t_obra o
    LEFT JOIN obras.t_detalle_obra d ON o.id_obra = d.id_obra
    LEFT JOIN obras.t_tipo_obra t ON o.id_tipo_obra = t.id_tipo_obra
    LEFT JOIN obras.t_usuario u_sup ON d.id_supervisor = u_sup.id_usuario
    LEFT JOIN obras.t_persona p_sup ON u_sup.id_persona = p_sup.id_persona
    LEFT JOIN obras.t_usuario u_cli ON d.id_cliente = u_cli.id_usuario
    LEFT JOIN obras.t_persona p_cli ON u_cli.id_persona = p_cli.id_persona
    WHERE o.id_obra = p_id_obra AND (o.id_empresa = p_id_empresa OR p_id_empresa IS NULL);

    IF NOT FOUND THEN
        RETURN json_build_object(
            'success', false,
            'error', 'La obra no existe o no pertenece a esta empresa.'
        );
    END IF;

    -- Obtener responsables asignados
    SELECT COALESCE(json_agg(
        json_build_object(
            'id_usuario', ou.id_usuario,
            'username', u.username,
            'nombre_completo', p.nombre_completo,
            'fecha_asignacion', ou.fecha_asignacion
        )
    ), '[]'::json)
    INTO v_responsables
    FROM obras.t_obra_usuario ou
    INNER JOIN obras.t_usuario u ON ou.id_usuario = u.id_usuario
    INNER JOIN obras.t_persona p ON u.id_persona = p.id_persona
    WHERE ou.id_obra = p_id_obra
      AND u.id_empresa = v_obra.id_empresa
      AND EXISTS (SELECT 1 FROM obras.t_rol r
                  WHERE r.id_rol = u.id_rol AND r.nombre_rol = 'JEFE DE OBRA');

    RETURN json_build_object(
        'success', true,
        'data', json_build_object(
            'id_obra', v_obra.id_obra,
            'codigo', v_obra.codigo,
            'nombre', v_obra.nombre,
            'descripcion', v_obra.descripcion,
            'estado_obra', v_obra.estado_obra,
            'fecha_inicio', v_obra.fecha_inicio,
            'fecha_fin', v_obra.fecha_fin,
            'id_empresa', v_obra.id_empresa,
            'moneda', v_obra.moneda,
            'created_at', v_obra.created_at,
            'updated_at', v_obra.updated_at,
            'id_tipo_obra', v_obra.id_tipo_obra,
            'tipo_obra_nombre', v_obra.tipo_obra_nombre,
            'ubicacion', v_obra.ubicacion,
            'latitud', v_obra.latitud,
            'longitud', v_obra.longitud,
            'zona', v_obra.zona,
            'distrito', v_obra.distrito,
            'uv', v_obra.uv,
            'manzana', v_obra.manzana,
            'valor_estimado', v_obra.valor_estimado,
            'descripcion_cliente', v_obra.descripcion_cliente,
            'observacion', v_obra.observacion,
            'id_supervisor', v_obra.id_supervisor,
            'supervisor_nombre', v_obra.supervisor_nombre,
            'id_cliente', v_obra.id_cliente,
            'cliente_nombre', v_obra.cliente_nombre,
            'responsables', v_responsables
        )
    );
END;
$function$
```

</details>

## 72. sp_registrar_intento_fallido

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: t_seguridad_usuario.
- Referencias Python: backend\app\repos\auth_repos.py.
- Scripts con CREATE del nombre: **no localizado en los SQL versionados revisados**.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.sp_registrar_intento_fallido(p_id_usuario integer)
 RETURNS json
 LANGUAGE plpgsql
AS $function$
        DECLARE
            v_intentos INT;
            v_bloqueado_hasta TIMESTAMP;
        BEGIN
            SELECT intentos_fallidos + 1 INTO v_intentos
            FROM obras.t_seguridad_usuario
            WHERE id_usuario = p_id_usuario;

            IF v_intentos >= 5 THEN
                v_bloqueado_hasta := CURRENT_TIMESTAMP + INTERVAL '15 minutes';
            ELSE
                v_bloqueado_hasta := NULL;
            END IF;

            UPDATE obras.t_seguridad_usuario
            SET intentos_fallidos = v_intentos,
                bloqueado_hasta = v_bloqueado_hasta,
                ultima_actualizacion = CURRENT_TIMESTAMP
            WHERE id_usuario = p_id_usuario;

            RETURN json_build_object(
                'intentos_fallidos', v_intentos,
                'bloqueado_hasta', v_bloqueado_hasta
            );
        END;
        $function$
```

</details>

## 73. sp_registrar_obra

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: t_detalle_obra, t_obra.
- Referencias Python: backend\app\repos\obra_repos.py.
- Scripts con CREATE del nombre: **no localizado en los SQL versionados revisados**.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.sp_registrar_obra(p_codigo character varying, p_nombre character varying, p_descripcion text, p_id_tipo_obra integer, p_estado_obra character varying, p_fecha_inicio date, p_fecha_fin date, p_id_empresa integer, p_moneda character varying, p_ubicacion character varying, p_zona character varying, p_distrito character varying, p_uv character varying, p_manzana character varying, p_latitud numeric, p_longitud numeric, p_id_supervisor integer, p_id_cliente integer, p_cotizacion_inicial numeric, p_descripcion_cliente text, p_observacion text)
 RETURNS json
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_id_obra integer;
BEGIN
    INSERT INTO obras.t_obra (
        id_tipo_obra, estado_obra, fecha_inicio, fecha_fin, id_empresa, codigo, nombre, descripcion, moneda
    ) VALUES (
        p_id_tipo_obra, p_estado_obra, p_fecha_inicio, p_fecha_fin, p_id_empresa, p_codigo, p_nombre, p_descripcion, p_moneda
    ) RETURNING id_obra INTO v_id_obra;

    INSERT INTO obras.t_detalle_obra (
        id_obra, ubicacion, latitud, longitud, id_supervisor, id_cliente, descripcion_cliente, observacion, cotizacion_inicial, zona, distrito, uv, manzana
    ) VALUES (
        v_id_obra, p_ubicacion, p_latitud, p_longitud, p_id_supervisor, p_id_cliente, p_descripcion_cliente, p_observacion, p_cotizacion_inicial, p_zona, p_distrito, p_uv, p_manzana
    );

    RETURN json_build_object(
        'success', true,
        'id_obra', v_id_obra,
        'message', 'Obra registrada exitosamente'
    );
EXCEPTION WHEN OTHERS THEN
    RETURN json_build_object(
        'success', false,
        'error', SQLERRM
    );
END;
$function$
```

</details>

## 74. sp_retirar_responsable_obra

- Lenguaje: plpgsql. Volatilidad: v (v=volatile, s=stable, i=immutable).
- Tablas mencionadas: t_detalle_obra, t_obra, t_obra_usuario, t_rol, t_usuario.
- Referencias Python: backend\app\repos\obra_repos.py.
- Scripts con CREATE del nombre: backend\database\migration_personal_obra.sql, backend\database\migration_personal_obra_rollback.sql.

<details>
<summary>Definici?n real</summary>

```sql
CREATE OR REPLACE FUNCTION obras.sp_retirar_responsable_obra(p_id_obra integer, p_id_usuario integer, p_id_empresa integer)
 RETURNS json
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_filas_afectadas integer;
BEGIN
    -- Validar obra
    IF NOT EXISTS(
        SELECT 1 FROM obras.t_obra WHERE id_obra = p_id_obra AND (id_empresa = p_id_empresa OR p_id_empresa IS NULL)
    ) THEN
        RETURN json_build_object(
            'success', false,
            'error', 'La obra no pertenece a su empresa o no existe.'
        );
    END IF;

    DELETE FROM obras.t_obra_usuario
    WHERE id_obra = p_id_obra AND id_usuario = p_id_usuario;

    GET DIAGNOSTICS v_filas_afectadas = ROW_COUNT;

    -- Si era el supervisor de t_detalle_obra, limpiarlo o colocar otro existente
    UPDATE obras.t_detalle_obra
    SET id_supervisor = (
        SELECT ou.id_usuario
        FROM obras.t_obra_usuario ou
        JOIN obras.t_usuario u ON u.id_usuario = ou.id_usuario
        JOIN obras.t_rol r ON r.id_rol = u.id_rol
        JOIN obras.t_obra o ON o.id_obra = ou.id_obra
        WHERE ou.id_obra = p_id_obra
          AND r.nombre_rol = 'JEFE DE OBRA'
          AND u.estado = 'ACTIVO'
          AND u.id_empresa = o.id_empresa
        ORDER BY ou.fecha_asignacion, ou.id_usuario
        LIMIT 1
    )
    WHERE id_obra = p_id_obra AND id_supervisor = p_id_usuario;

    RETURN json_build_object(
        'success', true,
        'message', 'Responsable retirado exitosamente.'
    );
EXCEPTION WHEN OTHERS THEN
    RETURN json_build_object(
        'success', false,
        'error', SQLERRM
    );
END;
$function$
```

</details>
