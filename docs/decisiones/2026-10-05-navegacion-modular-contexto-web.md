# Navegación modular y contexto Empresa/Obra del frontend

**RETIRADA por solicitud del usuario el 2026-10-05.** Esta nota describe una intervención histórica que se revierte completamente. El backend estaba fuera del alcance autorizado. Consultar [reversión y validación](2026-10-05-reversion-navegacion-web.md); los contratos y pasos de activación siguientes ya no representan la versión vigente.

Fecha: 2026-10-05. Solicitud: reorganizar sidebar/header y accesos a IA conservando diseño oscuro, tipografía, paleta, responsive y contenido de dashboards.

## Análisis previo y contratos

Se leyeron arquitectura general, Reportes/IA, operación, arquitectura BD e inventario/rutinas y se revisaron shell Angular, guards, AuthService, proyectos/detalle, Reportes, asistente y rutas/servicios de autenticación. Actualmente el sidebar se elimina al colapsar; sus enlaces carecen de selección consistente y “Gestión”/“Nuevo” apuntan a un tab que la lista no consume. El selector de obra solo navega a la lista. AuthService concede accesos mediante mapas de nombres de rol; login no entrega permisos y roles tampoco. No hay endpoint actual que entregue permisos generales efectivos de la sesión.

Mantener capas `routes → services → repos → PostgreSQL`. La única ampliación backend necesaria es una consulta autenticada de contexto/permisos actuales de la propia cuenta, en transacción de solo lectura, reutilizando tablas existentes y la política vigente: ADMINISTRADOR global tiene bypass de acciones; otras cuentas usan t_rol_permiso. Entregar permisos y capacidades de alcance/administración global desde el servidor. No crear permisos, roles, migraciones ni cambiar reglas de recursos. El frontend deja de inferir accesos de nombres de rol y espera esta consulta antes de activar rutas privadas; error de contexto no concede permisos.

Modelo declarativo de navegación por secciones/items, filtrado por permisos/capacidades del servidor; grupos vacíos ocultos, selección por ruta/tab/familia de reportes y expansión independiente. Conservar acceso a módulos existentes adicionales (compras, equipos, administración, usuario); backup mantiene capacidad global y sus reglas backend sin modificación. Rail colapsado conserva iconos y acceso con nombres accesibles/tooltips; móvil conserva panel/overlay. Tarjeta de usuario única: avatar, nombre, rol y empresa operativa actual.

Contexto de obra compartido separado de la identidad/JWT y vinculado a la empresa autorizada. Cambio de empresa limpia obra, cargas y resultados previos, invalida respuestas tardías y renueva vista operativa sin cambiar HTML/contenido de dashboards. Selector usa listado de obras autorizado existente y filtra empresa; módulos reciben id_obra cuando lo soportan. Seleccionar/abrir una obra sincroniza contexto; rutas de recurso no permanecen en otra empresa tras un cambio. Asignaciones usan detalle/estructura/responsables de obra seleccionada y, sin obra, conducen a Gestión para elegirla, sin tabs ficticios.

Reportes financieros/inventario/personal/obras/incidencias son accesos al mismo módulo y catálogo backend autorizado, mediante familia en query params. No duplicar reportes, cálculos o dashboards. Filtrar opciones por catálogo/permisos del dominio y aplicar selección inicial/contexto sin generar reportes automáticamente.

Asistente: conservar una sola instancia/conversación del shell; barra superior presenta consulta rápida y respuesta breve, burbuja expande conversación completa, ruta del sidebar muestra la misma instancia en modo amplio de análisis. No montar un segundo chat ni usar nueva API IA. Cambios de empresa/obra invalidan respuestas anteriores; no enviar conversaciones con contexto antiguo. En formularios, la obra seleccionada filtra consultas existentes; en IA se incorpora como contexto textual a la solicitud para su interpretación en el backend, sin ampliar el contrato ni sustituir autorización.

## Validación prevista

Pruebas aisladas backend para contexto activo/permisos/bypass/cuenta inválida; Angular para permisos sin fallback de rol, navegación/selección/grupos vacíos, selector dependiente de empresa y respuestas tardías, contexto de obra, accesos IA únicos y filtros de familias de reportes. Compilar producción y suites de Reportes/Backup para regresiones. Revisar impacto Flutter: nuevo endpoint aditivo, sin cambiar login ni contratos móviles. Sin migraciones, workers, envíos, escrituras BD o cambios de dashboards. Documentar resultados reales y límites de comprobación visual.

## Implementación

