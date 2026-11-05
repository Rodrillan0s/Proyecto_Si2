# CU29: validación diferencial de las correcciones

Fecha: 2026-10-26, America/La_Paz. Referencia: [auditoría original](2026-10-26-auditoria-independiente-cu29.md). Se contrastó también la [nota de correcciones](2026-10-26-correccion-auditoria-cu29.md). Base Git: `7209f88`, con cambios locales y archivos nuevos. No hay un commit intermedio que identifique exclusivamente la entrega corregida: la comparación se hace contra las causas y reproducciones documentadas en los 16 hallazgos originales.

## Dictamen

**CU29 no está listo para cerrarse.** Resultado: **4 CORREGIDOS, 12 PARCIALMENTE CORREGIDOS y 0 PENDIENTES sin avance**. «Parcialmente corregido» incluye requisitos originales que siguen pendientes y regresiones introducidas al corregirlos; no significa que sean aceptables para cierre.

Las suites disponibles pasan, pero se reprodujeron errores 500 en operaciones y continuación de conversación, un bypass comercial por módulo, autorización incompleta del diagnóstico y ausencia de garantías de atomicidad/idempotencia. Estos resultados bloquean la aceptación.

Esta revisión fue diferencial: no repite una auditoría general de otros módulos. No se modificó código, pruebas, configuración ni migraciones. El único archivo nuevo de esta validación es este informe, requerido por AGENTS.md. No hubo escrituras en PostgreSQL, envíos, workers ni cambios en mantenimiento.

## Contexto y criterio de comprobación

Se consultaron AGENTS.md, arquitectura/patrones, arquitectura y operación de Reportes/IA, arquitectura de base de datos y las referencias pertinentes al inventario/rutinas. Se verificaron las correcciones en las capas y contratos afectados: rutas de IA, coordinación, contexto de autorización, tickets, servicios/repositorios de las tres operaciones, diagnóstico, historial y Angular.

Se considera CORREGIDO un hallazgo cuyo defecto concreto dejó de reproducirse y tiene evidencia de ejecución dentro del alcance indicado. No certifica componentes externos no ejecutados. En particular, B2 se refiere a la extracción del ID; no certifica que la creación completa de incidencias funcione, porque sigue bloqueada por A5.

El flujo aún usa `routes → services → repos → PostgreSQL`, con SQL de diagnóstico/reautorización dentro de servicios y commits propios de los repositorios de dominio. El contexto real es `services/reportes/authorization.Context`: contiene usuario, empresa, rol, persona, permisos y correo; **no contiene `obras_autorizadas`**. Las propuestas y resultados siguen en memoria por proceso. Esas diferencias entre contratos reales y mocks son decisivas para esta validación.

## Pruebas y nivel de evidencia

| Código | Comprobación ejecutada | Alcance real y límites |
| --- | --- | --- |
| T1 | Regresión principal: **193 aprobadas**, 9 subtests | Incluye las **17** pruebas actuales de `test_asistente_administrativo.py`, antes 6. Se bloquearon conexiones `psycopg2.connect`. Hay lógica real, exportadores y validadores, pero contexto, servicios o persistencia sustituidos según cada test. No equivale a integración PostgreSQL. |
| T2 | Dominios relacionados: **192 aprobadas, 6 omitidas**, 38 subtests | Incidencias, material, OT, RFI y personal. Las omitidas son integraciones PostgreSQL optativas de personal. Las pruebas de restricciones CU19 usan SQLite en memoria; las demás son principalmente pruebas con repositorios sustituidos. |
| T3 | Reproducciones HTTP del router real, con JWT sintético firmado, verificador y `Context` reales | Aplicación FastAPI aislada; cuenta/política y persistencia simuladas; creación de material por servicio real. Sin middleware de mantenimiento de la fábrica completa ni servidor desplegado. Detectó 403 correctos, bypass de módulo y 500 de integración. |
| T4 | Ejecución de las tres funciones reales de dominio, sustituyendo solo persistencia/bitácora | Para aislar el despacho posterior al error de A5, se usó un contexto de prueba con `obras_autorizadas`, que **no existe en producción**. Esta prueba valida nombres, argumentos y resultados posteriores; no acredita el flujo completo. Incluye fallo de seguimiento después de crear y reintento. |
| T5 | PostgreSQL real, conexión con `default_transaction_read_only=on`, timeout y rollback final | **82 EXPLAIN de Reportes aprobados**. Adicionalmente, **9 EXPLAIN focalizados: 8 aprobados y 1 fallido**, metadatos de columnas y definición de la función oficial de inventario. Sin ANALYZE, filas de negocio, migraciones ni escrituras. |
| T6 | Angular: **25 pruebas aprobadas** en 3 archivos; más **6 comprobaciones temporales** de métodos actuales | TestBed/DOM emulado y HTTP simulado. Se extrajeron/transpilaron los métodos originales `confirmOperation` y `cancelOperation`, sin editar el archivo: éxito normal, éxito tardío y error tardío para cada uno. No es aceptación de navegador real o voz real. |
| T7 | Reproducciones focalizadas de planificación, diagnóstico, conocimiento y tickets entre procesos | Funciones reales con datos sintéticos; proveedor y filas sustituidos cuando corresponde. La prueba entre procesos usa un segundo intérprete real: el ticket existe en el primero y falta en el segundo. Sin escritura de negocio. |

