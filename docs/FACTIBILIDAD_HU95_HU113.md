# Factibilidad de HU95–HU113

Fecha: 2026-10-04. Alcance: evaluación, sin implementar las HU ni modificar la base.

## 1. Evidencia y criterio

Se consultaron `AGENTS.md`, [la arquitectura general](ARQUITECTURA_Y_PATRONES.md), [la arquitectura de PostgreSQL](ARQUITECTURA_BASE_DATOS.md), [el inventario real](BASE_DATOS_INVENTARIO.md) y los servicios/repositorios/rutas actuales de costos, estimaciones, inventario, personal, OT, maquinaria, unidades e IA.

La base fue inspeccionada en el análisis anterior de esta sesión. Para esta evaluación se reutilizó esa fotografía; no se abrió una conexión nueva ni se contaron filas comerciales. La existencia de tablas/campos demuestra capacidad estructural, no cantidad, calidad o cobertura histórica de datos.

Se proporcionaron títulos de historias, sin criterios de aceptación. Por ello, «viable ahora» significa que hay una base suficiente para desarrollar una versión inicial con un alcance explícito; no significa que la HU esté terminada o que cualquier interpretación de su título sea realizable con los datos actuales.

Resultado: **15 HU viables para una versión inicial**, algunas con reglas y límites; **4 HU requieren alcance parcial o completar captura de datos**.

## 2. Evaluación por historia

| HU | Historia | Factibilidad actual | Base existente y trabajo necesario |
| --- | --- | --- | --- |
| HU95 | Generar reportes presupuestarios | Viable ahora | Usar `t_estimacion`, partidas y APU actuales para reporte por obra/versión/estado, cantidades y montos; construir consulta, presentación y exportación. Evitar el flujo antiguo que consulta `t_apu` retirado. |
| HU96 | Consultar comparativo de costos | Base ya implementada; viable consolidar | `control_costos_services.obtener_comparacion`, GET `/api/control-costos/obras/{id_obra}/comparacion` y pestaña Angular comparan original, revisado, ejecutado y variaciones. Requiere línea base ACTIVA y registros de costos. Validar aceptación y ejecución antes de declararla terminada. |
| HU97 | Generar reporte de stock | Viable ahora | `inventario_services.listar_stock`/`obtener_kpis`, lotes y stock mínimo permiten existencias, faltantes y valoración. Añadir reporte completo y exportación; no exportar solo la página visible. |
| HU98 | Generar reporte de consumo de materiales | Parcial; completar semántica/captura | Movimientos contienen material, cantidad, fecha, tipo y OT opcional. Permiten reporte de salidas registradas; ajustes y materiales asociados a una unidad no demuestran consumo físico. Falta asegurar registro inequívoco de consumo, devolución y obra/OT para una medición completa. |
| HU99 | Generar reporte de asignación de personal | Viable ahora | `t_obra_usuario`, `t_orden_trabajo_usuario`, usuarios/personas/roles y fecha de asignación permiten personal asignado por obra/OT/rol. El reporte inicial describe asignaciones actuales; no reconstruye retiros que se eliminaron. |
| HU100 | Generar reporte de utilización de personal | Parcial; faltan medidas de tiempo/capacidad | Se puede contar OT pendientes/finalizadas y asignaciones por trabajador. No hay partes de horas, jornada disponible ni dedicación individual en las tablas de asignación. Fechas de una OT no son horas efectivas de cada responsable. |
| HU101 | Generar reporte ejecutivo de avance | Viable ahora, con definición de indicador | Existen obras, estados, fechas, OT, incidencias y `t_avance_obra` por unidad. Definir si avance será porcentaje de OT finalizadas o avance físico agregado; evitar equiparar ambos o sumar porcentajes de unidades sin ponderación. |
| HU102 | Generar reporte del estado de unidades | Viable ahora | Unidades, estructura, estado e historial permiten distribución por obra/tipo/estado y detalle. Separar estado constructivo de estado comercial de la asociación CRM. |
| HU103 | Generar reporte de incidencias | Viable ahora | Incidencia, responsable, prioridad, estado, fechas, seguimiento y vínculos OT permiten reporte por obra/período/actor. Agregar filtros, métricas y exportación autorizada. |
| HU104 | Generar reporte de incidencias críticas | Viable ahora | Subconjunto con prioridad CRITICA; combinar con estado y duración de atención. Definir si incluye históricas resueltas/cerradas o solo críticas activas. |
| HU105 | Consultar métricas mediante lenguaje natural | Viable ahora, catálogo acotado | Reutilizar `AIService`/`GeminiProvider` y añadir métricas deterministas por dominio. Interpretar consultas soportadas y obtener datos autorizados. No entregar acceso SQL libre a la IA. |
| HU106 | Consultar costos y desvíos mediante IA | Viable ahora | Proveer a IA comparativos CU17 calculados por el backend y referencias a partidas/línea base. Agregar contexto de costos y permiso correspondiente. Mostrar ausencia de línea base/datos sin inventar montos. |
| HU107 | Consultar estado y avances mediante IA | Viable ahora | Contexto de proyectos, OT, unidades e incidencias, con indicadores definidos para HU101. Respuesta con alcance y fecha del dato. No confundir progreso operativo con progreso físico. |
| HU108 | Consultar inventario mediante IA | Viable ahora | Contexto de stock, mínimos, movimientos y compras pendientes con permisos de cada dominio. Debe soportar agregados/filtros, no depender de un listado truncado para responder cantidades globales. |
| HU109 | Restringir los datos consultados por IA según permisos | Viable ahora; prerrequisito transversal | El CRM actual verifica permiso y empresa, pero no implementa un control general de todos los dominios. Crear selección de contexto por tenant, permiso, recurso/campo y relación; probar rechazo de acceso cruzado y auditoría. |
| HU110 | Generar recomendaciones ante desvíos de costos | Viable ahora, recomendaciones explicables | Con comparativos, categorías y órdenes de cambio se pueden identificar partidas con sobrecosto y sugerir revisión/acciones. No atribuir causas no registradas ni afirmar sobrecosto por bajo gasto en una obra todavía en ejecución. |
| HU111 | Generar recomendaciones para optimizar compra de materiales | Viable ahora, alcance básico | Usar stock mínimo, existencias, proveedores/materiales y cantidades pendientes de recepción para sugerir reposición y evitar duplicar compras. Optimización de precio/proveedor/plazo necesita cotizaciones comparables, tiempos de entrega y demanda futura confiable. |
| HU112 | Generar recomendaciones para reasignar maquinaria y personal | Parcial; posible apoyo por reglas | Hay estado y asignaciones de maquinaria, y carga por OT/personas. Se pueden sugerir candidatos con menos asignaciones, revisando estado/empresa. Reasignación óptima requiere disponibilidad temporal, habilidades, capacidad, prioridad y restricciones de traslado. No ejecutar reasignaciones automáticamente. |
| HU113 | Generar alertas predictivas de posibles retrasos | Parcial; posible alerta de riesgo básica | Fechas, OT abiertas, incidencias y avances permiten señales de riesgo o proyección simple si hay historia suficiente. Predicción validada requiere cronograma con avance esperado, series temporales confiables y medición de resultados. No se comprobó esa cobertura en los datos. |

