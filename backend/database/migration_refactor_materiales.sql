BEGIN;

SET search_path TO obras, public;

-- 1. Eliminar referencias y vaciar tablas de materiales
DELETE FROM obras.t_movimiento_almacen;
DELETE FROM obras.t_unidad_material;
DELETE FROM obras.t_materiales_almacen;
DELETE FROM obras.t_material_caracteristica;
DELETE FROM obras.t_proveedor_material;

UPDATE obras.t_apu_componente SET id_recurso = NULL WHERE tipo_recurso = 'MATERIAL';
UPDATE obras.t_analisi_precio_unitario_insumo SET id_material = NULL;

DELETE FROM obras.t_material;
DELETE FROM obras.t_material_base;

ALTER SEQUENCE obras.t_material_id_material_seq RESTART WITH 1;
ALTER SEQUENCE obras.t_material_base_id_material_base_seq RESTART WITH 1;

-- 2. Eliminar trigger que auto-poblaba materiales al crear empresa
DROP TRIGGER IF EXISTS trg_poblar_catalogo_nueva_empresa ON obras.t_empresa;
DROP FUNCTION IF EXISTS obras.fn_trg_poblar_catalogo_empresa();

-- 3. Asegurar constraints e índices en t_material
ALTER TABLE obras.t_material DROP CONSTRAINT IF EXISTS uq_material_empresa_codigo;
DROP INDEX IF EXISTS obras.uq_material_empresa_codigo;

ALTER TABLE obras.t_material
    ADD CONSTRAINT uq_material_empresa_codigo UNIQUE (id_empresa, codigo);

CREATE INDEX IF NOT EXISTS idx_material_empresa_estado ON obras.t_material (id_empresa, estado);
CREATE INDEX IF NOT EXISTS idx_material_categoria ON obras.t_material (id_categoria);
CREATE INDEX IF NOT EXISTS idx_material_base ON obras.t_material (id_material_base);

-- 4. Triggers simples para updated_at
CREATE OR REPLACE FUNCTION obras.fn_material_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tg_material_updated_at ON obras.t_material;
CREATE TRIGGER tg_material_updated_at
BEFORE UPDATE ON obras.t_material
FOR EACH ROW EXECUTE FUNCTION obras.fn_material_updated_at();

DROP TRIGGER IF EXISTS tg_material_base_updated_at ON obras.t_material_base;
CREATE TRIGGER tg_material_base_updated_at
BEFORE UPDATE ON obras.t_material_base
FOR EACH ROW EXECUTE FUNCTION obras.fn_material_updated_at();

-- 5. Asegurar las 8 categorías requeridas
INSERT INTO obras.t_categoria_material (nombre, descripcion, estado)
VALUES
    ('Áridos y Aglomerantes', 'Cementos, cales, yesos, arenas, gravas y piedras', 'ACTIVO'),
    ('Aceros, Hierros y Fijaciones', 'Barras corrugadas, alambres, mallas, perfiles y pernos', 'ACTIVO'),
    ('Mampostería, Prefabricados y Muros', 'Ladrillos cerámicos, bloques, viguetas y bovedillas', 'ACTIVO'),
    ('Instalaciones Hidráulicas y Sanitarias', 'Tuberías PVC, PPR, accesorios, griferías y tanques', 'ACTIVO'),
    ('Instalaciones Eléctricas y Telecomunicaciones', 'Cables de cobre, ductos, térmicos, cajas y tomacorrientes', 'ACTIVO'),
    ('Cubiertas, Techos y Aislamiento', 'Calaminas, tejas, policarbonatos, cumbreras y aislantes', 'ACTIVO'),
    ('Acabados, Revestimientos y Pisos', 'Cerámicas, porcelanatos, adhesivos, pastinas y pinturas', 'ACTIVO'),
    ('Carpintería, Cerrajería y Vidrios', 'Puertas, ventanas de aluminio, cerraduras y vidrios', 'ACTIVO')
ON CONFLICT DO NOTHING;

