"""Edición global de capacidades con revisión de impacto y concurrencia optimista."""
import hashlib
import json
from fastapi import HTTPException
from app.repos import planes_repos as repo
from app.services.planes_catalog import MODULOS


def exigir_global(token):
    if token.get('nombre_rol')!='ADMINISTRADOR':
        raise HTTPException(403,'Solo el Super Admin puede configurar los planes.')


def validar(datos):
    datos=dict(datos)
    modulos=datos.get('modulos',[])
    if len(modulos)!=len(set(modulos)) or set(modulos)-MODULOS.keys():
        raise HTTPException(422,'Seleccione módulos existentes sin repetirlos.')
    for campo,menor,mayor in [('limite_usuarios',1,100000),('limite_obras',1,100000),('consultas_ia_mes',0,1000000)]:
        if type(datos.get(campo)) is not int or not menor<=datos[campo]<=mayor:
            raise HTTPException(422,f'El valor de {campo} está fuera del rango permitido.')
    if datos.get('nivel_reportes') not in ('NINGUNO','OPERATIVOS','TODOS'):
        raise HTTPException(422,'Nivel de reportes inválido.')
    if ('ia' in modulos)!=(datos['consultas_ia_mes']>0):
        raise HTTPException(422,'Active IA con un cupo mayor a cero, o desactívela y deje el cupo en cero.')
    if 'reportes' not in modulos and (datos['nivel_reportes']!='NINGUNO' or datos.get('exportar_reportes') or datos.get('automatizar_reportes')):
        raise HTTPException(422,'Sin el módulo Reportes, desactive su generación, exportación y automatización.')
    if datos['nivel_reportes']=='NINGUNO' and (datos.get('exportar_reportes') or datos.get('automatizar_reportes')):
        raise HTTPException(422,'La exportación requiere un nivel de reportes habilitado.')
    if datos.get('automatizar_reportes') and not datos.get('exportar_reportes'):
        raise HTTPException(422,'La automatización requiere exportación de reportes.')
    datos['modulos']=sorted(modulos)
    datos['nombre']=str(datos.get('nombre','')).strip()
    datos['descripcion']=str(datos.get('descripcion','')).strip()
    if not datos['nombre'] or len(datos['nombre'])>80 or len(datos['descripcion'])>1000:
        raise HTTPException(422,'Revise el nombre y la descripción del plan.')
    datos['prestaciones']=[MODULOS[m] for m in MODULOS if m in modulos and m not in ('ia','reportes')]
    return datos


def firma(codigo, datos, empresas):
    texto=json.dumps({'codigo':codigo,'datos':datos,'empresas':empresas},sort_keys=True,ensure_ascii=False,default=str)
    return hashlib.sha256(texto.encode()).hexdigest()


def impacto(actual,datos,empresas):
    eliminados=sorted(set(actual['modulos'])-set(datos['modulos']))
    return {'empresas':empresas,'total_empresas':len(empresas),
        'modulos_retirados':[{'codigo':m,'nombre':MODULOS[m]} for m in eliminados],
        'empresas_sobre_cupo':[e for e in empresas if e['usuarios_activos']>datos['limite_usuarios'] or e['obras_activas']>datos['limite_obras']],
        'confirmacion':firma(actual['codigo'],datos,empresas),
        'mensaje':'Los cambios se aplican a todas las empresas de este plan. Se conservan datos e historial; los módulos retirados quedan en solo lectura y los cupos inferiores bloquean nuevas altas.'}


def configurar(token,codigo,datos,confirmacion=None):
    exigir_global(token)
    datos=validar(datos)
    with repo.transaccion() as cur:
        actual=repo.obtener(cur,codigo,bloquear=confirmacion is not None)
        if not actual: raise HTTPException(404,'Plan no encontrado.')
        if actual['version']!=datos['version']:
            raise HTTPException(409,'El plan cambió. Recargue su configuración y revise el impacto de nuevo.')
        empresas=repo.empresas(cur,codigo)
        vista=impacto(actual,datos,empresas)
        if confirmacion is None: return vista
        if confirmacion!=vista['confirmacion']:
            raise HTTPException(409,'La configuración o las empresas afectadas cambiaron. Revise el impacto nuevamente.')
        nuevo=repo.guardar(cur,codigo,datos)
        repo.historial_insertar(cur,codigo,token['nro_usuario'],actual,nuevo,empresas)
        return nuevo
