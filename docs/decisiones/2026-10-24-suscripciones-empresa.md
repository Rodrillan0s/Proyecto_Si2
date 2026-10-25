# Suscripciones manuales por empresa

Evolución del mismo trabajo: [restricciones ya implementadas y migración aplicada](2026-10-24-restricciones-suscripciones.md). Esta nota conserva el estado de la primera entrega; las menciones a prestaciones solo descriptivas, ausencia de cuotas o ausencia de cambios móviles quedan superadas por la evolución enlazada.

## Solicitud y alcance
Tres planes (Básico, Profesional, Empresarial), compartidos por los usuarios de cada empresa. Sin pagos. Asignar ejemplos a empresas con usuarios existentes para cubrir al menos cuatro usuarios, sin crear cuentas ni cambiar roles.

## Contexto y decisión previa
Revisados arquitectura general, arquitectura de BD, inventario de usuario/empresa/roles y rutina de login; rutas, servicios y repositorios de usuarios/empresas, seguridad y clientes Angular. No existe suscripción en estos flujos. Se conservarán cambios locales anteriores de presupuesto y autenticación.

## Capas y contratos
Nuevo flujo routes → services → repos → PostgreSQL. Catálogo global de tres planes y una suscripción actual por empresa con historial de cambios. Gestión exclusiva de ADMINISTRADOR global. Lectura propia para usuarios con empresa válida comprobada contra BD, independiente de la empresa seleccionada en Angular. ADMINISTRADOR_EMPRESA no asigna planes. API aditiva: catálogo, consulta propia, listado global y asignación manual. Estado efectivo derivado de vigencia, sin workers. No cambia JWT, roles, permisos ni acceso actual a módulos; las prestaciones son descriptivas en esta primera etapa y no se anuncian cuotas implementadas.

## Presentación y compatibilidad
Pantalla dedicada `/suscripciones`, accesible desde Cuenta → Suscripción, usando estilos existentes. El administrador global ve las empresas y el formulario de asignación; los demás usuarios ven su plan y el catálogo sin controles de escritura. Contrato nuevo disponible para Flutter sin cambiar los endpoints actuales; revisado `mobile/lib/services/empresa_service.dart`, no requiere cambios para mantener su flujo. Sin pasarela, renovaciones automáticas, bloqueos ni cobros.

## Validación prevista
Inspeccionar objetos reales en la BD configurada del backend con lectura antes de migrar. Migración transaccional incremental, parámetros SQL y restricciones de fechas/estados. Pruebas aisladas de permisos, aislamiento, estados y asignación; compilación Angular. Aplicar exclusivamente nuevas tablas y asignaciones autorizadas; no ejecutar otras migraciones ni iniciar servicios.

## Implementación y validación realizada

- Inspección real de solo lectura: BD `obras`, esquema `obras`, cuenta configurada `devpoppy`. Ambas tablas principales nuevas estaban ausentes; se comprobaron columnas de empresa, usuario y rol. Empresas existentes: OBRATEC (5 usuarios), CLIENTES SIN EMPRESA (6), LA ROCA (2), EL GRAN PIRAI (2). No se extrajeron contraseñas ni correos.
- Migración **aplicada**, no solo preparada: `python backend/migrate_subscriptions.py --database obras --seed`. Tres tablas, tres planes, historial e índice. Asignaciones activas desde 2026-10-24 y sin fecha de fin: La Roca → Profesional; El Gran Piraí → Empresarial. Cubren cuatro usuarios existentes. Las demás empresas quedan sin plan. No se crean usuarios ni se asigna plan a la empresa técnica.
- Ejecutor exige nombre de BD explícito, usa transacción, bloqueo asesor y timeouts. Seed repetible con `ON CONFLICT DO NOTHING`, conserva asignaciones previas y solo registra historial de inserciones nuevas. Asignación administrativa e historial comparten transacción y bloqueo de empresa. `actualizado_por`/`id_actor` guardan actor; asignación inicial usa origen `ASIGNACION_INICIAL` y actor NULL, pues es una operación de instalación autorizada fuera de sesión.
- Estados almacenados: ACTIVA/SUSPENDIDA/CANCELADA. Consulta deriva SIN_PLAN/PROGRAMADA/VENCIDA según existencia y fechas en America/La_Paz. Fin inclusivo; NULL significa vigencia sin fecha final. No se necesitan procesos automáticos.
- API: GET `/planes`, `/mi-empresa`, `/empresas`, `/empresas/{id}/historial`; PUT `/empresas/{id}`, todos bajo `/api/suscripciones`. Historial limitado a los 50 cambios recientes. Lectura global y escritura requieren ADMINISTRADOR, nunca ADMINISTRADOR_EMPRESA. Consulta propia comprueba usuario activo y empresa actual contra JWT; rechaza contexto incompleto o discrepante.
- `PYTHONPATH=backend .venv/Scripts/python.exe -m pytest backend/tests/test_suscripciones.py backend/tests/test_security_rules.py -q`: **17 pruebas pasaron**. Sin conexión ni escrituras: aislamiento, permisos, contrato, fechas, plan/empresa inexistentes y actor.
- `npx.cmd ng test --watch=false --ts-config=tsconfig.suscripciones.spec.json --include=src/app/pages/suscripciones/suscripciones.spec.ts`: **3 pruebas pasaron**. Consulta propia, asignación a empresa elegida y recuperación de error.
- `npm.cmd run build -- --configuration development` y `npm.cmd run build`: ambos correctos. Producción requirió red para fuentes Google existentes. Persisten advertencias anteriores de tamaños CSS, Leaflet CommonJS y componente de presupuesto importado sin uso; sin errores.
- `.venv/Scripts/python.exe backend/verify_subscriptions.py`: API montada con TestClient y repositorio SQL real, conexión forzada a solo lectura. Confirmó tres planes, dos suscripciones activas, cuatro usuarios cubiertos, historial, consulta propia y 403 para acceso cruzado/listado global/escritura de administrador de empresa. No inicia la app completa ni procesos/envíos.
- Se instaló pytest en `.venv` para pruebas; no se cambió el manifiesto de dependencias de producción. Advertencias de deprecación del TestClient existente, sin fallos.

## Operación y límites

Reiniciar el backend local si no tiene recarga automática y abrir Cuenta → Suscripción. No se ha desplegado código al servidor. Los cambios de esquema y asignaciones ya existen en la BD configurada; otros entornos requieren ejecutar la migración señalando su nombre explícitamente. La pantalla nueva requiere la API nueva.

La suscripción registra clasificación comercial y vigencia. Las prestaciones del catálogo son descriptivas: no implementa límites ni bloquea módulos, cuentas o inicios de sesión por plan/expiración. Se conserva autorización por rol y recurso. No hay precios, facturas, pagos ni renovaciones automáticas. Flutter conserva sus funciones actuales y puede consumir la API nueva; no se agregó una pantalla móvil.

Reversión de código: retirar ruta/entrada de menú y router nuevos. Retirar tablas requiere una operación posterior expresamente autorizada, exportando primero asignaciones/historial; no se ejecutó reversión ni borrado de datos. El historial registra cambios del módulo, sin protección append-only ante SQL directo del propietario.
