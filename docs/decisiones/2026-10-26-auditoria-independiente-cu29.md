# Auditoría independiente final del CU29

Fecha: 2026-10-26, America/La_Paz. Estado: revisión terminada; correcciones pendientes de decisión. Base Git: `7209f88`, incluyendo los cambios locales y archivos nuevos presentes al revisar. No se atribuyen todos los cambios locales a un autor o commit concreto.

## Dictamen y alcance

**No aprobar todavía el cierre del CU29.** Se identificaron **6 hallazgos altos, 8 medios y 2 bajos**. No se confirmó un hallazgo crítico bajo el alcance y las condiciones de esta revisión. Esto no certifica ausencia de vulnerabilidades en producción.

Se revisaron los ocho módulos backend solicitados, los nuevos módulos de operaciones/análisis/conocimiento, autorización de Reportes, autenticación y política SaaS, los servicios/repositorios de dominio invocados, Angular del asistente y sus servicios y pruebas. Se contrastaron los cambios locales con HEAD. Se consultaron `AGENTS.md`, `ARQUITECTURA_Y_PATRONES.md`, `ARQUITECTURA_REPORTES_IA.md`, `OPERACION_REPORTES.md`, `ARQUITECTURA_BASE_DATOS.md`, el inventario y las rutinas pertinentes, y la nota de refactorización CU29.

No se modificó código de aplicación ni pruebas versionadas. Este documento registra el análisis exigido por AGENTS.md. No se ejecutaron migraciones, workers, correos, operaciones de negocio ni escrituras en PostgreSQL. Las reproducciones de operaciones utilizaron repositorios sustituidos y actores/datos sintéticos.

Las ubicaciones siguientes corresponden a las líneas de la copia auditada; pueden cambiar cuando Antigravity edite los archivos.

## Capas, contratos y contexto de autorización

El flujo de consulta sigue `ai_routes → reportes_services.assistant → assistant_service → repositorios`. La reserva SaaS `consulta_ia` permanece alrededor de la consulta unificada. Las consultas dinámicas conservan esquemas estrictos, fuentes/campos registrados, SQL parametrizado y reautorización.

El nuevo flujo de confirmación es distinto: `ai_routes.post_confirmar_operacion → assistant_operations.ejecutar_propuesta → servicio de dominio → repositorio`. Omite la recarga de `Context` y el permiso de acción. Las autorizaciones que las rutas tradicionales aportaban no se ejecutan automáticamente al llamar al servicio directamente. El análisis operativo introduce SQL en el servicio y evita la autorización por fuente del motor de Reportes.

La conversación sigue vinculada a actor y empresa, pero ahora conserva respuestas con datos y las vuelve a suministrar al planificador. La vista previa y el ticket tampoco comparten un contrato tipado y normalizado por operación. Estos son cambios de responsabilidades y confianza que requieren corrección; esta auditoría no los implementa.

## Crítico

No se confirmó ejecución anónima, SQL arbitrario ni escritura de un administrador de empresa sobre recursos de otra empresa. Los límites de la validación integrada se detallan al final. Los problemas altos de autorización sí se reprodujeron de forma aislada y bloquean la aceptación.

## Alto

### A1. La confirmación omite RBAC actual y las capacidades del dominio que escribe

- **Archivo y ubicación:** `backend/app/routes/ai_routes.py:73-84`; `backend/app/services/ai/assistant_operations.py:95-123`; `backend/app/services/incidencia_services.py:112-115,163-212`; `backend/app/services/suscripcion_policy.py:70-83`; `backend/app/services/planes_catalog.py:15-25`.
- **Evidencia:** la ruta solo depende de `verificar_token`. El permiso se exige al proponer, pero `ejecutar_propuesta` no recarga `context` ni ejecuta `ctx.require`. `incidencia_services.registrar` valida pertenencia y campos, pero la autorización `autorizar_registro` pertenece al flujo de la ruta tradicional. El guard SaaS identifica esta URL como módulo `ia`, sin exigir el módulo `incidencias` que se escribe.
- **Reproducción:** router real en FastAPI, JWT sintético firmado y verificador real; política/identidad y repositorios sustituidos. Se emitió un ticket con `Registrar_incidencias`; durante la confirmación el conjunto actual de permisos estaba vacío y el plan solo habilitaba `ia`. Resultado: **HTTP 200**, llamada a `incidencia_repos.crear`, **cero comprobaciones del permiso actual**. No se insertó nada en una base real.
- **Impacto:** se puede ejecutar una incidencia con permiso revocado o con el módulo de incidencias retirado del plan. Los controles actuales de cuenta activa y coincidencia de rol/empresa con JWT no detectan la revocación de un permiso dentro del mismo rol.
- **Solución recomendada:** recargar actor, empresa y permisos al confirmar; exigir el permiso específico y la capacidad comercial del dominio; comprobar recurso antes de consumir el ticket. Reutilizar una entrada de dominio que incluya las mismas reglas de autorización del flujo ordinario. No resolverlo únicamente agregando un permiso fijo a una ruta que ejecuta tres tipos de operaciones.

