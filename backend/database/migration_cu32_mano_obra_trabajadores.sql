BEGIN;

CREATE TABLE IF NOT EXISTS obras.t_salario_trabajador (
    id_salario BIGSERIAL PRIMARY KEY,
    id_empresa INTEGER NOT NULL REFERENCES obras.t_empresa(id_empresa) ON DELETE RESTRICT,
    id_usuario INTEGER NOT NULL REFERENCES obras.t_usuario(id_usuario) ON DELETE RESTRICT,
    salario_diario NUMERIC(14,2) NOT NULL CHECK (salario_diario > 0),
    fecha_vigencia DATE NOT NULL,
    registrado_por INTEGER NOT NULL REFERENCES obras.t_usuario(id_usuario) ON DELETE RESTRICT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_salario_trabajador_vigencia
        UNIQUE (id_empresa, id_usuario, fecha_vigencia)
);

CREATE INDEX IF NOT EXISTS idx_salario_trabajador_vigente
    ON obras.t_salario_trabajador (id_empresa, id_usuario, fecha_vigencia DESC);

CREATE TABLE IF NOT EXISTS obras.t_jornada_trabajador_obra (
    id_jornada BIGSERIAL PRIMARY KEY,
    id_empresa INTEGER NOT NULL REFERENCES obras.t_empresa(id_empresa) ON DELETE RESTRICT,
    id_obra INTEGER NOT NULL REFERENCES obras.t_obra(id_obra) ON DELETE RESTRICT,
    id_usuario INTEGER NOT NULL REFERENCES obras.t_usuario(id_usuario) ON DELETE RESTRICT,
    id_salario BIGINT NOT NULL REFERENCES obras.t_salario_trabajador(id_salario) ON DELETE RESTRICT,
    fecha DATE NOT NULL,
    dias_trabajados NUMERIC(5,2) NOT NULL CHECK (dias_trabajados >= 0 AND dias_trabajados <= 1),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_jornada_trabajador_obra_fecha
        UNIQUE (id_empresa, id_obra, id_usuario, fecha)
);

CREATE INDEX IF NOT EXISTS idx_jornada_trabajador_obra_fecha
    ON obras.t_jornada_trabajador_obra (id_empresa, id_obra, fecha);

CREATE TABLE IF NOT EXISTS obras.t_cu32_mano_obra_cierre (
    id_cierre BIGSERIAL PRIMARY KEY,
    id_empresa INTEGER NOT NULL REFERENCES obras.t_empresa(id_empresa) ON DELETE RESTRICT,
    id_obra INTEGER NOT NULL REFERENCES obras.t_obra(id_obra) ON DELETE RESTRICT,
    id_jornada BIGINT NOT NULL REFERENCES obras.t_jornada_trabajador_obra(id_jornada) ON DELETE RESTRICT,
    id_usuario INTEGER NOT NULL REFERENCES obras.t_usuario(id_usuario) ON DELETE RESTRICT,
    id_salario BIGINT NOT NULL REFERENCES obras.t_salario_trabajador(id_salario) ON DELETE RESTRICT,
    fecha DATE NOT NULL,
    dias_trabajados NUMERIC(5,2) NOT NULL CHECK (dias_trabajados >= 0 AND dias_trabajados <= 1),
    salario_diario NUMERIC(14,2) NOT NULL CHECK (salario_diario > 0),
    costo_calculado NUMERIC(16,2) NOT NULL CHECK (costo_calculado >= 0),
    cerrado_en TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_cu32_mano_obra_jornada UNIQUE (id_jornada)
);

CREATE INDEX IF NOT EXISTS idx_cu32_mano_obra_cierre_obra
    ON obras.t_cu32_mano_obra_cierre (id_empresa, id_obra);

COMMIT;
