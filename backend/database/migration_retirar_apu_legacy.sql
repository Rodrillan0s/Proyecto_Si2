-- Archive and retire the obsolete obras.t_apu model.
-- Current APU/estimation flow remains in t_analisis_precio_unitario and t_estimacion.
BEGIN;

CREATE TABLE IF NOT EXISTS obras.t_apu_legacy_archive (
    id_archivo BIGSERIAL PRIMARY KEY,
    tabla_origen VARCHAR(80) NOT NULL,
    id_origen TEXT NOT NULL,
    registro JSONB NOT NULL,
    archivado_en TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_apu_legacy_archive UNIQUE (tabla_origen, id_origen)
);

DO $archive$
BEGIN
    IF to_regclass('obras.t_categoria_apu') IS NOT NULL THEN
        INSERT INTO obras.t_apu_legacy_archive(tabla_origen, id_origen, registro)
        SELECT 't_categoria_apu', c.id_categoria::text, to_jsonb(c)
        FROM obras.t_categoria_apu c
        ON CONFLICT (tabla_origen, id_origen) DO NOTHING;
    END IF;

    IF to_regclass('obras.t_apu') IS NOT NULL THEN
        INSERT INTO obras.t_apu_legacy_archive(tabla_origen, id_origen, registro)
        SELECT 't_apu', a.id_apu::text, to_jsonb(a)
        FROM obras.t_apu a
        ON CONFLICT (tabla_origen, id_origen) DO NOTHING;
    END IF;

    IF to_regclass('obras.t_apu_componente') IS NOT NULL THEN
        INSERT INTO obras.t_apu_legacy_archive(tabla_origen, id_origen, registro)
        SELECT 't_apu_componente', c.id_componente::text, to_jsonb(c)
        FROM obras.t_apu_componente c
        ON CONFLICT (tabla_origen, id_origen) DO NOTHING;
    END IF;
END
$archive$;

DROP FUNCTION IF EXISTS obras.fn_copiar_apu_base_empresa(INTEGER, INTEGER, VARCHAR);
DROP FUNCTION IF EXISTS obras.fn_versionar_apu(INTEGER);
DROP FUNCTION IF EXISTS obras.fn_calcular_apu(INTEGER);

DO $budget_link$
BEGIN
    IF to_regclass('obras.t_partida_presupuesto') IS NOT NULL
       AND EXISTS (
           SELECT 1 FROM information_schema.columns
           WHERE table_schema = 'obras'
             AND table_name = 't_partida_presupuesto'
             AND column_name = 'id_apu'
       ) THEN
        ALTER TABLE obras.t_partida_presupuesto
            DROP CONSTRAINT IF EXISTS t_partida_presupuesto_id_apu_fkey;
        UPDATE obras.t_partida_presupuesto SET id_apu = NULL;
        ALTER TABLE obras.t_partida_presupuesto DROP COLUMN id_apu;
    END IF;
END
$budget_link$;

DROP TABLE IF EXISTS obras.t_apu_componente RESTRICT;
DROP TABLE IF EXISTS obras.t_apu RESTRICT;
DROP TABLE IF EXISTS obras.t_categoria_apu RESTRICT;

COMMIT;