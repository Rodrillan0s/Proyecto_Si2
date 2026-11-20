BEGIN;

SET search_path TO obras, public;

-- 1. Permisos del sistema
INSERT INTO obras.t_permiso (nombre_permiso)
VALUES
    ('Visualizar_ordenes_compra'),
    ('Registrar_ordenes_compra'),
    ('Aprobar_ordenes_compra'),
    ('Recepcionar_ordenes_compra')
ON CONFLICT DO NOTHING;

INSERT INTO obras.t_rol_permiso (id_rol, id_permiso)
SELECT r.id_rol, p.id_permiso
FROM obras.t_rol r
CROSS JOIN obras.t_permiso p
WHERE UPPER(r.nombre_rol) = 'ADMINISTRADOR_EMPRESA'
  AND p.nombre_permiso IN (
      'Visualizar_ordenes_compra',
      'Registrar_ordenes_compra',
      'Aprobar_ordenes_compra',
      'Recepcionar_ordenes_compra'
  )
ON CONFLICT DO NOTHING;

-- 2. Tabla de Orden de Compra
CREATE TABLE IF NOT EXISTS obras.t_orden_compra (
    id_orden_compra SERIAL PRIMARY KEY,
    id_empresa INT NOT NULL REFERENCES obras.t_empresa(id_empresa) ON DELETE RESTRICT,
    id_proveedor INT NOT NULL REFERENCES obras.t_proveedor(id_proveedor) ON DELETE RESTRICT,
    numero_orden VARCHAR(50) NOT NULL,
    fecha DATE NOT NULL DEFAULT CURRENT_DATE,
    observaciones TEXT,
    estado VARCHAR(30) NOT NULL DEFAULT 'BORRADOR',
    id_usuario_solicitante INT NOT NULL REFERENCES obras.t_usuario(id_usuario) ON DELETE RESTRICT,
    subtotal NUMERIC(15,2) NOT NULL DEFAULT 0.00,
    total NUMERIC(15,2) NOT NULL DEFAULT 0.00,
    id_usuario_aprobacion INT REFERENCES obras.t_usuario(id_usuario) ON DELETE SET NULL,
    fecha_aprobacion TIMESTAMPTZ,
    observacion_aprobacion TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_orden_compra_estado CHECK (
        estado IN ('BORRADOR', 'PENDIENTE_APROBACION', 'APROBADA', 'RECHAZADA', 'CANCELADA', 'RECIBIDA_PARCIAL', 'RECIBIDA')
    ),
    CONSTRAINT uq_orden_compra_empresa_numero UNIQUE (id_empresa, numero_orden)
);

CREATE INDEX IF NOT EXISTS idx_orden_compra_empresa ON obras.t_orden_compra(id_empresa);
CREATE INDEX IF NOT EXISTS idx_orden_compra_estado ON obras.t_orden_compra(id_empresa, estado);
CREATE INDEX IF NOT EXISTS idx_orden_compra_proveedor ON obras.t_orden_compra(id_proveedor);

-- 3. Tabla Detalle de Orden de Compra
CREATE TABLE IF NOT EXISTS obras.t_orden_compra_detalle (
    id_detalle SERIAL PRIMARY KEY,
    id_orden_compra INT NOT NULL REFERENCES obras.t_orden_compra(id_orden_compra) ON DELETE CASCADE,
    id_material INT NOT NULL REFERENCES obras.t_material(id_material) ON DELETE RESTRICT,
    cantidad_solicitada NUMERIC(14,3) NOT NULL CHECK (cantidad_solicitada > 0),
    precio_unitario NUMERIC(15,2) NOT NULL CHECK (precio_unitario >= 0),
    subtotal NUMERIC(15,2) NOT NULL CHECK (subtotal >= 0),
    cantidad_recibida NUMERIC(14,3) NOT NULL DEFAULT 0.00 CHECK (cantidad_recibida >= 0),

    CONSTRAINT chk_detalle_recibida_le_solicitada CHECK (cantidad_recibida <= cantidad_solicitada),
    CONSTRAINT uq_orden_compra_material UNIQUE (id_orden_compra, id_material)
);