**Total de suites backend: 385 aprobadas, 6 omitidas y 47 subtests aprobados. Angular: 25 aprobadas.** Las reproducciones adicionales no se suman artificialmente a esos totales. El aviso de backend fue la deprecación Starlette/TestClient respecto a httpx.

## Tabla de los 16 hallazgos originales

En ubicaciones abreviadas, `assistant_*.py`, `knowledge_base.py` y `query_engine.py` pertenecen a `backend/app/services/ai/`; los demás archivos indican su ruta cuando es necesario. Líneas de la copia validada.

| ID y hallazgo original | Estado | Evidencia de la corrección y defecto restante | Pruebas realizadas |
| --- | --- | --- | --- |
| **A1. Revalidación RBAC/SaaS al confirmar** | **PARCIALMENTE CORREGIDO** | `assistant_operations.py:203-230` recarga el contexto, exige el permiso específico y comprueba escritura. Revocar `Registrar_materiales` devuelve **403** y conserva PENDIENTE; suspender el plan también devuelve **403**. Sin embargo, solo se llama `exigir_escritura`, sin exigir el módulo de destino: con plan activo que únicamente habilita `ia`, confirmar material devuelve **200** y alcanza `material_repos.crear`. Persiste el bypass de un módulo retirado del plan. | T1: tests A1 con mocks; T3: JWT, guard, contexto y servicio de materiales reales, repositorios/política simulados. |
| **A2. Vinculación a usuario/empresa y recurso** | **PARCIALMENTE CORREGIDO** | `assistant_operations.py:203-240` comprueba empresa real de la obra y fuerza empresa del ticket al dominio. Una obra simulada de empresa 8 para ticket de empresa 5 devuelve **403**; un JWT nuevo del mismo usuario trasladado a empresa 6 también obtiene **403 al confirmar**. Pero el control de obras usa un atributo inexistente de `Context` (`:71,88,214,223`), sin integración funcional. Además, cancelar ese ticket con el mismo usuario ya en empresa 6 devuelve **200**: `cancelar_propuesta:141-157` solo compara usuario. El contexto seleccionado del global no se transmite en confirmar/cancelar. | T1: test A2 con contexto simulado; T3: pertenencia/traslado/cancelación, con contexto real para la ejecución. |
| **A3. Protección del diagnóstico por fuente y fila** | **PARCIALMENTE CORREGIDO** | Se omiten dominios sin permiso para CLIENTE y se agregan filtros de trabajador. Pero `assistant_analysis.py:146` sigue consultando inventario para ADMINISTRADOR_EMPRESA sin permiso, y usa `Visualizar_materiales` en lugar del permiso de inventario del flujo existente. El nuevo filtro de incidencias del trabajador (`:65`) referencia **`i.id_usuario`, inexistente**, confirmado con PostgreSQL. Tampoco hay reautorización de fuentes al devolver el diagnóstico: se reprodujo un dato de incidencia presente en la respuesta tras retirar su permiso en el contexto final (`assistant_service.py:449-455`). | T1: tests A3 mockeados; T5: **42703** real en SQL de trabajador; T7: omisión de fuentes, consulta sin permiso y revocación antes de respuesta con Context reales/filas sintéticas. |
| **A4. Diagnóstico contra inventario real** | **PARCIALMENTE CORREGIDO** | `assistant_analysis.py:150-153` elimina la tabla inexistente y llama a `fn_listar_inventario_empresa`; su SQL pasa EXPLAIN real. Sin embargo, pide estado **`AGOTADO`**. La definición actual de PostgreSQL genera **`SIN_STOCK`** para stock cero y aplica igualdad `bm.estado_stock = p_estado_stock`. El nuevo filtro no selecciona los agotados y puede omitir una alerta aunque ya no falle por tabla ausente. | T1: test A4 sustituye filas y no detecta el estado inválido; T5: EXPLAIN y lectura real de la definición de función, sin consultar inventario de clientes. |
| **A5. Creación real de OT y materiales** | **PARCIALMENTE CORREGIDO** | Las llamadas ahora apuntan a funciones existentes (`assistant_operations.py:255,281,310`). Material alcanza el servicio real y devuelve ID **302** en T3. Incidencia y OT, sin embargo, fallan al proponer con **AttributeError: `Context` no tiene `obras_autorizadas`**; un ticket sintético válido también responde **500** al confirmar con el contexto real. Al aislar ese bloqueo con un contexto de prueba ampliado, los tres servicios reales devuelven IDs correctos; esto no sana el camino normal. | T1: los tests «contrato real» sustituyen las funciones de dominio completas; T3: fallos con Context real; T4: servicios reales y repositorios sustituidos, adaptación expresamente limitada al test. No se insertaron recursos en PostgreSQL. |
| **A6. Historial sensible en el planificador** | **PARCIALMENTE CORREGIDO** | `assistant_service.py:139-145` ya envía únicamente pregunta y tema: la respuesta antigua sensible deja de entrar al prompt. Ese aspecto de seguridad pasa el test. Pero el flujo de conversación válido se rompe en `:263`: **`repo.conversation_request` no existe**. Tras pasar pertenencia/UUID, la continuación devuelve **500** antes de planificar. La seguridad del payload está corregida aisladamente; la solución integrada del historial no funciona. Continúa la persistencia de `texto_respuesta`, aunque ya no se reutiliza en ese payload. | T1: test A6 con proveedor simulado; T3: continuación HTTP de conversación válida y reproducción directa del AttributeError; inspección del repositorio confirma ausencia de la función. |
| **M1. Vista previa y parámetros confiables** | **PARCIALMENTE CORREGIDO** | El resumen ahora se genera en backend (`assistant_operations.py:76-104`) y Angular muestra parámetros (`asistente.html:76-83`); un resumen adversario se ignora. Hay modelos por operación y un guard de intención. Pero «**Lista el material nuevo**» todavía genera `accion='operacion'`: el guard equipara la palabra `nuevo` con una solicitud de creación. Además se retiraron `extra='forbid'`, los límites de listas y el Literal de `ReadPlan` (`assistant_service.py:20-35`); un plan con cinco reportes y un campo extra `sql` se acepta ignorando este último. No se ejecutó SQL arbitrario: es pérdida de validación del contrato, no prueba de ejecución de SQL. | T1: test de lectura/operación con proveedor simulado; T4: resumen backend con funciones de dominio reales; T7: intención de lectura y validación real de Pydantic. |
| **M2. Obra implícita y negaciones** | **PARCIALMENTE CORREGIDO** | Se eliminó `works[0]`, se pide aclaración sin obra/contexto y se usa la obra activa autorizada. La negación original «No crear...» queda protegida. Pero `assistant_service.py:75-76` adopta el contexto aun cuando la pregunta nombra una obra desconocida: con contexto 10, «Registra incidencia en obra Desconocida» propone operar en **10**. La referencia desconocida sigue convirtiéndose en otra obra sin aclaración. | T1: test M2 cubre falta de obra/negación; T7: obra activa, desconocida y comparación de parámetros del plan. |
| **M3. Consumo del ticket por usuario ajeno** | **CORREGIDO** | `assistant_operations.py:180-193` comprueba propietario antes de pasar a EJECUTANDO. Otro usuario recibe **403**; el ticket sigue presente y su propietario puede cancelarlo (**200**). No se consume al rechazar al actor ajeno. | T1: test M3; T3: HTTP aislado con JWT firmado y comprobación del estado preservado. |
| **M4. Cancelación, expiración y estado compartido** | **PARCIALMENTE CORREGIDO** | Existe cancelación backend, limpieza bajo lock y `expira_en` ISO. Cancelar responde **200**, luego confirmar **404**; ticket vencido también **404**. Persiste `_propuestas` local (`assistant_operations.py:42-45`): un segundo proceso real recibe **404** aunque el primero conserva el ticket. Tras éxito se guarda resultado y acto seguido se borra el registro (`:340-344`); repetir devuelve **404**, sin resultado idempotente recuperable. | T1: test M4; T3: cancelación/expiración/replay; T7: dos intérpretes reales, sin DB. |
| **M5. Atomicidad, errores e idempotencia** | **PARCIALMENTE CORREGIDO** | El mapeo de errores de dominio a 4xx está añadido (`assistant_operations.py:330-338`). No existe una transacción que abarque ticket, creación, seguimiento y auditoría; los commits de dominio siguen separados. Ante cualquier fallo se vuelve a PENDIENTE (`:325-328`). Con servicios reales, repositorios sustituidos y el contexto ampliado de T4, se simuló fallo de seguimiento tras crear: **500**, estado PENDIENTE; reintentar invocó `crear` **dos veces**, devolviendo ID 602 en el segundo intento. No es prueba de dos commits PostgreSQL reales, pero reproduce la coordinación que permitiría repetir una escritura ya confirmada. | T1: test M5 simula la excepción del servicio completo; T4: servicio de incidencia real/fallo en repositorio de seguimiento, revisión de commits existentes. Sin ensayo de rollback/concurrencia sobre DB real. |
| **M6. Respuestas tardías de confirmación Angular** | **CORREGIDO** | `asistente.ts:254-309` captura versión y empresa y protege éxito, catch y finally, tanto al confirmar como al cancelar. Se comprobaron los métodos actuales: respuestas/errores viejos no agregan mensajes, no sobrescriben el error del contexto nuevo ni liberan el busy de una petición nueva. La versión también cambia al cambiar obra y al destruir el componente. | T6: **6 comprobaciones aprobadas** sobre métodos originales y **25 pruebas Angular aprobadas**. Sin navegador real; no se usa el build como prueba del flujo. |
| **M7. Columnas de fuentes nuevas** | **CORREGIDO** | `query_engine.py:66,69` usa campos actuales: `personal_obra` con `id_obra,id_usuario,fecha_asignacion`; `empresas` con `id_empresa,nombre_empresa,nit,descripcion`. Metadatos del PostgreSQL actual no muestran columnas ausentes y las consultas generadas pasan EXPLAIN. Se conserva el filtro por empresa/obra en personal y el catálogo de empresas exclusivo del global. | T5: metadatos y EXPLAIN reales de ambas fuentes; como comprobación de regresión del mismo lector, también pasó `consultas_tecnicas`. Sin extraer filas de negocio. |
| **M8. Calidad y cobertura de pruebas** | **PARCIALMENTE CORREGIDO** | Hay 17 pruebas CU29 en lugar de 6 y se añadieron casos negativos. Continúan usando MagicMock para el contexto y sustituyendo funciones enteras de dominio en los tests llamados «contrato real». El test de trabajador exige en un string la columna incorrecta `i.id_usuario`. Sigue la búsqueda ineficaz `assertNotIn('Acme',str(save.call_args))` en `test_assistant_queries.py:214`. No hay tests de la continuación válida de conversación ni del ciclo HTTP de confirmación/cancelación en la suite entregada. Las 25 pruebas Angular siguen sin cubrir esos métodos nuevos. | T1/T2/T6: suites verdes. T3/T5/T7 encontraron fallos que esas suites no detectan; T4 distingue contrato real de mock completo. |
| **B1. Conocimiento de rutas, cuotas y capacidades** | **PARCIALMENTE CORREGIDO** | Se corrigieron `/equipos-maquinaria`, cuota configurable y bloqueo de restore; el filtro de módulos consulta permisos efectivos (`knowledge_base.py:239-245`). Pero los procedimientos (`:280-288`) solo filtran rol, ignorando `proc['permisos']`: con ADMINISTRADOR_EMPRESA y permisos vacíos, una consulta de aprobación de compra devuelve **dos procedimientos**. Los campos de permiso de algunos módulos siguen sin corresponder al dominio que describen; no se consulta la habilitación comercial actual al presentar capacidades. | T1: dos tests B1 positivos; T7: función real con permisos vacíos y revisión del filtro de procedimientos. |
| **B2. ID de incidencia perdido en la respuesta** | **CORREGIDO** | `assistant_operations.py:255-261` extrae `resp['id_incidencia']` del nivel superior y lo conserva en `resultado`. Se verificó **501** usando `incidencia_services.registrar` real, no un mock del servicio. Esta clasificación corresponde al mapeo del resultado; la creación normal continúa bloqueada por el error de Context descrito en A5. | T1: test B2 con contrato de respuesta alineado; T4: dominio real/repositorios sustituidos y contexto ampliado para aislar la etapa posterior. |

