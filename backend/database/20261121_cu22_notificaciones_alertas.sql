-- ============================================================================
-- CU22: Gestionar comunicaciones y notificaciones (HU141 y HU142)
-- Migración aditiva e idempotente sobre el esquema obras.
-- PREPARADA: no se aplica automáticamente; ejecutar solo en entornos autorizados.
-- ============================================================================

BEGIN;

-- 1. Tabla de configuración de alertas por eventos (HU141)
-- Permite reglas generales por empresa (id_obra IS NULL) y sobrescritura opcional por obra.
CREATE TABLE IF NOT EXISTS obras.t_configuracion_alerta_evento (
    id_configuracion SERIAL PRIMARY KEY,
    id_empresa INTEGER NOT NULL REFERENCES obras.t_empresa(id_empresa) ON DELETE CASCADE,
    id_obra INTEGER NULL REFERENCES obras.t_obra(id_obra) ON DELETE CASCADE,
    tipo_evento VARCHAR(60) NOT NULL,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    roles_destino JSONB NOT NULL DEFAULT '["ADMINISTRADOR_EMPRESA", "JEFE DE OBRA"]'::jsonb,
    actualizado_por INTEGER NULL REFERENCES obras.t_usuario(id_usuario) ON DELETE SET NULL,
    creado_en TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_config_alerta_tipo_evento CHECK (
        tipo_evento IN (
            'AVANCE_OBRA',
            'INCIDENCIA',
            'ORDEN_TRABAJO',
            'CONSULTA_TECNICA',
            'OBRA_ESTADO',
            'ORDEN_CAMBIO',
            'CRONOGRAMA',
            'CRM_PROSPECTO'
        )
    ),
    CONSTRAINT chk_config_alerta_roles_array CHECK (jsonb_typeof(roles_destino) = 'array')
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_config_alerta_empresa_obra_evento
    ON obras.t_configuracion_alerta_evento (id_empresa, COALESCE(id_obra, 0), tipo_evento);

CREATE INDEX IF NOT EXISTS idx_config_alerta_empresa_obra
    ON obras.t_configuracion_alerta_evento (id_empresa, id_obra);

-- 2. Mejoras aditivas en obras.notificacion para trazabilidad, rendimiento e idempotencia (HU142)
ALTER TABLE obras.notificacion
    ADD COLUMN IF NOT EXISTS id_empresa INTEGER NULL;

ALTER TABLE obras.notificacion
    ADD COLUMN IF NOT EXISTS id_obra INTEGER NULL;

ALTER TABLE obras.notificacion
    ADD COLUMN IF NOT EXISTS clave_evento VARCHAR(160) NULL;

CREATE INDEX IF NOT EXISTS idx_notificacion_usuario_leido_fecha
    ON obras.notificacion (nro_usuario, leido, fecha_creacion DESC, id_notificacion DESC);

CREATE UNIQUE INDEX IF NOT EXISTS uq_notificacion_usuario_clave_evento
    ON obras.notificacion (nro_usuario, clave_evento)
    WHERE clave_evento IS NOT NULL;

COMMIT;