CREATE INDEX IF NOT EXISTS idx_orden_compra_detalle_orden ON obras.t_orden_compra_detalle(id_orden_compra);
CREATE INDEX IF NOT EXISTS idx_orden_compra_detalle_material ON obras.t_orden_compra_detalle(id_material);

-- 4. Columnas de trazabilidad en t_movimiento_almacen
ALTER TABLE obras.t_movimiento_almacen
    ADD COLUMN IF NOT EXISTS tipo_movimiento VARCHAR(20) DEFAULT 'ENTRADA',
    ADD COLUMN IF NOT EXISTS id_empresa INT REFERENCES obras.t_empresa(id_empresa),
    ADD COLUMN IF NOT EXISTS id_orden_compra INT REFERENCES obras.t_orden_compra(id_orden_compra),
    ADD COLUMN IF NOT EXISTS id_usuario INT REFERENCES obras.t_usuario(id_usuario),
    ADD COLUMN IF NOT EXISTS observaciones TEXT,
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP;

-- 5. Tabla de Recepción de Compra
CREATE TABLE IF NOT EXISTS obras.t_recepcion_compra (
    id_recepcion SERIAL PRIMARY KEY,
    id_orden_compra INT NOT NULL REFERENCES obras.t_orden_compra(id_orden_compra) ON DELETE RESTRICT,
    id_empresa INT NOT NULL REFERENCES obras.t_empresa(id_empresa) ON DELETE RESTRICT,
    numero_recepcion VARCHAR(50) NOT NULL,
    fecha_recepcion TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    id_usuario_recepcion INT NOT NULL REFERENCES obras.t_usuario(id_usuario) ON DELETE RESTRICT,
    observaciones TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_recepcion_empresa_numero UNIQUE (id_empresa, numero_recepcion)
);

CREATE INDEX IF NOT EXISTS idx_recepcion_compra_orden ON obras.t_recepcion_compra(id_orden_compra);
CREATE INDEX IF NOT EXISTS idx_recepcion_compra_empresa ON obras.t_recepcion_compra(id_empresa);

-- 6. Agregar FK de recepcion a t_movimiento_almacen
ALTER TABLE obras.t_movimiento_almacen
    ADD COLUMN IF NOT EXISTS id_recepcion INT REFERENCES obras.t_recepcion_compra(id_recepcion);

