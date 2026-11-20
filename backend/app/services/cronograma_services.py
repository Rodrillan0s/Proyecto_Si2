"""CU39: autorización de recurso, planificación y seguimiento determinista."""
from datetime import datetime
from zoneinfo import ZoneInfo
from app.repos import cronograma_repos as repo
from app.schemas.cronograma_schema import CronogramaCreate
from app.utils.cronograma_errors import CronogramaError


def hoy():
    return datetime.now(ZoneInfo('America/La_Paz')).date()


def autorizar(db, id_obra, token, accion='lectura'):
    from app.utils.security import obtener_permisos_rol
    rol = str(token.get('nombre_rol') or '').strip().upper().replace(' ', '_')
    if not token.get('nro_usuario'):
        raise CronogramaError('La sesión no identifica al usuario.',403)
    global_ = rol == 'ADMINISTRADOR'
    permitido = {'ADMINISTRADOR','ADMINISTRADOR_EMPRESA','JEFE_DE_OBRA'}
    if accion in ('lectura','planificacion'):
        permitido |= {'SUPERVISOR','SUPERVISOR_OBRA'}
    if rol not in permitido:
        raise CronogramaError('Su rol no está autorizado para esta acción de cronogramas.',403)
    permiso = {'lectura':'Visualizar_cronograma','crear':'Registrar_cronograma',
               'modificar':'Modificar_cronograma','planificacion':'Planificar_cronograma'}[accion]
    if not global_ and permiso not in obtener_permisos_rol(token.get('nombre_rol')):
        raise CronogramaError('No tiene permiso para esta acción de cronogramas.',403)
    empresa = None if global_ else token.get('id_empresa')
    if not global_ and not empresa:
        raise CronogramaError('La sesión no identifica una empresa.',403)
    obra = repo.obra(db,id_obra,empresa,accion!='lectura')
    if not obra:
        raise CronogramaError('La obra no existe o no pertenece a su empresa.',404)
    return obra


def validar_plan(plan, corte=None):
    corte = corte or hoy()
    by_key = {a.clave:a for a in plan.actividades}
    if len(by_key) != len(plan.actividades):
        raise CronogramaError('Cada actividad debe tener una clave distinta.')
    for a in plan.actividades:
        if a.fecha_inicio < plan.fecha_inicio or a.fecha_fin > plan.fecha_fin:
            raise CronogramaError(f'{a.nombre}: las fechas previstas deben estar dentro del cronograma.')
        if (a.inicio_real and a.inicio_real > corte) or (a.fin_real and a.fin_real > corte):
            raise CronogramaError(f'{a.nombre}: las fechas reales no pueden estar en el futuro.')
        for clave in a.dependencias:
            if clave not in by_key or clave == a.clave:
                raise CronogramaError(f'{a.nombre}: dependencia inexistente o consigo misma.')
    pendientes = {a.clave:set(a.dependencias) for a in plan.actividades}
    resueltas = set()
    while pendientes:
        libres = {key for key,deps in pendientes.items() if deps <= resueltas}
        if not libres:
            raise CronogramaError('Las dependencias forman un ciclo.')
        resueltas |= libres
        pendientes = {key:deps for key,deps in pendientes.items() if key not in libres}
    for a in plan.actividades:
        for clave in a.dependencias:
            previa = by_key[clave]
            if a.fecha_inicio < previa.fecha_fin:
                raise CronogramaError(f'{a.nombre}: debe comenzar después del fin previsto de {previa.nombre}.')
            if a.inicio_real and (not previa.fin_real or a.inicio_real < previa.fin_real):
                raise CronogramaError(f'{a.nombre}: su predecesora debe finalizar antes de su inicio real.')


