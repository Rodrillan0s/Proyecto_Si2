-- =============================================================================
-- MIGRACIÓN PREPARADA CU34: Asistente Comercial Inteligente y Recomendaciones
-- HUs: HU147, HU148, HU149, HU150 | Proveedor: DeepSeek API
-- IMPORTANTE: Script aditivo e idempotente. Revisar antes de aplicar en el
-- entorno designado. El repositorio comercial funciona también sin aplicar
-- las columnas opcionales, derivando precios desde características o parámetros.
-- =============================================================================

BEGIN;

SET search_path TO obras, public;

-- 1. Parámetros referenciales de estilos de acabado en t_parametro_estimacion
INSERT INTO obras.t_parametro_estimacion (id_empresa, categoria, codigo_clave, nombre, valor_numerico, descripcion)
VALUES
    (NULL, 'FACTOR_ESTILO', 'ESTANDAR', 'Estilo Estándar Funcional', 1.0000, 'Acabados residenciales estándar: pisos cerámicos, carpintería convencional, grifería cromada clásica y pintura látex lavable.'),
    (NULL, 'FACTOR_ESTILO', 'MINIMALISTA', 'Estilo Moderno Minimalista', 1.1500, 'Porcelanato rectificado gran formato, mesones de cuarzo, perfiles de aluminio negro mate e iluminación LED empotrada (+15%).'),
    (NULL, 'FACTOR_ESTILO', 'INDUSTRIAL', 'Estilo Urbano Industrial', 1.1000, 'Hormigón visto sellado, detalles en acero estructural, ladrillo visto tratado, rieles de iluminación y carpintería metálica (+10%).'),
    (NULL, 'FACTOR_ESTILO', 'CONTEMPORANEO', 'Estilo Contemporáneo Cálido', 1.1800, 'Pisos de ingeniería o porcelanato maderado, revestimientos texturizados, vestidores modulares y ventanales DVH (+18%).'),
    (NULL, 'FACTOR_ESTILO', 'LUJO', 'Estilo Premium / Lujo Exclusivo', 1.3500, 'Mármol/piedra sinterizada, grifería de alta gama, domótica integral, climatización eficiente y carpintería laqueada a medida (+35%).')
ON CONFLICT (COALESCE(id_empresa, 0), categoria, codigo_clave) DO NOTHING;

-- 2. Columnas comerciales opcionales en t_unidad_construccion
ALTER TABLE obras.t_unidad_construccion
    ADD COLUMN IF NOT EXISTS precio_venta NUMERIC(14,2) NULL,
    ADD COLUMN IF NOT EXISTS moneda VARCHAR(10) NOT NULL DEFAULT 'BOB',
    ADD COLUMN IF NOT EXISTS disponible_comercial BOOLEAN NOT NULL DEFAULT TRUE;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_unidad_precio_venta_pos'
    ) THEN
        ALTER TABLE obras.t_unidad_construccion
            ADD CONSTRAINT chk_unidad_precio_venta_pos
            CHECK (precio_venta IS NULL OR precio_venta >= 0);
    END IF;
END $$;

-- 3. Columnas de distribución y plano referencial en t_modelo_unidad
ALTER TABLE obras.t_modelo_unidad
    ADD COLUMN IF NOT EXISTS ambientes_distribucion JSONB NULL,
    ADD COLUMN IF NOT EXISTS plano_url VARCHAR(300) NULL;

COMMIT;

