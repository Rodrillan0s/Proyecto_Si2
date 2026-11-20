-- ============================================================================
-- OBRATEC - Estimaciones de costos con APU
-- Atómica, repetible y aislada de costos reales/almacén.
-- ============================================================================
BEGIN;

ALTER TABLE obras.t_obra
    ADD COLUMN IF NOT EXISTS presupuesto_objetivo NUMERIC(14,2),
    ADD COLUMN IF NOT EXISTS estado_estimacion VARCHAR(20) NOT NULL DEFAULT 'SIN_ESTIMAR';

DO $$ BEGIN
    ALTER TABLE obras.t_obra ADD CONSTRAINT chk_obra_estado_estimacion
        CHECK (estado_estimacion IN ('SIN_ESTIMAR','EN_ESTIMACION','ESTIMADA','APROBADA'));
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

ALTER TABLE obras.t_unidad_construccion
    ADD COLUMN IF NOT EXISTS especificacion_acabado VARCHAR(20) NOT NULL DEFAULT 'NORMAL';
DO $$ BEGIN
    ALTER TABLE obras.t_unidad_construccion ADD CONSTRAINT chk_unidad_especificacion_acabado
        CHECK (especificacion_acabado IN ('NORMAL','LUJO'));
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

ALTER TABLE obras.t_unidad_medida
    ADD COLUMN IF NOT EXISTS tipo VARCHAR(20) NOT NULL DEFAULT 'INSUMO';
DO $$ BEGIN
    ALTER TABLE obras.t_unidad_medida ADD CONSTRAINT chk_unidad_medida_tipo_apu
        CHECK (tipo IN ('GEOMETRICA','INSUMO','CONCEPTUAL'));
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

INSERT INTO obras.t_unidad_medida(nombre, abreviatura, tipo) VALUES
    ('Metro lineal', 'ml', 'GEOMETRICA'),
    ('Pie tablar', 'pt', 'INSUMO'),
    ('Tonelada', 'ton', 'INSUMO'),
    ('Jornal', 'jornal', 'CONCEPTUAL'),
    ('Punto eléctrico', 'punto', 'CONCEPTUAL'),
    ('Salida hidrosanitaria', 'salida', 'CONCEPTUAL'),
    ('Lote global', 'lote', 'CONCEPTUAL')
ON CONFLICT DO NOTHING;

