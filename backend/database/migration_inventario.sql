-- =============================================================================
-- MIGRACIÓN: MÓDULO DE INVENTARIOS DE EMPRESA Y KARDEX
-- Esquema: obras
-- Fecha: 2026-09-17
-- =============================================================================

BEGIN;

-- 1. Asegurar índices de rendimiento para almacén y movimientos
CREATE INDEX IF NOT EXISTS idx_materiales_almacen_material ON obras.t_materiales_almacen (id_material);
CREATE INDEX IF NOT EXISTS idx_movimiento_almacen_empresa ON obras.t_movimiento_almacen (id_empresa, fecha_movimiento DESC);
CREATE INDEX IF NOT EXISTS idx_movimiento_almacen_material ON obras.t_movimiento_almacen (id_material);
CREATE INDEX IF NOT EXISTS idx_movimiento_almacen_orden ON obras.t_movimiento_almacen (id_orden_compra);

-- 2. FUNCIÓN: Listar Inventario Físico Valorizado de la Empresa
CREATE OR REPLACE FUNCTION obras.fn_listar_inventario_empresa(
    p_id_empresa INT,
    p_id_categoria INT DEFAULT NULL,
    p_estado_stock VARCHAR DEFAULT NULL,
    p_q VARCHAR DEFAULT NULL,
    p_limit INT DEFAULT 50,
    p_offset INT DEFAULT 0
)
RETURNS TABLE (
    id_material INT,
    codigo VARCHAR,
    nombre_material VARCHAR,
    descripcion TEXT,
    id_categoria INT,
    categoria_nombre VARCHAR,
    id_unidad_medida INT,
    unidad_nombre VARCHAR,
    unidad_abreviatura VARCHAR,
    precio NUMERIC(15,2),
    stock_actual NUMERIC(15,3),
    stock_minimo NUMERIC(15,3),
    valor_total NUMERIC(15,2),
    estado_stock VARCHAR(20),
    id_empresa INT,
    nombre_empresa VARCHAR,
    total_count BIGINT
) LANGUAGE plpgsql AS $$
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
$$;

-- 3. FUNCIÓN: Resumen de KPIs y Métricas de Inventario
CREATE OR REPLACE FUNCTION obras.fn_resumen_kpis_inventario(p_id_empresa INT)
RETURNS TABLE (
    total_materiales INT,
    total_con_stock INT,
    total_sin_stock INT,
    total_stock_bajo INT,
    valor_total_inventario NUMERIC(15,2),
    total_movimientos_mes INT
) LANGUAGE plpgsql AS $$
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
$$;

-- 4. FUNCIÓN: Registrar Ajuste de Inventario o Stock Mínimo
CREATE OR REPLACE FUNCTION obras.fn_registrar_ajuste_inventario(
    p_id_empresa INT,
    p_id_material INT,
    p_cantidad NUMERIC,
    p_tipo_movimiento VARCHAR,
    p_id_usuario INT,
    p_observaciones TEXT,
    p_stock_minimo NUMERIC DEFAULT NULL
)
RETURNS TABLE (
    id_material INT,
    nuevo_stock NUMERIC(15,3),
    stock_minimo NUMERIC(15,3),
    id_movimiento INT
) LANGUAGE plpgsql AS $$
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
$$;

-- 5. FUNCIÓN: Listar Movimientos de Almacén (Kardex)
CREATE OR REPLACE FUNCTION obras.fn_listar_movimientos_almacen(
    p_id_empresa INT,
    p_id_material INT DEFAULT NULL,
    p_tipo_movimiento VARCHAR DEFAULT NULL,
    p_limit INT DEFAULT 50,
    p_offset INT DEFAULT 0
)
RETURNS TABLE (
    id_movimiento INT,
    fecha_movimiento DATE,
    created_at TIMESTAMPTZ,
    tipo_movimiento VARCHAR,
    cantidad_asignada NUMERIC(14,3),
    id_material INT,
    material_codigo VARCHAR,
    material_nombre VARCHAR,
    unidad_abreviatura VARCHAR,
    id_orden_compra INT,
    numero_orden VARCHAR,
    id_recepcion INT,
    numero_recepcion VARCHAR,
    id_usuario INT,
    nombre_usuario VARCHAR,
    observaciones TEXT,
    total_count BIGINT
) LANGUAGE plpgsql AS $$
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
$$;

COMMIT;