### A2. El ticket almacena empresa, pero la ejecución no la impone sobre el recurso

- **Archivo y ubicación:** `assistant_operations.py:29-55,71-79,104-123`; `incidencia_services.py:51-63,171-178`; `frontend/src/app/services/reportes.service.ts:152-158`.
- **Evidencia:** el comentario «coincidencia de usuario y empresa» solo compara `nro_usuario`. La empresa del ticket se recupera, pero para incidencias no se transmite ni se comprueba. La propuesta tampoco verifica que `id_obra` pertenezca a `ctx.empresa` o a las obras autorizadas. Para el administrador global, el servicio de incidencias usa empresa `None`, que permite búsqueda global. La confirmación Angular solo envía el UUID.
- **Reproducción:** contexto global seleccionado en empresa 5; ticket de incidencia con obra 888, cuya empresa simulada era 8. El servicio real, con persistencia sustituida, aceptó la confirmación: **HTTP 200**, obra enviada a crear **888**.
- **Impacto:** la operación global puede escribir en una empresa diferente de la seleccionada y almacenada en el ticket. Cambiar empresa en la interfaz no invalida el ticket del servidor. No se demostró este cruce para `ADMINISTRADOR_EMPRESA`: el servicio de incidencias sí filtra por su empresa JWT. Un JWT antiguo con empresa/rol desactualizado también queda protegido por el guard general; esos controles no sustituyen el vínculo con la empresa de la propuesta.
- **Solución recomendada:** validar pertenencia al proponer y confirmar, imponer siempre la empresa objetivo del ticket, y contrastarla con el contexto explícito actual. Para el global, exigir una selección expresa y consistente en ambos pasos. Probar cambio de empresa con JWT nuevo del mismo usuario y cambio de selección del global. Corregir también estos controles antes de conectar el servicio real de OT.

### A3. El diagnóstico expone dominios sin permiso y omite restricciones por fila

- **Archivo y ubicación:** `backend/app/services/ai/assistant_analysis.py:12-39,57-66,85-101,119-127`; `assistant_service.py:214-221,290-309,418-424`.
- **Evidencia:** el diagnóstico consulta incidencias, OT y RFI sin `ctx.require` ni autorización por fuente. Solo restringe inventario por nombre de rol. Una capacidad de consulta cualquiera permite llegar a esta rama. La selección de obras usa `repo.works`, pero no aplica las restricciones de trabajador sobre sus propias incidencias/OT ni las capacidades limitadas del cliente. La reautorización final solo trata CRM, reportes y `query_scopes`; el diagnóstico no genera estos scopes.
- **Reproducción:** `Context` real de `CLIENTE`, con `Visualizar_reportes` y `Visualizar_avances`, sin permisos de incidencias, OT ni RFI. Con filas sintéticas, el análisis devolvió el título de una incidencia reservada y el tipo de trabajo de una OT reservada. Ejecutó las tres consultas de esos dominios sin rechazar al actor.
- **Impacto:** revelación de actividad operativa a actores sin permiso del dominio dentro de una obra accesible. También permite devolver un diagnóstico sin revalidar los permisos y asignaciones usados después de calcularlo.
- **Solución recomendada:** definir fuentes autorizadas del diagnóstico y reutilizar las políticas de Reportes/consultas, incluyendo restricciones por fila. Omitir explícitamente fuentes no autorizadas o rechazar la solicitud; informar cobertura parcial. Reautorizar los mismos permisos y recursos antes de devolverlo. No basta filtrar `id_empresa`.

### A4. El diagnóstico administrativo falla contra el esquema PostgreSQL actual

- **Archivo y ubicación:** `assistant_analysis.py:85-101`; `assistant_service.py:290-309`.
- **Evidencia real:** en `obras`, con `transaction_read_only=on`, `EXPLAIN` de la consulta de inventario devolvió **42P01: relation "obras.t_inventario_almacen" does not exist**. Las otras tres consultas del diagnóstico pasaron `EXPLAIN`.
- **Impacto:** para `ADMINISTRADOR` y `ADMINISTRADOR_EMPRESA` se ejecuta esa consulta incondicionalmente; el diagnóstico completo termina en error en lugar de entregar indicadores. La prueba nueva no lo detecta porque reemplaza `repo.rows` por una secuencia de resultados.
- **Solución recomendada:** consumir el repositorio/función de inventario vigente, con autorización, columnas y semántica reales. Validar SQL contra el entorno designado sin crear una tabla alternativa para satisfacer la consulta. Mantener el SQL en repositorios. Si falta una fuente instalada, devolver un error específico o un diagnóstico parcial expresamente identificado.

