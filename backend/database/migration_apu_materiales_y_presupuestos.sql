-- Apply after migration_estimacion_apu.sql and any legacy APU migration.
-- Apply before seed_estimacion_apu.sql; the seed now targets this schema.
BEGIN;

ALTER TABLE obras.t_analisis_precio_unitario
    ADD COLUMN IF NOT EXISTS codigo VARCHAR(40),
    ADD COLUMN IF NOT EXISTS rendimiento NUMERIC(12,4),
    ADD COLUMN IF NOT EXISTS costo_materiales NUMERIC(14,2) NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS mano_de_obra NUMERIC(10,2) NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS costo_directo NUMERIC(14,2) NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS porcentaje_utilidad NUMERIC(7,3) NOT NULL DEFAULT 10,
    ADD COLUMN IF NOT EXISTS precio_unitario_final NUMERIC(14,2) NOT NULL DEFAULT 0;

CREATE SEQUENCE IF NOT EXISTS obras.seq_apu_codigo;

UPDATE obras.t_analisis_precio_unitario
SET codigo = 'APU-' || id_empresa::text || '-' || LPAD(id_analisis_precio_unitario::text, 5, '0')
WHERE codigo IS NULL OR BTRIM(codigo) = '';

CREATE UNIQUE INDEX IF NOT EXISTS uq_apu_empresa_codigo
    ON obras.t_analisis_precio_unitario(id_empresa, codigo);

ALTER TABLE obras.t_analisis_precio_unitario
    DROP CONSTRAINT IF EXISTS chk_apu_direct_labor_nonnegative,
    DROP CONSTRAINT IF EXISTS chk_apu_margin_nonnegative,
    DROP CONSTRAINT IF EXISTS chk_apu_yield_nonnegative,
    ADD CONSTRAINT chk_apu_direct_labor_nonnegative CHECK (mano_de_obra >= 0),
    ADD CONSTRAINT chk_apu_margin_nonnegative CHECK (porcentaje_utilidad >= 0),
    ADD CONSTRAINT chk_apu_yield_nonnegative CHECK (rendimiento IS NULL OR rendimiento >= 0);

CREATE TABLE IF NOT EXISTS obras.t_apu_detalle_mano_obra_archivo (
    id_archivo BIGSERIAL PRIMARY KEY,
    id_detalle_origen INTEGER NOT NULL UNIQUE,
    registro JSONB NOT NULL,
    archivado_en TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO obras.t_apu_detalle_mano_obra_archivo(id_detalle_origen, registro)
SELECT i.id_analisis_precio_unitario_insumo, to_jsonb(i)
FROM obras.t_analisi_precio_unitario_insumo i
WHERE i.tipo_insumo = 'MANO_OBRA'
   OR (i.tipo_insumo = 'OTRO' AND i.nombre ~* '^(mano de obra|cuadrilla|pe[oó]n|alba[nñ]il|pintor|carpintero|colocador|instalador|pulidor|tablaroquera|fierrero|ayudante|ebanista|especialista)')
ON CONFLICT (id_detalle_origen) DO NOTHING;

UPDATE obras.t_analisis_precio_unitario a
SET mano_de_obra = COALESCE(a.mano_de_obra, 0) + COALESCE(l.costo, 0)
FROM (
    SELECT i.id_analisis_precio_unitario,
           SUM(ROUND(i.cantidad * i.precio_unitario, 2)) AS costo
    FROM obras.t_analisi_precio_unitario_insumo i
    WHERE i.tipo_insumo = 'MANO_OBRA'
       OR (i.tipo_insumo = 'OTRO' AND i.nombre ~* '^(mano de obra|cuadrilla|pe[oó]n|alba[nñ]il|pintor|carpintero|colocador|instalador|pulidor|tablaroquera|fierrero|ayudante|ebanista|especialista)')
    GROUP BY i.id_analisis_precio_unitario
) l
WHERE a.id_analisis_precio_unitario = l.id_analisis_precio_unitario;

DELETE FROM obras.t_analisi_precio_unitario_insumo i
WHERE i.tipo_insumo = 'MANO_OBRA'
   OR (i.tipo_insumo = 'OTRO' AND i.nombre ~* '^(mano de obra|cuadrilla|pe[oó]n|alba[nñ]il|pintor|carpintero|colocador|instalador|pulidor|tablaroquera|fierrero|ayudante|ebanista|especialista)');

DO $materiales$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM obras.t_categoria_material WHERE id_categoria = 1) THEN
        RAISE EXCEPTION 'Se requiere la categoría obras.t_categoria_material id_categoria=1 para migrar los materiales genéricos.';
    END IF;
