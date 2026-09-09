-- ============================================================================
-- MIGRACIÓN CU12: Gestión integral de unidades de construcción
-- IMPORTANTE: revisar y ejecutar manualmente. No reemplaza la migración HU35.
-- ============================================================================

CREATE SEQUENCE IF NOT EXISTS obras.seq_codigo_unidad START WITH 1 INCREMENT BY 1;

CREATE OR REPLACE FUNCTION obras.fn_generar_codigo_unidad()
RETURNS varchar AS $$
BEGIN
    RETURN 'UNI-' || LPAD(nextval('obras.seq_codigo_unidad')::text, 6, '0');
END;
$$ LANGUAGE plpgsql;

CREATE TABLE IF NOT EXISTS obras.t_modelo_unidad (
    id_modelo SERIAL PRIMARY KEY,
    id_empresa INTEGER NOT NULL,
    nombre VARCHAR(120) NOT NULL,
    descripcion TEXT,
    tipo_unidad VARCHAR(30) NOT NULL DEFAULT 'OTRO',
    superficie_base NUMERIC(12,2),
    cantidad_plantas_base INTEGER,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_modelo_unidad_empresa FOREIGN KEY (id_empresa)
        REFERENCES obras.t_empresa(id_empresa) ON DELETE RESTRICT,
    CONSTRAINT chk_modelo_tipo_unidad CHECK (
        tipo_unidad IN ('VIVIENDA', 'DEPARTAMENTO', 'LOCAL', 'LOTE', 'OFICINA', 'OTRO')
    ),
    CONSTRAINT chk_modelo_superficie CHECK (superficie_base IS NULL OR superficie_base >= 0),
    CONSTRAINT chk_modelo_plantas CHECK (cantidad_plantas_base IS NULL OR cantidad_plantas_base >= 0),
    CONSTRAINT uq_modelo_unidad_empresa_nombre UNIQUE (id_empresa, nombre)
);

