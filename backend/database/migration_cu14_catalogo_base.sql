-- =============================================================================
-- MIGRACIÓN CU14: REDEFINICIÓN DE CATÁLOGO BASE DE LA PLATAFORMA Y EMPRESA
-- =============================================================================

BEGIN;

SET search_path TO obras, public;

-- -----------------------------------------------------------------------------
-- 1. CATEGORÍAS ESTÁNDAR DE MATERIALES EN BOLIVIA
-- -----------------------------------------------------------------------------
INSERT INTO obras.t_categoria_material (nombre, descripcion, estado)
SELECT cat.nombre, cat.descripcion, 'ACTIVO'
FROM (
    VALUES 
        ('Cementos y aglomerantes', 'Cementos, yesos, cales y aglutinantes de construcción'),
        ('Agregados', 'Arenas, gravas, ripios y piedras para mezclas y bases'),
        ('Mampostería', 'Ladrillos cerámicos, bloques de hormigón y adobe'),
        ('Acero y metálicos', 'Fierros corrugados, alambres, perfiles y mallas electrosoldadas'),
        ('Madera', 'Tablas, tablones, listones, vigas y tableros estructurales'),
        ('Cubiertas', 'Calaminas, tejas cerámicas, fibrocemento y policarbonatos'),
        ('Instalaciones', 'Tuberías sanitarias, de presión, accesorios y material eléctrico'),
        ('Acabados', 'Revestimientos cerámicos, porcelanatos, pinturas y pegamentos')
) AS cat(nombre, descripcion)
WHERE NOT EXISTS (
    SELECT 1 FROM obras.t_categoria_material WHERE LOWER(TRIM(nombre)) = LOWER(TRIM(cat.nombre))
);


-- -----------------------------------------------------------------------------
-- 2. TABLA: t_material_base (Catálogo Maestro de la Plataforma)
-- Materiales comunes que cualquier constructora puede adoptar.
-- No pertenecen a ninguna empresa en particular.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS obras.t_material_base (
    id_material_base SERIAL PRIMARY KEY,
    codigo VARCHAR(50) NOT NULL,
    nombre_material VARCHAR(200) NOT NULL,
    descripcion TEXT,
    id_categoria INT NOT NULL REFERENCES obras.t_categoria_material(id_categoria),
    id_unidad_medida INT NOT NULL REFERENCES obras.t_unidad_medida(id_unidad_medida),
    precio_referencial NUMERIC(15,2) DEFAULT NULL, -- Precio referencial en BOB
    estado VARCHAR(20) NOT NULL DEFAULT 'ACTIVO',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_material_base_codigo UNIQUE (codigo),
    CONSTRAINT chk_material_base_estado CHECK (estado IN ('ACTIVO', 'INACTIVO'))
);

CREATE INDEX IF NOT EXISTS idx_material_base_cat ON obras.t_material_base(id_categoria);
CREATE INDEX IF NOT EXISTS idx_material_base_um ON obras.t_material_base(id_unidad_medida);


-- -----------------------------------------------------------------------------
-- 3. POBLACIÓN DEL CATÁLOGO BASE DE BOLIVIA
-- -----------------------------------------------------------------------------
DO $$
DECLARE
    -- Categorías
    c_cem INT; c_agr INT; c_mam INT; c_ace INT;
    c_mad INT; c_cub INT; c_ins INT; c_aca INT;
    -- Unidades
    u_bolsa INT; u_kg INT; u_m INT; u_m2 INT; u_m3 INT; u_u INT; u_barra INT;
