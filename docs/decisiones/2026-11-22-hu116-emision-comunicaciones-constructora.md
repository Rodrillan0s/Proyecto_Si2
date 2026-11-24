# Decisión de Diseño: HU116 – Emisión y Recepción de Comunicaciones Directas de la Constructora

## Contexto y Alcance
La auditoría de la HU116 confirmó que el flujo de consulta/recepción para el cliente (`GET /api/crm/cliente/comunicaciones` y la vista en `panel.html`) se encuentra completamente implementado, probado y funcional. Sin embargo, no existía en el backend ningún endpoint para que la empresa constructora cree o envíe comunicaciones a un cliente (`POST /api/crm/comunicaciones`), ni existía interfaz en el frontend administrativo para redactar y despachar dichos avisos. Por esta razón, el cliente Fabricio (`id_usuario=20`, `id_cliente=54`, `id_empresa=1`) siempre registraba 0 comunicaciones.

Esta decisión formaliza el diseño y la implementación del flujo de emisión para completar el ciclo de vida de la HU116:
`Personal de la constructora rediseña/redacta comunicación` → `Valida tenant, cliente, obra y unidad` → `Persiste en obras.notificacion` → `Cliente autenticado consulta y visualiza su comunicado en el portal`.

## Capas y Contratos

### 1. Base de datos (`obras.notificacion`)
Se reutiliza la tabla existente `obras.notificacion` sin alterar su estructura ni requerir migraciones:
- `titulo`: VARCHAR NOT NULL.
- `cuerpo`: TEXT NOT NULL.
- `tipo_referencia`: VARCHAR (por defecto 'COMUNICACION').
- `nro_usuario`: INTEGER NOT NULL (ID del usuario destinatario, resuelto a partir de `t_crm_cliente.id_persona` -> `t_usuario.id_usuario`).
- `leido`: BOOLEAN NOT NULL DEFAULT false.
- `fecha_creacion`: TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP.
- `id_empresa`: INTEGER NULL (tenant del emisor y receptor).
- `id_obra`: INTEGER NULL (obra asociada al aviso, opcional).

### 2. Repositorio (`crm_repos.py` y `notificaciones_repos.py`)
- `crm_repos.obtener_id_usuario_por_cliente(id_cliente, id_empresa)`:
  Resuelve el `id_usuario` a partir de `t_crm_cliente` y `t_usuario` vinculados por `id_persona` en la misma empresa.
- `crm_repos.validar_unidad_asociada_cliente(id_cliente, id_unidad)`:
  Comprueba que la unidad esté asociada al cliente en `t_crm_cliente_unidad`.
- `notificaciones_repos.crear_comunicacion_cliente_db(titulo, cuerpo, tipo_referencia, nro_usuario, id_empresa, id_obra)`:
  Inserta de forma parametrizada en `obras.notificacion` garantizando `leido = false` y retorna los metadatos creados.

### 3. Servicios (`crm_services.py`)
- Función `crear_comunicacion_cliente(data: dict, token: dict, ip: str = None)`:
  1. Resuelve `id_empresa` del JWT mediante `_empresa(token)`.
  2. Valida la existencia y pertenencia del cliente destinatario (`crm_repos.obtener_cliente_por_id`).
  3. Resuelve el `nro_usuario` del cliente. Si no tiene usuario activo con acceso, rechaza con error claro.
  4. Valida título y cuerpo no vacíos.
  5. Si se indica `id_obra`, valida pertenencia de la obra a la empresa.
  6. Si se indica `id_unidad`, valida pertenencia al tenant y correspondencia con el cliente. Si no se especificó `id_obra`, se deriva de la unidad.
  7. Persiste en `obras.notificacion` y registra la acción en bitácora.

### 4. Rutas (`crm_routes.py`)
- `POST /api/crm/comunicaciones` (código HTTP 201):
  - Autorización: Requiere rol administrativo/operativo (`ADMINISTRADOR`, `ADMINISTRADOR_EMPRESA`, `JEFE DE OBRA`, `RESPONSABLE`) o permisos `Modificar_clientes` / `Registrar_clientes`.
  - Roles cliente y operarios no autorizados reciben 403 Forbidden.
  - No acepta `id_empresa` en el cuerpo; el tenant se deriva exclusivamente del token JWT autenticado.

### 5. Frontend (`crm.service.ts`, `crm.ts`, `crm.html`)
- `crm.service.ts`: método `enviarComunicacionCliente(payload)`.
- `crm.ts`: estado modal `mostrarModalComunicacion`, formulario `formComunicacion`, validaciones y gestión reactiva.
- `crm.html`:
  - Botón de acción `💬 Comunicar` en la tabla de clientes.
  - Botón `+ Enviar Comunicación` en la ficha de detalle e historial del cliente (`mostrarModalDetalle`).
  - Modal interactivo de redacción con feedback visual de carga, selección opcional de obra/unidad y manejo de errores.

## Validación Prevista
- Pruebas unitarias para roles autorizados, roles denegados (403), validación de aislamiento multi-tenant, unidades ajenas, persistencia en `obras.notificacion` con `leido=false`, consulta exitosa por parte del cliente mediante `GET /api/crm/cliente/comunicaciones` y verificación de no-regresión para HU114, HU115 y HU117.
- Prueba real con el cliente Fabricio (`id_usuario=20`, `id_cliente=54`, `id_obra=8`, `id_unidad=9`) comprobando inserción en BD y lectura correcta por el servicio.

## Diagnóstico y Corrección del Flujo de Envío en Frontend (HU116)
- **Causa del bloqueo visual en "Enviando comunicación..."**:
  1. Uso innecesario de `takeUntilDestroyed(this.destroyRef)` en una petición HTTP POST transaccional mutativa, susceptible a abortar el stream de respuesta ante eventos de ciclo de vida del componente.
  2. Ausencia del operador RxJS `finalize()`, provocando que cualquier interrupción del Observable deje `guardandoComunicacion = true` permanentemente.
  3. `cerrarModalComunicacion()` no reseteaba los valores de `formComunicacion`, manteniendo datos residuales.
- **Error 401 en consola ("Petición 401 sin token...")**:
  Generado por `error-interceptor.ts` en peticiones de hidratación/arranque cuando `authService.obtenerToken()` aún es nulo. Completamente independiente de `POST /api/crm/comunicaciones` que incluye Authorization Bearer y recibe HTTP 201 Created.
- **Acciones correctivas**:
  1. Incorporar `finalize(() => { this.guardandoComunicacion = false; this.cdr.detectChanges(); })` en el stream de `crm.service.ts`.
  2. Retirar `takeUntilDestroyed` de la mutación HTTP.
  3. Limpiar integralmente `formComunicacion` y `guardandoComunicacion` al cerrar y al enviar exitosamente.
  4. Garantizar feedback de éxito inmediato con `mostrarExito()` y detección explícita del 201 (`res?.success`).
  5. Evitar peticiones redundantes adicionales innecesarias en `crm.ts`.

