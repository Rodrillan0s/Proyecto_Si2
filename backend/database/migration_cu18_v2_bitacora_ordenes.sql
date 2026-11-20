-- ============================================================================
-- MIGRACIÓN CU18 (v2): Avances de Obra derivados de Órdenes de Trabajo (Bitácora)
-- Los avances se calculan automáticamente a partir de las órdenes de trabajo:
--   Avance Global = (Órdenes FINALIZADAS / Total de Órdenes) * 100%
-- Registra las cuadrillas y personal que cumplieron cada orden,
-- así como las órdenes que faltan por cumplir para alcanzar el 100%.
-- ============================================================================

-- 1. FUNCIÓN: fn_resumen_avances_obra (v2)
-- Retorna el cálculo del % global, conteo de órdenes cumplidas y pendientes,
-- y el listado de cuadrillas involucradas.
CREATE OR REPLACE FUNCTION obras.fn_resumen_avances_obra(
    p_id_obra    INTEGER,
    p_id_empresa INTEGER
) RETURNS JSON AS $$
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
$$ LANGUAGE plpgsql;


-- 2. FUNCIÓN: fn_listar_avances_obra (v2)
-- Retorna la bitácora completa de órdenes de trabajo de la obra,
-- detallando la cuadrilla, personal responsable, fechas, observaciones
-- y el aporte porcentual individual de cada orden al proyecto.
CREATE OR REPLACE FUNCTION obras.fn_listar_avances_obra(
    p_id_obra    INTEGER,
    p_id_empresa INTEGER,
    p_estado     VARCHAR(30) DEFAULT NULL
) RETURNS JSON AS $$
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
$$ LANGUAGE plpgsql;
