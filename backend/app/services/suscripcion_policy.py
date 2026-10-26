"""Política comercial compartida; no sustituye permisos ni pertenencia por recurso."""
from contextlib import contextmanager
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from fastapi import HTTPException
from app.repos import suscripcion_repos as repo
from app.services.planes_catalog import MODULOS, modulo_ruta

OPERATIVOS = frozenset({'stock', 'consumo_materiales', 'asignacion_personal', 'utilizacion_personal',
                        'avance_ejecutivo', 'estado_unidades', 'incidencias', 'incidencias_criticas'})


def hoy():
    return datetime.now(ZoneInfo('America/La_Paz')).date()


def modulo_habilitado(fila, modulo):
    return bool(fila and modulo in (fila.get('modulos') or []))


def capacidades(fila, fecha=None):
    fecha = fecha or hoy()
    estado = 'SIN_PLAN'
    if fila and fila.get('codigo_plan'):
        estado = fila['estado']
        if estado == 'ACTIVA':
            if fila['fecha_inicio'] > fecha:
                estado = 'PROGRAMADA'
            elif fila.get('fecha_fin') and fila['fecha_fin'] < fecha:
                estado = 'GRACIA' if fecha <= fila['fecha_fin'] + timedelta(days=7) else 'VENCIDA'
    escritura = estado in ('ACTIVA', 'GRACIA')
    return dict(estado_efectivo=estado, solo_lectura=not escritura,
                gracia_hasta=(fila['fecha_fin'] + timedelta(days=7)) if fila and fila.get('fecha_fin') else None,
                ia_habilitada=bool(escritura and modulo_habilitado(fila,'ia') and fila.get('consultas_ia_mes', 0)),
                reportes_habilitado=bool(escritura and modulo_habilitado(fila,'reportes') and fila.get('nivel_reportes')!='NINGUNO'),
                modulos_solo_lectura=[{'codigo':m,'nombre':n} for m,n in MODULOS.items() if not modulo_habilitado(fila,m)],
                exportar_habilitado=bool(escritura and modulo_habilitado(fila,'reportes') and fila.get('exportar_reportes')),
                automatizar_habilitado=bool(escritura and modulo_habilitado(fila,'reportes') and fila.get('automatizar_reportes')))


def obtener(empresa, cur=None):
    return repo.obtener_politica(empresa, cur)


def exigir_escritura(empresa, cur=None):
    fila = obtener(empresa, cur)
    if capacidades(fila)['solo_lectura']:
        raise HTTPException(403, 'SUSCRIPCION_SOLO_LECTURA: Su empresa está en modo de solo lectura. Contacte al administrador para activar o renovar el plan.')
    return fila


def exigir_funcion(empresa, funcion, cur=None):
    fila = exigir_escritura(empresa, cur)
    campo = {'ia': 'consultas_ia_mes', 'exportar': 'exportar_reportes', 'automatizar': 'automatizar_reportes'}[funcion]
    modulo='ia' if funcion=='ia' else 'reportes'
    if not modulo_habilitado(fila,modulo) or not fila.get(campo):
        raise HTTPException(403, f'SUSCRIPCION_FUNCION: La función {funcion} no está incluida en el plan de su empresa.')
    return fila


def reporte_permitido(empresa, reporte, cur=None):
    return reporte_en_plan(obtener(empresa, cur), reporte)


def reporte_en_plan(fila, reporte):
    return bool(modulo_habilitado(fila,'reportes') and fila.get('codigo_plan')
        and (fila.get('nivel_reportes')=='TODOS' or (fila.get('nivel_reportes')=='OPERATIVOS' and reporte in OPERATIVOS)))


def proteger_http(token, metodo, ruta):
    usuario = repo.obtener_usuario(token.get('nro_usuario'))
    if (not usuario or usuario['estado'] != 'ACTIVO' or usuario['id_empresa'] != token.get('id_empresa')
            or usuario.get('nombre_rol') != token.get('nombre_rol')):
        raise HTTPException(403, 'Su cuenta o contexto de empresa cambió. Inicie sesión nuevamente.')
    # No se modifica la sesión ni se bloquea el cuidado de la cuenta.
    if token.get('nombre_rol') == 'ADMINISTRADOR' or metodo in ('GET', 'HEAD', 'OPTIONS'):
        return
    if any(ruta == p or ruta.startswith(p + '/') for p in ('/api/auth', '/api/perfil', '/api/suscripciones', '/api/pagos')):
        return
    fila=exigir_escritura(usuario['id_empresa'])
    modulo=modulo_ruta(ruta)
    if modulo and not modulo_habilitado(fila,modulo):
        raise HTTPException(403, f'SUSCRIPCION_MODULO: {MODULOS[modulo]} está disponible solo para consulta en su plan.')


def autorizar_ia(token, empresa=None):
    if token.get('nombre_rol') == 'ADMINISTRADOR':
        return None
    from app.services.suscripcion_services import autorizar_empresa
    empresa = autorizar_empresa(token, empresa)
    exigir_funcion(empresa, 'ia')
    return empresa


@contextmanager
def consulta_ia(token, empresa=None):
    empresa = autorizar_ia(token, empresa)
    if empresa is None:
        yield
        return
    mes = hoy().replace(day=1)
    # Reserva persistida en una transacción corta; no hay locks durante el proveedor.
    if not repo.reservar_ia(empresa, mes):
        raise HTTPException(429, 'SUSCRIPCION_IA_CUPO: Se alcanzó el cupo mensual de consultas de IA de su empresa.')
    try:
        yield
    except BaseException:
        repo.liberar_ia(empresa, mes)
        raise


def exigir_reporte(ctx, reporte, action='Visualizar_reportes', cur=None, lectura=False):
    if ctx.rol == 'ADMINISTRADOR':
        return
    if not lectura and not reporte_permitido(ctx.empresa, reporte, cur):
        raise HTTPException(403, 'SUSCRIPCION_REPORTE: Este reporte no está incluido en el plan de su empresa.')
    if action in ('Exportar_reportes', 'Enviar_reportes', 'Programar_reportes'):
        exigir_funcion(ctx.empresa, 'exportar' if action == 'Exportar_reportes' else 'automatizar', cur)
