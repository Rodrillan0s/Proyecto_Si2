# CU34: Asistente Comercial Inteligente y Recomendaciones para Clientes Potenciales (DeepSeek API)

**Fecha:** 2026-11-05  
**Autores:** Equipo de Arquitectura OBRATEC / Antigravity  
**Estado:** Implementado y Validado (Backend + Frontend Angular; Migración SQL aditiva preparada)  
**Historias de Usuario cubiertas:** HU147, HU148, HU149, HU150  
**Caso de Uso:** CU34 (Consultar asistente comercial y recomendaciones)  
**Actor Principal:** Cliente Potencial (Visitante público o prospecto registrado)  
**Proveedor de IA Exclusivo:** DeepSeek API (`deepseek-chat`, `deepseek-flash`, `deepseek-reasoner`)

---

## 1. Solicitud y Alcance

### A. Historias de Usuario
- **HU147 (Consultar unidades inmobiliarias por lenguaje natural):** Permitir al cliente potencial expresar sus necesidades en lenguaje coloquial (ej. *"departamento de 3 dormitorios en Equipetrol con balcón hasta 95 mil dólares"*) y obtener opciones reales del inventario de la constructora.
- **HU148 (Recibir recomendaciones por presupuesto y preferencias):** Algoritmo de scoring multicriterio determinista (sobre 100 puntos) que evalúa presupuesto, metraje, tipología, dormitorios, zona y amenidades, generando explicaciones comerciales fundamentadas (`razones_recomendacion`).
- **HU149 (Comparar alternativas inmobiliarias):** Generación de matriz comparativa estructurada lado a lado (precios en USD y BOB, $m^2$, costo por $m^2$, ambientes, características, estado comercial y veredicto técnico).
- **HU150 (Solicitar contacto desde el asistente comercial):** Captura de datos del prospecto por formulario o desde lenguaje natural en el chat y persistencia transaccional en el módulo CRM (`obras.t_persona`, `obras.t_crm_cliente`, `obras.t_crm_cliente_unidad`, `obras.t_crm_interaccion`).

### B. Capacidades Avanzadas Implementadas
1. **Lectura e Interpretación Multimodal de Imágenes de Planos:** El cliente puede subir imágenes (`PNG`, `JPEG`, `WEBP` hasta 10 MiB) de planos arquitectónicos; el servicio valida magic bytes y dimensiones reales, invoca `DeepSeekProvider.complete_vision()` (`deepseek-flash`) para extraer ambientes, cotas estimadas, superficie en $m^2$ y distribución, cotiza la construcción en los 5 estilos arquitectónicos y empareja con los modelos (`t_modelo_unidad`) y unidades (`t_unidad_construccion`) más afines de la constructora.
2. **Estimación Paramétrica Determinista de Costos y Estilos:** Cálculo exacto en Python con `Decimal` (`ROUND_HALF_UP`) que cotiza unidades o construcciones personalizadas según 5 estilos (`ESTANDAR`, `INDUSTRIAL`, `MINIMALISTA`, `CONTEMPORANEO`, `LUJO`), desglosando capítulos constructivos (52% Obra Gris y Estructura, 18% Instalaciones Hidrosanitarias/Eléctricas, 30% Acabados y Carpintería), extras (`parqueo`, `baulera`, `domotica`) y evaluación inversa de presupuesto máximo del cliente, alimentado por `t_parametro_estimacion`, `t_analisis_precio_unitario` y `t_material`.
3. **Cero Respuestas Vagas (Grounded RAG Estricto):** Prohibición de invención de precios, metrajes o unidades. El motor ejecuta extracción híbrida (heurísticas deterministas + JSON estructurado de DeepSeek), filtra y puntúa en Python sobre datos reales de PostgreSQL y pasa el contexto verificado a DeepSeek para redacción ejecutiva con respaldo determinista automático si la red o cuota externa no está disponible.
4. **Proveedor Exclusivo DeepSeek:** Uso exclusivo de `https://api.deepseek.com/v1/chat/completions` mediante `DeepSeekProvider`.

---

## 2. Contexto Actual y Archivos Revisados

