# Restricciones efectivas de suscripción

## Solicitud y alcance previo a implementación
Aplicar las reglas acordadas: Básico 5 usuarios/2 obras, Profesional 15/10, Empresarial 50/30; todos los módulos de gestión y CRM en los tres. Reportes básicos operativos sin exportación; Profesional reportes financieros y exportación manual; Empresarial además automatización/envíos y asistente IA, 500 consultas/mes calendario America/La_Paz compartidas. Sin pagos.

## Contexto revisado
Arquitectura general, BD e inventario/rutinas de usuario/obra; arquitectura y operación de reportes y backups. Rutas, servicios y repositorios de suscripciones, usuarios, registro público, obras, IA (unificada y CRM), autorización/reportes/worker; Angular shell/asistente/reportes y cliente Dio Flutter. Se conserva trabajo local anterior de presupuesto y auth.

## Capas, contratos, tenant y decisión
- Política común en services, SQL en repos. Restricción de escrituras HTTP desde la dependencia autenticada (antes de handlers que capturan excepciones); no cambia JWT, epoch, mantenimiento, backups, credenciales ni RBAC.
- SQL incremental: capacidades por plan, consumo mensual IA y triggers de cupo en usuarios/obras para cubrir registro, alta, transferencia y reactivación por cualquier cliente. Exclusión del rol global en cupo de usuarios; las altas administrativas para una empresa respetan su cupo. Obras PLANIFICACION/ACTIVO/PAUSADO consumen cupo; FINALIZADO/CANCELADO no. Usuarios ACTIVO consumen cupo. Se conserva edición al exceder cupo; no se borran registros.
- Sin plan/programada/suspendida/cancelada o vencida tras 7 días: negocio solo lectura. Perfil, contraseña, login y consulta/administración global de suscripciones conservados. Empresa técnica CLIENTES SIN EMPRESA no recibe suscripción comercial y su registro de identidad sigue posible; no obtiene acceso de escritura a negocio.
- Aprovisionar Básico sin vencimiento a empresas comerciales sin plan y a nuevas empresas; preservar planes existentes e historial. No rebajar ni suspender ninguna cuenta por datos existentes.
- IA bloqueada antes de cualquier llamada a proveedor, incluidos aliases y fallback de interpretación. Reserva atómica persistida antes del proveedor, liberada ante fallo; una solicitud lógica cuenta una vez, no cada llamada interna. Global exento. Voz exige IA empresarial y consume cupo para evitar bypass por transcripción.
- Reportes revalidan plan en catálogo, generación, exportación, archivos, envíos, programación y worker existente. Después de downgrade se conservan reportes históricos en lectura con permisos de recurso; exportación/envío y nuevas generaciones obedecen plan actual. Worker no se inicia ni envía durante validaciones.
- Contrato aditivo en suscripciones con capacidades, consumos y solo_lectura. Angular informa cupos/reglas y errores; Flutter interpreta detail/code sin invalidar sesión por 403/409/429. Backend es autoridad para ambos.

## Validación prevista
Inspección real de solo lectura de objetos, estados y rutinas antes de migrar. Pruebas aisladas de bordes de gracia, IA concurrente/cupo, reportes y acceso cruzado. PostgreSQL de pruebas solo en esquema aislado explícito con rollback/limpieza y sin invocar funciones de negocio externas. Aplicar migración únicamente a `obras` ya designada y comprobar catálogo/consumo sin usar IA ni ejecutar envíos. Compilar Angular y comprobaciones móviles disponibles.

## Resultado

Implementación terminada. `python backend/migrate_subscriptions.py --database obras --restricciones` se ejecutó correctamente contra la base de negocio ya designada. La migración está **aplicada**, no solo preparada. No se modificó `obratec_control`, ni se inició backend/worker/daemon, ni se hicieron llamadas a proveedores o envíos reales.

### Estado comprobado en la base real

| Empresa | Plan | Usuarios activos computables | Obras activas | IA consumida |
| --- | --- | --- | --- | --- |
| CONSTRUCTORA OBRATEC | Básico | 2/5 | 3/2 | 0 |
| CONSTRUCTORA LA ROCA | Profesional | 1/15 | 3/10 | 0 |
| CONSTRUCTORA EL GRAN PIRAI | Empresarial | 2/50 | 3/30 | 0/500 |

