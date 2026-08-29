-- ============================================================================
-- MIGRACIÓN HU35: Estructura Jerárquica de Obra (WBS)
-- ============================================================================

-- 1. Tabla obras.t_estructura_obra
CREATE TABLE IF NOT EXISTS obras.t_estructura_obra (
    id_estructura SERIAL PRIMARY KEY,
    id_obra INTEGER NOT NULL,
    id_padre INTEGER NULL,
    nombre VARCHAR(150) NOT NULL,
    tipo VARCHAR(50) NOT NULL DEFAULT 'Sector',
    descripcion TEXT,
    orden INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_estructura_obra FOREIGN KEY (id_obra) 
        REFERENCES obras.t_obra(id_obra) ON DELETE CASCADE,
    CONSTRAINT fk_estructura_padre FOREIGN KEY (id_padre) 
        REFERENCES obras.t_estructura_obra(id_estructura) ON DELETE CASCADE
);

-- Índices de búsqueda
CREATE INDEX IF NOT EXISTS idx_estructura_obra_id_obra ON obras.t_estructura_obra(id_obra);
CREATE INDEX IF NOT EXISTS idx_estructura_obra_id_padre ON obras.t_estructura_obra(id_padre);

-- 2. Trigger para updated_at
CREATE OR REPLACE FUNCTION obras.fn_actualizar_updated_at_estructura()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tg_actualizar_updated_at_estructura ON obras.t_estructura_obra;
CREATE TRIGGER tg_actualizar_updated_at_estructura
BEFORE UPDATE ON obras.t_estructura_obra
FOR EACH ROW
EXECUTE FUNCTION obras.fn_actualizar_updated_at_estructura();

-- 3. Funciones de Gestión de Estructura (Prefijo fn_)

-- A. fn_listar_estructura_obra
CREATE OR REPLACE FUNCTION obras.fn_listar_estructura_obra(
    p_id_obra integer,
    p_id_empresa integer
) RETURNS json AS $$
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
$$ LANGUAGE plpgsql;

-- B. fn_registrar_estructura_obra
CREATE OR REPLACE FUNCTION obras.fn_registrar_estructura_obra(
    p_id_obra integer,
    p_id_padre integer,
    p_nombre varchar,
    p_tipo varchar,
    p_descripcion text,
    p_orden integer,
    p_id_empresa integer
) RETURNS json AS $$
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
$$ LANGUAGE plpgsql;

-- C. fn_actualizar_estructura_obra
CREATE OR REPLACE FUNCTION obras.fn_actualizar_estructura_obra(
    p_id_estructura integer,
    p_id_obra integer,
    p_nombre varchar,
    p_tipo varchar,
    p_descripcion text,
    p_orden integer,
    p_id_empresa integer
) RETURNS json AS $$
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
$$ LANGUAGE plpgsql;

-- D. fn_eliminar_estructura_obra
CREATE OR REPLACE FUNCTION obras.fn_eliminar_estructura_obra(
    p_id_estructura integer,
    p_id_obra integer,
    p_id_empresa integer
) RETURNS json AS $$
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
$$ LANGUAGE plpgsql;

-- E. fn_reordenar_estructura_obra
CREATE OR REPLACE FUNCTION obras.fn_reordenar_estructura_obra(
    p_id_estructura integer,
    p_id_obra integer,
    p_direccion varchar, -- 'UP' o 'DOWN'
    p_id_empresa integer
) RETURNS json AS $$
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
$$ LANGUAGE plpgsql;