## 3. Qué existe y qué debe desarrollarse

HU96 tiene un comparativo funcional ya construido en backend y UI. Eso no certifica la HU completa sin revisar sus criterios de aceptación y probar el flujo.

Los datos para HU95, HU97, HU99 y HU101–HU104 están representados, pero no se encontró una implementación general de reportes/exportaciones de estas HU en los archivos revisados. Hay que desarrollar consultas agregadas, filtros, formato, permisos, presentación y descarga según el alcance solicitado.

La IA existente expone consulta/sugerencias de **CRM**. La presencia de `GeminiProvider` reduce trabajo de integración, pero no significa que HU105–HU108, HU110 o HU111 ya estén implementadas. Requieren nuevos contextos y casos de uso. No se verificó disponibilidad externa del proveedor ni su configuración efectiva; comprobarla al implementar.

HU109 tiene una base parcial en CRM; debe extenderse antes de habilitar contexto de costos, inventario, personal o múltiples dominios en una misma pregunta.

## 4. Límites de los indicadores

### Consumo y stock

La ruta actual de ajuste acepta ENTRADA_AJUSTE, SALIDA_AJUSTE y AJUSTE_INVENTARIO. Una salida de ajuste puede ser corrección de inventario. `t_unidad_material` describe materiales asociados a una unidad, sin registrar por sí sola entrega, instalación, devolución o pérdida.

Para HU98 inicial puede reportarse «salidas registradas» claramente identificadas. Para «consumo real por obra/OT/período» se debe definir y asegurar la captura del evento, la cantidad/unidad, sus devoluciones y el ámbito de empresa. Las FK opcionales y campos NULL no pueden transformarse silenciosamente en datos completos.

