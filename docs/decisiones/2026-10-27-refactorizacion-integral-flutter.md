# Decisión de Arquitectura: Refactorización Integral Móvil (Flutter) - OBRATEC

**Fecha:** 2026-10-27  
**Estado:** Implementada y Validada  
**Alcance:** Exclusivamente cliente móvil Flutter (`mobile/`).  
**Exclusiones expresas:** Backend, PostgreSQL, migraciones, infraestructura, Angular, CU38 (Planos y documentos) y CU39 (Cronogramas y planificación).

---

## 1. Contexto y Diagnóstico
La aplicación móvil OBRATEC requiere modernización visual y de rendimiento sin reescritura total:
1. **Rendimiento y Ciclo de Vida:**
   - Evitar llamadas HTTP duplicadas en `initState` y en callbacks de navegación.
   - Corregir el cálculo de KPIs en el Dashboard: los indicadores aparecían en cero debido a discrepancias en las claves (`estado` vs `estado_obra`) y normalización de mayúsculas/minúsculas frente a los valores devueltos por `sp_listar_obras`.
   - Reemplazar bloqueos de pantalla completa por skeleton y placeholders locales.
2. **Sistema de Diseño Unificado:**
   - Inspirado en el prototipo de 12 pantallas (modos oscuro y claro):
     - Login estilizado con fondo temático y selector de pestañas limpio.
     - Dashboard con cabecera de marca OBRATEC, tarjeta compacta de contexto multiempresa, cuadrícula 2x2 de métricas y accesos rápidos limpios.
     - Lista de proyectos compacta con chips de estado horizontales, buscador y tarjetas de alta densidad informativa.
     - Detalle de proyecto con pestañas claras (Resumen, Estructura, Unidades, Equipo/Módulos) y barra de acciones inferiores.
     - Estados vacíos ilustrativos (p. ej. Estructura vacía con cubo 3D isométrico).
     - Perfil y Ajustes estructurado en tarjetas de información sin spinner de bloqueo total.
3. **Integración Funcional:**
   - **Consultas Técnicas de Obra:** Integración completa de listado por proyecto, detalle, creación y respuestas técnicas consumiendo endpoints existentes de `/api/consultas-tecnicas`, respetando permisos y aislamiento por empresa/proyecto.
   - **Asistente Inteligente Administrativo y Operativo:** Actualización del cliente móvil para comunicarse con `/api/ai/consulta`, `/api/ai/operacion/confirmar` y `/api/ai/operacion/cancelar`. Restringido a `ADMINISTRADOR` y `ADMINISTRADOR_EMPRESA`, con soporte para vista previa de acciones propuestas y confirmación explícita sin respuestas simuladas ni doble confirmación.

4. **Iteración 2 — Ajustes Específicos y Comandos de Voz:**
   - **Plan SaaS en Ajustes/Perfil:** Añadir sección con tarjeta informativa del plan SaaS consumiendo `/api/suscripciones/mi-empresa` (exclusivo para `ADMINISTRADOR` y `ADMINISTRADOR_EMPRESA`; oculto estrictamente para `CLIENTE` y operarios).
   - **Comandos de Voz en Asistente:** Integrar reconocimiento de voz (`SpeechToText` / `ReportesVoice`) directamente en la barra de consulta del `AsistenteScreen` con micro-animación de escucha y transcripción en vivo.
   - **Nombres Reales de Empresa:** Corregir el mapeo de `nombre_empresa` y `nit` desde `/api/empresas/` en el modal selector y la propagación a `AuthProvider` para eliminar la etiqueta genérica "Empresa Activa: Empresa".
   - **Optimización de Latencia y Apertura Instantánea:** Eliminar `await` antes de abrir `showModalBottomSheet` en selectores y modales de creación, mostrando el modal inmediatamente con skeleton/carga interna no bloqueante.

