# Refactorización del CU29: Asistente Inteligente Administrativo y Operativo

**Fecha:** 2026-10-26  
**Autores:** Equipo de Arquitectura OBRATEC / Antigravity  
**Estado:** Aprobado / En implementación  
**Contexto:** Evolución del CU29 de un asistente centrado en reportes y analítica hacia un Asistente Inteligente Administrativo y Operativo para roles `ADMINISTRADOR` y `ADMINISTRADOR_EMPRESA`.

---

## 1. Contexto y Objetivos

El CU29 actual resuelve eficazmente la interpretación de lenguaje natural para ejecutar los 12 reportes del catálogo oficial y consultas dinámicas tipadas mediante `query_engine.py`. Sin embargo, los administradores de la plataforma y de las empresas constructoras requieren asistencia integral en la gestión diaria:
1. Comprender el funcionamiento de los módulos de OBRATEC sin alucinaciones de interfaz o rutas inexistentes.
2. Supervisar de forma cruzada obras, inventario, compras, personal y finanzas con alertas tempranas y recomendaciones justificadas en datos reales.
3. Recibir asistencia operativa en tareas administrativas de bajo riesgo mediante un flujo seguro de dos pasos: **interpretación/propuesta con vista previa** → **confirmación explícita del usuario** → **ejecución mediante servicios de dominio y registro en bitácora**.

---

## 2. Decisiones de Arquitectura y Patrones

### A. Preservación del Flujo y Principios Innegociables
- **Flujo:** `routes → services → repos → PostgreSQL`.
- **Cero SQL Libre:** El LLM (DeepSeek / Gemini) **nunca** genera sentencias SQL. Todas las lecturas se validan como planes tipados (`ReadPlan`) o pasan por `query_engine.py` y repositorios parametrizados.
- **Cálculos Deterministas:** Las métricas, variaciones, costos y avances se calculan en backend con precisión fija (`Decimal`), nunca en el prompt del LLM.
- **Aislamiento Multi-Tenant y RBAC:**
  - `ADMINISTRADOR`: opera con alcance global o empresa seleccionada expresamente.
  - `ADMINISTRADOR_EMPRESA`: estrictamente restringido a los recursos de su empresa (`id_empresa` del token).
  - La pertenencia a la empresa y la verificación de permisos se revalidan en el backend antes de preparar y antes de ejecutar cualquier operación.
- **Cuotas de Suscripción:** Se mantiene el gestor de cuotas mensual `consulta_ia` (500 solicitudes/mes por empresa) protegiendo el consumo del proveedor.

### B. Extensión del Contrato `ReadPlan`
El modelo Pydantic de salida del LLM se expande con soporte para:
- `accion`: `'reportes' | 'consulta' | 'crm' | 'ayuda' | 'conocimiento' | 'analisis' | 'operacion'`
- `operacion_propuesta`: Detalle tipado de la acción administrativa propuesta (tipo de entidad, campos validados, resumen para el usuario, identificador de operación temporal).
- `contexto_conversacion`: Identificador de sesión para enlazar preguntas sucesivas y desambiguación.

### C. Base de Conocimiento Real de OBRATEC
Se implementa un catálogo estructurado del sistema en backend que describe:
- Módulos reales existentes y sus rutas en Angular (`/proyectos`, `/inventario`, `/compras`, `/ordenes-trabajo`, `/incidencias`, `/control-costos`, etc.).
- Procedimientos administrativos (creación de obras, aprobación de compras, asignación de maquinaria, gestión de APU).
- Políticas de permisos y roles autorizados.
- La IA tiene prohibido inventar funcionalidades, módulos o botones fuera de esta base verificada.

### D. Motor de Análisis y Recomendaciones Operativas
Se añaden rutinas analíticas deterministas que evalúan:
1. **Desviaciones de Costos:** Obras con costo ejecutado superior a la línea base activa.
2. **Alertas de Stock Crítico:** Insumos con existencia menor al stock mínimo, descontando órdenes de compra en camino.
3. **Órdenes de Trabajo Atrasadas:** Tareas vencidas sin finalizar.
4. **Incidencias Críticas:** Incidencias abiertas de prioridad ALTA/CRITICA sin resolver.
5. **Avances Físicos Lentos:** Unidades con retraso significativo frente a cronograma.

### E. Asistencia Operativa de Bajo Riesgo (Preview + Confirmación)
Flujo seguro de 2 pasos:
1. **Paso 1 (Propuesta):** El usuario pide p.ej. *"Crea una incidencia de prioridad media en la obra Torre Norte: Rotura de tubería menor"*. La IA interpreta los parámetros, valida existencia de la obra y permisos, genera un token temporal de operación (`preview`) con los datos validados y retorna la vista previa con un mensaje claro: *"He preparado la siguiente incidencia: [...]. ¿Deseas confirmarla?"*.
2. **Paso 2 (Confirmación):** El usuario pulsa **Confirmar** en el frontend (o responde "Sí, confirmo"), enviando el ID de la propuesta al endpoint `/api/ai/operacion/confirmar`. El backend revalida permisos y ejecuta la operación reutilizando el servicio de dominio respectivo (`incidencias_services.crear_incidencia`), registrando la acción en `t_bitacora`.
- **Restricciones estrictas:** No se permiten eliminaciones (*soft/hard deletes*), ni cambios de roles/permisos, ni cobros/pagos, ni restauraciones de copias de seguridad.

### F. Interfaz Angular
- El workspace (`/asistente`) y el drawer flotante admiten flujo continuo de mensajes con soporte de:
  - Tarjetas de vista previa de operaciones con botones de confirmación / cancelación interactivos.
  - Badges de entidades referenciadas (obras, compras, usuarios).
  - Sugerencias rápidas de preguntas de seguimiento (*chips*).
  - Integración transparente de entrada por voz (Web Speech API / backend Whisper).

---

## 3. Plan de Implementación Incremental por Etapas

- **Etapa 1:** Conversación, contexto y seguimiento de conversación en `assistant_service.py`.
- **Etapa 2:** Conocimiento del sistema OBRATEC y herramientas administrativas ampliadas en `query_engine.py` / `knowledge_base.py`.
- **Etapa 3:** Módulo de análisis cruzado y recomendaciones preventivas.
- **Etapa 4:** Asistencia operativa con vista previa, token de confirmación y bitácora de auditoría.
- **Etapa 5:** Workspace Angular renovado y pruebas integrales.
