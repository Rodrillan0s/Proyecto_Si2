-- =============================================================================
-- MIGRACIÓN CU21: CRM (Clientes, Prospectos, Interacciones, Asociación Unidades)
-- =============================================================================

-- 1. Modulo CRM
INSERT INTO obras.t_modulo (nombre_modulo)
SELECT 'Modulo_crm'
WHERE NOT EXISTS (SELECT 1 FROM obras.t_modulo WHERE nombre_modulo = 'Modulo_crm');

-- 2. Permisos CRM
INSERT INTO obras.t_permiso (nombre_permiso, id_modulo)
SELECT 'Visualizar_clientes', m.id_modulo
FROM obras.t_modulo m
WHERE m.nombre_modulo = 'Modulo_crm'
  AND NOT EXISTS (SELECT 1 FROM obras.t_permiso WHERE nombre_permiso = 'Visualizar_clientes');

INSERT INTO obras.t_permiso (nombre_permiso, id_modulo)
SELECT 'Registrar_clientes', m.id_modulo
FROM obras.t_modulo m
WHERE m.nombre_modulo = 'Modulo_crm'
  AND NOT EXISTS (SELECT 1 FROM obras.t_permiso WHERE nombre_permiso = 'Registrar_clientes');

INSERT INTO obras.t_permiso (nombre_permiso, id_modulo)
SELECT 'Modificar_clientes', m.id_modulo
FROM obras.t_modulo m
WHERE m.nombre_modulo = 'Modulo_crm'
  AND NOT EXISTS (SELECT 1 FROM obras.t_permiso WHERE nombre_permiso = 'Modificar_clientes');

-- 3. Asignación a Roles (ADMINISTRADOR, ADMINISTRADOR_EMPRESA, JEFE DE OBRA)
INSERT INTO obras.t_rol_permiso (id_rol, id_permiso)
SELECT r.id_rol, p.id_permiso
FROM obras.t_rol r
CROSS JOIN obras.t_permiso p
WHERE r.nombre_rol IN ('ADMINISTRADOR', 'ADMINISTRADOR_EMPRESA', 'JEFE DE OBRA')
  AND p.nombre_permiso IN ('Visualizar_clientes', 'Registrar_clientes', 'Modificar_clientes')
ON CONFLICT (id_rol, id_permiso) DO NOTHING;

-- 4. Tabla Clientes y Prospectos CRM
CREATE TABLE IF NOT EXISTS obras.t_crm_cliente (
    id_cliente SERIAL PRIMARY KEY,
    id_empresa INT NOT NULL REFERENCES obras.t_empresa(id_empresa) ON DELETE CASCADE,
    id_persona INT NOT NULL REFERENCES obras.t_persona(id_persona) ON DELETE RESTRICT,
    email VARCHAR(150),
    tipo_cliente VARCHAR(20) NOT NULL DEFAULT 'PROSPECTO',
    estado VARCHAR(30) NOT NULL DEFAULT 'NUEVO',
    origen VARCHAR(50) DEFAULT 'DIRECTO',
    presupuesto_estimado NUMERIC(15,2) DEFAULT NULL,
    notas TEXT,
    id_usuario_asignado INT REFERENCES obras.t_usuario(id_usuario) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_crm_empresa_persona UNIQUE (id_empresa, id_persona),
    CONSTRAINT chk_crm_tipo_estado CHECK (
        (tipo_cliente = 'PROSPECTO' AND estado IN ('NUEVO', 'CONTACTADO', 'INTERESADO', 'EN_NEGOCIACION', 'CONVERTIDO', 'PERDIDO'))
        OR
        (tipo_cliente = 'CLIENTE' AND estado IN ('ACTIVO', 'INACTIVO'))
    )
);

-- Trigger de updated_at para cliente
DROP TRIGGER IF EXISTS tg_crm_actualizar_cliente ON obras.t_crm_cliente;
CREATE TRIGGER tg_crm_actualizar_cliente
BEFORE UPDATE ON obras.t_crm_cliente
FOR EACH ROW EXECUTE FUNCTION obras.fn_actualizar_updated_at();

-- 5. Tabla de Interacciones Comerciales (HU84, HU81)
CREATE TABLE IF NOT EXISTS obras.t_crm_interaccion (
    id_interaccion SERIAL PRIMARY KEY,
    id_cliente INT NOT NULL REFERENCES obras.t_crm_cliente(id_cliente) ON DELETE CASCADE,
    id_usuario INT NOT NULL REFERENCES obras.t_usuario(id_usuario) ON DELETE RESTRICT,
    tipo VARCHAR(30) NOT NULL,
    asunto VARCHAR(200) NOT NULL,
    detalle TEXT NOT NULL,
    fecha_interaccion TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_proximo_contacto TIMESTAMPTZ DEFAULT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 6. Tabla de Asociación Cliente ↔ Unidad Inmobiliaria (HU85)
CREATE TABLE IF NOT EXISTS obras.t_crm_cliente_unidad (
    id_cliente_unidad SERIAL PRIMARY KEY,
    id_cliente INT NOT NULL REFERENCES obras.t_crm_cliente(id_cliente) ON DELETE CASCADE,
    id_unidad INT NOT NULL REFERENCES obras.t_unidad_construccion(id_unidad) ON DELETE RESTRICT,
    estado_asociacion VARCHAR(30) NOT NULL DEFAULT 'INTERESADO',
    monto_pactado NUMERIC(15,2) DEFAULT NULL,
    fecha_asociacion TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    observaciones TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_crm_estado_asociacion CHECK (
        estado_asociacion IN ('INTERESADO', 'RESERVADO', 'VENDIDO', 'ENTREGADO', 'CANCELADO')
    )
);

-- Trigger de updated_at para cliente_unidad
DROP TRIGGER IF EXISTS tg_crm_actualizar_cliente_unidad ON obras.t_crm_cliente_unidad;
CREATE TRIGGER tg_crm_actualizar_cliente_unidad
BEFORE UPDATE ON obras.t_crm_cliente_unidad
FOR EACH ROW EXECUTE FUNCTION obras.fn_actualizar_updated_at();

-- 7. Índices de unicidad parcial
-- A) Una unidad no puede tener dos reservas o ventas activas simultáneamente:
CREATE UNIQUE INDEX IF NOT EXISTS uq_crm_unidad_reservada_vendida
ON obras.t_crm_cliente_unidad (id_unidad)
WHERE estado_asociacion IN ('RESERVADO', 'VENDIDO');

-- B) Un cliente no puede tener dos negociaciones activas duplicadas sobre la misma unidad:
CREATE UNIQUE INDEX IF NOT EXISTS uq_crm_cliente_unidad_activa
ON obras.t_crm_cliente_unidad (id_cliente, id_unidad)
WHERE estado_asociacion IN ('INTERESADO', 'RESERVADO', 'VENDIDO');
