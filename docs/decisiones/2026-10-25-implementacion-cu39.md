# Implementación CU39

## Solicitud y alcance
Completar HU131–HU134 en API, Angular y Flutter, corrigiendo los hallazgos de la revisión CU39 del mismo día. Preservar cambios de usuario existentes.

## Contexto previo
Se revisaron arquitectura general, arquitectura de base, inventario/rutinas de obras y permisos, revisión CU39, wrapper PostgreSQL, servicios y repositorios de obras/incidencias/bitácora, rutas actuales y los clientes Web/Móvil.

## Capas, contratos y autorización previstos
Mantener routes → services → repos → PostgreSQL. Cabeceras de cronogramas con versión de concurrencia y actividades con tipo ACTIVIDAD/HITO, fechas previstas/reales, avance y dependencias fin-inicio dentro del mismo cronograma. Validar fechas, progreso, referencias y ciclos. Consultar por solapamiento de período y derivar días de retraso respecto a fecha de corte Bolivia; no predicción IA ni actualización de OT.

Servicios validan JWT, empresa real de obra y actor/permiso antes de operar. ADMINISTRADOR global es excepción explícita; ADMINISTRADOR_EMPRESA sigue aislado. Jefe puede crear/actualizar cronogramas; Supervisor planifica actividades/hitos y consulta. Permisos separados de cabecera y planificación, registrados idempotentemente sin conceder capacidades a otros roles. Conservar barreras de mantenimiento/suscripción; revisar mapeo de ruta a módulo obras.

Repositorio usa una transacción por escritura, bloqueo de cabecera, versión optimista y auditoría en la misma conexión; sin commit parcial. Cambios de dependencias validan todo el grafo bajo ese bloqueo. No modificar wrapper compartido. Migración incremental separada; inspección actual de catálogos de solo lectura antes de determinar compatibilidad. Migración preparada no equivale a aplicada; aplicar a base real solo con destino designado.

Angular y Flutter comparten contrato /api/obras/{id}/cronogramas, editor de cabecera y actividades/dependencias, filtros y retrasos. Acceso visible desde detalle de obra; mantener estilo existente sin rediseño global.

## Validación prevista
Pruebas aisladas de aislamiento/actor/contexto incompleto, rangos temporales, grafo/ciclos, retrasos, rollback/commit/concurrencia y enrutamiento. Build Angular y análisis Flutter. Comprobar catálogos actuales sin ejecutar funciones de negocio. No realizar pruebas con escrituras en base desconocida.

## Implementación y resultados
Se implementaron contratos estrictos Pydantic y API completa de agregado: cabecera, actividades/hitos, dependencias, ejecución, consulta por período y retrasos. Autorización en servicios exige actor permitido, permiso persistido y empresa real de obra; el administrador global es la única excepción de tenant. Se integró `/api/obras` en la política del módulo `obras`. Repositorio confirma una sola transacción, bloquea cabecera, limita espera de locks, comprueba versión y audita sin commits parciales.

Angular ofrece ruta `/cronogramas`, selección de obra, acceso desde detalle, editor completo, filtros y estado de errores/conflictos sin perder el borrador. Cancela lecturas obsoletas y protege cambios de contexto/navegación. Flutter reutiliza el contrato mediante ApiClient y ofrece listado, edición, fechas, hitos, predecesoras, ejecución y filtros desde el detalle de obra. Al crear selecciona el nuevo cronograma. No se rediseñaron módulos ajenos.

### Instalación real
La inspección inicial se realizó con `default_transaction_read_only=on`: no existían tablas ni permisos CU39, ni rol Supervisor. El usuario autorizó explícitamente instalar en la base `obras` configurada. `manage_cronogramas.py --apply --database obras` confirmó la instalación en una sola transacción; no reasignó cuentas ni ejecutó operaciones de negocio. La inspección posterior independiente con transacción de solo lectura confirmó tres tablas, 23 columnas, 20 restricciones, 14 asignaciones CU39 y acceso del usuario configurado a los objetos. La migración ya está aplicada, no solo preparada.

### Validación realizada
- 21 pruebas backend aprobadas: contratos, fechas, grafo/ciclos, hitos, retrasos históricos, filtros, rol, empresa ajena y contexto incompleto; persistencia y auditoría atómicas; rollback ante fallo; versiones obsoletas; dos escrituras simultáneas (una confirma, otra recibe 409); rutas HTTP. La migración se instaló dos veces en PostgreSQL 16 aislado `127.0.0.1:55439/cu39_test`, sin duplicaciones. Se usó el código real con conexión local sustituida, sin escrituras de pruebas en la base de negocio.
- Angular: build de desarrollo y producción correctos; 6 pruebas CU39 aprobadas (ruta y obra, contrato Supervisor, cancelación de lectura, dependencias, versión de eliminación y recuperación de filtro inválido).
- Flutter: análisis de archivos funcionales modificados sin incidencias; 3 pruebas aprobadas de permisos, payload y editor Supervisor. Build Web completo correcto. El SDK advierte sobre WebAssembly en flutter_secure_storage y fuente Cupertino; no bloquea la compilación JavaScript.
- Backend local `/openapi.json` devolvió 200 con las rutas CU39 actualizadas. El acceso de navegador sin sesión a `/cronogramas` redirigió correctamente a login. No se introdujeron credenciales ni se realizó un ciclo autenticado en el navegador del usuario.
- Comprobación final de privilegios confirmó SELECT, INSERT, UPDATE y DELETE individualmente para las tres tablas nuevas. `git diff --check` pasó y no quedaron marcadores de conflicto en código. La instancia PostgreSQL de pruebas fue detenida; frontend y backend locales permanecen disponibles. Se conservan advertencias previas de Angular sobre CSS/Leaflet/importación no utilizada; no bloquean el build.

### Límites explícitos
La fecha de corte reconstruye estado/fechas de ejecución, pero el porcentaje es el último registrado, no una serie histórica. No hay predicción IA ni modificación de OT. Los usuarios deben tener su rol real asignado: se creó Supervisor, no se seleccionaron personas para ese rol. No se desplegaron cambios en Render ni se publicó una nueva aplicación móvil. Se conserva la configuración local y API_BASE_URL.

La operación reproducible y las reglas están en [OPERACION_CRONOGRAMAS.md](../OPERACION_CRONOGRAMAS.md).

### Bloqueo móvil adicional encontrado al validar
El archivo ya versionado de detalle de obra contiene dos conflictos Git sin resolver; app_config.dart contiene otro entre dos IP LAN y una variante localhost para Web. Impiden compilar Flutter y acceder a CU39. Se resuelven los bloques de detalle conservando la variante HEAD con filtros/acciones completas. Se conserva API_BASE_URL, la IP LAN de HEAD para dispositivo y localhost para Web; la URL cloud declarada sigue disponible. No se cambian contratos de unidades ni se ejecutan escrituras en sus endpoints. Se incluye la reparación porque bloquea directamente la integración móvil solicitada.