END
$materiales$;

WITH faltantes AS (
    SELECT MIN(i.id_analisis_precio_unitario_insumo) AS primer_detalle,
           i.id_empresa,
           MIN(BTRIM(i.nombre)) AS nombre,
           i.id_unidad_medida,
           MIN(i.precio_unitario) AS precio
    FROM obras.t_analisi_precio_unitario_insumo i
    WHERE i.id_material IS NULL
    GROUP BY i.id_empresa, LOWER(BTRIM(i.nombre)), i.id_unidad_medida
)
INSERT INTO obras.t_material
        (codigo, nombre_material, descripcion, id_categoria, id_unidad_medida, precio, estado, id_empresa)
    SELECT 'APU-MIG-' || f.id_empresa::text || '-' || f.primer_detalle::text,
           f.nombre,
           'Material catalogado automáticamente desde un detalle APU existente.',
           1,
           f.id_unidad_medida,
           f.precio,
           'ACTIVO',
           f.id_empresa
    FROM faltantes f
    WHERE NOT EXISTS (
        SELECT 1 FROM obras.t_material m
        WHERE m.id_empresa = f.id_empresa
          AND m.id_unidad_medida = f.id_unidad_medida
          AND LOWER(BTRIM(m.nombre_material)) = LOWER(f.nombre)
    );

UPDATE obras.t_material m
SET id_categoria = COALESCE(
    CASE
        WHEN m.nombre_material ~* '(arena|piedra|concreto|agua|grava)' THEN
            (SELECT MIN(c.id_categoria) FROM obras.t_categoria_material c WHERE c.nombre ILIKE '%Agregad%')
        WHEN m.nombre_material ~* '(cemento|mortero|yeso)' THEN
            (SELECT MIN(c.id_categoria) FROM obras.t_categoria_material c WHERE (c.nombre ILIKE '%Cemento%' OR c.nombre ILIKE '%Aglomerante%') AND c.nombre NOT ILIKE '%Test%')
        WHEN m.nombre_material ~* '(varilla|alambr|acero|clavo|tornill|malla|herrajes)' THEN
            (SELECT MIN(c.id_categoria) FROM obras.t_categoria_material c WHERE c.nombre ILIKE '%Acero%' OR c.nombre ILIKE '%Metal%')
        WHEN m.nombre_material ~* '(madera|puerta|vigueta|bovedilla|carpinter)' THEN
            (SELECT MIN(c.id_categoria) FROM obras.t_categoria_material c WHERE c.nombre ILIKE '%Madera%' OR c.nombre ILIKE '%Carpinter%')
        WHEN m.nombre_material ~* '(bloque|ladrillo)' THEN
            (SELECT MIN(c.id_categoria) FROM obras.t_categoria_material c WHERE c.nombre ILIKE '%Mamposter%')
        ELSE
            (SELECT MIN(c.id_categoria) FROM obras.t_categoria_material c WHERE c.nombre ILIKE '%Acabado%' OR c.nombre ILIKE '%Revestimiento%' OR c.nombre ILIKE '%Piso%')
    END,
    1
)
WHERE m.codigo LIKE 'APU-MIG-%';

UPDATE obras.t_analisi_precio_unitario_insumo i
SET id_material = (
    SELECT MIN(m.id_material)
    FROM obras.t_material m
    WHERE m.id_empresa = i.id_empresa
      AND m.id_unidad_medida = i.id_unidad_medida
      AND LOWER(BTRIM(m.nombre_material)) = LOWER(BTRIM(i.nombre))
)
WHERE i.id_material IS NULL;

ALTER TABLE obras.t_analisi_precio_unitario_insumo
    DROP CONSTRAINT IF EXISTS chk_apu_insumo_tipo,
    DROP CONSTRAINT IF EXISTS chk_apu_insumo_material_tipo,
    DROP CONSTRAINT IF EXISTS chk_apu_insumo_mano_tipo,
    DROP CONSTRAINT IF EXISTS chk_apu_detalle_solo_material,
    DROP CONSTRAINT IF EXISTS fk_apu_insumo_mano_obra,
    DROP CONSTRAINT IF EXISTS fk_apu_insumo_material,
    DROP COLUMN IF EXISTS id_mano_obra;

UPDATE obras.t_analisi_precio_unitario_insumo SET tipo_insumo = 'MATERIAL';

