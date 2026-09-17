-- ============================================================================
-- OBRATEC - SEED de estimación / APU (Bloques 1, 2 y 3) para empresa demo (1)
-- Re-ejecutable: crea unidades, materiales, cuadrillas, APUs e insumos de
-- manera idempotente y actualiza las funciones de cálculo a redondeo por línea:
--     costo APU  = SUM(ROUND(cantidad * precio_unitario, 2))
-- Ejecutar con: python -c "... psycopg2 ... execute(open(sql).read())"
-- ============================================================================
BEGIN;

-- ============================================================================
-- 1. FUNCIONES DE CÁLCULO (redondeo por línea)
-- ============================================================================
CREATE OR REPLACE FUNCTION obras.fn_calcular_analisis_precio_unitario(p_id_analisis_precio_unitario INTEGER, p_id_empresa INTEGER)
RETURNS json AS $$
DECLARE v_apu json; v_insumos json; v_total numeric;
BEGIN
    SELECT json_build_object('id_analisis_precio_unitario', a.id_analisis_precio_unitario, 'nombre', a.nombre, 'descripcion', a.descripcion,
        'id_unidad_medida', a.id_unidad_medida, 'tipo_analisis_precio_unitario', a.tipo_analisis_precio_unitario, 'calidad', a.calidad)
    INTO v_apu FROM obras.t_analisis_precio_unitario a WHERE a.id_analisis_precio_unitario = p_id_analisis_precio_unitario AND a.id_empresa = p_id_empresa;
    IF v_apu IS NULL THEN RETURN json_build_object('success', false, 'error', 'La partida no existe o no pertenece a su empresa.'); END IF;
    SELECT COALESCE(SUM(ROUND(i.cantidad * i.precio_unitario, 2)), 0), COALESCE(json_agg(json_build_object('id', i.id_analisis_precio_unitario_insumo, 'tipo_insumo', i.tipo_insumo, 'nombre', i.nombre, 'cantidad', i.cantidad, 'precio_unitario', i.precio_unitario, 'total', ROUND(i.cantidad * i.precio_unitario, 2), 'id_unidad_medida', i.id_unidad_medida) ORDER BY i.orden, i.id_analisis_precio_unitario_insumo), '[]'::json)
    INTO v_total, v_insumos FROM obras.t_analisi_precio_unitario_insumo i WHERE i.id_analisis_precio_unitario = p_id_analisis_precio_unitario AND i.id_empresa = p_id_empresa;
    RETURN json_build_object('success', true, 'apu', v_apu, 'insumos', v_insumos, 'costo_directo_unitario', ROUND(v_total, 2));
END; $$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION obras.fn_calcular_estimacion(p_id_estimacion INTEGER, p_id_empresa INTEGER)
RETURNS json AS $$
DECLARE v_detalle json; v_directo numeric; v_indirectos numeric; v_utilidad numeric; v_total numeric; v_factor_i numeric; v_factor_u numeric;
BEGIN
    SELECT COALESCE(e.factor_indirectos, 0), COALESCE(e.factor_utilidad, 0) INTO v_factor_i, v_factor_u FROM obras.t_estimacion e WHERE e.id_estimacion = p_id_estimacion AND e.id_empresa = p_id_empresa;
    IF NOT FOUND THEN RETURN json_build_object('success', false, 'error', 'La estimación no existe o no pertenece a su empresa.'); END IF;
    SELECT COALESCE(SUM(ROUND(x.costo * x.cantidad, 2)), 0), COALESCE(json_agg(json_build_object('id_analisis_precio_unitario', x.id_apu, 'nombre', x.nombre, 'unidad', x.abreviatura, 'costo_unitario', ROUND(x.costo, 2), 'cantidad', x.cantidad, 'subtotal', ROUND(x.costo * x.cantidad, 2)) ORDER BY x.orden), '[]'::json)
    INTO v_directo, v_detalle FROM (SELECT d.orden, d.cantidad, a.id_analisis_precio_unitario id_apu, a.nombre, um.abreviatura, COALESCE((SELECT SUM(ROUND(i.cantidad * i.precio_unitario, 2)) FROM obras.t_analisi_precio_unitario_insumo i WHERE i.id_analisis_precio_unitario = a.id_analisis_precio_unitario AND i.id_empresa = p_id_empresa), 0) costo FROM obras.t_estimacion_analisis_precio_unitario d JOIN obras.t_estimacion e ON e.id_estimacion = d.id_estimacion JOIN obras.t_analisis_precio_unitario a ON a.id_analisis_precio_unitario = d.id_analisis_precio_unitario JOIN obras.t_unidad_medida um ON um.id_unidad_medida = a.id_unidad_medida WHERE d.id_estimacion = p_id_estimacion AND e.id_empresa = p_id_empresa AND a.id_empresa = p_id_empresa) x;
    v_indirectos := 0;
    v_utilidad := v_directo * v_factor_u;
    v_total := v_directo + v_utilidad;
    RETURN json_build_object('success', true, 'detalle', v_detalle, 'subtotal_directo', ROUND(v_directo, 2), 'indirectos', ROUND(v_indirectos, 2), 'utilidad', ROUND(v_utilidad, 2), 'monto_total', ROUND(v_total, 2));