-- 6. Cargar dataset inicial en t_material_base
DO $$
DECLARE
    c_ari INT; c_ace INT; c_mam INT; c_hid INT;
    c_ele INT; c_cub INT; c_aca INT; c_car INT;
    u_bolsa INT; u_kg INT; u_m INT; u_m2 INT; u_m3 INT;
    u_pza INT; u_barra INT; u_ml INT; u_gal INT;
BEGIN
    SELECT id_categoria INTO c_ari FROM obras.t_categoria_material WHERE LOWER(TRIM(nombre)) LIKE '%áridos y aglomerantes%' LIMIT 1;
    SELECT id_categoria INTO c_ace FROM obras.t_categoria_material WHERE LOWER(TRIM(nombre)) LIKE '%aceros, hierros%' LIMIT 1;
    SELECT id_categoria INTO c_mam FROM obras.t_categoria_material WHERE LOWER(TRIM(nombre)) LIKE '%mampostería%' LIMIT 1;
    SELECT id_categoria INTO c_hid FROM obras.t_categoria_material WHERE LOWER(TRIM(nombre)) LIKE '%instalaciones hidráulicas%' LIMIT 1;
    SELECT id_categoria INTO c_ele FROM obras.t_categoria_material WHERE LOWER(TRIM(nombre)) LIKE '%instalaciones eléctricas%' LIMIT 1;
    SELECT id_categoria INTO c_cub FROM obras.t_categoria_material WHERE LOWER(TRIM(nombre)) LIKE '%cubiertas%' LIMIT 1;
    SELECT id_categoria INTO c_aca FROM obras.t_categoria_material WHERE LOWER(TRIM(nombre)) LIKE '%acabados%' LIMIT 1;
    SELECT id_categoria INTO c_car FROM obras.t_categoria_material WHERE LOWER(TRIM(nombre)) LIKE '%carpintería%' LIMIT 1;

    SELECT id_unidad_medida INTO u_bolsa FROM obras.t_unidad_medida WHERE LOWER(TRIM(abreviatura)) = 'bolsa' LIMIT 1;
    SELECT id_unidad_medida INTO u_kg FROM obras.t_unidad_medida WHERE LOWER(TRIM(abreviatura)) = 'kg' LIMIT 1;
    SELECT id_unidad_medida INTO u_m FROM obras.t_unidad_medida WHERE LOWER(TRIM(abreviatura)) = 'm' LIMIT 1;
    SELECT id_unidad_medida INTO u_m2 FROM obras.t_unidad_medida WHERE LOWER(TRIM(abreviatura)) = 'm2' LIMIT 1;
    SELECT id_unidad_medida INTO u_m3 FROM obras.t_unidad_medida WHERE LOWER(TRIM(abreviatura)) = 'm3' LIMIT 1;
    SELECT id_unidad_medida INTO u_pza FROM obras.t_unidad_medida WHERE LOWER(TRIM(abreviatura)) IN ('pza', 'u') LIMIT 1;
    SELECT id_unidad_medida INTO u_barra FROM obras.t_unidad_medida WHERE LOWER(TRIM(abreviatura)) = 'barra' LIMIT 1;
    SELECT id_unidad_medida INTO u_ml FROM obras.t_unidad_medida WHERE LOWER(TRIM(abreviatura)) = 'ml' LIMIT 1;
    SELECT id_unidad_medida INTO u_gal FROM obras.t_unidad_medida WHERE LOWER(TRIM(abreviatura)) = 'gal' LIMIT 1;

    -- Categoría 1: Áridos y Aglomerantes
    INSERT INTO obras.t_material_base (codigo, nombre_material, descripcion, id_categoria, id_unidad_medida, precio_referencial) VALUES
        ('MAT-ARI-001', 'Cemento Portland IP-30', 'Cemento estructural de uso general en bolsa de 50 kg', c_ari, u_bolsa, 52.00),
        ('MAT-ARI-002', 'Cemento Portland IP-40', 'Cemento de alta resistencia inicial para obras civiles mayores', c_ari, u_bolsa, 58.00),
        ('MAT-ARI-003', 'Cemento Blanco', 'Cemento portland blanco para acabados y juntas', c_ari, u_bolsa, 75.00),
        ('MAT-ARI-004', 'Cal viva / hidratada', 'Cal para revoques y morteros tradicionales bolsa 20 kg', c_ari, u_bolsa, 25.00),
        ('MAT-ARI-005', 'Yeso de construcción', 'Yeso para enlucidos interiores bolsa 30 kg', c_ari, u_bolsa, 22.00),
        ('MAT-ARI-006', 'Arena fina lavada', 'Arena limpia clasificada para revoques y morteros', c_ari, u_m3, 110.00),
        ('MAT-ARI-007', 'Arena gruesa', 'Arena para hormigones y contrapisos', c_ari, u_m3, 95.00),
        ('MAT-ARI-008', 'Grava común rodada', 'Grava rodada limpia para mezclas de hormigón', c_ari, u_m3, 120.00),
        ('MAT-ARI-009', 'Ripio triturado 3/4"', 'Agregado grueso chancado para hormigón armado', c_ari, u_m3, 130.00),
        ('MAT-ARI-010', 'Piedra manzana bruta', 'Piedra para cimientos ciclópeos y muros de contención', c_ari, u_m3, 90.00),
        ('MAT-ARI-011', 'Piedra chancada 1/2"', 'Piedra partida para drenajes y carpetas', c_ari, u_m3, 115.00);

    -- Categoría 2: Aceros, Hierros y Fijaciones
    INSERT INTO obras.t_material_base (codigo, nombre_material, descripcion, id_categoria, id_unidad_medida, precio_referencial) VALUES
        ('MAT-ACE-001', 'Fierro corrugado 6 mm', 'Barra corrugada ASTM A706 de 12 metros', c_ace, u_barra, 28.00),
        ('MAT-ACE-002', 'Fierro corrugado 8 mm', 'Barra corrugada de 12 metros para estribos y losas', c_ace, u_barra, 45.00),
        ('MAT-ACE-003', 'Fierro corrugado 10 mm', 'Barra corrugada estructural de 12 metros', c_ace, u_barra, 70.00),
        ('MAT-ACE-004', 'Fierro corrugado 12 mm', 'Barra corrugada estructural de 12 metros', c_ace, u_barra, 100.00),
        ('MAT-ACE-005', 'Fierro corrugado 16 mm', 'Barra corrugada pesada para columnas y vigas 12m', c_ace, u_barra, 175.00),
        ('MAT-ACE-006', 'Fierro corrugado 20 mm', 'Barra corrugada para zapatas y fundaciones 12m', c_ace, u_barra, 275.00),
        ('MAT-ACE-007', 'Alambre de amarre #16', 'Alambre recocido dulce para enfierradura', c_ace, u_kg, 12.00),
        ('MAT-ACE-008', 'Clavos de construcción con cabeza', 'Clavos para encofrado surtidos 2" a 4"', c_ace, u_kg, 14.00),
        ('MAT-ACE-009', 'Malla electrosoldada 15x15 cm 4.2mm', 'Malla para refuerzo de contrapisos y losas', c_ace, u_m2, 22.00),
        ('MAT-ACE-010', 'Perfil metálico Costanera 100x50x15x2mm', 'Perfil de acero conformado en frío 6m', c_ace, u_barra, 140.00),
        ('MAT-ACE-011', 'Perno de anclaje expansivo 1/2" x 4"', 'Perno mecánico para anclajes en hormigón', c_ace, u_pza, 8.50);

    -- Categoría 3: Mampostería, Prefabricados y Muros
    INSERT INTO obras.t_material_base (codigo, nombre_material, descripcion, id_categoria, id_unidad_medida, precio_referencial) VALUES
        ('MAT-MAM-001', 'Ladrillo cerámico 6 huecos (24x15x18)', 'Ladrillo cerámico para muros divisorios', c_mam, u_pza, 0.95),
        ('MAT-MAM-002', 'Ladrillo cerámico 3 huecos caravista', 'Ladrillo para tabiques y fachadas vistas', c_mam, u_pza, 1.20),
        ('MAT-MAM-003', 'Ladrillo gambote macizo cocido', 'Ladrillo adobito macizo para muros portantes', c_mam, u_pza, 0.70),
        ('MAT-MAM-004', 'Ladrillo tubular 21 huecos', 'Ladrillo estructural para muros armados', c_mam, u_pza, 1.60),
        ('MAT-MAM-005', 'Bloque de hormigón 15x20x40 cm', 'Bloque de cemento vibrocomprimido para muros', c_mam, u_pza, 4.50),
        ('MAT-MAM-006', 'Vigueta pretensada de hormigón', 'Vigueta prefabricada estructural para losas', c_mam, u_ml, 28.00),
        ('MAT-MAM-007', 'Plastofor / bovedilla para losa alivianada', 'Bloque de EPS alivianado 100x40x12 cm', c_mam, u_pza, 18.00);

    -- Categoría 4: Instalaciones Hidráulicas y Sanitarias
    INSERT INTO obras.t_material_base (codigo, nombre_material, descripcion, id_categoria, id_unidad_medida, precio_referencial) VALUES
        ('MAT-HID-001', 'Tubo PVC sanitario 4" (110 mm)', 'Tubería de desagüe sanitario campana 4m', c_hid, u_barra, 85.00),
        ('MAT-HID-002', 'Tubo PVC sanitario 2" (50 mm)', 'Tubería de desagüe sanitario secundario 4m', c_hid, u_barra, 42.00),
        ('MAT-HID-003', 'Tubo PVC presión 1/2" SDR-13.5', 'Tubería rosca/encolar para agua fría 6m', c_hid, u_barra, 32.00),
        ('MAT-HID-004', 'Tubo PPR termofusión 20 mm PN-20', 'Tubo de polipropileno para agua fría y caliente 4m', c_hid, u_barra, 45.00),
        ('MAT-HID-005', 'Tubo PPR termofusión 25 mm PN-20', 'Tubo de polipropileno matriz de distribución 4m', c_hid, u_barra, 58.00),
        ('MAT-HID-006', 'Codo PVC sanitario 4" x 90°', 'Accesorio para desagüe sanitario', c_hid, u_pza, 14.00),
        ('MAT-HID-007', 'Tee PVC sanitaria 4"', 'Derivación sanitaria con campana', c_hid, u_pza, 22.00),
        ('MAT-HID-008', 'Llave de paso esférica 1/2" de bronce', 'Válvula de corte de paso total', c_hid, u_pza, 45.00),
        ('MAT-HID-009', 'Pegamento PVC para tuberías 250 g', 'Adhesivo para unión química de PVC', c_hid, u_pza, 28.00),
        ('MAT-HID-010', 'Tanque de agua polietileno 1000 L', 'Tanque tricapa con flotador y accesorios', c_hid, u_pza, 850.00);

    -- Categoría 5: Instalaciones Eléctricas y Telecomunicaciones
    INSERT INTO obras.t_material_base (codigo, nombre_material, descripcion, id_categoria, id_unidad_medida, precio_referencial) VALUES
        ('MAT-ELE-001', 'Cable de cobre unipolar 1.5 mm2', 'Conductor aislado para retornos de iluminación', c_ele, u_m, 2.80),
        ('MAT-ELE-002', 'Cable de cobre unipolar 2.5 mm2', 'Conductor para circuitos de tomas e iluminación', c_ele, u_m, 4.20),
        ('MAT-ELE-003', 'Cable de cobre unipolar 4.0 mm2', 'Conductor para circuitos de fuerza y duchas', c_ele, u_m, 6.80),
        ('MAT-ELE-004', 'Cable de cobre unipolar 6.0 mm2', 'Conductor alimentador de tablero secundario', c_ele, u_m, 10.50),
        ('MAT-ELE-005', 'Tubo conduit PVC rígido 3/4" x 3m', 'Tubería rígida para cableado empotrado', c_ele, u_barra, 12.00),
        ('MAT-ELE-006', 'Tubo corrugado flexible 3/4"', 'Manguera corrugada para losa y tabiques', c_ele, u_m, 2.50),
        ('MAT-ELE-007', 'Caja rectangular de embutir 4x2"', 'Caja plástica reforzada para tomas e interruptores', c_ele, u_pza, 3.00),
        ('MAT-ELE-008', 'Interruptor termomagnético bipolar 20A', 'Disyuntor de protección sobrecorriente', c_ele, u_pza, 48.00),
        ('MAT-ELE-009', 'Tomacorriente doble con tierra', 'Placa modular de tomas 10/16A', c_ele, u_pza, 25.00),
        ('MAT-ELE-010', 'Interruptor simple modular', 'Placa con interruptor de embutir', c_ele, u_pza, 18.00);

    -- Categoría 6: Cubiertas, Techos y Aislamiento
    INSERT INTO obras.t_material_base (codigo, nombre_material, descripcion, id_categoria, id_unidad_medida, precio_referencial) VALUES
        ('MAT-CUB-001', 'Calamina galvanizada ondulada #28 (3m)', 'Chapa de zinc acanalada para tinglados y cubiertas', c_cub, u_pza, 70.00),
        ('MAT-CUB-002', 'Calamina trapezoidal #28 prepintada (3m)', 'Chapa conformada prepintada para techos', c_cub, u_pza, 85.00),
        ('MAT-CUB-003', 'Teja cerámica colonial', 'Teja curva de arcilla cocida tipo española', c_cub, u_pza, 2.50),
        ('MAT-CUB-004', 'Teja de fibrocemento ondulada 2.44m', 'Placa ondulada sin asbesto para techumbres', c_cub, u_pza, 65.00),
        ('MAT-CUB-005', 'Cumbrera galvanizada 0.40 x 2.0 m', 'Caballete de remate para techos de calamina', c_cub, u_pza, 35.00),
        ('MAT-CUB-006', 'Tornillo autoperforante 2" con neopreno', 'Fijación con arandela de sellado hermético', c_cub, u_pza, 0.60),
        ('MAT-CUB-007', 'Manta aislante térmica foil de aluminio', 'Aislante de lana de vidrio/espuma 50mm', c_cub, u_m2, 28.00);

    -- Categoría 7: Acabados, Revestimientos y Pisos
    INSERT INTO obras.t_material_base (codigo, nombre_material, descripcion, id_categoria, id_unidad_medida, precio_referencial) VALUES
        ('MAT-ACA-001', 'Piso cerámico 45x45 cm', 'Cerámica esmaltada para pisos de tráfico medio/alto', c_aca, u_m2, 55.00),
        ('MAT-ACA-002', 'Porcelanato pulido rectificado 60x60 cm', 'Porcelanato de alta resistencia para interiores', c_aca, u_m2, 110.00),
        ('MAT-ACA-003', 'Revestimiento azulejo cerámico 25x40 cm', 'Azulejo esmaltado para baños y cocinas', c_aca, u_m2, 48.00),
        ('MAT-ACA-004', 'Piso flotante melamínico HDF 8 mm', 'Piso laminado con manta niveladora', c_aca, u_m2, 75.00),
        ('MAT-ACA-005', 'Adhesivo cementicio para cerámica 20 kg', 'Mortero cola gris para pisos y paredes', c_aca, u_bolsa, 28.00),
        ('MAT-ACA-006', 'Adhesivo especial para porcelanato 20 kg', 'Mortero cola flexible con aditivos poliméricos', c_aca, u_bolsa, 45.00),
        ('MAT-ACA-007', 'Pastina para juntas 1 kg', 'Fraguador impermeable antihongos para juntas', c_aca, u_kg, 8.00),
        ('MAT-ACA-008', 'Pintura látex lavable para interiores', 'Pintura vinílica acabado mate galón', c_aca, u_gal, 85.00),
        ('MAT-ACA-009', 'Pintura látex acrílica para exteriores', 'Pintura hidrorrepelente para fachadas galón', c_aca, u_gal, 115.00),
        ('MAT-ACA-010', 'Sellador fijador acrílico para muros', 'Imprimante fijador concentrado galón', c_aca, u_gal, 55.00);

    -- Categoría 8: Carpintería, Cerrajería y Vidrios
    INSERT INTO obras.t_material_base (codigo, nombre_material, descripcion, id_categoria, id_unidad_medida, precio_referencial) VALUES
        ('MAT-CAR-001', 'Puerta placa de madera 0.80 x 2.10 m', 'Hoja de puerta enchapada para interiores', c_car, u_pza, 220.00),
        ('MAT-CAR-002', 'Marco de madera 2" x 4" para puerta', 'Marco cepillado de tajibo/roble para puerta', c_car, u_pza, 110.00),
        ('MAT-CAR-003', 'Cerradura de acceso principal doble golpe', 'Chapa de seguridad con 3 llaves', c_car, u_pza, 140.00),
        ('MAT-CAR-004', 'Cerradura pomo para puerta interior', 'Cerradura cilíndrica pomo acabado satín', c_car, u_pza, 65.00),
        ('MAT-CAR-005', 'Bisagra de acero 3 1/2" con tornillos', 'Bisagra para puertas de carpintería', c_car, u_pza, 15.00),
        ('MAT-CAR-006', 'Ventana corrediza de aluminio 1.20 x 1.00 m', 'Ventana línea 20 con vidrio colocado', c_car, u_pza, 450.00),
        ('MAT-CAR-007', 'Vidrio flotado incoloro 4 mm', 'Vidrio plano para carpinterías convencionales', c_car, u_m2, 90.00),
        ('MAT-CAR-008', 'Silicona selladora neutra 300 ml', 'Sellador para vidrios y carpintería de aluminio', c_car, u_pza, 32.00);
