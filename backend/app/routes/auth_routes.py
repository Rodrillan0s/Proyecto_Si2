from flask import Blueprint,request,jsonify
from app.services import auth_services

router=Blueprint('auth_routes',__name__)


@router.post('/api/register')
def register():
    data=request.get_json()

    if not data:
        return jsonify({
            'success':False,
            'message':'Debe enviar los datos para registrarse.'
        }),401
    
    response_data,status_code=auth_services.register_new_user(data)

    return jsonify(response_data),status_code


#INICIO DE SESION
@router.post('/api/login')
def login():
    data=request.get_json()

    if not data:
        return jsonify({
            'success':False,
            'message':'Petición Vacia.'
        })
    
    response_data,status_code=auth_services.validate_user(data)
    return jsonify(response_data),status_code