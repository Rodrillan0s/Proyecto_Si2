-- Migración incremental. Revisar/aplicar en el entorno elegido, no desde el arranque HTTP.
BEGIN;
SELECT pg_advisory_xact_lock(20261004);
CREATE TABLE IF NOT EXISTS obras.t_reporte_programacion (
 id UUID PRIMARY KEY, id_empresa INTEGER NOT NULL REFERENCES obras.t_empresa,
 id_usuario INTEGER NOT NULL REFERENCES obras.t_usuario,
 configuracion JSONB NOT NULL, habilitada BOOLEAN NOT NULL DEFAULT TRUE,
 next_run TIMESTAMPTZ NOT NULL, estado VARCHAR(20) NOT NULL DEFAULT 'ACTIVA',
 error TEXT, created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS obras.t_reporte_programacion_destinatario (
 programacion UUID NOT NULL REFERENCES obras.t_reporte_programacion,
 id_usuario INTEGER NOT NULL REFERENCES obras.t_usuario,
 PRIMARY KEY(programacion,id_usuario)
);
CREATE TABLE IF NOT EXISTS obras.t_reporte_ejecucion (
 id UUID PRIMARY KEY, id_empresa INTEGER NOT NULL REFERENCES obras.t_empresa,
 id_usuario INTEGER NOT NULL REFERENCES obras.t_usuario,
 programacion UUID REFERENCES obras.t_reporte_programacion,
 ocurrencia TIMESTAMPTZ, solicitud JSONB NOT NULL, politica JSONB NOT NULL,
 alcance INTEGER[] NOT NULL DEFAULT '{}', resultado JSONB,
 estado VARCHAR(20) NOT NULL CHECK(estado IN ('PENDIENTE','GENERANDO','LISTO','FALLIDO')),
 lease_until TIMESTAMPTZ, intentos INTEGER NOT NULL DEFAULT 0,
 error TEXT, created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 UNIQUE(programacion,ocurrencia)
);
CREATE TABLE IF NOT EXISTS obras.t_reporte_archivo (
 id UUID PRIMARY KEY, ejecucion UUID NOT NULL REFERENCES obras.t_reporte_ejecucion,
 formato VARCHAR(4) NOT NULL CHECK(formato IN ('pdf','xlsx')),
 nombre TEXT NOT NULL, contenido BYTEA NOT NULL CHECK(octet_length(contenido)<=5242880),
 sha256 CHAR(64) NOT NULL, expires_at TIMESTAMPTZ NOT NULL,
 UNIQUE(ejecucion,formato)
);
CREATE TABLE IF NOT EXISTS obras.t_reporte_envio (
 id UUID PRIMARY KEY, ejecucion UUID NOT NULL REFERENCES obras.t_reporte_ejecucion,
 id_usuario INTEGER NOT NULL REFERENCES obras.t_usuario, formatos JSONB NOT NULL,
 identidad TEXT NOT NULL UNIQUE,
 estado VARCHAR(20) NOT NULL DEFAULT 'PENDIENTE'
 CHECK(estado IN ('PENDIENTE','ENVIANDO','ACEPTADO','FALLIDO','INCIERTO')),
 intentos INTEGER NOT NULL DEFAULT 0, next_run TIMESTAMPTZ NOT NULL DEFAULT now(),
 lease_until TIMESTAMPTZ, message_id TEXT, error TEXT,
 resultado JSONB, created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS obras.t_asistente_conversacion (
 id UUID PRIMARY KEY, id_empresa INTEGER NOT NULL REFERENCES obras.t_empresa,
 id_usuario INTEGER NOT NULL REFERENCES obras.t_usuario,
 solicitud JSONB, expires_at TIMESTAMPTZ NOT NULL DEFAULT now()+interval '30 days'
);
CREATE TABLE IF NOT EXISTS obras.t_asistente_mensaje (
 id BIGSERIAL PRIMARY KEY, conversacion UUID NOT NULL REFERENCES obras.t_asistente_conversacion ON DELETE CASCADE,
 texto TEXT NOT NULL CHECK(length(texto)<=2000), respuesta JSONB NOT NULL,
 created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_reporte_due ON obras.t_reporte_programacion(next_run) WHERE habilitada;
CREATE INDEX IF NOT EXISTS idx_reporte_job ON obras.t_reporte_ejecucion(estado,lease_until);
CREATE INDEX IF NOT EXISTS idx_reporte_owner ON obras.t_reporte_ejecucion(id_empresa,id_usuario,created_at DESC);
CREATE INDEX IF NOT EXISTS idx_reporte_mail_due ON obras.t_reporte_envio(estado,next_run);
CREATE INDEX IF NOT EXISTS idx_reporte_expire ON obras.t_reporte_archivo(expires_at);
INSERT INTO obras.t_modulo(nombre_modulo)
SELECT 'Modulo_reportes' WHERE NOT EXISTS(SELECT 1 FROM obras.t_modulo WHERE nombre_modulo='Modulo_reportes');
INSERT INTO obras.t_permiso(nombre_permiso,id_modulo)
SELECT name,(SELECT min(id_modulo) FROM obras.t_modulo WHERE nombre_modulo='Modulo_reportes')
FROM unnest(ARRAY['Visualizar_reportes','Exportar_reportes','Enviar_reportes','Programar_reportes','Administrar_programaciones_reportes']) name
WHERE NOT EXISTS(SELECT 1 FROM obras.t_permiso p WHERE p.nombre_permiso=name);
INSERT INTO obras.t_rol_permiso(id_rol,id_permiso)
SELECT r.id_rol,p.id_permiso FROM obras.t_rol r CROSS JOIN obras.t_permiso p
WHERE p.nombre_permiso IN ('Visualizar_reportes','Exportar_reportes','Enviar_reportes','Programar_reportes','Administrar_programaciones_reportes')
AND (r.nombre_rol IN ('ADMINISTRADOR','ADMINISTRADOR_EMPRESA')
 OR (r.nombre_rol='JEFE DE OBRA' AND p.nombre_permiso<>'Administrar_programaciones_reportes')
 OR (r.nombre_rol IN ('CLIENTE','ELECTRICO','PLOMERO','MAESTROALBAÑIL','ALBAÑIL') AND p.nombre_permiso IN ('Visualizar_reportes','Exportar_reportes')))
ON CONFLICT DO NOTHING;
COMMIT;
