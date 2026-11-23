import os
import sys
import json
from dotenv import load_dotenv

load_dotenv('backend/.env')
sys.path.insert(0, 'backend')

from app.classes.postgres import PostgreSQL
from app.services import crm_services
from app.utils.security import create_access_token

def run():
    print('======================================================================')
    print('PASO 1: Iniciar sesión como usuario autorizado de la constructora')
    print('======================================================================')
    token_emisor = {
        'nro_usuario': 5,
        'username': 'PABLOPT',
        'id_empresa': 1,
        'nombre_rol': 'JEFE DE OBRA'
    }
    jwt_emisor = create_access_token(
        nro_usuario=5,
        username='PABLOPT',
        nombre_rol='JEFE DE OBRA',
        id_empresa=1,
        nombre_empresa='OBRATEC',
        nombre_completo='Pablo Perez',
        nro_taller=None
    )
    print(f"Usuario emisor autenticado: {token_emisor['username']} ({token_emisor['nombre_rol']})")

    print('\n======================================================================')
    print('PASO 2: Enviar comunicación directa a FABRICIO')
    print('======================================================================')
    payload_comunicacion = {
        'id_cliente': 54,
        'id_obra': 8,
        'id_unidad': 9,
        'titulo': 'Avance de su unidad',
        'cuerpo': 'Se informa que su unidad UNI-000009 presenta avances en su proceso de construcción.',
        'tipo_referencia': 'COMUNICACION'
    }
    res_envio = crm_services.crear_comunicacion_cliente(payload_comunicacion, token_emisor, ip='127.0.0.1')
    print('Respuesta del servicio al enviar:')
    print(json.dumps(res_envio, indent=2, default=str))

    id_notif_creada = res_envio['data']['id_notificacion']

    print('\n======================================================================')
    print('PASO 3: Comprobar en PostgreSQL el registro en obras.notificacion')
    print('======================================================================')
    db = PostgreSQL()
    db.create_connection()
    fila_bd = db.execute_query('''
        SELECT id_notificacion, titulo, cuerpo, tipo_referencia, nro_usuario, leido, fecha_creacion, id_empresa, id_obra
        FROM obras.notificacion
        WHERE id_notificacion = %s;
    ''', (id_notif_creada,), fetchone=True)
    db.close_connection()

    print('Registro encontrado en obras.notificacion:')
    print(f'  id_notificacion: {fila_bd[0]}')
    print(f'  titulo:          {fila_bd[1]}')
    print(f'  cuerpo:          {fila_bd[2]}')
    print(f'  tipo_referencia: {fila_bd[3]}')
    print(f'  nro_usuario:     {fila_bd[4]} (Verificado: 20)')
    print(f'  leido:           {fila_bd[5]} (Verificado: False)')
    print(f'  fecha_creacion:  {fila_bd[6]}')
    print(f'  id_empresa:      {fila_bd[7]} (Verificado: 1)')
    print(f'  id_obra:         {fila_bd[8]} (Verificado: 8)')

    assert fila_bd[4] == 20, 'El nro_usuario no corresponde a Fabricio'
    assert fila_bd[7] == 1, 'El id_empresa no es 1'
    assert fila_bd[8] == 8, 'El id_obra no es 8'
    assert fila_bd[5] is False, 'leido no inicio en False'

    print('\n======================================================================')
    print('PASO 4 y 5: Cerrar sesion de constructora e iniciar sesion como FABRICIO')
    print('======================================================================')
    token_fabricio = {
        'nro_usuario': 20,
        'username': 'FABRICIO',
        'id_empresa': 1,
        'nombre_rol': 'CLIENTE'
    }
    jwt_fabricio = create_access_token(
        nro_usuario=20,
        username='FABRICIO',
        nombre_rol='CLIENTE',
        id_empresa=1,
        nombre_empresa='OBRATEC',
        nombre_completo='Fabricio',
        nro_taller=None
    )
    print(f"Sesion iniciada como cliente: {token_fabricio['username']} (id_usuario={token_fabricio['nro_usuario']})")

    print('\n======================================================================')
    print('PASO 6 y 7: Consultar seccion COMUNICACIONES en Dashboard del cliente')
    print('======================================================================')
    res_portal = crm_services.listar_comunicaciones_cliente_autenticado(token_fabricio)
    print('Resultado recibido en el panel del cliente:')
    print(json.dumps(res_portal, indent=2, default=str))

    print('\nVerificaciones del panel:')
    print(f"  Total comunicaciones:     {len(res_portal['data'])}")
    print(f"  Comunicaciones no leidas: {res_portal['no_leidas']}")
    primera = res_portal['data'][0]
    print(f"  Titulo mostrado:          {primera['titulo']}")
    print(f"  Mensaje mostrado:         {primera['cuerpo']}")
    print(f"  Estado leido:             {primera['leido']} -> Renderiza badge: 'Nuevo'")
    print(f"  Fecha creacion:           {primera['fecha_creacion']}")

    assert res_portal['no_leidas'] >= 1
    assert primera['titulo'] == 'Avance de su unidad'
    assert primera['leido'] is False

    print('\n======================================================================')
    print('PASO 8: Actualizar seccion y verificar persistencia')
    print('======================================================================')
    res_portal_recarga = crm_services.listar_comunicaciones_cliente_autenticado(token_fabricio)
    print(f"Comprobacion de recarga exitosa: {len(res_portal_recarga['data'])} comunicaciones encontradas.")
    print('>>> TODO EL FLUJO END-TO-END FUNCIONO PERFECTAMENTE <<<')

if __name__ == '__main__':
    run()
