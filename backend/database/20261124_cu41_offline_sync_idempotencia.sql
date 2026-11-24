-- =============================================================================
-- MIGRACIÓN CU41: Operación Offline y Sincronización (Idempotencia y Marcas Temporales)
-- HUs asociadas: HU91, HU92, HU93, HU94
-- Estado: PREPARADA PARA REVISIÓN (NO ejecutar automáticamente sin autorización)
-- =============================================================================
-- Migración aditiva y retrocompatible con CU18 (avances) y CU19 (incidencias).
-- No modifica contratos ni columnas existentes.
-- =============================================================================

CREATE TABLE IF NOT EXISTS obras.t_sync_operacion_offline (
    id_sync BIGSERIAL PRIMARY KEY,
    client_operation_id VARCHAR(100) NOT NULL,
    id_empresa INTEGER NOT NULL REFERENCES obras.t_empresa(id_empresa) ON DELETE RESTRICT,
    id_usuario INTEGER NOT NULL REFERENCES obras.t_usuario(id_usuario) ON DELETE RESTRICT,
    tipo_operacion VARCHAR(30) NOT NULL
        CHECK (tipo_operacion IN ('AVANCE_OBRA', 'INCIDENCIA')),
    id_obra INTEGER NOT NULL REFERENCES obras.t_obra(id_obra) ON DELETE RESTRICT,
    id_recurso_creado INTEGER NULL,
    fecha_ocurrencia_local TIMESTAMPTZ NOT NULL,
    fecha_sincronizacion TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    estado VARCHAR(20) NOT NULL DEFAULT 'EN_PROCESO'
        CHECK (estado IN ('EN_PROCESO', 'PROCESADO', 'ERROR')),
    respuesta_json JSONB NULL,
    CONSTRAINT chk_sync_client_op_no_vacio CHECK (btrim(client_operation_id) <> ''),
    CONSTRAINT uq_sync_op_idempotencia UNIQUE (id_empresa, id_usuario, tipo_operacion, client_operation_id)
);

CREATE INDEX IF NOT EXISTS idx_sync_op_empresa_usuario
    ON obras.t_sync_operacion_offline (id_empresa, id_usuario, fecha_sincronizacion DESC);

CREATE INDEX IF NOT EXISTS idx_sync_op_obra
    ON obras.t_sync_operacion_offline (id_obra);

-- Columnas opcionales para diferenciar ocurrencia offline vs sincronización (HU91 / HU92)
ALTER TABLE obras.t_avance_obra
    ADD COLUMN IF NOT EXISTS fecha_ocurrencia_local TIMESTAMPTZ NULL,
    ADD COLUMN IF NOT EXISTS fecha_sincronizacion TIMESTAMPTZ NULL;

ALTER TABLE obras.t_incidencia
    ADD COLUMN IF NOT EXISTS fecha_ocurrencia_local TIMESTAMPTZ NULL,
    ADD COLUMN IF NOT EXISTS fecha_sincronizacion TIMESTAMPTZ NULL;
