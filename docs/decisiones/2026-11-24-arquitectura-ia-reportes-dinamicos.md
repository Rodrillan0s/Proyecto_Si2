# Decisión Arquitectónica: Motor Semántico Compartido, Orquestador IA Multi-Perfil y Reportes Universales

**Fecha:** 2026-11-24  
**Alcance:** Evolución de `backend/app/services/semantic/`, `backend/app/services/ai/`, `backend/app/services/reportes/` y `backend/app/services/reportes_services.py`. Compatible retroactivamente con los 12 reportes estándar, `reportes_worker.py`, Angular y Flutter. Sin SQL libre generado por el modelo ni alteración destructiva de tablas existentes.

---

## 1. Capas y principios de diseño

1. **Autoridad única de autorización (`app/services/reportes/authorization.py`):**
   - Concentra `context()`, `allowed()`, `authorize()`, `authorize_entity()`, `authorize_relation()`, `authorize_tool()` y `authorize_semantic_query()`.
   - `SemanticCatalog` es estrictamente declarativo (permisos, estrategia de tenant, RLS por rol, columnas permitidas, cardinalidad de relaciones); nunca duplica lógica RBAC.
   - `policy_snapshot` en conversaciones sirve únicamente para invalidar contexto entre turnos; nunca sustituye la reautorización en vivo contra PostgreSQL.
2. **Núcleo semántico compartido (`app/services/semantic/`):**
   - `contracts.py`: `SemanticQuerySpec`, `CrossModuleSpec`, `ReportSpecPatch`, `ChartSpec`, `UnifiedResultSet` (superconjunto estricto de `ReportResult`).
   - `catalog.py`: 24 entidades verificadas (incluyendo CU39 cronogramas, CU42 garantías/posventa, CRM interacciones/unidades, órdenes de cambio) con cero exposición de PII o credenciales.
   - `compiler.py`: compilador AST → SQL parametrizado (`%s`) con pushdown de `WHERE`, `GROUP BY`, `DATE_TRUNC`, `ORDER BY`, `LIMIT` y CTEs pre-agregados anti-fan-out para cruces multi-módulo.
   - `executor.py`: ejecución en `REPEATABLE READ, READ ONLY`, `statement_timeout = '15s'`, cálculos monetarios en `Decimal`, comparativas entre períodos e inferencia de `chart_spec`.
3. **Capacidades especializadas desacopladas:**
   - Recomendaciones/comparaciones inmobiliarias (`commercial_query_engine.py` + `cost_estimation_service.py`) diferenciando precio `PUBLICADO`, `PACTADO` y `ESTIMADO_PARAMETRICO`.
   - Análisis de planos (`vision_extractor.py` + `blueprint_vision_service.py`) separando extracción PDF vectorial / multimodal / OCR del cálculo determinista y eliminando la fabricación de ambientes por defecto cuando la imagen no es legible.
   - Bandeja proactiva de pendientes (`proactive_inbox_service.py`) consolidada y priorizada por perfil/permisos con rutas Angular reales.
4. **Orquestador IA con DeepSeek Function Calling y contexto en 6 compartimentos:**
   - `providers.py`: `DeepSeekProvider.chat_with_tools()` (máx. 3 rondas por turno bajo una sola reserva `consulta_ia`).
   - `context_manager.py`: separa formalmente historial (`t_asistente_mensaje` guardando `texto_respuesta`), `preferencias_usuario`, `entidades_resueltas`, `report_spec_activo`, `ultima_ejecucion` y `resumen_herramientas`.
   - `orchestrator.py`: filtra herramientas por `authorization.authorize_tool()`, soporta modificación incremental de reportes (`modificar_reporte_activo`) y conserva fallback determinista ante fallo de DeepSeek.

---

## 2. Contexto de tenant, permisos y compatibilidad

- `id_empresa` y `scope_obras` se inyectan exclusivamente desde `Context` (JWT + recarga en BD); jamás son parámetros editables por el LLM.
- `CLIENTE` y `WORKERS` aplican filtros RLS por fila en SQL.
- `UnifiedResultSet` conserva todas las claves raíz de `ReportResult` exigidas por Angular (`reportes.service.ts`) y Flutter (`reportes_service.dart`, `ai_assistant_service.dart`).
- Reportes dinámicos generados en chat pueden persistirse en `t_reporte_ejecucion` para exportarse por `/api/reportes/ejecuciones/{id}/exportaciones` → `/api/reportes/archivos/{id}`.

---

## 3. Validación prevista

- Pruebas unitarias dedicadas: `test_semantic_query_engine.py`, `test_ai_orchestrator_tools.py`, `test_proactive_inbox.py`, `test_vision_extractor.py`.
- Regresión backend: `test_reportes`, `test_reportes_api`, `test_cu41_offline_sync`, `test_cu42_garantias_posventa`.
- Regresión frontend: `npm run build`, `test:posventa`, `test:pagos`, `test:cu30`, `test:cu31`.


## 4. Implementación realizada

- **Autorización centralizada (`authorization.py`)**: Se añadieron `can_access_entity`, `authorized_entities`, `authorize_semantic_query`, `authorize_cross_module` y `authorize_tool`. Ningún componente duplica reglas RBAC ni confía en `policy_snapshot` para autorizar.
- **Motor Semántico Compartido (`backend/app/services/semantic/`)**:
  - `contracts.py`: `SemanticQuerySpec`, `CrossModuleSpec`, `ReportSpecPatch`, `ChartSpec`, `UnifiedResultSet` (superset estricto del contrato `ReportResult` de Angular y `ReportesService` de Flutter).
  - `catalog.py`: Catálogo declarativo de 24 entidades verificadas en PostgreSQL (incluyendo cronogramas CU39 y garantías/posventa CU42).
  - `compiler.py`: Compilador SQL parametrizado con pushdown de filtros/agregaciones/orden/límite, aislamiento por empresa/obras/RLS, prevención de mezcla de monedas y versiones de estimaciones, y CTEs pre-agregados por `id_obra` para cruces multi-módulo sin fan-out.
  - `executor.py`: Ejecución en transacciones `REPEATABLE READ, READ ONLY`, soporte para modificación incremental de reportes activos (`ReportSpecPatch`) y generación automática de `ChartSpec`.
