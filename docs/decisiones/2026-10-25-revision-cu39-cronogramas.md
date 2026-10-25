# Revisión CU39: cronogramas y planificación de obra

## Solicitud y alcance
Verificar la implementación existente frente a HU131–HU134 y explicar su ausencia en la interfaz Web/Móvil. Revisión de código y pruebas aisladas; no se modifica implementación ni se aplican migraciones en esta revisión.

## Contexto y archivos revisados
Se consultaron ARQUITECTURA_Y_PATRONES.md, ARQUITECTURA_BASE_DATOS.md, inventario y rutinas enlazados (apartados de roles, permisos y obras), la nota de arranque, app.routes.ts, navegación del shell, detalle de proyecto, AuthService, roleGuard, entornos, componente/plantilla/servicio de cronogramas, fábrica FastAPI, rutas/servicios/repositorio/schema CU39 y wrapper PostgreSQL. Se buscaron referencias a cronogramas en mobile/lib, backend/database y pruebas existentes; no se encontraron implementaciones móviles, migraciones CU39 ni pruebas específicas.

## Resultado por historia

| Historia | Estado comprobado en el repositorio |
| --- | --- |
| HU131: crear y actualizar | Esqueleto de API y esquema de cabecera. Web solo muestra un listado; no hay formularios ni métodos cliente de escritura. El repositorio no confirma sus escrituras. Sin implementación móvil localizada. |
| HU132: hitos, dependencias y fechas | Sin modelo de actividades/hitos/dependencias, endpoints ni UI correspondientes. Solo hay fechas generales de cabecera, sin validación de orden temporal. |
| HU133: consulta por período | Existe listado básico, pero es inaccesible por navegación y llama a endpoints incorrectos, sin obra ni filtros de período. No hay consulta de actividades programadas. |
| HU134: identificar retrasos | El repositorio retorna [] incondicionalmente. La ruta está además detrás del parámetro dinámico de detalle. No hay cálculo, presentación ni comparación con ejecución real. |

CU39 no está completo ni integrado funcionalmente.

## Hallazgos y prioridades

### P1: autorización por recurso ausente
Todos los servicios reciben token_data pero lo ignoran. El repositorio filtra únicamente por id_obra proporcionado en URL y no comprueba empresa ni asignación del actor. exigir_permiso comprueba capacidad por rol, no pertenencia de obra. Si el permiso está asignado, falta una barrera de aplicación contra acceso entre empresas tanto para lectura como escritura. ADMINISTRADOR_EMPRESA no debe tratarse como administrador global. No se demuestra explotación contra una base real en esta revisión.

Evidencia: backend/app/services/cronograma_services.py:10–75; backend/app/repos/cronograma_repos.py; backend/app/utils/security.py, exigir_permiso.

### P1: escrituras revertidas y éxito falso
crear_cronograma, actualizar_cronograma y eliminar_cronograma llaman execute_query sin commit=True y cierran con close_connection() cuyo valor por defecto es rollback. Pueden devolver un ID/éxito aunque la operación no persista. UPDATE y DELETE devuelven True sin comprobar rowcount: también anuncian éxito cuando no existe el recurso.

Evidencia: backend/app/repos/cronograma_repos.py:40–141 y backend/app/classes/postgres.py.

### P1: integración de consulta rota
La ruta Angular /proyectos/:id/cronogramas existe, pero ningún enlace o pestaña del detalle ni registro de navegación permite descubrirla. El componente no lee :id y llama listarCronogramas() sin argumento. El servicio envía GET /api/cronogramas/; con argumento enviaría /api/proyectos/{id}/cronogramas/. El backend solo registra /api/obras/{id_obra}/cronogramas/. Ambas variantes cliente son incompatibles.

Evidencia: frontend/src/app/app.routes.ts:168; pages/cronogramas/cronogramas.ts:31; services/cronograma.service.ts:31–35; layouts/admin-layout/navegacion.ts; pages/proyectos/detalle/proyecto-detalle.html; backend/app/routes/cronograma_routes.py:6.

### P1: funcionalidades de planificación ausentes
No hay actividades, hitos, dependencias, formularios, estados de ejecución, consulta por período ni cálculo de retraso. consultar_retrasos retorna una lista vacía sin acceder a datos. GET /retrasos se registra después de GET /{id_cronograma}: el enrutamiento consume la cadena como ID y la validación entera impide llegar al handler esperado (422 bajo el comportamiento estándar de FastAPI).

