-- Solo en obratec_control. No modifica public.backup_jobs ni public.system_state.
BEGIN;
SELECT pg_advisory_xact_lock(2026100502);
DO $$ BEGIN
 IF current_database()='obras' OR to_regclass('public.backup_jobs') IS NULL
    OR to_regclass('backup_control.t_backup_control') IS NULL THEN
  RAISE EXCEPTION 'Se requiere la base de control con cola VM y barrera instaladas';
 END IF;
END $$;
CREATE TABLE IF NOT EXISTS backup_control.t_backup_vm_request (
 -- Referencia lógica: no añadir FK/triggers a la cola que mantiene el daemon.
 identidad TEXT PRIMARY KEY, job_id BIGINT NOT NULL UNIQUE,
 id_usuario INTEGER NOT NULL, origen TEXT NOT NULL CHECK(origen IN ('MANUAL','AUTOMATICO')),
 created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMIT;