- **Orquestador Multi-Perfil y DeepSeek Function Calling (`backend/app/services/ai/`)**:
  - `providers.py`: `DeepSeekProvider.chat_with_tools()` manteniendo DeepSeek API como proveedor actual.
  - `context_manager.py`: Estado conversacional persistido en 6 compartimentos separados (`policy_snapshot`, `entidades_resueltas`, `preferencias_usuario`, `report_spec_activo`, `ultima_ejecucion`, `resumen_herramientas`) e invalidación selectiva por cambio de permisos/empresa; se corrigió además la persistencia de `texto_respuesta` en `t_asistente_mensaje`.
  - `proactive_inbox_service.py`: Bandeja proactiva segmentada por rol (`ADMINISTRADOR`, `TRABAJADOR`, `CLIENTE`) con rutas accionables del frontend.
  - `orchestrator.py`: Loop acotado de tool calling con herramientas semánticas y especializadas (`consultar_datos`, `analizar_cruce_obras`, `modificar_reporte_activo`, `ejecutar_reporte_estandar`, `exportar_reporte_activo`, `consultar_pendientes`, `ejecutar_diagnostico_operativo`, `recomendar_inmuebles`, `comparar_inmuebles`, `consultar_ayuda_plataforma`, `proponer_operacion`).
  - `vision_extractor.py`: Extractor honesto para planos (validación de magic bytes, extracción de texto vectorial PDF, adaptador multimodal opcional, cero fabricación de ambientes cuando no hay visión disponible).
  - `assistant_service.py` y `knowledge_base.py`: Integración del orquestador con fallback automático ante indisponibilidad del proveedor (`ProviderError`) y cobertura documental de cronogramas (CU39) y garantías/posventa (CU42).
- **Integración de Reportes Universales (`reportes/contracts.py` y `reportes_services.py`)**: Soporte de `ReportRequest.consulta_dinamica` en `build()` y `owned()`, manteniendo compatibilidad total con los 12 reportes estándar, `reportes_worker.py`, Angular y Flutter.

## 5. Validación ejecutada

- Comando: `python -m pytest tests/test_semantic_and_orchestrator.py tests/test_reportes.py tests/test_reportes_api.py tests/test_cu41_offline_sync.py tests/test_cu42_garantias_posventa.py -v`
- Resultado real: **60 passed, 0 failed** (10.17s):
  - `tests/test_semantic_and_orchestrator.py`: 13/13 passed (autorización centralizada, inyección tenant/obra/RLS, rechazo de SQL injection, bloqueo anti-mezcla de monedas y versiones, parches incrementales, CTEs sin fan-out, invalidación selectiva de 6 compartimentos, loop de function calling, honestidad en extractor de planos, bandeja proactiva de cliente).
  - `tests/test_reportes.py`: 35/35 passed (incluyendo `test_assistant_reuses_report_and_survives_provider_outage`).
  - `tests/test_reportes_api.py`: 6/6 passed.
  - `tests/test_cu41_offline_sync.py`: 4/4 passed.
  - `tests/test_cu42_garantias_posventa.py`: 2/2 passed.
- Sin migraciones SQL ejecutadas automáticamente, sin commits ni push.


## 6. Cierre complementario (UI Angular/Flutter, migración preparada y limpieza)

- **Migración SQL aditiva aplicada y verificada (`147.15.29.190:5433/obras`):** [20261124_ia_asistente_propuestas.sql](file:///d:/Locked%20Files%20--EY/Projectos/Proyecto_Si2/backend/database/20261124_ia_asistente_propuestas.sql) creó `obras.t_asistente_propuesta` (14 columnas) e índices `t_asistente_propuesta_pkey`, `idx_asistente_propuesta_actor` y `idx_asistente_propuesta_expira`. `assistant_operations.py` persiste automáticamente en PostgreSQL y conserva degradación segura a memoria.
- **Visualización de `chart_spec` y `pendientes` en Angular:**
  - Nuevo componente standalone sin dependencias externas `ChartSpecCardComponent` (`kpi`, `bar`, `stacked_bar`, `line`, `pie`).
  - Integrado en `reportes.html` y `asistente.html`, junto con la tarjeta de bandeja proactiva `pendientes` con navegación directa a rutas Angular.
- **Visualización de `chart_spec` y `pendientes` en Flutter:**
  - Nuevo widget nativo `ChartSpecCard` (`mobile/lib/widgets/chart_spec_card.dart`).
  - Integrado en `asistente_screen.dart` (junto con tarjeta de `pendientes`) y `reportes_screen.dart`.
- **Deprecación controlada:** `context_builder.py` marcado explícitamente como `DEPRECATED` (conservado solo por compatibilidad con el endpoint heredado `/api/ai/crm`).
- **Validaciones ejecutadas:**
  - Backend: `pytest` (53/53 passed en 2.60s).
  - Angular: `npm run build` (exit 0); `reportes.service.spec.ts` (5/5 passed) y `reportes.spec.ts` (7/7 passed); `reportes-asistente.spec.ts` mantiene un fallo previo por mock sin `auth.usuario$`.
  - Flutter: `flutter analyze` sobre los 4 archivos modificados (`No issues found!`).
