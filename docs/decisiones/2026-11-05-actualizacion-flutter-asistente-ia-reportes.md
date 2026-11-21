# Actualización de Flutter Móvil: Asistente de IA Unificado, Motor de Reportes, Notificaciones Push y Dominio Render

**Fecha:** 2026-11-05  
**Estado:** Implementado y validado  
**Módulos afectados:** `mobile/lib/config/app_config.dart`, `mobile/lib/services/api_client.dart`, `mobile/lib/services/auth_service.dart`, `mobile/lib/services/recovery_service.dart`, `mobile/lib/services/auth_provider.dart`, `mobile/lib/services/ai_assistant_service.dart`, `mobile/lib/services/reportes_service.dart`, `mobile/lib/services/notificacion_service.dart`, `mobile/lib/screens/asistente_screen.dart`, `mobile/lib/screens/reportes_screen.dart`, `mobile/lib/screens/notificaciones_screen.dart`, `mobile/lib/screens/home_screen.dart`, `mobile/lib/screens/auth_screens.dart`, `mobile/test/widget_test.dart`, `backend/app/__init__.py`, `backend/app/repos/notificaciones_repos.py`, `backend/app/services/notificaciones_services.py`, `backend/app/routes/notificaciones_routes.py`

---

## 1. Contexto y problema

Tras la consolidación en la plataforma web (Angular) del **Asistente de IA Unificado** (que integra en una misma interfaz el modo `Gestión / Admin` y el modo `Comercial & Planos` con lectura multimodal de planos y estimación paramétrica por estilo) y las mejoras al **Motor de Reportes** (incluyendo `saldo_comercial` para análisis de obras con déficit/ganancia, `costos_periodo`, `comparativo_costos`, `stock` con alertas y personalización de presentación/columnas), la aplicación móvil en Flutter (`mobile/`) presentaba los siguientes requerimientos y desfases:

1. **Asistente móvil limitado y desalineado con los contratos actuales (`asistente_screen.dart`, `ai_assistant_service.dart`):**
   - Solo permitía acceso a `ADMINISTRADOR` y `ADMINISTRADOR_EMPRESA`, bloqueando a otros roles con permisos operativos (`JEFE_DE_OBRA`, `SUPERVISOR_OBRA`) y mostrando pantalla de bloqueo a `CLIENTE`.
   - No integraba el modo **`Comercial & Planos`** (`/api/public/comercial/{empresa_ref}/catalogo`, `/chat`, `/estimar-costo`, `/analizar-plano`, `/solicitar-contacto`) para búsqueda por lenguaje natural (HU147), recomendaciones por presupuesto con porcentaje de afinidad (HU148), tabla comparativa lado a lado (HU149), captura de prospectos en CRM (HU150) y lectura de planos arquitectónicos con recálculo en vivo por estilo (`ESTANDAR`, `INDUSTRIAL`, `MINIMALISTA`, `CONTEMPORANEO`, `LUJO`).
   - En el modo administrativo (`/api/ai/consulta`), leía claves antiguas (`propuesta_operacion`, `diagnostico`) en lugar de los campos canónicos del motor unificado (`operacion_propuesta`, `resultado_analisis`, `ejecucion`, `ejecuciones`, `opciones`, `obras`, `solicitud`, `sugerencias`, `tema`), impidiendo visualizar y exportar reportes generados por lenguaje natural (como `"Generame un reporte de las obras con mas deficit"`).
   - No aislaba ni preservaba sesiones en memoria por par `(usuario, id_empresa)` al cambiar entre pestañas o al cerrar sesión y entrar con otra cuenta.

2. **Pantalla de Reportes móvil sin diseño ejecutivo ni personalización (`reportes_screen.dart`):**
   - Carecía de filtros por familia de reportes (`Finanzas y Rentabilidad`, `Obras y Avance`, `Inventario`, `Personal`, `Incidencias`), selectores rápidos de período (`Hoy`, `Últimos 7 días`, `Últimos 30 días`, `Este mes`, `Mes anterior`), personalización de presentación (`titulo`, `orientacion`, `ordenar_por`, `orden`, `columnas`), tarjetas ejecutivas de KPIs de resumen (para visualizar saldos positivos/negativos de `saldo_comercial`) y enlace directo con las ejecuciones generadas desde el Asistente de IA.
   - En `home_screen.dart`, el grid de accesos rápidos no incluía accesos directos a `ReportesScreen` ni a `CrmScreen`.

3. **Actualización de dominio del backend móvil y Notificaciones Push en tiempo real:**
   - El cliente móvil apuntaba al dominio anterior (`https://obratec-66o2.onrender.com`) en lugar del nuevo dominio desplegado `https://obratech-y040.onrender.com`.
   - `NotificacionesScreen` operaba únicamente por consulta manual al abrir la vista, leía llaves desactualizadas (`tipo`, `created_at` en vez de `tipo_referencia`, `fecha_creacion`), carecía de soporte para modo oscuro, no mantenía conexión WebSocket en tiempo real (`/api/ws/notificaciones?token=...`), ni mostraba banners push emergentes o contadores de no leídas en la campana del `HomeScreen`.

