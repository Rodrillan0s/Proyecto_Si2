-- Incremental: no repone límites ni cambia asignaciones vigentes.
ALTER TABLE obras.t_plan_suscripcion
    ADD COLUMN IF NOT EXISTS modulos jsonb,
    ADD COLUMN IF NOT EXISTS version integer NOT NULL DEFAULT 1 CHECK (version>0),
    ADD COLUMN IF NOT EXISTS actualizado_en timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP;
UPDATE obras.t_plan_suscripcion SET modulos=
    '["obras","avances","ordenes_trabajo","incidencias","presupuestos","control_costos","compras","inventario","materiales","proveedores","equipos","crm","usuarios","reportes"]'::jsonb
    || CASE WHEN consultas_ia_mes>0 THEN '["ia"]'::jsonb ELSE '[]'::jsonb END
WHERE modulos IS NULL;
ALTER TABLE obras.t_plan_suscripcion ALTER COLUMN modulos SET NOT NULL;
ALTER TABLE obras.t_plan_suscripcion ALTER COLUMN modulos SET DEFAULT
    '["obras","avances","ordenes_trabajo","incidencias","presupuestos","control_costos","compras","inventario","materiales","proveedores","equipos","crm","usuarios","reportes"]'::jsonb;
DO $$ BEGIN
    IF NOT EXISTS(SELECT 1 FROM pg_constraint WHERE conrelid='obras.t_plan_suscripcion'::regclass AND conname='chk_plan_modulos') THEN
        ALTER TABLE obras.t_plan_suscripcion ADD CONSTRAINT chk_plan_modulos CHECK (
            jsonb_typeof(modulos)='array' AND modulos <@
            '["obras","avances","ordenes_trabajo","incidencias","presupuestos","control_costos","compras","inventario","materiales","proveedores","equipos","crm","usuarios","reportes","ia"]'::jsonb);
    END IF;
END $$;
CREATE TABLE IF NOT EXISTS obras.t_plan_suscripcion_historial (
    id bigserial PRIMARY KEY,
    codigo_plan varchar(20) NOT NULL REFERENCES obras.t_plan_suscripcion(codigo),
    version integer NOT NULL,
    id_actor integer REFERENCES obras.t_usuario(id_usuario) ON DELETE SET NULL,
    antes jsonb NOT NULL,
    despues jsonb NOT NULL,
    empresas_afectadas jsonb NOT NULL,
    creado_en timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(codigo_plan,version)
);
