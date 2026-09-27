-- ============================================================================
-- MIGRACIÓN CU18: Registrar y Consultar Avances de Obra
-- HU-105 – T22: Registrar y consultar avances de obra
-- Actores: JEFE DE OBRA (Responsable del Proyecto) / ADMINISTRADOR_EMPRESA (Supervisor)
-- ============================================================================
-- Dependencias: t_unidad_construccion, t_usuario, t_obra, t_permiso, t_rol_permiso
-- ============================================================================

-- ────────────────────────────────────────────────────────────────────────────
-- 1. TABLA PRINCIPAL: t_avance_obra
--    Registra avances periódicos de las unidades de construcción de un proyecto.
--    Reutiliza t_unidad_construccion (ya existe) como entidad de referencia.
-- ────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS obras.t_avance_obra (
    id_avance          SERIAL PRIMARY KEY,
    id_obra            INTEGER NOT NULL,
    id_unidad          INTEGER NOT NULL,
    porcentaje_avance  NUMERIC(5,2) NOT NULL DEFAULT 0
                       CONSTRAINT chk_avance_porcentaje CHECK (porcentaje_avance BETWEEN 0 AND 100),
    fecha_registro     DATE NOT NULL DEFAULT CURRENT_DATE,
    observacion        TEXT,
    id_usuario         INTEGER NOT NULL,
    created_at         TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_avance_obra   FOREIGN KEY (id_obra)
        REFERENCES obras.t_obra(id_obra) ON DELETE CASCADE,
    CONSTRAINT fk_avance_unidad FOREIGN KEY (id_unidad)
        REFERENCES obras.t_unidad_construccion(id_unidad) ON DELETE CASCADE,
    CONSTRAINT fk_avance_usuario FOREIGN KEY (id_usuario)
        REFERENCES obras.t_usuario(id_usuario) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_avance_obra_id_obra    ON obras.t_avance_obra(id_obra);
CREATE INDEX IF NOT EXISTS idx_avance_obra_id_unidad  ON obras.t_avance_obra(id_unidad);
CREATE INDEX IF NOT EXISTS idx_avance_obra_fecha      ON obras.t_avance_obra(fecha_registro DESC);

COMMENT ON TABLE obras.t_avance_obra IS
  'CU18 – Registra el historial de avances de obra por unidad de construcción.';

-- ────────────────────────────────────────────────────────────────────────────
-- 2. PERMISOS CU18
--    Usa el mismo permiso Modificar_obras para registrar (ya tiene JEFE DE OBRA
--    y ADMINISTRADOR_EMPRESA). Agrega Registrar_avances y Visualizar_avances
--    para control fino.
-- ────────────────────────────────────────────────────────────────────────────

-- Insertar permisos solo si no existen
INSERT INTO obras.t_permiso (nombre_permiso)
SELECT 'Visualizar_avances'
WHERE NOT EXISTS (SELECT 1 FROM obras.t_permiso WHERE nombre_permiso = 'Visualizar_avances');

INSERT INTO obras.t_permiso (nombre_permiso)
SELECT 'Registrar_avances'
WHERE NOT EXISTS (SELECT 1 FROM obras.t_permiso WHERE nombre_permiso = 'Registrar_avances');

-- Asignar Visualizar_avances a: ADMINISTRADOR_EMPRESA (id=3), JEFE DE OBRA (id=4), CLIENTE (id=2)
INSERT INTO obras.t_rol_permiso (id_rol, id_permiso)
SELECT r.id_rol, p.id_permiso
FROM obras.t_rol r
CROSS JOIN obras.t_permiso p
WHERE r.nombre_rol IN ('ADMINISTRADOR_EMPRESA', 'JEFE DE OBRA', 'CLIENTE')
  AND p.nombre_permiso = 'Visualizar_avances'
ON CONFLICT DO NOTHING;

-- Asignar Registrar_avances a: ADMINISTRADOR_EMPRESA (id=3), JEFE DE OBRA (id=4)
INSERT INTO obras.t_rol_permiso (id_rol, id_permiso)
SELECT r.id_rol, p.id_permiso
FROM obras.t_rol r
CROSS JOIN obras.t_permiso p
WHERE r.nombre_rol IN ('ADMINISTRADOR_EMPRESA', 'JEFE DE OBRA')
  AND p.nombre_permiso = 'Registrar_avances'
ON CONFLICT DO NOTHING;

-- ────────────────────────────────────────────────────────────────────────────
-- 3. FUNCIÓN: fn_registrar_avance_obra
--    Registra un nuevo avance y actualiza el estado de la unidad si corresponde.
-- ────────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION obras.fn_registrar_avance_obra(
    p_id_obra           INTEGER,
    p_id_unidad         INTEGER,
    p_id_empresa        INTEGER,
    p_porcentaje        NUMERIC,
    p_fecha_registro    DATE,
    p_observacion       TEXT,
    p_id_usuario        INTEGER
) RETURNS JSON AS $$
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
$$ LANGUAGE plpgsql;

-- ────────────────────────────────────────────────────────────────────────────
-- 4. FUNCIÓN: fn_listar_avances_obra
--    Consulta el historial de avances de una obra con datos completos.
-- ────────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION obras.fn_listar_avances_obra(
    p_id_obra    INTEGER,
    p_id_empresa INTEGER,
    p_id_unidad  INTEGER DEFAULT NULL
) RETURNS JSON AS $$
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
$$ LANGUAGE plpgsql;

-- ────────────────────────────────────────────────────────────────────────────
-- 5. FUNCIÓN: fn_resumen_avances_obra
--    Retorna el avance más reciente por unidad + porcentaje global de obra.
-- ────────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION obras.fn_resumen_avances_obra(
    p_id_obra    INTEGER,
    p_id_empresa INTEGER
) RETURNS JSON AS $$
DECLARE
    v_obra_valida    BOOLEAN;
    v_resumen        JSON;
    v_avance_global  NUMERIC;
BEGIN
    SELECT EXISTS(
        SELECT 1 FROM obras.t_obra
        WHERE id_obra = p_id_obra
          AND (id_empresa = p_id_empresa OR p_id_empresa IS NULL)
    ) INTO v_obra_valida;

    IF NOT v_obra_valida THEN
        RETURN json_build_object('success', false,
            'error', 'El proyecto no existe o no pertenece a su empresa.');
    END IF;

    -- Último avance por unidad
    SELECT COALESCE(json_agg(
        json_build_object(
            'id_unidad',         u.id_unidad,
            'codigo_unidad',     u.codigo,
            'nombre_unidad',     e.nombre,
            'tipo_unidad',       u.tipo_unidad,
            'estado_unidad',     u.estado,
            'ultimo_avance',     COALESCE(ult.porcentaje_avance, 0),
            'fecha_ultimo',      ult.fecha_registro
        )
        ORDER BY e.nombre
    ), '[]'::json)
    INTO v_resumen
    FROM obras.t_unidad_construccion u
    INNER JOIN obras.t_estructura_obra e ON e.id_estructura = u.id_estructura
    LEFT JOIN LATERAL (
        SELECT porcentaje_avance, fecha_registro
        FROM obras.t_avance_obra
        WHERE id_unidad = u.id_unidad AND id_obra = p_id_obra
        ORDER BY created_at DESC
        LIMIT 1
    ) ult ON TRUE
    WHERE e.id_obra = p_id_obra;

    -- Promedio global
    SELECT COALESCE(AVG(sub.ult_pct), 0)
    INTO v_avance_global
    FROM (
        SELECT DISTINCT ON (a.id_unidad)
            a.porcentaje_avance AS ult_pct
        FROM obras.t_avance_obra a
        WHERE a.id_obra = p_id_obra
        ORDER BY a.id_unidad, a.created_at DESC
    ) sub;

    RETURN json_build_object(
        'success',          true,
        'avance_global',    ROUND(v_avance_global, 2),
        'unidades',         v_resumen
    );
END;
$$ LANGUAGE plpgsql;

-- ────────────────────────────────────────────────────────────────────────────
-- 6. FUNCIÓN: fn_eliminar_avance_obra
-- ────────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION obras.fn_eliminar_avance_obra(
    p_id_avance  INTEGER,
    p_id_obra    INTEGER,
    p_id_empresa INTEGER
) RETURNS JSON AS $$
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
$$ LANGUAGE plpgsql;