-- 7. Tabla Detalle de Recepción de Compra
CREATE TABLE IF NOT EXISTS obras.t_recepcion_compra_detalle (
    id_recepcion_detalle SERIAL PRIMARY KEY,
    id_recepcion INT NOT NULL REFERENCES obras.t_recepcion_compra(id_recepcion) ON DELETE CASCADE,
    id_orden_compra_detalle INT NOT NULL REFERENCES obras.t_orden_compra_detalle(id_detalle) ON DELETE RESTRICT,
    id_material INT NOT NULL REFERENCES obras.t_material(id_material) ON DELETE RESTRICT,
    cantidad_recibida NUMERIC(14,3) NOT NULL CHECK (cantidad_recibida > 0),
    precio_unitario NUMERIC(15,2) NOT NULL DEFAULT 0.00,
    id_movimiento_almacen INT REFERENCES obras.t_movimiento_almacen(id_movimiento) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_recepcion_detalle_recepcion ON obras.t_recepcion_compra_detalle(id_recepcion);
CREATE INDEX IF NOT EXISTS idx_recepcion_detalle_oc_detalle ON obras.t_recepcion_compra_detalle(id_orden_compra_detalle);

-- 8. Trigger simple para updated_at en t_orden_compra
CREATE OR REPLACE FUNCTION obras.fn_orden_compra_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tg_orden_compra_updated_at ON obras.t_orden_compra;
CREATE TRIGGER tg_orden_compra_updated_at
BEFORE UPDATE ON obras.t_orden_compra
FOR EACH ROW EXECUTE FUNCTION obras.fn_orden_compra_updated_at();

-- 9. Funciones de negocio (fn_...)

-- 9.1 Generar número de orden de compra
CREATE OR REPLACE FUNCTION obras.fn_generar_numero_orden_compra(p_id_empresa INT)
RETURNS VARCHAR AS $$
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
$$ LANGUAGE plpgsql;

-- 9.2 Generar número de recepción
CREATE OR REPLACE FUNCTION obras.fn_generar_numero_recepcion(p_id_empresa INT)
RETURNS VARCHAR AS $$
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
$$ LANGUAGE plpgsql;

-- 9.3 Registrar orden de compra
CREATE OR REPLACE FUNCTION obras.fn_registrar_orden_compra(
    p_id_empresa INT,
    p_id_proveedor INT,
    p_id_usuario INT,
    p_fecha DATE,
    p_observaciones TEXT,
    p_estado VARCHAR,
    p_items_json JSONB
)
RETURNS INT AS $$
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
$$ LANGUAGE plpgsql;

-- 9.4 Cambiar estado de orden de compra (enviar a aprobación o cancelar)
CREATE OR REPLACE FUNCTION obras.fn_cambiar_estado_orden_compra(
    p_id_empresa INT,
    p_id_orden_compra INT,
    p_nuevo_estado VARCHAR
)
RETURNS BOOLEAN AS $$
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
$$ LANGUAGE plpgsql;

-- 9.5 Aprobar o rechazar orden de compra
CREATE OR REPLACE FUNCTION obras.fn_aprobar_rechazar_orden_compra(
    p_id_empresa INT,
    p_id_orden_compra INT,
    p_id_usuario INT,
    p_aprobar BOOLEAN,
    p_observacion TEXT
)
RETURNS BOOLEAN AS $$
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
$$ LANGUAGE plpgsql;

-- 9.6 Registrar recepción de materiales e impactar inventario
CREATE OR REPLACE FUNCTION obras.fn_registrar_recepcion_compra(
    p_id_empresa INT,
    p_id_orden_compra INT,
    p_id_usuario INT,
    p_observaciones TEXT,
    p_items_json JSONB
)
RETURNS INT AS $$
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
$$ LANGUAGE plpgsql;

-- 9.7 Consultar orden de compra y sus detalles
CREATE OR REPLACE FUNCTION obras.fn_consultar_orden_compra(
    p_id_empresa INT,
    p_id_orden_compra INT
)
RETURNS TABLE (
    id_orden_compra INT,
    numero_orden VARCHAR,
    fecha DATE,
    observaciones TEXT,
    estado VARCHAR,
    id_empresa INT,
    nombre_empresa VARCHAR,
    id_proveedor INT,
    nombre_proveedor VARCHAR,
    nit_proveedor VARCHAR,
    id_usuario_solicitante INT,
    nombre_solicitante VARCHAR,
    subtotal NUMERIC,
    total NUMERIC,
    id_usuario_aprobacion INT,
    nombre_aprobador VARCHAR,
    fecha_aprobacion TIMESTAMPTZ,
    observacion_aprobacion TEXT,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
) AS $$
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
        (pers_sol.nombre || ' ' || pers_sol.primer_apellido)::VARCHAR AS nombre_solicitante,
        oc.subtotal,
        oc.total,
        oc.id_usuario_aprobacion,
        CASE WHEN pers_aprob.id_persona IS NOT NULL 
             THEN (pers_aprob.nombre || ' ' || pers_aprob.primer_apellido)::VARCHAR 
             ELSE NULL END AS nombre_aprobador,
        oc.fecha_aprobacion,
        oc.observacion_aprobacion,
        oc.created_at,
        oc.updated_at
    FROM obras.t_orden_compra oc
    JOIN obras.t_empresa e ON e.id_empresa = oc.id_empresa
    JOIN obras.t_proveedor p ON p.id_proveedor = oc.id_proveedor
    JOIN obras.t_usuario u_sol ON u_sol.id_usuario = oc.id_usuario_solicitante
    JOIN obras.t_persona pers_sol ON pers_sol.id_persona = u_sol.id_persona
    LEFT JOIN obras.t_usuario u_aprob ON u_aprob.id_usuario = oc.id_usuario_aprobacion
    LEFT JOIN obras.t_persona pers_aprob ON pers_aprob.id_persona = u_aprob.id_persona
    WHERE oc.id_orden_compra = p_id_orden_compra
      AND (p_id_empresa IS NULL OR oc.id_empresa = p_id_empresa);
END;
$$ LANGUAGE plpgsql;

-- 9.8 Listar detalles de una orden de compra
CREATE OR REPLACE FUNCTION obras.fn_listar_detalles_orden_compra(p_id_orden_compra INT)
RETURNS TABLE (
    id_detalle INT,
    id_material INT,
    codigo_material VARCHAR,
    nombre_material VARCHAR,
    unidad_abreviatura VARCHAR,
    cantidad_solicitada NUMERIC,
    precio_unitario NUMERIC,
    subtotal NUMERIC,
    cantidad_recibida NUMERIC,
    cantidad_pendiente NUMERIC
) AS $$
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
$$ LANGUAGE plpgsql;

-- 9.9 Listar recepciones de una orden de compra
CREATE OR REPLACE FUNCTION obras.fn_listar_recepciones_orden(p_id_orden_compra INT)
RETURNS TABLE (
    id_recepcion INT,
    numero_recepcion VARCHAR,
    fecha_recepcion TIMESTAMPTZ,
    id_usuario_recepcion INT,
    nombre_usuario_recepcion VARCHAR,
    observaciones TEXT,
    total_items_recibidos BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        r.id_recepcion,
        r.numero_recepcion,
        r.fecha_recepcion,
        r.id_usuario_recepcion,
        (pers.nombre || ' ' || pers.primer_apellido)::VARCHAR AS nombre_usuario_recepcion,
        r.observaciones,
        COUNT(rd.id_recepcion_detalle) AS total_items_recibidos
    FROM obras.t_recepcion_compra r
    JOIN obras.t_usuario u ON u.id_usuario = r.id_usuario_recepcion
    JOIN obras.t_persona pers ON pers.id_persona = u.id_persona
    LEFT JOIN obras.t_recepcion_compra_detalle rd ON rd.id_recepcion = r.id_recepcion
    WHERE r.id_orden_compra = p_id_orden_compra
    GROUP BY r.id_recepcion, r.numero_recepcion, r.fecha_recepcion, r.id_usuario_recepcion, pers.nombre, pers.primer_apellido, r.observaciones
    ORDER BY r.fecha_recepcion DESC;
END;
$$ LANGUAGE plpgsql;

-- 9.10 Listar órdenes de compra paginado
CREATE OR REPLACE FUNCTION obras.fn_listar_ordenes_compra(
    p_id_empresa INT,
    p_q VARCHAR DEFAULT NULL,
    p_estado VARCHAR DEFAULT NULL,
    p_id_proveedor INT DEFAULT NULL,
    p_limit INT DEFAULT 20,
    p_offset INT DEFAULT 0
)
RETURNS TABLE (
    id_orden_compra INT,
    numero_orden VARCHAR,
    fecha DATE,
    observaciones TEXT,
    estado VARCHAR,
    id_empresa INT,
    nombre_empresa VARCHAR,
    id_proveedor INT,
    nombre_proveedor VARCHAR,
    id_usuario_solicitante INT,
    nombre_solicitante VARCHAR,
    subtotal NUMERIC,
    total NUMERIC,
    items_count BIGINT,
    items_recibidos_count BIGINT,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ,
    total_count BIGINT
) AS $$
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
            (pers_sol.nombre || ' ' || pers_sol.primer_apellido)::VARCHAR AS nombre_solicitante,
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
        JOIN obras.t_persona pers_sol ON pers_sol.id_persona = u_sol.id_persona
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
                 oc.id_usuario_solicitante, pers_sol.nombre, pers_sol.primer_apellido,
                 oc.subtotal, oc.total, oc.created_at, oc.updated_at
    )
    SELECT 
        f.*,
        COUNT(*) OVER() AS total_count
    FROM filtrados f
    ORDER BY f.id_orden_compra DESC
    LIMIT p_limit OFFSET p_offset;
END;
$$ LANGUAGE plpgsql;

COMMIT;
