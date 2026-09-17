-- =============================================================================
-- MIGRACIÓN CU14: POBLAR CATÁLOGO BASE EN TODAS LAS CONSTRUCTORAS
-- =============================================================================
-- 1. Inserta los 56 materiales base de Bolivia en el catálogo corporativo
--    (obras.t_material) de todas las empresas existentes.
-- 2. Crea las entradas iniciales de almacén (obras.t_materiales_almacen) con
--    stock 0 para permitir su uso inmediato en presupuestos y APUs.
-- 3. Crea una función y trigger para que cualquier NUEVA empresa que se registre
--    en el futuro herede automáticamente los materiales del catálogo base.
-- =============================================================================

BEGIN;

SET search_path TO obras, public;

-- -----------------------------------------------------------------------------
-- 1. POBLAR MATERIALES BASE A TODAS LAS EMPRESAS EXISTENTES
-- -----------------------------------------------------------------------------
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
    e.id_empresa,
    mb.id_material_base,
    mb.codigo,
    mb.nombre_material,
    mb.descripcion,
    mb.id_categoria,
    mb.id_unidad_medida,
    COALESCE(mb.precio_referencial, 0.00),
    'ACTIVO',
    FALSE,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
FROM obras.t_empresa e
CROSS JOIN obras.t_material_base mb
WHERE mb.estado = 'ACTIVO'
  AND NOT EXISTS (
      SELECT 1 FROM obras.t_material m 
      WHERE m.id_empresa = e.id_empresa 
        AND (m.id_material_base = mb.id_material_base OR LOWER(BTRIM(m.codigo)) = LOWER(BTRIM(mb.codigo)))
  );

-- -----------------------------------------------------------------------------
-- 2. CREAR REGISTRO INICIAL EN ALMACÉN PARA MATERIALES SIN LOTE
-- -----------------------------------------------------------------------------
INSERT INTO obras.t_materiales_almacen (
    id_material,
    cantidad_inicial,
    cantidad_actual,
    precio_venta,
    fecha_ingreso,
    stock_minimo
)
SELECT
    m.id_material,
    0,
    0,
    m.precio,
    CURRENT_DATE,
    0.00
FROM obras.t_material m
WHERE NOT EXISTS (
    SELECT 1 FROM obras.t_materiales_almacen a WHERE a.id_material = m.id_material
);

-- -----------------------------------------------------------------------------
-- 3. TRIGGER AUTOMÁTICO PARA FUTURAS EMPRESAS
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION obras.fn_trg_poblar_catalogo_empresa()
RETURNS TRIGGER AS $$
BEGIN
    -- Insertar materiales base activos en la nueva empresa
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
        NEW.id_empresa,
        mb.id_material_base,
        mb.codigo,
        mb.nombre_material,
        mb.descripcion,
        mb.id_categoria,
        mb.id_unidad_medida,
        COALESCE(mb.precio_referencial, 0.00),
        'ACTIVO',
        FALSE,
        CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP
    FROM obras.t_material_base mb
    WHERE mb.estado = 'ACTIVO'
      AND NOT EXISTS (
          SELECT 1 FROM obras.t_material m 
          WHERE m.id_empresa = NEW.id_empresa 
            AND (m.id_material_base = mb.id_material_base OR LOWER(BTRIM(m.codigo)) = LOWER(BTRIM(mb.codigo)))
      );

    -- Generar lote inicial de almacén con stock 0
    INSERT INTO obras.t_materiales_almacen (
        id_material,
        cantidad_inicial,
        cantidad_actual,
        precio_venta,
        fecha_ingreso,
        stock_minimo
    )
    SELECT
        m.id_material,
        0,
        0,
        m.precio,
        CURRENT_DATE,
        0.00
    FROM obras.t_material m
    WHERE m.id_empresa = NEW.id_empresa
      AND NOT EXISTS (
          SELECT 1 FROM obras.t_materiales_almacen a WHERE a.id_material = m.id_material
      );

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_poblar_catalogo_nueva_empresa ON obras.t_empresa;
CREATE TRIGGER trg_poblar_catalogo_nueva_empresa
AFTER INSERT ON obras.t_empresa
FOR EACH ROW
EXECUTE FUNCTION obras.fn_trg_poblar_catalogo_empresa();

COMMIT;
