-- =============================================================================
-- MIGRACIÓN CU33: Gestión de Garantías y Servicio Posventa (HU161 a HU168)
-- Esquema: obras
-- Idempotente y aditiva
-- =============================================================================

-- 1. TABLA DE GARANTÍAS INMOBILIARIAS (HU161, HU162, HU168)
CREATE TABLE IF NOT EXISTS obras.t_unidad_garantia (
    id_garantia SERIAL PRIMARY KEY,
    id_empresa INT NOT NULL REFERENCES obras.t_empresa(id_empresa) ON DELETE CASCADE,
    id_unidad INT NOT NULL REFERENCES obras.t_unidad_construccion(id_unidad) ON DELETE CASCADE,
    id_cliente INT NOT NULL REFERENCES obras.t_crm_cliente(id_cliente) ON DELETE CASCADE,
    tipo_garantia VARCHAR(60) NOT NULL,
    descripcion_cobertura TEXT NOT NULL,
    condiciones TEXT,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'VIGENTE',
    id_usuario_registro INT REFERENCES obras.t_usuario(id_usuario) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_garantia_fechas CHECK (fecha_fin >= fecha_inicio),
    CONSTRAINT chk_garantia_estado CHECK (estado IN ('VIGENTE', 'VENCIDA', 'ANULADA'))
);

CREATE INDEX IF NOT EXISTS idx_garantia_empresa ON obras.t_unidad_garantia (id_empresa);
CREATE INDEX IF NOT EXISTS idx_garantia_unidad ON obras.t_unidad_garantia (id_unidad);
CREATE INDEX IF NOT EXISTS idx_garantia_cliente ON obras.t_unidad_garantia (id_cliente);
CREATE INDEX IF NOT EXISTS idx_garantia_estado ON obras.t_unidad_garantia (estado);


-- 2. TABLA DE SOLICITUDES DE POSVENTA / TICKETS (HU163 a HU168)
CREATE TABLE IF NOT EXISTS obras.t_posventa_solicitud (
    id_solicitud SERIAL PRIMARY KEY,
    codigo_ticket VARCHAR(32) NOT NULL UNIQUE,
    id_empresa INT NOT NULL REFERENCES obras.t_empresa(id_empresa) ON DELETE CASCADE,
    id_unidad INT NOT NULL REFERENCES obras.t_unidad_construccion(id_unidad) ON DELETE RESTRICT,
    id_cliente INT NOT NULL REFERENCES obras.t_crm_cliente(id_cliente) ON DELETE RESTRICT,
    id_garantia INT REFERENCES obras.t_unidad_garantia(id_garantia) ON DELETE SET NULL,
    aplica_garantia BOOLEAN NULL,
    titulo VARCHAR(200) NOT NULL,
    descripcion_defecto TEXT NOT NULL,
    categoria VARCHAR(50) NULL,
    prioridad VARCHAR(20) NOT NULL DEFAULT 'MEDIA',
    estado VARCHAR(30) NOT NULL DEFAULT 'PENDIENTE',
    id_usuario_registro INT REFERENCES obras.t_usuario(id_usuario) ON DELETE SET NULL,
    id_usuario_clasifica INT REFERENCES obras.t_usuario(id_usuario) ON DELETE SET NULL,
    id_usuario_asigna INT REFERENCES obras.t_usuario(id_usuario) ON DELETE SET NULL,
    id_supervisor_asignado INT REFERENCES obras.t_usuario(id_usuario) ON DELETE SET NULL,
    fecha_estimada_visita DATE NULL,
    instrucciones_tecnicas TEXT NULL,
    observaciones_clasificacion TEXT NULL,
    fecha_cierre TIMESTAMPTZ NULL,
    motivo_rechazo_cierre TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_solicitud_prioridad CHECK (prioridad IN ('BAJA', 'MEDIA', 'ALTA', 'URGENTE')),
    CONSTRAINT chk_solicitud_estado CHECK (estado IN ('PENDIENTE', 'CLASIFICADA', 'ASIGNADA', 'EN_ATENCION', 'RESUELTA', 'CERRADA', 'RECHAZADA'))
);

CREATE INDEX IF NOT EXISTS idx_posventa_empresa ON obras.t_posventa_solicitud (id_empresa);
CREATE INDEX IF NOT EXISTS idx_posventa_unidad ON obras.t_posventa_solicitud (id_unidad);
CREATE INDEX IF NOT EXISTS idx_posventa_cliente ON obras.t_posventa_solicitud (id_cliente);
CREATE INDEX IF NOT EXISTS idx_posventa_supervisor ON obras.t_posventa_solicitud (id_supervisor_asignado);
CREATE INDEX IF NOT EXISTS idx_posventa_estado ON obras.t_posventa_solicitud (estado);
CREATE INDEX IF NOT EXISTS idx_posventa_ticket ON obras.t_posventa_solicitud (codigo_ticket);


