-- =============================================================================
-- MIGRACIÓN: REDISEÑO DE ANÁLISIS DE PRECIOS UNITARIOS (APU)
-- Esquema: obras
-- Fecha: 2026-09-17
-- =============================================================================

BEGIN;

-- 1. CREACIÓN DE CATÁLOGO GLOBAL DE CATEGORÍAS DE APU
CREATE TABLE IF NOT EXISTS obras.t_categoria_apu (
    id_categoria SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    descripcion TEXT,
    icono VARCHAR(50) DEFAULT 'folder',
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Inserción / normalización de las 28 categorías base
INSERT INTO obras.t_categoria_apu (nombre, descripcion, icono) VALUES
    ('ALFOMBRAS', 'Suministro e instalación de alfombras y tapices de piso', 'layers'),
    ('ARTEFACTOS SANITARIOS', 'Inodoros, lavamanos, tinas, duchas y griferías', 'droplet'),
    ('CARPINTERÍA DE ALUMINIO', 'Ventanas, mamparas y perfiles de aluminio', 'maximize'),
    ('CARPINTERÍA DE MADERA', 'Puertas, marcos, zócalos y revestimientos de madera', 'box'),
    ('CERRAJERÍA', 'Chapas, candados, jaladores y accesorios de seguridad', 'key'),
    ('CERRAMIENTOS', 'Muros perimetrales, rejas y mallas de cerramiento', 'shield'),
    ('CUBIERTAS Y CIELORRASOS', 'Tejados, calaminas, cielos falsos y aislantes', 'home'),
    ('DEMOLICIÓN', 'Demolición manual y mecanizada, retiros y picado', 'trash-2'),
    ('DRENAJE PLUVIAL', 'Canaletas, bajantes y tuberías de evacuación pluvial', 'cloud-rain'),
    ('HORMIGONES', 'Hormigón armado, simple, ciclópeo, zapatas, vigas y columnas', 'database'),
    ('IMPERMEABILIZACIÓN', 'Impermeabilización de losas, sobrecimientos y tanques', 'umbrella'),
    ('INSTALACIÓN ELÉCTRICA', 'Cableado, tableros, tomas e iluminación interior', 'zap'),
    ('INSTALACIÓN HIDRÁULICA', 'Red de agua fría y caliente, bombas y presurizadores', 'activity'),
    ('INSTALACIÓN SANITARIA', 'Cámaras de inspección, desagües y ventilación cloacal', 'filter'),
    ('JARDINERÍA Y VEGETACIÓN', 'Paisajismo, siembra de césped, plantas y riego', 'feather'),
    ('MAMPOSTERÍA', 'Muros de ladrillo cerámico, adobe, bloquetas y tabiques', 'grid'),
    ('MESONES', 'Mesones de granito, mármol, hormigón y microcemento', 'layout'),
    ('METÁLICOS', 'Estructuras metálicas, tinglados, barandas y cerchas', 'tool'),
    ('MOVIMIENTO DE TIERRAS', 'Excavaciones, rellenos, compactado y nivelación', 'truck'),
    ('OBRAS COMPLEMENTARIAS', 'Limpieza general, retiro de escombros y cerramientos de obra', 'check-circle'),
    ('OBRAS PRELIMINARES', 'Instalación de faenas, replanteo y trazado topográfico', 'compass'),
    ('PINTURAS', 'Látex, acrílico, anticorrosivo, barnices y esmaltes', 'edit-3'),
    ('PISOS Y CONTRAPISOS', 'Cerámica, porcelanato, contrapisos de cemento y parquet', 'trello'),
    ('QUINCALLERÍA', 'Bisagras, correderas, rieles y tornillería especializada', 'disc'),
    ('REVESTIMIENTOS', 'Azulejos, texturas, revoque interior/exterior y estuco', 'sun'),
    ('SISTEMA ELÉCTRICO', 'Acometidas de media tensión, transformadores y pozos a tierra', 'cpu'),
    ('VIAL', 'Cordones, aceras, pavimentos rígidos, flexibles y adoquines', 'navigation'),
    ('VIDRIOS', 'Vidrios templados, laminados, flotados y espejos', 'square')
ON CONFLICT (nombre) DO NOTHING;

-- 2. AMPLIACIÓN DE OBRAS.T_APU
-- Permitir que id_empresa sea nulo para APUs del Catálogo Base OBRATEC
ALTER TABLE obras.t_apu ALTER COLUMN id_empresa DROP NOT NULL;

-- Agregar columna es_base
ALTER TABLE obras.t_apu ADD COLUMN IF NOT EXISTS es_base BOOLEAN NOT NULL DEFAULT FALSE;

-- Agregar clave foránea a categoría
ALTER TABLE obras.t_apu ADD COLUMN IF NOT EXISTS id_categoria INT REFERENCES obras.t_categoria_apu(id_categoria) ON DELETE RESTRICT;

-- Agregar trazabilidad al APU base de origen
ALTER TABLE obras.t_apu ADD COLUMN IF NOT EXISTS id_apu_base INT REFERENCES obras.t_apu(id_apu) ON DELETE SET NULL;

-- Agregar columnas de factores y precio unitario
ALTER TABLE obras.t_apu ADD COLUMN IF NOT EXISTS porcentaje_gastos_generales NUMERIC(5,2) NOT NULL DEFAULT 8.00;
ALTER TABLE obras.t_apu ADD COLUMN IF NOT EXISTS monto_gastos_generales NUMERIC(15,2) NOT NULL DEFAULT 0.00;
ALTER TABLE obras.t_apu ADD COLUMN IF NOT EXISTS porcentaje_utilidad NUMERIC(5,2) NOT NULL DEFAULT 15.00;
ALTER TABLE obras.t_apu ADD COLUMN IF NOT EXISTS monto_utilidad NUMERIC(15,2) NOT NULL DEFAULT 0.00;
ALTER TABLE obras.t_apu ADD COLUMN IF NOT EXISTS porcentaje_impuestos NUMERIC(5,2) NOT NULL DEFAULT 3.09;
ALTER TABLE obras.t_apu ADD COLUMN IF NOT EXISTS monto_impuestos NUMERIC(15,2) NOT NULL DEFAULT 0.00;
ALTER TABLE obras.t_apu ADD COLUMN IF NOT EXISTS precio_unitario NUMERIC(15,2) NOT NULL DEFAULT 0.00;

-- Índices de consulta rápida
CREATE INDEX IF NOT EXISTS idx_apu_empresa_categoria ON obras.t_apu (id_empresa, id_categoria);
CREATE INDEX IF NOT EXISTS idx_apu_es_base ON obras.t_apu (es_base);
CREATE INDEX IF NOT EXISTS idx_apu_es_vigente ON obras.t_apu (es_vigente);
CREATE INDEX IF NOT EXISTS idx_apu_codigo_base ON obras.t_apu (codigo_base);

-- Asignar categoría por defecto a APUs existentes si están nulas
UPDATE obras.t_apu 
SET id_categoria = (SELECT id_categoria FROM obras.t_categoria_apu WHERE nombre = 'PISOS Y CONTRAPISOS')
WHERE id_categoria IS NULL AND (nombre ILIKE '%piso%' OR nombre ILIKE '%cerámica%' OR nombre ILIKE '%ceramico%');

UPDATE obras.t_apu 
SET id_categoria = (SELECT id_categoria FROM obras.t_categoria_apu WHERE nombre = 'HORMIGONES')
WHERE id_categoria IS NULL AND nombre ILIKE '%hormig%';

UPDATE obras.t_apu 
SET id_categoria = (SELECT id_categoria FROM obras.t_categoria_apu WHERE nombre = 'OBRAS PRELIMINARES')
WHERE id_categoria IS NULL;

-- 3. CORRECCIÓN Y NORMALIZACIÓN DE OBRAS.T_APU_COMPONENTE
-- Eliminar restricciones conflictivas sobre id_recurso
ALTER TABLE obras.t_apu_componente DROP CONSTRAINT IF EXISTS fk_apu_comp_material;
ALTER TABLE obras.t_apu_componente DROP CONSTRAINT IF EXISTS fk_apu_comp_equipo;

-- Agregar columnas dedicadas para cada catálogo existente
ALTER TABLE obras.t_apu_componente ADD COLUMN IF NOT EXISTS id_material INT REFERENCES obras.t_material(id_material) ON DELETE SET NULL;
ALTER TABLE obras.t_apu_componente ADD COLUMN IF NOT EXISTS id_mano_obra INT REFERENCES obras.t_mano_obra(id_mano_obra) ON DELETE SET NULL;
ALTER TABLE obras.t_apu_componente ADD COLUMN IF NOT EXISTS id_equipo INT REFERENCES obras.t_equipo(id_equipo) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_apu_comp_material ON obras.t_apu_componente (id_material);
CREATE INDEX IF NOT EXISTS idx_apu_comp_mano_obra ON obras.t_apu_componente (id_mano_obra);
CREATE INDEX IF NOT EXISTS idx_apu_comp_equipo ON obras.t_apu_componente (id_equipo);

-- 4. FUNCIONES ALMACENADAS DE CÁLCULO Y GESTIÓN (PREFIJO fn_)

-- 4.1 fn_calcular_apu: Calcula costo directo y aplica factores paramétricos
CREATE OR REPLACE FUNCTION obras.fn_calcular_apu(p_id_apu INT)
RETURNS TABLE (
    id_apu INT,
    costo_materiales NUMERIC(15,2),
    costo_mano_obra NUMERIC(15,2),
    costo_equipos NUMERIC(15,2),
    costo_directo NUMERIC(15,2),
    monto_gastos_generales NUMERIC(15,2),
    monto_utilidad NUMERIC(15,2),
    monto_impuestos NUMERIC(15,2),
    precio_unitario NUMERIC(15,2)
) LANGUAGE plpgsql AS $$
DECLARE
    v_mat NUMERIC(15,2) := 0.00;
    v_mo  NUMERIC(15,2) := 0.00;
    v_eq  NUMERIC(15,2) := 0.00;
    v_cd  NUMERIC(15,2) := 0.00;
    v_pct_gg NUMERIC(5,2) := 8.00;
    v_monto_gg NUMERIC(15,2) := 0.00;
    v_pct_ut NUMERIC(5,2) := 15.00;
    v_monto_ut NUMERIC(15,2) := 0.00;
    v_pct_it NUMERIC(5,2) := 3.09;
    v_monto_it NUMERIC(15,2) := 0.00;
    v_pu NUMERIC(15,2) := 0.00;
BEGIN
    -- 1. Calcular subtotales por tipo de recurso
    SELECT 
        COALESCE(SUM(CASE WHEN tipo_recurso = 'MATERIAL' THEN subtotal ELSE 0 END), 0.00),
        COALESCE(SUM(CASE WHEN tipo_recurso = 'MANO_OBRA' THEN subtotal ELSE 0 END), 0.00),
        COALESCE(SUM(CASE WHEN tipo_recurso = 'EQUIPO' THEN subtotal ELSE 0 END), 0.00)
    INTO v_mat, v_mo, v_eq
    FROM obras.t_apu_componente
    WHERE t_apu_componente.id_apu = p_id_apu;

    v_cd := v_mat + v_mo + v_eq;

    -- 2. Obtener porcentajes configurados en el APU
    SELECT 
        COALESCE(porcentaje_gastos_generales, 8.00),
        COALESCE(porcentaje_utilidad, 15.00),
        COALESCE(porcentaje_impuestos, 3.09)
    INTO v_pct_gg, v_pct_ut, v_pct_it
    FROM obras.t_apu
    WHERE t_apu.id_apu = p_id_apu;

    -- 3. Cálculo de factores en cascada estándar
    -- GG = CD * %GG
    v_monto_gg := ROUND(v_cd * (v_pct_gg / 100.0), 2);
    -- Utilidad = (CD + GG) * %UT
    v_monto_ut := ROUND((v_cd + v_monto_gg) * (v_pct_ut / 100.0), 2);
    -- Impuestos = (CD + GG + UT) * %IT
    v_monto_it := ROUND((v_cd + v_monto_gg + v_monto_ut) * (v_pct_it / 100.0), 2);
    -- Precio Unitario Final
    v_pu := v_cd + v_monto_gg + v_monto_ut + v_monto_it;

    -- 4. Actualizar tabla t_apu
    UPDATE obras.t_apu
    SET costo_materiales = v_mat,
        costo_mano_obra = v_mo,
        costo_equipos = v_eq,
        costo_directo = v_cd,
        costo_unitario_total = v_cd,
        monto_gastos_generales = v_monto_gg,
        monto_utilidad = v_monto_ut,
        monto_impuestos = v_monto_it,
        precio_unitario = v_pu,
        updated_at = CURRENT_TIMESTAMP
    WHERE t_apu.id_apu = p_id_apu;

    RETURN QUERY
    SELECT p_id_apu, v_mat, v_mo, v_eq, v_cd, v_monto_gg, v_monto_ut, v_monto_it, v_pu;
END;
$$;

-- 4.2 fn_copiar_apu_base_empresa: Copia un APU base hacia una empresa
CREATE OR REPLACE FUNCTION obras.fn_copiar_apu_base_empresa(
    p_id_apu_base INT,
    p_id_empresa INT,
    p_codigo_personalizado VARCHAR DEFAULT NULL
)
RETURNS INT LANGUAGE plpgsql AS $$
DECLARE
    v_base RECORD;
    v_nuevo_id INT;
    v_nuevo_codigo VARCHAR(50);
    v_anio INT := EXTRACT(YEAR FROM CURRENT_DATE);
    v_seq INT;
    v_comp RECORD;
    v_id_mat_emp INT;
    v_precio_mat NUMERIC(15,2);
    v_id_mo_emp INT;
    v_precio_mo NUMERIC(15,2);
    v_id_eq_emp INT;
    v_precio_eq NUMERIC(15,2);
    v_precio_comp NUMERIC(15,2);
    v_subtotal_comp NUMERIC(15,2);
BEGIN
    -- Validar que el APU base exista
    SELECT * INTO v_base FROM obras.t_apu WHERE id_apu = p_id_apu_base;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'El APU base ID % no existe.', p_id_apu_base;
    END IF;

    -- Generar código si no se especificó uno
    IF p_codigo_personalizado IS NOT NULL AND TRIM(p_codigo_personalizado) <> '' THEN
        v_nuevo_codigo := TRIM(p_codigo_personalizado);
    ELSE
        SELECT COALESCE(MAX(
            CASE 
                WHEN codigo ~ '^APU-[0-9]{4}-[0-9]+' THEN 
                    SPLIT_PART(codigo, '-', 3)::INT
                ELSE 0
            END
        ), 0) + 1 INTO v_seq
        FROM obras.t_apu
        WHERE id_empresa = p_id_empresa;

        v_nuevo_codigo := 'APU-' || v_anio::TEXT || '-' || LPAD(v_seq::TEXT, 4, '0');
    END IF;

    -- Insertar encabezado del APU copiado para la empresa
    INSERT INTO obras.t_apu (
        id_empresa,
        id_obra,
        codigo,
        codigo_base,
        version,
        nombre,
        descripcion,
        id_unidad_medida,
        rendimiento_base,
        id_categoria,
        es_base,
        id_apu_base,
        porcentaje_gastos_generales,
        porcentaje_utilidad,
        porcentaje_impuestos,
        estado,
        es_vigente
    ) VALUES (
        p_id_empresa,
        NULL,
        v_nuevo_codigo,
        COALESCE(v_base.codigo_base, v_base.codigo),
        1,
        v_base.nombre,
        v_base.descripcion,
        v_base.id_unidad_medida,
        v_base.rendimiento_base,
        v_base.id_categoria,
        FALSE,
        v_base.id_apu,
        v_base.porcentaje_gastos_generales,
        v_base.porcentaje_utilidad,
        v_base.porcentaje_impuestos,
        'ACTIVO',
        TRUE
    ) RETURNING id_apu INTO v_nuevo_id;

    -- Clonar componentes adaptando a recursos de la empresa
    FOR v_comp IN 
        SELECT * FROM obras.t_apu_componente WHERE id_apu = p_id_apu_base
    LOOP
        v_id_mat_emp := NULL;
        v_id_mo_emp := NULL;
        v_id_eq_emp := NULL;
        v_precio_comp := v_comp.precio_unitario;

        IF v_comp.tipo_recurso = 'MATERIAL' THEN
            -- Buscar material equivalente en el catálogo de la empresa
            IF v_comp.id_material IS NOT NULL THEN
                SELECT m_emp.id_material, m_emp.precio 
                INTO v_id_mat_emp, v_precio_mat
                FROM obras.t_material m_base
                JOIN obras.t_material m_emp 
                  ON m_emp.id_empresa = p_id_empresa 
                 AND (m_emp.codigo = m_base.codigo OR m_emp.id_material_base = m_base.id_material)
                WHERE m_base.id_material = v_comp.id_material
                LIMIT 1;

                IF v_id_mat_emp IS NOT NULL AND v_precio_mat > 0 THEN
                    v_precio_comp := v_precio_mat;
                END IF;
            END IF;

        ELSIF v_comp.tipo_recurso = 'MANO_OBRA' THEN
            -- Buscar recurso de mano de obra en la empresa con nombre similar
            SELECT id_mano_obra, costo_unitario 
            INTO v_id_mo_emp, v_precio_mo
            FROM obras.t_mano_obra
            WHERE id_empresa = p_id_empresa AND activo = TRUE
              AND nombre ILIKE '%' || SPLIT_PART(v_comp.descripcion_recurso, ':', 1) || '%'
            ORDER BY id_mano_obra ASC
            LIMIT 1;

            IF v_id_mo_emp IS NOT NULL AND v_precio_mo > 0 THEN
                v_precio_comp := v_precio_mo;
            END IF;

        ELSIF v_comp.tipo_recurso = 'EQUIPO' THEN
            -- Buscar equipo en la empresa
            SELECT id_equipo, costo_unitario 
            INTO v_id_eq_emp, v_precio_eq
            FROM obras.t_equipo
            WHERE id_empresa = p_id_empresa AND activo = TRUE
              AND nombre ILIKE '%' || SPLIT_PART(v_comp.descripcion_recurso, ':', 1) || '%'
            ORDER BY id_equipo ASC
            LIMIT 1;

            IF v_id_eq_emp IS NOT NULL AND v_precio_eq > 0 THEN
                v_precio_comp := v_precio_eq;
            END IF;
        END IF;

        v_subtotal_comp := ROUND(COALESCE(v_comp.rendimiento, v_comp.cantidad, 1.0) * v_precio_comp, 2);

        INSERT INTO obras.t_apu_componente (
            id_apu,
            tipo_recurso,
            id_recurso,
            id_material,
            id_mano_obra,
            id_equipo,
            descripcion_recurso,
            id_unidad_medida,
            cantidad,
            rendimiento,
            precio_unitario,
            subtotal
        ) VALUES (
            v_nuevo_id,
            v_comp.tipo_recurso,
            COALESCE(v_id_mat_emp, v_id_mo_emp, v_id_eq_emp, v_comp.id_recurso),
            v_id_mat_emp,
            v_id_mo_emp,
            v_id_eq_emp,
            v_comp.descripcion_recurso,
            v_comp.id_unidad_medida,
            COALESCE(v_comp.rendimiento, v_comp.cantidad, 1.0),
            COALESCE(v_comp.rendimiento, v_comp.cantidad, 1.0),
            v_precio_comp,
            v_subtotal_comp
        );
    END LOOP;

    -- Recalcular el APU copiado
    PERFORM obras.fn_calcular_apu(v_nuevo_id);

    RETURN v_nuevo_id;
END;
$$;

-- 4.3 fn_versionar_apu: Genera una nueva versión v(n+1) del APU
CREATE OR REPLACE FUNCTION obras.fn_versionar_apu(p_id_apu_original INT)
RETURNS INT LANGUAGE plpgsql AS $$
DECLARE
    v_orig RECORD;
    v_nueva_ver INT;
    v_nuevo_codigo VARCHAR(50);
    v_nuevo_id INT;
BEGIN
    SELECT * INTO v_orig FROM obras.t_apu WHERE id_apu = p_id_apu_original;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'El APU ID % no existe.', p_id_apu_original;
    END IF;

    v_nueva_ver := COALESCE(v_orig.version, 1) + 1;
    v_nuevo_codigo := COALESCE(v_orig.codigo_base, v_orig.codigo) || '-v' || v_nueva_ver::TEXT;

    -- 1. Desmarcar original como vigente
    UPDATE obras.t_apu
    SET es_vigente = FALSE,
        updated_at = CURRENT_TIMESTAMP
    WHERE id_apu = p_id_apu_original;

    -- 2. Insertar nueva versión
    INSERT INTO obras.t_apu (
        id_empresa,
        id_obra,
        codigo,
        codigo_base,
        version,
        nombre,
        descripcion,
        id_unidad_medida,
        rendimiento_base,
        id_categoria,
        es_base,
        id_apu_base,
        porcentaje_gastos_generales,
        porcentaje_utilidad,
        porcentaje_impuestos,
        estado,
        es_vigente
    ) VALUES (
        v_orig.id_empresa,
        v_orig.id_obra,
        v_nuevo_codigo,
        COALESCE(v_orig.codigo_base, v_orig.codigo),
        v_nueva_ver,
        v_orig.nombre,
        v_orig.descripcion,
        v_orig.id_unidad_medida,
        v_orig.rendimiento_base,
        v_orig.id_categoria,
        v_orig.es_base,
        v_orig.id_apu_base,
        v_orig.porcentaje_gastos_generales,
        v_orig.porcentaje_utilidad,
        v_orig.porcentaje_impuestos,
        'ACTIVO',
        TRUE
    ) RETURNING id_apu INTO v_nuevo_id;

    -- 3. Clonar componentes
    INSERT INTO obras.t_apu_componente (
        id_apu,
        tipo_recurso,
        id_recurso,
        id_material,
        id_mano_obra,
        id_equipo,
        descripcion_recurso,
        id_unidad_medida,
        cantidad,
        rendimiento,
        precio_unitario,
        subtotal
    )
    SELECT
        v_nuevo_id,
        tipo_recurso,
        id_recurso,
        id_material,
        id_mano_obra,
        id_equipo,
        descripcion_recurso,
        id_unidad_medida,
        cantidad,
        rendimiento,
        precio_unitario,
        subtotal
    FROM obras.t_apu_componente
    WHERE id_apu = p_id_apu_original;

    -- 4. Recalcular
    PERFORM obras.fn_calcular_apu(v_nuevo_id);

    RETURN v_nuevo_id;
END;
$$;

-- 5. SEMILLA: CATÁLOGO BASE DE APUS (OBRATEC)

DO $$
DECLARE
    v_cat_demo INT;
    v_cat_horm INT;
    v_cat_piso INT;
    v_cat_mamp INT;
    v_cat_pint INT;
    v_id_apu INT;
    v_um_m2 INT := 4;
    v_um_m3 INT := 5;
    v_um_ml INT := 8;
    v_um_pza INT := 15;
    v_um_hr INT := 19;
    v_um_kg INT := 2;
    v_um_bolsa INT := 1;
BEGIN
    SELECT id_categoria INTO v_cat_demo FROM obras.t_categoria_apu WHERE nombre = 'DEMOLICIÓN';
    SELECT id_categoria INTO v_cat_horm FROM obras.t_categoria_apu WHERE nombre = 'HORMIGONES';
    SELECT id_categoria INTO v_cat_piso FROM obras.t_categoria_apu WHERE nombre = 'PISOS Y CONTRAPISOS';
    SELECT id_categoria INTO v_cat_mamp FROM obras.t_categoria_apu WHERE nombre = 'MAMPOSTERÍA';
    SELECT id_categoria INTO v_cat_pint FROM obras.t_categoria_apu WHERE nombre = 'PINTURAS';

    -- APU BASE 1: Retiro de puertas y ventanas (Ejemplo del usuario)
    IF NOT EXISTS (SELECT 1 FROM obras.t_apu WHERE codigo = 'APU-BASE-DEM-001') THEN
        INSERT INTO obras.t_apu (
            id_empresa, codigo, codigo_base, version, nombre, descripcion,
            id_unidad_medida, rendimiento_base, id_categoria, es_base,
            porcentaje_gastos_generales, porcentaje_utilidad, porcentaje_impuestos,
            estado, es_vigente
        ) VALUES (
            NULL, 'APU-BASE-DEM-001', 'APU-BASE-DEM-001', 1,
            'Retiro de puertas y ventanas',
            'Desmontaje cuidadoso de carpinterías de puertas y ventanas incluyendo marcos y batientes, acopio en obra.',
            v_um_m2, 1.0, v_cat_demo, TRUE,
            8.00, 15.00, 3.09, 'ACTIVO', TRUE
        ) RETURNING id_apu INTO v_id_apu;

        -- Componentes: Peón 0.20 hr (30 Bs/hr)
        INSERT INTO obras.t_apu_componente (id_apu, tipo_recurso, descripcion_recurso, id_unidad_medida, cantidad, rendimiento, precio_unitario, subtotal)
        VALUES (v_id_apu, 'MANO_OBRA', 'Peón / Ayudante', v_um_hr, 0.20, 0.20, 30.00, 6.00);

        -- Herramientas menores (5% de MO -> 0.05 hr aprox o cuota)
        INSERT INTO obras.t_apu_componente (id_apu, tipo_recurso, descripcion_recurso, id_unidad_medida, cantidad, rendimiento, precio_unitario, subtotal)
        VALUES (v_id_apu, 'EQUIPO', 'Herramientas menores (5% MO)', v_um_hr, 0.05, 0.05, 6.00, 0.30);

        PERFORM obras.fn_calcular_apu(v_id_apu);
    END IF;

    -- APU BASE 2: Demolición muro de ladrillo e=15 cm
    IF NOT EXISTS (SELECT 1 FROM obras.t_apu WHERE codigo = 'APU-BASE-DEM-002') THEN
        INSERT INTO obras.t_apu (
            id_empresa, codigo, codigo_base, version, nombre, descripcion,
            id_unidad_medida, rendimiento_base, id_categoria, es_base,
            porcentaje_gastos_generales, porcentaje_utilidad, porcentaje_impuestos,
            estado, es_vigente
        ) VALUES (
            NULL, 'APU-BASE-DEM-002', 'APU-BASE-DEM-002', 1,
            'Demolición muro de ladrillo e=15 cm',
            'Demolición manual de muro de mampostería de ladrillo adobito o cerámico con espesor de 15 cm sin recuperación.',
            v_um_m2, 1.0, v_cat_demo, TRUE,
            8.00, 15.00, 3.09, 'ACTIVO', TRUE
        ) RETURNING id_apu INTO v_id_apu;

        INSERT INTO obras.t_apu_componente (id_apu, tipo_recurso, descripcion_recurso, id_unidad_medida, cantidad, rendimiento, precio_unitario, subtotal)
        VALUES (v_id_apu, 'MANO_OBRA', 'Peón / Ayudante', v_um_hr, 0.85, 0.85, 30.00, 25.50);

        INSERT INTO obras.t_apu_componente (id_apu, tipo_recurso, descripcion_recurso, id_unidad_medida, cantidad, rendimiento, precio_unitario, subtotal)
        VALUES (v_id_apu, 'EQUIPO', 'Herramientas menores y combo de demolición', v_um_hr, 0.05, 0.05, 25.00, 1.25);

        PERFORM obras.fn_calcular_apu(v_id_apu);
    END IF;

    -- APU BASE 3: Demolición muro de cordón
    IF NOT EXISTS (SELECT 1 FROM obras.t_apu WHERE codigo = 'APU-BASE-DEM-003') THEN
        INSERT INTO obras.t_apu (
            id_empresa, codigo, codigo_base, version, nombre, descripcion,
            id_unidad_medida, rendimiento_base, id_categoria, es_base,
            porcentaje_gastos_generales, porcentaje_utilidad, porcentaje_impuestos,
            estado, es_vigente
        ) VALUES (
            NULL, 'APU-BASE-DEM-003', 'APU-BASE-DEM-003', 1,
            'Demolición muro de cordón',
            'Picado y demolición de cordones de acera de hormigón simple o armado.',
            v_um_ml, 1.0, v_cat_demo, TRUE,
            8.00, 15.00, 3.09, 'ACTIVO', TRUE
        ) RETURNING id_apu INTO v_id_apu;

        INSERT INTO obras.t_apu_componente (id_apu, tipo_recurso, descripcion_recurso, id_unidad_medida, cantidad, rendimiento, precio_unitario, subtotal)
        VALUES (v_id_apu, 'MANO_OBRA', 'Peón / Ayudante', v_um_hr, 0.50, 0.50, 30.00, 15.00);

        INSERT INTO obras.t_apu_componente (id_apu, tipo_recurso, descripcion_recurso, id_unidad_medida, cantidad, rendimiento, precio_unitario, subtotal)
        VALUES (v_id_apu, 'EQUIPO', 'Herramientas menores', v_um_hr, 0.05, 0.05, 15.00, 0.75);

        PERFORM obras.fn_calcular_apu(v_id_apu);
    END IF;

    -- APU BASE 4: Descascarado de revoque
    IF NOT EXISTS (SELECT 1 FROM obras.t_apu WHERE codigo = 'APU-BASE-DEM-004') THEN
        INSERT INTO obras.t_apu (
            id_empresa, codigo, codigo_base, version, nombre, descripcion,
            id_unidad_medida, rendimiento_base, id_categoria, es_base,
            porcentaje_gastos_generales, porcentaje_utilidad, porcentaje_impuestos,
            estado, es_vigente
        ) VALUES (
            NULL, 'APU-BASE-DEM-004', 'APU-BASE-DEM-004', 1,
            'Descascarado de revoque',
            'Retiro y picado superficial de revoque deteriorado de cal o cemento en muros.',
            v_um_m2, 1.0, v_cat_demo, TRUE,
            8.00, 15.00, 3.09, 'ACTIVO', TRUE
        ) RETURNING id_apu INTO v_id_apu;

        INSERT INTO obras.t_apu_componente (id_apu, tipo_recurso, descripcion_recurso, id_unidad_medida, cantidad, rendimiento, precio_unitario, subtotal)
        VALUES (v_id_apu, 'MANO_OBRA', 'Peón / Ayudante', v_um_hr, 0.35, 0.35, 30.00, 10.50);

        INSERT INTO obras.t_apu_componente (id_apu, tipo_recurso, descripcion_recurso, id_unidad_medida, cantidad, rendimiento, precio_unitario, subtotal)
        VALUES (v_id_apu, 'EQUIPO', 'Herramientas menores', v_um_hr, 0.05, 0.05, 10.00, 0.50);

        PERFORM obras.fn_calcular_apu(v_id_apu);
    END IF;

    -- APU BASE 5: Desmontaje de cubierta
    IF NOT EXISTS (SELECT 1 FROM obras.t_apu WHERE codigo = 'APU-BASE-DEM-005') THEN
        INSERT INTO obras.t_apu (
            id_empresa, codigo, codigo_base, version, nombre, descripcion,
            id_unidad_medida, rendimiento_base, id_categoria, es_base,
            porcentaje_gastos_generales, porcentaje_utilidad, porcentaje_impuestos,
            estado, es_vigente
        ) VALUES (
            NULL, 'APU-BASE-DEM-005', 'APU-BASE-DEM-005', 1,
            'Desmontaje de cubierta',
            'Desmontaje cuidadoso de cubiertas de teja o calamina con acopio selectivo.',
            v_um_m2, 1.0, v_cat_demo, TRUE,
            8.00, 15.00, 3.09, 'ACTIVO', TRUE
        ) RETURNING id_apu INTO v_id_apu;

        INSERT INTO obras.t_apu_componente (id_apu, tipo_recurso, descripcion_recurso, id_unidad_medida, cantidad, rendimiento, precio_unitario, subtotal)
        VALUES (v_id_apu, 'MANO_OBRA', 'Cuadrilla 1: Albañil + 2 ayudantes', v_um_hr, 0.30, 0.30, 65.00, 19.50);

        INSERT INTO obras.t_apu_componente (id_apu, tipo_recurso, descripcion_recurso, id_unidad_medida, cantidad, rendimiento, precio_unitario, subtotal)
        VALUES (v_id_apu, 'EQUIPO', 'Andamio Metálico Tubular (Cuerpo)', v_um_hr, 0.20, 0.20, 15.00, 3.00);

        PERFORM obras.fn_calcular_apu(v_id_apu);
    END IF;

    -- APU BASE 6: Remoción de contrapiso
    IF NOT EXISTS (SELECT 1 FROM obras.t_apu WHERE codigo = 'APU-BASE-DEM-006') THEN
        INSERT INTO obras.t_apu (
            id_empresa, codigo, codigo_base, version, nombre, descripcion,
            id_unidad_medida, rendimiento_base, id_categoria, es_base,
            porcentaje_gastos_generales, porcentaje_utilidad, porcentaje_impuestos,
            estado, es_vigente
        ) VALUES (
            NULL, 'APU-BASE-DEM-006', 'APU-BASE-DEM-006', 1,
            'Remoción de contrapiso',
            'Picado y remoción de contrapiso de hormigón pobre o cascote hasta 5 cm de espesor.',
            v_um_m2, 1.0, v_cat_demo, TRUE,
            8.00, 15.00, 3.09, 'ACTIVO', TRUE
        ) RETURNING id_apu INTO v_id_apu;

        INSERT INTO obras.t_apu_componente (id_apu, tipo_recurso, descripcion_recurso, id_unidad_medida, cantidad, rendimiento, precio_unitario, subtotal)
        VALUES (v_id_apu, 'MANO_OBRA', 'Peón / Ayudante', v_um_hr, 0.60, 0.60, 30.00, 18.00);

        INSERT INTO obras.t_apu_componente (id_apu, tipo_recurso, descripcion_recurso, id_unidad_medida, cantidad, rendimiento, precio_unitario, subtotal)
        VALUES (v_id_apu, 'EQUIPO', 'Herramientas menores', v_um_hr, 0.05, 0.05, 10.00, 0.50);

        PERFORM obras.fn_calcular_apu(v_id_apu);
    END IF;

    -- APU BASE 7: Remoción de piso de cemento
    IF NOT EXISTS (SELECT 1 FROM obras.t_apu WHERE codigo = 'APU-BASE-DEM-007') THEN
        INSERT INTO obras.t_apu (
            id_empresa, codigo, codigo_base, version, nombre, descripcion,
            id_unidad_medida, rendimiento_base, id_categoria, es_base,
            porcentaje_gastos_generales, porcentaje_utilidad, porcentaje_impuestos,
            estado, es_vigente
        ) VALUES (
            NULL, 'APU-BASE-DEM-007', 'APU-BASE-DEM-007', 1,
            'Remoción de piso de cemento',
            'Picado y desprendimiento de piso de cemento alisado o frotachado.',
            v_um_m2, 1.0, v_cat_demo, TRUE,
            8.00, 15.00, 3.09, 'ACTIVO', TRUE
        ) RETURNING id_apu INTO v_id_apu;

        INSERT INTO obras.t_apu_componente (id_apu, tipo_recurso, descripcion_recurso, id_unidad_medida, cantidad, rendimiento, precio_unitario, subtotal)
        VALUES (v_id_apu, 'MANO_OBRA', 'Peón / Ayudante', v_um_hr, 0.70, 0.70, 30.00, 21.00);

        INSERT INTO obras.t_apu_componente (id_apu, tipo_recurso, descripcion_recurso, id_unidad_medida, cantidad, rendimiento, precio_unitario, subtotal)
        VALUES (v_id_apu, 'EQUIPO', 'Herramientas menores', v_um_hr, 0.05, 0.05, 10.00, 0.50);

        PERFORM obras.fn_calcular_apu(v_id_apu);
    END IF;

    -- APU BASE 8: Retiro de verja metálica
    IF NOT EXISTS (SELECT 1 FROM obras.t_apu WHERE codigo = 'APU-BASE-DEM-008') THEN
        INSERT INTO obras.t_apu (
            id_empresa, codigo, codigo_base, version, nombre, descripcion,
            id_unidad_medida, rendimiento_base, id_categoria, es_base,
            porcentaje_gastos_generales, porcentaje_utilidad, porcentaje_impuestos,
            estado, es_vigente
        ) VALUES (
            NULL, 'APU-BASE-DEM-008', 'APU-BASE-DEM-008', 1,
            'Retiro de verja metálica',
            'Desanclaje y retiro de verjas y portones de reja metálica.',
            v_um_m2, 1.0, v_cat_demo, TRUE,
            8.00, 15.00, 3.09, 'ACTIVO', TRUE
        ) RETURNING id_apu INTO v_id_apu;

        INSERT INTO obras.t_apu_componente (id_apu, tipo_recurso, descripcion_recurso, id_unidad_medida, cantidad, rendimiento, precio_unitario, subtotal)
        VALUES (v_id_apu, 'MANO_OBRA', 'Peón / Ayudante', v_um_hr, 0.45, 0.45, 30.00, 13.50);

        INSERT INTO obras.t_apu_componente (id_apu, tipo_recurso, descripcion_recurso, id_unidad_medida, cantidad, rendimiento, precio_unitario, subtotal)
        VALUES (v_id_apu, 'EQUIPO', 'Cortadora Eléctrica de Disco', v_um_hr, 0.15, 0.15, 20.00, 3.00);

        PERFORM obras.fn_calcular_apu(v_id_apu);
    END IF;

    -- APU BASE 9: Hormigón armado columnas (Categoría HORMIGONES)
    IF NOT EXISTS (SELECT 1 FROM obras.t_apu WHERE codigo = 'APU-BASE-HOR-001') THEN
        INSERT INTO obras.t_apu (
            id_empresa, codigo, codigo_base, version, nombre, descripcion,
            id_unidad_medida, rendimiento_base, id_categoria, es_base,
            porcentaje_gastos_generales, porcentaje_utilidad, porcentaje_impuestos,
            estado, es_vigente
        ) VALUES (
            NULL, 'APU-BASE-HOR-001', 'APU-BASE-HOR-001', 1,
            'Hormigón armado para columnas H-21',
            'Elaboración, vaciado y vibrado de hormigón estructural H-21 para columnas, incluye materiales y encofrado.',
            v_um_m3, 1.0, v_cat_horm, TRUE,
            10.00, 15.00, 3.09, 'ACTIVO', TRUE
        ) RETURNING id_apu INTO v_id_apu;

        -- Materiales
        INSERT INTO obras.t_apu_componente (id_apu, tipo_recurso, descripcion_recurso, id_unidad_medida, cantidad, rendimiento, precio_unitario, subtotal)
        VALUES (v_id_apu, 'MATERIAL', 'Cemento Portland IP-30', v_um_bolsa, 7.50, 7.50, 52.00, 390.00);

        INSERT INTO obras.t_apu_componente (id_apu, tipo_recurso, descripcion_recurso, id_unidad_medida, cantidad, rendimiento, precio_unitario, subtotal)
        VALUES (v_id_apu, 'MATERIAL', 'Arena gruesa lavada', v_um_m3, 0.45, 0.45, 95.00, 42.75);

        INSERT INTO obras.t_apu_componente (id_apu, tipo_recurso, descripcion_recurso, id_unidad_medida, cantidad, rendimiento, precio_unitario, subtotal)
        VALUES (v_id_apu, 'MATERIAL', 'Grava común rodada', v_um_m3, 0.85, 0.85, 120.00, 102.00);

        -- Mano de obra
        INSERT INTO obras.t_apu_componente (id_apu, tipo_recurso, descripcion_recurso, id_unidad_medida, cantidad, rendimiento, precio_unitario, subtotal)
        VALUES (v_id_apu, 'MANO_OBRA', 'Cuadrilla 2: Albañil + 3 ayudantes', v_um_hr, 8.00, 8.00, 85.00, 680.00);

        -- Equipos
        INSERT INTO obras.t_apu_componente (id_apu, tipo_recurso, descripcion_recurso, id_unidad_medida, cantidad, rendimiento, precio_unitario, subtotal)
        VALUES (v_id_apu, 'EQUIPO', 'Mezcladora de Hormigón 350L', v_um_hr, 2.50, 2.50, 35.00, 87.50);

        INSERT INTO obras.t_apu_componente (id_apu, tipo_recurso, descripcion_recurso, id_unidad_medida, cantidad, rendimiento, precio_unitario, subtotal)
        VALUES (v_id_apu, 'EQUIPO', 'Vibradora de Inmersión 4HP', v_um_hr, 2.00, 2.00, 25.00, 50.00);

        PERFORM obras.fn_calcular_apu(v_id_apu);
    END IF;

    -- APU BASE 10: Colocación de cerámica esmaltada (Categoría PISOS Y CONTRAPISOS)
    IF NOT EXISTS (SELECT 1 FROM obras.t_apu WHERE codigo = 'APU-BASE-PIS-001') THEN
        INSERT INTO obras.t_apu (
            id_empresa, codigo, codigo_base, version, nombre, descripcion,
            id_unidad_medida, rendimiento_base, id_categoria, es_base,
            porcentaje_gastos_generales, porcentaje_utilidad, porcentaje_impuestos,
            estado, es_vigente
        ) VALUES (
            NULL, 'APU-BASE-PIS-001', 'APU-BASE-PIS-001', 1,
            'Colocación de piso cerámico esmaltado',
            'Provisión y colocación de piso cerámico esmaltado de alto tránsito con pegamento y empastinado.',
            v_um_m2, 1.0, v_cat_piso, TRUE,
            8.00, 15.00, 3.09, 'ACTIVO', TRUE
        ) RETURNING id_apu INTO v_id_apu;

        -- Materiales
        INSERT INTO obras.t_apu_componente (id_apu, tipo_recurso, descripcion_recurso, id_unidad_medida, cantidad, rendimiento, precio_unitario, subtotal)
        VALUES (v_id_apu, 'MATERIAL', 'Adhesivo cementicio para cerámica 20 kg', v_um_bolsa, 0.25, 0.25, 28.00, 7.00);

        -- Mano de obra
        INSERT INTO obras.t_apu_componente (id_apu, tipo_recurso, descripcion_recurso, id_unidad_medida, cantidad, rendimiento, precio_unitario, subtotal)
        VALUES (v_id_apu, 'MANO_OBRA', 'Cuadrilla 3: Albañil + 1 ayudante', v_um_hr, 0.60, 0.60, 75.00, 45.00);

        -- Equipos
        INSERT INTO obras.t_apu_componente (id_apu, tipo_recurso, descripcion_recurso, id_unidad_medida, cantidad, rendimiento, precio_unitario, subtotal)
        VALUES (v_id_apu, 'EQUIPO', 'Cortadora Eléctrica de Disco', v_um_hr, 0.15, 0.15, 20.00, 3.00);

        PERFORM obras.fn_calcular_apu(v_id_apu);
    END IF;

    -- APU BASE 11: Contrapiso de cascote e=5cm (Categoría PISOS Y CONTRAPISOS)
    IF NOT EXISTS (SELECT 1 FROM obras.t_apu WHERE codigo = 'APU-BASE-PIS-002') THEN
        INSERT INTO obras.t_apu (
            id_empresa, codigo, codigo_base, version, nombre, descripcion,
            id_unidad_medida, rendimiento_base, id_categoria, es_base,
            porcentaje_gastos_generales, porcentaje_utilidad, porcentaje_impuestos,
            estado, es_vigente
        ) VALUES (
            NULL, 'APU-BASE-PIS-002', 'APU-BASE-PIS-002', 1,
            'Contrapiso de cascote e=5cm',
            'Ejecución de contrapiso de hormigón pobre con cascote de ladrillo de 5 cm de espesor sobre tierra compactada.',
            v_um_m2, 1.0, v_cat_piso, TRUE,
            8.00, 15.00, 3.09, 'ACTIVO', TRUE
        ) RETURNING id_apu INTO v_id_apu;

        INSERT INTO obras.t_apu_componente (id_apu, tipo_recurso, descripcion_recurso, id_unidad_medida, cantidad, rendimiento, precio_unitario, subtotal)
        VALUES (v_id_apu, 'MATERIAL', 'Cemento Portland IP-30', v_um_bolsa, 0.22, 0.22, 52.00, 11.44);

        INSERT INTO obras.t_apu_componente (id_apu, tipo_recurso, descripcion_recurso, id_unidad_medida, cantidad, rendimiento, precio_unitario, subtotal)
        VALUES (v_id_apu, 'MATERIAL', 'Arena fina lavada', v_um_m3, 0.03, 0.03, 110.00, 3.30);

        INSERT INTO obras.t_apu_componente (id_apu, tipo_recurso, descripcion_recurso, id_unidad_medida, cantidad, rendimiento, precio_unitario, subtotal)
        VALUES (v_id_apu, 'MANO_OBRA', 'Cuadrilla 4: Peón / ayudante', v_um_hr, 0.50, 0.50, 30.00, 15.00);

        INSERT INTO obras.t_apu_componente (id_apu, tipo_recurso, descripcion_recurso, id_unidad_medida, cantidad, rendimiento, precio_unitario, subtotal)
        VALUES (v_id_apu, 'EQUIPO', 'Mezcladora de Hormigón 350L', v_um_hr, 0.10, 0.10, 35.00, 3.50);

        PERFORM obras.fn_calcular_apu(v_id_apu);
    END IF;

END;
$$;

COMMIT;
