-- =============================================================================
-- MIGRACIÓN ADITIVA CU42: Índices dedicados para obras.t_solicitud_posventa
-- Motivo: Los nombres idx_posventa_unidad e idx_posventa_cliente ya existían
--         en obras.t_posventa_solicitud; PostgreSQL requiere unicidad de nombre
--         de índice dentro del esquema.
-- Alcance: Exclusivamente aditivo. No modifica datos ni afecta índices previos.
-- =============================================================================

CREATE INDEX IF NOT EXISTS idx_solicitud_posventa_unidad
    ON obras.t_solicitud_posventa (id_unidad, creado_en DESC);

CREATE INDEX IF NOT EXISTS idx_solicitud_posventa_cliente
    ON obras.t_solicitud_posventa (id_cliente, creado_en DESC);
