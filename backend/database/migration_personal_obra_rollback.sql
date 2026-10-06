-- Revierte exclusivamente las dos funciones de migration_personal_obra.sql.
BEGIN;

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
    WHERE ou.id_obra = p_id_obra;

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
$function$;

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
        SELECT id_usuario FROM obras.t_obra_usuario WHERE id_obra = p_id_obra LIMIT 1
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
$function$;

COMMIT;
