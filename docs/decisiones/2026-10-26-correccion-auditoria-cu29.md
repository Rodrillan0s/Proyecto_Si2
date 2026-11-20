# Corrección Integral de Hallazgos de Auditoría CU29: Asistente Administrativo y Operativo

**Fecha:** 2026-10-26  
**Autores:** Equipo de Arquitectura OBRATEC / Antigravity  
**Estado:** En implementación  
**Referencia:** `docs/decisiones/2026-10-26-auditoria-independiente-cu29.md`, `AGENTS.md`, `ARQUITECTURA_Y_PATRONES.md`

---

## 1. Contexto y Alcance

La auditoría independiente realizada sobre el CU29 identificó 16 hallazgos clasificados en:
- **6 Altos (A1-A6):** Fallas en revalidación RBAC/SaaS al confirmar, evasión del ámbito de empresa del ticket, exposición no autorizada en diagnósticos, tabla inexistente en inventario, llamadas a funciones inexistentes en OT/materiales y contaminación de prompt con respuestas históricas no autorizadas.
- **8 Medios (M1-M8):** Vistas previas basadas en resúmenes libres del modelo, selección ciega de la primera obra ante ambigüedades, consumo prematuro de tickets por usuarios ajenos, falta de endpoint de cancelación y sincronización de expiración, falta de captura de errores de dominio (HTTP 500), desincronización de respuestas tardías en Angular ante cambio de contexto, columnas inexistentes en esquemas `personal_obra`/`empresas`, y mocks desalineados con los contratos reales.
- **2 Bajos (B1-B2):** Ruta desactualizada `/equipo-maquinaria` y asunciones fijas en la base de conocimiento, y pérdida del identificador de recurso generado en incidencias.

---

## 2. Decisiones Arquitectónicas y de Patrones

### A. Fase 1: Seguridad y Autorización
1. **Revalidación Re-autorizada en Confirmación (A1, A2):**
   - Durante `ejecutar_propuesta(token, id_propuesta, ip)`:
     - Se carga `ctx = repo.context(db, usuario_token, empresa_solicitada=propuesta['id_empresa'])`.
     - Se invoca `ctx.require(permiso_operacion)` (`Registrar_incidencias`, `Registrar_ordenes_trabajo`, `Registrar_materiales`).
     - Se verifica la capacidad de escritura SaaS de la empresa destino con `suscripcion_policy.exigir_escritura(propuesta['id_empresa'])` y habilitación modular.
     - Se valida que `id_obra` pertenezca fehacientemente a `propuesta['id_empresa']` y a las obras autorizadas del usuario (`ctx.obras_autorizadas`).
     - Se asegura que el token de sesión o el contrato del servicio de dominio reciba forzosamente `id_empresa = propuesta['id_empresa']`, impidiendo que un Administrador Global opere cruzadamente contra obras de otra empresa.
2. **Autorización Granular por Dominio en Diagnóstico Administrativo (A3):**
   - En `analizar_salud_operativa`:
     - Cada bloque de análisis valida su permiso individual:
       - Incidencias: requiere `Visualizar_incidencias`. Aplica restricción por fila si el rol es trabajador (`es_trabajador`).
       - Órdenes de trabajo: requiere `Visualizar_ordenes_trabajo`. Aplica restricción por fila si el trabajador solo puede ver sus asignaciones.
       - Materiales / Inventario: requiere `Visualizar_materiales` o rol de administración (`ADMINISTRADOR`, `ADMINISTRADOR_EMPRESA`).
       - Consultas técnicas (RFI): requiere `Visualizar_consultas_tecnicas`.
     - Si un actor carece de permiso para un dominio, dicho dominio se omite del diagnóstico de forma segura y se anota en `fuentes_omitidas`, retornando una evaluación parcial transparente.
3. **Saneamiento Estricto de Historial Conversacional (A6):**
   - En `assistant_service.py`, el historial pasado al planificador (`historial_conversacion`) solo incluirá preguntas textuales previas del usuario y metadatos de tema, suprimiendo completamente el texto libre devuelto por el modelo (`texto_respuesta`), evitando inyección indirecta de datos de dominios cuyos permisos hayan sido revocados.

### B. Fase 2: Fallos Funcionales e Integraciones de Dominio
1. **Consulta Real de Inventario en PostgreSQL (A4):**
   - Se reemplaza la referencia inexistente `obras.t_inventario_almacen` por la función almacenada oficial del sistema:
     `SELECT id_material, codigo, nombre_material, stock_actual, stock_minimo, precio FROM obras.fn_listar_inventario_empresa(%s, NULL, 'AGOTADO', NULL, 20, 0)`.
