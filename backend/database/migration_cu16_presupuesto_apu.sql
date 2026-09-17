-- =============================================================================
-- MIGRACIÓN CU16: GESTIONAR PRESUPUESTOS Y APU (HISTORIAS DE USUARIO HU53–HU60)
-- =============================================================================

BEGIN;

SET search_path TO obras, public;

-- -----------------------------------------------------------------------------
-- 1. TABLA: t_presupuesto
-- Representa el presupuesto de una obra creada en CU11.
-- Soporta versionado, inmutabilidad tras aprobación y estimación paramétrica inicial.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS obras.t_presupuesto (
    id_presupuesto SERIAL PRIMARY KEY,
    id_obra INT NOT NULL REFERENCES obras.t_obra(id_obra) ON DELETE CASCADE,
    codigo VARCHAR(50) NOT NULL,
    nombre VARCHAR(200) NOT NULL,
    descripcion TEXT,
    version INT NOT NULL DEFAULT 1,
    estado VARCHAR(30) NOT NULL DEFAULT 'BORRADOR',
    es_vigente BOOLEAN NOT NULL DEFAULT FALSE,
    fecha DATE NOT NULL DEFAULT CURRENT_DATE,
    
    -- Estimación Paramétrica Inicial (Requerimientos Preliminares)
    superficie_m2 NUMERIC(12,2) DEFAULT NULL,
    tipo_suelo VARCHAR(100) DEFAULT NULL,
    costo_m2_estimado NUMERIC(15,2) DEFAULT NULL,
    monto_estimado_inicial NUMERIC(15,2) DEFAULT NULL,
    
    -- Costo Analítico Consolidado (Calculado a partir de partidas)
    total_presupuesto NUMERIC(15,2) NOT NULL DEFAULT 0.00,
    observaciones TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_presupuesto_estado 
        CHECK (estado IN ('BORRADOR', 'EN_REVISION', 'APROBADO', 'CERRADO')),
    CONSTRAINT chk_presupuesto_version_pos 
        CHECK (version >= 1),
    CONSTRAINT uq_presupuesto_obra_version 
        UNIQUE (id_obra, version)
);

-- Solo una versión vigente por obra a la vez
CREATE UNIQUE INDEX IF NOT EXISTS uq_presupuesto_obra_vigente 
ON obras.t_presupuesto (id_obra) 
WHERE (es_vigente = TRUE);

CREATE INDEX IF NOT EXISTS idx_presupuesto_obra 
ON obras.t_presupuesto (id_obra);


-- -----------------------------------------------------------------------------
-- 2. TABLA: t_apu (Análisis de Precios Unitarios)
-- Biblioteca corporativa de APU reutilizable por empresa (y opcionalmente obra).
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS obras.t_apu (
    id_apu SERIAL PRIMARY KEY,
    id_empresa INT NOT NULL REFERENCES obras.t_empresa(id_empresa) ON DELETE CASCADE,
    id_obra INT REFERENCES obras.t_obra(id_obra) ON DELETE SET NULL,
    codigo VARCHAR(50) NOT NULL,
    nombre VARCHAR(200) NOT NULL,
    descripcion TEXT,
    id_unidad_medida INT NOT NULL REFERENCES obras.t_unidad_medida(id_unidad_medida),
    rendimiento_base NUMERIC(12,4) NOT NULL DEFAULT 1.0000,
    costo_unitario_total NUMERIC(15,2) NOT NULL DEFAULT 0.00,
    estado VARCHAR(20) NOT NULL DEFAULT 'ACTIVO',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_apu_estado 
        CHECK (estado IN ('ACTIVO', 'INACTIVO')),
    CONSTRAINT uq_apu_empresa_codigo 
        UNIQUE (id_empresa, codigo)
);

CREATE INDEX IF NOT EXISTS idx_apu_empresa 
ON obras.t_apu (id_empresa);

CREATE INDEX IF NOT EXISTS idx_apu_obra 
ON obras.t_apu (id_obra);