BEGIN
    SELECT id_categoria INTO c_cem FROM obras.t_categoria_material WHERE LOWER(TRIM(nombre)) = 'cementos y aglomerantes' LIMIT 1;
    SELECT id_categoria INTO c_agr FROM obras.t_categoria_material WHERE LOWER(TRIM(nombre)) = 'agregados' LIMIT 1;
    SELECT id_categoria INTO c_mam FROM obras.t_categoria_material WHERE LOWER(TRIM(nombre)) = 'mampostería' LIMIT 1;
    SELECT id_categoria INTO c_ace FROM obras.t_categoria_material WHERE LOWER(TRIM(nombre)) = 'acero y metálicos' LIMIT 1;
    SELECT id_categoria INTO c_mad FROM obras.t_categoria_material WHERE LOWER(TRIM(nombre)) = 'madera' LIMIT 1;
    SELECT id_categoria INTO c_cub FROM obras.t_categoria_material WHERE LOWER(TRIM(nombre)) = 'cubiertas' LIMIT 1;
    SELECT id_categoria INTO c_ins FROM obras.t_categoria_material WHERE LOWER(TRIM(nombre)) = 'instalaciones' LIMIT 1;
    SELECT id_categoria INTO c_aca FROM obras.t_categoria_material WHERE LOWER(TRIM(nombre)) = 'acabados' LIMIT 1;

    SELECT id_unidad_medida INTO u_bolsa FROM obras.t_unidad_medida WHERE LOWER(TRIM(nombre)) = 'bolsa' LIMIT 1;
    SELECT id_unidad_medida INTO u_kg FROM obras.t_unidad_medida WHERE LOWER(TRIM(nombre)) = 'kilogramo' LIMIT 1;
    SELECT id_unidad_medida INTO u_m FROM obras.t_unidad_medida WHERE LOWER(TRIM(nombre)) = 'metro' LIMIT 1;
    SELECT id_unidad_medida INTO u_m2 FROM obras.t_unidad_medida WHERE LOWER(TRIM(nombre)) = 'metro cuadrado' LIMIT 1;
    SELECT id_unidad_medida INTO u_m3 FROM obras.t_unidad_medida WHERE LOWER(TRIM(nombre)) = 'metro cúbico' OR LOWER(TRIM(abreviatura)) = 'm3' LIMIT 1;
    SELECT id_unidad_medida INTO u_u FROM obras.t_unidad_medida WHERE LOWER(TRIM(nombre)) = 'unidad' LIMIT 1;
    SELECT id_unidad_medida INTO u_barra FROM obras.t_unidad_medida WHERE LOWER(TRIM(nombre)) = 'barra' LIMIT 1;

    -- A) Cementos y aglomerantes
    INSERT INTO obras.t_material_base (codigo, nombre_material, descripcion, id_categoria, id_unidad_medida, precio_referencial)
    VALUES
        ('BASE-CEM-01', 'Cemento Portland', 'Cemento Portland estándar de uso general en obra', c_cem, u_bolsa, 50.00),
        ('BASE-CEM-02', 'Cemento IP', 'Cemento con puzolana para hormigones y albañilería', c_cem, u_bolsa, 48.00),
        ('BASE-CEM-03', 'Cemento IP-30', 'Cemento estructural de alta resistencia normalizada IP-30', c_cem, u_bolsa, 52.00),
        ('BASE-CEM-04', 'Cemento IP-40', 'Cemento de alta resistencia inicial para obras civiles mayores', c_cem, u_bolsa, 56.00),
        ('BASE-CEM-05', 'Cal hidratada', 'Cal para revoques, mampostería y mezclas tradicionales', c_cem, u_bolsa, 25.00),
        ('BASE-CEM-06', 'Yeso de construcción', 'Yeso para enlucidos interiores y cielo raso', c_cem, u_bolsa, 22.00)
    ON CONFLICT (codigo) DO NOTHING;

    -- B) Agregados
    INSERT INTO obras.t_material_base (codigo, nombre_material, descripcion, id_categoria, id_unidad_medida, precio_referencial)
    VALUES
        ('BASE-AGR-01', 'Arena fina', 'Arena lavada cernida para revoques y morteros', c_agr, u_m3, 110.00),
        ('BASE-AGR-02', 'Arena gruesa', 'Arena para hormigones y contrapisos', c_agr, u_m3, 95.00),
        ('BASE-AGR-03', 'Grava común', 'Grava rodada limpia para hormigón armado', c_agr, u_m3, 120.00),
        ('BASE-AGR-04', 'Ripio clasificado', 'Ripio triturado para mezclas estructurales', c_agr, u_m3, 130.00),
        ('BASE-AGR-05', 'Piedra bruta', 'Piedra manzana/bruta para cimientos ciclópeos y muros', c_agr, u_m3, 90.00),
        ('BASE-AGR-06', 'Piedra triturada', 'Piedra chancada para sub-base y drenajes', c_agr, u_m3, 115.00)
    ON CONFLICT (codigo) DO NOTHING;

    -- C) Mampostería
    INSERT INTO obras.t_material_base (codigo, nombre_material, descripcion, id_categoria, id_unidad_medida, precio_referencial)
    VALUES
        ('BASE-MAM-01', 'Ladrillo cerámico 6 huecos', 'Ladrillo hueco estándar para muros divisorios (24x15x18)', c_mam, u_u, 0.95),
        ('BASE-MAM-02', 'Ladrillo cerámico 3 huecos', 'Ladrillo caravista / tabique de 3 perforaciones', c_mam, u_u, 1.20),
        ('BASE-MAM-03', 'Ladrillo gambote macizo', 'Ladrillo adobito macizo cocido para muros portantes', c_mam, u_u, 0.70),
        ('BASE-MAM-04', 'Bloque de hormigón', 'Bloque hueco de cemento y arena para muros perimetrales', c_mam, u_u, 4.50),
        ('BASE-MAM-05', 'Bloque de cemento macizo', 'Bloque pesado para sobrecimientos y contenciones', c_mam, u_u, 5.00),
        ('BASE-MAM-06', 'Adobe tradicional', 'Bloque de barro y paja secado al sol', c_mam, u_u, 0.80)
    ON CONFLICT (codigo) DO NOTHING;

    -- D) Acero y metálicos
    INSERT INTO obras.t_material_base (codigo, nombre_material, descripcion, id_categoria, id_unidad_medida, precio_referencial)
    VALUES
        ('BASE-ACE-01', 'Fierro corrugado 6 mm', 'Barra corrugada ASTM A706 / CBH 87 de 12 metros', c_ace, u_barra, 28.00),
        ('BASE-ACE-02', 'Fierro corrugado 8 mm', 'Barra corrugada para estribos y losas de 12 metros', c_ace, u_barra, 45.00),
        ('BASE-ACE-03', 'Fierro corrugado 10 mm', 'Barra corrugada estructural de 12 metros', c_ace, u_barra, 70.00),
        ('BASE-ACE-04', 'Fierro corrugado 12 mm', 'Barra corrugada estructural de 12 metros', c_ace, u_barra, 100.00),
        ('BASE-ACE-05', 'Fierro corrugado 16 mm', 'Barra corrugada pesada para columnas y vigas', c_ace, u_barra, 175.00),
        ('BASE-ACE-06', 'Alambre de amarre #16', 'Alambre recocido dulce para enfierradura', c_ace, u_kg, 12.00),
        ('BASE-ACE-07', 'Malla electrosoldada 15x15', 'Malla electrosoldada de alambre para contrapiso y losas', c_ace, u_m2, 22.00),
        ('BASE-ACE-08', 'Perfil metálico Costanera', 'Perfil de acero conformado en frío 100x50x15x2 mm', c_ace, u_barra, 140.00)
    ON CONFLICT (codigo) DO NOTHING;

    -- E) Madera
    INSERT INTO obras.t_material_base (codigo, nombre_material, descripcion, id_categoria, id_unidad_medida, precio_referencial)
    VALUES
        ('BASE-MAD-01', 'Tabla de madera semidura', 'Tabla de encofrado 1" x 8" x 3m', c_mad, u_u, 35.00),
        ('BASE-MAD-02', 'Tablón de madera', 'Tablón para andamio y pasarelas 2" x 10" x 3m', c_mad, u_u, 75.00),
        ('BASE-MAD-03', 'Listón de madera', 'Listón para cerchas y arriostre 2" x 2" x 3m', c_mad, u_u, 18.00),
        ('BASE-MAD-04', 'Viga de madera estructural', 'Viga para envigado de techo 2" x 6" x 4m', c_mad, u_u, 110.00),
        ('BASE-MAD-05', 'Madera terciada fenólico 15mm', 'Placa multilaminada para encofrado caravista', c_mad, u_u, 210.00),
        ('BASE-MAD-06', 'Machimbre de pino / tajibo', 'Piso machihembrado pulido de madera', c_mad, u_m2, 85.00)
    ON CONFLICT (codigo) DO NOTHING;

    -- F) Cubiertas
    INSERT INTO obras.t_material_base (codigo, nombre_material, descripcion, id_categoria, id_unidad_medida, precio_referencial)
    VALUES
        ('BASE-CUB-01', 'Calamina galvanizada #28', 'Calamina trapezoidal cincada de 3.0 m', c_cub, u_u, 75.00),
        ('BASE-CUB-02', 'Calamina ondulada #28', 'Calamina acanalada estándar para tinglados', c_cub, u_u, 70.00),
        ('BASE-CUB-03', 'Teja cerámica colonial', 'Teja de arcilla cocida tipo española', c_cub, u_u, 2.50),
        ('BASE-CUB-04', 'Teja de fibrocemento', 'Placa ondulada sin asbesto de 2.44 m', c_cub, u_u, 65.00),
        ('BASE-CUB-05', 'Policarbonato alveolar 6mm', 'Plancha traslúcida con protección UV para claraboyas', c_cub, u_m2, 90.00)
    ON CONFLICT (codigo) DO NOTHING;

    -- G) Instalaciones
    INSERT INTO obras.t_material_base (codigo, nombre_material, descripcion, id_categoria, id_unidad_medida, precio_referencial)
    VALUES
        ('BASE-INS-01', 'Tubo PVC sanitario 4"', 'Tubo de desagüe pluvial y servidas campana 4m', c_ins, u_barra, 85.00),
        ('BASE-INS-02', 'Tubo PVC presión 1/2"', 'Tubo de agua potable rosca o encolar SDR-13.5 6m', c_ins, u_barra, 32.00),
        ('BASE-INS-03', 'Tubo PPR termofusión 20mm', 'Tubería de polipropileno para agua fría y caliente 4m', c_ins, u_barra, 45.00),
        ('BASE-INS-04', 'Codo PVC sanitario 4" x 90°', 'Accesorio de desagüe sanitario', c_ins, u_u, 14.00),
        ('BASE-INS-05', 'Tee PVC sanitaria 4"', 'Accesorio de derivación sanitaria', c_ins, u_u, 22.00),
        ('BASE-INS-06', 'Unión PVC presión 1/2"', 'Accesorio para unión de agua potable', c_ins, u_u, 4.50),
        ('BASE-INS-07', 'Cable eléctrico monopolar 2.5 mm2', 'Conductor de cobre aislado para circuito de tomas e iluminación', c_ins, u_m, 4.20),
        ('BASE-INS-08', 'Conduit PVC eléctrico 3/4"', 'Tubo conduit liviano para cableado empotrado 3m', c_ins, u_barra, 12.00),
        ('BASE-INS-09', 'Caja eléctrica rectangular 4x2', 'Caja plástica o metálica para interruptores y enchufes', c_ins, u_u, 3.00)
    ON CONFLICT (codigo) DO NOTHING;

    -- H) Acabados
    INSERT INTO obras.t_material_base (codigo, nombre_material, descripcion, id_categoria, id_unidad_medida, precio_referencial)
    VALUES
        ('BASE-ACA-01', 'Cerámica esmaltada para piso', 'Piso cerámico tráfico medio/alto 45x45', c_aca, u_m2, 55.00),
        ('BASE-ACA-02', 'Porcelanato pulido 60x60', 'Revestimiento pulido rectificado de alta resistencia', c_aca, u_m2, 110.00),
        ('BASE-ACA-03', 'Azulejo blanco brillante 20x30', 'Revestimiento para baños y cocinas', c_aca, u_m2, 48.00),
        ('BASE-ACA-04', 'Piso flotante laminado 8mm', 'Piso melamínico HDF tipo madera con manta aislante', c_aca, u_m2, 75.00),
        ('BASE-ACA-05', 'Cemento para contrapiso', 'Mezcla seca predosificada para nivelación de piso', c_aca, u_bolsa, 42.00),
        ('BASE-ACA-06', 'Pintura látex interior', 'Pintura vinílica lavable acabado mate', c_aca, u_u, 140.00),
        ('BASE-ACA-07', 'Pintura acrílica exterior', 'Pintura hidrorrepelente para fachadas', c_aca, u_u, 195.00),
        ('BASE-ACA-08', 'Sellador fijador de muros', 'Imprimante para preparación de superficies de revoque', c_aca, u_u, 60.00),
        ('BASE-ACA-09', 'Adhesivo cementicio para cerámica', 'Pegamento en polvo base cemento gris', c_aca, u_bolsa, 28.00),
        ('BASE-ACA-10', 'Pastina para juntas', 'Emboquillador impermeable para fraguado de baldosas', c_aca, u_kg, 8.00)
    ON CONFLICT (codigo) DO NOTHING;

END $$;


-- -----------------------------------------------------------------------------
-- 4. VINCULAR t_material CON EL CATÁLOGO BASE
-- -----------------------------------------------------------------------------
ALTER TABLE obras.t_material 
    ADD COLUMN IF NOT EXISTS id_material_base INT REFERENCES obras.t_material_base(id_material_base) ON DELETE SET NULL;

ALTER TABLE obras.t_material 
    ADD COLUMN IF NOT EXISTS es_propio BOOLEAN NOT NULL DEFAULT FALSE;

-- Restricción para evitar que una empresa adopte dos veces el mismo material base
CREATE UNIQUE INDEX IF NOT EXISTS uq_empresa_material_base 
ON obras.t_material (id_empresa, id_material_base) 
WHERE (id_material_base IS NOT NULL);

COMMIT;
