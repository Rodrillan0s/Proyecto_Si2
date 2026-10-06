-- ============================================================================
-- MIGRACIÓN CU19 (ampliación): ubicación, tiempos de atención y relación
-- Incidencia <-> Orden de Trabajo (M:N).
-- Requiere haber ejecutado antes migration_cu19_incidencias.sql.
-- Incremental y segura para re-ejecución (no usa DROP TABLE ni borra datos).
-- NO modifica obras.t_orden_trabajo ni ninguna tabla de otros casos de uso.
-- ============================================================================
BEGIN;

-- BD compartida: si alguna tabla está bloqueada por otra sesión, abortar en
-- lugar de quedar esperando (y bloquear a otros) indefinidamente.
SET LOCAL lock_timeout = '5s';

-- ─────────────────────────────────────────────────────────────────────────────
-- 1. NUEVAS COLUMNAS EN t_incidencia
-- ─────────────────────────────────────────────────────────────────────────────
ALTER TABLE obras.t_incidencia ADD COLUMN IF NOT EXISTS ubicacion             VARCHAR(255) NULL;
ALTER TABLE obras.t_incidencia ADD COLUMN IF NOT EXISTS fecha_inicio_atencion TIMESTAMPTZ  NULL;
ALTER TABLE obras.t_incidencia ADD COLUMN IF NOT EXISTS fecha_fin_atencion    TIMESTAMPTZ  NULL;

-- Relleno de incidencias ya avanzadas antes de esta migración: se toman las
-- fechas reales del historial (t_incidencia_seguimiento). Si no hubiera
-- historial se usa la mejor aproximación disponible (created_at/updated_at).
-- El trigger CU19 de updated_at se desactiva solo durante el relleno para no
-- alterar updated_at de registros existentes (se reactiva a continuación).
ALTER TABLE obras.t_incidencia DISABLE TRIGGER tg_cu19_actualizar_incidencia;

UPDATE obras.t_incidencia i
SET fecha_inicio_atencion = COALESCE(
        (SELECT MIN(s.fecha) FROM obras.t_incidencia_seguimiento s
         WHERE s.id_incidencia = i.id_incidencia AND s.estado_nuevo = 'EN_PROCESO'
           AND s.estado_anterior IS DISTINCT FROM 'EN_PROCESO'),
        i.created_at)
WHERE i.estado IN ('EN_PROCESO', 'RESUELTA', 'CERRADA')
  AND i.fecha_inicio_atencion IS NULL;

UPDATE obras.t_incidencia i
SET fecha_fin_atencion = GREATEST(
        i.fecha_inicio_atencion,
        COALESCE(
            (SELECT MIN(s.fecha) FROM obras.t_incidencia_seguimiento s
             WHERE s.id_incidencia = i.id_incidencia AND s.estado_nuevo = 'RESUELTA'
               AND s.estado_anterior IS DISTINCT FROM 'RESUELTA'),
            i.updated_at))
WHERE i.estado IN ('RESUELTA', 'CERRADA')
  AND i.fecha_fin_atencion IS NULL;

ALTER TABLE obras.t_incidencia ENABLE TRIGGER tg_cu19_actualizar_incidencia;

DO $$
BEGIN
    -- fin nunca antes que inicio, y no puede existir fin sin inicio.
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_incidencia_fechas_atencion') THEN
        ALTER TABLE obras.t_incidencia ADD CONSTRAINT chk_incidencia_fechas_atencion CHECK (
            fecha_fin_atencion IS NULL
            OR (fecha_inicio_atencion IS NOT NULL AND fecha_fin_atencion >= fecha_inicio_atencion)
        );
    END IF;

    -- Coherencia fechas <-> estado:
    --   ABIERTA/ASIGNADA: sin fechas; EN_PROCESO: solo inicio;
    --   RESUELTA/CERRADA: inicio y fin.
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_incidencia_fechas_estado') THEN
        ALTER TABLE obras.t_incidencia ADD CONSTRAINT chk_incidencia_fechas_estado CHECK (
            (estado IN ('ABIERTA', 'ASIGNADA')
                AND fecha_inicio_atencion IS NULL AND fecha_fin_atencion IS NULL)
            OR (estado = 'EN_PROCESO'
                AND fecha_inicio_atencion IS NOT NULL AND fecha_fin_atencion IS NULL)
            OR (estado IN ('RESUELTA', 'CERRADA')
                AND fecha_inicio_atencion IS NOT NULL AND fecha_fin_atencion IS NOT NULL)
        );
    END IF;
