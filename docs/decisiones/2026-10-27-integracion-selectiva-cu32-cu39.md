# Integración selectiva CU32/CU39 en eddy

Fecha: 2026-10-27, America/La_Paz. Solicitud: incorporar gastos operativos finales y cronogramas únicamente en backend/frontend, dando prioridad a eddy. Mobile queda excluido de cualquier modificación.

## Fuentes y límites

Base de trabajo: eddy `28b52be`. Fuentes actualizadas mediante fetch: origin/anghy `89b2346` (CU39, últimos cambios backend/web en `8549ee4`) y origin/Grover `32a8981` (CU32). No se hará merge completo ni sustitución de archivos compartidos. Se conservarán los cambios de eddy de contexto operativo, caché/cancelación de lecturas, Reportes/IA, CU23, pagos, suscripciones y módulos restantes. Las bajas ya presentes en backend/.pytest_tmp son ajenas a esta integración y no se restaurarán ni incorporarán como parte de ella.

## Capas, contratos y persistencia

CU39 aporta repositorio, servicio, contratos Pydantic, rutas, errores, migración incremental, preflight, pruebas y pantalla/servicio Angular. Usa empresa autorizada del JWT y recurso obra; permisos de cronograma independientes de la navegación. Se agregarán solo registro del router, clasificación SaaS de la ruta /api/obras, permisos web y accesos. Las tablas nuevas y grants se preparan, sin aplicar a producción.

CU32 amplía el CU17 actual: resumen opcional final=true y finalización de obra con cálculo en una conexión compartida. Requiere además salarios, jornadas y cierre de mano de obra incorporados por el último commit de Grover; sin ellos el cálculo final omitiría una fuente. Se importarán estos archivos nuevos, el SQL y sus pruebas. En los repositorios/servicios de costos y obras se incorporarán únicamente conexiones opcionales, el enlace de finalización y la protección contra doble contabilización. Modificar_obras no concederá lectura de importes; esta continúa exigiendo Visualizar_control_costos.

La pantalla de control de costos de Grover sustituye la coordinación de contexto de eddy. Para preservar eddy, sus controles actuales no se reemplazarán: la interfaz de cierre y mano de obra se aislará en una pantalla CU32 con sus mismos contratos backend y accesos desde obra/control de costos. Se reutilizarán estilos/componentes actuales. No se importará el alias npm dev ni cambios ajenos al funcionamiento de los dos CU.

No se presupone que las migraciones estén instaladas. Se verificará compatibilidad de esquema mediante lecturas/metadatos y, cuando sea posible, PostgreSQL local desechable con datos sintéticos. No habrá migraciones ni escrituras en la base configurada. La ausencia del esquema nuevo debe dar un error de instalación del CU, preservando el flujo previo de costos cuando aún no está habilitado el cierre nuevo.

## Validación prevista

Pruebas backend de las ramas más regresión de costos, obras, Reportes y política SaaS de eddy; pruebas Angular de cronogramas y contratos CU32; build para compatibilidad de compilación, sin tratarlo como aceptación funcional. Comprobar selección de empresa/obra, respuestas tardías, permisos por acción, rollback de finalización, dependencias cíclicas y versiones optimistas. Verificar al finalizar que mobile no presenta diferencias.

## Resultado

Integración aplicada en el árbol de trabajo de eddy, sin merge completo, commit ni push. Mobile no presenta diferencias. El trabajo previo del CU29 se conserva tal como está en eddy; no se amplía ni se declara terminado dentro de esta integración.

| Grupo | Archivos incorporados o ajustes indispensables |
| --- | --- |
| CU39 backend | `cronograma_repos.py`, `cronograma_services.py`, `cronograma_routes.py`, `schemas/cronograma_schema.py`, `utils/cronograma_errors.py`; registro aditivo en `app/__init__.py` y clasificación `/api/obras` como módulo SaaS obras. |
| CU39 web | Página `pages/cronogramas`, `cronograma.service.ts`, permisos Auth, rutas con guard de salida, entradas de menú y acceso desde detalle de obra. |
| CU32 backend | `gastos_operativos_services.py`, `trabajadores_costos_services.py`, `trabajadores_costos_repos.py`; ampliaciones limitadas de `control_costos_*` y de la finalización en `obra_*`. |
| CU32 web | Contratos/métodos aditivos en `control-costos.service.ts`; nueva página `pages/gastos-operativos`, accesos en menú, detalle de obra y cabecera de Control de costos. El resto de la pantalla de costos de eddy no se sustituyó. |
| Instalación | Los dos SQL de las ramas y `manage_cronogramas.py`, que permite inspección `--check` en solo lectura. |
| Validación | Pruebas específicas de las ramas, prueba de regresión de doble contabilización en CU17, nuevas pruebas web de CU32/contexto y respuesta tardía de CU39, ejecutor y 11 pruebas PostgreSQL de integración. Dos scripts npm y tsconfig específicos. |

La adaptación adicional protege el resultado de escrituras de cronogramas frente a cambios de ruta/empresa. La página CU32 cancela GET anteriores y descarta resultados POST de otro contexto; mantiene la restricción de empresa del JWT existente en costos. La ausencia del esquema CU32 devuelve 503 en las funciones nuevas. Registrar MANO_OBRA por CU17 continúa funcionando sin la tabla de cierres; solo se tolera su ausencia en una conexión propia, nunca dentro de una transacción compartida abortada.