ALTER TABLE obras.t_analisi_precio_unitario_insumo
    ALTER COLUMN id_material SET NOT NULL,
    ALTER COLUMN tipo_insumo SET DEFAULT 'MATERIAL',
    ADD CONSTRAINT chk_apu_detalle_solo_material CHECK (tipo_insumo = 'MATERIAL'),
    ADD CONSTRAINT fk_apu_insumo_material FOREIGN KEY (id_material)
        REFERENCES obras.t_material(id_material) ON DELETE RESTRICT;

ALTER TABLE obras.t_analisi_precio_unitario_insumo
    ADD COLUMN IF NOT EXISTS subtotal NUMERIC(14,2)
    GENERATED ALWAYS AS (ROUND(cantidad * precio_unitario, 2)) STORED;

ALTER TABLE obras.t_estimacion
    ADD COLUMN IF NOT EXISTS cliente VARCHAR(200) NOT NULL DEFAULT '';

ALTER TABLE obras.t_estimacion_analisis_precio_unitario
    ADD COLUMN IF NOT EXISTS item_codigo VARCHAR(40),
    ADD COLUMN IF NOT EXISTS precio_unitario NUMERIC(14,2),
    ADD COLUMN IF NOT EXISTS costo_directo_unitario NUMERIC(14,2),
    ADD COLUMN IF NOT EXISTS precio_total NUMERIC(16,2)
    GENERATED ALWAYS AS (ROUND(cantidad * COALESCE(precio_unitario, 0), 2)) STORED;

UPDATE obras.t_analisis_precio_unitario a
SET costo_materiales = COALESCE((
        SELECT SUM(i.subtotal)
        FROM obras.t_analisi_precio_unitario_insumo i
        WHERE i.id_analisis_precio_unitario = a.id_analisis_precio_unitario
    ), 0),
    codigo = COALESCE(a.codigo, 'APU-' || a.id_empresa::text || '-' || LPAD(a.id_analisis_precio_unitario::text, 5, '0'));

UPDATE obras.t_analisis_precio_unitario
SET porcentaje_utilidad = 10
WHERE porcentaje_utilidad IS NULL OR porcentaje_utilidad = 0;

UPDATE obras.t_estimacion_analisis_precio_unitario d
    SET precio_unitario = a.precio_unitario_final,
    costo_directo_unitario = a.costo_directo,
    item_codigo = COALESCE(NULLIF(BTRIM(d.item_codigo), ''), '01.' || LPAD(d.orden::text, 2, '0'))
FROM obras.t_analisis_precio_unitario a
WHERE a.id_analisis_precio_unitario = d.id_analisis_precio_unitario;

ALTER TABLE obras.t_estimacion_analisis_precio_unitario
    ALTER COLUMN item_codigo SET NOT NULL,
    ALTER COLUMN precio_unitario SET NOT NULL,
    ALTER COLUMN costo_directo_unitario SET NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_estimacion_item_codigo
    ON obras.t_estimacion_analisis_precio_unitario(id_estimacion, item_codigo);

UPDATE obras.t_estimacion SET factor_indirectos = 0, factor_utilidad = 0;

CREATE OR REPLACE FUNCTION obras.fn_sync_apu_precio()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.codigo IS NULL OR BTRIM(NEW.codigo) = '' THEN
        NEW.codigo := 'APU-' || NEW.id_empresa::text || '-' || LPAD(nextval('obras.seq_apu_codigo')::text, 5, '0');
    END IF;
    NEW.costo_materiales := COALESCE((
        SELECT SUM(i.subtotal)
        FROM obras.t_analisi_precio_unitario_insumo i
        WHERE i.id_analisis_precio_unitario = NEW.id_analisis_precio_unitario
    ), 0);
    NEW.mano_de_obra := COALESCE(NEW.mano_de_obra, 0);
    NEW.porcentaje_utilidad := COALESCE(NEW.porcentaje_utilidad, 0);
    NEW.costo_directo := ROUND(NEW.costo_materiales + NEW.mano_de_obra, 2);
    NEW.precio_unitario_final := ROUND(NEW.costo_directo * (1 + NEW.porcentaje_utilidad / 100), 2);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tg_sync_apu_precio ON obras.t_analisis_precio_unitario;
CREATE TRIGGER tg_sync_apu_precio
BEFORE INSERT OR UPDATE OF codigo, id_empresa, costo_materiales, mano_de_obra, porcentaje_utilidad
ON obras.t_analisis_precio_unitario
FOR EACH ROW EXECUTE FUNCTION obras.fn_sync_apu_precio();