END $$;

-- ─────────────────────────────────────────────────────────────────────────────
-- 2. RELACIÓN M:N obras.t_incidencia_orden_trabajo
--    Una incidencia puede afectar a varias OT y una OT puede estar afectada
--    por varias incidencias. Solo guarda las claves (más auditoría mínima);
--    los datos de la OT se leen siempre de obras.t_orden_trabajo.
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS obras.t_incidencia_orden_trabajo (
    id_incidencia   INTEGER     NOT NULL,
    orden_nro       INTEGER     NOT NULL,
    id_usuario      INTEGER     NULL,
    fecha_registro  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_incidencia_orden_trabajo PRIMARY KEY (id_incidencia, orden_nro),
    CONSTRAINT fk_incidencia_ot_incidencia FOREIGN KEY (id_incidencia)
        REFERENCES obras.t_incidencia(id_incidencia) ON DELETE CASCADE,
    -- CASCADE (no RESTRICT) para no bloquear la eliminación de OT que realiza
    -- el módulo de Órdenes de Trabajo.
    CONSTRAINT fk_incidencia_ot_orden FOREIGN KEY (orden_nro)
        REFERENCES obras.t_orden_trabajo(orden_nro) ON DELETE CASCADE,
    CONSTRAINT fk_incidencia_ot_usuario FOREIGN KEY (id_usuario)
        REFERENCES obras.t_usuario(id_usuario) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_incidencia_ot_orden ON obras.t_incidencia_orden_trabajo(orden_nro);

-- Defensa en profundidad (además de la validación del backend): la OT debe
-- pertenecer a la MISMA obra que la incidencia. Al ser la misma obra, también
-- es el mismo tenant (la empresa se deriva de t_obra.id_empresa).
CREATE OR REPLACE FUNCTION obras.fn_validar_incidencia_ot_cu19()
RETURNS TRIGGER AS $$
DECLARE
    v_obra_incidencia INTEGER;
    v_obra_orden      INTEGER;
BEGIN
    SELECT id_obra INTO v_obra_incidencia FROM obras.t_incidencia WHERE id_incidencia = NEW.id_incidencia;
    SELECT id_obra INTO v_obra_orden      FROM obras.t_orden_trabajo WHERE orden_nro = NEW.orden_nro;
    IF v_obra_incidencia IS NULL OR v_obra_orden IS NULL OR v_obra_incidencia <> v_obra_orden THEN
        RAISE EXCEPTION 'La orden de trabajo % no pertenece a la obra de la incidencia %.',
            NEW.orden_nro, NEW.id_incidencia;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tg_cu19_validar_incidencia_ot ON obras.t_incidencia_orden_trabajo;
CREATE TRIGGER tg_cu19_validar_incidencia_ot
    BEFORE INSERT OR UPDATE ON obras.t_incidencia_orden_trabajo
    FOR EACH ROW EXECUTE FUNCTION obras.fn_validar_incidencia_ot_cu19();

-- Nota de permisos: NO se crean permisos nuevos. Seleccionar las OT afectadas
-- reutiliza 'Asignar_incidencias' (mismo actor que asigna el responsable:
-- Jefe de Obra / Administrador de empresa) y consultarlas 'Visualizar_incidencias'.

COMMIT;
