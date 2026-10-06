# Plan de refactorización del frontend: navegación, contexto y rendimiento

Fecha: 2026-10-05, America/La_Paz. Estado: **propuesto para aprobación; sin implementación**.

## 1. Objetivo y alcance

Reorganizar la navegación web de OBRATEC y reducir las esperas al consultar datos, conservando el diseño actual y el contenido de los dashboards. Revisar las conexiones entre shell, rutas, guards, servicios HTTP, páginas, empresa, obra y asistente antes de cambiar cada flujo.

**La implementación propuesta es exclusivamente frontend y documentación.** No modificar backend, endpoints, JWT, login, funciones/procedimientos SQL, índices, esquema, roles, permisos o Flutter. No volver a introducir `/api/auth/contexto`, ni otra dependencia de un endpoint inexistente. Mantener los cambios actuales de Backup/OCI y sus restricciones. No iniciar workers, correos, restauraciones o automatizaciones como parte de las pruebas.

La optimización inmediata de consultas consiste en hacer menos solicitudes redundantes, cargar únicamente lo necesario, aprovechar filtros/paginación existentes y procesar correctamente respuestas concurrentes. Cambiar el SQL que ejecuta una solicitud requiere una intervención posterior, separada y expresamente autorizada. Este plan incluye cómo detectar esa necesidad, sin incluir su ejecución en la aprobación del frontend.

Referencias revisadas: [arquitectura general](ARQUITECTURA_Y_PATRONES.md), [Reportes/IA](ARQUITECTURA_REPORTES_IA.md), [operación](OPERACION_REPORTES.md), [base de datos](ARQUITECTURA_BASE_DATOS.md), inventario/rutinas enlazados y [reversión anterior](decisiones/2026-10-05-reversion-navegacion-web.md). La intervención retirada no se utilizará como una implementación válida para copiar sin revisión.

## 2. Hallazgos del código actual

Son hallazgos de lectura de código, no mediciones de latencia del servidor.

| Flujo | Hallazgo | Acción propuesta |
| --- | --- | --- |
| Dashboard | La suscripción inicial a empresa carga materiales/proveedores y `cargarDatosPorRol()` vuelve a solicitarlos. | Unificar la carga inicial y los cambios efectivos de empresa; una solicitud por recurso/contexto. |
| Inventario | La emisión inicial de empresa llama `cargarTodo()` y `ngOnInit()` lo vuelve a llamar. | Eliminar el segundo disparo; mantener stock y KPIs independientes. |
| Materiales | La suscripción inicial carga materiales y después se llama nuevamente al mismo método. | Una carga inicial, conservando debounce y paginación. |
| Incidencias | La suscripción inicial carga incidencias y al final de la inicialización se repite. | Unificar disparos y descartar respuestas de filtros anteriores. |
| Compras | La suscripción inicial carga órdenes/catálogos y luego se repiten ambas operaciones. | Una carga de órdenes; catálogos del formulario solo cuando correspondan. |
| Estimaciones/APU | Se recorren secuencialmente todas las páginas de materiales al abrir el módulo; también se selecciona automáticamente la primera obra. | Materiales bajo demanda al usar el editor; preservar material seleccionado y completar páginas cuando el control lo necesite. Resolver explícitamente el contexto de obra. |
| Control de costos | Ya usa `forkJoin` para cuatro consultas, pero espera las cuatro y no vincula sus respuestas a una versión de obra. | Conservar paralelismo, proteger cambios rápidos de obra y evaluar carga por pestaña/estado independiente. No prometer una mejora solo por añadir más paralelismo. |
| Reportes | Después del catálogo espera historial, destinatarios y programaciones antes de finalizar `load()`. | Habilitar generación al tener catálogo; cargar historial/programaciones al abrirlos y destinatarios al preparar envío, conservando permisos y acceso directo a ejecuciones. |
| Asistente | Ya existe una instancia flotante compartida; consulta catálogo también usado por Reportes. | Mantener esa instancia y compartir solicitudes de catálogo compatibles dentro del mismo contexto. |
| Proyectos | Dashboard, páginas y otros selectores solicitan el mismo listado; no hay deduplicación compartida. | Compartir solicitudes simultáneas y evaluar reutilización breve con invalidación tras escrituras. |
| Sidebar | Al colapsar se elimina el `<aside>`; Gestión y Editar/Nuevo apuntan al mismo tab; los enlaces no tienen selección uniforme. | Rail de iconos, destinos reales y estado activo consistente. |
| Empresa | Algunas páginas escuchan cambios y otras solo cargan una vez. El listado de obras no recibe un filtro de empresa en su contrato actual. | Inventariar consumidor por consumidor; respetar ámbito backend y aplicar filtros locales solo sobre resultados autorizados. |
| CRM | La inicialización no se suscribe a cambios de empresa, aunque su servicio admite `id_empresa` en varias consultas. | Conectar lista, métricas y recursos dependientes al contexto utilizando exclusivamente parámetros existentes. |
| Rutas | Las páginas se importan directamente y hay una entrada duplicada de estimaciones. | Revisar duplicado y aplicar carga diferida gradualmente sin cambiar URLs/guards. |