-- -----------------------------------------------------------------------------
-- 3. TABLA: t_apu_componente
-- Insumos (Materiales, Mano de Obra, Equipos) que integran el APU.
-- Guarda snapshot histórico del precio_unitario del componente.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS obras.t_apu_componente (
    id_componente SERIAL PRIMARY KEY,
    id_apu INT NOT NULL REFERENCES obras.t_apu(id_apu) ON DELETE CASCADE,
    tipo_recurso VARCHAR(20) NOT NULL,
    id_recurso INT DEFAULT NULL, -- Si es MATERIAL, FK a t_material(id_material).
    descripcion_recurso VARCHAR(200) NOT NULL,
    id_unidad_medida INT NOT NULL REFERENCES obras.t_unidad_medida(id_unidad_medida),
    cantidad NUMERIC(14,4) NOT NULL DEFAULT 1.0000,
    precio_unitario NUMERIC(15,2) NOT NULL DEFAULT 0.00,
    subtotal NUMERIC(15,2) NOT NULL DEFAULT 0.00,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_apu_comp_tipo 
        CHECK (tipo_recurso IN ('MATERIAL', 'MANO_OBRA', 'EQUIPO')),
    CONSTRAINT chk_apu_comp_cant_pos 
        CHECK (cantidad >= 0),
    CONSTRAINT chk_apu_comp_precio_pos 
        CHECK (precio_unitario >= 0)
);

-- Si id_recurso está presente y es MATERIAL, valida con t_material
ALTER TABLE obras.t_apu_componente
    DROP CONSTRAINT IF EXISTS fk_apu_comp_material;
ALTER TABLE obras.t_apu_componente
    ADD CONSTRAINT fk_apu_comp_material 
    FOREIGN KEY (id_recurso) REFERENCES obras.t_material(id_material) 
    ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_apu_componente_apu 
ON obras.t_apu_componente (id_apu);


-- -----------------------------------------------------------------------------
-- 4. TABLA: t_partida_presupuesto
-- Conceptos de costo de la obra.
-- Conserva el costo unitario aplicado (snapshot) al asociar el APU.
-- Relación con CU12 (estructura/unidad) es estrictamente opcional/desacoplada.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS obras.t_partida_presupuesto (
    id_partida SERIAL PRIMARY KEY,
    id_presupuesto INT NOT NULL REFERENCES obras.t_presupuesto(id_presupuesto) ON DELETE CASCADE,
    id_apu INT REFERENCES obras.t_apu(id_apu) ON DELETE SET NULL,
    codigo VARCHAR(50) NOT NULL,
    nombre VARCHAR(200) NOT NULL,
    descripcion TEXT,
    id_unidad_medida INT NOT NULL REFERENCES obras.t_unidad_medida(id_unidad_medida),
    cantidad NUMERIC(14,4) NOT NULL DEFAULT 1.0000,
    precio_unitario NUMERIC(15,2) NOT NULL DEFAULT 0.00,
    importe_total NUMERIC(15,2) NOT NULL DEFAULT 0.00,
    orden INT NOT NULL DEFAULT 0,
    
    -- Vínculos opcionales con CU12 (desacoplados)
    id_estructura INT REFERENCES obras.t_estructura_obra(id_estructura) ON DELETE SET NULL,
    id_unidad_construccion INT REFERENCES obras.t_unidad_construccion(id_unidad) ON DELETE SET NULL,
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_partida_cant_pos 
        CHECK (cantidad >= 0),
    CONSTRAINT chk_partida_precio_pos 
        CHECK (precio_unitario >= 0)
);

CREATE INDEX IF NOT EXISTS idx_partida_presupuesto 
ON obras.t_partida_presupuesto (id_presupuesto);

CREATE INDEX IF NOT EXISTS idx_partida_apu 
ON obras.t_partida_presupuesto (id_apu);


