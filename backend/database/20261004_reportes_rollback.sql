-- Reversión estructural para un entorno sin historial de reportes.
-- Los permisos del catálogo se conservan: no se asume propiedad exclusiva de nombres globales.
BEGIN;
SELECT pg_advisory_xact_lock(20261004);
DO $$
BEGIN
 IF EXISTS(SELECT 1 FROM obras.t_reporte_ejecucion)
 OR EXISTS(SELECT 1 FROM obras.t_reporte_programacion)
 OR EXISTS(SELECT 1 FROM obras.t_asistente_conversacion) THEN
   RAISE EXCEPTION 'Hay datos de reportes/asistente. Conservar tablas y revertir el despliegue, o archivar antes de una reversión estructural.';
 END IF;
END $$;
DROP TABLE obras.t_asistente_mensaje;
DROP TABLE obras.t_asistente_conversacion;
DROP TABLE obras.t_reporte_envio;
DROP TABLE obras.t_reporte_archivo;
DROP TABLE obras.t_reporte_ejecucion;
DROP TABLE obras.t_reporte_programacion_destinatario;
DROP TABLE obras.t_reporte_programacion;
COMMIT;