### A5. Dos de las tres operaciones ofrecidas llaman funciones inexistentes

- **Archivo y ubicación:** `assistant_operations.py:130-157`; `backend/app/services/orden_Trabajo_services.py:63`; `backend/app/services/material_services.py:95`.
- **Evidencia:** se llama `orden_Trabajo_services.registrar_orden_trabajo`, pero la función existente es `crear_orden_trabajo(data, token_data, client_ip)`. Se llama `material_services.crear`, pero existe `registrar(data, token, ip)`, con un contrato distinto para la empresa.
- **Reproducción:** confirmaciones a través del router real, sin sustituir esos servicios: **HTTP 500 para crear OT y HTTP 500 para crear material**. El ticket ya había sido retirado de memoria.
- **Impacto:** dos operaciones centrales del CU29 no funcionan y el usuario pierde la propuesta al intentar ejecutarlas.
- **Solución recomendada:** integrar los contratos reales, con autorización y validación de recursos antes de llamar. Agregar pruebas de las tres ramas sin mockear la función de servicio que se pretende verificar. Cambiar solo el nombre de la función de OT es insuficiente: su servicio existente no aporta por sí solo todos los controles de tenant/RBAC exigidos al asistente.

### A6. El historial vuelve a introducir datos cuyos permisos ya pudieron revocarse

- **Archivo y ubicación:** `assistant_service.py:123-129,153,229-243,363,432-444`; `backend/app/repos/reportes_repos.py:273-274`.
- **Evidencia:** se guardan hasta 1.000 caracteres de cada respuesta en `texto_respuesta`; las últimas cuatro respuestas entran después en `historial_conversacion`. Solo se reautoriza la solicitud anterior de reporte; no se validan las fuentes/obras que originaron las respuestas conservadas. Para `accion='ayuda'`, `plan.mensaje` se devuelve directamente. Esto cambia el contrato documentado anterior, que solo reutilizaba preguntas como contexto de lenguaje.
- **Reproducción:** con un actor que actualmente solo tiene acceso a proveedores, el planificador recibió una respuesta anterior sintética de costos `IMPORTE_RESERVADO_999`. Una salida de proveedor simulada con `accion='ayuda'` y ese dato fue aceptada. Se comprobó también que el JSON entregado a `add_message` conserva texto de resultados.
- **Impacto:** los controles de las nuevas consultas no impiden reexponer datos antiguos después de revocar permisos o acceso a una obra. Además, contenido procedente de registros puede pasar de respuesta narrativa a entrada del planificador con capacidad de proponer escrituras.
- **Solución recomendada:** conservar para el lenguaje las preguntas del usuario, o vincular cada respuesta con fuentes, recursos y política verificables y reautorizarlos antes de reutilizar contenido. Invalidar contexto sensible ante revocaciones. No tratar una respuesta previa del modelo como instrucciones confiables.

## Medio

### M1. La vista previa confiable puede sustituirse por un resumen del modelo

- **Archivo y ubicación:** `assistant_service.py:21-27,130-173,312-328`; `assistant_operations.py:34-40,70-90`; `frontend/src/app/components/asistente/asistente.html:63-85`.
- **Evidencia:** `ActionProposal.parametros` es un `dict` libre. El backend calcula `resumen_limpio`, pero prefiere `resumen` del modelo. Angular solo muestra ese resumen, no los parámetros efectivos. La normalización local de título/prioridad/descripción no reemplaza el diccionario que se almacena y ejecuta. El planificador acepta una operación devuelta por el proveedor incluso ante una pregunta de lectura; se reprodujo con «Cuántos proveedores hay» y una propuesta simulada de crear incidencia sobre otro recurso.
- **Impacto:** prompt injection desde mensajes, registros recuperados o respuestas previas puede producir una propuesta cuya descripción visible no corresponde a lo que hará. No se demostró autoejecución: el botón de confirmación sigue siendo necesario y la lista de tres operaciones impide invocar nombres arbitrarios. Esa barrera pierde valor si la vista previa no describe los parámetros reales.
- **Solución recomendada:** modelos estrictos por operación, campos permitidos y valores normalizados persistidos; resumen generado exclusivamente por backend con todos los efectos relevantes, empresa/obra identificables y parámetros visibles. Separar la selección de lectura de la propuesta de escritura y exigir intención clara de creación. Marcar mensajes/registros como contenido no confiable y probar salidas adversarias; un prompt por sí solo no es un control suficiente.

### M2. Se elige silenciosamente la primera obra, incluso si el mensaje la niega o no existe

