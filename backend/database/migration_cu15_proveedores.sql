-- ============================================================================
-- MIGRACIÓN CU15: Gestión de proveedores
-- Ejecutar manualmente sobre la base de datos. Atómica y segura para re-ejecución.
-- ============================================================================
BEGIN;

-- ─────────────────────────────────────────────────────────────────────────────
-- 1. TABLA PRINCIPAL: t_proveedor
-- ─────────────────────────────────────────────────────────────────────────────
DROP TABLE IF EXISTS obras.t_proveedor CASCADE;
CREATE TABLE obras.t_proveedor (
    id_proveedor  SERIAL PRIMARY KEY,
    nombre        VARCHAR(200) NOT NULL,
    nit           VARCHAR(50)  NOT NULL,
    telefono      VARCHAR(30),
    email         VARCHAR(150),
    direccion     TEXT,
    contacto      VARCHAR(150),
    estado        VARCHAR(10)  NOT NULL DEFAULT 'ACTIVO',
    id_empresa    INTEGER      NOT NULL,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_proveedor_estado   CHECK (estado IN ('ACTIVO', 'INACTIVO')),
    CONSTRAINT chk_proveedor_nombre   CHECK (BTRIM(nombre) <> ''),
    CONSTRAINT chk_proveedor_nit      CHECK (BTRIM(nit)    <> ''),
    CONSTRAINT fk_proveedor_empresa   FOREIGN KEY (id_empresa)
        REFERENCES obras.t_empresa(id_empresa) ON DELETE RESTRICT
);

-- NIT único por empresa
CREATE UNIQUE INDEX IF NOT EXISTS uq_proveedor_empresa_nit
    ON obras.t_proveedor (id_empresa, LOWER(BTRIM(nit)));

-- Índice por empresa + estado para listados
CREATE INDEX IF NOT EXISTS idx_proveedor_empresa_estado
    ON obras.t_proveedor (id_empresa, estado);

-- ─────────────────────────────────────────────────────────────────────────────
-- 2. TABLA INTERMEDIA MUCHOS A MUCHOS: t_proveedor_material
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS obras.t_proveedor_material (
    id_proveedor_material SERIAL PRIMARY KEY,
    id_proveedor          INTEGER      NOT NULL,
    id_material           INTEGER      NOT NULL,
    created_at            TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_pm_proveedor FOREIGN KEY (id_proveedor)
        REFERENCES obras.t_proveedor(id_proveedor) ON DELETE CASCADE,
    CONSTRAINT fk_pm_material  FOREIGN KEY (id_material)
        REFERENCES obras.t_material(id_material)   ON DELETE CASCADE,
    CONSTRAINT uq_proveedor_material
        UNIQUE (id_proveedor, id_material)
);

CREATE INDEX IF NOT EXISTS idx_pm_proveedor ON obras.t_proveedor_material (id_proveedor);
CREATE INDEX IF NOT EXISTS idx_pm_material  ON obras.t_proveedor_material (id_material);

-- ─────────────────────────────────────────────────────────────────────────────
-- 3. TRIGGER updated_at para t_proveedor
-- ─────────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION obras.fn_actualizar_updated_at_cu15()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tg_cu15_actualizar_proveedor ON obras.t_proveedor;
CREATE TRIGGER tg_cu15_actualizar_proveedor
    BEFORE UPDATE ON obras.t_proveedor
    FOR EACH ROW EXECUTE FUNCTION obras.fn_actualizar_updated_at_cu15();

-- ─────────────────────────────────────────────────────────────────────────────
-- 4. PERMISOS CU15
-- ─────────────────────────────────────────────────────────────────────────────
INSERT INTO obras.t_permiso (nombre_permiso)
SELECT p.nombre FROM (VALUES
    ('Visualizar_proveedores'),
    ('Registrar_proveedores'),
    ('Modificar_proveedores')
) AS p(nombre)
WHERE NOT EXISTS (
    SELECT 1 FROM obras.t_permiso x WHERE x.nombre_permiso = p.nombre
);

-- Asignar los tres permisos al rol ADMINISTRADOR_EMPRESA
INSERT INTO obras.t_rol_permiso (id_rol, id_permiso)
SELECT r.id_rol, p.id_permiso
FROM obras.t_rol r
CROSS JOIN obras.t_permiso p
WHERE UPPER(r.nombre_rol) = 'ADMINISTRADOR_EMPRESA'
  AND p.nombre_permiso IN (
      'Visualizar_proveedores',
      'Registrar_proveedores',
      'Modificar_proveedores'
  )
ON CONFLICT DO NOTHING;

-- Asignar visualización al JEFE DE OBRA si existe ese rol
INSERT INTO obras.t_rol_permiso (id_rol, id_permiso)
SELECT r.id_rol, p.id_permiso
FROM obras.t_rol r
CROSS JOIN obras.t_permiso p
WHERE UPPER(r.nombre_rol) = 'JEFE DE OBRA'
  AND p.nombre_permiso = 'Visualizar_proveedores'
ON CONFLICT DO NOTHING;

COMMIT;