También se revisarán respuestas vacías y errores por separado: un error HTTP no debe transformarse en «cero obras/materiales» ni dejar el indicador de carga indefinidamente activo. El número cero solo debe corresponder a una respuesta válida del backend. Los contadores del dashboard deben actualizarse al llegar sus datos, no solo al emitirse el cambio de empresa.

## 3. Arquitectura propuesta y límites de compatibilidad

### Navegación y permisos

Registro declarativo de secciones/enlaces en frontend: etiqueta, icono, URL, parámetros admitidos y permisos necesarios. El sidebar y los destinos utilizarán el mismo registro; las páginas conservarán los guards actuales y el backend seguirá autorizando cada recurso.

El registro llamará a `AuthService.hasPermission/hasAnyPermission/hasAllPermissions`, sin incorporar mapas nuevos por nombre de rol. **Limitación actual:** login y perfil no entregan una lista general de permisos efectivos; AuthService utiliza permisos explícitos de sesión cuando existen y un fallback local por rol. Se conservará esa compatibilidad en esta fase para evitar quitar accesos o cambiar la sesión. No se afirmará que la navegación refleja todos los permisos actuales de PostgreSQL. Sustituir completamente ese fallback por permisos dinámicos exige otro contrato autorizado del backend y queda fuera de este plan.

Backup mantiene su regla existente de ADMINISTRADOR global. El selector global de empresa mantiene la distinción vigente entre ADMINISTRADOR y ADMINISTRADOR_EMPRESA. Estas reglas de alcance no se reemplazarán por permisos genéricos de lectura ni se extenderán a otros roles.

### Contexto operativo

Extensión de estado frontend sobre el mecanismo reactivo actual de empresa, sin reemplazar AuthService ni cambiar el contenido de `usuario`, el token o sus métodos públicos. Una obra seleccionada será un filtro de navegación, nunca una autorización.

El estado de obra tendrá identificador, nombre y empresa. Se seleccionará desde datos devueltos por APIs existentes; al cambiar empresa se limpiará una obra incompatible. No se seleccionará silenciosamente la primera obra. Una selección local o un parámetro de URL no acredita pertenencia: el detalle debe confirmar el recurso con el backend.

Cada página afectada incorporará un adaptador pequeño de contexto: cambio efectivo → limpiar resultado anterior → cancelar lectura sustituida cuando sea posible → solicitar con los parámetros admitidos → aceptar únicamente la respuesta del contexto vigente. **No desmontar y volver a crear globalmente el router-outlet**, ni reiniciar todos los dashboards, formularios o el chat para propagar un filtro. Si hay un formulario sin guardar, se debe resolver antes de cambiar su contexto.

| Módulo | Empresa/obra con contratos existentes | Regla de integración |
| --- | --- | --- |
| Dashboard y proyectos | Listado de obras autorizado; empresa como filtro local cuando aplica. | Mantener datos y contadores; recargar solo recursos que lo requieren. Seleccionar obra no vacía automáticamente el resumen empresarial. |
| Materiales, inventario, proveedores y compras | Sus servicios admiten filtros de empresa en las consultas revisadas. | Usarlos donde el endpoint correspondiente los admite; stock no se filtrará por obra si su contrato no lo soporta. |
| CRM | Lista/métricas/detalles admiten empresa; revisar asesores y operaciones individualmente. | Propagar empresa también a recursos auxiliares compatibles y limpiar selecciones anteriores. |
| Órdenes de trabajo | El servicio admite empresa y obra. | Enviar filtros existentes y conservar navegación a detalle. |
| Incidencias | Filtros por obra/unidad y alcance decidido por backend. | Validar la obra, limpiar unidad dependiente y respetar paginación/semántica de resumen actuales. |
| Estimaciones y control de costos | Los servicios backend revisados resuelven empresa desde el JWT. | La empresa seleccionada del administrador no cambia ese JWT. No presentar una empresa distinta como operativa si la API no admite su alcance: explicar la limitación y evitar solicitudes incompatibles. |
| Reportes e IA | Empresa explícita y catálogo autorizado; obra según tipo de reporte. | Elegir solo obras del catálogo aplicable; mostrar familias realmente disponibles y conservar exportación/envío/programación. |
| Backup, usuarios, roles, empresas, perfil y bitácora | Alcances y restricciones propios. | Revisarlos en regresión; no aplicar indiscriminadamente filtros de obra a módulos globales. |

