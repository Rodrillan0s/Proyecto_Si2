-- =============================================================================
-- MIGRACIÓN: REFACTORIZACIÓN CU16 - PRESUPUESTO Y APU PROFESIONAL
-- =============================================================================

BEGIN;

SET search_path TO obras, public;

-- 1. Asegurar unidades de medida para tiempo (Hora, Día) si no existen
INSERT INTO obras.t_unidad_medida (nombre, abreviatura, estado)
SELECT 'Hora', 'hr', 'ACTIVO'
WHERE NOT EXISTS (
    SELECT 1 FROM obras.t_unidad_medida WHERE LOWER(nombre) = 'hora' OR LOWER(abreviatura) IN ('h', 'hr', 'hrs')
);

INSERT INTO obras.t_unidad_medida (nombre, abreviatura, estado)
SELECT 'Día', 'día', 'ACTIVO'
WHERE NOT EXISTS (
    SELECT 1 FROM obras.t_unidad_medida WHERE LOWER(nombre) IN ('día', 'dia') OR LOWER(abreviatura) IN ('d', 'dia')
);

-- 2. TABLA: t_equipo (Catálogo de Maquinaria y Equipos de Construcción)
CREATE TABLE IF NOT EXISTS obras.t_equipo (
    id_equipo SERIAL PRIMARY KEY,
    id_empresa INT NOT NULL REFERENCES obras.t_empresa(id_empresa) ON DELETE CASCADE,
    codigo VARCHAR(50) NOT NULL,
    nombre VARCHAR(200) NOT NULL,
    descripcion TEXT,
    id_unidad_medida INT NOT NULL REFERENCES obras.t_unidad_medida(id_unidad_medida),
    costo_unitario NUMERIC(15,2) NOT NULL DEFAULT 0.00,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_equipo_costo_pos CHECK (costo_unitario >= 0),
    CONSTRAINT uq_equipo_empresa_codigo UNIQUE (id_empresa, codigo)
);

CREATE INDEX IF NOT EXISTS idx_equipo_empresa ON obras.t_equipo(id_empresa);

-- 3. Modificaciones en t_apu para Versionado y Subtotales por Tipo de Recurso
ALTER TABLE obras.t_apu
    ADD COLUMN IF NOT EXISTS version INT NOT NULL DEFAULT 1,
    ADD COLUMN IF NOT EXISTS codigo_base VARCHAR(50),
    ADD COLUMN IF NOT EXISTS costo_materiales NUMERIC(15,2) NOT NULL DEFAULT 0.00,
    ADD COLUMN IF NOT EXISTS costo_mano_obra NUMERIC(15,2) NOT NULL DEFAULT 0.00,
    ADD COLUMN IF NOT EXISTS costo_equipos NUMERIC(15,2) NOT NULL DEFAULT 0.00,
    ADD COLUMN IF NOT EXISTS costo_directo NUMERIC(15,2) NOT NULL DEFAULT 0.00,
    ADD COLUMN IF NOT EXISTS es_vigente BOOLEAN NOT NULL DEFAULT TRUE;

-- Actualizar filas existentes
UPDATE obras.t_apu 
SET codigo_base = codigo 
WHERE codigo_base IS NULL;

UPDATE obras.t_apu 
SET costo_directo = costo_unitario_total 
WHERE costo_directo = 0.00 AND costo_unitario_total > 0;

-- Ajustar restricción de unicidad para permitir versionado por empresa
ALTER TABLE obras.t_apu DROP CONSTRAINT IF EXISTS uq_apu_empresa_codigo;
ALTER TABLE obras.t_apu DROP CONSTRAINT IF EXISTS uq_apu_empresa_codigo_ver;
ALTER TABLE obras.t_apu ADD CONSTRAINT uq_apu_empresa_codigo_ver UNIQUE (id_empresa, codigo_base, version);

CREATE INDEX IF NOT EXISTS idx_apu_codigo_base ON obras.t_apu(id_empresa, codigo_base);

-- 4. Modificaciones en t_apu_componente para rendimientos
ALTER TABLE obras.t_apu_componente
    ADD COLUMN IF NOT EXISTS rendimiento NUMERIC(14,4) NOT NULL DEFAULT 1.0000;

UPDATE obras.t_apu_componente
SET rendimiento = cantidad
WHERE rendimiento = 1.0000 AND cantidad != 1.0000;

-- Clave foránea para equipos si tipo_recurso = 'EQUIPO'
ALTER TABLE obras.t_apu_componente DROP CONSTRAINT IF EXISTS fk_apu_comp_equipo;
ALTER TABLE obras.t_apu_componente
    ADD CONSTRAINT fk_apu_comp_equipo 
    FOREIGN KEY (id_recurso) REFERENCES obras.t_equipo(id_equipo) 
    ON DELETE SET NULL;

-- 5. Poblar catálogo base de Equipos / Maquinaria para todas las constructoras
DO $$
DECLARE
    emp RECORD;
    v_id_hr INT;
    v_id_dia INT;