Evidencia: backend/app/repos/cronograma_repos.py:143–149; backend/app/routes/cronograma_routes.py:29,56; schema y UI CU39.

### P2: permisos y persistencia no acreditados
La ruta exige Visualizar_cronograma; el fallback Angular no registra ese permiso para Jefe de Obra/Supervisor, ni Registrar_cronograma/Modificar_cronograma. Los permisos explícitos que pueda traer una sesión dependen de BD y no fueron comprobados. El administrador global tiene bypass; no cabe afirmar que todos los usuarios estén bloqueados. No se localizó migración CU39 ni t_cronograma en el inventario histórico. Esto NO demuestra que la tabla o los permisos no existan actualmente: la instalación real queda pendiente de inspección de catálogos de solo lectura. El rol SUPERVISOR_OBRA aparece en mapas locales, pero su equivalencia con usuarios/roles actuales también requiere verificación.

### P2: validación y errores incompletos
El schema admite nombre vacío y fecha_fin anterior a fecha_inicio. PUT no permite borrar campos opcionales con null porque el repositorio ignora None. Se exponen excepciones internas mediante str(exc), y errores técnicos se convierten en 400. No hay auditoría implementada; ip se recibe pero no se utiliza. orm_mode genera advertencia de compatibilidad con Pydantic 2.

## Patrones, capas, contratos y tenant
Se mantienen nominalmente routes → services → repos → PostgreSQL y componente → servicio HTTP, pero falta la responsabilidad de autorización por recurso en servicios y coherencia de contratos entre clientes y API. La corrección debe resolver empresa autorizada mediante JWT y obra real, comprobar pertenencia y reglas de actor, reservar excepciones para ADMINISTRADOR global, y preservar las barreras de suscripciones/mantenimiento vigentes. La empresa seleccionada en UI no concede acceso.

No se cambió arquitectura, contrato ni persistencia durante esta revisión; no corresponde presentar un simple enlace como terminación de CU39.

## Verificaciones realizadas y límites
Se ejecutaron funciones reales aisladas mediante AST de Python, sustituyendo imports de infraestructura por dobles en memoria, sin cargar la fábrica de aplicación ni abrir conexiones:

- Las tres escrituras omitieron commit y cerraron con rollback por defecto; crear devolvió ID, actualizar/eliminar True con rowcount simulado 0.
- listar_cronogramas devolvió el mismo resultado para JWT de dos empresas diferentes y contexto vacío: token_data ignorado. Esto prueba ausencia de validación en el servicio, no permisos efectivos del servidor.
- consultar_retrasos devolvió [] incondicionalmente.
- Se instanció el schema Pydantic con nombre vacío y fechas invertidas y fue aceptado.
- Se verificó por AST el orden GET: /, /{id_cronograma}, /retrasos. No se ejecutó una petición FastAPI para el 422, pues FastAPI no está instalado en el runtime de revisión.
- Búsqueda de navegación, móvil, migraciones y tests; revisión estática de endpoints y permisos.

La corrección anterior comprobó build de producción y servidor de desarrollo HTTP 200, lo que solo acredita compilación y entrega del frontend. Esta revisión no verifica navegación autenticada, disponibilidad backend, tabla real, grants, permisos persistidos ni datos de negocio. No se ejecutaron migraciones, pruebas contra BD ni envíos externos.

## Secuencia de corrección propuesta
1. Inspeccionar catálogos actuales de tabla/columnas/restricciones/FK/roles/grants y permisos CU39 en transacción explícita de solo lectura; identificar el actor Supervisor real.
2. Definir modelo de actividades/hitos/dependencias y ejecución, invariantes temporales y ausencia de ciclos; migración incremental preparada separada de su aplicación a entorno designado.
3. Completar autorización por obra/tenant, transacciones, comprobación de filas afectadas, validación, auditoría y errores; registrar /retrasos antes de /{id_cronograma}. Probar aislamiento y persistencia con dobles y entorno de pruebas designado.
4. Alinear endpoints y contexto de obra en Angular/Flutter; integrar acceso visible desde detalle, permisos y CRUD por actor; incluir actividades, períodos y retrasos basados en datos reales.
5. Validar las cuatro historias en ambos clientes con Jefe/Supervisor, empresa ajena, contexto incompleto y administrador global; actualizar referencias de arquitectura cuando se implemente el modelo definitivo.
