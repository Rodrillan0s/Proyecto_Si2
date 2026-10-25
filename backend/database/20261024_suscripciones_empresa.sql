-- Suscripciones manuales. Sin pagos ni cambios de permisos existentes.
CREATE TABLE IF NOT EXISTS obras.t_plan_suscripcion (
    codigo varchar(20) PRIMARY KEY,
    nombre varchar(80) NOT NULL,
    descripcion text NOT NULL,
    prestaciones jsonb NOT NULL CHECK (jsonb_typeof(prestaciones) = 'array'),
    orden integer NOT NULL UNIQUE
);
INSERT INTO obras.t_plan_suscripcion (codigo, nombre, descripcion, prestaciones, orden) VALUES
('BASICO', 'Básico', 'Organización inicial para una empresa constructora.', '["Organización de proyectos", "Usuarios y roles de la empresa", "Seguimiento operativo"]', 1),
('PROFESIONAL', 'Profesional', 'Gestión integral para equipos en crecimiento.', '["Todo lo incluido en Básico", "Presupuestos y control de costos", "Compras e inventario"]', 2),
('EMPRESARIAL', 'Empresarial', 'Coordinación empresarial y seguimiento comercial.', '["Todo lo incluido en Profesional", "Gestión comercial CRM", "Reportes y seguimiento gerencial"]', 3)
ON CONFLICT (codigo) DO NOTHING;

CREATE TABLE IF NOT EXISTS obras.t_suscripcion_empresa (
    id_empresa integer PRIMARY KEY REFERENCES obras.t_empresa(id_empresa) ON DELETE CASCADE,
    codigo_plan varchar(20) NOT NULL REFERENCES obras.t_plan_suscripcion(codigo),
    estado varchar(15) NOT NULL CHECK (estado IN ('ACTIVA', 'SUSPENDIDA', 'CANCELADA')),
    fecha_inicio date NOT NULL,
    fecha_fin date,
    actualizado_por integer REFERENCES obras.t_usuario(id_usuario) ON DELETE SET NULL,
    actualizado_en timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (fecha_fin IS NULL OR fecha_fin >= fecha_inicio)
);
CREATE TABLE IF NOT EXISTS obras.t_suscripcion_historial (
    id bigserial PRIMARY KEY,
    id_empresa integer NOT NULL REFERENCES obras.t_empresa(id_empresa) ON DELETE CASCADE,
    codigo_plan varchar(20) NOT NULL REFERENCES obras.t_plan_suscripcion(codigo),
    estado varchar(15) NOT NULL CHECK (estado IN ('ACTIVA', 'SUSPENDIDA', 'CANCELADA')),
    fecha_inicio date NOT NULL,
    fecha_fin date,
    id_actor integer REFERENCES obras.t_usuario(id_usuario) ON DELETE SET NULL,
    origen varchar(30) NOT NULL DEFAULT 'ADMINISTRACION',
    creado_en timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (fecha_fin IS NULL OR fecha_fin >= fecha_inicio)
);
CREATE INDEX IF NOT EXISTS idx_suscripcion_historial_empresa ON obras.t_suscripcion_historial(id_empresa, creado_en DESC, id DESC);
