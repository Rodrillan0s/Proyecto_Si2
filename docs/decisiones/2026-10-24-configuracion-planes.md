# Configuración administrativa de planes

## Solicitud y contexto previo
Crear sección exclusiva del Super Admin (rol real ADMINISTRADOR) para modificar planes, módulos, cupos y funciones sin editar código. Revisados arquitectura general/BD, inventario y rutinas de usuarios/obras, arquitectura/operación Reportes, rutas y política de suscripciones, contadores SQL, Angular navegación/guards/Suscripciones y consumidores Flutter. La definición de capacidades existe en BD pero no hay edición, módulos configurables ni historial de definición.

## Capas y contratos previstos
Mantener routes → services → repos → PostgreSQL. API administrativa con catálogo de módulos conocidos, previsualización de empresas afectadas, guardado confirmado e historial de antes/después. No se crean planes arbitrarios ni módulos que el producto no implemente: se configuran Básico/Profesional/Empresarial y sus módulos existentes. La previsualización devuelve confirmación vinculada al contenido, versión y empresas; guardado revalida y usa control optimista para no pisar cambios concurrentes.

## Tenant, permisos y aplicación de políticas
Solo ADMINISTRADOR global puede editar/previsualizar/ver historial global. ADMINISTRADOR_EMPRESA solo consulta su suscripción. Cambiar un plan afecta a sus empresas actuales y futuras sin cambiar asignaciones ni borrar datos. Retirar módulos deja lectura histórica y bloquea escrituras HTTP por rutas y aliases; IA y generación/exportación/envío de reportes se protegen además en servicios/worker. Usuarios/obras mantienen cupos SQL existentes. Los módulos futuros requieren implementación y registro explícitos, no cadenas arbitrarias introducidas por el administrador. Los permisos RBAC siguen siendo condición necesaria.

## Persistencia y migración
SQL incremental: módulos JSONB, versión de plan e historial de definiciones con actor y snapshots. Conservar capacidades y asignaciones actuales. Runner específico sobre `obras` designada, sin repetir la migración de restricciones que podría reponer valores predeterminados. Inspeccionar objetos reales antes de aplicar; no iniciar workers, pagos ni envíos.

## Presentación y validación prevista
Angular: Administración → Configuración de planes, acceso también desde Suscripciones para global. Selección de plan, controles de módulos/límites/reportes/IA, resumen de impacto y confirmación revisable antes de guardar, historial. Suscripciones muestra prestaciones desde la configuración actual, evitando descripciones estáticas contradictorias. Contratos aditivos: Flutter recibe la política nueva y la API deniega escrituras independientemente de sus controles locales.

Pruebas aisladas de permisos, validaciones, preview obsoleta, módulos/aliases, reportes/IA y UI. PostgreSQL con esquema de pruebas aislado y posterior comprobación real de solo lectura. Build Angular. Mantener archivos locales anteriores del usuario.

## Implementación final

- Pantalla `/configuracion-planes` bajo el shell autenticado y guard de rol ADMINISTRADOR, con entrada en Administración y enlace desde Suscripciones solo para global. Se editan nombre, descripción, módulos implementados, límites de usuarios/obras, generación de reportes NINGUNO/OPERATIVOS/TODOS, PDF/Excel, envíos/programación y cupo mensual de IA.
- API aditiva en `/api/suscripciones`: GET `/configuracion/modulos`; POST `/planes/{codigo}/previsualizar`; PUT `/planes/{codigo}` con confirmación; GET `/planes/{codigo}/historial`. Los tres endpoints administrativos y el catálogo de módulos requieren ADMINISTRADOR. Catálogo normal de planes sigue disponible para usuarios autenticados. Payload tipado estricto, módulos conocidos únicos y dependencias coherentes: IA requiere cupo positivo; sin Reportes no hay generación/exportación/automatización; automatización requiere exportación.
- Previsualización calcula empresas actuales, módulos retirados y empresas que quedarían sobre cupo. Firma SHA256 del borrador normalizado, versión y snapshot de empresas/consumos; es un control de consistencia, no una credencial ni permiso. Guardado recalcula impacto bajo lock del plan, rechaza versión/firma obsoletas con 409 y guarda definición + auditoría atómicamente. Editar borrador invalida revisión/confirmación en Angular.
- Historial por plan incluye versión, actor, timestamp, snapshots completos y empresas afectadas. La UI presenta antes/después de nombre, cupos, módulos y funciones. Una falla de auditoría revierte la edición del plan.
- Registro de 15 módulos reales en `planes_catalog.py`, con correspondencia a todas las rutas mutadoras actuales, incluidos aliases CRM/IA/inventario y subrutas de presupuestos/costos/avances bajo proyectos. Retirar un módulo bloquea sus escrituras HTTP para usuarios de sus empresas; no borra registros ni elimina lecturas con permisos. Las operaciones internas integradas siguen las reglas de sus propios flujos y permisos; no se deshabilitan triggers de negocio.
- IA y Reportes se protegen también en servicios/worker, no solo en HTTP. Se puede habilitar IA en Básico o Profesional si el administrador lo decide y asigna cupo. La reserva SQL comprueba módulo IA y vigencia. Cupo mensual consumido no se reinicia al editar el plan. El catálogo/acciones de Reportes refleja la configuración actual y los permisos.
- Suscripciones publica módulos y versión, muestra módulos no habilitados y mantiene el nombre vigente. Las prestaciones guardadas se regeneran desde los módulos seleccionados para evitar listar funciones retiradas. Para empresas sin suscripción, los módulos provenientes del LEFT JOIN pueden ser NULL; el listado los interpreta como vacíos y conserva el estado SIN_PLAN sin fallar.
- No se agregan roles ni grants. El global conserva su administración; el plan nunca concede permisos RBAC ni autoriza acceso a otra empresa. Las capacidades se comprueban en cada operación; un cliente con interfaz desactualizada sigue recibiendo denegación del backend. Usuarios de sesiones ya abiertas deben recargar para reflejar nuevos indicadores visuales del shell.