- **Archivo y ubicación:** `assistant_service.py:64-80,244-252,312-315`.
- **Evidencia:** si no coincide un nombre/código, `target_work = works[0]['id_obra']`. El contexto `id_obra_contexto` se usa en reportes/consultas/análisis, pero no al construir esa propuesta. Se reprodujo selección de obra 9 para «Registra una incidencia por fuga», «Registra una incidencia en la obra Inexistente» y «No crear una incidencia».
- **Impacto:** creación propuesta para la obra incorrecta; la obra activa en Angular puede ser otra. Las negaciones y referencias ambiguas también generan operaciones.
- **Solución recomendada:** usar un contexto de obra autorizado explícito o pedir aclaración; rechazar referencias desconocidas y múltiples coincidencias. No recurrir a la primera fila. Distinguir negación, explicación y solicitud de ejecución.

### M3. Otro usuario puede consumir el ticket antes de recibir el rechazo

- **Archivo y ubicación:** `assistant_operations.py:95-107`.
- **Evidencia y reproducción:** `pop` ocurre antes de validar el propietario. Otro usuario autenticado con el UUID recibió **403**; el propietario legítimo recibió **404** al intentarlo después. La lista de operaciones no llegó a ejecutarse para el usuario ajeno.
- **Impacto:** denegación de una propuesta si se conoce su UUID. No es una posibilidad de adivinar UUID ni una suplantación exitosa; es consumo no autorizado del recurso.
- **Solución recomendada:** consultar y validar propiedad, empresa y estado antes de reclamar la ejecución de forma atómica. Los rechazos ajenos no deben alterar el ticket.

### M4. El ciclo de vida de tickets depende del proceso y cancelar no revoca

- **Archivo y ubicación:** `assistant_operations.py:12-26,70-99`; `frontend/src/app/components/asistente/asistente.ts:274-279`.
- **Evidencia:** diccionario y lock locales al proceso; no hay persistencia ni backend de cancelación. `cancelOperation` solo marca `cancelado` en el mensaje. La limpieza recorre y modifica el diccionario fuera del lock. El vencimiento es de 15 minutos, pero la respuesta no informa la fecha de expiración.
- **Impacto:** reinicio o petición a otro worker pierde la propuesta; una cancelación visual deja el UUID ejecutable hasta expirar. No hay resultado durable recuperable después de perder la respuesta HTTP. La limpieza puede competir con inserciones y consumos; no se realizó una prueba de carga de esa carrera.
- **Solución recomendada:** estado compartido con actor/tenant, expiración, estados PENDIENTE/EJECUTANDO/EJECUTADA/CANCELADA y resultado; transición atómica y cancelación autenticada. Guardar identidad estable para reintentos y mostrar expiración. Mientras exista memoria local, proteger también su limpieza; no confundir el lock local con una garantía entre procesos.

### M5. No hay atomicidad entre ticket, creación, seguimiento y auditoría; los errores de dominio se convierten en 500

- **Archivo y ubicación:** `assistant_operations.py:99,123-128`; `incidencia_services.py:199-212`; `backend/app/repos/incidencia_repos.py:174-197,398-421`; `backend/app/repos/bitacora_repos.py:37-59`; `ai_routes.py:73-84`.
- **Evidencia:** crear incidencia y crear seguimiento abren conexiones y confirman separadamente. La bitácora vuelve a confirmar por separado y el asistente agrega otra entrada después. El ticket se elimina antes de todo ello. La ruta nueva no traduce `IncidenciaError` a su estado HTTP, como sí hace la ruta original. Una prioridad inválida se reprodujo como **500**, no como error de validación.
- **Impacto:** un fallo posterior al primer commit puede dejar una incidencia creada aunque el cliente reciba error y no pueda recuperar el resultado con el ticket. Pedir otra propuesta puede duplicar la acción. Esta falta de transacción en incidencias ya existía; el flujo nuevo la incorpora junto con consumo anticipado del ticket.
- **Solución recomendada:** definir una transacción de dominio para creación, seguimiento y auditoría; asociar el resultado durable a la identidad de operación. Resolver reintentos sin repetir la escritura y preservar un estado incierto cuando no pueda conocerse el resultado. Traducir errores de negocio a 4xx/409 según el contrato y validar antes de reclamar ejecución.

### M6. Angular acepta una confirmación tardía después de cambiar empresa/obra

- **Archivo y ubicación:** `frontend/src/app/components/asistente/asistente.ts:155-174,254-272`.
- **Evidencia:** `send`, descarga y selección de obra protegen sus respuestas con `version`; `confirmOperation` no lo hace. La suscripción de contexto limpia mensajes y libera `busy`, pero la promesa vieja luego agrega un mensaje al nuevo contexto y vuelve a modificar `busy`/errores.
- **Reproducción:** se extrajeron y transpilaron los métodos actuales del archivo con TypeScript, se dejó pendiente la confirmación, se simuló el cambio de versión y limpieza de mensajes, y se resolvió la respuesta. El mensaje «Operación empresa A» apareció en la lista del contexto nuevo. Es una reproducción de los métodos, no una prueba completa de navegador.
- **Impacto:** información de una operación previa aparece bajo otra empresa/obra; una confirmación vieja puede interferir con el indicador de una petición nueva o con la destrucción del componente.
- **Solución recomendada:** capturar versión, actor y tenant al iniciar; descartar efectos de UI si cambian, incluido `finally`. No presentar el descarte visual como cancelación de una escritura que el servidor ya pudo ejecutar. Combinarlo con M4 para consultar su estado.

