# Decisión de Diseño: HU115 – Consultar fotografías actualizadas de unidad

## Contexto y Alcance
En la implementación previa de CU30 (HU115), las fotografías se obtenían desde `obras.t_incidencia_evidencia` mediante `incidencia_repos.py`. Funcionalmente, esto era incorrecto porque `t_incidencia_evidencia` pertenece al ciclo de incidencias (HU73) y no refleja las fotografías directas del proceso constructivo de la unidad.

Se rediseña la arquitectura de HU115 para:
1. Consultar exclusivamente la tabla existente `obras.t_unidad_fotografia` mediante `crm_repos.py`.
2. Desvincular por completo `incidencia_repos.py` del flujo de fotografías de unidad en `crm_services.py`.
3. Preservar las rutas cliente:
   - `GET /api/crm/cliente/unidades/{id_unidad}/fotografias`
   - `GET /api/crm/cliente/unidades/{id_unidad}/fotografias/{id_fotografia}/archivo`
4. Implementar el endpoint administrativo/operativo para carga de fotografías de unidad:
   - `POST /api/unidades/{id_unidad}/fotografias`
   con almacenamiento aislado bajo `backend/uploads/unidades/{id_unidad}/` y ruta relativa registrada en BD.
5. Adaptar el contrato en frontend (`crm.service.ts` y `panel.ts`) para soportar limpiamente `id_fotografia` manteniendo compatibilidad.

## Capas y Contratos

### 1. Base de datos (`obras.t_unidad_fotografia`)
Columnas vigentes:
- `id_fotografia` (SERIAL PK)
- `id_unidad` (INTEGER NOT NULL FK -> `obras.t_unidad_construccion`)
- `ruta_archivo` (VARCHAR NOT NULL)
- `nombre_archivo` (VARCHAR NOT NULL)
- `tipo_mime` (VARCHAR NULL)
- `tamano_bytes` (INTEGER NULL)
- `es_principal` (BOOLEAN NOT NULL DEFAULT false)
- `orden` (INTEGER NOT NULL DEFAULT 1)
- `id_usuario` (INTEGER NULL FK -> `obras.t_usuario`)
- `created_at` (TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)

### 2. Repositorio (`crm_repos.py` y `unidad_repos.py`)
- `listar_fotografias_cliente_cu30(id_cliente, id_unidad, id_empresa)`:
  Consulta `t_unidad_fotografia` vinculando `t_unidad_construccion`, `t_estructura_obra`, `t_obra`, `t_crm_cliente` y `t_crm_cliente_unidad`.
  Garantiza:
  - La unidad pertenece a una obra del tenant (`o.id_empresa = %s`).
  - El cliente pertenece al mismo tenant (`c.id_empresa = %s`).
  - La unidad está asociada al cliente (`EXISTS in t_crm_cliente_unidad`).
  - Solo devuelve fotos de `id_unidad`.
  - Filtro estricto de MIME: `image/jpeg`, `image/png`, `image/webp`, `image/gif`.
  - Orden: `orden ASC, created_at DESC, id_fotografia DESC`.
- `obtener_fotografia_cliente_cu30(id_cliente, id_unidad, id_fotografia, id_empresa)`:
  Verifica todas las condiciones anteriores filtrando por `id_fotografia`.
- `insertar_fotografia_unidad(id_unidad, ruta_archivo, nombre_archivo, tipo_mime, tamano_bytes, es_principal, orden, id_usuario)`:
  Inserta de forma parametrizada en `t_unidad_fotografia`.
- `obtener_empresa_de_unidad(id_unidad)`:
  Obtiene la empresa y obra dueña de la unidad para validación de tenant del operador.

### 3. Servicios (`crm_services.py` y `unidad_services.py`)
- `crm_services.listar_fotografias_cliente_autenticado`:
  Extrae identidad del JWT (`_contexto_cliente_cu30`), valida acceso a la unidad, delega a `crm_repos.listar_fotografias_cliente_cu30` y agrega `url_archivo` con el endpoint autenticado.
- `crm_services.obtener_archivo_fotografia_cliente_autenticado`:
  Valida propiedad de unidad y tenant, obtiene metadatos de `crm_repos`, valida contención de ruta con `relative_to(backend/uploads/unidades)` y existencia en disco.
