-- CU19: ejecutar despu?s de las migraciones existentes. No modifica OT ni permisos.
BEGIN;
ALTER TABLE obras.t_incidencia ALTER COLUMN estado TYPE VARCHAR(21);
ALTER TABLE obras.t_incidencia_seguimiento ALTER COLUMN estado_anterior TYPE VARCHAR(21);
ALTER TABLE obras.t_incidencia_seguimiento ALTER COLUMN estado_nuevo TYPE VARCHAR(21);
ALTER TABLE obras.t_incidencia DROP CONSTRAINT chk_incidencia_estado;
ALTER TABLE obras.t_incidencia ADD CONSTRAINT chk_incidencia_estado CHECK (estado IN ('ABIERTA','ASIGNADA','EN_PROCESO','PENDIENTE_VALIDACION','RESUELTA','CERRADA'));
ALTER TABLE obras.t_incidencia_seguimiento DROP CONSTRAINT chk_incidencia_seg_estado_nuevo;
ALTER TABLE obras.t_incidencia_seguimiento ADD CONSTRAINT chk_incidencia_seg_estado_nuevo CHECK (estado_nuevo IN ('ABIERTA','ASIGNADA','EN_PROCESO','PENDIENTE_VALIDACION','RESUELTA','CERRADA'));
ALTER TABLE obras.t_incidencia_seguimiento DROP CONSTRAINT chk_incidencia_seg_estado_anterior;
ALTER TABLE obras.t_incidencia_seguimiento ADD CONSTRAINT chk_incidencia_seg_estado_anterior CHECK (estado_anterior IS NULL OR estado_anterior IN ('ABIERTA','ASIGNADA','EN_PROCESO','PENDIENTE_VALIDACION','RESUELTA','CERRADA'));
ALTER TABLE obras.t_incidencia DROP CONSTRAINT chk_incidencia_fechas_estado;
ALTER TABLE obras.t_incidencia ADD CONSTRAINT chk_incidencia_fechas_estado CHECK (
    (estado IN ('ABIERTA','ASIGNADA') AND fecha_inicio_atencion IS NULL AND fecha_fin_atencion IS NULL)
    OR (estado = 'EN_PROCESO' AND fecha_inicio_atencion IS NOT NULL AND fecha_fin_atencion IS NULL)
    OR (estado IN ('PENDIENTE_VALIDACION','RESUELTA','CERRADA') AND fecha_inicio_atencion IS NOT NULL AND fecha_fin_atencion IS NOT NULL)
);
COMMIT;