CREATE TABLE IF NOT EXISTS obras.t_mano_obra (
    id_mano_obra SERIAL PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    descripcion TEXT,
    id_unidad_medida INTEGER NOT NULL,
    costo_unitario NUMERIC(14,2) NOT NULL CHECK (costo_unitario >= 0),
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    id_empresa INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_mano_obra_unidad FOREIGN KEY (id_unidad_medida)
        REFERENCES obras.t_unidad_medida(id_unidad_medida) ON DELETE RESTRICT,
    CONSTRAINT fk_mano_obra_empresa FOREIGN KEY (id_empresa)
        REFERENCES obras.t_empresa(id_empresa) ON DELETE RESTRICT
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_mano_obra_empresa_nombre_activo
    ON obras.t_mano_obra(id_empresa, LOWER(BTRIM(nombre))) WHERE activo;

CREATE TABLE IF NOT EXISTS obras.t_analisis_precio_unitario (
    id_analisis_precio_unitario SERIAL PRIMARY KEY,
    id_obra INTEGER NULL,
    id_padre INTEGER NULL,
    id_estructura INTEGER NULL,
    nombre VARCHAR(200) NOT NULL,
    descripcion TEXT,
    id_unidad_medida INTEGER NOT NULL,
    tipo_analisis_precio_unitario VARCHAR(20) NOT NULL DEFAULT 'OBRA_GRIS',
    calidad VARCHAR(20) NULL,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    id_empresa INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_apu_obra FOREIGN KEY (id_obra) REFERENCES obras.t_obra(id_obra) ON DELETE CASCADE,
    CONSTRAINT fk_apu_padre FOREIGN KEY (id_padre)
        REFERENCES obras.t_analisis_precio_unitario(id_analisis_precio_unitario) ON DELETE CASCADE,
    CONSTRAINT fk_apu_estructura FOREIGN KEY (id_estructura)
        REFERENCES obras.t_estructura_obra(id_estructura) ON DELETE SET NULL,
    CONSTRAINT fk_apu_unidad FOREIGN KEY (id_unidad_medida)
        REFERENCES obras.t_unidad_medida(id_unidad_medida) ON DELETE RESTRICT,
    CONSTRAINT fk_apu_empresa FOREIGN KEY (id_empresa)
        REFERENCES obras.t_empresa(id_empresa) ON DELETE RESTRICT,
    CONSTRAINT chk_apu_tipo CHECK (tipo_analisis_precio_unitario IN ('OBRA_GRIS','EXCAVACION','ACABADO','SUBCONTRATO')),
    CONSTRAINT chk_apu_calidad CHECK (calidad IS NULL OR calidad IN ('NORMAL','LUJO'))
);
CREATE INDEX IF NOT EXISTS idx_apu_obra ON obras.t_analisis_precio_unitario(id_obra);
CREATE INDEX IF NOT EXISTS idx_apu_empresa_activo ON obras.t_analisis_precio_unitario(id_empresa, activo);
CREATE INDEX IF NOT EXISTS idx_apu_estructura ON obras.t_analisis_precio_unitario(id_estructura);

CREATE TABLE IF NOT EXISTS obras.t_analisi_precio_unitario_insumo (
    id_analisis_precio_unitario_insumo SERIAL PRIMARY KEY,
    id_analisis_precio_unitario INTEGER NOT NULL,
    tipo_insumo VARCHAR(20) NOT NULL,
    id_material INTEGER NULL,
    id_mano_obra INTEGER NULL,
    nombre VARCHAR(200) NOT NULL,
    id_unidad_medida INTEGER NOT NULL,
    cantidad NUMERIC(12,4) NOT NULL CHECK (cantidad >= 0),
    precio_unitario NUMERIC(14,2) NOT NULL CHECK (precio_unitario >= 0),
    orden INTEGER NOT NULL DEFAULT 1,
    id_empresa INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_apu_insumo_apu FOREIGN KEY (id_analisis_precio_unitario)
        REFERENCES obras.t_analisis_precio_unitario(id_analisis_precio_unitario) ON DELETE CASCADE,
    CONSTRAINT fk_apu_insumo_material FOREIGN KEY (id_material)
        REFERENCES obras.t_material(id_material) ON DELETE SET NULL,
    CONSTRAINT fk_apu_insumo_mano_obra FOREIGN KEY (id_mano_obra)
        REFERENCES obras.t_mano_obra(id_mano_obra) ON DELETE SET NULL,
    CONSTRAINT fk_apu_insumo_unidad FOREIGN KEY (id_unidad_medida)
        REFERENCES obras.t_unidad_medida(id_unidad_medida) ON DELETE RESTRICT,
    CONSTRAINT fk_apu_insumo_empresa FOREIGN KEY (id_empresa)
        REFERENCES obras.t_empresa(id_empresa) ON DELETE RESTRICT,
    CONSTRAINT chk_apu_insumo_tipo CHECK (tipo_insumo IN ('MATERIAL','MANO_OBRA','OTRO')),
    CONSTRAINT chk_apu_insumo_material_tipo CHECK (tipo_insumo <> 'MATERIAL' OR id_mano_obra IS NULL),
    CONSTRAINT chk_apu_insumo_mano_tipo CHECK (tipo_insumo <> 'MANO_OBRA' OR id_material IS NULL)
);
CREATE INDEX IF NOT EXISTS idx_apu_insumo_apu
    ON obras.t_analisi_precio_unitario_insumo(id_analisis_precio_unitario);

CREATE TABLE IF NOT EXISTS obras.t_estimacion (
    id_estimacion SERIAL PRIMARY KEY,
    id_obra INTEGER NOT NULL,
    nombre VARCHAR(150) NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    estado VARCHAR(20) NOT NULL DEFAULT 'BORRADOR',
    descripcion TEXT,
    factor_indirectos NUMERIC(8,4),
    factor_utilidad NUMERIC(8,4),
    monto_total NUMERIC(16,2),
    id_empresa INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_estimacion_obra FOREIGN KEY (id_obra) REFERENCES obras.t_obra(id_obra) ON DELETE CASCADE,
    CONSTRAINT fk_estimacion_empresa FOREIGN KEY (id_empresa) REFERENCES obras.t_empresa(id_empresa) ON DELETE RESTRICT,
    CONSTRAINT chk_estimacion_estado CHECK (estado IN ('BORRADOR','APROBADA','ARCHIVADA')),
    CONSTRAINT chk_estimacion_factores CHECK ((factor_indirectos IS NULL OR factor_indirectos >= 0) AND (factor_utilidad IS NULL OR factor_utilidad >= 0))
);
CREATE INDEX IF NOT EXISTS idx_estimacion_obra ON obras.t_estimacion(id_obra);

CREATE TABLE IF NOT EXISTS obras.t_estimacion_analisis_precio_unitario (
    id_estimacion_analisis_precio_unitario SERIAL PRIMARY KEY,
    id_estimacion INTEGER NOT NULL,
    id_analisis_precio_unitario INTEGER NOT NULL,
    cantidad NUMERIC(12,3) NOT NULL CHECK (cantidad >= 0),
    orden INTEGER NOT NULL DEFAULT 1,
    observacion TEXT,
    CONSTRAINT fk_estimacion_apu_estimacion FOREIGN KEY (id_estimacion) REFERENCES obras.t_estimacion(id_estimacion) ON DELETE CASCADE,
    CONSTRAINT fk_estimacion_apu_apu FOREIGN KEY (id_analisis_precio_unitario) REFERENCES obras.t_analisis_precio_unitario(id_analisis_precio_unitario) ON DELETE RESTRICT,
    CONSTRAINT uq_estimacion_apu UNIQUE (id_estimacion, id_analisis_precio_unitario),
    CONSTRAINT uq_estimacion_apu_orden UNIQUE (id_estimacion, orden)
);

CREATE OR REPLACE FUNCTION obras.fn_actualizar_updated_at_estimacion_apu()
RETURNS TRIGGER AS $$ BEGIN NEW.updated_at = CURRENT_TIMESTAMP; RETURN NEW; END; $$ LANGUAGE plpgsql;
DROP TRIGGER IF EXISTS tg_mano_obra_updated_at ON obras.t_mano_obra;
CREATE TRIGGER tg_mano_obra_updated_at BEFORE UPDATE ON obras.t_mano_obra FOR EACH ROW EXECUTE FUNCTION obras.fn_actualizar_updated_at_estimacion_apu();
DROP TRIGGER IF EXISTS tg_apu_updated_at ON obras.t_analisis_precio_unitario;
CREATE TRIGGER tg_apu_updated_at BEFORE UPDATE ON obras.t_analisis_precio_unitario FOR EACH ROW EXECUTE FUNCTION obras.fn_actualizar_updated_at_estimacion_apu();
DROP TRIGGER IF EXISTS tg_apu_insumo_updated_at ON obras.t_analisi_precio_unitario_insumo;
CREATE TRIGGER tg_apu_insumo_updated_at BEFORE UPDATE ON obras.t_analisi_precio_unitario_insumo FOR EACH ROW EXECUTE FUNCTION obras.fn_actualizar_updated_at_estimacion_apu();
DROP TRIGGER IF EXISTS tg_estimacion_updated_at ON obras.t_estimacion;
CREATE TRIGGER tg_estimacion_updated_at BEFORE UPDATE ON obras.t_estimacion FOR EACH ROW EXECUTE FUNCTION obras.fn_actualizar_updated_at_estimacion_apu();

CREATE OR REPLACE FUNCTION obras.fn_calcular_analisis_precio_unitario(p_id_analisis_precio_unitario INTEGER, p_id_empresa INTEGER)
RETURNS json AS $$
DECLARE v_apu json; v_insumos json; v_total numeric;
BEGIN
    SELECT json_build_object('id_analisis_precio_unitario', a.id_analisis_precio_unitario, 'nombre', a.nombre, 'descripcion', a.descripcion,
        'id_unidad_medida', a.id_unidad_medida, 'tipo_analisis_precio_unitario', a.tipo_analisis_precio_unitario, 'calidad', a.calidad)
    INTO v_apu FROM obras.t_analisis_precio_unitario a WHERE a.id_analisis_precio_unitario = p_id_analisis_precio_unitario AND a.id_empresa = p_id_empresa;
    IF v_apu IS NULL THEN RETURN json_build_object('success', false, 'error', 'La partida no existe o no pertenece a su empresa.'); END IF;
    SELECT COALESCE(SUM(i.cantidad * i.precio_unitario), 0), COALESCE(json_agg(json_build_object('id', i.id_analisis_precio_unitario_insumo, 'tipo_insumo', i.tipo_insumo, 'nombre', i.nombre, 'cantidad', i.cantidad, 'precio_unitario', i.precio_unitario, 'total', ROUND(i.cantidad * i.precio_unitario, 2), 'id_unidad_medida', i.id_unidad_medida) ORDER BY i.orden, i.id_analisis_precio_unitario_insumo), '[]'::json)
    INTO v_total, v_insumos FROM obras.t_analisi_precio_unitario_insumo i WHERE i.id_analisis_precio_unitario = p_id_analisis_precio_unitario AND i.id_empresa = p_id_empresa;
    RETURN json_build_object('success', true, 'apu', v_apu, 'insumos', v_insumos, 'costo_directo_unitario', ROUND(v_total, 2));
END; $$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION obras.fn_calcular_estimacion(p_id_estimacion INTEGER, p_id_empresa INTEGER)
RETURNS json AS $$
DECLARE v_detalle json; v_directo numeric; v_indirectos numeric; v_utilidad numeric; v_total numeric; v_factor_i numeric; v_factor_u numeric;
BEGIN
    SELECT COALESCE(e.factor_indirectos, 0), COALESCE(e.factor_utilidad, 0) INTO v_factor_i, v_factor_u FROM obras.t_estimacion e WHERE e.id_estimacion = p_id_estimacion AND e.id_empresa = p_id_empresa;
    IF NOT FOUND THEN RETURN json_build_object('success', false, 'error', 'La estimación no existe o no pertenece a su empresa.'); END IF;
    SELECT COALESCE(SUM(x.costo * x.cantidad), 0), COALESCE(json_agg(json_build_object('id_analisis_precio_unitario', x.id_apu, 'nombre', x.nombre, 'unidad', x.abreviatura, 'costo_unitario', ROUND(x.costo, 2), 'cantidad', x.cantidad, 'subtotal', ROUND(x.costo * x.cantidad, 2)) ORDER BY x.orden), '[]'::json)
    INTO v_directo, v_detalle FROM (SELECT d.orden, d.cantidad, a.id_analisis_precio_unitario id_apu, a.nombre, um.abreviatura, COALESCE((SELECT SUM(i.cantidad * i.precio_unitario) FROM obras.t_analisi_precio_unitario_insumo i WHERE i.id_analisis_precio_unitario = a.id_analisis_precio_unitario AND i.id_empresa = p_id_empresa), 0) costo FROM obras.t_estimacion_analisis_precio_unitario d JOIN obras.t_estimacion e ON e.id_estimacion = d.id_estimacion JOIN obras.t_analisis_precio_unitario a ON a.id_analisis_precio_unitario = d.id_analisis_precio_unitario JOIN obras.t_unidad_medida um ON um.id_unidad_medida = a.id_unidad_medida WHERE d.id_estimacion = p_id_estimacion AND e.id_empresa = p_id_empresa AND a.id_empresa = p_id_empresa) x;
    v_indirectos := 0;
    v_utilidad := v_directo * v_factor_u;
    v_total := v_directo + v_utilidad;
    RETURN json_build_object('success', true, 'detalle', v_detalle, 'subtotal_directo', ROUND(v_directo, 2), 'indirectos', ROUND(v_indirectos, 2), 'utilidad', ROUND(v_utilidad, 2), 'monto_total', ROUND(v_total, 2));
END; $$ LANGUAGE plpgsql;

INSERT INTO obras.t_permiso(nombre_permiso)
SELECT nombre FROM (VALUES ('Visualizar_estimaciones'), ('Registrar_estimaciones'), ('Modificar_estimaciones'), ('Eliminar_estimaciones'), ('Visualizar_mano_obra'), ('Registrar_mano_obra')) p(nombre)
WHERE NOT EXISTS (SELECT 1 FROM obras.t_permiso x WHERE x.nombre_permiso = p.nombre);
INSERT INTO obras.t_rol_permiso(id_rol, id_permiso)
SELECT r.id_rol, p.id_permiso FROM obras.t_rol r CROSS JOIN obras.t_permiso p
WHERE UPPER(r.nombre_rol) = 'ADMINISTRADOR_EMPRESA' AND p.nombre_permiso IN ('Visualizar_estimaciones','Registrar_estimaciones','Modificar_estimaciones','Eliminar_estimaciones','Visualizar_mano_obra','Registrar_mano_obra')
ON CONFLICT DO NOTHING;

COMMIT;