END; $$ LANGUAGE plpgsql;

-- ============================================================================
-- 2. UNIDADES DE MEDIDA nuevas (idempotente)
-- ============================================================================
INSERT INTO obras.t_unidad_medida(nombre, abreviatura, tipo)
SELECT v.nombre, v.abreviatura, v.tipo
FROM (VALUES ('Pieza', 'pza', 'INSUMO'), ('Galon', 'gal', 'INSUMO')) v(nombre, abreviatura, tipo)
WHERE NOT EXISTS (SELECT 1 FROM obras.t_unidad_medida u WHERE LOWER(BTRIM(u.abreviatura)) = LOWER(BTRIM(v.abreviatura)) AND u.estado = 'ACTIVO');

-- ============================================================================
-- 3. MATERIALES de uso en APU (código APU-M##), empresa 1
--    Categorías reutilizadas: Agregados / Cementos y aglomerantes /
--    Acero y metálicos / Mampostería / Acabados / Madera
-- ============================================================================
WITH datos(codigo, nombre, descripcion, categoria, unidad, precio) AS (VALUES
    ('APU-M01', 'Cemento Portland Tipo I', 'Cemento de uso general para concreto y mortero', 'Cementos y aglomerantes', 'bolsa', 25.00),
    ('APU-M02', 'Arena gruesa', 'Arena gruesa lavada para mortero y concreto', 'Agregados', 'm3', 12.50),
    ('APU-M03', 'Piedra chancada 1/2"', 'Piedra chancada de media pulgada', 'Agregados', 'm3', 45.00),
    ('APU-M04', 'Agua', 'Agua para mezclas y curado', 'Agregados', 'm3', 5.00),
    ('APU-M05', 'Madera para encofrado (tablon)', 'Tablón de madera para encofrados', 'Madera', 'pza', 18.00),
    ('APU-M06', 'Clavos de acero 3"', 'Clavos de acero de 3 pulgadas', 'Madera', 'kg', 8.50),
    ('APU-M07', 'Acero corrugado 3/8"', 'Acero corrugado de 3/8 de pulgada', 'Acero y metálicos', 'barra', 22.00),
    ('APU-M08', 'Alambre recocido #16', 'Alambre recocido numero 16', 'Acero y metálicos', 'kg', 6.00),
    ('APU-M09', 'Ladrillo KK 18 huecos', 'Ladrillo king kong de 18 huecos', 'Mampostería', 'u', 1.20),
    ('APU-M10', 'Mortero premezclado', 'Mortero premezclado para tarrajeos', 'Cementos y aglomerantes', 'bolsa', 30.00),
    ('APU-M11', 'Yeso en polvo', 'Yeso en polvo para enlucidos', 'Acabados', 'kg', 2.50),
    ('APU-M12', 'Pintura látex', 'Pintura látex para interiores', 'Acabados', 'gal', 45.00),
    ('APU-M13', 'Cinta de enmascarar', 'Cinta de enmascarar de papel', 'Acabados', 'u', 3.00),
    ('APU-M14', 'Pasta para muros', 'Pasta lista para empastar muros', 'Acabados', 'bolsa', 15.00),
    ('APU-M15', 'Aditivo impermeabilizante', 'Aditivo impermeabilizante para morteros', 'Agregados', 'gal', 55.00),
    ('APU-M16', 'Piso cerámico 60x60', 'Piso de cerámico esmaltado 60 x 60 cm', 'Mampostería', 'm2', 32.00),
    ('APU-M17', 'Pegamento para cerámico', 'Pegamento adhesivo para pisos cerámicos', 'Mampostería', 'bolsa', 18.00)
)
INSERT INTO obras.t_material(codigo, nombre_material, descripcion, id_categoria, id_unidad_medida, precio, estado, id_empresa)
SELECT d.codigo, d.nombre, d.descripcion, cat.id_categoria, um.id_unidad_medida, d.precio, 'ACTIVO', 1
FROM datos d
JOIN obras.t_categoria_material cat ON LOWER(BTRIM(cat.nombre)) = LOWER(BTRIM(d.categoria)) AND cat.estado = 'ACTIVO'
JOIN obras.t_unidad_medida um ON LOWER(BTRIM(um.abreviatura)) = LOWER(BTRIM(d.unidad)) AND um.estado = 'ACTIVO'
WHERE NOT EXISTS (SELECT 1 FROM obras.t_material m WHERE m.codigo = d.codigo AND m.id_empresa = 1);

-- ============================================================================
-- 4. CUADRILLAS / MANO DE OBRA (costos 65, 85, 75 y 30 por jornal)
-- ============================================================================
INSERT INTO obras.t_mano_obra(nombre, descripcion, id_unidad_medida, costo_unitario, id_empresa)
SELECT v.nombre, v.descripcion, um.id_unidad_medida, v.costo, 1
FROM (VALUES
    ('Cuadrilla 1: Albañil + 2 ayudantes', 'Cuadrilla base de albañilería', 65),
    ('Cuadrilla 2: Albañil + 3 ayudantes', 'Cuadrilla reforzada de albañilería', 85),
    ('Cuadrilla 3: Albañil + 1 ayudante', 'Cuadrilla ligera de albañilería', 75),
    ('Cuadrilla 4: Peón / ayudante', 'Cuadrilla de peones y ayudantes', 30)
) v(nombre, descripcion, costo)
JOIN obras.t_unidad_medida um ON LOWER(BTRIM(um.abreviatura)) = 'jornal' AND um.estado = 'ACTIVO'
WHERE NOT EXISTS (SELECT 1 FROM obras.t_mano_obra mo WHERE LOWER(BTRIM(mo.nombre)) = LOWER(BTRIM(v.nombre)) AND mo.id_empresa = 1);

-- ============================================================================
-- 5. APUs BLOQUE 1 - Obra gris / excavación (costos esperados)
--    23.75 | 37.91 | 231.38 | 16.17 | 18.01 | 8.40
-- ============================================================================
WITH nuevos AS (
    INSERT INTO obras.t_analisis_precio_unitario(id_obra, nombre, descripcion, id_unidad_medida, tipo_analisis_precio_unitario, calidad, id_empresa)
    SELECT NULL, v.nombre, v.descripcion, um.id_unidad_medida, v.tipo, v.calidad, 1
    FROM (VALUES
        ('Excavación de zanjas para cimientos', 'Excavación manual de zanjas para cimientos corridos', 'EXCAVACION', NULL, 'm3'),
        ('Cimiento corrido (concreto 1:8)', 'Cimiento corrido de concreto ciclópeo mezcla 1:8', 'OBRA_GRIS', NULL, 'm3'),
        ('Muro de ladrillo KK de soga', 'Muro de ladrillo king kong en aparejo de soga', 'OBRA_GRIS', NULL, 'm2'),
        ('Sobrecimiento reforzado', 'Sobrecimiento de concreto armado con acero mínimo', 'OBRA_GRIS', NULL, 'm'),
        ('Columna de concreto armado 0.25x0.25', 'Columna de concreto armado de sección 0.25 x 0.25 m', 'OBRA_GRIS', NULL, 'u'),
        ('Losa aligerada (e=0.20 m)', 'Losa aligerada con viguetas y techo de espesor 0.20 m', 'OBRA_GRIS', NULL, 'm2')
    ) v(nombre, descripcion, tipo, calidad, unidad)
    JOIN obras.t_unidad_medida um ON LOWER(BTRIM(um.abreviatura)) = LOWER(BTRIM(v.unidad)) AND um.estado = 'ACTIVO'
    WHERE NOT EXISTS (SELECT 1 FROM obras.t_analisis_precio_unitario a WHERE a.nombre = v.nombre AND a.id_empresa = 1)
    RETURNING id_analisis_precio_unitario, nombre
)
INSERT INTO obras.t_analisi_precio_unitario_insumo(id_analisis_precio_unitario, tipo_insumo, id_material, id_mano_obra, nombre, id_unidad_medida, cantidad, precio_unitario, orden, id_empresa)
SELECT n.id_analisis_precio_unitario,
       i.tipo,
       CASE WHEN i.tipo = 'MATERIAL' THEN m.id_material END,
       CASE WHEN i.tipo = 'MANO_OBRA' THEN mo.id_mano_obra END,
       COALESCE(m.nombre_material, mo.nombre),
       um.id_unidad_medida, i.cantidad, i.precio, i.orden, 1
FROM nuevos n
JOIN (VALUES
    ('Excavación de zanjas para cimientos', 'MANO_OBRA', '', 'Cuadrilla 4: Peón / ayudante', 'jornal', 0.6250, 30.00, 1),
    ('Excavación de zanjas para cimientos', 'MATERIAL', 'APU-M04', '', 'm3', 1.0000, 5.00, 2),
    ('Cimiento corrido (concreto 1:8)', 'MATERIAL', 'APU-M01', '', 'bolsa', 0.8000, 25.00, 1),
    ('Cimiento corrido (concreto 1:8)', 'MATERIAL', 'APU-M02', '', 'm3', 0.8000, 12.50, 2),
    ('Cimiento corrido (concreto 1:8)', 'MATERIAL', 'APU-M03', '', 'm3', 0.1400, 45.00, 3),
    ('Cimiento corrido (concreto 1:8)', 'MATERIAL', 'APU-M04', '', 'm3', 0.1000, 5.00, 4),
    ('Cimiento corrido (concreto 1:8)', 'MANO_OBRA', '', 'Cuadrilla 1: Albañil + 2 ayudantes', 'jornal', 0.0170, 65.00, 5),
    ('Muro de ladrillo KK de soga', 'MATERIAL', 'APU-M09', '', 'u', 55.0000, 1.20, 1),
    ('Muro de ladrillo KK de soga', 'MATERIAL', 'APU-M01', '', 'bolsa', 0.6400, 25.00, 2),
    ('Muro de ladrillo KK de soga', 'MATERIAL', 'APU-M02', '', 'm3', 0.3900, 12.50, 3),
    ('Muro de ladrillo KK de soga', 'MANO_OBRA', '', 'Cuadrilla 2: Albañil + 3 ayudantes', 'jornal', 1.7000, 85.00, 4),
    ('Sobrecimiento reforzado', 'MATERIAL', 'APU-M01', '', 'bolsa', 0.2000, 25.00, 1),
    ('Sobrecimiento reforzado', 'MATERIAL', 'APU-M02', '', 'm3', 0.1500, 12.50, 2),
    ('Sobrecimiento reforzado', 'MATERIAL', 'APU-M03', '', 'm3', 0.1000, 45.00, 3),
    ('Sobrecimiento reforzado', 'MATERIAL', 'APU-M04', '', 'm3', 0.1000, 5.00, 4),
    ('Sobrecimiento reforzado', 'MANO_OBRA', '', 'Cuadrilla 1: Albañil + 2 ayudantes', 'jornal', 0.0660, 65.00, 5),
    ('Columna de concreto armado 0.25x0.25', 'MATERIAL', 'APU-M07', '', 'barra', 0.2500, 22.00, 1),
    ('Columna de concreto armado 0.25x0.25', 'MATERIAL', 'APU-M08', '', 'kg', 0.0500, 6.00, 2),
    ('Columna de concreto armado 0.25x0.25', 'MATERIAL', 'APU-M01', '', 'bolsa', 0.2000, 25.00, 3),
    ('Columna de concreto armado 0.25x0.25', 'MATERIAL', 'APU-M02', '', 'm3', 0.1000, 12.50, 4),
    ('Columna de concreto armado 0.25x0.25', 'MATERIAL', 'APU-M03', '', 'm3', 0.1000, 45.00, 5),
    ('Columna de concreto armado 0.25x0.25', 'MATERIAL', 'APU-M05', '', 'pza', 0.0250, 18.00, 6),
    ('Columna de concreto armado 0.25x0.25', 'MATERIAL', 'APU-M06', '', 'kg', 0.0200, 8.50, 7),
    ('Columna de concreto armado 0.25x0.25', 'MANO_OBRA', '', 'Cuadrilla 4: Peón / ayudante', 'jornal', 0.0280, 30.00, 8),
    ('Losa aligerada (e=0.20 m)', 'MATERIAL', 'APU-M01', '', 'bolsa', 0.1500, 25.00, 1),
    ('Losa aligerada (e=0.20 m)', 'MATERIAL', 'APU-M02', '', 'm3', 0.1000, 12.50, 2),
    ('Losa aligerada (e=0.20 m)', 'MATERIAL', 'APU-M03', '', 'm3', 0.0500, 45.00, 3),
    ('Losa aligerada (e=0.20 m)', 'MATERIAL', 'APU-M04', '', 'm3', 0.0500, 5.00, 4),
    ('Losa aligerada (e=0.20 m)', 'MANO_OBRA', '', 'Cuadrilla 1: Albañil + 2 ayudantes', 'jornal', 0.0138, 65.00, 5)
) i(apu, tipo, material, cuadrilla, unidad, cantidad, precio, orden)
  ON i.apu = n.nombre
LEFT JOIN obras.t_material m ON m.codigo = i.material AND m.id_empresa = 1
LEFT JOIN obras.t_mano_obra mo ON LOWER(BTRIM(mo.nombre)) = LOWER(BTRIM(i.cuadrilla)) AND mo.id_empresa = 1
JOIN obras.t_unidad_medida um ON LOWER(BTRIM(um.abreviatura)) = LOWER(BTRIM(i.unidad)) AND um.estado = 'ACTIVO';

-- ============================================================================
-- 6. APUs BLOQUE 2 - Acabados (6 NORMAL + 6 LUJO), sin herramientas ni maquinaria
-- ============================================================================
WITH nuevos AS (
    INSERT INTO obras.t_analisis_precio_unitario(id_obra, nombre, descripcion, id_unidad_medida, tipo_analisis_precio_unitario, calidad, id_empresa)
    SELECT NULL, v.nombre, v.descripcion, um.id_unidad_medida, v.tipo, v.calidad, 1
    FROM (VALUES
        ('Tarrajeo de muros interiores', 'Tarrajeo de muros con mortero premezclado', 'ACABADO', 'NORMAL', 'm2'),
        ('Tarrajeo de cielo raso', 'Tarrajeo de cielorraso con mortero premezclado', 'ACABADO', 'NORMAL', 'm2'),
        ('Contrapiso de 40 mm', 'Contrapiso de cemento, arena y piedra de 40 mm', 'ACABADO', 'NORMAL', 'm2'),
        ('Piso cerámico 60x60', 'Piso de cerámico 60 x 60 cm asentado con pegamento', 'ACABADO', 'NORMAL', 'm2'),
        ('Pintura látex 2 manos', 'Pintura látex dos manos sobre muros empastados', 'ACABADO', 'NORMAL', 'm2'),
        ('Enlucido con yeso', 'Enlucido de muros interiores con yeso', 'ACABADO', 'NORMAL', 'm2'),
        ('Tarrajeo de muros fino', 'Tarrajeo de muros con acabado fino', 'ACABADO', 'LUJO', 'm2'),
        ('Tarrajeo de cielo raso fino', 'Tarrajeo de cielorraso con acabado fino', 'ACABADO', 'LUJO', 'm2'),
        ('Contrapiso pulido impermeabilizado', 'Contrapiso pulido con aditivo impermeabilizante', 'ACABADO', 'LUJO', 'm2'),
        ('Piso porcelanato 60x60', 'Piso de porcelanato 60 x 60 cm asentado con pegamento', 'ACABADO', 'LUJO', 'm2'),
        ('Pintura látex premium 3 manos', 'Pintura látex premium tres manos sobre muros empastados', 'ACABADO', 'LUJO', 'm2'),
        ('Enlucido fino con yeso', 'Enlucido de muros interiores con yeso de acabado fino', 'ACABADO', 'LUJO', 'm2')
    ) v(nombre, descripcion, tipo, calidad, unidad)
    JOIN obras.t_unidad_medida um ON LOWER(BTRIM(um.abreviatura)) = LOWER(BTRIM(v.unidad)) AND um.estado = 'ACTIVO'
    WHERE NOT EXISTS (SELECT 1 FROM obras.t_analisis_precio_unitario a WHERE a.nombre = v.nombre AND a.id_empresa = 1)
    RETURNING id_analisis_precio_unitario, nombre
)
INSERT INTO obras.t_analisi_precio_unitario_insumo(id_analisis_precio_unitario, tipo_insumo, id_material, id_mano_obra, nombre, id_unidad_medida, cantidad, precio_unitario, orden, id_empresa)
SELECT n.id_analisis_precio_unitario,
       i.tipo,
       CASE WHEN i.tipo = 'MATERIAL' THEN m.id_material END,
       CASE WHEN i.tipo = 'MANO_OBRA' THEN mo.id_mano_obra END,
       COALESCE(m.nombre_material, mo.nombre),
       um.id_unidad_medida, i.cantidad, i.precio, i.orden, 1
FROM nuevos n
JOIN (VALUES
    ('Tarrajeo de muros interiores', 'MATERIAL', 'APU-M10', '', 'bolsa', 0.5000, 30.00, 1),
    ('Tarrajeo de muros interiores', 'MATERIAL', 'APU-M04', '', 'm3', 0.1000, 5.00, 2),
    ('Tarrajeo de muros interiores', 'MANO_OBRA', '', 'Cuadrilla 2: Albañil + 3 ayudantes', 'jornal', 0.0776, 85.00, 3),
    ('Tarrajeo de cielo raso', 'MATERIAL', 'APU-M10', '', 'bolsa', 0.6000, 30.00, 1),
    ('Tarrajeo de cielo raso', 'MATERIAL', 'APU-M04', '', 'm3', 0.1200, 5.00, 2),
    ('Tarrajeo de cielo raso', 'MANO_OBRA', '', 'Cuadrilla 2: Albañil + 3 ayudantes', 'jornal', 0.0824, 85.00, 3),
    ('Contrapiso de 40 mm', 'MATERIAL', 'APU-M01', '', 'bolsa', 0.2000, 25.00, 1),
    ('Contrapiso de 40 mm', 'MATERIAL', 'APU-M02', '', 'm3', 0.2400, 12.50, 2),
    ('Contrapiso de 40 mm', 'MATERIAL', 'APU-M03', '', 'm3', 0.1000, 45.00, 3),
    ('Contrapiso de 40 mm', 'MATERIAL', 'APU-M04', '', 'm3', 0.0600, 5.00, 4),
    ('Contrapiso de 40 mm', 'MANO_OBRA', '', 'Cuadrilla 1: Albañil + 2 ayudantes', 'jornal', 0.0231, 65.00, 5),
    ('Piso cerámico 60x60', 'MATERIAL', 'APU-M16', '', 'm2', 1.0500, 32.00, 1),
    ('Piso cerámico 60x60', 'MATERIAL', 'APU-M17', '', 'bolsa', 0.2000, 18.00, 2),
    ('Piso cerámico 60x60', 'MANO_OBRA', '', 'Cuadrilla 3: Albañil + 1 ayudante', 'jornal', 0.0540, 75.00, 3),
    ('Pintura látex 2 manos', 'MATERIAL', 'APU-M12', '', 'gal', 0.1000, 45.00, 1),
    ('Pintura látex 2 manos', 'MATERIAL', 'APU-M14', '', 'bolsa', 0.2000, 15.00, 2),
    ('Pintura látex 2 manos', 'MATERIAL', 'APU-M13', '', 'u', 0.0200, 3.00, 3),
    ('Pintura látex 2 manos', 'MANO_OBRA', '', 'Cuadrilla 4: Peón / ayudante', 'jornal', 0.0707, 30.00, 4),
    ('Enlucido con yeso', 'MATERIAL', 'APU-M11', '', 'kg', 2.0000, 2.50, 1),
    ('Enlucido con yeso', 'MATERIAL', 'APU-M04', '', 'm3', 0.1000, 5.00, 2),
    ('Enlucido con yeso', 'MANO_OBRA', '', 'Cuadrilla 4: Peón / ayudante', 'jornal', 0.2300, 30.00, 3),
    ('Tarrajeo de muros fino', 'MATERIAL', 'APU-M10', '', 'bolsa', 0.6000, 30.00, 1),
    ('Tarrajeo de muros fino', 'MATERIAL', 'APU-M04', '', 'm3', 0.1500, 5.00, 2),
    ('Tarrajeo de muros fino', 'MANO_OBRA', '', 'Cuadrilla 2: Albañil + 3 ayudantes', 'jornal', 0.0900, 85.00, 3),
    ('Tarrajeo de cielo raso fino', 'MATERIAL', 'APU-M10', '', 'bolsa', 0.7000, 30.00, 1),
    ('Tarrajeo de cielo raso fino', 'MATERIAL', 'APU-M04', '', 'm3', 0.1500, 5.00, 2),
    ('Tarrajeo de cielo raso fino', 'MANO_OBRA', '', 'Cuadrilla 2: Albañil + 3 ayudantes', 'jornal', 0.0959, 85.00, 3),
    ('Contrapiso pulido impermeabilizado', 'MATERIAL', 'APU-M01', '', 'bolsa', 0.2500, 25.00, 1),
    ('Contrapiso pulido impermeabilizado', 'MATERIAL', 'APU-M02', '', 'm3', 0.3000, 12.50, 2),
    ('Contrapiso pulido impermeabilizado', 'MATERIAL', 'APU-M03', '', 'm3', 0.1000, 45.00, 3),
    ('Contrapiso pulido impermeabilizado', 'MATERIAL', 'APU-M04', '', 'm3', 0.0800, 5.00, 4),
    ('Contrapiso pulido impermeabilizado', 'MATERIAL', 'APU-M15', '', 'gal', 0.0200, 55.00, 5),
    ('Contrapiso pulido impermeabilizado', 'MANO_OBRA', '', 'Cuadrilla 1: Albañil + 2 ayudantes', 'jornal', 0.0308, 65.00, 6),
    ('Piso porcelanato 60x60', 'MATERIAL', 'APU-M16', '', 'm2', 1.0500, 32.00, 1),
    ('Piso porcelanato 60x60', 'MATERIAL', 'APU-M17', '', 'bolsa', 0.3000, 18.00, 2),
    ('Piso porcelanato 60x60', 'MANO_OBRA', '', 'Cuadrilla 2: Albañil + 3 ayudantes', 'jornal', 0.2341, 85.00, 3),
    ('Pintura látex premium 3 manos', 'MATERIAL', 'APU-M12', '', 'gal', 0.1200, 45.00, 1),
    ('Pintura látex premium 3 manos', 'MATERIAL', 'APU-M14', '', 'bolsa', 0.2500, 15.00, 2),
    ('Pintura látex premium 3 manos', 'MATERIAL', 'APU-M13', '', 'u', 0.0300, 3.00, 3),
    ('Pintura látex premium 3 manos', 'MANO_OBRA', '', 'Cuadrilla 4: Peón / ayudante', 'jornal', 0.0980, 30.00, 4),
    ('Enlucido fino con yeso', 'MATERIAL', 'APU-M11', '', 'kg', 2.4000, 2.50, 1),
    ('Enlucido fino con yeso', 'MATERIAL', 'APU-M04', '', 'm3', 0.1200, 5.00, 2),
    ('Enlucido fino con yeso', 'MANO_OBRA', '', 'Cuadrilla 4: Peón / ayudante', 'jornal', 0.3000, 30.00, 3)
) i(apu, tipo, material, cuadrilla, unidad, cantidad, precio, orden)
  ON i.apu = n.nombre
LEFT JOIN obras.t_material m ON m.codigo = i.material AND m.id_empresa = 1
LEFT JOIN obras.t_mano_obra mo ON LOWER(BTRIM(mo.nombre)) = LOWER(BTRIM(i.cuadrilla)) AND mo.id_empresa = 1
JOIN obras.t_unidad_medida um ON LOWER(BTRIM(um.abreviatura)) = LOWER(BTRIM(i.unidad)) AND um.estado = 'ACTIVO';

-- ============================================================================
-- 7. APUs BLOQUE 3 - Subcontratos (sin insumos)
-- ============================================================================
INSERT INTO obras.t_analisis_precio_unitario(id_obra, nombre, descripcion, id_unidad_medida, tipo_analisis_precio_unitario, calidad, id_empresa)
SELECT NULL, v.nombre, v.descripcion, um.id_unidad_medida, 'SUBCONTRATO', NULL, 1
FROM (VALUES
    ('Instalaciones eléctricas (global)', 'Instalaciones eléctricas completas por subcontrato', 'lote'),
    ('Instalaciones sanitarias (global)', 'Instalaciones sanitarias completas por subcontrato', 'lote'),
    ('Instalaciones de gas / GLP (global)', 'Instalaciones de gas doméstico por subcontrato', 'lote'),
    ('Carpintería metálica (puertas y ventanas)', 'Puertas, ventanas y elementos metálicos por subcontrato', 'u'),
    ('Sistema contra incendios (global)', 'Sistema contra incendios por subcontrato', 'm2'),
    ('Estructura metálica (montaje)', 'Montaje de estructura metálica por subcontrato', 'ton')
) v(nombre, descripcion, unidad)
JOIN obras.t_unidad_medida um ON LOWER(BTRIM(um.abreviatura)) = LOWER(BTRIM(v.unidad)) AND um.estado = 'ACTIVO'
WHERE NOT EXISTS (SELECT 1 FROM obras.t_analisis_precio_unitario a WHERE a.nombre = v.nombre AND a.id_empresa = 1);

COMMIT;

-- ============================================================================
-- 8. VERIFICACIÓN: costos directos por APU y conteos
-- ============================================================================
SELECT a.nombre, a.tipo_analisis_precio_unitario, a.calidad, um.abreviatura AS unidad,
       ROUND((SELECT SUM(ROUND(i.cantidad * i.precio_unitario, 2))
              FROM obras.t_analisi_precio_unitario_insumo i
              WHERE i.id_analisis_precio_unitario = a.id_analisis_precio_unitario), 2) AS costo_directo
FROM obras.t_analisis_precio_unitario a
JOIN obras.t_unidad_medida um ON um.id_unidad_medida = a.id_unidad_medida
WHERE a.id_empresa = 1
ORDER BY a.tipo_analisis_precio_unitario, a.calidad NULLS FIRST, a.nombre;

SELECT 'materiales' AS entidad, COUNT(*) AS total FROM obras.t_material WHERE id_empresa = 1 AND codigo LIKE 'APU-%'
UNION ALL SELECT 'cuadrillas', COUNT(*) FROM obras.t_mano_obra WHERE id_empresa = 1
UNION ALL SELECT 'apus', COUNT(*) FROM obras.t_analisis_precio_unitario WHERE id_empresa = 1
UNION ALL SELECT 'insumos', COUNT(*) FROM obras.t_analisi_precio_unitario_insumo WHERE id_empresa = 1;