### M7. Dos nuevas fuentes modulares no coinciden con las columnas reales

- **Archivo y ubicación:** `backend/app/services/ai/query_engine.py:66,69`; `backend/app/repos/assistant_repos.py:14-24`.
- **Evidencia real:** `information_schema.columns` de `obras` confirmó que `t_obra_usuario` no contiene `id_obra_usuario`, `rol_obra` ni `activo`; `t_empresa` no contiene `direccion`, `estado_empresa` ni `created_at`. El guard de esquema rechaza ambas fuentes con **503** antes de su consulta de datos.
- **Impacto:** `personal_obra` y `empresas` se ofrecen en el catálogo a actores habilitados, pero fallan al utilizarlas. Las demás tablas/columnas declaradas en MODULES sí se encontraron en la inspección, excluyendo el nombre calculado por join `nombre_completo`.
- **Solución recomendada:** ajustar campos y claves al esquema comprobado; no agregar columnas para hacer coincidir suposiciones. Añadir comprobación de metadatos/EXPLAIN para cada fuente nueva y pruebas de contrato con datos representativos.

### M8. Las pruebas nuevas no verifican los contratos y controles que afirman cubrir

- **Archivo y ubicación:** `backend/tests/test_asistente_administrativo.py:57-119`; `backend/tests/test_assistant_queries.py:111-121,201-214`; `frontend/src/app/components/asistente/reportes-asistente.spec.ts`; `frontend/src/app/services/reportes.service.spec.ts`.
- **Evidencia:** las seis pruebas nuevas cubren conocimiento, esquema, una incidencia con `ctx.require` y servicio sustituidos, y análisis con `repo.rows` sustituido. El mock de incidencia devuelve `data.id_incidencia`, diferente del contrato real. No hay casos de OT/material reales, revocación al confirmar, empresa del ticket, expiración, propietario ajeno, cancelación, procesos, SQL del diagnóstico o inyección desde registros. Las pruebas Angular existentes no incluyen `confirmOperation`/`cancelOperation` ni su transporte HTTP.
- **Evidencia adicional:** la prueba «without_persisting_rows» busca `Acme` en `str(save.call_args)`. `psycopg2.extras.Json` se representa como objeto, ocultando el contenido: se reprodujo texto presente en `.adapted['texto_respuesta']` mientras la búsqueda en `str(call_args)` devolvía falso. La prueba aprueba aunque haya persistencia de datos.
- **Impacto:** suites verdes con fallos de funcionamiento y autorización comprobados en esta revisión. La prueba SQL mockeada solo cubre tres fuentes anteriores, con columnas inventadas a partir de MODULES, y no detecta el esquema incorrecto de las nuevas.
- **Solución recomendada:** comprobar argumentos JSON reales, usar `Context` real para decisiones de permiso y mantener dobles en el límite de persistencia/proveedor. Agregar casos negativos y pruebas HTTP de la confirmación. Completar aceptación contra PostgreSQL de pruebas designado con dos tenants, fallos y concurrencia; añadir pruebas DOM/navegador de confirmar, cancelar, expirar y cambiar contexto.

## Bajo

### B1. El conocimiento «verificado» contiene rutas y capacidades incorrectas

- **Archivo y ubicación:** `backend/app/services/ai/knowledge_base.py:115,148,163,218-267`; `frontend/src/app/app.routes.ts:172`.
- **Evidencia:** indica `/equipo-maquinaria`, pero la ruta Angular es `/equipos-maquinaria`; fija 500 consultas/mes cuando el cupo es configurable; presenta restauración como capacidad sin reflejar su bloqueo operativo vigente. Filtra por listas de roles, sin consultar los campos `permiso_ver`/`permisos` que declara ni las capacidades actuales.
- **Impacto:** instrucciones incorrectas y módulos presentados como habilitados aunque no correspondan a los permisos reales. La base de conocimiento no concede acceso al endpoint, pero sí contradice la promesa de orientación verificada.
- **Solución recomendada:** contrastar rutas con el registro real, expresar restricciones operativas y obtener capacidades/cupos actuales; filtrar por permisos efectivos. Probar rutas y procedimientos concretos, no solo que exista un resultado.

### B2. Una incidencia exitosa pierde el ID del recurso en la respuesta

