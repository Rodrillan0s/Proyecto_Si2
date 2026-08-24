from backend.app.routes import password_recovery_routes
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import Config
from app.routes import main_routes, auth_routes 
from app.routes import users_routes, tenant_routes
from app.routes import roles_routes, backup_routes 
from app.routes import profile_routes, notificaciones_routes, password_recovery_routes


def create_app() -> FastAPI:
    app = FastAPI(
        title="API Base de Gestión",
        version="1.0.0",
        description="Backend FastAPI Base estructurado en 3 capas"
    )

    #CONFIGURACION DE CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    #REGISTRO DE RUTAS
    app.include_router(main_routes.router)
    app.include_router(auth_routes.router,prefix='/api/auth')
    app.include_router(password_recovery_routes.router,prefix='/api/auth')
    app.include_router(users_routes.router,prefix='/api/usuarios')
    app.include_router(tenant_routes.router,prefix='/api/empresas')
    app.include_router(roles_routes.router,prefix='/api/roles')
    app.include_router(backup_routes.router,prefix='/api/backup')
    app.include_router(profile_routes.router,prefix='/api/perfil')
    app.include_router(notificaciones_routes.router,prefix='/api/ws')
    
    
    return app
