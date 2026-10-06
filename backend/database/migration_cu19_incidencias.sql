-- ============================================================================
-- MIGRACIÓN CU19: Gestión de incidencias (HU69-HU74)
-- Ejecutar manualmente sobre la base de datos. Incremental y segura para
-- re-ejecución (no usa DROP TABLE, no borra información existente).
-- ============================================================================
BEGIN;

-- ─────────────────────────────────────────────────────────────────────────────
-- 1. TABLA PRINCIPAL: t_incidencia
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS obras.t_incidencia (
    id_incidencia        SERIAL PRIMARY KEY,
    id_obra              INTEGER      NOT NULL,
    id_unidad            INTEGER      NULL,
    id_usuario_registro  INTEGER      NOT NULL,
    id_responsable       INTEGER      NULL,
    titulo               VARCHAR(200) NOT NULL,
    descripcion          TEXT         NOT NULL,
    prioridad            VARCHAR(10)  NOT NULL,
    estado               VARCHAR(20)  NOT NULL DEFAULT 'ABIERTA',
    created_at           TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at           TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_incidencia_obra FOREIGN KEY (id_obra)
        REFERENCES obras.t_obra(id_obra) ON DELETE RESTRICT,
    CONSTRAINT fk_incidencia_unidad FOREIGN KEY (id_unidad)
        REFERENCES obras.t_unidad_construccion(id_unidad) ON DELETE SET NULL,
    CONSTRAINT fk_incidencia_usuario_registro FOREIGN KEY (id_usuario_registro)
        REFERENCES obras.t_usuario(id_usuario) ON DELETE RESTRICT,
    CONSTRAINT fk_incidencia_responsable FOREIGN KEY (id_responsable)
        REFERENCES obras.t_usuario(id_usuario) ON DELETE SET NULL,

    CONSTRAINT chk_incidencia_titulo CHECK (BTRIM(titulo) <> ''),
    CONSTRAINT chk_incidencia_descripcion CHECK (BTRIM(descripcion) <> ''),
    CONSTRAINT chk_incidencia_prioridad CHECK (prioridad IN ('BAJA', 'MEDIA', 'ALTA', 'CRITICA')),
    CONSTRAINT chk_incidencia_estado CHECK (estado IN ('ABIERTA', 'ASIGNADA', 'EN_PROCESO', 'RESUELTA', 'CERRADA'))
);

-- Nota: id_empresa NO se almacena en t_incidencia; se deriva siempre por
-- t_incidencia -> t_obra -> id_empresa (ver incidencia_repos.py), igual que
-- se hace en obras.t_unidad_construccion.

CREATE INDEX IF NOT EXISTS idx_incidencia_obra          ON obras.t_incidencia(id_obra);
CREATE INDEX IF NOT EXISTS idx_incidencia_unidad        ON obras.t_incidencia(id_unidad);
CREATE INDEX IF NOT EXISTS idx_incidencia_responsable   ON obras.t_incidencia(id_responsable);
CREATE INDEX IF NOT EXISTS idx_incidencia_estado        ON obras.t_incidencia(estado);
CREATE INDEX IF NOT EXISTS idx_incidencia_prioridad     ON obras.t_incidencia(prioridad);
CREATE INDEX IF NOT EXISTS idx_incidencia_obra_estado   ON obras.t_incidencia(id_obra, estado);

CREATE OR REPLACE FUNCTION obras.fn_actualizar_updated_at_cu19()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tg_cu19_actualizar_incidencia ON obras.t_incidencia;
CREATE TRIGGER tg_cu19_actualizar_incidencia
    BEFORE UPDATE ON obras.t_incidencia
    FOR EACH ROW EXECUTE FUNCTION obras.fn_actualizar_updated_at_cu19();

-- ─────────────────────────────────────────────────────────────────────────────
-- 2. SEGUIMIENTO: obras.t_incidencia_seguimiento
--    (historial cronológico de comentarios y cambios de estado; distinto de
--     la bitácora general del sistema obras.t_bitacora)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS obras.t_incidencia_seguimiento (
    id_seguimiento  SERIAL PRIMARY KEY,
    id_incidencia   INTEGER      NOT NULL,
    id_usuario      INTEGER      NULL,
    estado_anterior VARCHAR(20)  NULL,
    estado_nuevo    VARCHAR(20)  NOT NULL,
    observacion     TEXT,
    fecha           TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_incidencia_seguimiento_incidencia FOREIGN KEY (id_incidencia)
        REFERENCES obras.t_incidencia(id_incidencia) ON DELETE CASCADE,
    CONSTRAINT fk_incidencia_seguimiento_usuario FOREIGN KEY (id_usuario)
        REFERENCES obras.t_usuario(id_usuario) ON DELETE SET NULL,
    CONSTRAINT chk_incidencia_seg_estado_nuevo CHECK (
        estado_nuevo IN ('ABIERTA', 'ASIGNADA', 'EN_PROCESO', 'RESUELTA', 'CERRADA')
    ),
    CONSTRAINT chk_incidencia_seg_estado_anterior CHECK (
        estado_anterior IS NULL OR estado_anterior IN ('ABIERTA', 'ASIGNADA', 'EN_PROCESO', 'RESUELTA', 'CERRADA')
    )
);