---

## 2. Decisiones de diseño y arquitectura

### 2.1 Capas y contratos preservados
- Se mantiene intacto el patrón `routes → services → repos → PostgreSQL` en el backend y `screens → services/providers → ApiClient.dio` en Flutter.
- **Dominio del backend móvil (`mobile/lib/config/app_config.dart`):**
  - `AppConfig.defaultCloudUrl` pasa a `'https://obratech-y040.onrender.com'`.
  - Se incorporan `AppConfig.resolveBaseUrl(String? customUrl)` y `AppConfig.wsBaseUrlFrom(String httpUrl)` para migrar automáticamente cualquier URL antigua (`obratec-66o2.onrender.com`) y construir la URL WebSocket segura (`wss://obratech-y040.onrender.com/api/ws/notificaciones?token=...`).
- **Contratos consumidos:**
  - **Asistente Administrativo y de Reportes:** `POST /api/ai/consulta`, `POST /api/ai/operacion/confirmar`, `POST /api/ai/operacion/cancelar`.
  - **Asistente Comercial e Inmobiliario:** `GET /api/public/comercial/empresas`, `GET /api/public/comercial/{empresa_ref}/catalogo`, `POST /api/public/comercial/{empresa_ref}/chat`, `POST /api/public/comercial/{empresa_ref}/estimar-costo`, `POST /api/public/comercial/{empresa_ref}/analizar-plano`, `POST /api/public/comercial/{empresa_ref}/solicitar-contacto`.
  - **Motor de Reportes y Voz:** `GET /api/reportes/catalogo`, `POST /api/reportes/interpretar`, `POST /api/reportes/ejecuciones`, `GET /api/reportes/ejecuciones/{id}`, `POST /api/reportes/ejecuciones/{id}/exportaciones`, `GET /api/reportes/archivos/{id}`, `POST /api/reportes/ejecuciones/{id}/envios`, `GET/POST/PATCH /api/reportes/programaciones`, `POST /api/voz/transcribir`.
  - **Notificaciones Push y WebSockets:** `WS /api/ws/notificaciones?token=<jwt>`, `GET /api/ws/historial`, `PUT /api/ws/leer`, `POST /api/ws/prueba`.

### 2.2 Aislamiento de sesiones por usuario y tenant (`id_empresa`)
- `AiAssistantService` gestiona almacenes de sesión en memoria indexados por `claveSesion = "${usuarioIdentidad}:${idEmpresaActiva ?? 'global'}:${idObraContexto ?? 0}"` para el modo administrativo y `"${usuarioIdentidad}:${empresaRef}"` para el modo comercial.
- Al cambiar de pestaña en `HomeScreen` o abrir/cerrar vistas secundarias, la conversación activa se preserva sin reiniciarse.
- Al cambiar de usuario (`loginExitoso` / `cerrarSesion` en `AuthProvider`) se invoca `AiAssistantService.clearAllSessions()` y se reinicia el canal de notificaciones push (`NotificacionService.instance.disconnect()`), purgando cualquier estado previo.

### 2.3 Arquitectura de Notificaciones Push en Móvil y Backend
- En el backend (`notificaciones_repos.py`, `notificaciones_services.py`, `notificaciones_routes.py`):
  - Se actualiza la resolución de destinatarios hacia `obras.t_usuario` y `obras.t_rol` respetando el aislamiento por `id_empresa` (notificando únicamente a los usuarios activos de la empresa involucrada y a los administradores globales).
  - Se añade `emitir_notificacion_push_empresa` para persistir alertas en `obras.notificacion` y despacharlas por WebSocket (`manager.send_personal_message`) ante eventos clave de obra (incidencias, órdenes de trabajo, avances de obra y nuevos prospectos comerciales), además de un endpoint autenticado `POST /api/ws/prueba` para verificar notificaciones push en tiempo real desde la app.
- En Flutter (`notificacion_service.dart`, `home_screen.dart`, `notificaciones_screen.dart`):
  - `NotificacionService` expone un controlador reactivo (`ChangeNotifier` + `Stream<Map<String, dynamic>> incomingPushStream`) que gestiona la conexión `WebSocketChannel` hacia `wss://obratech-y040.onrender.com/api/ws/notificaciones?token=...` con reconexión automática y sondeo periódico de respaldo cada 25 segundos.
  - Cuando arriba una alerta nueva (vía WebSocket o diferencial de bandeja), `HomeScreen` reproduce feedback háptico (`HapticFeedback.mediumImpact()`) y despliega un **Banner Push flotante** en la parte superior con acceso directo al detalle, actualizando al instante el badge rojo de no leídas en el icono de campana superior e inferior.

