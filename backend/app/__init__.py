from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import Config

from app.routes import main_routes, auth_routes, users_routes, tenant_routes, roles_routes, backup_routes, profile_routes, notificaciones_routes, password_recovery_routes, bitacora_routes, obra_routes, estructura_routes, unidad_routes, material_routes, proveedor_routes



def create_app() -> FastAPI:
    app = FastAPI(
        title="API Base de Gestión",
        version="1.0.0",
        description="Backend FastAPI Base estructurado en 3 capas"
    )

    # CONFIGURACIÓN DE CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:4200",
            "https://obratec.onrender.com"
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # REGISTRO DE RUTAS
    app.include_router(main_routes.router)
    app.include_router(auth_routes.router,prefix='/api/auth')
    app.include_router(password_recovery_routes.router,prefix='/api/auth')
    app.include_router(users_routes.router,prefix='/api/usuarios')
    app.include_router(tenant_routes.router,prefix='/api/empresas')
    app.include_router(roles_routes.router,prefix='/api/roles')
    app.include_router(backup_routes.router,prefix='/api/backup')
    app.include_router(profile_routes.router,prefix='/api/perfil')
    app.include_router(notificaciones_routes.router,prefix='/api/ws')
    app.include_router(bitacora_routes.router,prefix='/api/bitacora')
    app.include_router(obra_routes.router,prefix='/api/proyectos')
    app.include_router(estructura_routes.router)
    app.include_router(unidad_routes.router)
    app.include_router(material_routes.router,prefix='/api/materiales')
    app.include_router(proveedor_routes.router,prefix='/api/proveedores')
    
    return app