END $$;

-- 7. Funciones de PostgreSQL

-- 7.1 Registrar material
CREATE OR REPLACE FUNCTION obras.fn_registrar_material(
    p_id_empresa INT,
    p_codigo VARCHAR,
    p_nombre_material VARCHAR,
    p_descripcion TEXT,
    p_id_categoria INT,
    p_id_unidad_medida INT,
    p_precio NUMERIC,
    p_id_material_base INT DEFAULT NULL,
    p_es_propio BOOLEAN DEFAULT TRUE
)
RETURNS INT AS $$
DECLARE
    v_id_material INT;
    v_es_propio BOOLEAN;
BEGIN
    IF p_id_empresa IS NULL THEN
        RAISE EXCEPTION 'El id_empresa es obligatorio';
    END IF;

    IF TRIM(COALESCE(p_codigo, '')) = '' THEN
        RAISE EXCEPTION 'El código del material es obligatorio';
    END IF;

    IF TRIM(COALESCE(p_nombre_material, '')) = '' THEN
        RAISE EXCEPTION 'El nombre del material es obligatorio';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM obras.t_empresa WHERE id_empresa = p_id_empresa) THEN
        RAISE EXCEPTION 'La empresa % no existe', p_id_empresa;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM obras.t_categoria_material WHERE id_categoria = p_id_categoria AND estado = 'ACTIVO') THEN
        RAISE EXCEPTION 'La categoría % no existe o no está activa', p_id_categoria;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM obras.t_unidad_medida WHERE id_unidad_medida = p_id_unidad_medida AND estado = 'ACTIVO') THEN
        RAISE EXCEPTION 'La unidad de medida % no existe o no está activa', p_id_unidad_medida;
    END IF;

    IF EXISTS (SELECT 1 FROM obras.t_material WHERE id_empresa = p_id_empresa AND LOWER(TRIM(codigo)) = LOWER(TRIM(p_codigo))) THEN
        RAISE EXCEPTION 'El código % ya existe en la empresa %', p_codigo, p_id_empresa;
    END IF;

    v_es_propio := CASE WHEN p_id_material_base IS NOT NULL THEN FALSE ELSE COALESCE(p_es_propio, TRUE) END;

    INSERT INTO obras.t_material (
        id_empresa,
        id_material_base,
        codigo,
        nombre_material,
        descripcion,
        id_categoria,
        id_unidad_medida,
        precio,
        estado,
        es_propio,
        created_at,
        updated_at
    ) VALUES (
        p_id_empresa,
        p_id_material_base,
        TRIM(p_codigo),
        TRIM(p_nombre_material),
        NULLIF(TRIM(p_descripcion), ''),
        p_id_categoria,
        p_id_unidad_medida,
        COALESCE(p_precio, 0),
        'ACTIVO',
        v_es_propio,
        CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP
    )
    RETURNING id_material INTO v_id_material;

    RETURN v_id_material;
