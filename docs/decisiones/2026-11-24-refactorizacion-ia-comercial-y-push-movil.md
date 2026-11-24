# Decisión Arquitectónica: Refactorización de IA Comercial (CU34) y Notificaciones Push Móvil

- **Fecha:** 2026-11-24
- **Alcance:**
  1. Refactorización del motor comercial IA (`backend/app/services/commercial/` + `commercial_repos.py`), incorporando interpretación estructurada por DeepSeek, filtros obligatorios previos al scoring, diferenciación estricta de amoblamiento y tipos de precio, `project_proposal_engine.py` (3 escenarios + recopilación progresiva + separación terreno/construcción) y contexto conversacional comercial aislado.
  2. Ajustes en la app móvil Flutter (`asistente_screen.dart`, `ai_assistant_service.dart`, `offline_sync_service.dart`, `notificacion_service.dart`) para soportar propuestas de proyectos personalizados, amoblamiento/precios diferenciados y notificaciones push operativas consistentes (incluyendo eventos de sincronización offline CU41, propuestas comerciales y banners push globales con soporte de bandeja/reintento).

## 1. Diagnóstico de la auditoría inicial

1. **Ignoraba columnas comerciales reales y exponía `monto_pactado` de terceros:** `obras.t_unidad_construccion` ya cuenta con `publicado_comercial`, `precio_venta`, `moneda_comercial`, `descripcion_comercial` y `estado_comercial`, pero `commercial_repos.listar_unidades_comerciales()` no las consultaba y en su lugar consultaba `ultimo_monto_pactado` de `t_crm_cliente_unidad` (precio pactado de terceros).
2. **Filtros obligatorios no excluyentes:** En `commercial_query_engine.filtrar_y_recomendar_unidades()`, las unidades `RESERVADA`, de tipología incompatible (ej. `OFICINA` al pedir `VIVIENDA`) o por encima de `presupuesto_max` solo marcaban `cumple_estricto = False`, pero permanecían en `evaluadas` y se devolvían igualmente como `unidades_recomendadas`.
3. **Amoblamiento ausente:** No existía diferenciación entre `AMOBLADA`, `PARCIALMENTE_AMOBLADA`, `SIN_AMOBLAR` y `DESCONOCIDO` ni cotización separada de mobiliario.
4. **Scoring arbitrario (`afinidad_score`):** Sumaba puntos base fijos aun sin criterios declarados (~64% mínimo), no penalizaba datos desconocidos relevantes y rankeaba unidades que incumplían restricciones obligatorias.
5. **Sin motor de propuestas de proyectos personalizados:** Al no existir coincidencias en inventario, el asistente terminaba en un mensaje estático en vez de proponer alternativas de construcción personalizadas fundamentadas en `t_parametro_estimacion`, `t_analisis_precio_unitario` y `t_material`.

## 2. Arquitectura propuesta

- **Capas preservadas:** `commercial_routes.py` / `orchestrator.py` → `commercial_assistant_service.py` → (`commercial_query_engine.py`, `cost_estimation_service.py`, `project_proposal_engine.py`) → `commercial_repos.py` → PostgreSQL.
- **Autorización y tenant:** `authorization.py` sigue siendo la autoridad en el flujo autenticado; en `/api/public/comercial/{empresa_ref}` se mantiene `_resolver_y_autorizar_empresa` con bloqueo cross-tenant JWT. Jamás se expone `monto_pactado` de terceros.
- **Interpretación DeepSeek-first:** DeepSeek JSON mode extrae `CommercialSearchCriteria` (incluyendo `amoblamiento_preferido`, `amoblamiento_indispensable`, `acepta_cotizar_mobiliario`, `tiene_terreno`, `superficie_terreno_m2`, `plazo_deseado_meses`, `intencion='proponer_proyecto'`, `necesita_aclaracion`), con respaldo determinista local solo si DeepSeek no está disponible o devuelve campos faltantes.
- **Motor comercial estricto (`commercial_query_engine.py`):**
  - Fase 1 (Hard Filters): `disponibilidad_comercial == 'DISPONIBLE'` (cuando `solo_disponibles=True`, excluyendo `RESERVADA`, `VENDIDA`, `NO_DISPONIBLE` y `publicado_comercial=False`), `tipo_unidad` compatible (nunca `OFICINA`/`LOCAL`/`LOTE` si se pidió `VIVIENDA`), `precio <= presupuesto_max` (con tipo de cambio explícito y fecha de referencia), `amoblamiento` obligatorio solo si el usuario lo confirmó como indispensable.
  - Fase 2 (Scoring verificable): Solo evalúa unidades que pasaron Fase 1. Calcula `afinidad_score` ponderado únicamente sobre criterios activos, penalizando información `DESCONOCIDO` cuando es relevante (ej. mobiliario desconocido con advertencia explícita) y generando `razones_recomendacion` y `advertencias_unidad` desde el mismo payload que construye el texto.
  - Si 0 unidades pasan Fase 1: `unidades_recomendadas = []`, `coincidencias_exactas = 0`, y `motivos_exclusion` explicando por qué se descartaron.