Los totales de usuarios registrados siguen siendo 5, 2 y 2 respectivamente; los cupos excluyen inactivos y administradores globales. Las tres obras existentes de OBRATEC se conservan y pueden editarse, pero no se agrega o reactiva una cuarta mientras no se libere capacidad o cambie el plan. Empresa técnica CLIENTES SIN EMPRESA sigue sin plan comercial. Fechas de inicio de suscripciones: 2026-10-24, sin fin hasta que el administrador lo establezca.

### Implementación concreta

- Nuevas capacidades de plan, contadores de recursos y tabla de consumo mensual con PK empresa/mes. Provisionamiento Básico transaccional para empresas nuevas, sin cambiar planes ya asignados. Altas y reactivaciones reservan cupo con UPDATE condicional bajo lock de fila; transferencias bloquean contadores en orden fijo. Ante error, persona/usuario/obra/contadores se revierten en la misma transacción. Las bajas liberan cupo; no hay limpieza automática de registros.
- La política de escritura evalúa fecha final inclusiva y siete días posteriores de gracia. Suspensión/cancelación/programación futura/sin plan bloquean escrituras sin gracia. Global puede administrar sin suscripción, pero los usuarios globales no consumen plazas; crear trabajadores/obras para una empresa sigue sujeto al cupo SQL de destino.
- La API publica estado efectivo, `solo_lectura`, `gracia_hasta`, límites y consumos. Errores comerciales normalizados como `detail` y `code`: 403 por función/reporte/solo lectura, 409 por cupos, 429 por IA. El normalizador reconoce códigos envueltos por handlers/rutinas antiguos sin exponer contexto SQL.
- Todas las escrituras HTTP autenticadas de negocio pasan por la política común, incluyendo aliases sin `/api`. Lecturas existentes y cuidado de cuenta se conservan. Se valida en BD estado/empresa/rol actuales del usuario contra el JWT; no se modifica su formato ni la coordinación de sesiones globales.
- Se corrigió persistencia y lectura del estado ACTIVO/INACTIVO en gestión de usuarios. Se reutilizó su formulario existente; no se agregó un flujo paralelo. Las rutas exigen permisos de usuarios y el repositorio valida pertenencia antes de editar persona/usuario. Roles numéricos recibidos como texto se normalizan para impedir asignaciones globales que evadan cupo. Un administrador de empresa no modifica/elimina un administrador global.
- El registro público ignora el rol solicitado y no permite adherirse a una empresa existente con usuarios por su nombre; requiere alta administrativa. Esto cierra un camino para omitir autorización/cupos mediante una asignación de rol global. La primera cuenta de empresa nueva usa el rol empresarial existente; no se migraron roles/grants.
- Perfil permanece disponible para datos propios, pero siempre deriva persona/empresa desde el usuario autenticado. Cambiar descripción empresarial exige administrador y suscripción editable, evitando usar la excepción de perfil como escritura de negocio en modo lectura. La conexión del repositorio ahora se cierra también en este flujo.
- Se corrigió el retorno faltante al obtener una conexión saludable del pool: antes se pedía una segunda conexión sin devolver la primera. La validación frecuente de suscripción necesitaba evitar ese agotamiento; prueba aislada confirma una adquisición/devolución por apertura normal.
- Reportes básicos: stock, consumo de materiales, asignación/carga de personal, avances, unidades e incidencias. Profesional agrega presupuestario, comparativo de costos, costos por período y saldo comercial, con PDF/Excel. Empresarial añade envíos/programaciones. Las definiciones existentes siguen siendo el catálogo determinista; nuevas definiciones futuras requieren clasificación deliberada en la política.
- Cada solicitud IA, incluida transcripción de servidor y la opción explícita `usar_ia`, consume una unidad al completar. Una solicitud unificada puede realizar varias llamadas internas y sigue contando una sola vez. Fallos que se propagan liberan la reserva; respuestas de aclaración o fallback cuentan como solicitud atendida. Una caída abrupta del proceso conserva la reserva, lo cual evita exceder cupo por reintentos inciertos. Cambiar o renovar plan no reinicia el consumo del mes. Global está exento.
- Angular oculta lanzadores/menú IA sin capacidad, informa cupos y solo lectura/gracia y deshabilita nuevas generaciones de reportes sin escritura. Flutter Reportes usa acciones del catálogo para ocultar IA/voz y preparación en solo lectura. Dio conserva su manejo de 401 y muestra `detail` para restricciones; no se invalida sesión por un 403/409/429 comercial.

