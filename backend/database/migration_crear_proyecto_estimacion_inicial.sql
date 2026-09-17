-- =============================================================================
-- MIGRACIÓN: CREAR PROYECTO CON ESTIMACIÓN INICIAL PARAMÉTRICA
-- =============================================================================
-- 1. Tabla de Parámetros Configurables para el Algoritmo de Estimación
-- 2. Población de Parámetros Referenciales para Construcción en Bolivia
-- 3. Tabla de Estimaciones Históricas Inmutables por Obra
-- =============================================================================

BEGIN;

SET search_path TO obras, public;

-- -----------------------------------------------------------------------------
-- 1. TABLA: t_parametro_estimacion
-- Permite configurar los costos referenciales y factores por categoría.
-- Soporta valores globales de la plataforma (id_empresa IS NULL) o específicos por constructora.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS obras.t_parametro_estimacion (
    id_parametro SERIAL PRIMARY KEY,
    id_empresa INT NULL REFERENCES obras.t_empresa(id_empresa) ON DELETE CASCADE,
    categoria VARCHAR(50) NOT NULL, 
    -- Categorías válidas: 'COSTO_M2_TIPO', 'FACTOR_NIVELES', 'FACTOR_TERRENO', 'FACTOR_COMPLEJIDAD'
    codigo_clave VARCHAR(50) NOT NULL, 
    -- Claves: 'VIVIENDA', 'EDIFICIO', '1_2', 'FIRME', 'BAJO', etc.
    nombre VARCHAR(100) NOT NULL,
    valor_numerico NUMERIC(15,4) NOT NULL,
    descripcion TEXT,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_param_empresa_categoria_clave 
ON obras.t_parametro_estimacion (COALESCE(id_empresa, 0), categoria, codigo_clave);

CREATE INDEX IF NOT EXISTS idx_parametro_cat_clave 
ON obras.t_parametro_estimacion (categoria, codigo_clave, activo);


-- -----------------------------------------------------------------------------
-- 2. POBLACIÓN DE PARÁMETROS REFERENCIALES BASE DE LA PLATAFORMA (BOLIVIA)
-- -----------------------------------------------------------------------------
INSERT INTO obras.t_parametro_estimacion (id_empresa, categoria, codigo_clave, nombre, valor_numerico, descripcion)
VALUES
    -- A) Costo referencial por m² según tipo de obra (en Bolivianos - BOB)
    (NULL, 'COSTO_M2_TIPO', 'VIVIENDA', 'Vivienda unifamiliar / pareada', 2800.0000, 'Construcción residencial tradicional con losas, muros cerámicos y acabados estándar en Bolivia (~400 USD/m²)'),
    (NULL, 'COSTO_M2_TIPO', 'EDIFICIO', 'Edificio residencial / oficinas', 3500.0000, 'Estructura en altura de hormigón armado, ascensores, fundaciones profundas e instalaciones especiales (~500 USD/m²)'),
    (NULL, 'COSTO_M2_TIPO', 'COMERCIAL', 'Comercial / Tiendas / Centros comerciales', 3200.0000, 'Espacios comerciales con vanos amplios, vidriados de seguridad y circulación peatonal (~460 USD/m²)'),
    (NULL, 'COSTO_M2_TIPO', 'INDUSTRIAL', 'Industrial / Galpones / Tinglados', 2400.0000, 'Estructuras metálicas, losas de alta carga y cubiertas de calamina con aislamiento (~345 USD/m²)'),
    (NULL, 'COSTO_M2_TIPO', 'OTRO', 'Otro tipo de obra civil', 2500.0000, 'Obras civiles diversas y construcciones no tipificadas (~360 USD/m²)'),

    -- B) Factor de niveles (según cantidad de pisos / altura)
    (NULL, 'FACTOR_NIVELES', '1_2', '1 a 2 niveles', 1.0000, 'Construcción a nivel de rasante o planta baja + 1 piso sin requerimientos complejos de izaje'),
    (NULL, 'FACTOR_NIVELES', '3_5', '3 a 5 niveles', 1.0800, 'Izaje menor, andamiaje extendido y seguridad en altura (+8%)'),
    (NULL, 'FACTOR_NIVELES', '6_10', '6 a 10 niveles', 1.1500, 'Bombeo de hormigón a presión, grúas pluma y fundaciones reforzadas (+15%)'),
    (NULL, 'FACTOR_NIVELES', 'MAS_10', 'Más de 10 niveles', 1.2500, 'Alta ingeniería vertical, elevadores de carga y logística de altura (+25%)'),

    -- C) Factor de terreno (según mecánica de suelos)
    (NULL, 'FACTOR_TERRENO', 'FIRME', 'Terreno Firme (Gravoso / Cohesivo bueno)', 1.0000, 'Suelo con buena capacidad portante, excavación sencilla y zapatas aisladas normales'),
    (NULL, 'FACTOR_TERRENO', 'ARCILLOSO', 'Terreno Arcilloso (Expansivo / Blando)', 1.1500, 'Requiere mejoramiento de suelo, losas de fundación o vigas de atado (+15%)'),
    (NULL, 'FACTOR_TERRENO', 'ARENOSO', 'Terreno Arenoso (Inestable / Friccionante)', 1.0800, 'Requiere entibados temporales y zapatas continuas combinadas (+8%)'),
    (NULL, 'FACTOR_TERRENO', 'ROCOSO', 'Terreno Rocoso (Semiduro / Duro)', 1.1200, 'Alta resistencia pero alta dificultad y costo de excavación con compresor/martillo (+12%)'),
    (NULL, 'FACTOR_TERRENO', 'OTRO', 'Otro tipo de suelo', 1.0500, 'Suelos mixtos o con características especiales (+5%)'),

    -- D) Factor de complejidad constructiva
    (NULL, 'FACTOR_COMPLEJIDAD', 'BAJO', 'Bajo (Diseño regular ortogonal)', 1.0000, 'Diseño simétrico, luces cortas, acabados estándar de plaza'),
    (NULL, 'FACTOR_COMPLEJIDAD', 'MEDIO', 'Medio (Diseño contemporáneo)', 1.1000, 'Luces intermedias, vanos generosos, acabados de primera calidad (+10%)'),
    (NULL, 'FACTOR_COMPLEJIDAD', 'ALTO', 'Alto (Diseño singular / Premium)', 1.2500, 'Voladizos estructurales, doble altura, instalaciones de climatización central y acabados de lujo (+25%)')
