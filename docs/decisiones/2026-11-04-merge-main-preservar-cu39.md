# Merge origin/main conservando CU39

## Alcance y contexto
Resolver el merge ya iniciado por el usuario, sin descartar sus diagramas y documentos sin seguimiento. Se conservan los módulos nuevos de main y las funcionalidades de cronogramas web/móvil.

## Capas y contratos
CU39 mantiene routes → services → repos → PostgreSQL. El contrato Pydantic y la serialización HTTP de la rama local conservan validación estricta: no inventar inicio/fin real, nombres ni avances, ni ignorar campos ajenos. Servicios y repositorio coinciden entre ambas ramas. Se incorpora de main la protección de respuestas tardías por contexto en Angular y su prueba. La fábrica registra cronogramas, consultas técnicas y pagos sin duplicar routers.

## Tenant y permisos
Se conservan empresa autorizada del JWT, permisos por acción, DAG, versiones optimistas y transacciones de CU39. El menú móvil nuevo conserva las acciones de main y añade acceso a Cronogramas condicionado a Visualizar_cronograma. Se conserva la dirección LAN local configurada y el destino cloud por defecto recibido de main.

## Documentación e instalación
Unir las referencias de arquitectura de ambas ramas, diferenciando la instalación histórica autorizada de CU39 en obras de la integración posterior de main probada en destino desechable. No se ejecutan migraciones ni se acredita el estado actual de una base por documentos históricos.

## Validación prevista
Pruebas unitarias CU39 backend sin conexiones externas, pruebas Angular de cronogramas y contratos nuevos, compilación Angular, pruebas/análisis Flutter y verificación de ausencia de conflictos. Completar el merge si las comprobaciones lo permiten; sin push. Los diagramas/documentos ajenos al índice permanecerán sin incorporar al commit.

## Conflictos semánticos del merge automático
La compilación detectó métodos puedeVerCronogramas/abrirCronogramas duplicados en detalle de obra; también se detectaron dos registros de cada ruta CU39. Se conservará una única implementación y un registro de cada ruta con permisos y guard de salida. Esto evita pérdida de compilación y rutas ambiguas aun en archivos que Git fusionó sin conflicto textual.

## Resultado y validación (05/11/2026)

- Nueve conflictos textuales resueltos; eliminados también los duplicados de rutas y métodos que el merge automático había introducido. Contrato Pydantic, serialización HTTP, servicios, repositorio y pantalla/servicio móvil CU39 coinciden con HEAD local previo.
- Backend CU39: 13 pruebas unitarias correctas y 8 de persistencia omitidas por no designar un clúster de pruebas. Se bloqueó psycopg2.connect durante las pruebas. No acredita persistencia actual ni instalación en una base.
- Regresión backend de gastos finales, trabajadores y consultas técnicas: 47 pruebas correctas, con conexiones externas bloqueadas. La fábrica real genera OpenAPI con los métodos de cronogramas, planificación, pagos y consultas técnicas. La primera comprobación por APIRoute directo se sustituyó por OpenAPI, que expande los routers incluidos de la versión instalada.
- Angular: 10 pruebas CU39 correctas, 10 de gastos finales correctas y build completo en configuración development correcto. Las pruebas usan HTTP simulado; no equivalen a navegación manual ni despliegue. El primer intento de Vitest falló por permisos sobre TEMP; se repitió correctamente con TEMP/TMP en .angular/merge-temp.
- Flutter: 4 pruebas CU39 correctas. Dart analyze de detalle de proyecto, pantalla/servicio de cronogramas, configuración y AuthProvider: No issues found. El SDK requirió acceso a su caché fuera del sandbox.
- XML/diagramas y documentos locales sin seguimiento no se añadieron al índice ni se sobrescribieron. Sin migraciones, envíos externos ni push.
- Sin archivos unmerged; verificación de sintaxis Python y unicidad de rutas/métodos correcta. git diff --cached --check pasa para los archivos resueltos. El diff completo contiene avisos de espacios/CRLF ya recibidos de main en otros módulos, que no se reformataron por estar fuera del conflicto.