-- -----------------------------------------------------------------------------
-- 5. TABLA: t_costo_ejecutado
-- Registra los costos reales incurridos en la obra (HU59).
-- Totalmente independiente del presupuesto (no modifica las partidas).
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS obras.t_costo_ejecutado (
    id_costo_ejecutado SERIAL PRIMARY KEY,
    id_obra INT NOT NULL REFERENCES obras.t_obra(id_obra) ON DELETE CASCADE,
    id_partida INT REFERENCES obras.t_partida_presupuesto(id_partida) ON DELETE SET NULL,
    codigo_costo VARCHAR(50),
    origen_costo VARCHAR(30) NOT NULL DEFAULT 'REGISTRO_MANUAL',
    tipo_recurso VARCHAR(20) NOT NULL DEFAULT 'MATERIAL',
    descripcion VARCHAR(250) NOT NULL,
    id_unidad_medida INT REFERENCES obras.t_unidad_medida(id_unidad_medida),
    cantidad NUMERIC(14,4) NOT NULL DEFAULT 1.0000,
    costo_unitario NUMERIC(15,2) NOT NULL DEFAULT 0.00,
    importe_total NUMERIC(15,2) NOT NULL DEFAULT 0.00,
    fecha DATE NOT NULL DEFAULT CURRENT_DATE,
    observacion TEXT,
    id_usuario_registro INT NOT NULL REFERENCES obras.t_usuario(id_usuario),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_costo_ejec_origen 
        CHECK (origen_costo IN ('REGISTRO_MANUAL', 'ALMACEN', 'COMPRA', 'MANO_OBRA', 'EQUIPO', 'SUBCONTRATO', 'OTRO')),
    CONSTRAINT chk_costo_ejec_tipo 
        CHECK (tipo_recurso IN ('MATERIAL', 'MANO_OBRA', 'EQUIPO', 'OTRO')),
    CONSTRAINT chk_costo_ejec_cant_pos 
        CHECK (cantidad >= 0),
    CONSTRAINT chk_costo_ejec_unit_pos 
        CHECK (costo_unitario >= 0)
);

CREATE INDEX IF NOT EXISTS idx_costo_ejecutado_obra 
ON obras.t_costo_ejecutado (id_obra);

CREATE INDEX IF NOT EXISTS idx_costo_ejecutado_partida 
ON obras.t_costo_ejecutado (id_partida);


-- -----------------------------------------------------------------------------
-- 6. TRIGGERS: UPDATED_AT
-- -----------------------------------------------------------------------------
DROP TRIGGER IF EXISTS tg_presupuesto_actualizar ON obras.t_presupuesto;
CREATE TRIGGER tg_presupuesto_actualizar
    BEFORE UPDATE ON obras.t_presupuesto
    FOR EACH ROW
    EXECUTE FUNCTION obras.fn_actualizar_updated_at();

DROP TRIGGER IF EXISTS tg_apu_actualizar ON obras.t_apu;
CREATE TRIGGER tg_apu_actualizar
    BEFORE UPDATE ON obras.t_apu
    FOR EACH ROW
    EXECUTE FUNCTION obras.fn_actualizar_updated_at();

DROP TRIGGER IF EXISTS tg_partida_actualizar ON obras.t_partida_presupuesto;
CREATE TRIGGER tg_partida_actualizar
    BEFORE UPDATE ON obras.t_partida_presupuesto
    FOR EACH ROW
    EXECUTE FUNCTION obras.fn_actualizar_updated_at();


-- -----------------------------------------------------------------------------
-- 7. MÓDULO Y PERMISOS DEL SISTEMA
-- -----------------------------------------------------------------------------
INSERT INTO obras.t_modulo (nombre_modulo)
SELECT 'Modulo_presupuestos'
WHERE NOT EXISTS (
    SELECT 1 FROM obras.t_modulo WHERE nombre_modulo = 'Modulo_presupuestos'
);

DO $$
DECLARE
    v_id_modulo INT;
    v_id_perm_vis INT;
    v_id_perm_reg INT;
    v_id_perm_mod INT;
    v_id_perm_apr INT;
    v_id_perm_costo INT;
    r_id_admin INT;
    r_id_admin_emp INT;
    r_id_jefe_obra INT;