## Regresiones introducidas por las correcciones

### R1. Contrato inexistente de Context en operaciones — bloqueante

`backend/app/services/reportes/authorization.py:9-15` no declara `obras_autorizadas`; tampoco lo construye `context()`. Las referencias nuevas de `assistant_operations.py:71,88,214,223` causan AttributeError cuando el actor sí tiene el permiso exigido. Las pruebas pasan porque sus MagicMock tienen ese atributo agregado manualmente.

Debe resolverse contra el contrato real de autorización y el conjunto de obras obtenido de los repositorios, con denegación si el conjunto autorizado está vacío. Agregar simplemente un atributo opcional y conservar `if ctx.obras_autorizadas` podría introducir otro bypass por lista vacía. No se implementó ninguna corrección en esta validación.

### R2. Continuación de conversación llama un repositorio inexistente — bloqueante

`assistant_service.py:263` llama a `reportes_repos.conversation_request`, que no está definido. La excepción fue reproducida directamente y mediante HTTP aislado: una conversación válida pasa el control de pertenencia y devuelve 500. La versión auditada originalmente tomaba la solicitud del registro de conversación ya recuperado.

Debe restaurarse un acceso válido a la solicitud persistida y su autorización vigente. La prueba requerida es una segunda pregunta con UUID válido y datos autorizados, además del rechazo de un UUID ajeno; comprobar solo el rechazo de la conversación ajena deja sin cubrir el camino afectado.

