# Nota de Arquitectura: Diagrama de Componentes C4 (Nivel 3) — OBRATEC

**Fecha:** 2026-11-22  
**Autor:** Antigravity  
**Contexto:** Especificación y modelado formal del Nivel 3 (Componentes) bajo el **Modelo C4 (Simon Brown)** para el contenedor principal **API Backend [FastAPI + Uvicorn]**, respetando estrictamente el código fuente, dependencias e infraestructura real del repositorio OBRATEC.

---

## 1. Validación de Stack e Infraestructura Real contra el Repositorio

A partir del análisis directo de los archivos de configuración y código fuente:

1. **Frontend Web (`frontend/package.json`):**
   - Framework: `Angular 18+ (SSR / Client)` + `Tailwind CSS`.
   - Protocolo: REST API sobre `HTTPS/JSON` y `WebSocket` para notificaciones reactivas.
2. **Aplicación Móvil (`mobile/pubspec.yaml`):**
   - Framework: `Flutter + Dart`.
   - Cliente HTTP: `Dio`.
   - Persistencia local: `flutter_secure_storage` y `shared_preferences` para credenciales/tokens.
3. **API Backend (`backend/run.py`, `backend/requirements.txt`, `backend/app/__init__.py`):**
   - Servidor y Framework: `FastAPI` montado sobre servidor ASGI `Uvicorn` (con soporte de workers en producción mediante `Gunicorn`).
   - Mapeo C4: `APIRouter` como componentes Controller, servicios de dominio en `app/services/`, adaptadores en `app/services/payments` y `app/services/ai/`, repositorios en `app/repos/`.
4. **Persistencia Central (`backend/app/config.py`, `backend/app/classes/postgres.py`):**
   - Motor: `PostgreSQL` bajo el esquema multi-inquilino `obras`.
   - Conexión: `psycopg2` / `SQLAlchemy` con pooling de conexiones y aislamiento por `id_empresa`.
5. **Sistemas Externos Confirmados (`backend/app/config.py`, servicios y SDKs):**
   - **Brevo API:** Notificaciones por correo electrónico y distribución de reportes (`app/services/email_service.py`, `app/services/reportes/worker.py`).
   - **Stripe API:** Procesamiento de pasarela de pagos y suscripciones SaaS (`app/services/payments/stripe_gateway.py`, `app/services/pago_services.py`).
   - **Gemini / Groq API:** Modelos de lenguaje para asistente conversacional y recomendaciones (`app/services/ai/gemini_provider.py`).
   - **Cloudinary API:** Almacenamiento seguro de evidencias multimedia de obra (`app/services/incidencia_services.py`).

---

## 2. Modularización del Nivel 3 por los 8 Paquetes Funcionales Oficiales

Conforme a la estructura funcional oficial de OBRATEC (establecida en los paquetes de arquitectura y casos de uso), el contenedor `API Backend [FastAPI + Uvicorn]` se modela en **8 diagramas de componentes C4**, correspondientes a:

1. **Módulo 1: GESTIÓN DE USUARIOS** (`c4_component_01_gestion_usuarios.mmd`)
   - Router: `app.routes.auth_routes`, `app.routes.users_routes`
   - Services: `app.services.auth_services`, `app.services.users_services`, `app.services.email_service`
   - Repos: `app.repos.users_repos`
   - DB: `obras.t_usuario`, `obras.t_persona`, `obras.t_rol`, `obras.t_empresa`
   - Ext: `Brevo API` (envío de correos de bienvenida y restablecimiento).

2. **Módulo 2: GESTIÓN DE PROYECTOS** (`c4_component_02_gestion_proyectos.mmd`)
   - Router: `app.routes.obra_routes`
   - Services: `app.services.obra_services`
   - Repos: `app.repos.obra_repos`
   - DB: `obras.t_obra`, `obras.t_ubicacion_obra`, `obras.t_empresa`
   - Ext: N/A.

