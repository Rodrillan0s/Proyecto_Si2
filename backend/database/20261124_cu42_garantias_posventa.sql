-- =============================================================================
-- MIGRACIÓN CU42: Garantías Inmobiliarias y Servicio Posventa (HU161–HU168)
-- Estado: PREPARADA PARA REVISIÓN (NO ejecutar automáticamente sin autorización)
-- =============================================================================
-- Migración aditiva y aislada: no modifica CU30 (t_cliente_solicitud) ni CU31.
-- Reutiliza t_empresa, t_unidad_construccion, t_crm_cliente y t_usuario.
-- =============================================================================

CREATE TABLE IF NOT EXISTS obras.t_garantia_inmobiliaria (
    id_garantia SERIAL PRIMARY KEY,
    id_empresa INTEGER NOT NULL REFERENCES obras.t_empresa(id_empresa) ON DELETE RESTRICT,
    id_unidad INTEGER NOT NULL REFERENCES obras.t_unidad_construccion(id_unidad) ON DELETE RESTRICT,
    codigo VARCHAR(50) NULL,
    tipo_garantia VARCHAR(80) NOT NULL,
    descripcion TEXT NOT NULL,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NULL,
    observaciones TEXT NULL,
    id_usuario_registro INTEGER NOT NULL REFERENCES obras.t_usuario(id_usuario) ON DELETE RESTRICT,
    creado_en TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_garantia_tipo_no_vacio CHECK (btrim(tipo_garantia) <> ''),
    CONSTRAINT chk_garantia_desc_no_vacia CHECK (btrim(descripcion) <> ''),
    CONSTRAINT chk_garantia_fechas CHECK (fecha_fin IS NULL OR fecha_fin >= fecha_inicio)
);

CREATE INDEX IF NOT EXISTS idx_garantia_empresa_unidad
    ON obras.t_garantia_inmobiliaria (id_empresa, id_unidad, creado_en DESC);

CREATE TABLE IF NOT EXISTS obras.t_solicitud_posventa (
    id_solicitud_posventa SERIAL PRIMARY KEY,
    id_empresa INTEGER NOT NULL REFERENCES obras.t_empresa(id_empresa) ON DELETE RESTRICT,
    id_unidad INTEGER NOT NULL REFERENCES obras.t_unidad_construccion(id_unidad) ON DELETE RESTRICT,
    id_cliente INTEGER NOT NULL REFERENCES obras.t_crm_cliente(id_cliente) ON DELETE RESTRICT,
    id_garantia INTEGER NULL REFERENCES obras.t_garantia_inmobiliaria(id_garantia) ON DELETE SET NULL,
    titulo VARCHAR(200) NOT NULL,
    descripcion TEXT NOT NULL,
    categoria VARCHAR(50) NULL,
    estado VARCHAR(30) NOT NULL DEFAULT 'REGISTRADA'
        CHECK (estado IN ('REGISTRADA', 'CLASIFICADA', 'ASIGNADA', 'EN_ATENCION', 'RESUELTA', 'CERRADA')),
    id_responsable INTEGER NULL REFERENCES obras.t_usuario(id_usuario) ON DELETE SET NULL,
    id_usuario_creacion INTEGER NOT NULL REFERENCES obras.t_usuario(id_usuario) ON DELETE RESTRICT,
    creado_en TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_posventa_titulo_no_vacio CHECK (btrim(titulo) <> ''),
    CONSTRAINT chk_posventa_desc_no_vacia CHECK (btrim(descripcion) <> '')
);

CREATE INDEX IF NOT EXISTS idx_posventa_empresa_estado
    ON obras.t_solicitud_posventa (id_empresa, estado, creado_en DESC);

CREATE INDEX IF NOT EXISTS idx_posventa_unidad
    ON obras.t_solicitud_posventa (id_unidad, creado_en DESC);

CREATE INDEX IF NOT EXISTS idx_posventa_cliente
    ON obras.t_solicitud_posventa (id_cliente, creado_en DESC);

CREATE INDEX IF NOT EXISTS idx_posventa_responsable
    ON obras.t_solicitud_posventa (id_responsable);

CREATE TABLE IF NOT EXISTS obras.t_posventa_seguimiento (
    id_seguimiento SERIAL PRIMARY KEY,
    id_solicitud_posventa INTEGER NOT NULL REFERENCES obras.t_solicitud_posventa(id_solicitud_posventa) ON DELETE CASCADE,
    id_usuario INTEGER NOT NULL REFERENCES obras.t_usuario(id_usuario) ON DELETE RESTRICT,
    accion VARCHAR(40) NOT NULL
        CHECK (accion IN ('REGISTRO', 'CLASIFICACION', 'ASIGNACION', 'ATENCION', 'CAMBIO_ESTADO')),
    estado_anterior VARCHAR(30) NULL,
    estado_nuevo VARCHAR(30) NULL,
    observacion TEXT NOT NULL,
    creado_en TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_posventa_seg_obs_no_vacia CHECK (btrim(observacion) <> '')
);

CREATE INDEX IF NOT EXISTS idx_posventa_seguimiento_solicitud
    ON obras.t_posventa_seguimiento (id_solicitud_posventa, creado_en ASC, id_seguimiento ASC);