- **Archivo y ubicación:** `assistant_operations.py:123-124,163-168`; `incidencia_services.py:208-212`; `test_asistente_administrativo.py:80`.
- **Evidencia:** el servicio devuelve `id_incidencia` en el nivel superior, pero el asistente busca `resp.get('data', {})`. La reproducción del endpoint devolvió `success=true` con `resultado={}` después de llamar al repositorio. El mock del test oculta la discrepancia.
- **Impacto:** no se puede enlazar o comprobar el recurso creado desde el resultado, lo que dificulta verificar qué se ejecutó y resolver errores o duplicados.
- **Solución recomendada:** normalizar respuestas tipadas por operación y conservar el ID/estado real. Validar el éxito devuelto por el dominio antes de marcar la propuesta como ejecutada.

## Mejoras opcionales

1. **Completar y describir el alcance del diagnóstico.** La nota CU29 promete desviaciones de costos, stock bajo mínimo descontando compras y avance lento; el módulo implementado evalúa incidencias, OT, stock igual o inferior a cero y RFI. Después de corregir seguridad/SQL, reutilizar indicadores existentes para costos y reposición, o actualizar la nota para diferenciar lo implementado de lo pendiente. El `LIMIT 20` de stock debería distinguir muestra de total al presentarse. Ubicación: `assistant_analysis.py:29-161` y nota de refactorización CU29, sección D. Beneficio: evitar interpretar este resultado como diagnóstico financiero integral.
2. **Completar la presentación del flujo.** Tipar `Message.operacion_propuesta`/`resultado_analisis`, ofrecer filtros para los tres temas nuevos y separar sugerencias de texto de acciones. Los chips «Confirmar ejecución» y «Cancelar operación» se envían actualmente como preguntas mediante `send`, no ejecutan esas acciones. Ubicación: `asistente.ts:39-43,109-119,254-279`; `asistente.html:24-36,103-106`; `assistant_service.py:329`. Beneficio: coherencia entre botones y conversación, sin ampliar permisos.

## Validación ejecutada y cobertura funcional

### Suites del repositorio

Se ejecutaron mediante `pytest` para conservar las fixtures del proyecto. Se bloqueó `psycopg2.connect` durante las suites aisladas para impedir conexiones accidentales. No se interpreta el número de casos como porcentaje de cobertura funcional ni de líneas.

| Suite | Resultado | Qué verifica realmente |
| --- | --- | --- |
| `test_asistente_administrativo.py` | 6 aprobadas | Funciones puras y flujo con contexto/servicio/repositorio simulados. Sin HTTP, permisos persistidos ni SQL real. |
| `test_assistant_queries.py` | 25 aprobadas | Validadores/evaluador reales; proveedor, datos, transacciones y parte de autorización sustituidos. Comprobaciones textuales de SQL, no aislamiento con dos tenants reales. |
| `test_reportes.py` | 33 aprobadas | Autorización con actores simulados, cálculos/exportadores reales, scheduler y worker con repos/correo sustituidos; proveedor DeepSeek con transporte simulado y STT desactivado. |
| `test_reportes_api.py` | 7 aprobadas | Rutas/validación/headers y registro de aplicación mediante TestClient; autenticación y servicios sustituidos. No confirmación CU29 ni permisos en BD. |
| `test_reportes_personalizacion.py` | 14 aprobadas | Contratos/presentación/cálculos y coordinación con mocks. Incluye rechazo de conversación ajena simulado. |
| `test_security_rules.py` | 3 aprobadas | Distinción funcional global/empresa, sin cuentas persistidas. |
| `test_suscripcion_restricciones.py` | 43 aprobadas | Política SaaS y guards con persistencia simulada; no reserva mensual concurrente en PostgreSQL real. |
| `test_configuracion_planes.py` | 34 aprobadas | Reglas/contratos/HTTP y repositorio en memoria. |
| `test_control_costos_services.py` | 17 aprobadas | Casos de dominio y cálculos con repositorios sustituidos. |
| **Subtotal principal** | **182 aprobadas; 9 subtests aprobados** | Regresión aislada. |
| Dominios relacionados: `test_consulta_tecnica`, `test_material_services`, `test_incidencia_services`, `test_incidencia_authorization`, `test_incidencia_atencion`, `test_incidencia_candidatos`, `test_incidencia_registro_movil`, `test_incidencia_validacion_bd`, `test_ot_afectacion`, `test_obra_personal` | **192 aprobadas, 6 omitidas; 38 subtests aprobados** | Mayormente lógica real con repositorios/actores sustituidos. `test_incidencia_validacion_bd` sí ejecuta restricciones y escrituras, pero en **SQLite en memoria**, no en PostgreSQL. Las seis integraciones PostgreSQL optativas de personal quedaron omitidas. |
| Angular: `npm.cmd run test:reportes` | **25 aprobadas, 3 archivos** | TestBed/DOM emulado y HttpTestingController, servicios o HTTP sustituidos. Incluye limpieza de consultas ante cambio de empresa y liberación de micrófono simulado; no el ciclo nuevo de confirmación. |

