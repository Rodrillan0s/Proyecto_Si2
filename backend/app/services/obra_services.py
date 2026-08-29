from app.repos import obra_repos, bitacora_repos
from datetime import datetime

def generar_siguiente_codigo(id_empresa: int) -> str:
    now = datetime.now()
    year = now.strftime("%Y")
    month = now.strftime("%m")
    prefix = f"P{year}-{month}-"

    from app.classes.postgres import PostgreSQL
    from app.config import Config
    db = PostgreSQL()
    db.create_connection()
    try:
        query = f"""
            SELECT codigo 
            FROM {Config.SCHEMA}.t_obra 
            WHERE id_empresa = %s AND codigo LIKE %s 
            ORDER BY codigo DESC 
            LIMIT 1;
        """
        ultimo = db.execute_query(query, (id_empresa, f"{prefix}%"), fetchone=True)
        if ultimo and ultimo[0]:
            ultimo_cod = str(ultimo[0]).strip()
            try:
                partes = ultimo_cod.split("-")
                seq = int(partes[-1]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1
        return f"{prefix}{str(seq).zfill(4)}"
    finally:
        db.close_connection()

def registrar_obra(data: dict, token_data: dict, client_ip: str = "unknown"):
    # 1. Obtener id_empresa de forma segura
    id_empresa = token_data.get('id_empresa')
    if token_data.get('nombre_rol') == 'ADMINISTRADOR':
        id_empresa = data.get('id_empresa') or id_empresa
    
    if not id_empresa:
        raise ValueError("El ID de la empresa es obligatorio.")

    # 2. Generación o validación automática del código (Formato: PYYYY-MM-NNNN)
    codigo = (data.get('codigo') or '').strip().upper()
    if not codigo or 'AUTO' in codigo or codigo.startswith('['):
        codigo = generar_siguiente_codigo(id_empresa)

    id_tipo_obra = data.get('id_tipo_obra')
    if not id_tipo_obra:
        raise ValueError("El tipo de proyecto es obligatorio.")

    estado_inicial = 'PLANIFICACION'

    nombre = (data.get('nombre') or '').strip()
    if not nombre:
        from app.classes.postgres import PostgreSQL
        from app.config import Config
        db = PostgreSQL()
        db.create_connection()
        try:
            tipo_res = db.execute_query(f"SELECT nombre_obra FROM {Config.SCHEMA}.t_tipo_obra WHERE id_tipo_obra = %s", (id_tipo_obra,), fetchone=True)
            tipo_nombre = tipo_res[0] if (tipo_res and tipo_res[0]) else "Proyecto"
            nombre = f"{tipo_nombre} {codigo}"
        finally:
            db.close_connection()

    # 3. Validar fechas
    fecha_inicio_str = data.get('fecha_inicio')
    fecha_fin_str = data.get('fecha_fin')

    if not fecha_inicio_str:
        raise ValueError("La fecha de inicio es obligatoria.")

    try:
        fecha_inicio = datetime.strptime(fecha_inicio_str, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError("Formato de fecha de inicio incorrecto. Debe ser YYYY-MM-DD.")

    fecha_fin = None
    if fecha_fin_str and len(fecha_fin_str.strip()) > 0:
        try:
            fecha_fin = datetime.strptime(fecha_fin_str, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Formato de fecha de finalización estimado incorrecto. Debe ser YYYY-MM-DD.")
        
        if fecha_fin < fecha_inicio:
            raise ValueError("La fecha de finalización estimada no puede ser anterior a la fecha de inicio.")

    # 4. Validar valor estimado
    cotizacion_inicial = data.get('valor_estimado') or 0.0
    try:
        cotizacion_inicial = float(cotizacion_inicial)
        if cotizacion_inicial < 0:
            raise ValueError()
    except (ValueError, TypeError):
        raise ValueError("El valor estimado debe ser un número decimal no negativo.")

    # 5. Parámetros opcionales y regionalización
    moneda = data.get('moneda') or 'BOB'
    ubicacion = data.get('ubicacion') or ''
    zona = data.get('zona') or ''
    distrito = data.get('distrito') or ''
    uv = data.get('uv') or ''
    manzana = data.get('manzana') or ''
    
    try:
        latitud = float(data.get('latitud')) if data.get('latitud') else None
        longitud = float(data.get('longitud')) if data.get('longitud') else None
    except (ValueError, TypeError):
        raise ValueError("Las coordenadas de latitud y longitud deben ser números válidos.")

    id_supervisor = data.get('id_supervisor') or None
    id_cliente = data.get('id_cliente') or None
    descripcion = data.get('descripcion') or ''
    descripcion_cliente = data.get('descripcion_cliente') or ''
    observacion = data.get('observacion') or ''

    # 6. Registrar mediante el Repositorio (Invocación al SP)
    res = obra_repos.registrar_obra_sp(
        codigo, nombre, descripcion, id_tipo_obra, estado_inicial, fecha_inicio, fecha_fin, id_empresa, moneda,
        ubicacion, zona, distrito, uv, manzana, latitud, longitud, id_supervisor, id_cliente,
        cotizacion_inicial, descripcion_cliente, observacion
    )

    if not res.get('success'):
        error_msg = res.get('error', '')
        if "uq_obra_empresa_codigo" in error_msg:
            raise ValueError(f"El código de proyecto '{codigo}' ya está en uso en su empresa.")
        raise ValueError(error_msg or "No se pudo registrar el proyecto.")

    # 7. Registrar en la bitácora
    bitacora_repos.registrar_bitacora(
        id_usuario=token_data.get('nro_usuario'),
        modulo="PROYECTOS",
        accion="CREAR_OBRA",
        descripcion=f"Proyecto creado con código {codigo} y nombre {nombre}.",
        ip=client_ip,
        estado="EXITOSO"
    )

    return res

def actualizar_obra(id_obra: int, data: dict, token_data: dict, client_ip: str = "unknown"):
    # 1. Obtener id_empresa a validar (Defensa en profundidad)
    id_empresa = token_data.get('id_empresa')
    if token_data.get('nombre_rol') == 'ADMINISTRADOR':
        # Para el administrador global, obtenemos la empresa de la obra actual
        obra_actual = obra_repos.obtener_obra_detalle_sp(id_obra, None)
        if not obra_actual.get('success'):
            raise ValueError("El proyecto no existe.")
        id_empresa = obra_actual['data']['id_empresa']

    if not id_empresa:
        raise ValueError("El ID de la empresa es obligatorio.")

    # 2. Validar campos obligatorios
    nombre = (data.get('nombre') or '').strip()
    id_tipo_obra = data.get('id_tipo_obra')

    if not nombre:
        raise ValueError("El nombre del proyecto es obligatorio.")
    if not id_tipo_obra:
        raise ValueError("El tipo de proyecto es obligatorio.")

    # 3. Validar fechas
    fecha_inicio_str = data.get('fecha_inicio')
    fecha_fin_str = data.get('fecha_fin')

    if not fecha_inicio_str:
        raise ValueError("La fecha de inicio es obligatoria.")

    try:
        fecha_inicio = datetime.strptime(str(fecha_inicio_str), "%Y-%m-%d").date()
    except ValueError:
        raise ValueError("Formato de fecha de inicio incorrecto. Debe ser YYYY-MM-DD.")

    fecha_fin = None
    if fecha_fin_str and len(str(fecha_fin_str).strip()) > 0:
        try:
            fecha_fin = datetime.strptime(str(fecha_fin_str), "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Formato de fecha de finalización estimado incorrecto. Debe ser YYYY-MM-DD.")
        
        if fecha_fin < fecha_inicio:
            raise ValueError("La fecha de finalización estimada no puede ser anterior a la fecha de inicio.")

    # 4. Validar valor estimado
    cotizacion_inicial = data.get('valor_estimado') or 0.0
    try:
        cotizacion_inicial = float(cotizacion_inicial)
        if cotizacion_inicial < 0:
            raise ValueError()
    except (ValueError, TypeError):
        raise ValueError("El valor estimado debe ser un número decimal no negativo.")

    # 5. Parámetros opcionales
    moneda = data.get('moneda') or 'BOB'
    ubicacion = data.get('ubicacion') or ''
    zona = data.get('zona') or ''
    distrito = data.get('distrito') or ''
    uv = data.get('uv') or ''
    manzana = data.get('manzana') or ''
    
    try:
        latitud = float(data.get('latitud')) if data.get('latitud') else None
        longitud = float(data.get('longitud')) if data.get('longitud') else None
    except (ValueError, TypeError):
        raise ValueError("Las coordenadas de latitud y longitud deben ser números válidos.")

    id_supervisor = data.get('id_supervisor') or None
    id_cliente = data.get('id_cliente') or None
    descripcion = data.get('descripcion') or ''
    descripcion_cliente = data.get('descripcion_cliente') or ''
    observacion = data.get('observacion') or ''

    # 6. Actualizar mediante SP
    res = obra_repos.actualizar_obra_sp(
        id_obra, id_empresa, id_tipo_obra, fecha_inicio, fecha_fin, nombre, descripcion, moneda,
        ubicacion, zona, distrito, uv, manzana, latitud, longitud, id_supervisor, id_cliente,
        cotizacion_inicial, descripcion_cliente, observacion
    )

    if not res.get('success'):
        raise ValueError(res.get('error', "No se pudo actualizar el proyecto."))

    # 7. Registrar bitácora
    bitacora_repos.registrar_bitacora(
        id_usuario=token_data.get('nro_usuario'),
        modulo="PROYECTOS",
        accion="ACTUALIZAR_OBRA",
        descripcion=f"Proyecto {id_obra} actualizado.",
        ip=client_ip,
        estado="EXITOSO"
    )

    return res

def listar_obras(token_data: dict):
    # Si es Administrador del Sistema, puede listar todas las obras pasando None
    id_empresa = None if token_data.get('nombre_rol') == 'ADMINISTRADOR' else token_data.get('id_empresa')
    return obra_repos.listar_obras_sp(id_empresa)

def obtener_obra_detalle(id_obra: int, token_data: dict):
    id_empresa = None if token_data.get('nombre_rol') == 'ADMINISTRADOR' else token_data.get('id_empresa')
    res = obra_repos.obtener_obra_detalle_sp(id_obra, id_empresa)
    if not res.get('success'):
        raise ValueError(res.get('error', "El proyecto no existe o no tiene permisos para verlo."))
    return res

def actualizar_estado_obra(id_obra: int, nuevo_estado: str, token_data: dict, client_ip: str = "unknown"):
    id_empresa = token_data.get('id_empresa')
    if token_data.get('nombre_rol') == 'ADMINISTRADOR':
        # Para el administrador global, obtenemos la empresa de la obra actual
        obra_actual = obra_repos.obtener_obra_detalle_sp(id_obra, None)
        if not obra_actual.get('success'):
            raise ValueError("El proyecto no existe.")
        id_empresa = obra_actual['data']['id_empresa']

    if not id_empresa:
        raise ValueError("El ID de la empresa es obligatorio.")

    res = obra_repos.actualizar_estado_obra_sp(id_obra, id_empresa, nuevo_estado)
    if not res.get('success'):
        raise ValueError(res.get('error', "No se pudo cambiar el estado del proyecto."))

    # Registrar en bitácora
    bitacora_repos.registrar_bitacora(
        id_usuario=token_data.get('nro_usuario'),
        modulo="PROYECTOS",
        accion="CAMBIAR_ESTADO_OBRA",
        descripcion=f"Estado del proyecto {id_obra} cambiado a {nuevo_estado}.",
        ip=client_ip,
        estado="EXITOSO"
    )
    return res

def asignar_responsable(id_obra: int, id_usuario: int, token_data: dict, client_ip: str = "unknown"):
    id_empresa = token_data.get('id_empresa')
    if token_data.get('nombre_rol') == 'ADMINISTRADOR':
        obra_actual = obra_repos.obtener_obra_detalle_sp(id_obra, None)
        if not obra_actual.get('success'):
            raise ValueError("El proyecto no existe.")
        id_empresa = obra_actual['data']['id_empresa']

    if not id_empresa:
        raise ValueError("El ID de la empresa es obligatorio.")

    # Validar que el usuario a asignar tenga el rol 'JEFE DE OBRA'
    from app.classes.postgres import PostgreSQL
    from app.config import Config
    db = PostgreSQL()
    db.create_connection()
    try:
        query_val = f"""
            SELECT r.nombre_rol 
            FROM {Config.SCHEMA}.t_usuario u
            INNER JOIN {Config.SCHEMA}.t_rol r ON u.id_rol = r.id_rol
            WHERE u.id_usuario = %s AND (u.id_empresa = %s OR %s IS NULL);
        """
        user_rol = db.execute_query(query_val, (id_usuario, id_empresa, id_empresa), fetchone=True)
        if not user_rol or user_rol[0] != 'JEFE DE OBRA':
            raise ValueError("Solo se permite asignar como responsable a usuarios con el rol 'JEFE DE OBRA'.")
    finally:
        db.close_connection()

    res = obra_repos.asignar_responsable_sp(id_obra, id_usuario, id_empresa)
    if not res.get('success'):
        raise ValueError(res.get('error', "No se pudo asignar el responsable."))

    # Registrar en bitácora
    bitacora_repos.registrar_bitacora(
        id_usuario=token_data.get('nro_usuario'),
        modulo="PROYECTOS",
        accion="ASIGNAR_RESPONSABLE",
        descripcion=f"Responsable {id_usuario} asignado al proyecto {id_obra}.",
        ip=client_ip,
        estado="EXITOSO"
    )
    return res

def retirar_responsable(id_obra: int, id_usuario: int, token_data: dict, client_ip: str = "unknown"):
    id_empresa = token_data.get('id_empresa')
    if token_data.get('nombre_rol') == 'ADMINISTRADOR':
        obra_actual = obra_repos.obtener_obra_detalle_sp(id_obra, None)
        if not obra_actual.get('success'):
            raise ValueError("El proyecto no existe.")
        id_empresa = obra_actual['data']['id_empresa']

    if not id_empresa:
        raise ValueError("El ID de la empresa es obligatorio.")

    res = obra_repos.retirar_responsable_sp(id_obra, id_usuario, id_empresa)
    if not res.get('success'):
        raise ValueError(res.get('error', "No se pudo retirar el responsable."))

    # Registrar en bitácora
    bitacora_repos.registrar_bitacora(
        id_usuario=token_data.get('nro_usuario'),
        modulo="PROYECTOS",
        accion="RETIRAR_RESPONSABLE",
        descripcion=f"Responsable {id_usuario} retirado del proyecto {id_obra}.",
        ip=client_ip,
        estado="EXITOSO"
    )
    return res

def obtener_tipos_proyecto():
    return obra_repos.obtener_tipos_obra()