### Personal y maquinaria

Las tablas de asignación de personal guardan el vínculo y fecha de asignación, pero no horas, porcentaje de jornada ni fecha de retiro. El retiro de vínculos puede impedir reconstruir una historia de ocupación. La maquinaria tiene estado, fecha de asignación y retiro; tampoco registra horas de operación reales.

Puede calcularse carga aproximada por número de OT y equipos asignados. No debe presentarse como utilización porcentual de capacidad sin denominador de disponibilidad y numerador de horas efectivas.

### Costos y avance

HU96 compara presupuesto y ejecutado. Una variación negativa de ejecutado frente al presupuesto total puede reflejar una obra incompleta; no demuestra ahorro. HU110 puede actuar sobre excedentes registrados y explicar límites, pero causas/proyección al cierre requieren evidencia adicional.

HU101/HU107 deben definir el indicador: porcentaje de OT finalizadas, último avance registrado por unidad o agregación con pesos explícitos. Cada indicador responde a una pregunta distinta. Los datos comerciales de CRM tampoco equivalen al estado de construcción de la unidad.

### Recomendación y predicción

HU110–HU113 no requieren necesariamente un modelo de aprendizaje automático. Reglas transparentes y proyecciones simples pueden cubrir una versión inicial si coinciden con sus criterios de aceptación. Deben distinguirse sugerencias basadas en datos de una optimización global o una predicción calibrada.

Una alerta por fecha vencida detecta un retraso actual; no es por sí sola una alerta predictiva. HU113 necesita identificar riesgo antes del vencimiento y justificar cómo se estima, incluso si se usa una heurística.

## 5. Arquitectura propuesta para implementarlas

Conservar `routes → services → repos → PostgreSQL`:

1. Reportes: repositorios de lectura por dominio; servicios que calculen métricas/formateen resultados; rutas para filtros y exportación; UI web/móvil según el alcance pedido.
2. Métricas numéricas y monetarias: obtenerlas mediante consultas/cálculos deterministas, preservando Decimal y NUMERIC. La IA redacta y explica los resultados; no es la autoridad para sumar o inventar valores.
3. IA: mantener el proveedor desacoplado y agregar contextos por dominio. Resolver tenant y permiso **antes** de leer/serializar contexto. Si una pregunta necesita dos dominios, autorizar ambos y excluir el no permitido.
4. Recomendaciones: reglas que produzcan motivo, evidencia, valores utilizados y alcance; IA opcional para explicación. No mutar costos, compras o asignaciones como efecto de una consulta.
5. HU109: contexto autorizado reutilizable por reportes e IA, sin prometer aislamiento por prompt. Separar permisos de consulta, exportación y acciones cuando el producto lo requiera.

No crear tablas de reportes solo para duplicar datos existentes. Evaluar persistencia adicional cuando haya una necesidad concreta: horas de personal, consumo, cronograma, snapshots, programación de reportes o registro de alertas. No usar repositorios antiguos de presupuesto/APU incompatibles con la base real.

En reportes multiempresa, no sumar importes de distintas monedas sin separar moneda o definir una conversión. Exportaciones deben conservar el ámbito autorizado y recoger todos los registros filtrados, no solo la página de UI.

## 6. Secuencia sugerida

- Primero: HU109 como base de autorización; validar la HU96 existente.
- Reportes: HU95, HU97, HU99 y HU101–HU104 usando el modelo actual y criterios de indicadores.
- Consultas IA: HU105–HU108 sobre esas mismas métricas y permisos.
- Recomendaciones iniciales: HU110 y HU111 con reglas y evidencia.
- Completar eventos/capacidad/cronograma para HU98, HU100, HU112 y HU113; aceptar versiones parciales solo si sus limitaciones satisfacen los criterios de negocio.

## 7. Validación de esta evaluación

Se revisaron estructuras de asignación, avances, OT, movimientos, unidades y maquinaria; servicios de inventario; cálculo de comparación CU17; consumidor Angular; y clases de IA/proveedor/contexto. Se verificó cobertura documental de las 19 HU.

No se ejecutaron pruebas funcionales ni se implementó código. No se comprobó calidad de registros ni se llamó Gemini. La validación de factibilidad completa depende de criterios de aceptación, alcance de reporte y cobertura de datos.