CREATE OR REPLACE FUNCTION obras.fn_recalcular_apu_materiales()
RETURNS TRIGGER AS $$
DECLARE v_apu INTEGER;
BEGIN
    IF TG_OP = 'DELETE' THEN
        v_apu := OLD.id_analisis_precio_unitario;
    ELSE
        v_apu := NEW.id_analisis_precio_unitario;
    END IF;
    UPDATE obras.t_analisis_precio_unitario a
    SET costo_materiales = COALESCE((
        SELECT SUM(i.subtotal)
        FROM obras.t_analisi_precio_unitario_insumo i
        WHERE i.id_analisis_precio_unitario = v_apu
    ), 0)
    WHERE a.id_analisis_precio_unitario = v_apu;
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tg_recalcular_apu_materiales ON obras.t_analisi_precio_unitario_insumo;
CREATE TRIGGER tg_recalcular_apu_materiales
AFTER INSERT OR UPDATE OR DELETE ON obras.t_analisi_precio_unitario_insumo
FOR EACH ROW EXECUTE FUNCTION obras.fn_recalcular_apu_materiales();

CREATE OR REPLACE FUNCTION obras.fn_snapshot_precio_partida()
RETURNS TRIGGER AS $$
DECLARE v_precio NUMERIC; v_directo NUMERIC;
BEGIN
    IF NEW.precio_unitario IS NULL OR NEW.costo_directo_unitario IS NULL THEN
        SELECT a.precio_unitario_final, a.costo_directo INTO v_precio, v_directo
        FROM obras.t_analisis_precio_unitario a
        JOIN obras.t_estimacion e ON e.id_empresa = a.id_empresa
        WHERE e.id_estimacion = NEW.id_estimacion
          AND a.id_analisis_precio_unitario = NEW.id_analisis_precio_unitario;
        NEW.precio_unitario := COALESCE(NEW.precio_unitario, v_precio, 0);
        NEW.costo_directo_unitario := COALESCE(NEW.costo_directo_unitario, v_directo, 0);
    END IF;
    IF NEW.item_codigo IS NULL OR BTRIM(NEW.item_codigo) = '' THEN
        NEW.item_codigo := '01.' || LPAD(NEW.orden::text, 2, '0');
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tg_snapshot_precio_partida ON obras.t_estimacion_analisis_precio_unitario;
CREATE TRIGGER tg_snapshot_precio_partida
BEFORE INSERT OR UPDATE OF precio_unitario, costo_directo_unitario, item_codigo, orden
ON obras.t_estimacion_analisis_precio_unitario
FOR EACH ROW EXECUTE FUNCTION obras.fn_snapshot_precio_partida();

CREATE OR REPLACE FUNCTION obras.fn_recalcular_monto_estimacion()
RETURNS TRIGGER AS $$
DECLARE v_estimacion INTEGER;
BEGIN
    IF TG_OP = 'DELETE' THEN
        v_estimacion := OLD.id_estimacion;
    ELSE
        v_estimacion := NEW.id_estimacion;
    END IF;
    UPDATE obras.t_estimacion e
    SET monto_total = COALESCE((
        SELECT SUM(d.precio_total)
        FROM obras.t_estimacion_analisis_precio_unitario d
        WHERE d.id_estimacion = v_estimacion
    ), 0)
    WHERE e.id_estimacion = v_estimacion;
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tg_recalcular_monto_estimacion ON obras.t_estimacion_analisis_precio_unitario;
CREATE TRIGGER tg_recalcular_monto_estimacion
AFTER INSERT OR UPDATE OR DELETE ON obras.t_estimacion_analisis_precio_unitario
FOR EACH ROW EXECUTE FUNCTION obras.fn_recalcular_monto_estimacion();

