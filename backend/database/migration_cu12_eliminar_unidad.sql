-- ============================================================================
-- MIGRACIÓN CU12: Eliminación controlada de unidades de construcción
-- IMPORTANTE: revisar y ejecutar manualmente.
-- No modifica las protecciones de eliminación de la estructura CU11.
-- ============================================================================

CREATE OR REPLACE FUNCTION obras.fn_eliminar_unidad_construccion(
    p_id_obra INTEGER,
    p_id_unidad INTEGER,
    p_id_empresa INTEGER
) RETURNS JSON AS $$
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
$$ LANGUAGE plpgsql;
