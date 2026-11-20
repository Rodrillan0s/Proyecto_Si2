-- CU39. Aplicar transaccionalmente solo en el destino designado.
-- No reasigna usuarios ni modifica planes, OT o datos existentes de obras.
CREATE TABLE IF NOT EXISTS obras.t_cronograma (
    id_cronograma serial PRIMARY KEY,
    id_obra integer NOT NULL REFERENCES obras.t_obra(id_obra) ON DELETE CASCADE,
    nombre varchar(180) NOT NULL CHECK (length(trim(nombre))>0),
    descripcion text NOT NULL DEFAULT '',
    fecha_inicio date NOT NULL,
    fecha_fin date NOT NULL,
    version integer NOT NULL DEFAULT 1 CHECK (version>0),
    creado_en timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (fecha_fin>=fecha_inicio)
);
CREATE INDEX IF NOT EXISTS idx_cronograma_obra ON obras.t_cronograma(id_obra,fecha_inicio);

CREATE TABLE IF NOT EXISTS obras.t_cronograma_actividad (
    id_cronograma integer NOT NULL REFERENCES obras.t_cronograma(id_cronograma) ON DELETE CASCADE,
    clave varchar(64) NOT NULL CHECK (clave ~ '^[A-Za-z0-9_-]+$'),
    nombre varchar(180) NOT NULL CHECK (length(trim(nombre))>0),
    descripcion text NOT NULL DEFAULT '',
    tipo varchar(10) NOT NULL CHECK (tipo IN ('ACTIVIDAD','HITO')),
    fecha_inicio date NOT NULL,
    fecha_fin date NOT NULL CHECK (fecha_fin>=fecha_inicio),
    inicio_real date,
    fin_real date,
    avance integer NOT NULL DEFAULT 0 CHECK (avance BETWEEN 0 AND 100),
    orden integer NOT NULL DEFAULT 0,
    PRIMARY KEY (id_cronograma,clave),
    CHECK (tipo<>'HITO' OR (fecha_inicio=fecha_fin AND avance IN (0,100))),
    CHECK (fin_real IS NULL OR (inicio_real IS NOT NULL AND fin_real>=inicio_real)),
    CHECK ((avance=100)=(fin_real IS NOT NULL)),
    CHECK (avance=0 OR inicio_real IS NOT NULL)
);

CREATE TABLE IF NOT EXISTS obras.t_cronograma_dependencia (
    id_cronograma integer NOT NULL,
    actividad varchar(64) NOT NULL,
    predecesora varchar(64) NOT NULL,
    PRIMARY KEY(id_cronograma,actividad,predecesora),
    FOREIGN KEY(id_cronograma,actividad)
        REFERENCES obras.t_cronograma_actividad(id_cronograma,clave) ON DELETE CASCADE,
    FOREIGN KEY(id_cronograma,predecesora)
        REFERENCES obras.t_cronograma_actividad(id_cronograma,clave) ON DELETE CASCADE,
    CHECK(actividad<>predecesora)
);

-- El inventario actual no tiene Supervisor. Crear el rol sin cambiar ningún usuario.
INSERT INTO obras.t_rol(nombre_rol)
SELECT 'SUPERVISOR_OBRA' WHERE NOT EXISTS (
    SELECT 1 FROM obras.t_rol WHERE upper(replace(nombre_rol,' ','_')) IN ('SUPERVISOR','SUPERVISOR_OBRA')
);
DO $$
DECLARE modulo bigint;
BEGIN
    SELECT id_modulo INTO modulo FROM obras.t_modulo WHERE nombre_modulo='Modulo_obras' ORDER BY id_modulo LIMIT 1;
    IF modulo IS NULL THEN RAISE EXCEPTION 'Falta Modulo_obras; instalar el baseline antes de CU39'; END IF;
    INSERT INTO obras.t_permiso(nombre_permiso,id_modulo)
    SELECT p,modulo FROM unnest(ARRAY['Visualizar_cronograma','Registrar_cronograma',
        'Modificar_cronograma','Planificar_cronograma']) p
    WHERE NOT EXISTS(SELECT 1 FROM obras.t_permiso WHERE nombre_permiso=p);
END $$;

INSERT INTO obras.t_rol_permiso(id_rol,id_permiso)
SELECT r.id_rol,p.id_permiso FROM obras.t_rol r CROSS JOIN obras.t_permiso p
WHERE p.nombre_permiso IN ('Visualizar_cronograma','Registrar_cronograma','Modificar_cronograma','Planificar_cronograma')
AND (upper(replace(r.nombre_rol,' ','_')) IN ('ADMINISTRADOR','ADMINISTRADOR_EMPRESA','JEFE_DE_OBRA')
    OR (upper(replace(r.nombre_rol,' ','_')) IN ('SUPERVISOR','SUPERVISOR_OBRA')
        AND p.nombre_permiso IN ('Visualizar_cronograma','Planificar_cronograma')))
ON CONFLICT DO NOTHING;
-- Supervisor necesita descubrir el detalle de obra que contiene CU39.
INSERT INTO obras.t_rol_permiso(id_rol,id_permiso)
SELECT r.id_rol,p.id_permiso FROM obras.t_rol r CROSS JOIN obras.t_permiso p
WHERE upper(replace(r.nombre_rol,' ','_')) IN ('SUPERVISOR','SUPERVISOR_OBRA')
AND p.nombre_permiso='Visualizar_obras' ON CONFLICT DO NOTHING;