ON CONFLICT DO NOTHING;


-- -----------------------------------------------------------------------------
-- 3. TABLA: t_obra_estimacion
-- Almacena la estimación inicial generada asociada a la obra.
-- Conserva inmutablemente los requisitos, parámetros y factores utilizados.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS obras.t_obra_estimacion (
    id_estimacion SERIAL PRIMARY KEY,
    id_obra INT NOT NULL REFERENCES obras.t_obra(id_obra) ON DELETE CASCADE,
    tipo_obra VARCHAR(100) NOT NULL,
    superficie_m2 NUMERIC(12,2) NOT NULL,
    niveles INT NOT NULL DEFAULT 1,
    tipo_terreno VARCHAR(100) NOT NULL,
    complejidad VARCHAR(50) NOT NULL,
    ubicacion VARCHAR(255) NULL,
    caracteristicas_generales TEXT NULL,

    -- Parámetros y factores congelados (Snapshot inmutable)
    costo_referencial_m2 NUMERIC(15,2) NOT NULL,
    factor_niveles NUMERIC(8,4) NOT NULL,
    factor_terreno NUMERIC(8,4) NOT NULL,
    factor_complejidad NUMERIC(8,4) NOT NULL,

    -- Montos calculados
    costo_base NUMERIC(15,2) NOT NULL,
    monto_estimado NUMERIC(15,2) NOT NULL,
    moneda VARCHAR(10) NOT NULL DEFAULT 'BOB',

    fecha_estimacion TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_obra_estimacion_obra 
ON obras.t_obra_estimacion (id_obra);

COMMIT;