La finalización requiere línea base activa de una estimación aprobada. Estado, cierre de jornadas y cálculo se confirman juntos; si falla la validación se revierte el estado. El PATCH conserva su contrato y no revela importes al permiso Modificar_obras. El resumen final sigue el diseño de Grover: consulta recalculable de los costos registrados de CU17 más salarios congelados en el cierre de jornadas; no constituye un cierre contable inmutable ni acredita pagos. No cambia los reportes CU17.

## Resultados de validación

| Comprobación ejecutada | Resultado y alcance |
| --- | --- |
| Pytest de costos, gastos finales, trabajadores, cronogramas, personal de obra, seguridad, planes y Reportes/API | **152 passed, 14 skipped**, 25 subtests. Se bloqueó `psycopg2.connect` a bases externas durante estas suites. Las pruebas usan mocks; no prueban persistencia por sí mismas. Los opt-in de PostgreSQL originales se omiten sin su destino explícito. |
| `python tests/cu32_cu39_postgres_check.py` | **11 passed**, PostgreSQL 17 local desechable con esquema previo sin datos de negocio y actores sintéticos. No se simularon servicios, repositorios, SQL, funciones de obra, JWT, permisos ni suscripciones. Se cambió únicamente la configuración hacia el destino local verificado. |
| `npm.cmd run test:cronogramas` | **10 passed**. Renderizado y acciones, contratos HTTP, planificación de supervisor, conflictos, dependencias, hitos, cancelación GET y descarte de respuesta POST de una ruta anterior. Backend HTTP simulado. |
| `npm.cmd run test:gastos-finales` | **10 passed**. Contratos de servicio, resumen del servidor, aislamiento visual y cancelación por empresa, obra desconocida, salario/jornada, autorización de controles y reintento. Backend HTTP simulado. |
| `npm.cmd run test:reportes` | **25 passed**, regresión web de Reportes y asistente. |
| `npm.cmd run test:navigation` | **19 passed, 1 failed**. Falla existente `Nuevo y Gestión tienen destinos diferentes...`: lee `sections` antes de inicializar el componente; `items.find('nuevo')` es undefined. Se repitió temporalmente con `navegacion.ts` de HEAD de eddy y dio el mismo fallo; el archivo se restauró íntegramente tras la comprobación. No se cambió el componente ni esa prueba ajena. |
| `npm.cmd run build` | Compilación de producción correcta. Se requirió acceso de red para las fuentes Google ya existentes; permanecen advertencias de presupuestos CSS y Leaflet CommonJS. No equivale a una prueba de navegador. |
| Git | Rama eddy; `git diff --check` correcto en archivos modificados, `git diff --name-only -- mobile` vacío. No se incluyeron los borrados previos de evidencias temporales. |

Las pruebas PostgreSQL ejercen: salarios y jornadas mediante servicio y endpoints; reintento de jornada sin duplicación; cálculo final 50 de material + 100 de mano de obra; finalización reiterada sin duplicar cierres; rechazo de jornadas tras finalizar; rollback de estado/cierres sin línea base y ante combinación manual/calculada; permisos, tenant, suspensión SaaS y validación HTTP; CU17 sin tabla CU32; CRUD/versiones/retrasos/auditoría de cronogramas; dos actualizaciones simultáneas con resultados 200/409; fallo SQL mediante trigger sintético con rollback; supervisor limitado a planificar; 503 sin esquema CU39; registro de rutas en la fábrica real de la aplicación.

No se validaron interacción manual en navegador, despliegue remoto, privilegios del usuario de producción sobre las tablas nuevas ni instalación de sus migraciones. Tampoco se probó mobile, que queda fuera del alcance.

## Requisitos para habilitación en un entorno designado

**Migraciones preparadas e instaladas únicamente en la base local de pruebas; no aplicadas por este trabajo a la base configurada ni a producción.** Se debe comprobar antes el esquema y permisos efectivos del destino.

- CU39: `backend/database/20261025_cu39_cronogramas.sql`, tres tablas, índices y cuatro permisos con asignaciones a roles. Requiere el módulo existente `Modulo_obras`. `python manage_cronogramas.py --check` inspecciona columnas, restricciones, permisos y privilegios sin escribir; la aplicación mediante `--apply --database <destino>` es una operación posterior explícita.
- CU32: `backend/database/migration_cu32_mano_obra_trabajadores.sql`, salarios, jornadas y cierre de mano de obra. Requiere el modelo actual de obras/usuarios/CU17; verificar permisos de tablas y secuencias para el usuario de aplicación. Sin esta instalación, las nuevas acciones devuelven 503 y la finalización nueva no se confirma parcialmente.
- Tras instalar permisos, renovar la sesión y considerar el TTL de 120 segundos de la caché RBAC existente del backend.

Reproducción local: el ejecutor nuevo reutiliza el destino ya preparado por `tests/cu29_postgres_check.py --prepare` (copia solo DDL, no datos). Antes de cualquier escritura exige localhost, nombre `cu29_test_*` y marca de clúster `obratec.cu29_test=disposable`; sin configuración las pruebas se omiten. No ejecutar estos fixtures contra una base de negocio. Las migraciones se aplican dos veces en la prueba para comprobar instalación idempotente.
