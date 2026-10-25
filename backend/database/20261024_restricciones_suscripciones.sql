-- Incremental sobre 20261024_suscripciones_empresa.sql. Ejecutar en una transacción.
ALTER TABLE obras.t_plan_suscripcion
    ADD COLUMN IF NOT EXISTS limite_usuarios integer NOT NULL DEFAULT 5 CHECK (limite_usuarios > 0),
    ADD COLUMN IF NOT EXISTS limite_obras integer NOT NULL DEFAULT 2 CHECK (limite_obras > 0),
    ADD COLUMN IF NOT EXISTS consultas_ia_mes integer NOT NULL DEFAULT 0 CHECK (consultas_ia_mes >= 0),
    ADD COLUMN IF NOT EXISTS nivel_reportes varchar(20) NOT NULL DEFAULT 'OPERATIVOS',
    ADD COLUMN IF NOT EXISTS exportar_reportes boolean NOT NULL DEFAULT false,
    ADD COLUMN IF NOT EXISTS automatizar_reportes boolean NOT NULL DEFAULT false;
UPDATE obras.t_plan_suscripcion SET
    limite_usuarios=CASE codigo WHEN 'BASICO' THEN 5 WHEN 'PROFESIONAL' THEN 15 ELSE 50 END,
    limite_obras=CASE codigo WHEN 'BASICO' THEN 2 WHEN 'PROFESIONAL' THEN 10 ELSE 30 END,
    consultas_ia_mes=CASE WHEN codigo='EMPRESARIAL' THEN 500 ELSE 0 END,
    nivel_reportes=CASE WHEN codigo='BASICO' THEN 'OPERATIVOS' ELSE 'TODOS' END,
    exportar_reportes=(codigo<>'BASICO'), automatizar_reportes=(codigo='EMPRESARIAL'),
    prestaciones='["Obras, avances e incidencias", "Presupuestos y APU", "Compras e inventario", "Control de costos y órdenes de cambio", "CRM"]'::jsonb
WHERE codigo IN ('BASICO','PROFESIONAL','EMPRESARIAL') AND NOT(to_jsonb(t_plan_suscripcion) ? 'version');

CREATE TABLE IF NOT EXISTS obras.t_suscripcion_cupo (
    id_empresa integer PRIMARY KEY REFERENCES obras.t_empresa(id_empresa) ON DELETE CASCADE,
    usuarios integer NOT NULL DEFAULT 0 CHECK (usuarios >= 0),
    obras integer NOT NULL DEFAULT 0 CHECK (obras >= 0)
);
CREATE TABLE IF NOT EXISTS obras.t_suscripcion_ia_uso (
    id_empresa integer NOT NULL REFERENCES obras.t_empresa(id_empresa) ON DELETE CASCADE,
    mes date NOT NULL CHECK (extract(day FROM mes)=1),
    consultas integer NOT NULL CHECK (consultas >= 0),
    PRIMARY KEY (id_empresa, mes)
);

-- Bloqueo breve para capturar contadores iniciales y publicar los triggers sin carreras.
LOCK TABLE obras.t_usuario, obras.t_obra IN SHARE ROW EXCLUSIVE MODE;
INSERT INTO obras.t_suscripcion_cupo (id_empresa,usuarios,obras)
SELECT e.id_empresa,
    (SELECT count(*) FROM obras.t_usuario u LEFT JOIN obras.t_rol r USING(id_rol)
     WHERE u.id_empresa=e.id_empresa AND u.estado='ACTIVO' AND r.nombre_rol IS DISTINCT FROM 'ADMINISTRADOR'),
    (SELECT count(*) FROM obras.t_obra o WHERE o.id_empresa=e.id_empresa
     AND COALESCE(o.estado_obra,'') NOT IN ('FINALIZADO','CANCELADO','ARCHIVADO'))
FROM obras.t_empresa e
ON CONFLICT (id_empresa) DO UPDATE SET usuarios=EXCLUDED.usuarios,obras=EXCLUDED.obras;

