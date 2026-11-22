-- =============================================================================
-- MIGRACIÓN CU31 (FASE 1): Comercialización de Unidades Inmobiliarias
-- HUs asociadas: HU143, HU144, HU145, HU146
-- Migración aditiva y segura para el esquema obras
-- =============================================================================

-- 1. EXTENSIÓN COMERCIAL EN t_unidad_construccion (IMPORTANTE: estado constructivo NO se modifica)
ALTER TABLE obras.t_unidad_construccion
    ADD COLUMN IF NOT EXISTS publicado_comercial BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS precio_venta NUMERIC(15,2) NULL,
    ADD COLUMN IF NOT EXISTS moneda_comercial VARCHAR(10) NOT NULL DEFAULT 'BOB',
    ADD COLUMN IF NOT EXISTS descripcion_comercial TEXT NULL,
    ADD COLUMN IF NOT EXISTS estado_comercial VARCHAR(30) NOT NULL DEFAULT 'DISPONIBLE';

-- Restricción check para estado comercial de la unidad
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'chk_unidad_estado_comercial'
          AND conrelid = 'obras.t_unidad_construccion'::regclass
    ) THEN
        ALTER TABLE obras.t_unidad_construccion
            ADD CONSTRAINT chk_unidad_estado_comercial
            CHECK (estado_comercial IN ('DISPONIBLE', 'RESERVADA', 'VENDIDA', 'NO_DISPONIBLE'));
    END IF;
END $$;

-- Restricción check para precio de venta no negativo
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'chk_unidad_precio_comercial'
          AND conrelid = 'obras.t_unidad_construccion'::regclass
    ) THEN
        ALTER TABLE obras.t_unidad_construccion
            ADD CONSTRAINT chk_unidad_precio_comercial
            CHECK (precio_venta IS NULL OR precio_venta >= 0);
    END IF;
END $$;

-- Índices aditivos para optimización de consultas comerciales
CREATE INDEX IF NOT EXISTS idx_unidad_estado_comercial
    ON obras.t_unidad_construccion (estado_comercial);

CREATE INDEX IF NOT EXISTS idx_unidad_publicado_comercial
    ON obras.t_unidad_construccion (publicado_comercial);


