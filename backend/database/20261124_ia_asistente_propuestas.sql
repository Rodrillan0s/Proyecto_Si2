-- ============================================================================
-- Migración aditiva PREPARADA (NO aplicada automáticamente)
-- Persistencia y auditoría de propuestas de operación del Asistente IA
-- Fecha: 2026-11-24
-- ============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS obras.t_asistente_propuesta (
    id_propuesta   UUID PRIMARY KEY,
    id_empresa     INTEGER NOT NULL REFERENCES obras.t_empresa(id_empresa),
    id_usuario     INTEGER NOT NULL REFERENCES obras.t_usuario(id_usuario),
    tipo_operacion VARCHAR(60) NOT NULL,
    entidad        VARCHAR(120) NOT NULL,
    resumen        TEXT NOT NULL,
    parametros     JSONB NOT NULL DEFAULT '{}'::jsonb,
    politica       JSONB NOT NULL DEFAULT '{}'::jsonb,
    contexto_obra  INTEGER NULL REFERENCES obras.t_obra(id_obra),
    estado         VARCHAR(20) NOT NULL DEFAULT 'PENDIENTE'
        CHECK (estado IN ('PENDIENTE', 'EJECUTANDO', 'EJECUTADA', 'CANCELADA', 'EXPIRADA')),
    resultado      JSONB NULL,
    creado_en      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expira_en      TIMESTAMPTZ NOT NULL,
    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_asistente_propuesta_actor
    ON obras.t_asistente_propuesta (id_empresa, id_usuario, estado, creado_en DESC);

CREATE INDEX IF NOT EXISTS idx_asistente_propuesta_expira
    ON obras.t_asistente_propuesta (expira_en)
    WHERE estado = 'PENDIENTE';

COMMENT ON TABLE obras.t_asistente_propuesta IS
    'Tickets persistentes de operaciones asistidas propuestas por el Asistente IA que requieren confirmación explícita.';

COMMIT;
