-- ============================================================================
-- CU17 - Control de costos y ordenes de cambio
--
-- Prerrequisitos:
--   1. migration_estimacion_apu.sql
--   2. migration_apu_materiales_y_presupuestos.sql
--
-- Incidencia previa de CU16: la BD inspeccionada no tiene el indice
-- idx_apu_obra. Su correccion corresponde a CU16 y no se realiza aqui.
--
-- Esta migracion no modifica datos ni estructuras de CU16. Las estimaciones y
-- sus partidas se usan exclusivamente como linea base historica de solo lectura.
-- ============================================================================

BEGIN;

-- Algunas instalaciones tienen una tabla homonima de un modulo legacy. La
-- estructura CU17 se reconoce por sus columnas y restricciones propias. Una
-- tabla incompatible solo se archiva si esta vacia; nunca se elimina ni se
-- transforma silenciosamente si contiene datos.
DO $cu17_legacy_costo$
DECLARE
    v_es_cu17 BOOLEAN;
    v_tiene_datos BOOLEAN;
    v_nombre_archivo TEXT := 't_costo_ejecutado_legacy';
    v_sufijo INTEGER := 1;
    v_secuencia TEXT;
    v_nombre_secuencia TEXT;
    v_indice RECORD;
    v_nombre_indice TEXT;
BEGIN
    IF to_regclass('obras.t_costo_ejecutado') IS NULL THEN
        RETURN;
    END IF;

    SELECT
        COUNT(*) FILTER (WHERE c.column_name IN (
            'id_costo_ejecutado', 'id_control_costo', 'id_empresa', 'id_obra',
            'id_partida_presupuestaria', 'fecha', 'concepto', 'categoria',
            'cantidad', 'costo_unitario', 'monto', 'documento', 'observacion',
            'estado', 'registrado_por', 'anulado_por', 'anulado_en',
            'motivo_anulacion', 'created_at', 'updated_at'
        )) = 20
        AND BOOL_OR(c.column_name = 'id_costo_ejecutado' AND c.udt_name = 'int8')
        AND EXISTS (
            SELECT 1
            FROM pg_constraint pc
            WHERE pc.conrelid = 'obras.t_costo_ejecutado'::regclass
              AND pc.conname = 'chk_costo_ejecutado_anulacion'
        )
        AND EXISTS (
            SELECT 1
            FROM pg_constraint pc
            WHERE pc.conrelid = 'obras.t_costo_ejecutado'::regclass
              AND pc.conname = 'fk_costo_ejecutado_control'
        )
      INTO v_es_cu17
      FROM information_schema.columns c
     WHERE c.table_schema = 'obras'
       AND c.table_name = 't_costo_ejecutado';

    IF v_es_cu17 THEN
        RETURN;
    END IF;

    EXECUTE 'SELECT EXISTS (SELECT 1 FROM obras.t_costo_ejecutado)'
       INTO v_tiene_datos;
    IF v_tiene_datos THEN
        RAISE EXCEPTION
            'Existe obras.t_costo_ejecutado con estructura legacy y datos. Debe archivarse o migrarse manualmente antes de ejecutar CU17.';
    END IF;

    WHILE to_regclass(format('obras.%I', v_nombre_archivo)) IS NOT NULL LOOP
        v_sufijo := v_sufijo + 1;
        v_nombre_archivo := 't_costo_ejecutado_legacy_' || v_sufijo::TEXT;
    END LOOP;

    SELECT pg_get_serial_sequence('obras.t_costo_ejecutado', 'id_costo_ejecutado')
      INTO v_secuencia;

    EXECUTE format(
        'ALTER TABLE obras.t_costo_ejecutado RENAME TO %I',
        v_nombre_archivo
    );

    -- Renombrar la PK libera tambien el nombre de su indice subyacente.
    IF EXISTS (
        SELECT 1
        FROM pg_constraint pc
        WHERE pc.conrelid = format('obras.%I', v_nombre_archivo)::regclass
          AND pc.contype = 'p'
    ) THEN
        EXECUTE format(
            'ALTER TABLE obras.%I RENAME CONSTRAINT %I TO %I',
            v_nombre_archivo,
            (
                SELECT pc.conname
                FROM pg_constraint pc
                WHERE pc.conrelid = format('obras.%I', v_nombre_archivo)::regclass
                  AND pc.contype = 'p'
                LIMIT 1
            ),
            v_nombre_archivo || '_pkey'
        );
    END IF;

    -- Los SERIAL/BIGSERIAL conservan el nombre de su secuencia al renombrar la
    -- tabla. Se renombra para que BIGSERIAL pueda crear la secuencia de CU17.
    IF v_secuencia IS NOT NULL THEN
        v_nombre_secuencia := v_nombre_archivo || '_id_costo_ejecutado_seq';
        WHILE to_regclass(format('obras.%I', v_nombre_secuencia)) IS NOT NULL LOOP
            v_sufijo := v_sufijo + 1;
            v_nombre_secuencia := v_nombre_archivo || '_id_seq_' || v_sufijo::TEXT;
        END LOOP;
        EXECUTE format(
            'ALTER SEQUENCE %s RENAME TO %I',
            v_secuencia,
            v_nombre_secuencia
        );
    END IF;

    -- Liberar nombres de indices legacy que puedan coincidir con CU17.
    FOR v_indice IN
        SELECT indexname
        FROM pg_indexes
        WHERE schemaname = 'obras'
          AND tablename = v_nombre_archivo
          AND indexname IN (
              'idx_costo_ejecutado_control_fecha',
              'idx_costo_ejecutado_partida_estado',
              'idx_costo_ejecutado_empresa_obra'
          )
    LOOP
        v_nombre_indice := LEFT(
            'idx_' || v_nombre_archivo || '_' || v_sufijo::TEXT,
            63
        );
        v_sufijo := v_sufijo + 1;
        EXECUTE format(
            'ALTER INDEX obras.%I RENAME TO %I',
            v_indice.indexname,
            v_nombre_indice
        );
    END LOOP;