CREATE INDEX IF NOT EXISTS idx_incidencia_seguimiento_incidencia_fecha
    ON obras.t_incidencia_seguimiento(id_incidencia, fecha DESC);

-- ─────────────────────────────────────────────────────────────────────────────
-- 3. EVIDENCIAS: obras.t_incidencia_evidencia (HU73)
--    No existía infraestructura previa de archivos (sin Cloudinary/S3/uploads
--    ni tabla de archivos). Se define almacenamiento en disco local del
--    backend; ruta_archivo guarda la ruta relativa al proyecto, nunca el
--    binario ni base64 en esta tabla.
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS obras.t_incidencia_evidencia (
    id_evidencia    SERIAL PRIMARY KEY,
    id_incidencia   INTEGER      NOT NULL,
    id_usuario      INTEGER      NULL,
    ruta_archivo    VARCHAR(500) NOT NULL,
    nombre_archivo  VARCHAR(255) NOT NULL,
    tipo_mime       VARCHAR(100),
    tamano_bytes    INTEGER,
    fecha           TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_incidencia_evidencia_incidencia FOREIGN KEY (id_incidencia)
        REFERENCES obras.t_incidencia(id_incidencia) ON DELETE CASCADE,
    CONSTRAINT fk_incidencia_evidencia_usuario FOREIGN KEY (id_usuario)
        REFERENCES obras.t_usuario(id_usuario) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_incidencia_evidencia_incidencia
    ON obras.t_incidencia_evidencia(id_incidencia);

-- ─────────────────────────────────────────────────────────────────────────────
-- 4. PERMISOS CU19
-- ─────────────────────────────────────────────────────────────────────────────
INSERT INTO obras.t_permiso(nombre_permiso)
SELECT p.nombre FROM (VALUES
    ('Visualizar_incidencias'),
    ('Registrar_incidencias'),
    ('Modificar_incidencias'),
    ('Asignar_incidencias'),
    ('Cerrar_incidencias')
) AS p(nombre)
WHERE NOT EXISTS (SELECT 1 FROM obras.t_permiso x WHERE x.nombre_permiso = p.nombre);

-- ADMINISTRADOR_EMPRESA: todos los permisos del módulo.
INSERT INTO obras.t_rol_permiso(id_rol, id_permiso)
SELECT r.id_rol, p.id_permiso
FROM obras.t_rol r CROSS JOIN obras.t_permiso p
WHERE UPPER(r.nombre_rol) = 'ADMINISTRADOR_EMPRESA'
  AND p.nombre_permiso IN (
      'Visualizar_incidencias', 'Registrar_incidencias',
      'Modificar_incidencias', 'Asignar_incidencias', 'Cerrar_incidencias'
  )
ON CONFLICT DO NOTHING;

-- JEFE DE OBRA (Responsable de Proyecto): registra, visualiza, modifica y
-- asigna. Confirmado como nombre real de rol en migration_cu15_proveedores.sql
-- y obra_services.py.
INSERT INTO obras.t_rol_permiso(id_rol, id_permiso)
SELECT r.id_rol, p.id_permiso
FROM obras.t_rol r CROSS JOIN obras.t_permiso p
WHERE UPPER(r.nombre_rol) = 'JEFE DE OBRA'
  AND p.nombre_permiso IN (
      'Visualizar_incidencias', 'Registrar_incidencias',
      'Modificar_incidencias', 'Asignar_incidencias'
  )
ON CONFLICT DO NOTHING;

-- SUPERVISOR: visualiza, apoya en el seguimiento y cierra incidencias
-- resueltas. El nombre exacto de este rol NO pudo confirmarse en el código
-- (los roles son dinámicos, gestionados vía /api/roles). Se intenta con las
-- variantes más probables; si el rol tiene otro nombre, esta sección no
-- inserta nada (no falla) y los permisos deben asignarse manualmente desde
-- la administración de roles.
INSERT INTO obras.t_rol_permiso(id_rol, id_permiso)
SELECT r.id_rol, p.id_permiso
FROM obras.t_rol r CROSS JOIN obras.t_permiso p
WHERE UPPER(r.nombre_rol) IN ('SUPERVISOR', 'SUPERVISOR DE OBRA', 'SUPERVISOR_OBRA')
  AND p.nombre_permiso IN (
      'Visualizar_incidencias', 'Modificar_incidencias', 'Cerrar_incidencias'
  )
ON CONFLICT DO NOTHING;

COMMIT;