### Validación ejecutada

- Backend: **139 pruebas aprobadas**, más 9 subtests, en `test_suscripciones.py`, `test_suscripcion_restricciones.py`, `test_security_rules.py`, `test_reportes.py`, `test_reportes_personalizacion.py`, `test_reportes_api.py`, `test_assistant_queries.py`. Sin BD/proveedores/correos reales; tests de aplicación desactivan Backup explícitamente para no registrar escritores en control. Cobertura de gracia (día 0/1/7/8), permisos, acceso cruzado, reportes tras downgrade, IA sin invocar proveedor en planes excluidos, reserva/reembolso, worker bloqueado y errores de rutinas legacy.
- PostgreSQL: **16 comprobaciones aprobadas** mediante `.venv/Scripts/python.exe backend/check_subscription_constraints.py --database obras`. Crea exclusivamente `codex_suscripciones_prueba_20261024`, con tablas mínimas y las migraciones reemplazando el esquema; no clona ni modifica datos de negocio. Comprueba altas, inactivos, reactivación, rol global, transferencias y rollback ante rechazo, downgrade sin borrado, gracia y dos altas simultáneas por último cupo. Dos reservas IA simultáneas con uso 499 dieron exactamente un éxito y un rechazo; total 500. El esquema de prueba se eliminó al finalizar.
- Postflight real de solo lectura: `.venv/Scripts/python.exe backend/verify_subscriptions.py`. Verificó planes 5/2/0, 15/10/0, 50/30/500; contadores coincidentes con registros actuales, historial, consulta propia, denegación cruzada y de IA para Profesional antes de proveedor/reserva. Consumo real permaneció cero.
- Angular: **48 pruebas aprobadas**: 25 de Reportes/asistente, 20 de navegación/lecturas/rendimiento y 3 de suscripciones. Incluyen IA oculta aunque haya permisos de módulos, banner de solo lectura, consulta propia y edición de plan con error recuperable.
- Angular: builds development y producción correctos. Advertencias existentes de CSS, importación sin uso en proyecto-detalle y Leaflet CommonJS; sin errores de compilación. `git diff --check` correcto.
- Flutter: revisados y ajustados los consumidores de Reportes y su cliente Dio. `flutter`/`dart` no disponibles en PATH, por lo que **no se ejecutó compilación/análisis móvil**.

### Operación, reversión y límites

Código actualizado en el workspace, sin commit/push/despliegue. Para usarlo, recargar o reiniciar el backend local y servir la compilación Angular nueva. Las tablas/triggers ya están instalados en la BD configurada; otro backend que siga usando esa BD también recibe los cupos SQL, pero necesita el código nuevo para aplicar toda la política HTTP/reportes/IA y sus mensajes.

No hay pagos, precios, facturas, mails de renovación ni workers nuevos. Las acciones iniciadas antes de un cambio de plan pueden terminar con la reserva ya aceptada; se revalida plan en nuevos accesos y antes de envíos externos. Los permisos por recurso siguen siendo necesarios además del plan. El propietario PostgreSQL puede alterar tablas/triggers; esto no implementa aislamiento contra el propietario ni RLS.

Una reversión exige preservar contadores, consumo e historial y coordinar código/SQL. No se ejecutó rollback de la migración. Eliminar tablas o deshabilitar triggers requiere una operación posterior explícita; revertir solo el código no retira los cupos instalados. No se borraron datos ni se archivaron obras automáticamente para ajustarlas a un plan.
