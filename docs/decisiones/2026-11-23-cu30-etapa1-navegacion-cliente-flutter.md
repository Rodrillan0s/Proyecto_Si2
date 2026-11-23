# Decisión de Diseño: CU30 Etapa 1 – Navegación y Pantalla Base para el Rol CLIENTE en Flutter

## Contexto y Alcance

El backend para el Caso de Uso CU30 (HU114, HU115, HU116 y HU117) ya se encuentra implementado, probado y validado. Esta etapa aborda el frontend móvil (Flutter) de manera incremental y controlada.

En esta **Etapa 1**, el objetivo es única y exclusivamente **preparar la navegación y la pantalla base para el rol CLIENTE**:
- Condicionar la interfaz de `HomeScreen` para que, cuando el usuario autenticado sea `CLIENTE`, presente la opción destacada **"Mis Proyectos y Unidades"**.
- Permitir la navegación imperativa hacia una nueva pantalla base: `ClienteUnidadesScreen`.
- Establecer en `ClienteUnidadesScreen` la estructura y layout visual base necesario para alojar el listado de proyectos y unidades en las etapas subsiguientes.
- **Exclusiones deliberadas de esta etapa:** No se implementa aún el avance físico (HU114), ni las fotografías de unidad (HU115), ni las comunicaciones oficiales (HU116), ni las solicitudes (HU117). No se agregan llamadas a endpoints nuevos ni se modifica el backend.
- **No afectación a otros roles:** La experiencia y flujos para `ADMINISTRADOR`, `ADMINISTRADOR_EMPRESA`, `JEFE DE OBRA`, `SUPERVISOR`, `RESPONSABLE` y `PERSONAL DE CAMPO` permanecen 100% inalterados.

## Capas y Contratos

### 1. Detección del Rol CLIENTE
Se reutiliza la infraestructura existente en `AuthProvider` (`mobile/lib/services/auth_provider.dart`):
- `auth.rolNormalizado`: Normaliza el rol del JWT recibido en el login (`usuario['nombre_rol']`).
- `auth.esCliente`: Getter booleano que evalúa `rolNormalizado == 'CLIENTE'`.
- No se alteran ni agregan nuevos contratos de autenticación o almacenamiento de tokens (`TokenStorage`).

### 2. Navegación en `HomeScreen`
En `mobile/lib/screens/home_screen.dart`:
- Se evalúa `auth.esCliente`.
- Cuando `auth.esCliente == true`:
  - Se presenta una tarjeta destacada de bienvenida al portal del cliente con el título **"Mis Proyectos y Unidades"**.
  - En la sección de accesos rápidos se incluye la opción **"Mis Proyectos y Unidades"** con el icono `Icons.home_work_rounded`.
  - Al pulsar sobre dicha opción, se ejecuta la navegación estándar de Flutter:
    `Navigator.push(context, MaterialPageRoute(builder: (_) => const ClienteUnidadesScreen()))`.
- Cuando `auth.esCliente == false`:
  - La opción no se muestra y el panel de control operativo para administradores y personal técnico permanece idéntico.

### 3. Pantalla Base `ClienteUnidadesScreen`
En `mobile/lib/screens/cliente_unidades_screen.dart`:
- Pantalla con soporte para modo claro y oscuro (`AppTheme.lightTheme` / `AppTheme.darkTheme`).
- Encabezado con AppBar estándar, botón de retorno y título "Mis Proyectos y Unidades".
- Tarjeta informativa del portal del cliente con resumen de contexto de empresa y propietario.
- Estructura contenedora y estado de preparación (placeholder visual con tarjeta modelo) listo para conectar la lista de proyectos y unidades en la Etapa 2.

## Contexto de Tenant y Permisos
- El rol `CLIENTE` pertenece a un tenant (`id_empresa`) y está enlazado a un usuario (`nro_usuario`).
- En esta etapa no se realizan peticiones de datos de unidades a la API, por lo que no se altera el manejo de tokens ni se realizan consultas no autorizadas.
- La navegación es estrictamente defensiva y aislada por el flag reactivo `auth.esCliente`.

## Validación Prevista
1. Comprobación de análisis estático con `flutter analyze` en `mobile/`.
2. Verificación de imports y ausencia de errores de sintaxis en Dart.
3. Verificación de que ningún archivo de backend ni pantalla administrativa de Flutter resulte afectado.
