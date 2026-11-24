-- ============================================================================
-- Migración aditiva PREPARADA (NO aplicada automáticamente)
-- Extensión compatible de atributos comerciales de amoblamiento en unidades
-- Fecha: 2026-11-24
-- ============================================================================

BEGIN;

ALTER TABLE obras.t_unidad_construccion
    ADD COLUMN IF NOT EXISTS estado_amoblamiento VARCHAR(30) NOT NULL DEFAULT 'DESCONOCIDO'
        CHECK (estado_amoblamiento IN ('AMOBLADA', 'PARCIALMENTE_AMOBLADA', 'SIN_AMOBLAR', 'DESCONOCIDO'));

ALTER TABLE obras.t_unidad_construccion
    ADD COLUMN IF NOT EXISTS costo_mobiliario_estimado NUMERIC(14, 2) NULL
        CHECK (costo_mobiliario_estimado IS NULL OR costo_mobiliario_estimado >= 0);

COMMENT ON COLUMN obras.t_unidad_construccion.estado_amoblamiento IS
    'Estado verificable de mobiliario de la unidad: AMOBLADA, PARCIALMENTE_AMOBLADA, SIN_AMOBLAR o DESCONOCIDO.';

COMMENT ON COLUMN obras.t_unidad_construccion.costo_mobiliario_estimado IS
    'Costo referencial opcional de paquete de mobiliario en la moneda comercial de la unidad.';

COMMIT;