### R3. Filtro nuevo de trabajador incompatible con PostgreSQL — bloqueante para ese diagnóstico

El EXPLAIN real del SQL de ELECTRICO falló con **42703: column i.id_usuario does not exist**. La columna de autor utilizada por el dominio vigente es `id_usuario_registro`. El test nuevo valida textualmente el nombre incorrecto y lo trata como evidencia de aislamiento. Debe comprobarse SQL y restricciones reales de filas, no solo una cadena generada.

### R4. Desaparición de agotados por filtro semánticamente incorrecto — bloqueante para aceptar el diagnóstico

La llamada nueva compila, pero no solicita un estado emitido por la función actual. La definición leída directamente de PostgreSQL contiene:

```text
WHEN COALESCE(SUM(ma.cantidad_actual), 0.00) <= 0 THEN 'SIN_STOCK'
...
OR bm.estado_stock = p_estado_stock
```

El código corregido pasa `AGOTADO`. Un EXPLAIN satisfactorio no detecta este error de negocio; el mock del test retorna material agotado independientemente del filtro. Debe usarse el estado real y verificarse un caso positivo de stock cero en un entorno de pruebas designado.

### R5. Contrato del planificador menos estricto

La corrección reemplazó el Literal y las listas acotadas de `ReadPlan` por strings/listas sin esos límites y retiró `extra='forbid'`. Se comprobó aceptación de cinco solicitudes y descarte silencioso de un campo extra `sql`. Los nombres de operación y fuentes mantienen validaciones posteriores; no se demostró ejecución de SQL del modelo. Es una regresión de validación que debe restablecerse y cubrirse al cerrar M1/M8.