def presentar(crono, desde=None, hasta=None, corte=None):
    corte = corte or hoy()
    if desde and hasta and desde > hasta:
        raise CronogramaError('El inicio del período no puede ser posterior al fin.')
    if corte > hoy():
        raise CronogramaError('La fecha de corte no puede estar en el futuro.')
    by_key = {a['clave']:a for a in crono['actividades']}
    items=[]
    for raw in crono['actividades']:
        a=dict(raw)
        fin = a['fin_real'] if a['fin_real'] and a['fin_real'] <= corte else None
        inicio = a['inicio_real'] if a['inicio_real'] and a['inicio_real'] <= corte else None
        a['estado'] = 'COMPLETADA' if fin else ('EN_CURSO' if inicio else 'PENDIENTE')
        a['dias_retraso'] = max(0,((fin or corte)-a['fecha_fin']).days)
        a['inicio_retrasado'] = not inicio and corte > a['fecha_inicio']
        a['bloqueada'] = any(not by_key[k]['fin_real'] or by_key[k]['fin_real'] > corte for k in a['dependencias'])
        items.append(a)
    programadas = [a for a in items if (not desde or a['fecha_fin'] >= desde) and (not hasta or a['fecha_inicio'] <= hasta)]
    return dict(crono,actividades=items,programadas=programadas,corte=corte,
        resumen={'total':len(programadas),'completadas':sum(a['estado']=='COMPLETADA' for a in programadas),
                 'retrasadas':sum(a['dias_retraso']>0 for a in programadas),
                 'pendientes_inicio':sum(a['inicio_retrasado'] for a in programadas)})


def listar_cronogramas(id_obra, token):
    with repo.sesion() as db:
        obra = autorizar(db,id_obra,token)
        return {'success':True,'obra':obra,'data':repo.listar(db,id_obra)}


def obtener_cronograma(id_obra,id_cronograma,token,desde=None,hasta=None,corte=None):
    with repo.sesion() as db:
        autorizar(db,id_obra,token)
        return {'success':True,'data':presentar(repo.obtener(db,id_obra,id_cronograma),desde,hasta,corte)}


def crear_cronograma(id_obra,datos,token,ip='unknown'):
    with repo.sesion(True) as db:
        autorizar(db,id_obra,token,'crear')
        validar_plan(datos)
        id_cronograma=repo.crear(db,id_obra,datos)
        repo.actividades(db,id_cronograma,datos.actividades)
        repo.auditar(db,token,'CREAR',id_obra,id_cronograma,ip)
        return {'success':True,'data':presentar(repo.obtener(db,id_obra,id_cronograma))}


def actualizar_cronograma(id_obra,id_cronograma,datos,token,ip='unknown',planificacion=False):
    with repo.sesion(True) as db:
        autorizar(db,id_obra,token,'planificacion' if planificacion else 'modificar')
        actual=repo.obtener(db,id_obra,id_cronograma,True)
        if datos.version != actual['version']:
            raise CronogramaError('Otra persona modificó este cronograma. Recargue antes de guardar.',409)
        if planificacion:
            datos=CronogramaCreate(nombre=actual['nombre'],descripcion=actual['descripcion'],
                fecha_inicio=actual['fecha_inicio'],fecha_fin=actual['fecha_fin'],actividades=datos.actividades)
        validar_plan(datos)
        repo.guardar(db,id_cronograma,datos)
        repo.actividades(db,id_cronograma,datos.actividades)
        repo.auditar(db,token,'PLANIFICAR' if planificacion else 'ACTUALIZAR',id_obra,id_cronograma,ip)
        return {'success':True,'data':presentar(repo.obtener(db,id_obra,id_cronograma))}


def eliminar_cronograma(id_obra,id_cronograma,version,token,ip='unknown'):
    with repo.sesion(True) as db:
        autorizar(db,id_obra,token,'modificar')
        actual=repo.obtener(db,id_obra,id_cronograma,True)
        if version != actual['version']:
            raise CronogramaError('El cronograma cambió. Recargue antes de eliminar.',409)
        repo.eliminar(db,id_cronograma)
        repo.auditar(db,token,'ELIMINAR',id_obra,id_cronograma,ip)
        return {'success':True}


def consultar_retrasos(id_obra,token,corte=None):
    with repo.sesion() as db:
        autorizar(db,id_obra,token)
        result=[]
        for c in repo.listar(db,id_obra):
            detalle=presentar(repo.obtener(db,id_obra,c['id_cronograma']),corte=corte)
            result.extend(dict(a,id_cronograma=c['id_cronograma'],cronograma=c['nombre'])
                          for a in detalle['actividades'] if a['dias_retraso']>0 or a['inicio_retrasado'])
        return {'success':True,'data':result,'corte':corte or hoy()}