BEGIN
    SELECT id_unidad_medida INTO v_id_hr FROM obras.t_unidad_medida WHERE abreviatura IN ('hr', 'h') LIMIT 1;
    IF v_id_hr IS NULL THEN
        SELECT id_unidad_medida INTO v_id_hr FROM obras.t_unidad_medida WHERE nombre ILIKE '%hora%' LIMIT 1;
    END IF;

    SELECT id_unidad_medida INTO v_id_dia FROM obras.t_unidad_medida WHERE abreviatura IN ('día', 'dia', 'd') LIMIT 1;
    IF v_id_dia IS NULL THEN
        SELECT id_unidad_medida INTO v_id_dia FROM obras.t_unidad_medida WHERE nombre ILIKE '%día%' LIMIT 1;
    END IF;

    FOR emp IN SELECT id_empresa FROM obras.t_empresa WHERE id_empresa != 2 LOOP
        -- Mezcladora de Hormigón 350L
        IF NOT EXISTS (SELECT 1 FROM obras.t_equipo WHERE id_empresa = emp.id_empresa AND codigo = 'EQ-001') THEN
            INSERT INTO obras.t_equipo (id_empresa, codigo, nombre, descripcion, id_unidad_medida, costo_unitario)
            VALUES (emp.id_empresa, 'EQ-001', 'Mezcladora de Hormigón 350L', 'Mezcladora de trompo motor a gasolina 8HP para hormigón y mortero', v_id_hr, 35.00);
        END IF;

        -- Vibradora de Inmersión 4HP
        IF NOT EXISTS (SELECT 1 FROM obras.t_equipo WHERE id_empresa = emp.id_empresa AND codigo = 'EQ-002') THEN
            INSERT INTO obras.t_equipo (id_empresa, codigo, nombre, descripcion, id_unidad_medida, costo_unitario)
            VALUES (emp.id_empresa, 'EQ-002', 'Vibradora de Inmersión 4HP', 'Vibradora de aguja para compactación de hormigón en columnas y vigas', v_id_hr, 25.00);
        END IF;

        -- Cortadora de Cerámica y Porcelanato
        IF NOT EXISTS (SELECT 1 FROM obras.t_equipo WHERE id_empresa = emp.id_empresa AND codigo = 'EQ-003') THEN
            INSERT INTO obras.t_equipo (id_empresa, codigo, nombre, descripcion, id_unidad_medida, costo_unitario)
            VALUES (emp.id_empresa, 'EQ-003', 'Cortadora Eléctrica de Disco', 'Cortadora de agua con disco diamantado para cerámica, porcelanato y azulejo', v_id_hr, 20.00);
        END IF;

        -- Compactadora tipo Canguro
        IF NOT EXISTS (SELECT 1 FROM obras.t_equipo WHERE id_empresa = emp.id_empresa AND codigo = 'EQ-004') THEN
            INSERT INTO obras.t_equipo (id_empresa, codigo, nombre, descripcion, id_unidad_medida, costo_unitario)
            VALUES (emp.id_empresa, 'EQ-004', 'Compactadora tipo Canguro (Sapito)', 'Pisón vibratorio de percusión para zanjas y cimientos', v_id_hr, 45.00);
        END IF;

        -- Guinche elevador 500kg
        IF NOT EXISTS (SELECT 1 FROM obras.t_equipo WHERE id_empresa = emp.id_empresa AND codigo = 'EQ-005') THEN
            INSERT INTO obras.t_equipo (id_empresa, codigo, nombre, descripcion, id_unidad_medida, costo_unitario)
            VALUES (emp.id_empresa, 'EQ-005', 'Guinche Elevador 500 kg', 'Elevador eléctrico monofásico/trifásico de balde para elevación vertical de materiales', v_id_hr, 30.00);
        END IF;

        -- Andamio Metálico Tubular
        IF NOT EXISTS (SELECT 1 FROM obras.t_equipo WHERE id_empresa = emp.id_empresa AND codigo = 'EQ-006') THEN
            INSERT INTO obras.t_equipo (id_empresa, codigo, nombre, descripcion, id_unidad_medida, costo_unitario)
            VALUES (emp.id_empresa, 'EQ-006', 'Andamio Metálico Tubular (Cuerpo)', 'Cuerpo de andamio metálico normalizado de 2.0x1.5m con crucetas y tablón metálico', v_id_dia, 15.00);
        END IF;

        -- Retroexcavadora con pala
        IF NOT EXISTS (SELECT 1 FROM obras.t_equipo WHERE id_empresa = emp.id_empresa AND codigo = 'EQ-007') THEN
            INSERT INTO obras.t_equipo (id_empresa, codigo, nombre, descripcion, id_unidad_medida, costo_unitario)
            VALUES (emp.id_empresa, 'EQ-007', 'Retroexcavadora Oruga/Neumático', 'Maquinaria pesada para excavación masiva de zanjas y movimiento de tierras', v_id_hr, 220.00);
        END IF;

        -- Camión Volqueta 6 m3
        IF NOT EXISTS (SELECT 1 FROM obras.t_equipo WHERE id_empresa = emp.id_empresa AND codigo = 'EQ-008') THEN
            INSERT INTO obras.t_equipo (id_empresa, codigo, nombre, descripcion, id_unidad_medida, costo_unitario)
            VALUES (emp.id_empresa, 'EQ-008', 'Camión Volqueta 6 m³', 'Transporte y retiro de material excedente y escombros', v_id_hr, 180.00);
        END IF;
    END LOOP;
END $$;

COMMIT;