1. **`docs/ARQUITECTURA_Y_PATRONES.md`, `docs/ARQUITECTURA_REPORTES_IA.md` y `docs/ARQUITECTURA_BASE_DATOS.md`:**
   - Flujo obligatorio `routes → services → repos → PostgreSQL`.
   - Aislamiento multi-tenant estricto por `id_empresa` validado contra `obras.t_empresa`.
   - Verificación contra las 68 tablas reales de `obras` en `docs/BASE_DATOS_INVENTARIO.md`.
2. **`backend/app/config.py` y `backend/app/services/ai/providers.py`:**
   - Se incorporaron `DEEPSEEK_CHAT_MODEL` (`deepseek-chat`), `DEEPSEEK_VISION_MODEL` (`deepseek-flash`) y `DEEPSEEK_REASONER_MODEL` (`deepseek-reasoner`) preservando `DEEPSEEK_MODEL`.
   - Se extendió `DeepSeekProvider` con `chat_completions()`, `chat_structured()` (con `response_format={"type": "json_object"}` y parseo tolerante de bloques JSON) y `complete_vision()` (bloques multimodales `image_url` en Base64 con validación de MIME y límite de 10 MiB).
3. **Compatibilidad con el Esquema Actual de `obras`:**
   - `commercial_repos.py` detecta dinámicamente (`_columna_existe`) si las columnas opcionales de la migración preparada (`precio_venta`, `moneda`, `disponible_comercial`) ya están aplicadas o si debe operar directamente sobre las 68 tablas actuales derivando disponibilidad real desde `t_crm_cliente_unidad` (`RESERVADO`, `VENDIDO`) y costos desde `t_parametro_estimacion` + `t_unidad_personalizacion`.
   - En `t_crm_interaccion`, la columna `id_usuario` es `NOT NULL`; el repositorio resuelve automáticamente el asesor comercial/administrador activo de la empresa (`ADMINISTRADOR_EMPRESA` / `JEFE DE OBRA`) para registrar la trazabilidad del lead.

---

## 3. Arquitectura implementada por capas

### A. Repositorio (`backend/app/repos/commercial_repos.py`)
- `listar_empresas_comerciales()`: Lista constructoras activas con conteo de obras y unidades.
- `resolver_empresa_comercial(empresa_ref)`: Resuelve por `id_empresa`, `nit` o slug de `razon_social`.
- `obtener_parametros_estimacion_empresa(id_empresa)`: Obtiene parámetros de `t_parametro_estimacion`, resumen de APUs (`t_analisis_precio_unitario`) y materiales destacados (`t_material`) de la empresa.
- `listar_unidades_comerciales(id_empresa)`: Consulta unidades con su proyecto (`t_obra`), modelo (`t_modelo_unidad`), ambientes (`t_unidad_ambiente`), características (`t_unidad_caracteristica`), personalizaciones (`t_unidad_personalizacion`) y estado comercial real en `t_crm_cliente_unidad`.
- `listar_modelos_comerciales(id_empresa)`: Catálogo de modelos de unidad por empresa.
- `registrar_lead_comercial_transaccional(...)`: Transacción atómica sobre `t_persona` $\rightarrow$ `t_crm_cliente` $\rightarrow$ `t_crm_cliente_unidad` (`INTERESADO`) $\rightarrow$ `t_crm_interaccion` (`NOTA`).

### B. Servicios de Dominio (`backend/app/services/commercial/`)
- `contracts.py`: Contratos Pydantic (`CommercialSearchCriteria`, `CostEstimationRequest`, `LeadContactRequest`, `CommercialChatRequest`).
- `cost_estimation_service.py`: Motor determinista con `Decimal` (`estimar_costo_constructivo`, `enriquecer_unidad_comercial`, `listar_catalogo_estilos`).
- `commercial_query_engine.py`: Extractor híbrido de criterios (`extraer_criterios_locales`, `combinar_criterios`), buscador y recomendador con scoring explicable (`filtrar_y_recomendar_unidades` para HU147/HU148) y comparador lado a lado (`comparar_alternativas_inmobiliarias` para HU149).
- `blueprint_vision_service.py`: Validador binario de formato y resolución (`detectar_formato_y_dimensiones`) y analizador de planos con `DeepSeekProvider.complete_vision()` + cotización multiescala y matching de unidades/modelos (`analizar_plano_y_cotizar`).
- `lead_capture_service.py`: Extracción de contacto desde texto natural (`extraer_datos_contacto_de_texto`) y registro validado en CRM (`registrar_solicitud_contacto` para HU150).
- `commercial_assistant_service.py`: Gestor de sesiones multi-turno aislado por `id_empresa` y orquestador de CU34 (`obtener_catalogo_inicial_comercial`, `procesar_consulta_comercial`, `ejecutar_estimacion_directa`, `procesar_plano_comercial`).

