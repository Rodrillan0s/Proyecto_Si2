-- ============================================================================
-- MIGRACIÓN CU14: Gestión de materiales
-- Ejecutar manualmente. Es atómica, preserva datos y no elimina columnas.
-- ============================================================================
BEGIN;

CREATE TABLE IF NOT EXISTS obras.t_categoria_material (
    id_categoria SERIAL PRIMARY KEY,
    nombre VARCHAR(120) NOT NULL,
    descripcion TEXT,
    estado VARCHAR(10) NOT NULL DEFAULT 'ACTIVO',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_categoria_material_estado CHECK (estado IN ('ACTIVO', 'INACTIVO')),
    CONSTRAINT chk_categoria_material_nombre CHECK (BTRIM(nombre) <> '')
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_categoria_material_nombre_activo
    ON obras.t_categoria_material (LOWER(BTRIM(nombre))) WHERE estado = 'ACTIVO';

CREATE TABLE IF NOT EXISTS obras.t_unidad_medida (
    id_unidad_medida SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    abreviatura VARCHAR(20) NOT NULL,
    estado VARCHAR(10) NOT NULL DEFAULT 'ACTIVO',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_unidad_medida_estado CHECK (estado IN ('ACTIVO', 'INACTIVO')),
    CONSTRAINT chk_unidad_medida_nombre CHECK (BTRIM(nombre) <> ''),
    CONSTRAINT chk_unidad_medida_abreviatura CHECK (BTRIM(abreviatura) <> '')
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_unidad_medida_nombre_activo
    ON obras.t_unidad_medida (LOWER(BTRIM(nombre))) WHERE estado = 'ACTIVO';
CREATE UNIQUE INDEX IF NOT EXISTS uq_unidad_medida_abreviatura_activo
    ON obras.t_unidad_medida (LOWER(BTRIM(abreviatura))) WHERE estado = 'ACTIVO';

INSERT INTO obras.t_categoria_material(nombre, descripcion)
SELECT 'Sin categoría', 'Categoría temporal para materiales existentes.'
WHERE NOT EXISTS (SELECT 1 FROM obras.t_categoria_material WHERE LOWER(nombre) = 'sin categoría');

INSERT INTO obras.t_unidad_medida(nombre, abreviatura) VALUES
    ('Bolsa', 'bolsa'), ('Kilogramo', 'kg'), ('Metro', 'm'),
    ('Metro cuadrado', 'm2'), ('Metro cúbico', 'm3'), ('Unidad', 'u'), ('Barra', 'barra')
ON CONFLICT DO NOTHING;

ALTER TABLE obras.t_material
    ADD COLUMN IF NOT EXISTS codigo VARCHAR(50),
    ADD COLUMN IF NOT EXISTS descripcion TEXT,
    ADD COLUMN IF NOT EXISTS id_categoria INTEGER,
    ADD COLUMN IF NOT EXISTS id_unidad_medida INTEGER,
    ADD COLUMN IF NOT EXISTS estado VARCHAR(10) NOT NULL DEFAULT 'ACTIVO',
    ADD COLUMN IF NOT EXISTS id_empresa INTEGER,
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP;

-- CU14 no obliga proveedor; se conserva la columna para compatibilidad con CU15.
ALTER TABLE obras.t_material ALTER COLUMN id_proveedor DROP NOT NULL;

UPDATE obras.t_material
SET codigo = 'LEGACY-' || id_material
WHERE codigo IS NULL OR BTRIM(codigo) = '';

UPDATE obras.t_material
SET id_categoria = (SELECT id_categoria FROM obras.t_categoria_material
                    WHERE LOWER(nombre) = 'sin categoría' ORDER BY id_categoria LIMIT 1)
WHERE id_categoria IS NULL;

UPDATE obras.t_material
SET id_unidad_medida = (SELECT id_unidad_medida FROM obras.t_unidad_medida
                       WHERE LOWER(nombre) = 'unidad' ORDER BY id_unidad_medida LIMIT 1)
WHERE id_unidad_medida IS NULL;

-- No se adivina la empresa cuando hay más de una: el bloque aborta toda la
-- migración y obliga a preparar un mapeo explícito para los registros heredados.
DO $$
DECLARE v_empresas INTEGER; v_empresa INTEGER;
BEGIN
    IF EXISTS (SELECT 1 FROM obras.t_material WHERE id_empresa IS NULL) THEN
        SELECT COUNT(*), MIN(id_empresa) INTO v_empresas, v_empresa FROM obras.t_empresa;
        IF v_empresas = 1 THEN
            UPDATE obras.t_material SET id_empresa = v_empresa WHERE id_empresa IS NULL;
        ELSE
            RAISE EXCEPTION 'CU14: existen materiales sin empresa y % empresas. Asigne id_empresa explícitamente antes de migrar.', v_empresas;
        END IF;
    END IF;
END $$;

ALTER TABLE obras.t_material
    ALTER COLUMN codigo SET NOT NULL,
    ALTER COLUMN id_categoria SET NOT NULL,
    ALTER COLUMN id_unidad_medida SET NOT NULL,
    ALTER COLUMN id_empresa SET NOT NULL;

DO $$ BEGIN
    ALTER TABLE obras.t_material ADD CONSTRAINT fk_material_categoria
        FOREIGN KEY (id_categoria) REFERENCES obras.t_categoria_material(id_categoria) ON DELETE RESTRICT;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
    ALTER TABLE obras.t_material ADD CONSTRAINT fk_material_unidad_medida
        FOREIGN KEY (id_unidad_medida) REFERENCES obras.t_unidad_medida(id_unidad_medida) ON DELETE RESTRICT;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
    ALTER TABLE obras.t_material ADD CONSTRAINT fk_material_empresa
        FOREIGN KEY (id_empresa) REFERENCES obras.t_empresa(id_empresa) ON DELETE RESTRICT;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
    ALTER TABLE obras.t_material ADD CONSTRAINT chk_material_estado
        CHECK (estado IN ('ACTIVO', 'INACTIVO'));
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
    ALTER TABLE obras.t_material ADD CONSTRAINT chk_material_precio
        CHECK (precio IS NULL OR precio >= 0);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

CREATE UNIQUE INDEX IF NOT EXISTS uq_material_empresa_codigo
    ON obras.t_material(id_empresa, LOWER(BTRIM(codigo)));
CREATE INDEX IF NOT EXISTS idx_material_empresa_estado ON obras.t_material(id_empresa, estado);
CREATE INDEX IF NOT EXISTS idx_material_categoria ON obras.t_material(id_categoria);

ALTER TABLE obras.t_materiales_almacen
    ADD COLUMN IF NOT EXISTS stock_minimo NUMERIC(14,3) NOT NULL DEFAULT 0;
DO $$ BEGIN
    ALTER TABLE obras.t_materiales_almacen ADD CONSTRAINT chk_almacen_cantidad_inicial
        CHECK (cantidad_inicial >= 0);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
    ALTER TABLE obras.t_materiales_almacen ADD CONSTRAINT chk_almacen_cantidad_actual
        CHECK (cantidad_actual >= 0);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
    ALTER TABLE obras.t_materiales_almacen ADD CONSTRAINT chk_almacen_stock_minimo
        CHECK (stock_minimo >= 0);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
CREATE INDEX IF NOT EXISTS idx_materiales_almacen_material ON obras.t_materiales_almacen(id_material);

CREATE TABLE IF NOT EXISTS obras.t_material_caracteristica (
    id_caracteristica SERIAL PRIMARY KEY,
    id_material INTEGER NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    valor VARCHAR(250) NOT NULL,
    CONSTRAINT fk_material_caracteristica_material FOREIGN KEY (id_material)
        REFERENCES obras.t_material(id_material) ON DELETE CASCADE,
    CONSTRAINT chk_material_caracteristica_nombre CHECK (BTRIM(nombre) <> ''),
    CONSTRAINT chk_material_caracteristica_valor CHECK (BTRIM(valor) <> '')
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_material_caracteristica_nombre
    ON obras.t_material_caracteristica(id_material, LOWER(BTRIM(nombre)));

CREATE OR REPLACE FUNCTION obras.fn_actualizar_updated_at_cu14() RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = CURRENT_TIMESTAMP; RETURN NEW; END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tg_cu14_actualizar_material ON obras.t_material;
CREATE TRIGGER tg_cu14_actualizar_material BEFORE UPDATE ON obras.t_material
FOR EACH ROW EXECUTE FUNCTION obras.fn_actualizar_updated_at_cu14();
DROP TRIGGER IF EXISTS tg_cu14_actualizar_categoria_material ON obras.t_categoria_material;
CREATE TRIGGER tg_cu14_actualizar_categoria_material BEFORE UPDATE ON obras.t_categoria_material
FOR EACH ROW EXECUTE FUNCTION obras.fn_actualizar_updated_at_cu14();
DROP TRIGGER IF EXISTS tg_cu14_actualizar_unidad_medida ON obras.t_unidad_medida;
CREATE TRIGGER tg_cu14_actualizar_unidad_medida BEFORE UPDATE ON obras.t_unidad_medida
FOR EACH ROW EXECUTE FUNCTION obras.fn_actualizar_updated_at_cu14();

INSERT INTO obras.t_permiso(nombre_permiso)
SELECT p.nombre FROM (VALUES
    ('Visualizar_materiales'), ('Registrar_materiales'),
    ('Modificar_materiales'), ('Desactivar_materiales')
) AS p(nombre)
WHERE NOT EXISTS (SELECT 1 FROM obras.t_permiso x WHERE x.nombre_permiso = p.nombre);

INSERT INTO obras.t_rol_permiso(id_rol, id_permiso)
SELECT r.id_rol, p.id_permiso
FROM obras.t_rol r CROSS JOIN obras.t_permiso p
WHERE UPPER(r.nombre_rol) = 'ADMINISTRADOR_EMPRESA'
  AND p.nombre_permiso IN ('Visualizar_materiales','Registrar_materiales','Modificar_materiales','Desactivar_materiales')
ON CONFLICT DO NOTHING;

COMMIT;