### Servicios de lectura y rendimiento

Mantener servicios HTTP como adaptadores de las APIs actuales. Incorporar deduplicación de lecturas seleccionadas y un estado explícito por recurso: pendiente, datos, vacío o error. No convertir automáticamente todas las APIs a un modelo nuevo ni utilizar un interceptor universal de caché.

Las solicitudes compartidas tendrán clave por sesión, contexto autorizado, URL y parámetros normalizados. Los datos empresariales se mantendrán en memoria, nunca en almacenamiento persistente nuevo. Cambiar cuenta/cerrar sesión elimina la caché; las escrituras invalidan los recursos relacionados. Los errores no se almacenan como resultados válidos. No guardar JWT, URLs PAR o respuestas sensibles en logs de medición.

## 4. Organización visual y destinos

Conservar colores, fuente, sidebar oscuro, header y área principal clara. No sustituir componentes ni modificar las tarjetas, tablas o métricas de los dashboards.

Secciones propuestas:

- **Principal:** Dashboard.
- **Proyectos y obras:** Ver obras, Gestión de proyectos, Nuevo proyecto, asignación de unidades, jefes de obra, órdenes de trabajo e incidencias.
- **Presupuestos y costos:** Presupuestos/APU y Control de costos.
- **Comercial y clientes:** CRM y Clientes.
- **Inventario y logística:** Stock, Materiales, Proveedores, Compras y Equipos/Maquinaria.
- **Reportes y analítica:** financieros, inventario, personal, obras e incidencias; todos reutilizan `/reportes` y su catálogo.
- **Inteligencia artificial:** Asistente Inteligente.
- **Administración y cuenta:** conservar empresas, usuarios, roles, bitácora, copias de respaldo, perfil y seguridad según accesos actuales.

Categorías expandibles con estado independiente; ocultar grupos sin opciones visibles. La sección activa debe poder encontrarse sin abrir todos los grupos. En escritorio, colapsar deja iconos con nombres accesibles/tooltips; en móvil mantiene panel y overlay. Preservar navegación por teclado, Escape, foco y atributos de selección/expansión.

Gestión abrirá el listado/edición existente; Nuevo abrirá el formulario actual de creación, con su permiso correspondiente. Asignación de unidades llevará a estructura de la obra seleccionada; jefes, a responsables del detalle. Sin obra seleccionada, conducir a la selección de obra con intención conservada. No añadir enlaces a tabs que el destino no consume.

Cabecera: empresa y obra legibles, estados globales «Todas las empresas» y «Todas las obras» donde sean compatibles, módulo actual y selectores utilizables en pantallas pequeñas. Evitar que el header cubra el título o que exista doble compensación de altura al usar sticky/fixed. Tarjeta lateral única con avatar, nombre, rol y empresa operativa; retirar únicamente la repetición de identidad en header, preservando acceso al perfil y cierre de sesión.

Reportes por familia será una preselección visual. No duplicar dashboards de reportes ni cambiar tipos/consultas backend. Si una familia no tiene reportes autorizados, no ofrecer un destino vacío. Conservar URLs de ejecuciones compartidas y parámetros de filtros existentes.

## 5. Asistente único

Mantener una sola instancia del componente y una conversación compartida; el historial puede filtrar temas.

| Acceso | Comportamiento propuesto |
| --- | --- |
| Cabecera | Consulta rápida y respuesta compacta utilizando el contrato actual. Enviar solo mediante acción explícita del usuario. |
| Burbuja | Conversación completa, historial, voz y acciones existentes. |
| Sidebar | Vista amplia del mismo asistente y conversación, sin montar un segundo componente de chat. |

Cambiar de modo o cerrar no borra conversación. Cambiar de empresa invalida mensajes/respuestas del contexto anterior. Integrar obra únicamente con el contexto que admite la solicitud existente; si se expresa como texto, preservar intención explícita del usuario, por ejemplo «todas las obras», y dejar interpretación/autorización al backend. No inventar campos IA, capacidades de escritura o SQL. Mantener catálogo bajo demanda y errores recuperables.