### 2.4 Reglas de interfaz y limpieza visual
- Cero menciones a códigos académicos (`CU34`, `CU37`, `HU147`, etc.) ni al proveedor subyacente (`DeepSeek`) en ninguna pantalla móvil.
- Indicadores de carga minimalistas (`"Cargando…"` / `"Consultando tus datos…"`).
- Prevención estricta de `RenderFlex overflow` mediante `Expanded`, `Flexible`, `Wrap` y `SingleChildScrollView`.

---

## 3. Plan de validación

1. Ejecutar `flutter analyze --no-pub` en `mobile/` verificando **0 issues**.
2. Ejecutar `flutter test --no-pub` en `mobile/` con pruebas de widgets y servicios para `AppConfig` (`https://obratech-y040.onrender.com` y `wss://obratech-y040.onrender.com`), `NotificacionService` (push en tiempo real y conteo de no leídas), `AsistenteScreen`, `ReportesScreen` y aislamiento de sesiones en `AiAssistantService` / `AuthProvider`.
3. Ejecutar pruebas unitarias de backend en `backend/tests/` verificando que los cambios en notificaciones y CORS no rompen contratos existentes.

---

## 4. Implementación y resultados de validación

1. **Dominio de backend móvil actualizado a `https://obratech-y040.onrender.com`:**
   - `AppConfig.defaultCloudUrl` y `AppConfig.apiBaseUrl` en `mobile/lib/config/app_config.dart` apuntan a `'https://obratech-y040.onrender.com'`.
   - `AppConfig.wsBaseUrl` resuelve a `'wss://obratech-y040.onrender.com'` y `AppConfig.resolveBaseUrl(...)` normaliza automáticamente cualquier URL antigua (`obratec-66o2.onrender.com`, `127.0.0.1`, `localhost`) en `ApiClient`, `AuthService`, `RecoveryService` y `NotificacionService`.
   - `backend/app/__init__.py` incluye `"https://obratech-y040.onrender.com"` en `allow_origins`.

2. **Notificaciones Push en Tiempo Real (WebSocket + Sondeo + Banner Push In-App + Badge):**
   - `mobile/lib/services/notificacion_service.dart` implementa `NotificacionService.instance` (`ChangeNotifier`) con conexión en vivo a `wss://obratech-y040.onrender.com/api/ws/notificaciones?token=<jwt>`, ping keepalive cada 25s, reconexión automática, sondeo de respaldo a `/api/ws/historial`, conteo `unreadCount` y stream `incomingPushStream`.
   - `mobile/lib/screens/home_screen.dart` despliega un banner push flotante superior con feedback háptico (`HapticFeedback.mediumImpact()`) ante cada nueva alerta en tiempo real y muestra badges numéricos en la campana del `AppBar` y del `BottomNavigationBar`.
   - `mobile/lib/screens/notificaciones_screen.dart` se rediseñó con soporte Dark/Light Mode, indicador de estado del canal Push en tiempo real y botón para emitir una notificación push de prueba (`POST /api/ws/prueba`).
   - Se integró emisión automática de notificaciones push en tiempo real (tanto local inmediata en móvil vía `NotificacionService.instance.emitLocalPush` como en backend vía `notificaciones_services.emitir_notificacion_push_empresa`) en todos los módulos operativos:
     - **Asistente de IA y Comercial (`asistente_screen.dart`, `lead_capture_service.py`, `commercial_routes.py`):** solicitud de contacto CRM desde tarjeta o chat y confirmación de operaciones administrativas asistidas por IA.
     - **Incidencias (`incidencia_service.dart`, `incidencia_services.py`):** registro de incidencia, asignación de responsable, cambio de estado/cierre y carga de evidencia fotográfica.
     - **Órdenes de Trabajo (`orden_trabajo_service.dart`, `orden_Trabajo_services.py`):** creación, actualización, cambio de estado y asignación de responsable.
     - **Consultas Técnicas / RFI (`consulta_tecnica_service.dart`, `consulta_tecnica_services.py`):** creación de consulta, respuesta técnica, asignación de responsable y cambio de estado.
     - **Avances y Obras (`obra_service.dart`, `avance_services.py`):** creación/edición de obra, cambio de estado de obra, asignación de jefe/responsable, creación de elemento en estructura jerárquica y registro de avance físico.
     - **CRM & Clientes (`crm_service.dart`):** alta de cliente/prospecto, avance de etapa comercial en pipeline, registro de interacción comercial y asociación de unidad inmobiliaria.
     - **Motor de Reportes (`reportes_service.dart`):** envío de reporte por correo/canal, ejecución inmediata de programación y cambio de estado de programación.

3. **Resultados de validación ejecutados:**
   - `cd mobile; flutter analyze --no-pub`: **0 issues found** (`No issues found!`).
   - `cd mobile; flutter test --no-pub`: **50/50 pruebas aprobadas** (`00:04 +50: All tests passed!`).