### C. Rutas HTTP (`backend/app/routes/commercial_routes.py`)
Registradas en `backend/app/__init__.py` bajo `/api/public/comercial`:
- `GET /api/public/comercial/empresas`
- `GET /api/public/comercial/{empresa_ref}/catalogo`
- `POST /api/public/comercial/{empresa_ref}/chat`
- `POST /api/public/comercial/{empresa_ref}/estimar-costo`
- `POST /api/public/comercial/{empresa_ref}/analizar-plano`
- `POST /api/public/comercial/{empresa_ref}/solicitar-contacto`
- Incluye limitador de tasa por ventana deslizante en memoria (30 peticiones/5 min general y 8 análisis de planos/5 min por IP) y verificación de no cruce de tenant cuando el usuario envía JWT de empresa interna.

### D. Frontend Angular (`frontend/src/app/`) — Burbuja Conversacional Unificada y Aislamiento por Usuario
- `services/asistente-comercial.service.ts`: Cliente HTTP tipado para todos los endpoints comerciales. Almacén reactivo de sesión en memoria aislado por usuario y constructora mediante claves compuestas (`${userPrefix}:${empresaRef}`). Suscripción reactiva a `AuthService.usuario$` para purgar completamente el historial y sesiones en memoria (`limpiarTodasLasSesiones()`) cuando ocurre cierre de sesión (`cerrarSesion`) o autenticación con otro usuario (`guardarSesion`). Esto garantiza que dos usuarios que compartan máquina o navegador nunca compartan ni vean el historial del otro.
- `services/auth.ts`: Incorporación de `usuarioSubject` (`BehaviorSubject`) y `usuario$` observable para notificar reactivamente al shell y asistentes cuando el usuario activo cambia o cierra sesión.
- `pages/asistente-comercial/asistente-comercial.ts` y `asistente-comercial.html`: Asistente de IA unificado en una sola ventana conversacional estilo burbuja flotante:
  1. Búsqueda en lenguaje natural y tarjetas inline de unidades recomendadas con afinidad y razones explicables.
  2. Selección y matriz comparativa lado a lado dentro del mismo chat.
  3. Adjunto directo de imagen de plano (`📐 Plano`) en la barra de composición del chat, radiografía de ambientes y tarjeta interactiva de estimación de costos con cambio de estilo en vivo (`ESTANDAR`, `INDUSTRIAL`, `MINIMALISTA`, `CONTEMPORANEO`, `LUJO`).
  4. Tarjeta inline de captura de contacto comercial (`📞 Contacto`) y confirmación directa en CRM, además de dictado por voz (`🎤 Dictar`) y botón para reiniciar manualmente la conversación (`↺ Nueva`).
  5. Limpieza de códigos internos (`CU34`, `HU147`, `HU148`, etc.) de toda la interfaz y reemplazo de textos técnicos o menciones a proveedores ("DeepSeek") durante la carga por un estado minimalista (`Cargando…`).
- Integrado como burbuja flotante en la portada pública (`HomeComponent` en `/` y `/comercial`) y embebido dentro de la burbuja `app-asistente` del shell autenticado (`AdminLayoutComponent`) mediante selector `Gestión / Admin` | `Comercial & Planos`.

