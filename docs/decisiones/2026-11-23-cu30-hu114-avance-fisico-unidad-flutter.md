# Decisión de Diseño: CU30 HU114 – Consulta de Avance Físico de Unidad para Cliente en Flutter

## Contexto y Alcance

En la Etapa 1 se estableció la navegación base hacia `ClienteUnidadesScreen` para usuarios con rol `CLIENTE`.
Esta etapa implementa de forma exclusiva la **HU114 – Consultar el avance físico de su unidad**:
1. Conectar `ClienteUnidadesScreen` con el endpoint de unidades del cliente (`GET /api/crm/cliente/unidades`).
2. Permitir seleccionar una unidad autorizada y navegar a `ClienteUnidadDetalleScreen`.
3. En `ClienteUnidadDetalleScreen`, consultar el avance físico mediante el endpoint verificado (`GET /api/proyectos/{id_obra}/avances/cliente/unidades/{id_unidad}`).
4. Renderizar el porcentaje actual de avance físico y el historial cronológico de reportes con sus fechas, observaciones y estados.

### Exclusiones Estrictas
- NO implementar HU115 (fotografías de unidad).
- NO implementar HU116 (comunicaciones de la constructora).
- NO implementar HU117 (solicitudes y respuestas).
- NO modificar el backend ni crear rutas adicionales.
- NO alterar el comportamiento para administradores, jefes de obra, supervisores o personal operativo.

## Capas y Contratos

### 1. Endpoints Backend Reales Consumidos

#### Endpoint A: Listado de unidades del cliente (CU30)
- **Método HTTP:** `GET`
- **Ruta:** `/api/crm/cliente/unidades`
- **Headers:** `Authorization: Bearer <token_jwt>` (Rol `CLIENTE`).
- **Respuesta real del backend:**
```json
{
  "success": true,
  "data": [
    {
      "id_cliente_unidad": 1,
      "id_cliente": 54,
      "id_unidad": 9,
      "estado_asociacion": "COMPRADO",
      "monto_pactado": 85000.0,
      "fecha_asociacion": "2026-03-15T10:00:00",
      "observaciones": null,
      "codigo_unidad": "DEP-302",
      "tipo_unidad": "DEPARTAMENTO",
      "superficie": 78.5,
      "estado_unidad_actual": "EN_CONSTRUCCION",
      "id_obra": 8,
      "nombre_obra": "Edificio Los Sauces",
      "codigo_obra": "OBR-008"
    }
  ]
}
```

#### Endpoint B: Historial de avance físico de la unidad (HU114)
- **Método HTTP:** `GET`
- **Ruta:** `/api/proyectos/{id_obra}/avances/cliente/unidades/{id_unidad}`
- **Headers:** `Authorization: Bearer <token_jwt>` (Rol `CLIENTE`).
- **Respuesta real del backend:**
```json
{
  "success": true,
  "data": [
    {
      "id_avance": 45,
      "id_obra": 8,
      "id_unidad": 9,
      "porcentaje_avance": 65.5,
      "estado_unidad": "EN_CONSTRUCCION",
      "fecha_registro": "2026-11-20T14:30:00",
      "observacion": "Conclusión de obra gruesa e instalaciones sanitarias."
    }
  ]
}
```

### 2. Capa de Servicios Móvil
- `UnidadService` (`mobile/lib/services/unidad_service.dart`):
  - Incorpora `listarUnidadesCliente()`: Realiza `GET /api/crm/cliente/unidades` utilizando el interceptor `ApiClient.dio` con token automático.
- `AvanceService` (`mobile/lib/services/avance_service.dart`):
  - Incorpora `consultarAvanceFisicoUnidadCliente({required int idObra, required int idUnidad})`: Realiza `GET /api/proyectos/$idObra/avances/cliente/unidades/$idUnidad`.

### 3. Capa de Presentación (UI)
- `ClienteUnidadesScreen` (`mobile/lib/screens/cliente_unidades_screen.dart`):
  - Ciclo de vida con `_cargarUnidades()`.
  - Estados: Cargando (`CircularProgressIndicator`), Error con retry, Vacío y Lista de unidades.
  - Cada tarjeta presenta: Código de unidad, Nombre de obra, Tipo de unidad, Superficie, Estado actual (`ConstructionStatusBadge`), Estado de asociación (`COMPRADO` / `RESERVADO`) y flecha de navegación.
- `ClienteUnidadDetalleScreen` (`mobile/lib/screens/cliente_unidad_detalle_screen.dart`):
  - Encabezado con datos del inmueble seleccionado.
  - Tarjeta de avance global con indicador de porcentaje animado y barra lineal.
  - Historial ordenado cronológicamente de avances registrados (fecha formateada, porcentaje, estado y observación técnica).
  - Manejo completo de estados (carga, vacío, error, éxito).
  - Botón de retorno en AppBar y soporte para Light/Dark mode.

## Contexto de Tenant y Permisos
- El backend resuelve el `id_cliente`, `id_usuario` e `id_empresa` exclusivamente a partir del token JWT.
- En la llamada de avance físico, el backend valida que la unidad pertenezca a la obra y esté asignada al cliente autenticado (`EXISTS in t_crm_cliente_unidad`); de lo contrario, responde 404/403.
- El cliente móvil solo puede consultar unidades devueltas por su propio listado autorizado.

## Validación Prevista
1. Análisis estático completo con `flutter analyze` en `mobile/`.
2. Pruebas de widgets y unitarias para HU114 en `mobile/test/cliente_unidades_test.dart`.
3. Verificación de no-regresión en la suite completa de pruebas móviles (`flutter test`).