END;
$cu17_legacy_costo$;

CREATE TABLE IF NOT EXISTS obras.t_control_costo_obra (
    id_control_costo BIGSERIAL PRIMARY KEY,
    id_empresa INTEGER NOT NULL,
    id_obra INTEGER NOT NULL,
    id_estimacion_base INTEGER NOT NULL,
    version_presupuesto INTEGER NOT NULL,
    moneda VARCHAR(10) NOT NULL,
    estado VARCHAR(10) NOT NULL DEFAULT 'ACTIVO',
    seleccionado_por INTEGER NOT NULL,
    seleccionado_en TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_control_costo_empresa FOREIGN KEY (id_empresa)
        REFERENCES obras.t_empresa(id_empresa) ON DELETE RESTRICT,
    CONSTRAINT fk_control_costo_obra FOREIGN KEY (id_obra)
        REFERENCES obras.t_obra(id_obra) ON DELETE RESTRICT,
    CONSTRAINT fk_control_costo_estimacion FOREIGN KEY (id_estimacion_base)
        REFERENCES obras.t_estimacion(id_estimacion) ON DELETE RESTRICT,
    CONSTRAINT fk_control_costo_usuario FOREIGN KEY (seleccionado_por)
        REFERENCES obras.t_usuario(id_usuario) ON DELETE RESTRICT,
    CONSTRAINT chk_control_costo_estado CHECK (estado IN ('ACTIVO', 'CERRADO')),
    CONSTRAINT chk_control_costo_moneda CHECK (BTRIM(moneda) <> '')
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_control_costo_obra_activo
    ON obras.t_control_costo_obra(id_empresa, id_obra)
    WHERE estado = 'ACTIVO';
CREATE INDEX IF NOT EXISTS idx_control_costo_estimacion
    ON obras.t_control_costo_obra(id_estimacion_base);

CREATE TABLE IF NOT EXISTS obras.t_costo_ejecutado (
    id_costo_ejecutado BIGSERIAL PRIMARY KEY,
    id_control_costo BIGINT NOT NULL,
    id_empresa INTEGER NOT NULL,
    id_obra INTEGER NOT NULL,
    id_partida_presupuestaria INTEGER NOT NULL,
    fecha DATE NOT NULL,
    concepto VARCHAR(250) NOT NULL,
    categoria VARCHAR(20) NOT NULL,
    cantidad NUMERIC(14,4) NOT NULL,
    costo_unitario NUMERIC(16,2) NOT NULL,
    monto NUMERIC(16,2) NOT NULL,
    documento VARCHAR(120),
    observacion TEXT,
    estado VARCHAR(12) NOT NULL DEFAULT 'REGISTRADO',
    registrado_por INTEGER NOT NULL,
    anulado_por INTEGER,
    anulado_en TIMESTAMPTZ,
    motivo_anulacion TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_costo_ejecutado_control FOREIGN KEY (id_control_costo)
        REFERENCES obras.t_control_costo_obra(id_control_costo) ON DELETE RESTRICT,
    CONSTRAINT fk_costo_ejecutado_empresa FOREIGN KEY (id_empresa)
        REFERENCES obras.t_empresa(id_empresa) ON DELETE RESTRICT,
    CONSTRAINT fk_costo_ejecutado_obra FOREIGN KEY (id_obra)
        REFERENCES obras.t_obra(id_obra) ON DELETE RESTRICT,
    CONSTRAINT fk_costo_ejecutado_partida FOREIGN KEY (id_partida_presupuestaria)
        REFERENCES obras.t_estimacion_analisis_precio_unitario(id_estimacion_analisis_precio_unitario) ON DELETE RESTRICT,
    CONSTRAINT fk_costo_ejecutado_registrado_por FOREIGN KEY (registrado_por)
        REFERENCES obras.t_usuario(id_usuario) ON DELETE RESTRICT,
    CONSTRAINT fk_costo_ejecutado_anulado_por FOREIGN KEY (anulado_por)
        REFERENCES obras.t_usuario(id_usuario) ON DELETE RESTRICT,
    CONSTRAINT chk_costo_ejecutado_concepto CHECK (BTRIM(concepto) <> ''),
    CONSTRAINT chk_costo_ejecutado_categoria CHECK (
        categoria IN ('MATERIAL', 'MANO_OBRA', 'EQUIPO', 'SUBCONTRATO', 'OTRO')
    ),
    CONSTRAINT chk_costo_ejecutado_cantidad CHECK (cantidad >= 0),
    CONSTRAINT chk_costo_ejecutado_unitario CHECK (costo_unitario >= 0),
    CONSTRAINT chk_costo_ejecutado_monto CHECK (
        monto >= 0 AND monto = ROUND(cantidad * costo_unitario, 2)
    ),
    CONSTRAINT chk_costo_ejecutado_estado CHECK (estado IN ('REGISTRADO', 'ANULADO')),
    CONSTRAINT chk_costo_ejecutado_anulacion CHECK (
        (estado = 'REGISTRADO' AND anulado_por IS NULL AND anulado_en IS NULL AND motivo_anulacion IS NULL)
        OR
        (estado = 'ANULADO' AND anulado_por IS NOT NULL AND anulado_en IS NOT NULL
         AND motivo_anulacion IS NOT NULL AND BTRIM(motivo_anulacion) <> '')
    )
);

CREATE INDEX IF NOT EXISTS idx_costo_ejecutado_control_fecha
    ON obras.t_costo_ejecutado(id_control_costo, fecha);
CREATE INDEX IF NOT EXISTS idx_costo_ejecutado_partida_estado
    ON obras.t_costo_ejecutado(id_partida_presupuestaria, estado);
CREATE INDEX IF NOT EXISTS idx_costo_ejecutado_empresa_obra
    ON obras.t_costo_ejecutado(id_empresa, id_obra);

CREATE TABLE IF NOT EXISTS obras.t_orden_cambio (
    id_orden_cambio BIGSERIAL PRIMARY KEY,
    codigo VARCHAR(40) NOT NULL,
    id_control_costo BIGINT NOT NULL,
    id_empresa INTEGER NOT NULL,
    id_obra INTEGER NOT NULL,
    id_estimacion_base INTEGER NOT NULL,
    titulo VARCHAR(200) NOT NULL,
    descripcion TEXT,
    justificacion TEXT NOT NULL,
    fecha DATE NOT NULL,
    impacto_costo NUMERIC(16,2) NOT NULL DEFAULT 0,
    impacto_plazo_dias INTEGER NOT NULL DEFAULT 0,
    estado VARCHAR(12) NOT NULL DEFAULT 'PENDIENTE',
    solicitado_por INTEGER NOT NULL,
    decidido_por INTEGER,
    fecha_decision TIMESTAMPTZ,
    motivo_decision TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_orden_cambio_control FOREIGN KEY (id_control_costo)
        REFERENCES obras.t_control_costo_obra(id_control_costo) ON DELETE RESTRICT,
    CONSTRAINT fk_orden_cambio_empresa FOREIGN KEY (id_empresa)
        REFERENCES obras.t_empresa(id_empresa) ON DELETE RESTRICT,
    CONSTRAINT fk_orden_cambio_obra FOREIGN KEY (id_obra)
        REFERENCES obras.t_obra(id_obra) ON DELETE RESTRICT,
    CONSTRAINT fk_orden_cambio_estimacion FOREIGN KEY (id_estimacion_base)
        REFERENCES obras.t_estimacion(id_estimacion) ON DELETE RESTRICT,
    CONSTRAINT fk_orden_cambio_solicitado_por FOREIGN KEY (solicitado_por)
        REFERENCES obras.t_usuario(id_usuario) ON DELETE RESTRICT,
    CONSTRAINT fk_orden_cambio_decidido_por FOREIGN KEY (decidido_por)
        REFERENCES obras.t_usuario(id_usuario) ON DELETE RESTRICT,
    CONSTRAINT uq_orden_cambio_codigo UNIQUE (id_empresa, id_obra, codigo),
    CONSTRAINT chk_orden_cambio_codigo CHECK (BTRIM(codigo) <> ''),
    CONSTRAINT chk_orden_cambio_titulo CHECK (BTRIM(titulo) <> ''),
    CONSTRAINT chk_orden_cambio_justificacion CHECK (BTRIM(justificacion) <> ''),
    CONSTRAINT chk_orden_cambio_estado CHECK (estado IN ('PENDIENTE', 'APROBADA', 'RECHAZADA')),
    CONSTRAINT chk_orden_cambio_decision CHECK (
        (estado = 'PENDIENTE' AND decidido_por IS NULL AND fecha_decision IS NULL AND motivo_decision IS NULL)
        OR
        (estado = 'APROBADA' AND decidido_por IS NOT NULL AND fecha_decision IS NOT NULL)
        OR
        (estado = 'RECHAZADA' AND decidido_por IS NOT NULL AND fecha_decision IS NOT NULL
         AND motivo_decision IS NOT NULL AND BTRIM(motivo_decision) <> '')
    )
);

CREATE INDEX IF NOT EXISTS idx_orden_cambio_control_estado
    ON obras.t_orden_cambio(id_control_costo, estado);
CREATE INDEX IF NOT EXISTS idx_orden_cambio_empresa_obra
    ON obras.t_orden_cambio(id_empresa, id_obra);

CREATE TABLE IF NOT EXISTS obras.t_orden_cambio_detalle (
    id_orden_cambio_detalle BIGSERIAL PRIMARY KEY,
    id_orden_cambio BIGINT NOT NULL,
    id_partida_presupuestaria INTEGER,
    id_analisis_precio_unitario INTEGER,
    tipo_cambio VARCHAR(30) NOT NULL,
    item_codigo_snapshot VARCHAR(40) NOT NULL,
    descripcion_snapshot VARCHAR(250) NOT NULL,
    unidad_snapshot VARCHAR(30) NOT NULL,
    cantidad_anterior NUMERIC(14,3) NOT NULL DEFAULT 0,
    cantidad_delta NUMERIC(14,3) NOT NULL DEFAULT 0,
    cantidad_revisada NUMERIC(14,3) NOT NULL DEFAULT 0,
    costo_anterior NUMERIC(16,2) NOT NULL DEFAULT 0,
    costo_nuevo NUMERIC(16,2) NOT NULL DEFAULT 0,
    impacto_costo NUMERIC(16,2) NOT NULL,
    observacion TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_orden_cambio_detalle_orden FOREIGN KEY (id_orden_cambio)
        REFERENCES obras.t_orden_cambio(id_orden_cambio) ON DELETE CASCADE,
    CONSTRAINT fk_orden_cambio_detalle_partida FOREIGN KEY (id_partida_presupuestaria)
        REFERENCES obras.t_estimacion_analisis_precio_unitario(id_estimacion_analisis_precio_unitario) ON DELETE RESTRICT,
    CONSTRAINT fk_orden_cambio_detalle_apu FOREIGN KEY (id_analisis_precio_unitario)
        REFERENCES obras.t_analisis_precio_unitario(id_analisis_precio_unitario) ON DELETE RESTRICT,
    CONSTRAINT chk_orden_cambio_detalle_tipo CHECK (tipo_cambio IN (
        'AUMENTO_CANTIDAD', 'DISMINUCION_CANTIDAD', 'CAMBIO_COSTO',
        'NUEVA_PARTIDA', 'ELIMINACION_PARTIDA'
    )),
    CONSTRAINT chk_orden_cambio_detalle_snapshot CHECK (
        BTRIM(item_codigo_snapshot) <> '' AND BTRIM(descripcion_snapshot) <> ''
        AND BTRIM(unidad_snapshot) <> ''
    ),
    CONSTRAINT chk_orden_cambio_detalle_cantidades CHECK (
        cantidad_anterior >= 0 AND cantidad_revisada >= 0
    ),
    CONSTRAINT chk_orden_cambio_detalle_costos CHECK (
        costo_anterior >= 0 AND costo_nuevo >= 0
    ),
    CONSTRAINT chk_orden_cambio_detalle_origen CHECK (
        (tipo_cambio = 'NUEVA_PARTIDA' AND id_partida_presupuestaria IS NULL)
        OR
        (tipo_cambio <> 'NUEVA_PARTIDA' AND id_partida_presupuestaria IS NOT NULL)
    )
);

CREATE INDEX IF NOT EXISTS idx_orden_cambio_detalle_orden
    ON obras.t_orden_cambio_detalle(id_orden_cambio);
CREATE INDEX IF NOT EXISTS idx_orden_cambio_detalle_partida
    ON obras.t_orden_cambio_detalle(id_partida_presupuestaria);

CREATE TABLE IF NOT EXISTS obras.t_orden_cambio_historial (
    id_orden_cambio_historial BIGSERIAL PRIMARY KEY,
    id_orden_cambio BIGINT NOT NULL,
    estado_anterior VARCHAR(12),
    estado_nuevo VARCHAR(12) NOT NULL,
    accion VARCHAR(30) NOT NULL,
    comentario TEXT,
    id_usuario INTEGER NOT NULL,
    fecha_evento TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ip_origen VARCHAR(64),
    CONSTRAINT fk_orden_cambio_historial_orden FOREIGN KEY (id_orden_cambio)
        REFERENCES obras.t_orden_cambio(id_orden_cambio) ON DELETE RESTRICT,
    CONSTRAINT fk_orden_cambio_historial_usuario FOREIGN KEY (id_usuario)
        REFERENCES obras.t_usuario(id_usuario) ON DELETE RESTRICT,
    CONSTRAINT chk_orden_cambio_historial_estados CHECK (
        (estado_anterior IS NULL OR estado_anterior IN ('PENDIENTE', 'APROBADA', 'RECHAZADA'))
        AND estado_nuevo IN ('PENDIENTE', 'APROBADA', 'RECHAZADA')
    ),
    CONSTRAINT chk_orden_cambio_historial_accion CHECK (
        accion IN ('CREACION', 'MODIFICACION', 'APROBACION', 'RECHAZO')
    )
);

CREATE INDEX IF NOT EXISTS idx_orden_cambio_historial_orden_fecha
    ON obras.t_orden_cambio_historial(id_orden_cambio, fecha_evento DESC);

CREATE OR REPLACE FUNCTION obras.fn_cu17_actualizar_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at := CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tg_cu17_control_updated_at ON obras.t_control_costo_obra;
CREATE TRIGGER tg_cu17_control_updated_at
    BEFORE UPDATE ON obras.t_control_costo_obra
    FOR EACH ROW EXECUTE FUNCTION obras.fn_cu17_actualizar_updated_at();

CREATE OR REPLACE FUNCTION obras.fn_cu17_linea_base_identidad_inmutable()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.id_empresa IS DISTINCT FROM OLD.id_empresa
       OR NEW.id_obra IS DISTINCT FROM OLD.id_obra
       OR NEW.id_estimacion_base IS DISTINCT FROM OLD.id_estimacion_base THEN
        RAISE EXCEPTION
            'La empresa, obra y estimacion base no pueden modificarse despues de crear la linea base.';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tg_cu17_linea_base_identidad_inmutable
    ON obras.t_control_costo_obra;
CREATE TRIGGER tg_cu17_linea_base_identidad_inmutable
    BEFORE UPDATE OF id_empresa, id_obra, id_estimacion_base
    ON obras.t_control_costo_obra
    FOR EACH ROW EXECUTE FUNCTION obras.fn_cu17_linea_base_identidad_inmutable();

DROP TRIGGER IF EXISTS tg_cu17_costo_updated_at ON obras.t_costo_ejecutado;
CREATE TRIGGER tg_cu17_costo_updated_at
    BEFORE UPDATE ON obras.t_costo_ejecutado
    FOR EACH ROW EXECUTE FUNCTION obras.fn_cu17_actualizar_updated_at();

DROP TRIGGER IF EXISTS tg_cu17_orden_updated_at ON obras.t_orden_cambio;
CREATE TRIGGER tg_cu17_orden_updated_at
    BEFORE UPDATE ON obras.t_orden_cambio
    FOR EACH ROW EXECUTE FUNCTION obras.fn_cu17_actualizar_updated_at();

CREATE OR REPLACE FUNCTION obras.fn_cu17_impedir_borrado_costo()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Los costos ejecutados no se eliminan; deben anularse.';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tg_cu17_impedir_borrado_costo ON obras.t_costo_ejecutado;
CREATE TRIGGER tg_cu17_impedir_borrado_costo
    BEFORE DELETE ON obras.t_costo_ejecutado
    FOR EACH ROW EXECUTE FUNCTION obras.fn_cu17_impedir_borrado_costo();

CREATE OR REPLACE FUNCTION obras.fn_cu17_orden_solo_pendiente()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.estado <> 'PENDIENTE' THEN
        RAISE EXCEPTION 'Solo una orden PENDIENTE puede modificarse.';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tg_cu17_orden_solo_pendiente ON obras.t_orden_cambio;
CREATE TRIGGER tg_cu17_orden_solo_pendiente
    BEFORE UPDATE ON obras.t_orden_cambio
    FOR EACH ROW EXECUTE FUNCTION obras.fn_cu17_orden_solo_pendiente();

CREATE OR REPLACE FUNCTION obras.fn_cu17_detalle_solo_pendiente()
RETURNS TRIGGER AS $$
DECLARE
    v_orden BIGINT;
    v_estado VARCHAR(12);
BEGIN
    v_orden := CASE WHEN TG_OP = 'DELETE' THEN OLD.id_orden_cambio ELSE NEW.id_orden_cambio END;
    SELECT estado INTO v_estado
    FROM obras.t_orden_cambio
    WHERE id_orden_cambio = v_orden;
    IF v_estado IS DISTINCT FROM 'PENDIENTE' THEN
        RAISE EXCEPTION 'Los detalles solo pueden cambiar mientras la orden esta PENDIENTE.';
    END IF;
    RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tg_cu17_detalle_solo_pendiente ON obras.t_orden_cambio_detalle;
CREATE TRIGGER tg_cu17_detalle_solo_pendiente
    BEFORE INSERT OR UPDATE OR DELETE ON obras.t_orden_cambio_detalle
    FOR EACH ROW EXECUTE FUNCTION obras.fn_cu17_detalle_solo_pendiente();

CREATE OR REPLACE FUNCTION obras.fn_cu17_validar_linea_base()
RETURNS TRIGGER AS $$
DECLARE
    v_version INTEGER;
    v_moneda VARCHAR(10);
BEGIN
    SELECT e.version, o.moneda
      INTO v_version, v_moneda
      FROM obras.t_estimacion e
      JOIN obras.t_obra o ON o.id_obra = e.id_obra
     WHERE e.id_estimacion = NEW.id_estimacion_base
       AND e.id_obra = NEW.id_obra
       AND e.id_empresa = NEW.id_empresa
       AND o.id_empresa = NEW.id_empresa
       AND e.estado = 'APROBADA'
       AND o.moneda IS NOT NULL
       AND BTRIM(o.moneda) <> '';

    IF NOT FOUND THEN
        RAISE EXCEPTION 'La linea base debe ser un presupuesto APROBADO de la misma obra y empresa, con moneda valida.';
    END IF;

    NEW.version_presupuesto := v_version;
    NEW.moneda := v_moneda;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tg_cu17_validar_linea_base ON obras.t_control_costo_obra;
CREATE TRIGGER tg_cu17_validar_linea_base
    BEFORE INSERT OR UPDATE OF id_empresa, id_obra, id_estimacion_base
    ON obras.t_control_costo_obra
    FOR EACH ROW EXECUTE FUNCTION obras.fn_cu17_validar_linea_base();

CREATE OR REPLACE FUNCTION obras.fn_cu17_validar_costo()
RETURNS TRIGGER AS $$
DECLARE
    v_empresa INTEGER;
    v_obra INTEGER;
    v_estimacion INTEGER;
    v_estado VARCHAR(10);
BEGIN
    SELECT id_empresa, id_obra, id_estimacion_base, estado
      INTO v_empresa, v_obra, v_estimacion, v_estado
      FROM obras.t_control_costo_obra
     WHERE id_control_costo = NEW.id_control_costo;

    IF NOT FOUND OR v_estado <> 'ACTIVO' THEN
        RAISE EXCEPTION 'La linea base no existe o no esta activa.';
    END IF;
    IF NEW.id_empresa <> v_empresa OR NEW.id_obra <> v_obra THEN
        RAISE EXCEPTION 'El costo no pertenece a la empresa y obra de su linea base.';
    END IF;
    IF NOT EXISTS (
        SELECT 1
          FROM obras.t_estimacion_analisis_precio_unitario d
         WHERE d.id_estimacion_analisis_precio_unitario = NEW.id_partida_presupuestaria
           AND d.id_estimacion = v_estimacion
    ) THEN
        RAISE EXCEPTION 'La partida no pertenece exactamente a la estimacion base.';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tg_cu17_validar_costo ON obras.t_costo_ejecutado;
CREATE TRIGGER tg_cu17_validar_costo
    BEFORE INSERT OR UPDATE OF id_control_costo, id_empresa, id_obra, id_partida_presupuestaria
    ON obras.t_costo_ejecutado
    FOR EACH ROW EXECUTE FUNCTION obras.fn_cu17_validar_costo();

CREATE OR REPLACE FUNCTION obras.fn_cu17_validar_orden()
RETURNS TRIGGER AS $$
DECLARE
    v_empresa INTEGER;
    v_obra INTEGER;
    v_estimacion INTEGER;
BEGIN
    SELECT id_empresa, id_obra, id_estimacion_base
      INTO v_empresa, v_obra, v_estimacion
      FROM obras.t_control_costo_obra
     WHERE id_control_costo = NEW.id_control_costo;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'La linea base indicada no existe.';
    END IF;
    IF NEW.id_empresa <> v_empresa OR NEW.id_obra <> v_obra
       OR NEW.id_estimacion_base <> v_estimacion THEN
        RAISE EXCEPTION 'La orden no coincide con la empresa, obra y estimacion de su linea base.';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tg_cu17_validar_orden ON obras.t_orden_cambio;
CREATE TRIGGER tg_cu17_validar_orden
    BEFORE INSERT OR UPDATE OF id_control_costo, id_empresa, id_obra, id_estimacion_base
    ON obras.t_orden_cambio
    FOR EACH ROW EXECUTE FUNCTION obras.fn_cu17_validar_orden();

CREATE OR REPLACE FUNCTION obras.fn_cu17_validar_detalle_orden()
RETURNS TRIGGER AS $$
DECLARE
    v_estimacion INTEGER;
    v_empresa INTEGER;
    v_obra INTEGER;
BEGIN
    SELECT id_estimacion_base, id_empresa, id_obra
      INTO v_estimacion, v_empresa, v_obra
      FROM obras.t_orden_cambio
     WHERE id_orden_cambio = NEW.id_orden_cambio;

    IF NEW.id_partida_presupuestaria IS NOT NULL AND NOT EXISTS (
        SELECT 1
          FROM obras.t_estimacion_analisis_precio_unitario d
         WHERE d.id_estimacion_analisis_precio_unitario = NEW.id_partida_presupuestaria
           AND d.id_estimacion = v_estimacion
    ) THEN
        RAISE EXCEPTION 'La partida del cambio no pertenece a la estimacion base.';
    END IF;

    IF NEW.id_analisis_precio_unitario IS NOT NULL AND NOT EXISTS (
        SELECT 1
          FROM obras.t_analisis_precio_unitario a
         WHERE a.id_analisis_precio_unitario = NEW.id_analisis_precio_unitario
           AND a.id_empresa = v_empresa
           AND (a.id_obra IS NULL OR a.id_obra = v_obra)
    ) THEN
        RAISE EXCEPTION 'El APU no pertenece a la empresa o a la obra de la orden.';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tg_cu17_validar_detalle_orden ON obras.t_orden_cambio_detalle;
CREATE TRIGGER tg_cu17_validar_detalle_orden
    BEFORE INSERT OR UPDATE ON obras.t_orden_cambio_detalle
    FOR EACH ROW EXECUTE FUNCTION obras.fn_cu17_validar_detalle_orden();

CREATE OR REPLACE FUNCTION obras.fn_cu17_historial_append_only()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'El historial de ordenes de cambio es inmutable.';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tg_cu17_historial_append_only ON obras.t_orden_cambio_historial;
CREATE TRIGGER tg_cu17_historial_append_only
    BEFORE UPDATE OR DELETE ON obras.t_orden_cambio_historial
    FOR EACH ROW EXECUTE FUNCTION obras.fn_cu17_historial_append_only();

INSERT INTO obras.t_permiso(nombre_permiso)
SELECT p.nombre
FROM (VALUES
    ('Visualizar_control_costos'),
    ('Registrar_costos_ejecutados'),
    ('Anular_costos_ejecutados'),
    ('Registrar_ordenes_cambio'),
    ('Modificar_ordenes_cambio'),
    ('Aprobar_ordenes_cambio')
) AS p(nombre)
WHERE NOT EXISTS (
    SELECT 1 FROM obras.t_permiso actual WHERE actual.nombre_permiso = p.nombre
);

-- Se asignan por nombre, nunca por IDs fijos. ADMINISTRADOR global omite esta
-- tabla por la regla existente en security.py. Se contemplan los nombres de rol
-- que existen actualmente en el proyecto.
INSERT INTO obras.t_rol_permiso(id_rol, id_permiso)
SELECT r.id_rol, p.id_permiso
FROM obras.t_rol r
CROSS JOIN obras.t_permiso p
WHERE UPPER(REPLACE(BTRIM(r.nombre_rol), '_', ' ')) IN (
        'ADMINISTRADOR EMPRESA', 'JEFE DE OBRA'
    )
  AND p.nombre_permiso IN (
        'Visualizar_control_costos',
        'Registrar_costos_ejecutados',
        'Anular_costos_ejecutados',
        'Registrar_ordenes_cambio',
        'Modificar_ordenes_cambio',
        'Aprobar_ordenes_cambio'
    )
ON CONFLICT DO NOTHING;

COMMIT;