BEGIN
    SELECT id_modulo INTO v_id_modulo FROM obras.t_modulo WHERE nombre_modulo = 'Modulo_presupuestos';

    -- Registrar permisos si no existen
    IF NOT EXISTS (SELECT 1 FROM obras.t_permiso WHERE nombre_permiso = 'Visualizar_presupuesto') THEN
        INSERT INTO obras.t_permiso (nombre_permiso, id_modulo) VALUES ('Visualizar_presupuesto', v_id_modulo);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM obras.t_permiso WHERE nombre_permiso = 'Registrar_presupuesto') THEN
        INSERT INTO obras.t_permiso (nombre_permiso, id_modulo) VALUES ('Registrar_presupuesto', v_id_modulo);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM obras.t_permiso WHERE nombre_permiso = 'Modificar_presupuesto') THEN
        INSERT INTO obras.t_permiso (nombre_permiso, id_modulo) VALUES ('Modificar_presupuesto', v_id_modulo);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM obras.t_permiso WHERE nombre_permiso = 'Aprobar_presupuesto') THEN
        INSERT INTO obras.t_permiso (nombre_permiso, id_modulo) VALUES ('Aprobar_presupuesto', v_id_modulo);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM obras.t_permiso WHERE nombre_permiso = 'Registrar_costo_ejecutado') THEN
        INSERT INTO obras.t_permiso (nombre_permiso, id_modulo) VALUES ('Registrar_costo_ejecutado', v_id_modulo);
    END IF;

    -- Obtener IDs de permisos
    SELECT id_permiso INTO v_id_perm_vis FROM obras.t_permiso WHERE nombre_permiso = 'Visualizar_presupuesto';
    SELECT id_permiso INTO v_id_perm_reg FROM obras.t_permiso WHERE nombre_permiso = 'Registrar_presupuesto';
    SELECT id_permiso INTO v_id_perm_mod FROM obras.t_permiso WHERE nombre_permiso = 'Modificar_presupuesto';
    SELECT id_permiso INTO v_id_perm_apr FROM obras.t_permiso WHERE nombre_permiso = 'Aprobar_presupuesto';
    SELECT id_permiso INTO v_id_perm_costo FROM obras.t_permiso WHERE nombre_permiso = 'Registrar_costo_ejecutado';

    -- Obtener IDs de roles reales
    SELECT id_rol INTO r_id_admin FROM obras.t_rol WHERE nombre_rol = 'ADMINISTRADOR';
    SELECT id_rol INTO r_id_admin_emp FROM obras.t_rol WHERE nombre_rol = 'ADMINISTRADOR_EMPRESA';
    SELECT id_rol INTO r_id_jefe_obra FROM obras.t_rol WHERE nombre_rol = 'JEFE DE OBRA';

    -- Asignar a ADMINISTRADOR
    IF r_id_admin IS NOT NULL THEN
        INSERT INTO obras.t_rol_permiso (id_rol, id_permiso) VALUES
            (r_id_admin, v_id_perm_vis),
            (r_id_admin, v_id_perm_reg),
            (r_id_admin, v_id_perm_mod),
            (r_id_admin, v_id_perm_apr),
            (r_id_admin, v_id_perm_costo)
        ON CONFLICT DO NOTHING;
    END IF;

    -- Asignar a ADMINISTRADOR_EMPRESA
    IF r_id_admin_emp IS NOT NULL THEN
        INSERT INTO obras.t_rol_permiso (id_rol, id_permiso) VALUES
            (r_id_admin_emp, v_id_perm_vis),
            (r_id_admin_emp, v_id_perm_reg),
            (r_id_admin_emp, v_id_perm_mod),
            (r_id_admin_emp, v_id_perm_apr),
            (r_id_admin_emp, v_id_perm_costo)
        ON CONFLICT DO NOTHING;
    END IF;

    -- Asignar a JEFE DE OBRA
    IF r_id_jefe_obra IS NOT NULL THEN
        INSERT INTO obras.t_rol_permiso (id_rol, id_permiso) VALUES
            (r_id_jefe_obra, v_id_perm_vis),
            (r_id_jefe_obra, v_id_perm_reg),
            (r_id_jefe_obra, v_id_perm_mod),
            (r_id_jefe_obra, v_id_perm_apr),
            (r_id_jefe_obra, v_id_perm_costo)
        ON CONFLICT DO NOTHING;
    END IF;

END $$;

COMMIT;
