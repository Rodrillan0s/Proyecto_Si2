-- Ejecutar SOLO en la base de control independiente designada. Nunca en obras.
BEGIN;
SELECT pg_advisory_xact_lock(2026100402);
CREATE SCHEMA IF NOT EXISTS backup_control;
CREATE TABLE IF NOT EXISTS backup_control.t_backup_control (
 id INTEGER PRIMARY KEY CHECK(id=1), version INTEGER NOT NULL DEFAULT 1,
 mantenimiento BOOLEAN NOT NULL DEFAULT FALSE, propietario UUID, motivo TEXT,
 session_epoch BIGINT NOT NULL DEFAULT 0, heartbeat TIMESTAMPTZ,
 updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
INSERT INTO backup_control.t_backup_control(id) VALUES(1) ON CONFLICT DO NOTHING;
CREATE TABLE IF NOT EXISTS backup_control.t_backup_programacion (
 id INTEGER PRIMARY KEY CHECK(id=1), configuracion JSONB NOT NULL,
 id_usuario INTEGER NOT NULL, next_run TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS backup_control.t_backup_ejecucion (
 id UUID PRIMARY KEY, id_usuario INTEGER NOT NULL, solicitud JSONB NOT NULL,
 origen TEXT NOT NULL, identidad TEXT NOT NULL UNIQUE,
 estado TEXT NOT NULL CHECK(estado IN ('PENDIENTE','GENERANDO','VERIFICANDO','LISTO','FALLIDO')),
 etapa TEXT NOT NULL DEFAULT 'En cola', intentos INTEGER NOT NULL DEFAULT 0,
 lease_until TIMESTAMPTZ, worker UUID, error TEXT, archivo UUID,
 protegido BOOLEAN NOT NULL DEFAULT FALSE,
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(), finished_at TIMESTAMPTZ
);
CREATE TABLE IF NOT EXISTS backup_control.t_backup_archivo (
 id UUID PRIMARY KEY, ejecucion UUID REFERENCES backup_control.t_backup_ejecucion,
 nombre TEXT NOT NULL UNIQUE, sha256 CHAR(64) NOT NULL, bytes BIGINT NOT NULL,
 alcance TEXT NOT NULL, key_id TEXT NOT NULL, manifiesto JSONB NOT NULL,
 remoto TEXT, protegido BOOLEAN NOT NULL DEFAULT FALSE,
 verificado_en TIMESTAMPTZ, eliminado_en TIMESTAMPTZ, created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS backup_control.t_backup_restauracion (
 id UUID PRIMARY KEY, archivo UUID NOT NULL REFERENCES backup_control.t_backup_archivo,
 id_usuario INTEGER NOT NULL, estado TEXT NOT NULL,
 etapa TEXT NOT NULL, operacion TEXT NOT NULL DEFAULT 'VALIDAR',
 lease_until TIMESTAMPTZ, worker UUID, error TEXT,
 stage_db TEXT, stage_dir TEXT, desafio TEXT, validada_en TIMESTAMPTZ,
 aplicar_en TIMESTAMPTZ, prebackup UUID, diario JSONB NOT NULL DEFAULT '[]',
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(), finished_at TIMESTAMPTZ
);
CREATE TABLE IF NOT EXISTS backup_control.t_backup_evento (
 id BIGSERIAL PRIMARY KEY, recurso UUID, id_usuario INTEGER, tipo TEXT NOT NULL,
 detalle JSONB NOT NULL DEFAULT '{}', created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
-- Leases de escritores HTTP y workers: la barrera se comparte entre procesos.
CREATE TABLE IF NOT EXISTS backup_control.t_backup_escritor (
 id UUID PRIMARY KEY, tipo TEXT NOT NULL, lease_until TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS backup_jobs_due ON backup_control.t_backup_ejecucion(estado,created_at);
CREATE INDEX IF NOT EXISTS backup_restore_due ON backup_control.t_backup_restauracion(estado,created_at);
COMMIT;