## Resultados de ejecución relevantes

Estas salidas usan únicamente actores e identificadores sintéticos y persistencia sustituida, salvo el bloque de PostgreSQL expresamente indicado:

```text
A1_REVOKED_RBAC                         403; ticket PENDIENTE
A1_SUSPENDED_PLAN                       403
A1_DISABLED_MATERIAL_MODULE             200; servicio real alcanzó crear; id_material 302
A2_FOREIGN_RESOURCE                     403
A2_NEW_TOKEN_NEW_COMPANY                 403 al confirmar
A2_CANCEL_NEW_COMPANY_SAME_USER          200
A5_REAL_CONTEXT_PROPOSE crear_incidencia AttributeError: Context sin obras_autorizadas
A5_REAL_CONTEXT_PROPOSE crear_orden_trabajo AttributeError: Context sin obras_autorizadas
A5_REAL_CONTEXT_CONFIRM ambas           500
REGRESSION_VALID_CONVERSATION            500
REGRESSION_CONVERSATION_EXCEPTION        AttributeError: repositorio sin conversation_request
M3_FOREIGN_USER                          403; ticket preservado
M4_CANCEL                               200; confirmar después 404
M4_EXPIRED                              404
M4_REPLAY_RESULT                        404
M4_SECOND_PROCESS                       404; primer proceso aún conserva ticket
A3_NO_INVENTORY_PERMISSION               fuentes_consultadas=['inventario']
A3_REVOKED_BEFORE_RETURN_LEAK            True
M5_POST_CREATE_FAILURE                  500; ticket PENDIENTE
M5_RETRY_CREATES_AGAIN                   2 llamadas a crear, id_incidencia 602
```