- **Motor de proyectos personalizados (`project_proposal_engine.py`):**
  - Reutiliza `cost_estimation_service.py` y datos reales (`t_parametro_estimacion`, `t_analisis_precio_unitario`, `t_material`).
  - Recopilación progresiva de datos faltantes (máximo 1–2 preguntas prioritarias por turno).
  - Diferencia explícitamente adquisición de terreno vs. costo de construcción cuando `tiene_terreno is False`.
  - Genera 3 escenarios (`Económico`, `Equilibrado`, `Superior`) cuando existen datos suficientes, detallando costos confirmados vs. estimados, moneda, tipo de cambio, fecha de referencia, alcance incluido/excluido, supuestos, partidas no estimables, nivel de confianza y aviso legal de propuesta preliminar.
- **Extensión aditiva de BD (opcional, migración preparada):** `estado_amoblamiento` y `costo_mobiliario_estimado` en `obras.t_unidad_construccion` (el repositorio detecta dinámicamente si existen o lee claves explícitas de `t_unidad_caracteristica` sin romper si no se aplica).
- **Móvil y Notificaciones Push:**
  - Sincronización de contratos comerciales nuevos en `ai_assistant_service.dart` y tarjetas de `propuesta_proyecto` / `estado_amoblamiento` / `tipo_precio` en `asistente_screen.dart`.
  - Consolidación de notificaciones push reales en `NotificacionService` (WebSocket `/api/ws/notificaciones` + reconexión exponencial + polling fallback + notificación local en eventos de sincronización offline CU41, propuestas comerciales, reportes y operaciones IA + estado visible de conexión Push y preferencias de alerta en `notificaciones_screen.dart`).

## 3. Validación prevista

- Nueva suite `backend/tests/test_commercial_ai_refactor.py` cubriendo los 10 escenarios obligatorios + aislamiento multiempresa + coherencia texto/tarjetas.
- Regresión backend (`test_semantic_and_orchestrator.py`, `test_reportes.py`, `test_reportes_api.py`).
- `flutter analyze` y `flutter test` sobre móvil.
- `npm run build` en Angular para confirmar compatibilidad total sin rupturas.


## 4. Validación ejecutada

- **Backend (`pytest`):** **72 passed, 0 failed** (10.21s):
  - `tests/test_commercial_ai_refactor.py`: **12/12 passed** (los 10 escenarios obligatorios + no exposición de `monto_pactado` de terceros + aislamiento multiempresa + coherencia texto/tarjetas).
  - `tests/test_semantic_and_orchestrator.py`: **13/13 passed**.
  - `tests/test_reportes.py`: **35/35 passed**.
  - `tests/test_reportes_api.py`: **6/6 passed**.
  - `tests/test_cu41_offline_sync.py`: **4/4 passed**.
  - `tests/test_cu42_garantias_posventa.py`: **2/2 passed**.
- **Flutter (`flutter analyze`):** 7 archivos modificados analizados → **No issues found!** (4.8s).
- **Angular (`npm run build`):** **exit 0** (22.5s), compatibilidad preservada.
- **Migración SQL:** `backend/database/20261124_ia_comercial_amoblamiento.sql` preparada (no aplicada automáticamente; el repositorio detecta las columnas dinámicamente).