## 6. Plan de optimización de solicitudes

Prioridad de implementación:

1. **Eliminar disparos duplicados.** Un solo origen para la carga inicial y cambios efectivos; comparar el ID de empresa antes de recargar. Separar actualizar manualmente de repetir automáticamente el mismo contexto.
2. **Evitar resultados tardíos.** Lecturas sustituibles mediante `switchMap` y limpieza al destruir componentes; para métodos actuales basados en Promise, versión de contexto y descarte de respuesta antigua. Cancelar HTTP desde el navegador no garantiza cancelar una consulta PostgreSQL que ya comenzó.
3. **Compartir solicitudes simultáneas.** Obras y catálogos consumidos por varias páginas: una petición pendiente para la misma clave. Primero deduplicación; añadir caché temporal solo tras definir invalidación y medir su necesidad.
4. **Cargar al necesitarlo.** Detalles, asesores/candidatos, catálogos de formularios, destinatarios y pestañas inactivas no deben bloquear el contenido principal. El mapa se inicializa cuando su contenedor está visible. No descargar todos los materiales de APU al entrar para un editor todavía cerrado.
5. **Respetar paginación y filtros del servidor.** Materiales, inventario, compras, proveedores y CRM deben consultar la página requerida y mantener totales del backend. Buscar con el debounce ya existente, más cancelación de búsqueda anterior. No elevar límites arbitrariamente ni afirmar que una página parcial representa el total.
6. **Estados independientes.** Una consulta auxiliar lenta no deja toda la página bloqueada; su error se muestra en su sección. Paralelizar solo solicitudes independientes, sin fan-out ilimitado ni reintentos automáticos de escrituras.
7. **Invalidación tras cambios.** Crear/editar obra invalida listado/detalle; ajustes/recepción invalidan stock/KPIs y materiales afectados; cambios CRM invalidan lista/métricas pertinentes. Enviar/programar sigue conservando sus claves de idempotencia. No cachear mutaciones, exportaciones o enlaces de descarga OCI.
8. **Carga diferida de rutas.** Migración gradual a `loadComponent` en páginas de peso significativo, preservando guards, URLs, recarga directa y comportamiento SSR/hidratación. No precargar simultáneamente todo el sistema para compensar.

Política inicial: datos operativos dinámicos, deduplicación de solicitudes pendientes sin caché duradera. Catálogos de baja variación pueden conservarse hasta cinco minutos en memoria si se confirma su alcance y se invalidan al modificarse. Catálogos con permisos/acciones, como Reportes, tendrán política separada y revalidación de contexto; no reutilizar indefinidamente autorizaciones antiguas. Se mantiene Actualizar para forzar consulta reciente.

El polling de Reportes ya se condiciona a trabajos pendientes y pestaña visible. Conservarlo, comprobar que no se solape y que cese al salir; no añadir intervalos por cada familia de reportes. Revisar la reconexión WebSocket para evitar lecturas repetidas de historial y reconexiones después de cerrar sesión, sin alterar su contrato.

## 7. Cómo identificar consultas SQL realmente lentas

Registrar una línea base antes de optimizar, diferenciando arranque frío, navegación con caché y cambio de empresa. Por módulo: número de GET, duplicados, duración, tamaño transferido, tiempo hasta datos principales y errores. Separar descarga del frontend, espera HTTP y renderizado; no atribuir toda demora a PostgreSQL sin evidencia.

Una única llamada lenta después de eliminar duplicados se documentará con ruta, parámetros anonimizados, tamaño y duración. No prometer un porcentaje de mejora ni tiempos absolutos sin medir. La cancelación y los indicadores de carga mejoran la interacción, pero no demuestran que el servidor ejecute más rápido.

**Trabajo futuro fuera de esta aprobación:** con autorización para backend/BD, revisar el flujo routes → services → repos → rutinas SQL del endpoint identificado; contrastar objetos/índices actuales y planes de ejecución. Evaluar filtros, joins, conteos, funciones invocadas repetidamente, paginación y alcance tenant antes de proponer un índice o reescribir una consulta. No ejecutar EXPLAIN ANALYZE, funciones de negocio, migraciones o pruebas de carga sobre una base desconocida. Mantener el inventario histórico como referencia, no como prueba de instalación actual.

## 8. Fases, entregables y orden

