from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import Config
from app.routes import reportes_routes
from app.utils.reportes_errors import ReportesSchemaMissing

from app.routes import main_routes, auth_routes, users_routes, tenant_routes, roles_routes, backup_routes, profile_routes,estimacion_routes,control_costos_routes, notificaciones_routes, password_recovery_routes, bitacora_routes, obra_routes, estructura_routes, unidad_routes, material_routes, proveedor_routes, orden_Trabajo_routes, crm_routes, ai_routes, presupuesto_routes, compras_routes, inventario_routes , equipos_maquinaria_routes, incidencia_routes, avance_routes


def create_app() -> FastAPI:
    app = FastAPI(
        title="API Base de Gestión",
        version="1.0.0",
        description="Backend FastAPI Base estructurado en 3 capas"
    )

    from app.services.backups.settings import BackupError
    from app.services.backups.coordination import MaintenanceMiddleware

    @app.exception_handler(BackupError)
    async def backup_error(request, exc):
        return JSONResponse(status_code=exc.status, content={'detail': str(exc), 'code': exc.code})

    app.add_middleware(MaintenanceMiddleware)

    @app.exception_handler(ReportesSchemaMissing)
    async def reportes_schema_missing(request, exc):
        return JSONResponse(status_code=503, content={
            'detail': str(exc), 'code': 'REPORTES_SCHEMA_MISSING'
        })

    # CONFIGURACIÓN DE CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:4200",
            "https://obratec.onrender.com"
        ],
        allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1|192\.168\.\d+\.\d+)(:[0-9]+)?$",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=['Content-Disposition', 'Retry-After'],
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
    app.include_router(compras_routes.router,prefix='/api/compras')
    app.include_router(orden_Trabajo_routes.router)
    app.include_router(crm_routes.router, prefix='/api/crm')
    app.include_router(crm_routes.router, prefix='/crm')
    app.include_router(ai_routes.router, prefix='/api/ai')
    app.include_router(ai_routes.router, prefix='/ai')
    app.include_router(presupuesto_routes.router_proyectos)
    app.include_router(presupuesto_routes.router_costos)
    app.include_router(inventario_routes.router, prefix='/api/inventario')
    app.include_router(inventario_routes.router, prefix='/inventario')
    app.include_router(equipos_maquinaria_routes.router)
    app.include_router(estimacion_routes.router)
    app.include_router(control_costos_routes.router)
    app.include_router(incidencia_routes.router,prefix='/api/incidencias')
    app.include_router(reportes_routes.router)
    app.include_router(reportes_routes.voice_router)
    # CU18 – Avances de Obra
    app.include_router(avance_routes.router)
    return app


###esto es una prueba 
