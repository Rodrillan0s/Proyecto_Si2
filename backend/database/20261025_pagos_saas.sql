-- CU37 Fase 1: configuración comercial y pagos de suscripciones.
-- Migración preparada; no ejecutarla sin una base explícitamente designada.

CREATE TABLE IF NOT EXISTS obras.t_plan_precio_saas (
    codigo_plan varchar(20) PRIMARY KEY
        REFERENCES obras.t_plan_suscripcion(codigo) ON DELETE RESTRICT,
    precio_menor bigint NOT NULL CHECK (precio_menor > 0),
    moneda varchar(3) NOT NULL CHECK (moneda = upper(moneda)),
    periodo_meses smallint NOT NULL DEFAULT 1 CHECK (periodo_meses > 0),
    activo boolean NOT NULL DEFAULT true,
    version integer NOT NULL DEFAULT 1 CHECK (version > 0),
    actualizado_por integer REFERENCES obras.t_usuario(id_usuario) ON DELETE SET NULL,
    actualizado_en timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS obras.t_pago_suscripcion (
    id_pago bigserial PRIMARY KEY,
    id_empresa integer NOT NULL
        REFERENCES obras.t_suscripcion_empresa(id_empresa) ON DELETE RESTRICT,
    codigo_plan varchar(20) NOT NULL
        REFERENCES obras.t_plan_suscripcion(codigo) ON DELETE RESTRICT,
    version_precio integer NOT NULL CHECK (version_precio > 0),
    monto_menor bigint NOT NULL CHECK (monto_menor > 0),
    moneda varchar(3) NOT NULL CHECK (moneda = upper(moneda)),
    periodo_meses smallint NOT NULL CHECK (periodo_meses > 0),
    estado varchar(15) NOT NULL DEFAULT 'PENDIENTE'
        CHECK (estado IN ('PENDIENTE', 'CONFIRMADO', 'FALLIDO', 'CANCELADO')),
    tipo_aplicacion varchar(20)
        CHECK (tipo_aplicacion IS NULL OR tipo_aplicacion IN ('CONTRATACION', 'RENOVACION', 'CAMBIO_PLAN')),
    idempotency_key varchar(255) NOT NULL UNIQUE,
    stripe_checkout_session_id varchar(255) UNIQUE,
    stripe_payment_intent_id varchar(255) UNIQUE,
    stripe_evento_confirmacion_id varchar(255) UNIQUE,
    stripe_checkout_url text,
    stripe_receipt_url text,
    stripe_payment_status varchar(30),
    stripe_livemode boolean NOT NULL DEFAULT false CHECK (NOT stripe_livemode),
    checkout_expira_en timestamptz,
    iniciado_por integer REFERENCES obras.t_usuario(id_usuario) ON DELETE SET NULL,
    verificado_por integer REFERENCES obras.t_usuario(id_usuario) ON DELETE SET NULL,
    id_historial_suscripcion bigint UNIQUE
        REFERENCES obras.t_suscripcion_historial(id) ON DELETE SET NULL,
    error_codigo varchar(80),
    error_detalle text,
    creado_en timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    confirmado_en timestamptz,
    aplicado_en timestamptz,
    CHECK (estado <> 'CONFIRMADO' OR (confirmado_en IS NOT NULL AND aplicado_en IS NOT NULL))
);

CREATE INDEX IF NOT EXISTS idx_pago_suscripcion_empresa_creado
    ON obras.t_pago_suscripcion(id_empresa, creado_en DESC);
CREATE INDEX IF NOT EXISTS idx_pago_suscripcion_estado_creado
    ON obras.t_pago_suscripcion(estado, creado_en DESC);