END;
$$ LANGUAGE plpgsql;

-- 7.2 Modificar material
CREATE OR REPLACE FUNCTION obras.fn_modificar_material(
    p_id_empresa INT,
    p_id_material INT,
    p_codigo VARCHAR,
    p_nombre_material VARCHAR,
    p_descripcion TEXT,
    p_id_categoria INT,
    p_id_unidad_medida INT,
    p_precio NUMERIC
)
RETURNS BOOLEAN AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM obras.t_material WHERE id_material = p_id_material AND id_empresa = p_id_empresa) THEN
        RAISE EXCEPTION 'Material no encontrado o no pertenece a la empresa %', p_id_empresa;
    END IF;

    IF TRIM(COALESCE(p_codigo, '')) = '' THEN
        RAISE EXCEPTION 'El código del material es obligatorio';
    END IF;

    IF TRIM(COALESCE(p_nombre_material, '')) = '' THEN
        RAISE EXCEPTION 'El nombre del material es obligatorio';
    END IF;

    IF EXISTS (
        SELECT 1 FROM obras.t_material 
        WHERE id_empresa = p_id_empresa 
          AND LOWER(TRIM(codigo)) = LOWER(TRIM(p_codigo)) 
          AND id_material <> p_id_material
    ) THEN
        RAISE EXCEPTION 'El código % ya está asignado a otro material en esta empresa', p_codigo;
    END IF;

    UPDATE obras.t_material
    SET codigo = TRIM(p_codigo),
        nombre_material = TRIM(p_nombre_material),
        descripcion = NULLIF(TRIM(p_descripcion), ''),
        id_categoria = p_id_categoria,
        id_unidad_medida = p_id_unidad_medida,
        precio = COALESCE(p_precio, precio),
        updated_at = CURRENT_TIMESTAMP
    WHERE id_material = p_id_material
      AND id_empresa = p_id_empresa;

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- 7.3 Consultar material individual
CREATE OR REPLACE FUNCTION obras.fn_consultar_material(
    p_id_empresa INT,
    p_id_material INT
)
RETURNS TABLE (
    id_material INT,
    codigo VARCHAR,
    nombre_material VARCHAR,
    descripcion TEXT,
    id_categoria INT,
    categoria_nombre VARCHAR,
    id_unidad_medida INT,
    unidad_nombre VARCHAR,
    unidad_abreviatura VARCHAR,
    precio NUMERIC,
    estado VARCHAR,
    id_empresa INT,
    nombre_empresa VARCHAR,
    id_material_base INT,
    es_propio BOOLEAN,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        m.id_material,
        m.codigo,
        m.nombre_material,
        m.descripcion,
        m.id_categoria,
        c.nombre AS categoria_nombre,
        m.id_unidad_medida,
        um.nombre AS unidad_nombre,
        um.abreviatura AS unidad_abreviatura,
        m.precio,
        m.estado,
        m.id_empresa,
        e.nombre_empresa,
        m.id_material_base,
        m.es_propio,
        m.created_at,
        m.updated_at
    FROM obras.t_material m
    JOIN obras.t_categoria_material c ON c.id_categoria = m.id_categoria
    JOIN obras.t_unidad_medida um ON um.id_unidad_medida = m.id_unidad_medida
    JOIN obras.t_empresa e ON e.id_empresa = m.id_empresa
    WHERE m.id_material = p_id_material
      AND (p_id_empresa IS NULL OR m.id_empresa = p_id_empresa);
END;
$$ LANGUAGE plpgsql;

-- 7.4 Listar materiales de una empresa
CREATE OR REPLACE FUNCTION obras.fn_listar_materiales_empresa(
    p_id_empresa INT,
    p_q VARCHAR DEFAULT NULL,
    p_id_categoria INT DEFAULT NULL,
    p_estado VARCHAR DEFAULT NULL,
    p_limit INT DEFAULT 50,
    p_offset INT DEFAULT 0
)
RETURNS TABLE (
    id_material INT,
    codigo VARCHAR,
    nombre_material VARCHAR,
    descripcion TEXT,
    id_categoria INT,
    categoria_nombre VARCHAR,
    id_unidad_medida INT,
    unidad_nombre VARCHAR,
    unidad_abreviatura VARCHAR,
    precio NUMERIC,
    estado VARCHAR,
    id_empresa INT,
    nombre_empresa VARCHAR,
    id_material_base INT,
    es_propio BOOLEAN,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ,
    total_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    WITH filtrados AS (
        SELECT 
            m.id_material,
            m.codigo,
            m.nombre_material,
            m.descripcion,
            m.id_categoria,
            c.nombre AS categoria_nombre,
            m.id_unidad_medida,
            um.nombre AS unidad_nombre,
            um.abreviatura AS unidad_abreviatura,
            m.precio,
            m.estado,
            m.id_empresa,
            e.nombre_empresa,
            m.id_material_base,
            m.es_propio,
            m.created_at,
            m.updated_at
        FROM obras.t_material m
        JOIN obras.t_categoria_material c ON c.id_categoria = m.id_categoria
        JOIN obras.t_unidad_medida um ON um.id_unidad_medida = m.id_unidad_medida
        JOIN obras.t_empresa e ON e.id_empresa = m.id_empresa
        WHERE (p_id_empresa IS NULL OR m.id_empresa = p_id_empresa)
          AND (p_id_categoria IS NULL OR m.id_categoria = p_id_categoria)
          AND (p_estado IS NULL OR m.estado = p_estado)
          AND (
              p_q IS NULL 
              OR m.codigo ILIKE '%' || p_q || '%' 
              OR m.nombre_material ILIKE '%' || p_q || '%'
          )
    )
    SELECT 
        f.*,
        COUNT(*) OVER() AS total_count
    FROM filtrados f
    ORDER BY f.nombre_material ASC, f.id_material ASC
    LIMIT p_limit OFFSET p_offset;
END;
$$ LANGUAGE plpgsql;

-- 7.5 Desactivar / activar material
CREATE OR REPLACE FUNCTION obras.fn_desactivar_material(
    p_id_empresa INT,
    p_id_material INT,
    p_nuevo_estado VARCHAR DEFAULT 'INACTIVO'
)
RETURNS BOOLEAN AS $$
BEGIN
    IF p_nuevo_estado NOT IN ('ACTIVO', 'INACTIVO') THEN
        RAISE EXCEPTION 'Estado no válido: %', p_nuevo_estado;
    END IF;

    UPDATE obras.t_material
    SET estado = p_nuevo_estado,
        updated_at = CURRENT_TIMESTAMP
    WHERE id_material = p_id_material
      AND (p_id_empresa IS NULL OR id_empresa = p_id_empresa);

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Material no encontrado o no pertenece a la empresa';
    END IF;

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- 7.6 Copiar catálogo base a una empresa
CREATE OR REPLACE FUNCTION obras.fn_copiar_catalogo_base_empresa(
    p_id_empresa INT
)
RETURNS INT AS $$
DECLARE
    v_insertados INT := 0;
BEGIN
    IF p_id_empresa IS NULL THEN
        RAISE EXCEPTION 'El id_empresa es obligatorio para inicializar el catálogo';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM obras.t_empresa WHERE id_empresa = p_id_empresa) THEN
        RAISE EXCEPTION 'La empresa % no existe', p_id_empresa;
    END IF;

    INSERT INTO obras.t_material (
        id_empresa,
        id_material_base,
        codigo,
        nombre_material,
        descripcion,
        id_categoria,
        id_unidad_medida,
        precio,
        estado,
        es_propio,
        created_at,
        updated_at
    )
    SELECT
        p_id_empresa,
        mb.id_material_base,
        mb.codigo,
        mb.nombre_material,
        mb.descripcion,
        mb.id_categoria,
        mb.id_unidad_medida,
        COALESCE(mb.precio_referencial, 0),
        'ACTIVO',
        FALSE,
        CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP
    FROM obras.t_material_base mb
    WHERE mb.estado = 'ACTIVO'
      AND NOT EXISTS (
          SELECT 1 FROM obras.t_material m
          WHERE m.id_empresa = p_id_empresa
            AND (m.id_material_base = mb.id_material_base OR LOWER(TRIM(m.codigo)) = LOWER(TRIM(mb.codigo)))
      );

    GET DIAGNOSTICS v_insertados = ROW_COUNT;
    RETURN v_insertados;
END;
$$ LANGUAGE plpgsql;

COMMIT;