3. **Módulo 3: INVENTARIO Y MATERIALES** (`c4_component_03_inventario_materiales.mmd`)
   - Router: `app.routes.material_routes`, `app.routes.orden_compra_routes`
   - Services: `app.services.material_services`, `app.services.orden_compra_services`
   - Repos: `app.repos.material_repos`, `app.repos.orden_compra_repos`
   - DB: `obras.t_material`, `obras.t_movimiento_inventario`, `obras.t_orden_compra`, `obras.t_almacen`
   - Ext: N/A.

4. **Módulo 4: PRESUPUESTO Y COSTOS** (`c4_component_04_presupuesto_costos.mmd`)
   - Router: `app.routes.estimacion_routes`, `app.routes.presupuestos`
   - Services: `app.services.estimacion_services`, `app.services.presupuesto_services`
   - Repos: `app.repos.estimacion_repos`, `app.repos.presupuestos`
   - DB: `obras.t_estimacion`, `obras.t_presupuesto`, `obras.t_apu`, `obras.t_partida`
   - Ext: N/A.

5. **Módulo 5: ACTIVIDADES Y ÓRDENES DE TRABAJO** (`c4_component_05_actividades_ordenes.mmd`)
   - Router: `app.routes.avance_routes`, `app.routes.incidencia_routes`, `app.routes.consulta_tecnica_routes`
   - Services: `app.services.avance_services`, `app.services.incidencia_services`, `app.services.consulta_tecnica_services`
   - Adapter: `app.services.cloudinary_service`
   - Repos: `app.repos.avance_repos`, `app.repos.incidencia_repos`, `app.repos.consulta_tecnica_repos`
   - DB: `obras.t_avance_obra`, `obras.t_incidencia`, `obras.t_consulta_tecnica`, `obras.t_evidencia_avance`
   - Ext: `Cloudinary API` (almacenamiento de fotos y evidencias técnicas).

6. **Módulo 6: REPORTES Y ANÁLISIS** (`c4_component_06_reportes_analisis.mmd`)
   - Router: `app.routes.reportes`
   - Services: `app.services.reportes.generator`, `app.services.reportes.worker`, `app.services.reporte_services`
   - Repos: `app.repos.reportes`
   - DB: `obras.t_reporte_generado`, `obras.t_plantilla_reporte`, `obras.t_obra`
   - Ext: `Brevo API` (distribución automatizada de reportes PDF/Excel por correo).

7. **Módulo 7: COMERCIAL Y CRM** (`c4_component_07_comercial_crm.mmd`)
   - Router: `app.routes.cliente_routes`, `app.routes.pago_routes`
   - Services: `app.services.cliente_services`, `app.services.pago_services`
   - Adapter: `app.services.payments.stripe_gateway`
   - Repos: `app.repos.cliente_repos`, `app.repos.pago_repos`
   - DB: `obras.t_cliente`, `obras.t_cotizacion`, `obras.t_suscripcion`, `obras.t_pago`
   - Ext: `Stripe API` (cobro de planes, suscripciones SaaS y transacciones comerciales).

8. **Módulo 8: ASISTENTE INTELIGENTE** (`c4_component_08_asistente_inteligente.mmd`)
   - Router: `app.routes.asistente_routes`
   - Services: `app.services.ai.chat_service`, `app.services.ai.context_retriever`
   - Adapter: `app.services.ai.gemini_provider`
   - Repos: `app.repos.asistente_repos`
   - DB: `obras.t_interaccion_asistente`, `obras.t_conocimiento_obra`
   - Ext: `Gemini / Groq API` (inferencia de modelos LLM con contextualización de obra).

---

## 3. Artefactos Generados

- Archivos Mermaid C4 individuales: `docs/diagramas/c4/c4_component_01_*.mmd` hasta `08_*.mmd`.
- Archivo unificado de Draw.io con 8 pestañas: `docs/diagramas/c4/diagramas_componentes_c4.drawio`.
