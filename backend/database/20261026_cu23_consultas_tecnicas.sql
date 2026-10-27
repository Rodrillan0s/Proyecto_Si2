-- ============================================================================
-- Migración: CU23 — Gestionar consultas técnicas de obra (RFI)
-- Fecha: 2026-10-26
-- Esquema: obras
-- Descripción:
--   Crea las tablas t_consulta_tecnica, t_consulta_tecnica_respuesta y
--   t_consulta_tecnica_historial para el seguimiento auditable del ciclo
--   de vida de consultas técnicas (RFI) de proyectos de construcción.
--   Registra permisos RBAC en t_permiso y los asigna en t_rol_permiso.
-- ============================================================================

-- 1. Tabla principal: t_consulta_tecnica
CREATE TABLE IF NOT EXISTS obras.t_consulta_tecnica (
    id_consulta_tecnica SERIAL PRIMARY KEY,
    id_empresa INTEGER NOT NULL REFERENCES obras.t_empresa(id_empresa) ON DELETE CASCADE,
    id_obra INTEGER NOT NULL REFERENCES obras.t_obra(id_obra) ON DELETE CASCADE,
    codigo VARCHAR(50) NOT NULL,
    asunto VARCHAR(200) NOT NULL,
    descripcion TEXT NOT NULL,
    referencia_tecnica VARCHAR(255),
    estado VARCHAR(30) NOT NULL DEFAULT 'ABIERTA',
    creado_por INTEGER NOT NULL REFERENCES obras.t_usuario(id_usuario) ON DELETE RESTRICT,
    asignado_a INTEGER REFERENCES obras.t_usuario(id_usuario) ON DELETE SET NULL,
    fecha_asignacion TIMESTAMPTZ,
    asignado_por INTEGER REFERENCES obras.t_usuario(id_usuario) ON DELETE SET NULL,
    fecha_cierre TIMESTAMPTZ,
    cerrado_por INTEGER REFERENCES obras.t_usuario(id_usuario) ON DELETE SET NULL,
    motivo_cierre TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_consulta_tecnica_estado CHECK (
        estado IN ('ABIERTA', 'ASIGNADA', 'RESPONDIDA', 'CERRADA')
    ),
    CONSTRAINT chk_consulta_tecnica_asunto CHECK (
        btrim(asunto) <> ''
    ),
    CONSTRAINT chk_consulta_tecnica_descripcion CHECK (
        btrim(descripcion) <> ''
    ),
    CONSTRAINT uq_consulta_tecnica_codigo UNIQUE (id_empresa, id_obra, codigo)
);

CREATE INDEX IF NOT EXISTS idx_consulta_tecnica_empresa_obra_estado 
    ON obras.t_consulta_tecnica (id_empresa, id_obra, estado);

CREATE INDEX IF NOT EXISTS idx_consulta_tecnica_asignado 
    ON obras.t_consulta_tecnica (asignado_a);

-- 2. Tabla de respuestas técnicas: t_consulta_tecnica_respuesta
CREATE TABLE IF NOT EXISTS obras.t_consulta_tecnica_respuesta (
    id_consulta_tecnica_respuesta SERIAL PRIMARY KEY,
    id_consulta_tecnica INTEGER NOT NULL REFERENCES obras.t_consulta_tecnica(id_consulta_tecnica) ON DELETE CASCADE,
    autor_id INTEGER NOT NULL REFERENCES obras.t_usuario(id_usuario) ON DELETE RESTRICT,
    contenido TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_consulta_respuesta_contenido CHECK (
        btrim(contenido) <> ''
    )
);

CREATE INDEX IF NOT EXISTS idx_consulta_respuesta_consulta 
    ON obras.t_consulta_tecnica_respuesta (id_consulta_tecnica, created_at ASC);

-- 3. Tabla de historial y auditoría: t_consulta_tecnica_historial
CREATE TABLE IF NOT EXISTS obras.t_consulta_tecnica_historial (
    id_historial SERIAL PRIMARY KEY,
    id_consulta_tecnica INTEGER NOT NULL REFERENCES obras.t_consulta_tecnica(id_consulta_tecnica) ON DELETE CASCADE,
    actor_id INTEGER NOT NULL REFERENCES obras.t_usuario(id_usuario) ON DELETE RESTRICT,
    tipo_evento VARCHAR(50) NOT NULL,
    estado_anterior VARCHAR(30),
    estado_nuevo VARCHAR(30),
    detalle TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_consulta_historial_evento CHECK (
        tipo_evento IN ('CREACION', 'ASIGNACION', 'REASIGNACION', 'RESPUESTA', 'CIERRE', 'REAPERTURA')
    )
);

CREATE INDEX IF NOT EXISTS idx_consulta_historial_consulta 
    ON obras.t_consulta_tecnica_historial (id_consulta_tecnica, created_at DESC);