### E. Configuración y Resiliencia del Motor de IA (`backend/app/services/ai/`)
- `config.py`: `AI_PROVIDER` configurado para usar `deepseek` por defecto (`os.getenv('AI_PROVIDER', 'deepseek')`), unificando el motor de IA en todo el backend (tanto para el asistente comercial de CU34 como para el asistente administrativo de reportes y diagnóstico).
- `providers.py`: `get_provider()` devuelve `DeepSeekProvider` por defecto.
- `reportes/catalog.py`: Ampliación exhaustiva de alias y términos semánticos en el catálogo de reportes:
  - `saldo_comercial`: Incorporación de alias para déficit, sobrecostos y pérdidas (`deficit`, `déficit`, `obras con mas deficit`, `obras con mayor deficit`, `obras con deficit`, `obras en deficit`, `obras deficitarias`, `proyectos deficitarios`, `mayor deficit`, `mas deficit`, `perdida`, `pérdida`, `perdidas`, `pérdidas`, `obras con perdidas`, `saldo negativo`, `balance comercial`, `balance financiero`).
  - `comparativo_costos`: Incorporación de alias para desvíos presupuestarios y sobrecostos (`sobrecosto`, `sobrecostos`, `desvio`, `desvío`, `desvios`, `desvíos`, `obras con sobrecosto`, `desviacion presupuestaria`, `costos ejecutados vs presupuestados`).
  - `stock`: Incorporación de alias para materiales e insumos críticos y agotados (`materiales agotados`, `materiales sin stock`, `insumos agotados`, `stock agotado`, `quiebre de stock`, `insumos faltantes`).
  - `presupuestario`: Incorporación de alias para presupuestos y estimaciones (`presupuestos`, `estimacion`, `costo estimado`, `presupuesto de obra`, `versiones de presupuesto`).
  - `avance_ejecutivo`: Incorporación de alias para progreso y retraso (`avance de obras`, `progreso de obras`, `estado de avance`, `porcentaje de avance`, `obras retrasadas`).
  - `incidencias` / `incidencias_criticas`: Incorporación de alias para problemas y fallas en obra (`problemas en obra`, `incidentes`, `fallas`, `bloqueos`, `urgencias`, `alertas`).
- `assistant_service.py`:
  - Detección semántica directa para consultas financieras (`finance`: deficit, perdidas, saldo negativo, rentabilidad) direccionadas inmediatamente a `saldo_comercial` con flag `losses` activo para ordenar por el mayor déficit primero.
  - Implementación de un resolvedor heurístico semántico de contingencia (`_inferir_plan_semantico`) en caso de que el proveedor externo de IA no esté configurado o falle por timeout/red/cuota, mapeando automáticamente la pregunta del usuario al reporte o consulta dinámica correcta en lugar de abortar con mensaje de indisponibilidad.

---

## 4. Validación Ejecutada y Resultados Reales

1. **Pruebas Unitarias y de Integración Backend (`pytest`):**
   - Archivo creado: `backend/tests/test_cu34_asistente_comercial.py` (8 pruebas que cubren `DeepSeekProvider.chat_structured`, `DeepSeekProvider.complete_vision`, cálculo determinista `Decimal` de costos y estilos, motor de recomendaciones HU147/HU148, matriz comparativa HU149, flujo de chat multi-turno, análisis de planos con imagen PNG válida y aislamiento multi-tenant frente a JWT de otra empresa + captura de lead HU150).
   - Comando ejecutado: `cd backend; python -m pytest tests/test_cu34_asistente_comercial.py tests/test_reportes.py -v`
   - Resultado real: **41 passed in 2.55s** (8 de CU34 + 33 de regresión en `test_reportes.py`).
2. **Compilación de Frontend Angular (`ng build`):**
   - Comando ejecutado: `cd frontend; npm run build`
   - Resultado real: **Exit code 0**, bundle lazy `asistente-comercial` generado (`62.75 kB` raw / `12.70 kB` transfer) sin errores de TypeScript ni de plantillas.
3. **Migración SQL Preparada:**
   - Archivo `backend/database/20261105_cu34_asistente_comercial.sql` preparado de forma aditiva e idempotente (`IF NOT EXISTS` / `ON CONFLICT DO NOTHING`). Conforme a `AGENTS.md`, no se ejecutó contra ninguna base de datos desconocida o de producción.