-- 3. TABLA DE EVIDENCIAS Y FOTOGRAFÍAS DE POSVENTA (HU163, HU166)
CREATE TABLE IF NOT EXISTS obras.t_posventa_evidencia (
    id_evidencia SERIAL PRIMARY KEY,
    id_solicitud INT NOT NULL REFERENCES obras.t_posventa_solicitud(id_solicitud) ON DELETE CASCADE,
    tipo_evidencia VARCHAR(30) NOT NULL DEFAULT 'CLIENTE_REPORTE',
    ruta_archivo VARCHAR(500) NOT NULL,
    nombre_archivo VARCHAR(255) NOT NULL,
    tipo_mime VARCHAR(100),
    tamano_bytes INT,
    id_usuario INT REFERENCES obras.t_usuario(id_usuario) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_evidencia_tipo CHECK (tipo_evidencia IN ('CLIENTE_REPORTE', 'SUPERVISOR_REPARACION', 'DOCUMENTO_ADJUNTO'))
);

CREATE INDEX IF NOT EXISTS idx_posventa_evidencia_solicitud ON obras.t_posventa_evidencia (id_solicitud);


-- 4. TABLA DE BITÁCORA Y SEGUIMIENTO HISTÓRICO (HU166, HU167, HU168)
CREATE TABLE IF NOT EXISTS obras.t_posventa_bitacora (
    id_bitacora SERIAL PRIMARY KEY,
    id_solicitud INT NOT NULL REFERENCES obras.t_posventa_solicitud(id_solicitud) ON DELETE CASCADE,
    id_usuario INT REFERENCES obras.t_usuario(id_usuario) ON DELETE SET NULL,
    tipo_evento VARCHAR(40) NOT NULL,
    estado_anterior VARCHAR(30),
    estado_nuevo VARCHAR(30),
    detalle_acciones TEXT NOT NULL,
    materiales_utilizados TEXT NULL,
    fecha TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_posventa_bitacora_solicitud ON obras.t_posventa_bitacora (id_solicitud);


-- 5. PERMISOS DEL MÓDULO POSVENTA
DO $$
DECLARE modulo_id INT;
BEGIN
    SELECT id_modulo INTO modulo_id FROM obras.t_modulo WHERE nombre_modulo = 'Modulo_crm' LIMIT 1;
    IF modulo_id IS NULL THEN
        SELECT id_modulo INTO modulo_id FROM obras.t_modulo ORDER BY id_modulo LIMIT 1;
    END IF;

    -- Permisos para Garantías
    INSERT INTO obras.t_permiso (nombre_permiso, id_modulo)
    SELECT p, modulo_id FROM unnest(ARRAY[
        'Visualizar_garantias',
        'Registrar_garantias',
        'Modificar_garantias',
        'Visualizar_posventa',
        'Registrar_posventa',
        'Clasificar_posventa',
        'Asignar_posventa',
        'Atender_posventa',
        'Cerrar_posventa'
    ]) p
    WHERE NOT EXISTS (SELECT 1 FROM obras.t_permiso WHERE nombre_permiso = p);
END $$;

-- Asignación a roles
INSERT INTO obras.t_rol_permiso (id_rol, id_permiso)
SELECT r.id_rol, p.id_permiso
FROM obras.t_rol r
CROSS JOIN obras.t_permiso p
WHERE p.nombre_permiso IN (
    'Visualizar_garantias', 'Registrar_garantias', 'Modificar_garantias',
    'Visualizar_posventa', 'Registrar_posventa', 'Clasificar_posventa',
    'Asignar_posventa', 'Atender_posventa', 'Cerrar_posventa'
)
AND (
    upper(replace(r.nombre_rol, ' ', '_')) IN ('ADMINISTRADOR', 'ADMINISTRADOR_EMPRESA')
    OR (
        upper(replace(r.nombre_rol, ' ', '_')) IN ('JEFE_DE_OBRA', 'JEFE_OBRA')
        AND p.nombre_permiso IN ('Visualizar_garantias', 'Visualizar_posventa', 'Asignar_posventa', 'Atender_posventa')
    )
    OR (
        upper(replace(r.nombre_rol, ' ', '_')) IN ('SUPERVISOR', 'SUPERVISOR_OBRA')
        AND p.nombre_permiso IN ('Visualizar_posventa', 'Atender_posventa')
    )
    OR (
        upper(replace(r.nombre_rol, ' ', '_')) = 'CLIENTE'
        AND p.nombre_permiso IN ('Visualizar_garantias', 'Visualizar_posventa', 'Registrar_posventa')
    )
)
ON CONFLICT (id_rol, id_permiso) DO NOTHING;