-- 4. Registro de permisos RBAC para CU23
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM obras.t_permiso WHERE nombre_permiso = 'Visualizar_consultas_tecnicas') THEN
        INSERT INTO obras.t_permiso (nombre_permiso, id_modulo) VALUES ('Visualizar_consultas_tecnicas', 3);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM obras.t_permiso WHERE nombre_permiso = 'Registrar_consultas_tecnicas') THEN
        INSERT INTO obras.t_permiso (nombre_permiso, id_modulo) VALUES ('Registrar_consultas_tecnicas', 3);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM obras.t_permiso WHERE nombre_permiso = 'Asignar_consultas_tecnicas') THEN
        INSERT INTO obras.t_permiso (nombre_permiso, id_modulo) VALUES ('Asignar_consultas_tecnicas', 3);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM obras.t_permiso WHERE nombre_permiso = 'Responder_consultas_tecnicas') THEN
        INSERT INTO obras.t_permiso (nombre_permiso, id_modulo) VALUES ('Responder_consultas_tecnicas', 3);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM obras.t_permiso WHERE nombre_permiso = 'Cerrar_consultas_tecnicas') THEN
        INSERT INTO obras.t_permiso (nombre_permiso, id_modulo) VALUES ('Cerrar_consultas_tecnicas', 3);
    END IF;
END $$;

-- 5. Asignación de permisos a roles correspondientes
-- Rol 1: ADMINISTRADOR
-- Rol 3: ADMINISTRADOR_EMPRESA
-- Rol 4: JEFE DE OBRA
-- Rol 9: SUPERVISOR_OBRA
DO $$
DECLARE
    v_perm_ver INT;
    v_perm_reg INT;
    v_perm_asig INT;
    v_perm_resp INT;
    v_perm_cerr INT;
BEGIN
    SELECT id_permiso INTO v_perm_ver FROM obras.t_permiso WHERE nombre_permiso = 'Visualizar_consultas_tecnicas';
    SELECT id_permiso INTO v_perm_reg FROM obras.t_permiso WHERE nombre_permiso = 'Registrar_consultas_tecnicas';
    SELECT id_permiso INTO v_perm_asig FROM obras.t_permiso WHERE nombre_permiso = 'Asignar_consultas_tecnicas';
    SELECT id_permiso INTO v_perm_resp FROM obras.t_permiso WHERE nombre_permiso = 'Responder_consultas_tecnicas';
    SELECT id_permiso INTO v_perm_cerr FROM obras.t_permiso WHERE nombre_permiso = 'Cerrar_consultas_tecnicas';

    -- Administrador Global (Rol 1): Todos los permisos
    INSERT INTO obras.t_rol_permiso (id_rol, id_permiso) VALUES (1, v_perm_ver) ON CONFLICT DO NOTHING;
    INSERT INTO obras.t_rol_permiso (id_rol, id_permiso) VALUES (1, v_perm_reg) ON CONFLICT DO NOTHING;
    INSERT INTO obras.t_rol_permiso (id_rol, id_permiso) VALUES (1, v_perm_asig) ON CONFLICT DO NOTHING;
    INSERT INTO obras.t_rol_permiso (id_rol, id_permiso) VALUES (1, v_perm_resp) ON CONFLICT DO NOTHING;
    INSERT INTO obras.t_rol_permiso (id_rol, id_permiso) VALUES (1, v_perm_cerr) ON CONFLICT DO NOTHING;

    -- Administrador de Empresa (Rol 3): Todos los permisos en su tenant
    INSERT INTO obras.t_rol_permiso (id_rol, id_permiso) VALUES (3, v_perm_ver) ON CONFLICT DO NOTHING;
    INSERT INTO obras.t_rol_permiso (id_rol, id_permiso) VALUES (3, v_perm_reg) ON CONFLICT DO NOTHING;
    INSERT INTO obras.t_rol_permiso (id_rol, id_permiso) VALUES (3, v_perm_asig) ON CONFLICT DO NOTHING;
    INSERT INTO obras.t_rol_permiso (id_rol, id_permiso) VALUES (3, v_perm_resp) ON CONFLICT DO NOTHING;
    INSERT INTO obras.t_rol_permiso (id_rol, id_permiso) VALUES (3, v_perm_cerr) ON CONFLICT DO NOTHING;

    -- Jefe de Obra (Rol 4): Todos los permisos
    INSERT INTO obras.t_rol_permiso (id_rol, id_permiso) VALUES (4, v_perm_ver) ON CONFLICT DO NOTHING;
    INSERT INTO obras.t_rol_permiso (id_rol, id_permiso) VALUES (4, v_perm_reg) ON CONFLICT DO NOTHING;
    INSERT INTO obras.t_rol_permiso (id_rol, id_permiso) VALUES (4, v_perm_asig) ON CONFLICT DO NOTHING;
    INSERT INTO obras.t_rol_permiso (id_rol, id_permiso) VALUES (4, v_perm_resp) ON CONFLICT DO NOTHING;
    INSERT INTO obras.t_rol_permiso (id_rol, id_permiso) VALUES (4, v_perm_cerr) ON CONFLICT DO NOTHING;

    -- Supervisor de Obra (Rol 9): Visualizar, Registrar, Responder y Asignar
    INSERT INTO obras.t_rol_permiso (id_rol, id_permiso) VALUES (9, v_perm_ver) ON CONFLICT DO NOTHING;
    INSERT INTO obras.t_rol_permiso (id_rol, id_permiso) VALUES (9, v_perm_reg) ON CONFLICT DO NOTHING;
    INSERT INTO obras.t_rol_permiso (id_rol, id_permiso) VALUES (9, v_perm_asig) ON CONFLICT DO NOTHING;
    INSERT INTO obras.t_rol_permiso (id_rol, id_permiso) VALUES (9, v_perm_resp) ON CONFLICT DO NOTHING;
END $$;