5. **Iteración 3 — Selector de Enrutamiento Servidor / Local (Debug):**
   - Incorporar en `PerfilScreen` un selector de destino de red (`Entorno / Servidor API`) con persistencia en `TokenStorage` (`custom_api_url`) y actualización inmediata de `ApiClient.dio.options.baseUrl`.
   - Opciones:
     - **Servidor Local:** `http://127.0.0.1:5000` (puerto TCP con túnel `adb reverse`).
     - **Servidor Web / Despliegue:** `https://obratec-66o2.onrender.com`.
     - **Personalizado / IP LAN:** Permite ingresar una dirección manual (ej. `http://192.168.1.X:5000`).

---

## 2. Decisiones de Arquitectura y Patrones

### Capas y Flujo
- **Presentación:** Widgets desacoplados (`mobile/lib/screens/`, `mobile/lib/widgets/`).
- **Estado y Autenticación:** `AuthService` en `mobile/lib/services/auth_service.dart` manteniendo token JWT, empresa activa (`idEmpresaActiva`), rol del usuario y contexto de vista global.
- **Servicios:** Clientes HTTP tipados (`mobile/lib/services/`) con manejo centralizado de cabeceras `Authorization: Bearer <token>`, `X-Id-Empresa`, timeouts y parseo seguro de excepciones.
- **Diseño Visual:** `mobile/lib/theme/app_theme.dart` como fuente única de verdad para tokens de color (naranja `#EA580C`, azul marino `#0B0F19`, superficies de tarjeta `#161F30`, bordes `#26334D`, y equivalentes en modo claro), tipografías, bordes redondeados y elevaciones.

### Manejo de Multiempresa y Aislamiento
- Todo acceso a recursos valida la pertenencia y envía `X-Id-Empresa` cuando no es vista global.
- Al conmutar empresa, los datos en memoria de proyectos, consultas y dashboard se invalidan y recargan inmediatamente para prevenir fugas visuales entre empresas.

### Restricciones de Dominio y Calidad
- Prohibición de identificadores académicos visibles (`CU23`, `CU29`, etc.) en la UI.
- Sin datos ficticios: las métricas provienen del conteo real de obras devueltas por el backend.
- Prevención total de `RenderFlex overflowed` mediante `SingleChildScrollView`, `Flexible`, `Expanded` y `SafeArea`.

---

## 3. Plan de Verificación y Resultados Reales
1. **Análisis Estático:** `flutter analyze` ejecutado con éxito: **0 issues found** (0 errores, 0 warnings, 0 infos).
2. **Suite de Pruebas Automatizadas:** `flutter test` ejecutado con éxito: **42/42 pruebas pasadas** (100% éxito en modelos, contratos, permisos y widgets de incidencias/obras).
3. **Validación de UI y Compatibilidad de Temas:**
   - Modo Oscuro y Claro verificados visualmente en Login, Dashboard, Proyectos, Detalle de Proyecto, Estructura WBS, Unidades, Asistente IA, Consultas Técnicas y Perfil.
   - Estado vacío de Estructura actualizado con representación isométrica 3D y botón de acción rápida.
   - Selector tipo segmented en modal de creación de elementos de estructura (`[Torre / Bloque]`, `[Nivel]`, `[Sector]`).
   - Sin spinners bloqueantes en pantalla de Perfil (renderizado inmediato desde `AuthProvider` con barra de progreso no intrusiva).
   - Eliminación de métricas en cero en Dashboard mediante normalización de estados y claves del backend.
   - Restricción de acceso al Asistente Inteligente móvil para roles `ADMINISTRADOR` y `ADMINISTRADOR_EMPRESA`.
   - Cero identificadores académicos (`CUxx`, `HUxx`, sprints) en toda la interfaz de usuario.
   - **Iteración 2 Verificada:**
     - Apartado de Plan SaaS y Suscripción integrado en Ajustes y Cuenta (`PerfilScreen`) visible exclusivamente para administradores y oculto para clientes y operarios.
     - Comandos y dictado por voz (`SpeechToText` / `ReportesVoice`) integrados directamente en `AsistenteScreen` con banner de escucha activa y botón dedicado.
     - Eliminada la latencia de apertura de modales: selector de empresa y modal de nuevo proyecto abren a 0 ms con carga interna y precaché de tipos.
     - Nombres reales de empresa y NIT reflejados correctamente en el selector y en todos los encabezados y etiquetas de la aplicación.