Se añadió `GET /api/auth/contexto` autenticado y sin caché, con consulta parametrizada de la propia cuenta activa. Devuelve permisos reales, capacidades de alcance global y tipos de reportes permitidos por la política vigente. El repositorio descarta la transacción de validación de conexión antes de establecer READ ONLY/REPEATABLE READ. El servidor conserva sus excepciones globales existentes; Angular deja de derivar permisos de nombres de roles. Los guards esperan el contexto; errores o respuestas de sesiones anteriores no conceden accesos. El endpoint es aditivo: login y clientes Flutter conservan sus contratos.

El registro `navegacion.ts` agrupa módulos y destinos; oculta grupos sin opciones autorizadas y conserva compras, equipos, administración y ajustes. Categorías independientes, selección por ruta/tab/familia, iconos accesibles en el rail y overlay móvil. Reportes abre el catálogo existente por familia, sin ejecutar automáticamente consultas. Nuevo proyecto abre el formulario de creación y Gestión mantiene el listado. Asignaciones apuntan a estructura/responsables del proyecto elegido; sin obra solicitan elegir desde Gestión.

ContextoOperativo mantiene una obra de la empresa activa. El shell carga obras autorizadas, descarta respuestas tardías y sincroniza detalle/selector. Cambiar empresa limpia la obra y recrea la vista operativa para recargar sus datos; cambiar obra aplica el filtro donde el módulo lo soporta. Se conectaron proyectos, incidencias, órdenes de trabajo, estimaciones, control de costos y Reportes sin reemplazar sus dashboards. La única adición al marcado del detalle es el ancla de responsables. El módulo de estimaciones deja de seleccionar silenciosamente la primera obra cuando la cabecera indica Todas las obras.

La tarjeta lateral muestra avatar, nombre, rol y empresa actual; se retiró la tarjeta duplicada de la cabecera. Se conserva una única instancia de Asistente fuera del outlet operativo: cabecera envía consulta rápida, burbuja expande historial y ruta `/asistente` presenta análisis amplio. Cambiar empresa/obra invalida respuestas anteriores; los modos comparten conversación. Voz y API IA siguen usando sus mecanismos existentes.

Para usar esta versión, reiniciar/desplegar backend y frontend juntos: la interfaz requiere el nuevo endpoint de contexto. No se necesita migración ni cambios de variables de entorno.

## Validación realizada y límites

- Backend: 97 pruebas aisladas aprobadas (`test_session_context`, `test_backup_downloads`, `test_backup_vm`, `test_backups`, `test_backups_engine`), incluidas siete nuevas de permisos/contexto y contrato HTTP. Las pruebas del endpoint desactivan el control de backups para no contactar una base real.
- Angular: 13 pruebas de navegación/contexto aprobadas; 22 de Reportes/asistente aprobadas. Cubren permisos sin fallback de roles, capacidades, cambio de sesión, empresa/obra, categorías, destinos contextuales, acceso único a IA y familias.
- Compilación final `npm run build`: correcta (2026-10-05 18:14 UTC). Persisten avisos de presupuestos CSS y Leaflet/CommonJS; el CSS del asistente supera el umbral de advertencia de 4 kB en 414 bytes, sin superar el límite de error.
- Navegador aislado, escritorio y móvil: `reportes-browser-check.cjs` terminó OK con 40 solicitudes simuladas y cero errores de ejecución. Verificó rail de 68 px, overlay móvil, selectores, consulta rápida, conversación y módulo compartido. Capturas temporales en `frontend/.angular/reportes-preview/`, ignoradas por Git. No utilizó sesión real, envió correos ni contactó APIs de negocio reales.
- Catálogo PostgreSQL: consulta de solo lectura a information_schema confirmó las columnas utilizadas de las cinco tablas de autenticación. No inspeccionó cuentas personales, modificó permisos ni aplicó scripts.
- Regresión web de Backup: 19 de 21 pruebas aprobadas. Dos aserciones de texto fallan por el contenido actual de `backup.html`, ajeno a esta refactorización: esperan mensajes de heartbeat pendiente y producción no habilitada. No se modificaron pantalla, política o seguridad de backups para ajustar esas aserciones. La navegación utiliza la capacidad global del servidor; el restore continúa sujeto a las restricciones backend existentes.

Estas comprobaciones no certifican un recorrido con cuentas reales ni todos los permisos configurados de cada tenant. No se iniciaron backend, workers de Reportes/Backup, migraciones, restauraciones ni procesos automáticos. El servidor frontend de comprobación se cerró al terminar. Se conservaron cambios previos del usuario, incluidos los del módulo Backup y eliminaciones documentales.
