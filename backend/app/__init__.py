from .config import Config
from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS
from app.routes import main_routes,bi_routes,iot_routes,notificaciones_routes,audit_routes,crm_routes,pedidos_routes,profile_routes,mant_maquinaria_routes,prediccion_routes,ordenes_routes,cultivos_routes,roles_routes,auth_routes,users_routes,terrenos_routes,empresas_routes,campanias_routes,maquinarias_routes,logistica_routes,fidelizacion_routes


def create_app():
    app=Flask(__name__)

    #CARGAR CONFIGURACION INICIAL
    app.config.from_object(Config)

    #REGISTRO DE RUTAS
    app.register_blueprint(main_routes.router)
    app.register_blueprint(auth_routes.router)
    app.register_blueprint(users_routes.router)
    app.register_blueprint(terrenos_routes.router)
    app.register_blueprint(empresas_routes.router)
    app.register_blueprint(campanias_routes.router)
    app.register_blueprint(maquinarias_routes.router)
    app.register_blueprint(roles_routes.router)
    app.register_blueprint(cultivos_routes.router)
    app.register_blueprint(prediccion_routes.router)
    app.register_blueprint(ordenes_routes.router)
    app.register_blueprint(mant_maquinaria_routes.router)
    app.register_blueprint(profile_routes.router)
    app.register_blueprint(pedidos_routes.router)
    app.register_blueprint(crm_routes.router)
    app.register_blueprint(audit_routes.router)
    app.register_blueprint(bi_routes.router)
    app.register_blueprint(logistica_routes.router)
    app.register_blueprint(fidelizacion_routes.router)
    app.register_blueprint(iot_routes.router)


    #CONFIGURACION CORS
    CORS(
        app,
        resources={r"/*": {"origins": "*"}},
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"]
    )

    #CONFIGURACION ENVIO DE ARCHVIOS
    app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024 

    #CONFIGURACION WEBSOCKET
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')
    
    notificaciones_routes.register_notificaciones_sockets(socketio)

    app.socketio=socketio

    return app