**Total backend: 374 pruebas aprobadas y 6 omitidas; 47 subtests aprobados.** Angular: 25 aprobadas. El único aviso final del backend fue la deprecación de Starlette/TestClient respecto a httpx.

Comandos principales, desde `backend`, envolviendo `pytest.main` con bloqueo de conexión PostgreSQL:

```text
pytest -q -p no:cacheprovider tests/test_asistente_administrativo.py tests/test_assistant_queries.py tests/test_reportes.py tests/test_reportes_api.py tests/test_reportes_personalizacion.py tests/test_security_rules.py tests/test_suscripcion_restricciones.py tests/test_configuracion_planes.py tests/test_control_costos_services.py
pytest -q -p no:cacheprovider tests/test_consulta_tecnica.py tests/test_material_services.py tests/test_incidencia_services.py tests/test_incidencia_authorization.py tests/test_incidencia_atencion.py tests/test_incidencia_candidatos.py tests/test_incidencia_registro_movil.py tests/test_incidencia_validacion_bd.py tests/test_ot_afectacion.py tests/test_obra_personal.py
```

Una primera ejecución de auditoría bloqueó también sockets de loopback y afectó TestClient en Windows; otra sustitución demasiado amplia afectó la prueba del pool. Se corrigió el aislamiento del ejecutor y se repitieron las suites con bloqueo exclusivo de la conexión real. Esos fallos del ejecutor no se atribuyen al producto. PowerShell bloqueó `npm.ps1`; la suite Angular se ejecutó correctamente con `npm.cmd`.

### Comprobaciones reales de base de datos, sin datos de negocio

- `python tests/reportes_sql_readonly_check.py`: **82 consultas pasaron EXPLAIN**. El script no usa ANALYZE, no ejecuta operaciones de negocio y revierte/cierra la conexión.
- Inspección adicional con conexión configurada y `default_transaction_read_only=on`, `statement_timeout=15000`, rollback final: se comprobó **`transaction_read_only=on`**, columnas declaradas de **18 fuentes** y los cuatro SQL del diagnóstico con `EXPLAIN` y savepoints. Resultado: dos fuentes con columnas ausentes y una consulta de análisis con tabla inexistente, descritas en A4/M7.
- Se confirmó que `t_consulta_tecnica` existe con las columnas declaradas por la consulta; **esto no acredita que se aplicara exactamente el script CU23 ni su historial de migración o todos sus grants/triggers**.
- No se consultaron filas de clientes, usuarios, obras ni inventario. No se verificó la matriz actual completa de permisos en la base ni se ejecutaron funciones mutadoras.

### Reproducciones adicionales de auditoría

No se agregaron tests al código. Se ejecutaron comprobaciones efímeras con el código actual:

| Caso | Resultado observado | Límite de la evidencia |
| --- | --- | --- |
| Confirmar sin Bearer / JWT inválido | 401 / 401 | Router aislado con autenticación real; no despliegue completo. |
| Ticket válido después de revocar permiso y retirar módulo de incidencias | 200, se alcanzó `crear`; cero verificaciones de permiso | JWT sintético firmado; estado de cuenta/política y repositorios simulados; servicio de incidencia real. |
| Reutilizar ticket ejecutado | 404 | Un proceso, sin concurrencia entre workers. |
| Usuario ajeno con UUID / propietario después | 403 / 404 | El primero no ejecuta, pero destruye la propuesta. |
| Ticket con fecha pasada | 404 | Vencimiento simulado, no espera de 15 minutos. |
| Crear OT / crear material | 500 / 500 | Despacho real a servicios, sin mockear sus funciones. |
| Error de validación de incidencia | 500 | Prioridad inválida, dominio real con repositorios sustituidos. |
| Global con ticket empresa 5 y obra de empresa 8 | 200, obra 888 enviada a crear | Pertenencia simulada en repositorio; no escritura real ni escalada de un administrador de empresa. |
| CLIENTE sin permisos de OT/incidencias/RFI | Datos operativos incluidos en recomendaciones | Context real, filas sintéticas; no consulta a usuarios reales. |
| Reutilización de respuesta anterior de dominio revocado | Se envía al proveedor; salida `ayuda` con dato aceptada | Proveedor adversario simulado; no prueba de explotación de DeepSeek/Gemini reales. |
| Confirmación Angular tardía | Respuesta antigua incorporada al contexto nuevo | Métodos originales extraídos/transpilados; no aceptación visual en navegador. |

Las reproducciones HTTP montaron el router real en una aplicación FastAPI aislada, manteniendo el verificador JWT y el guard SaaS, con la lectura de epoch sustituida. Una exploración inicial de la fábrica completa quedó detenida por su middleware de mantenimiento con 503; no se desactivó ni modificó el mantenimiento real para continuar. Los resultados del router aislado no acreditan integración con la barrera de mantenimiento.