## Migración aplicada y estado real

Inspección previa de solo lectura confirmó las capacidades existentes y ausencia de `t_plan_suscripcion_historial`. Se ejecutó `python backend/migrate_subscriptions.py --database obras --configuracion`, **aplicado correctamente**. Agregó módulos/versión/fecha e historial; conservó Básico 5/2/0, Profesional 15/10/0 y Empresarial 50/30/500. IA inicialmente solo en Empresarial. OBRATEC sigue Básico, La Roca Profesional y El Gran Piraí Empresarial. No se hicieron ediciones administrativas reales: versiones iniciales 1 e historial vacío confirmados después.

El flag `--configuracion` se ejecuta por separado de seed/restricciones para no restablecer capacidades. El SQL de restricciones también se protege de sobrescribir planes que ya tengan la columna de versión. Reaplicar configuración solo inicializa módulos NULL, conservando ediciones existentes.

## Validación realizada

- **173 pruebas backend** aprobadas más 9 subtests: configuración de planes, suscripciones/restricciones, seguridad, reportes, contratos/API, personalización y asistente. Incluye permisos de empresa frente a global, coherencia de módulos/límites, preview obsoleta por cambios de datos/versión/empresas, rutas y aliases protegidos, lectura histórica, IA configurable en Básico, empresa técnica sin plan y cobertura de todas las rutas mutadoras actuales.
- **57 pruebas Angular** aprobadas: 12 de configuración/Suscripciones, 25 de Reportes/asistente y 20 de navegación/lecturas/rendimiento. Revisión sin guardado automático, confirmación requerida, edición invalida preview, conflicto conserva borrador, mensajes de validación y capacidades dependientes.
- **20 comprobaciones PostgreSQL** aprobadas en el esquema aislado `codex_suscripciones_prueba_20261024`, eliminado al finalizar. Incluye pruebas existentes de cupos y concurrencia, edición de definición, auditoría completa, reaplicación sin reponer límites y rollback del plan cuando falla la FK del actor de auditoría. No modificó empresas/usuarios/planes de negocio.
- Postflight `.venv/Scripts/python.exe backend/inspect_plan_configuration.py --verificar`: consulta real de solo lectura confirmó columnas nuevas, versiones 1, módulos iniciales, historial vacío y previsualización de Básico (una empresa afectada, actualmente sobre cupo de obras).
- Postflight `.venv/Scripts/python.exe backend/verify_subscriptions.py`: API/SQL reales en solo lectura confirmó asignaciones, cupos, aislamiento y bloqueo IA de Profesional, con consumo real cero. Encontró el caso NULL de empresa técnica en el primer intento; se corrigió y se agregó regresión, luego pasó completo.
- Builds Angular development y producción correctos. Se mantienen advertencias previas de CSS, importación de presupuesto sin uso y Leaflet CommonJS; sin errores. `git diff --check` correcto.
- Flutter conserva su contrato y manejo de denegaciones; recibe módulos/capacidades aditivos. No se agregó editor móvil para administración global. El SDK no está disponible en PATH y no se compiló Flutter.

## Operación y límites

Código listo en el workspace, sin commit/push ni despliegue. Reiniciar/recargar backend local y actualizar Angular para ver la sección. No se iniciaron backend, worker, daemon ni envíos; no se llamó a proveedores IA ni se consumieron consultas reales.

No se crean módulos arbitrarios ni un constructor de funcionalidad: agregar un módulo nuevo al producto requiere implementar sus rutas y registrar su política. Bajar límites conserva datos sobre cupo y solo impide nuevas altas/reactivaciones; retirar módulos mantiene lectura autorizada. Gracia y estados de suscripción conservan las reglas existentes.

La previsualización refleja el snapshot observado; los conteos pueden variar con operaciones concurrentes y nuevos cambios de plan requieren revisión. Los cambios aplican a futuras solicitudes; no cancelan operaciones ya iniciadas. No hay notificaciones externas automáticas ni pagos. El historial es persistente de aplicación, sin defensa frente a SQL directo del propietario.

Una reversión necesita coordinar código/migración y preservar definiciones e historial. No se borraron tablas ni se revirtieron capacidades reales. Restaurar valores iniciales requiere una edición administrativa explícita con su revisión e historial; volver a ejecutar restricciones no los sobrescribe.