2. **Contratos Reales de Servicios de Dominio (A5, B2):**
   - `crear_incidencia`: Llama a `incidencia_services.registrar(data_crear, token_empresa, ip=ip)`. Extrae `id_incidencia` directamente de la raíz de la respuesta (`resp['id_incidencia']`).
   - `crear_orden_trabajo`: Llama a `orden_Trabajo_services.crear_orden_trabajo(data_ot, token_empresa, client_ip=ip)`. Extrae `orden_nro` de `resp['data']['orden_nro']`.
   - `crear_material`: Llama a `material_services.registrar(data_mat, token_empresa, ip=ip)`. Extrae `id_material` de `resp['id_material']`.
3. **Ajuste de Columnas en Catálogo de Fuentes Dinámicas (M7):**
   - `personal_obra`: Clave primaria compuesta `id_obra, id_usuario`, campos reales `fecha_asignacion`.
   - `empresas`: Campos reales `id_empresa, nombre_empresa, nit, descripcion`.

### C. Fase 3: Consistencia Operativa y Robustez
1. **Parámetros Tipados y Vista Previa Confiable (M1):**
   - Modelos Pydantic estrictos (`IncidenciaParams`, `OrdenTrabajoParams`, `MaterialParams`).
   - El `resumen` visible de la propuesta es generado **únicamente por el backend** con base en los campos tipados y validados.
   - Prohibición estricta de generar propuestas de acción en consultas de solo lectura (`accion != 'operacion'`).
2. **Desambiguación Explícita de Obras (M2):**
   - La selección de obra exige coincidencia inequívoca o `id_obra_contexto` activo. Ante obras desconocidas, ambiguas o inexistentes, el asistente responde pidiendo aclaración (`accion='ayuda'`), prohibiendo seleccionar silenciosamente `works[0]`.
3. **Consumo Atómico y Seguro de Tickets (M3, M4):**
   - La verificación de pertenencia (`id_usuario`) se realiza antes de alterar el estado del ticket.
   - Ciclo de vida con estados: `PENDIENTE`, `EJECUTANDO`, `EJECUTADA`, `CANCELADA`.
   - Endpoint explícito `POST /api/ai/operacion/cancelar` con auditoría en bitácora.
   - Las limpiezas de propuestas expiradas se ejecutan de manera thread-safe dentro del lock.
   - La propuesta expone `expira_en` en formato ISO.
4. **Mapeo de Excepciones de Dominio (M5):**
   - `IncidenciaError`, `MaterialError`, `ValueError` se interceptan y devuelven respuestas HTTP 400/409/422 con mensaje descriptivo, evitando errores 500 no controlados.
5. **Protección Contra Respuestas Tardías en Angular (M6):**
   - `confirmOperation` y `cancelOperation` en `asistente.ts` validan `version`, `empresaId` y `obraId` actuales antes de alterar el estado del componente.
   - Interfaz visual en `asistente.html` que muestra los parámetros estructurados de la operación.
6. **Actualización de Conocimiento Base (B1):**
   - Corrección de la ruta a `/equipos-maquinaria`.
   - Filtrado de capacidades según `ctx.permisos` reales.
   - Indicación del cupo SaaS configurable y advertencia sobre el estado bloqueado de la restauración en caliente.

---

## 3. Plan de Validación

1. **Pruebas de Regresión Backend:**
   - Reproducción de revocación de permisos durante confirmación (A1).
   - Verificación de asignación de empresa objetivo y rechazo de obras ajenas (A2).
   - Comprobación de diagnóstico sin permisos o con rol de trabajador (A3).
   - Ejecución de `analizar_salud_operativa` con mock de `fn_listar_inventario_empresa` (A4).
   - Confirmación real de creación de OT y material verificando contratos de servicio (A5).
   - Saneamiento de historial conversacional frente a respuestas previas (A6).
   - Validación de vista previa tipada y rechazo de propuestas en lecturas (M1).
   - Requerimiento de obra explícita sin fallback ciego (M2).
   - Intento de consumo de ticket ajeno con preservación del ticket original (M3).
   - Cancelación de ticket y exposición de `expira_en` (M4).
   - Manejo de excepciones de dominio con códigos 4xx (M5).
   - Consulta a fuentes modulares `personal_obra` y `empresas` (M7).
   - Verificación de ID de incidencia retornado (B2).
2. **Pruebas de Frontend Angular:**
   - Compilación estricta con TypeScript (`npx tsc --noEmit`).
   - Verificación de tests de reportes/asistente.
