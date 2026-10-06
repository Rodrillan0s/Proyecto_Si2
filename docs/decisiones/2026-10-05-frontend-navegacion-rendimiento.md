# Implementación frontend de navegación y rendimiento

Fecha: 2026-10-05. El usuario aprobó [el plan](../PLAN_REFACTOR_FRONTEND_NAVEGACION_RENDIMIENTO.md). Solo frontend/documentación; backend, JWT, esquema y permisos permanecen intactos.

## Análisis previo

Se revisaron arquitectura general, Reportes/IA y operación, plan y reversión anterior. Angular standalone compone shell → router-outlet → páginas y una instancia de asistente. AuthService y guards conservan sus contratos y fallback actuales. Registro de enlaces por permisos existentes; contexto Empresa/Obra como filtro de navegación, sin remount global del outlet. Servicios de lectura deduplican peticiones simultáneas por sesión/contexto, sin caché permanente ni cambios HTTP. Los módulos que operan con empresa del JWT no se presentan como globales. Datos y formularios existentes se conservan.

## Contratos y línea base de código

Panel duplica materiales/proveedores al emitir BehaviorSubject y cargar datos iniciales; Inventario duplica stock/KPIs; Materiales e Incidencias duplican listado; Compras duplica órdenes/catálogos. APU recorre materiales en páginas de 100 al montar; Reportes espera catálogo y recursos de pestañas auxiliares. Obras es GET /api/proyectos/ sin filtro empresa; materiales/inventario/compras/CRM admiten empresa; OT empresa/obra; costos/APU dependen del JWT. Catálogo Reportes autoriza familias. No se midieron latencias de APIs reales: pruebas simularán conteos y respuestas desordenadas sin DB/envíos.

## Validación prevista

Pruebas de solicitudes únicas, contexto y aislamiento de respuestas, destinos/sidebar, asistente único, Reportes y compatibilidad Backup; build producción y navegador aislado desktop/móvil con HTTP/WebSocket simulados. Comprobar diff backend vacío y conservar cambios previos de Backup/OCI. No nuevos endpoints, trabajadores, SQL o credenciales. Resultados se registrarán al terminar.

## Implementación

- Registro declarativo `navegacion.ts`: categorías plegables, iconos en rail, selección activa, destinos y permisos existentes. Conserva módulos de compras, maquinaria, administración y cuenta; Backup conserva su restricción global. Reportes usa familias y los identificadores disponibles en el catálogo autorizado, sin crear endpoints.
- `ContextoOperativo` deriva empresa de AuthService y mantiene la obra en memoria. Cambiar empresa limpia la obra; no altera JWT ni persistencia de sesión. Las páginas reaccionan sin reconstruir `router-outlet`. Formularios registrados piden confirmación al descartar y bloquean el cambio durante escrituras. La selección visual nunca concede autorización.
- APU/Costos conservan el contrato ligado a la empresa del JWT y muestran una advertencia cuando el contexto elegido es incompatible. CRM y los listados con soporte de empresa reutilizan sus parámetros HTTP existentes. El Dashboard conserva tarjetas, contenido y distribución; recalcula datos después de las respuestas y distingue errores de resultados vacíos.
- `LecturasCompartidas` comparte únicamente GET simultáneos por clave de recurso, empresa y token; elimina la entrada al finalizar o fallar. No incorpora caché permanente. `LecturasVigentes` cancela la lectura anterior por recurso y al destruir la página. No aplica reintentos automáticos a escrituras.
- Se eliminan inicializaciones duplicadas de Panel, Inventario, Materiales, Incidencias, Compras, CRM y Proveedores. Compras/APU cargan materiales al abrir el editor y recorren páginas de 100. Reportes carga inicialmente el catálogo; historial, programación y destinatarios se consultan al utilizarse. Las rutas cargan sus componentes bajo demanda conservando guards y contratos.
- Asistente: un componente en el shell y tres modos coordinados por signals. Cabecera ejecuta consulta rápida mediante acción explícita; burbuja abre conversación; `/asistente` presenta la misma conversación como módulo. Cambiar modo conserva historial; cambiar empresa/obra invalida conversación y respuestas anteriores. Los temas filtran historial. Las preguntas incorporan el contexto de obra como texto, conservando la API actual.
- Notificaciones detiene la reconexión al cerrar sesión. No se modificaron AuthService, guards, backend, Flutter, SQL, daemon ni funcionalidades de Backup.

## Validación ejecutada

Entorno local, HTTP/WebSocket y actores simulados; no se contactó la base, OCI, IA o Brevo. No se certifican latencias SQL ni un despliegue real.

| Comprobación | Resultado |
| --- | --- |
| Navegación y rendimiento | 16 pruebas aprobadas: permisos, destinos, rail, catálogo bajo demanda, deduplicación, cancelación, contexto y solicitudes iniciales de Inventario/Materiales/Incidencias/Compras. |
| Reportes y asistente | 21 pruebas aprobadas. |
| Compatibilidad Backup | 19 aprobadas y 2 fallos de textos preexistentes sobre heartbeat/restore. Se conservaron los cambios previos del usuario; no se modificó este módulo. |
| Navegador aislado 1366 × 900 / 390 × 844 | 38 solicitudes simuladas, cero errores de ejecución; rail, obra, consulta rápida, conversación, módulo único, Reportes, envío/programación simulados, tema oscuro y móvil. Dashboard muestra la obra de la empresa y su encabezado. Capturas en `frontend/.angular/reportes-preview/`. |
| Producción | Compilación aprobada; carga inicial 645,28 kB frente a 1,73 MB de la versión restaurada. Es tamaño de bundle sin comprimir, no tiempo de respuesta de la base. Persisten advertencias de presupuestos CSS y Leaflet CommonJS. |
| Alcance | `git diff -- backend`, AuthService y guards sin cambios. No migraciones, servidores backend, workers, correos ni restauraciones. |

Conteos controlados: Inventario inicia 2 solicitudes (stock/KPI), Materiales 3 (listado y dos catálogos), Incidencias 3 (listado y filtros), Compras 2 (órdenes/proveedores; materiales diferidos). Reportes no solicita recursos auxiliares al entrar. No hay una medición real de tiempo por endpoint; la optimización de SQL, índices y planes requiere una intervención backend autorizada aparte.

## Operación y límites

No requiere migraciones ni reiniciar backend. Compilar/desplegar el frontend según el flujo existente. Validar luego con cuentas reales y empresas autorizadas en el entorno de pruebas, incluyendo roles personalizados, pestañas de edición, exportación y micrófono; las pruebas sintéticas no certifican dispositivos ni entrega real de correo. La obra seleccionada no filtra módulos cuyos endpoints carecen de ese contrato. El historial del asistente sigue bajo las reglas existentes de conversación y contexto.