WITH nuevas AS (
    INSERT INTO obras.t_suscripcion_empresa (id_empresa,codigo_plan,estado,fecha_inicio)
    SELECT id_empresa,'BASICO','ACTIVA',(CURRENT_TIMESTAMP AT TIME ZONE 'America/La_Paz')::date
    FROM obras.t_empresa WHERE nombre_empresa <> 'CLIENTES SIN EMPRESA'
    ON CONFLICT (id_empresa) DO NOTHING RETURNING *
)
INSERT INTO obras.t_suscripcion_historial (id_empresa,codigo_plan,estado,fecha_inicio,origen)
SELECT id_empresa,codigo_plan,estado,fecha_inicio,'PLAN_INICIAL_BASICO' FROM nuevas;

CREATE OR REPLACE FUNCTION obras.fn_suscripcion_escritura(p_empresa integer) RETURNS boolean
LANGUAGE sql STABLE AS $$
    SELECT EXISTS (SELECT 1 FROM obras.t_suscripcion_empresa s WHERE s.id_empresa=p_empresa
        AND s.estado='ACTIVA' AND s.fecha_inicio <= (CURRENT_TIMESTAMP AT TIME ZONE 'America/La_Paz')::date
        AND (s.fecha_fin IS NULL OR s.fecha_fin + 7 >= (CURRENT_TIMESTAMP AT TIME ZONE 'America/La_Paz')::date));
$$;

CREATE OR REPLACE FUNCTION obras.fn_suscripcion_empresa_inicial() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    INSERT INTO obras.t_suscripcion_cupo(id_empresa) VALUES (NEW.id_empresa) ON CONFLICT DO NOTHING;
    IF NEW.nombre_empresa <> 'CLIENTES SIN EMPRESA' THEN
        INSERT INTO obras.t_suscripcion_empresa(id_empresa,codigo_plan,estado,fecha_inicio)
        VALUES (NEW.id_empresa,'BASICO','ACTIVA',(CURRENT_TIMESTAMP AT TIME ZONE 'America/La_Paz')::date);
        INSERT INTO obras.t_suscripcion_historial(id_empresa,codigo_plan,estado,fecha_inicio,origen)
        VALUES (NEW.id_empresa,'BASICO','ACTIVA',(CURRENT_TIMESTAMP AT TIME ZONE 'America/La_Paz')::date,'PLAN_INICIAL_BASICO');
    END IF;
    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION obras.fn_suscripcion_mover_cupo(p_empresa integer,p_tipo text,p_delta integer)
RETURNS void LANGUAGE plpgsql AS $$
DECLARE v_limite integer; v_tecnica boolean;
BEGIN
    IF p_empresa IS NULL OR p_delta=0 THEN RETURN; END IF;
    SELECT nombre_empresa='CLIENTES SIN EMPRESA' INTO v_tecnica FROM obras.t_empresa WHERE id_empresa=p_empresa;
    IF NOT FOUND THEN RETURN; END IF; -- La FK original valida pertenencia.
    IF p_delta < 0 OR v_tecnica THEN
        UPDATE obras.t_suscripcion_cupo SET
            usuarios=CASE WHEN p_tipo='usuarios' THEN GREATEST(0,usuarios+p_delta) ELSE usuarios END,
            obras=CASE WHEN p_tipo='obras' THEN GREATEST(0,obras+p_delta) ELSE obras END
        WHERE id_empresa=p_empresa;
        RETURN;
    END IF;
    IF NOT obras.fn_suscripcion_escritura(p_empresa) THEN
        RAISE EXCEPTION 'SUSCRIPCION_SOLO_LECTURA: La suscripción no permite nuevas altas.' USING ERRCODE='P0001';
    END IF;
    SELECT CASE WHEN p_tipo='usuarios' THEN p.limite_usuarios ELSE p.limite_obras END INTO v_limite
    FROM obras.t_suscripcion_empresa s JOIN obras.t_plan_suscripcion p ON p.codigo=s.codigo_plan
    WHERE s.id_empresa=p_empresa;
    -- UPDATE atómico: dos altas concurrentes no pueden consumir el último cupo.
    UPDATE obras.t_suscripcion_cupo SET
        usuarios=usuarios+CASE WHEN p_tipo='usuarios' THEN p_delta ELSE 0 END,
        obras=obras+CASE WHEN p_tipo='obras' THEN p_delta ELSE 0 END
    WHERE id_empresa=p_empresa AND (CASE WHEN p_tipo='usuarios' THEN usuarios ELSE obras END)+p_delta <= v_limite;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'SUSCRIPCION_CUPO: Límite de % activos alcanzado (%). Archive registros o solicite otro plan.', p_tipo,v_limite USING ERRCODE='P0001';
    END IF;
