# Reportes personalizables y asistente único

## Análisis previo

Se revisaron la arquitectura general, Reportes, operación, autorización, inventario SQL y rutinas. El chat ya tiene una sola instancia en el shell, pero separa dos modos que borran la conversación y llaman endpoints diferentes. Los reportes solo aceptan fechas en salidas/incidencias y carecen de opciones de presentación. El asistente solo explica resúmenes y no recibe filas, por lo que no puede identificar obras por sus métricas.

Se conserva `routes → services → repos`. Se añade un coordinador de consultas de solo lectura con selección de capacidades autorizadas (reportes y CRM), independiente del proveedor. El modelo selecciona contratos del catálogo y explica resultados; no escribe SQL ni tiene acceso directo a la base. Texto y voz comparten entrada y conversación, y los temas sirven para filtrar el historial visible, sin cambiar el procesamiento ni borrar mensajes. El endpoint CRM permanece compatible con consumidores anteriores.

## Contratos y datos

`ReportRequest.presentacion` será opcional, con valores por defecto compatibles: título, orden de columnas, ordenación y orientación PDF. Se guarda en el snapshot y programación; el mismo exportador sirve consulta, descarga y envío. Ocultar columnas es presentación, no autorización: las filas autorizadas completas se conservan para la intersección emisor/receptor y los resúmenes. Se valida toda columna contra el esquema del resultado, incluyendo resultados vacíos.

Fechas inclusivas según el dato real: creación de estimación, asignación a obra, inicio de OT, registro de avance, salida de almacén, creación de incidencia y fecha del costo ejecutado. Stock, estado de unidades y comparativo de línea base siguen siendo estados actuales; la interfaz explica esta diferencia. No se simula historia donde no existe.

Una nueva capacidad de saldo comercial cruza ventas CRM y costos CU17 por obra y moneda. No hay registros de cobros; monto pactado no acredita ingreso realizado. Las asociaciones VENDIDO/ENTREGADO se deduplican por unidad (última asociación autorizada); costos REGISTRADO de la línea base activa. Costos ausentes o ventas sin monto impiden concluir saldo. Nunca se suman monedas ni versiones ni se mezcla el modelo legacy. La consulta exige permisos de costos y CRM, además de Reportes, y respeta obras autorizadas.

## Validación prevista

Pruebas de autorización, columnas/ordenación, límites y compatibilidad, exportaciones, rangos inclusivos, saldo insuficiente, selección de capacidades, continuidad de conversación y cambio de tenant. Comprobar consultas nuevas con EXPLAIN de solo lectura en el esquema configurado y compilar Angular. No iniciar backend/worker en segundo plano, aplicar migraciones ni enviar correos. No se necesitan cambios de esquema ni cambios en Flutter: todos los campos nuevos son opcionales.

## Implementación y resultados

Implementado en backend y web. Se añadieron contratos `Presentation` y `AssistantRequest` opcionales, esquemas estables de columnas, personalización de snapshots/exportadores y preservación del formato en períodos de programaciones. El catálogo declara la fecha aplicable a cada reporte. La pantalla ofrece períodos rápidos, rangos abiertos, título, orientación, selección/orden de columnas y ordenación del detalle. GENERANDO se reconoce en la consulta de trabajos pendientes.

El coordinador `ai/assistant_service.py` reutiliza `reportes_services.create` y el constructor CRM existente, con autorización antes y después de leer y antes de devolver resultados. La rama CRM conserva esa excepción histórica de SQL en `ContextBuilder`; no se añadió SQL en el coordinador. Proveedor intercambiable, plan Pydantic sin SQL, catálogo permitido y revalidación por recurso. La selección de obra usa el mismo endpoint con una solicitud tipada y actualiza el contexto conversacional. Las preguntas anteriores se conservan como referencia de lenguaje; las respuestas antiguas y filas no se reutilizan como permisos ni como evidencia vigente.

Para explicar reportes generales se envían resúmenes completos y hasta 100 filas autorizadas, marcando explícitamente si el detalle es incompleto. No se presume que la muestra permite demostrar ausencia o responder cualquier agregado. El saldo financiero y los totales por período se calculan en el backend con Decimal; el saldo responde sin LLM. Montos CRM sin moneda propia, ventas sin importe y costos ausentes se explican; no se afirma una utilidad real. Los nombres y saldos se muestran según el ámbito actual, sin sumar monedas.

La burbuja y cabecera comparten un solo endpoint. CRM abre la misma conversación. Se retiraron modos de consulta; el selector de historial filtra mensajes por tema sin perder la conversación. El historial visible permanece en memoria durante la sesión del shell; todavía no hay un navegador de conversaciones antiguas tras refrescar. Permisos y cambio de empresa siguen invalidando contexto y respuestas tardías. No se añadieron herramientas que modifiquen registros por lenguaje natural.

Comprobaciones finales ejecutadas:

- `python -m unittest discover -s tests -p test_reportes*.py`: **54 pruebas correctas**; contratos, fuentes/permisos, contexto por tenant, rangos inclusivos, Decimal por moneda, exportación, proveedor caído y programación.
- `npm.cmd run test:reportes`: **21 pruebas correctas**; personalización en consulta/programación, rango abierto, columnas vacías, continuidad entre páginas, historial por tema, empresa activa y respuestas tardías.
- `python tests/reportes_sql_readonly_check.py`: **82 variantes validadas** por EXPLAIN sin ANALYZE, incluyendo fechas y fuentes nuevas, contra la base configurada. Sin lectura de filas de negocio ni escrituras.
- `npm.cmd run build`: compilación de producción correcta. Permanecen avisos de presupuestos CSS existentes/fuentes externas y Leaflet CommonJS; estilos nuevos de personalización y chat no exceden el aviso de 4 kB.
- `git diff --check`: sin errores de whitespace en archivos seguidos; avisos habituales LF/CRLF del entorno Windows.

No se iniciaron backend/worker en segundo plano, no se aplicaron migraciones ni se enviaron correos. No se invocó el proveedor IA real ni se validó voz en un dispositivo; las pruebas de transporte usan dobles. No se volvió a ejecutar el script de navegador en esta iteración. Flutter no se modificó y los contratos anteriores siguen admitidos mediante campos opcionales.