- `unidad_services.cargar_fotografia_unidad`:
  Valida pertenencia de la unidad a la empresa del usuario (o admin global), valida archivo (MIME permitido, tamaño máximo 10MB, extensión), genera nombre seguro en disco y persiste en `t_unidad_fotografia`.

### 4. Rutas (`crm_routes.py` y `unidad_routes.py`)
- `crm_routes`:
  - `GET /cliente/unidades/{id_unidad}/fotografias` (rol `CLIENTE`)
  - `GET /cliente/unidades/{id_unidad}/fotografias/{id_fotografia}/archivo` (rol `CLIENTE`)
- `unidad_routes`:
  - `POST /api/unidades/{id_unidad}/fotografias` (roles `JEFE_OBRA`, `RESPONSABLE`, `ADMINISTRADOR_EMPRESA`, `ADMINISTRADOR` o permiso `Modificar_obras` / `Registrar_avances`).

## Contexto de Tenant y Permisos
1. Clientes solo leen unidades explícitamente asociadas en `t_crm_cliente_unidad` de su mismo `id_empresa`.
2. El cliente nunca puede descargar fotografías de unidades de otros clientes o de obras de otro tenant.
3. El frontend no envía `id_cliente` ni `id_empresa`; se resuelven obligatoriamente de los claims del JWT.
4. Para la carga administrativa, un `ADMINISTRADOR_EMPRESA` o `JEFE DE OBRA` solo puede subir imágenes a unidades de obras de su empresa; `ADMINISTRADOR` global tiene acceso general.

## Validación Prevista
1. Pruebas unitarias backend actualizadas en `backend/tests/test_crm_cliente_hu115_hu117.py` sustituyendo referencias a `incidencia_repos` por `crm_repos` y `t_unidad_fotografia`.
2. Pruebas para carga administrativa de fotografías de unidad (validación de tenant, rol y archivo).
3. Verificación de no-regresión en `test_crm_cliente_unidades.py` y `test_avance_hu114.py`.
4. Compilación de Python y comprobación de `git diff --check`.
5. Verificación de build y pruebas frontend en Angular.
6. Preparación y verificación de la prueba real con FABRICIO (id_usuario 20, empresa 1, id_unidad 9).

## Interfaz Frontend para Jefe de Obra (Carga y Galería de Fotografías)

### 1. Componente y Servicio
- Componente: `ProyectoEstructuraComponent` (`frontend/src/app/pages/proyectos/estructura/proyecto-estructura.ts` y `.html`).
- Servicio: `UnidadesService` (`frontend/src/app/services/unidades.ts`), incorporando:
  - `listarFotografias(idUnidad)`: `GET /api/unidades/{id_unidad}/fotografias`
  - `subirFotografia(idUnidad, archivo, esPrincipal, orden)`: `POST /api/unidades/{id_unidad}/fotografias` mediante `FormData` sin alterar `Content-Type`.

### 2. Control de Permisos y Roles
- Método `puedeSubirFotografias()`:
  - Autoriza: `JEFE DE OBRA`, `JEFE_OBRA`, `RESPONSABLE`, `ADMINISTRADOR_EMPRESA`, `ADMINISTRADOR`, o usuarios con permisos `Modificar_obras` / `Registrar_avances`.
  - Bloquea estrictamente: rol `CLIENTE` (los clientes nunca ven controles de carga y solo visualizan sus unidades desde `/panel`).

### 3. Validaciones y UX
- Tipos permitidos: JPG, JPEG, PNG, WEBP.
- Tamaño máximo: 10 MB.
- Previsualización local con `URL.createObjectURL(file)`.
- Botones de acción [Confirmar Subida] y [Cancelar].
- Estado de carga (`subiendoFoto`) con spinner y prevención de doble submit.
- Galería de fotografías existentes con contador, fecha, tamaño y badge de foto principal.
- Estado vacío cuando no existen fotografías con mensaje explicativo.

### 4. Resultados de Validación
- Pruebas unitarias frontend: 10/10 pasadas (`npm run test:cu30`).
- Pruebas unitarias backend: 42/42 pasadas (`test_crm_cliente_hu115_hu117.py`, `test_crm_cliente_unidades.py`, `test_avance_hu114.py`).
- Compilación de producción: `ng build` exitoso (EXIT CODE 0).
- Simulación de flujo end-to-end: Carga con `PABLOPT` (HTTP 201) → Visualización en galería admin (HTTP 200) → Consulta y descarga con `FABRICIO` cliente (HTTP 200).
