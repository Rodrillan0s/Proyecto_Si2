-- =============================================================================
-- MIGRACIÓN CU30: HU117 - CONSULTAR ESTADO DE SOLICITUDES ENVIADAS
-- =============================================================================
-- Crea la tabla aditiva obras.t_cliente_solicitud para el registro, gestión
-- y consulta de solicitudes y consultas formuladas por clientes sobre sus unidades.
--
-- No reutiliza ni modifica obras.t_incidencia (incidencias de obra / operarios).
-- Reutiliza obras.t_unidad_fotografia si se asocia una evidencia gráfica.
-- =============================================================================

CREATE TABLE IF NOT EXISTS obras.t_cliente_solicitud (
    id_solicitud SERIAL PRIMARY KEY,
    id_cliente INTEGER NOT NULL REFERENCES obras.t_crm_cliente(id_cliente) ON DELETE CASCADE,
    id_usuario INTEGER NOT NULL REFERENCES obras.t_usuario(id_usuario) ON DELETE CASCADE,
    id_empresa INTEGER NOT NULL REFERENCES obras.t_empresa(id_empresa) ON DELETE CASCADE,
    id_obra INTEGER NOT NULL REFERENCES obras.t_obra(id_obra) ON DELETE RESTRICT,
    id_unidad INTEGER NULL REFERENCES obras.t_unidad_construccion(id_unidad) ON DELETE SET NULL,
    titulo VARCHAR(200) NOT NULL,
    descripcion TEXT NOT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'PENDIENTE'
        CHECK (estado IN ('PENDIENTE', 'EN_PROCESO', 'ATENDIDA', 'RECHAZADA')),
    respuesta TEXT NULL,
    id_usuario_respuesta INTEGER NULL REFERENCES obras.t_usuario(id_usuario) ON DELETE SET NULL,
    id_fotografia_evidencia INTEGER NULL REFERENCES obras.t_unidad_fotografia(id_fotografia) ON DELETE SET NULL,
    fecha_creacion TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_respuesta TIMESTAMPTZ NULL,
    CONSTRAINT chk_solicitud_titulo_no_vacio CHECK (btrim(titulo) <> ''),
    CONSTRAINT chk_solicitud_desc_no_vacia CHECK (btrim(descripcion) <> '')
);

-- Índices para optimizar consultas por tenant, cliente, obra y unidad
CREATE INDEX IF NOT EXISTS idx_cliente_solicitud_cliente ON obras.t_cliente_solicitud(id_cliente);
CREATE INDEX IF NOT EXISTS idx_cliente_solicitud_usuario ON obras.t_cliente_solicitud(id_usuario);
CREATE INDEX IF NOT EXISTS idx_cliente_solicitud_empresa ON obras.t_cliente_solicitud(id_empresa);
CREATE INDEX IF NOT EXISTS idx_cliente_solicitud_obra    ON obras.t_cliente_solicitud(id_obra);
CREATE INDEX IF NOT EXISTS idx_cliente_solicitud_unidad  ON obras.t_cliente_solicitud(id_unidad);
CREATE INDEX IF NOT EXISTS idx_cliente_solicitud_estado  ON obras.t_cliente_solicitud(estado);
CREATE INDEX IF NOT EXISTS idx_cliente_solicitud_fecha   ON obras.t_cliente_solicitud(fecha_creacion DESC);
