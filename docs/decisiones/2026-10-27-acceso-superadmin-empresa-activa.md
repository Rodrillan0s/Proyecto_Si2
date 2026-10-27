# Acceso Superadministrador y Resolución de Empresa Activa

## Contexto y Problema
El usuario con rol global `ADMINISTRADOR` (superadmin) debe poder gestionar y operar sobre cualquier empresa del sistema cambiando la empresa activa desde la cabecera.
Previamente:
1. En frontend (`estimaciones`, `control-costos`, `gastos-operativos`), la propiedad `contextoCompatible` comparaba rígidamente `id_empresa_activa === usuario.id_empresa`. Al loguearse con una empresa o sin ella, si seleccionaba otra empresa en el selector de cabecera se bloqueaba con un banner de incompatibilidad.
2. En las peticiones HTTP del frontend no se enviaba explícitamente el encabezado `X-Id-Empresa` con la empresa activa seleccionada.
3. En backend, `verificar_token` no permitía que un usuario con rol `ADMINISTRADOR` adoptara la empresa activa solicitada vía encabezado `X-Id-Empresa` o parámetro de consulta para servicios multitenant que dependen de `token['id_empresa']`.

## Capas y Solución Focalizada
- **Frontend Interceptor (`auth-interceptor.ts`)**: Inyecta el encabezado `X-Id-Empresa` en peticiones autenticadas si hay una empresa activa seleccionada.
- **Frontend Páginas (`estimaciones.ts`, `control-costos.ts`, `gastos-operativos.ts`)**: Para `ADMINISTRADOR`, `contextoCompatible` es verdadero siempre que exista una empresa activa seleccionada en la cabecera (`!!this.auth.obtenerIdEmpresaActiva()`).
- **Backend Seguridad (`backend/app/utils/security.py`)**: En `verificar_token`, si el rol es `ADMINISTRADOR` y se recibe el encabezado `X-Id-Empresa` (o query param `id_empresa`), se actualiza `payload['id_empresa']` para que los servicios dependientes operen en el tenant seleccionado.

## Validación Prevista
- Verificación de compilación TypeScript y tests unitarios.
- Verificación de endpoints backend con token de superadmin y encabezado `X-Id-Empresa`.