CREATE TABLE IF NOT EXISTS obras.t_modelo_caracteristica (
    id_modelo_caracteristica SERIAL PRIMARY KEY,
    id_modelo INTEGER NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    valor VARCHAR(250) NOT NULL,
    CONSTRAINT fk_modelo_caracteristica_modelo FOREIGN KEY (id_modelo)
        REFERENCES obras.t_modelo_unidad(id_modelo) ON DELETE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_modelo_caracteristica_nombre
    ON obras.t_modelo_caracteristica(id_modelo, LOWER(nombre));

CREATE TABLE IF NOT EXISTS obras.t_unidad_construccion (
    id_unidad SERIAL PRIMARY KEY,
    id_estructura INTEGER NOT NULL,
    codigo VARCHAR(20) NOT NULL DEFAULT obras.fn_generar_codigo_unidad(),
    tipo_unidad VARCHAR(30) NOT NULL DEFAULT 'OTRO',
    superficie NUMERIC(12,2) NOT NULL DEFAULT 0,
    cantidad_plantas INTEGER NOT NULL DEFAULT 0,
    estado VARCHAR(30) NOT NULL DEFAULT 'PLANIFICADO',
    id_modelo INTEGER NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_unidad_estructura FOREIGN KEY (id_estructura)
        REFERENCES obras.t_estructura_obra(id_estructura) ON DELETE RESTRICT,
    CONSTRAINT fk_unidad_modelo FOREIGN KEY (id_modelo)
        REFERENCES obras.t_modelo_unidad(id_modelo) ON DELETE SET NULL,
    CONSTRAINT uq_unidad_estructura UNIQUE (id_estructura),
    CONSTRAINT uq_unidad_codigo UNIQUE (codigo),
    CONSTRAINT chk_unidad_tipo CHECK (
        tipo_unidad IN ('VIVIENDA', 'DEPARTAMENTO', 'LOCAL', 'LOTE', 'OFICINA', 'OTRO')
    ),
    CONSTRAINT chk_unidad_superficie CHECK (superficie >= 0),
    CONSTRAINT chk_unidad_plantas CHECK (cantidad_plantas >= 0),
    CONSTRAINT chk_unidad_estado CHECK (
        estado IN ('PLANIFICADO', 'EN_CONSTRUCCION', 'FINALIZADO', 'SUSPENDIDO')
    )
);

CREATE TABLE IF NOT EXISTS obras.t_unidad_ambiente (
    id_ambiente SERIAL PRIMARY KEY,
    id_unidad INTEGER NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    cantidad INTEGER NOT NULL DEFAULT 1,
    CONSTRAINT fk_unidad_ambiente_unidad FOREIGN KEY (id_unidad)
        REFERENCES obras.t_unidad_construccion(id_unidad) ON DELETE CASCADE,
    CONSTRAINT chk_unidad_ambiente_cantidad CHECK (cantidad > 0)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_unidad_ambiente_nombre
    ON obras.t_unidad_ambiente(id_unidad, LOWER(nombre));

CREATE TABLE IF NOT EXISTS obras.t_unidad_caracteristica (
    id_caracteristica SERIAL PRIMARY KEY,
    id_unidad INTEGER NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    valor VARCHAR(250) NOT NULL,
    CONSTRAINT fk_unidad_caracteristica_unidad FOREIGN KEY (id_unidad)
        REFERENCES obras.t_unidad_construccion(id_unidad) ON DELETE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_unidad_caracteristica_nombre
    ON obras.t_unidad_caracteristica(id_unidad, LOWER(nombre));

CREATE TABLE IF NOT EXISTS obras.t_unidad_personalizacion (
    id_personalizacion SERIAL PRIMARY KEY,
    id_unidad INTEGER NOT NULL,
    tipo VARCHAR(50) NOT NULL,
    descripcion TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_unidad_personalizacion_unidad FOREIGN KEY (id_unidad)
        REFERENCES obras.t_unidad_construccion(id_unidad) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS obras.t_unidad_seguimiento (
    id_seguimiento SERIAL PRIMARY KEY,
    id_unidad INTEGER NOT NULL,
    estado_anterior VARCHAR(30),
    estado_nuevo VARCHAR(30) NOT NULL,
    id_usuario INTEGER NULL,
    observacion TEXT,
    fecha TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_unidad_seguimiento_unidad FOREIGN KEY (id_unidad)
        REFERENCES obras.t_unidad_construccion(id_unidad) ON DELETE CASCADE,
    CONSTRAINT fk_unidad_seguimiento_usuario FOREIGN KEY (id_usuario)
        REFERENCES obras.t_usuario(id_usuario) ON DELETE SET NULL,
    CONSTRAINT chk_seguimiento_estado_nuevo CHECK (
        estado_nuevo IN ('PLANIFICADO', 'EN_CONSTRUCCION', 'FINALIZADO', 'SUSPENDIDO')
    ),
    CONSTRAINT chk_seguimiento_estado_anterior CHECK (
        estado_anterior IS NULL OR estado_anterior IN ('PLANIFICADO', 'EN_CONSTRUCCION', 'FINALIZADO', 'SUSPENDIDO')
    )
);

-- Asociación de especificación. CU14 conserva la responsabilidad sobre el catálogo.
CREATE TABLE IF NOT EXISTS obras.t_unidad_material (
    id_unidad_material SERIAL PRIMARY KEY,
    id_unidad INTEGER NOT NULL,
    id_material INTEGER NOT NULL,
    cantidad NUMERIC(14,3) NOT NULL DEFAULT 1,
    unidad_medida VARCHAR(30),
    uso_ubicacion VARCHAR(150),
    acabado VARCHAR(150),
    observacion TEXT,
    CONSTRAINT fk_unidad_material_unidad FOREIGN KEY (id_unidad)
        REFERENCES obras.t_unidad_construccion(id_unidad) ON DELETE CASCADE,
    CONSTRAINT fk_unidad_material_material FOREIGN KEY (id_material)
        REFERENCES obras.t_material(id_material) ON DELETE RESTRICT,
    CONSTRAINT chk_unidad_material_cantidad CHECK (cantidad > 0),
    CONSTRAINT uq_unidad_material_uso UNIQUE (id_unidad, id_material, uso_ubicacion)
);

CREATE INDEX IF NOT EXISTS idx_modelo_unidad_empresa ON obras.t_modelo_unidad(id_empresa);
CREATE INDEX IF NOT EXISTS idx_unidad_modelo ON obras.t_unidad_construccion(id_modelo);
CREATE INDEX IF NOT EXISTS idx_unidad_ambiente_unidad ON obras.t_unidad_ambiente(id_unidad);
CREATE INDEX IF NOT EXISTS idx_unidad_caracteristica_unidad ON obras.t_unidad_caracteristica(id_unidad);
CREATE INDEX IF NOT EXISTS idx_unidad_personalizacion_unidad ON obras.t_unidad_personalizacion(id_unidad);
CREATE INDEX IF NOT EXISTS idx_unidad_seguimiento_unidad_fecha ON obras.t_unidad_seguimiento(id_unidad, fecha DESC);
CREATE INDEX IF NOT EXISTS idx_unidad_material_unidad ON obras.t_unidad_material(id_unidad);
CREATE INDEX IF NOT EXISTS idx_unidad_material_material ON obras.t_unidad_material(id_material);

CREATE OR REPLACE FUNCTION obras.fn_actualizar_updated_at_cu12()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tg_actualizar_modelo_unidad ON obras.t_modelo_unidad;
CREATE TRIGGER tg_actualizar_modelo_unidad
BEFORE UPDATE ON obras.t_modelo_unidad
FOR EACH ROW EXECUTE FUNCTION obras.fn_actualizar_updated_at_cu12();

DROP TRIGGER IF EXISTS tg_actualizar_unidad_construccion ON obras.t_unidad_construccion;
CREATE TRIGGER tg_actualizar_unidad_construccion
BEFORE UPDATE ON obras.t_unidad_construccion
FOR EACH ROW EXECUTE FUNCTION obras.fn_actualizar_updated_at_cu12();

-- Protege tanto el nodo-unidad como cualquier ancestro cuyo borrado alcanzaría
-- una unidad por la cascada jerárquica de HU35.
CREATE OR REPLACE FUNCTION obras.fn_proteger_unidades_estructura()
RETURNS TRIGGER AS $$
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
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tg_proteger_unidades_estructura ON obras.t_estructura_obra;
CREATE TRIGGER tg_proteger_unidades_estructura
BEFORE DELETE ON obras.t_estructura_obra
FOR EACH ROW EXECUTE FUNCTION obras.fn_proteger_unidades_estructura();

CREATE OR REPLACE FUNCTION obras.fn_registrar_unidad_construccion(
    p_id_obra INTEGER,
    p_id_empresa INTEGER,
    p_id_usuario INTEGER,
    p_id_estructura INTEGER,
    p_id_padre INTEGER,
    p_nombre VARCHAR,
    p_tipo_estructura VARCHAR,
    p_descripcion TEXT,
    p_tipo_unidad VARCHAR,
    p_superficie NUMERIC,
    p_cantidad_plantas INTEGER,
    p_estado VARCHAR,
    p_id_modelo INTEGER,
    p_ambientes JSON,
    p_caracteristicas JSON
) RETURNS JSON AS $$
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
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION obras.fn_actualizar_unidad_construccion(
    p_id_obra INTEGER,
    p_id_unidad INTEGER,
    p_id_empresa INTEGER,
    p_nombre VARCHAR,
    p_descripcion TEXT,
    p_tipo_unidad VARCHAR,
    p_superficie NUMERIC,
    p_cantidad_plantas INTEGER,
    p_id_modelo INTEGER,
    p_ambientes JSON,
    p_caracteristicas JSON
) RETURNS JSON AS $$
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
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION obras.fn_cambiar_estado_unidad(
    p_id_obra INTEGER,
    p_id_unidad INTEGER,
    p_id_empresa INTEGER,
    p_estado_nuevo VARCHAR,
    p_id_usuario INTEGER,
    p_observacion TEXT
) RETURNS JSON AS $$
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
$$ LANGUAGE plpgsql;
