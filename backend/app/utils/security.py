from datetime import datetime,timedelta,timezone
from app.config import Config
import jwt


def create_access_token(user_id,user_name,role,id_tenant,name,minutes=120):
    """
    GENERA EL JWT PARA LA SESION DEL USUARIO
    """

    payload={
        'user_id':user_id,
        'username':user_name,
        'role':role,
        'name':name,
        'exp':datetime.now(timezone.utc) + timedelta(minutes=minutes),
        'iat': datetime.now(timezone.utc)
    }

    return jwt.encode(payload, Config.TOKEN_SECRET_KEY, algorithm="HS256")


def decode_access_token(token):
    """
    DECODIFICA Y VALIDA EL JWT ENVIADO POR EL FRONTEND
    """
    try:
        #DECODIFICA EL TOKEN PARA OBTENER LOS VALORES DENTRO DE EL
        payload = jwt.decode(token, Config.TOKEN_SECRET_KEY, algorithms=["HS256"])
        
        #DEVUELVE UN JSON CON LOS VALORES DENTRO ('sub','username','role','exp','iat')
        return {
            'success':True,
            'message':'TOKEN VALIDO',
            'payload':payload
            }
        
    except jwt.ExpiredSignatureError:
        #DEVUELVE UN ERROR SI ES QUE EL TOKEN EXPIRO
        return {
            'success':False,
            'message':'TOKEN EXPIRADO'
        }
        
    except jwt.InvalidTokenError:
        #ERROR SI EL TOKEN ES INVALIDO
        return {
            'success':False,
            'message':'TOKEN INVALIDO'
        }