### Evaluación de las diez prioridades solicitadas

| Prioridad | Evaluación |
| --- | --- |
| 1. Multitenant y RBAC | Las lecturas dinámicas conservan filtros de empresa/obra y permisos por fuente. No se demostró cruce entre tenants para un administrador de empresa. Diagnóstico y operaciones tienen los incumplimientos A1-A3. |
| 2. Endpoint confirmar | Auditado estáticamente y mediante HTTP aislado con JWT firmado y dominio real/repositorios sustituidos. Fallos A1/A2/A5/M3/M5/B2. |
| 3. Tickets UUID | UUID4 y un consumo local bajo lock; expiración y propietario ajeno rechazan ejecución. Falta vínculo efectivo de empresa, cancelación, estado compartido e idempotencia recuperable; consumo ocurre antes de autorización. |
| 4. Revalidar al ejecutar | No se revalida el permiso específico; la validación general de cuenta/rol/empresa sí permanece en HTTP. |
| 5. Historial ajeno | `get_conversation` filtra simultáneamente UUID, empresa, usuario y expiración; se llama antes de `conversation_inputs`. No se encontró una vía directa de consultar conversación ajena por cambiar el UUID. Pruebas existentes usan repositorios simulados; falta ensayo PostgreSQL con dos tenants. A6 es un problema diferente: datos antiguos de la propia conversación tras revocación. |
| 6. Prompt injection | SQL/campos/fuentes se validan determinísticamente y no hay `eval` de herramientas del proveedor. El nuevo contexto mezcla respuestas derivadas de registros con planificación, acepta mensajes de ayuda libres y vistas previas del modelo; A6/M1. No se invocaron LLM reales para medir ataques. |
| 7. Dominio/transacciones | Incidencias reutiliza servicio; OT/material apuntan a funciones inexistentes. No hay una transacción de ejecución completa; A5/M5. |
| 8. Operaciones autorizadas | Solo tres nombres aceptados; no se encontró despacho arbitrario a pagos, roles, eliminación o restore. Parámetros, empresa, resumen e intención no quedan suficientemente ligados a la confirmación; A1/A2/M1/M2. |
| 9. Nuevos módulos | `consultas_tecnicas` filtra empresa y obras autorizadas; suscripción filtra empresa; planes es catálogo global explícito; personal hereda tenant por obra, pero falla por columnas. `empresas` usa lectura global solo para el global y falla por columnas. `incidencias` también existe en REGISTRY y la precedencia mantiene la ruta de Reportes; su nueva entrada MODULES no representa una lectura independiente. No se certifica aislamiento sobre filas reales. |
| 10. Regresión existente | Permanecen generación/exports de Reportes, adaptadores DeepSeek/Gemini, reserva SaaS y voz. Suites y SQL de Reportes pasan con los límites descritos. El diagnóstico nuevo falla y las operaciones eluden la política del dominio; no declarar conservación funcional completa solo por pruebas verdes. |

### Aspectos que no quedaron comprobados

- Alta/lectura reales en dos tenants, revocación persistida durante una solicitud, permisos actuales completos, rollback integral y duplicados bajo fallos/concurrencia. No hay una base de pruebas designada para esos ensayos.
- Tickets repartidos entre procesos/instancias, reinicios y carga concurrente. Las limitaciones descritas provienen del almacenamiento local y del orden de ejecución comprobados en código.
- Interfaz completa en navegador real, accesibilidad visual, dictado real, Whisper activado, permisos de micrófono de dispositivo, voz y confirmación en Flutter. No se ejecutó el script de navegador de Reportes ni un build de Angular como sustituto de aceptación funcional.
- DeepSeek/Gemini reales, disponibilidad de claves/configuración en despliegue y resistencia empírica a prompt injection. Se conservaron sus adaptadores; la suite ejercita DeepSeek con transporte simulado y la selección de proveedor, sin acreditar funcionamiento real de ambos.
- Worker/correos/programaciones en vivo, integración de mantenimiento y despliegue. No se iniciaron procesos de envío ni se alteraron barreras.

## Orden recomendado de corrección y aceptación

1. Corregir A1-A3 y A6: autorización al confirmar, tenant objetivo, permisos del diagnóstico y reutilización del historial.
2. Corregir A4/A5 y M7: consultas y funciones que hoy no funcionan contra el proyecto real.
3. Cerrar el contrato de propuesta/confirmación y el estado transaccional del ticket, y resolver M1-M6/B2.
4. Reforzar pruebas conforme a M8 y repetir aceptación sobre un PostgreSQL de pruebas designado, con dos tenants y fallos controlados; después validar los flujos Angular en navegador real y voz en dispositivo.

Estas recomendaciones son un entregable de auditoría. No se aplicaron correcciones ni se modificó la arquitectura de referencia para presentar los defectos como comportamiento aprobado.
