from flask import Blueprint,request

router=Blueprint('main_routes',__name__)

@router.route('/')
def index():
    return {
        'success':True,
        'message':'API Iniciada Exitosamente.'
    }