La reproducción M5 se hace después de aislar R1 con un contexto ampliado exclusivo del test; no debe leerse como una ejecución completa saludable del endpoint. Las ejecuciones de tres dominios en T4 devolvieron incidencia 501, OT 884 y material 302. No hubo inserciones reales.

PostgreSQL real, con `transaction_read_only=on` comprobado:

```text
Reportes: 82 EXPLAIN correctos
Diagnóstico ADMINISTRADOR_EMPRESA: incidencias OK, OT OK, inventario OK, RFI OK
Diagnóstico ELECTRICO: incidencias ERROR 42703; OT OK
Fuentes personal_obra, empresas, consultas_tecnicas: columnas válidas y EXPLAIN OK
Función oficial de inventario: estado de stock cero SIN_STOCK; filtro por igualdad
```

## Regresión ejecutada y límites de aceptación

Desde `backend` se ejecutaron las mismas suites relacionadas con las causas originales, mediante `pytest.main` y bloqueo preventivo de la conexión PostgreSQL real:

```text
pytest -q -p no:cacheprovider tests/test_asistente_administrativo.py tests/test_assistant_queries.py tests/test_reportes.py tests/test_reportes_api.py tests/test_reportes_personalizacion.py tests/test_security_rules.py tests/test_suscripcion_restricciones.py tests/test_configuracion_planes.py tests/test_control_costos_services.py
pytest -q -p no:cacheprovider tests/test_consulta_tecnica.py tests/test_material_services.py tests/test_incidencia_services.py tests/test_incidencia_authorization.py tests/test_incidencia_atencion.py tests/test_incidencia_candidatos.py tests/test_incidencia_registro_movil.py tests/test_incidencia_validacion_bd.py tests/test_ot_afectacion.py tests/test_obra_personal.py
python tests/reportes_sql_readonly_check.py
```

Desde `frontend`: `npm.cmd run test:reportes`. No se usó un build como sustituto de verificar comportamiento. Las comprobaciones efímeras T3/T4/T6/T7 no agregaron archivos de código ni tests al repositorio.

Se mantienen referencias de Reportes, exportación, proveedores, cuota y voz; las suites de regresión relacionadas pasan con los límites anteriores. No se verificó disponibilidad real de DeepSeek/Gemini, consumo de cuota concurrente en PostgreSQL, correos, worker, reconocimiento de voz real, Flutter o despliegue. Tampoco se verificó compatibilidad del endpoint aislado con el middleware de mantenimiento en ejecución real. No se cambió ni liberó mantenimiento.

No se probaron creación/rollback/idempotencia con escrituras reales ni dos tenants con datos de negocio en PostgreSQL, porque la conexión configurada no está designada como base de pruebas. La autorización anterior permite inspección de solo lectura; no transforma esa base en un destino autorizado de pruebas de escritura. La presencia de objetos tampoco acredita una migración aplicada concreta o sus grants.

## Condiciones pendientes para el cierre

1. Resolver R1/R2 y restituir el funcionamiento normal de propuesta, confirmación y segunda pregunta con el contexto/repositorio reales.
2. Revalidar módulo/capacidades de destino al confirmar y completar las restricciones de diagnóstico: permiso de inventario, fila correcta de trabajador y reautorización antes de entregar datos.
3. Corregir el estado de inventario y verificar una alerta positiva; conservar un contrato estricto del planificador y pedir aclaración para una obra desconocida aunque exista contexto de navegación.
4. Definir transacción de dominio y estado persistente de operación con recuperación de resultado/idempotencia; no volver a PENDIENTE ciegamente tras un posible commit. Completar vinculación de empresa al cancelar.
5. Añadir regresiones con Context real y servicios de dominio reales, limitando mocks a persistencia/proveedores; luego ejecutar aceptación en PostgreSQL de pruebas designado, dos tenants y fallos controlados, y en navegador para los flujos nuevos.

El avance respecto a la auditoría original es comprobable, especialmente en propietario del ticket, cancelación, vistas previas, mapeo del ID y descarte de respuestas tardías. **Los bloqueantes funcionales y de seguridad restantes impiden aprobar el cierre del CU29.**