-- 2. TABLA DE FOTOGRAFÍAS / GALERÍA DE MARKETING DE LA UNIDAD (HU143)
CREATE TABLE IF NOT EXISTS obras.t_unidad_fotografia (
    id_fotografia SERIAL PRIMARY KEY,
    id_unidad INT NOT NULL REFERENCES obras.t_unidad_construccion(id_unidad) ON DELETE CASCADE,
    ruta_archivo VARCHAR(500) NOT NULL,
    nombre_archivo VARCHAR(255) NOT NULL,
    tipo_mime VARCHAR(100),
    tamano_bytes INT,
    es_principal BOOLEAN NOT NULL DEFAULT FALSE,
    orden INT NOT NULL DEFAULT 1,
    id_usuario INT REFERENCES obras.t_usuario(id_usuario) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_unidad_fotografia_unidad
    ON obras.t_unidad_fotografia (id_unidad);

CREATE INDEX IF NOT EXISTS idx_unidad_fotografia_principal
    ON obras.t_unidad_fotografia (id_unidad, es_principal);


-- 3. TABLA DE HISTORIAL COMERCIAL DE LA UNIDAD (HU146)
CREATE TABLE IF NOT EXISTS obras.t_unidad_historial_comercial (
    id_historial SERIAL PRIMARY KEY,
    id_unidad INT NOT NULL REFERENCES obras.t_unidad_construccion(id_unidad) ON DELETE CASCADE,
    id_cliente INT REFERENCES obras.t_crm_cliente(id_cliente) ON DELETE SET NULL,
    id_cliente_unidad INT REFERENCES obras.t_crm_cliente_unidad(id_cliente_unidad) ON DELETE SET NULL,
    tipo_evento VARCHAR(40) NOT NULL,
    estado_anterior VARCHAR(30),
    estado_nuevo VARCHAR(30),
    precio_venta NUMERIC(15,2),
    monto_pactado NUMERIC(15,2),
    observacion TEXT,
    id_usuario INT REFERENCES obras.t_usuario(id_usuario) ON DELETE SET NULL,
    fecha TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_historial_comercial_unidad
    ON obras.t_unidad_historial_comercial (id_unidad);

CREATE INDEX IF NOT EXISTS idx_historial_comercial_cliente
    ON obras.t_unidad_historial_comercial (id_cliente);

CREATE INDEX IF NOT EXISTS idx_historial_comercial_fecha
    ON obras.t_unidad_historial_comercial (fecha DESC);


-- 4. CAMPOS ADICIONALES PARA RESERVAS EN t_crm_cliente_unidad (HU144)
ALTER TABLE obras.t_crm_cliente_unidad
    ADD COLUMN IF NOT EXISTS monto_reserva NUMERIC(15,2) NULL,
    ADD COLUMN IF NOT EXISTS fecha_vencimiento_reserva DATE NULL,
    ADD COLUMN IF NOT EXISTS id_usuario_registro INT REFERENCES obras.t_usuario(id_usuario) ON DELETE SET NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'chk_crm_cliente_unidad_monto_reserva'
          AND conrelid = 'obras.t_crm_cliente_unidad'::regclass
    ) THEN
        ALTER TABLE obras.t_crm_cliente_unidad
            ADD CONSTRAINT chk_crm_cliente_unidad_monto_reserva
            CHECK (monto_reserva IS NULL OR monto_reserva >= 0);
    END IF;
END $$;


-- 5. PERMISOS ADITIVOS PARA GESTIÓN COMERCIAL (CU31)
INSERT INTO obras.t_permiso (nombre_permiso, id_modulo)
SELECT 'Gestionar_comercializacion', m.id_modulo
FROM obras.t_modulo m
WHERE m.nombre_modulo = 'Modulo_crm'
  AND NOT EXISTS (
      SELECT 1 FROM obras.t_permiso WHERE nombre_permiso = 'Gestionar_comercializacion'
  );

INSERT INTO obras.t_rol_permiso (id_rol, id_permiso)
SELECT r.id_rol, p.id_permiso
FROM obras.t_rol r
CROSS JOIN obras.t_permiso p
WHERE r.nombre_rol IN ('ADMINISTRADOR', 'ADMINISTRADOR_EMPRESA', 'JEFE DE OBRA')
  AND p.nombre_permiso = 'Gestionar_comercializacion'
ON CONFLICT (id_rol, id_permiso) DO NOTHING;

-- 6. SINCRONIZACIÓN IDEMPOTENTE DE ESTADOS Y PRECIOS REALES DESDE t_crm_cliente_unidad
UPDATE obras.t_unidad_construccion u
SET estado_comercial = CASE
        WHEN cu.estado_asociacion IN ('VENDIDO', 'ENTREGADO') THEN 'VENDIDA'
        WHEN cu.estado_asociacion = 'RESERVADO' THEN 'RESERVADA'
        ELSE u.estado_comercial
    END,
    precio_venta = COALESCE(u.precio_venta, cu.monto_pactado)
FROM (
    SELECT DISTINCT ON (id_unidad)
        id_unidad,
        estado_asociacion,
        monto_pactado
    FROM obras.t_crm_cliente_unidad
    WHERE estado_asociacion IN ('ENTREGADO', 'VENDIDO', 'RESERVADO')
    ORDER BY id_unidad,
        CASE estado_asociacion
            WHEN 'ENTREGADO' THEN 1
            WHEN 'VENDIDO' THEN 2
            WHEN 'RESERVADO' THEN 3
            ELSE 4
        END,
        fecha_asociacion DESC
) cu
WHERE u.id_unidad = cu.id_unidad;
