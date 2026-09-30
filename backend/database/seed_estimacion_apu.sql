-- ============================================================================
-- OBRATEC - SEED de estimación / APU (Bloques 1, 2 y 3) para empresa demo (1)
-- Ejecutar después de migration_apu_materiales_y_presupuestos.sql.
-- Re-ejecutable: crea unidades, materiales, APUs y detalles solo de materiales.
-- Ejecutar con: python -c "... psycopg2 ... execute(open(sql).read())"
-- ============================================================================
BEGIN;

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
INSERT INTO obras.t_analisi_precio_unitario_insumo(id_analisis_precio_unitario, tipo_insumo, id_material, nombre, id_unidad_medida, cantidad, precio_unitario, orden, id_empresa)
SELECT n.id_analisis_precio_unitario, 'MATERIAL', m.id_material, m.nombre_material,
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
JOIN obras.t_unidad_medida um ON LOWER(BTRIM(um.abreviatura)) = LOWER(BTRIM(i.unidad)) AND um.estado = 'ACTIVO'
WHERE i.tipo = 'MATERIAL' AND m.id_material IS NOT NULL;

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
INSERT INTO obras.t_analisi_precio_unitario_insumo(id_analisis_precio_unitario, tipo_insumo, id_material, nombre, id_unidad_medida, cantidad, precio_unitario, orden, id_empresa)
SELECT n.id_analisis_precio_unitario, 'MATERIAL', m.id_material, m.nombre_material,
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
JOIN obras.t_unidad_medida um ON LOWER(BTRIM(um.abreviatura)) = LOWER(BTRIM(i.unidad)) AND um.estado = 'ACTIVO'
WHERE i.tipo = 'MATERIAL' AND m.id_material IS NOT NULL;

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

UPDATE obras.t_analisis_precio_unitario a
SET mano_de_obra = v.costo
FROM (VALUES
    ('Excavación de zanjas para cimientos', 18.75),
    ('Cimiento corrido (concreto 1:8)', 1.11),
    ('Muro de ladrillo KK de soga', 144.50),
    ('Sobrecimiento reforzado', 4.29),
    ('Columna de concreto armado 0.25x0.25', 0.84),
    ('Losa aligerada (e=0.20 m)', 0.90),
    ('Tarrajeo de muros interiores', 6.60),
    ('Tarrajeo de cielo raso', 7.00),
    ('Contrapiso de 40 mm', 1.50),
    ('Piso cerámico 60x60', 4.05),
    ('Pintura látex 2 manos', 2.12),
    ('Enlucido con yeso', 6.90),
    ('Tarrajeo de muros fino', 7.65),
    ('Tarrajeo de cielo raso fino', 8.15),
    ('Contrapiso pulido impermeabilizado', 2.00),
    ('Piso porcelanato 60x60', 19.90),
    ('Pintura látex premium 3 manos', 2.94),
    ('Enlucido fino con yeso', 9.00)
) AS v(nombre, costo)
WHERE a.id_empresa = 1 AND a.nombre = v.nombre;

COMMIT;

-- ============================================================================
-- 8. VERIFICACIÓN: costos directos por APU y conteos
-- ============================================================================
SELECT a.codigo, a.nombre, um.abreviatura AS unidad,
       a.costo_materiales, a.mano_de_obra, a.costo_directo,
       a.porcentaje_utilidad, a.precio_unitario_final
FROM obras.t_analisis_precio_unitario a
JOIN obras.t_unidad_medida um ON um.id_unidad_medida = a.id_unidad_medida
WHERE a.id_empresa = 1
ORDER BY a.nombre;

SELECT 'materiales' AS entidad, COUNT(*) AS total FROM obras.t_material WHERE id_empresa = 1 AND codigo LIKE 'APU-%'
UNION ALL SELECT 'apus', COUNT(*) FROM obras.t_analisis_precio_unitario WHERE id_empresa = 1
UNION ALL SELECT 'insumos', COUNT(*) FROM obras.t_analisi_precio_unitario_insumo WHERE id_empresa = 1;