CREATE OR REPLACE FUNCTION obras.fn_calcular_analisis_precio_unitario(p_id_analisis_precio_unitario INTEGER, p_id_empresa INTEGER)
RETURNS JSON AS $$
DECLARE v_apu JSON; v_insumos JSON; v_materiales NUMERIC; v_mano_obra NUMERIC; v_directo NUMERIC; v_utilidad NUMERIC; v_final NUMERIC;
BEGIN
    SELECT a.costo_materiales, a.mano_de_obra, a.costo_directo,
           ROUND(a.costo_directo * a.porcentaje_utilidad / 100, 2), a.precio_unitario_final
    INTO v_materiales, v_mano_obra, v_directo, v_utilidad, v_final
    FROM obras.t_analisis_precio_unitario a
    WHERE a.id_analisis_precio_unitario = p_id_analisis_precio_unitario AND a.id_empresa = p_id_empresa;
    IF NOT FOUND THEN
        RETURN json_build_object('success', false, 'error', 'La partida no existe o no pertenece a su empresa.');
    END IF;
    SELECT COALESCE(json_agg(json_build_object(
        'id_analisis_precio_unitario_insumo', i.id_analisis_precio_unitario_insumo,
        'id_material', i.id_material, 'nombre', i.nombre,
        'cantidad', i.cantidad, 'precio_unitario', i.precio_unitario,
        'subtotal', i.subtotal, 'id_unidad_medida', i.id_unidad_medida
    ) ORDER BY i.orden, i.id_analisis_precio_unitario_insumo), '[]'::json)
    INTO v_insumos
    FROM obras.t_analisi_precio_unitario_insumo i
    WHERE i.id_analisis_precio_unitario = p_id_analisis_precio_unitario AND i.id_empresa = p_id_empresa;
    SELECT json_build_object(
        'success', true,
        'costo_materiales', v_materiales,
        'mano_de_obra', v_mano_obra,
        'costo_directo', v_directo,
        'porcentaje_utilidad', a.porcentaje_utilidad,
        'utilidad', v_utilidad,
        'precio_unitario_final', v_final,
        'costo_directo_unitario', v_directo,
        'insumos', v_insumos
    ) INTO v_apu
    FROM obras.t_analisis_precio_unitario a
    WHERE a.id_analisis_precio_unitario = p_id_analisis_precio_unitario;
    RETURN v_apu;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION obras.fn_calcular_estimacion(p_id_estimacion INTEGER, p_id_empresa INTEGER)
RETURNS JSON AS $$
DECLARE v_detalle JSON; v_directo NUMERIC; v_utilidad NUMERIC; v_total NUMERIC;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM obras.t_estimacion WHERE id_estimacion = p_id_estimacion AND id_empresa = p_id_empresa) THEN
        RETURN json_build_object('success', false, 'error', 'La estimación no existe o no pertenece a su empresa.');
    END IF;
        SELECT COALESCE(SUM(ROUND(COALESCE(d.costo_directo_unitario, a.costo_directo) * d.cantidad, 2)), 0),
            COALESCE(SUM(ROUND((COALESCE(d.precio_unitario, a.precio_unitario_final) - COALESCE(d.costo_directo_unitario, a.costo_directo)) * d.cantidad, 2)), 0),
           COALESCE(SUM(d.precio_total), 0),
           COALESCE(json_agg(json_build_object(
               'id_analisis_precio_unitario', a.id_analisis_precio_unitario,
               'id_estimacion_analisis_precio_unitario', d.id_estimacion_analisis_precio_unitario,
               'item_codigo', d.item_codigo, 'nombre', a.nombre,
               'unidad', um.abreviatura,
               'costo_directo_unitario', COALESCE(d.costo_directo_unitario, a.costo_directo),
               'costo_unitario', COALESCE(d.precio_unitario, a.precio_unitario_final),
               'cantidad', d.cantidad, 'subtotal', d.precio_total
           ) ORDER BY d.orden), '[]'::json)
    INTO v_directo, v_utilidad, v_total, v_detalle
    FROM obras.t_estimacion_analisis_precio_unitario d
    JOIN obras.t_estimacion e ON e.id_estimacion = d.id_estimacion
    JOIN obras.t_analisis_precio_unitario a ON a.id_analisis_precio_unitario = d.id_analisis_precio_unitario
    JOIN obras.t_unidad_medida um ON um.id_unidad_medida = a.id_unidad_medida
    WHERE d.id_estimacion = p_id_estimacion AND e.id_empresa = p_id_empresa AND a.id_empresa = p_id_empresa;
    RETURN json_build_object(
        'success', true, 'detalle', v_detalle,
        'subtotal_directo', ROUND(v_directo, 2), 'utilidad', ROUND(v_utilidad, 2),
        'monto_total', ROUND(v_total, 2)
    );
END;
$$ LANGUAGE plpgsql;

UPDATE obras.t_analisis_precio_unitario
SET costo_materiales = COALESCE((
    SELECT SUM(i.subtotal)
    FROM obras.t_analisi_precio_unitario_insumo i
    WHERE i.id_analisis_precio_unitario = t_analisis_precio_unitario.id_analisis_precio_unitario
), 0);

UPDATE obras.t_estimacion_analisis_precio_unitario d
SET precio_unitario = a.precio_unitario_final
FROM obras.t_analisis_precio_unitario a
WHERE a.id_analisis_precio_unitario = d.id_analisis_precio_unitario;

UPDATE obras.t_estimacion e
SET monto_total = COALESCE((
    SELECT SUM(d.precio_total)
    FROM obras.t_estimacion_analisis_precio_unitario d
    WHERE d.id_estimacion = e.id_estimacion
), 0);

COMMIT;