END;
$$;

CREATE OR REPLACE FUNCTION obras.fn_suscripcion_validar_cupo() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE v_old integer; v_new integer; v_tipo text;
BEGIN
    v_tipo := CASE WHEN TG_TABLE_NAME='t_usuario' THEN 'usuarios' ELSE 'obras' END;
    IF TG_OP <> 'INSERT' THEN
        IF TG_TABLE_NAME='t_usuario' THEN
            IF OLD.estado='ACTIVO' AND NOT EXISTS(SELECT 1 FROM obras.t_rol WHERE id_rol=OLD.id_rol AND nombre_rol='ADMINISTRADOR') THEN
                v_old := OLD.id_empresa;
            END IF;
        ELSIF COALESCE(OLD.estado_obra,'') NOT IN ('FINALIZADO','CANCELADO','ARCHIVADO') THEN v_old := OLD.id_empresa;
        END IF;
    END IF;
    IF TG_OP <> 'DELETE' THEN
        IF TG_TABLE_NAME='t_usuario' THEN
            IF NEW.estado='ACTIVO' AND NOT EXISTS(SELECT 1 FROM obras.t_rol WHERE id_rol=NEW.id_rol AND nombre_rol='ADMINISTRADOR') THEN
                v_new := NEW.id_empresa;
            END IF;
        ELSIF COALESCE(NEW.estado_obra,'') NOT IN ('FINALIZADO','CANCELADO','ARCHIVADO') THEN v_new := NEW.id_empresa;
        END IF;
    END IF;
    IF v_old IS DISTINCT FROM v_new THEN
        -- Orden fijo para transferencias opuestas; cada modificación del contador toma lock de fila.
        PERFORM id_empresa FROM obras.t_suscripcion_cupo WHERE id_empresa IN (v_old,v_new) ORDER BY id_empresa FOR UPDATE;
        PERFORM obras.fn_suscripcion_mover_cupo(v_old,v_tipo,-1);
        PERFORM obras.fn_suscripcion_mover_cupo(v_new,v_tipo,1);
    END IF;
    IF TG_OP='DELETE' THEN RETURN OLD; ELSE RETURN NEW; END IF;
END;
$$;

DROP TRIGGER IF EXISTS tg_suscripcion_empresa_inicial ON obras.t_empresa;
CREATE TRIGGER tg_suscripcion_empresa_inicial AFTER INSERT ON obras.t_empresa
FOR EACH ROW EXECUTE FUNCTION obras.fn_suscripcion_empresa_inicial();
DROP TRIGGER IF EXISTS tg_suscripcion_cupo_usuario ON obras.t_usuario;
CREATE TRIGGER tg_suscripcion_cupo_usuario BEFORE INSERT OR UPDATE OR DELETE ON obras.t_usuario
FOR EACH ROW EXECUTE FUNCTION obras.fn_suscripcion_validar_cupo();
DROP TRIGGER IF EXISTS tg_suscripcion_cupo_obra ON obras.t_obra;
CREATE TRIGGER tg_suscripcion_cupo_obra BEFORE INSERT OR UPDATE OR DELETE ON obras.t_obra
FOR EACH ROW EXECUTE FUNCTION obras.fn_suscripcion_validar_cupo();