| Fase | Entregable | Condición de cierre |
| --- | --- | --- |
| 0. Contratos y línea base | Matriz ruta → página → servicio → endpoint → parámetros/permisos; capturas y solicitudes por módulo. | Destinos y ámbitos comprobados; limitaciones Empresa/JWT y permisos identificadas. |
| 1. Rendimiento inicial | Cargas únicas, respuestas vigentes, estados independientes y primeras lecturas bajo demanda. | Misma información visible, sin solicitudes duplicadas de inicialización. |
| 2. Sidebar/header | Registro modular, grupos, rail, selección, tarjeta y responsive. | Todos los enlaces conducen a flujos existentes; sin nuevas llamadas de autenticación. |
| 3. Empresa/obra | Integración por módulo, selectores y destinos de asignación. | Cambios de contexto no mezclan resultados ni pierden formularios/conversación sin advertencia aplicable. |
| 4. Reportes/asistente | Familias y tres modos sobre una sola conversación; catálogos y pestañas bajo demanda. | Exportaciones, voz, historial, envío y programaciones mantienen sus contratos. |
| 5. Rendimiento y regresión | Medición comparativa, carga diferida justificada y pruebas finales. | Compilación, rutas, permisos, tenants y funcionalidades existentes verificados; pendientes reales documentados. |

Aplicar cambios por flujo y revisar cada fase antes de ampliarlos al resto. No repetir un reemplazo amplio de AuthService/guards para acomodar la UI. La aprobación de este plan autoriza únicamente frontend/documentación; no incorpora la etapa SQL futura.

## 9. Archivos y validación

Áreas previstas: `frontend/src/app/layouts/admin-layout/`, `app.routes.ts`, servicios de lectura afectados, páginas que consumen contexto, `components/asistente/` y su servicio de coordinación. Nuevos archivos de navegación/contexto deben ser pequeños y reutilizar el mecanismo actual. AuthService conserva login, almacenamiento y contrato público; cualquier ajuste de lecturas/contexto se prueba contra sus consumidores. No editar `backend/` ni `mobile/`.

Verificación prevista:

- Comparar capturas de Dashboard y páginas afectadas antes/después, sin cambiar datos, tarjetas o disposición interna. Escritorio 1920/1366 y móvil 390 px; títulos visibles, sin solapamiento de header ni desbordamiento de selectores.
- Rutas directas/recarga, volver/adelante, grupos contraídos, rail, teclado y opción activa. Gestión, Nuevo, estructura y responsables deben ejecutar su intención real.
- Casos de ADMINISTRADOR global, ADMINISTRADOR_EMPRESA, permisos limitados y rol personalizado con permisos explícitos cuando la sesión los incluya. Conservar alcance de Backup y comprobar manejo de 401/403 sin falsear datos vacíos.
- Empresas A/B con datos existentes: misma empresa no recarga innecesariamente; alternancia rápida A → B → A no acepta resultados viejos. Obras disponibles corresponden al ámbito autorizado y operaciones JWT no se presentan falsamente como globales.
- Contar solicitudes con HttpTestingController y navegador simulado: una sola inicialización por recurso; catálogos del editor/pestañas se consultan cuando se utilizan; escrituras invalidan lecturas necesarias. Pruebas con errores, latencias y respuestas desordenadas.
- Reportes: catálogo real del contrato, familias, fechas/columnas, abrir ejecución, PDF/Excel, historial y programación. Envíos y voz se simulan; no correos reales.
- Asistente: cambiar modo conserva conversación, solo existe un componente, cambios de contexto invalidan respuesta previa y cerrar no genera otra petición.
- Compilar con `npm run build`, suites focalizadas de navegación/rendimiento y suites de Reportes/Backup. Registrar fallos preexistentes antes de atribuirlos al cambio; las dos aserciones de textos de Backup detectadas en la intervención retirada se reevaluarán contra el estado actual.
- Medir antes/después bajo las mismas condiciones. Meta verificable: eliminar duplicados identificados, reducir solicitudes/bytes iniciales en flujos bajo demanda y no introducir regresiones; reportar latencia residual por endpoint sin inventar mejoras SQL.
- Revisar diff final: cero cambios en backend/móvil/base de datos; conservar modificaciones previas del usuario. Actualizar documentación de arquitectura solo cuando se implemente el patrón, distinguiendo propuesta de resultado validado.

## 10. Estado de esta entrega

El usuario aprobó la implementación. Se completó la intervención frontend/documentación y sus comprobaciones locales: [implementación, patrones, resultados y límites](decisiones/2026-10-05-frontend-navegacion-rendimiento.md). Backend, autenticación y SQL permanecen intactos. La validación con actores reales y la optimización SQL constituyen comprobaciones posteriores en un entorno autorizado; no se simula haberlas ejecutado.
