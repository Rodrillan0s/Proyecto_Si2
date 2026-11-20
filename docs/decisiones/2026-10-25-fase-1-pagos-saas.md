# CU37 Fase 1: inicio y consulta de pagos SaaS con Stripe Test

## Alcance

Implementar solo backend para HU124 y la base persistente de HU125/HU126: catálogo comercial de precios, creación idempotente de un pago pendiente, creación de Stripe Checkout Session en modo prueba y consulta protegida del intento. No se implementan frontend, webhook, confirmación/aplicación de pagos, migrador automático, renovación ni cambio de plan en esta fase.

## Arquitectura y contratos

Se conserva `routes → services → repos → PostgreSQL`. `pago_routes` tipa el contrato HTTP y exige roles; `pago_services` revalida usuario, rol y empresa en base, toma el precio exclusivamente del servidor y coordina idempotencia; `pago_repos` contiene SQL parametrizado; `stripe_gateway` encapsula el SDK y rechaza claves/sesiones que no sean de prueba.

`obras.t_plan_precio_saas` mantiene una configuración comercial activa por `codigo_plan`. `obras.t_pago_suscripcion` conserva el snapshot inmutable de versión, importe, moneda y período. Se relaciona por `id_empresa` con la suscripción vigente de CU33 y por `codigo_plan` con su catálogo. CU33 continúa siendo autoridad de vigencia y estado; esta fase no actualiza `t_suscripcion_empresa` ni inserta `t_suscripcion_historial`.

## Tenant, permisos y seguridad

Solo `ADMINISTRADOR_EMPRESA` puede iniciar Checkout. `id_empresa` se deriva del usuario autenticado y se contrasta con usuario activo, rol y empresa actuales en PostgreSQL; el cuerpo acepta únicamente `codigo_plan`. `ADMINISTRADOR_EMPRESA` puede consultar solo pagos de su empresa y `ADMINISTRADOR` puede consultar cualquier pago. Los demás roles se rechazan.

`/api/pagos` se considera cuidado de cuenta y se exceptúa de la barrera general de escritura de suscripciones para permitir renovar desde solo lectura; cada endpoint conserva autorización explícita. No se reciben ni almacenan tarjetas. La clave secreta solo se usa en backend. El adaptador exige `sk_test_`, una Checkout Session `cs_test_` y `livemode=false`.

## Idempotencia y transacciones

El cliente aporta `Idempotency-Key` en cabecera. La clave es única localmente y se reutiliza en el POST de Stripe. Repetir empresa, plan y clave devuelve el mismo pago/sesión; reutilizar la clave con otro tenant o plan se rechaza. La creación local y la llamada externa no son una transacción distribuida: si Stripe falla, el pago permanece `PENDIENTE` con error sanitizado y puede reintentarse con la misma clave. Las restricciones únicas de pago, Checkout Session y PaymentIntent respaldan la coordinación.

No se restringe a un único pago pendiente por empresa, según el alcance solicitado. Esta decisión permite intentos distintos simultáneos y exige que la fase de webhook/verificación posterior bloquee y aplique cada pago confirmado exactamente una vez.

## Configuración y operación

Las credenciales se leen de entorno. No se incluyen claves reales. La migración queda preparada pero no se ejecuta ni se registra en un runner. Tampoco se insertan precios arbitrarios: un plan sin fila comercial activa no puede iniciar Checkout.

## Validación prevista

Pruebas unitarias y de API con repositorio/adaptador Stripe simulados: creación pendiente, snapshot del precio, aislamiento tenant, repetición idempotente, conflicto de clave y roles. No se conecta a PostgreSQL, no se llama a Stripe, no se ejecutan migraciones y no se inicia el backend.

## Implementación y validación realizada

- Se agregaron las dos tablas e índices solicitados en una migración preparada. No se ejecutó ni se incorporó a un runner automático. No se añadieron precios semilla.
- API registrada en `/api/pagos`: `GET /planes`, `POST /checkout-sessions` y `GET /{id_pago}`. El POST acepta solo `codigo_plan` y exige `Idempotency-Key`; `id_empresa`, importe, moneda, período y actor se derivan del contexto autorizado y PostgreSQL.
- `ADMINISTRADOR_EMPRESA` inicia pagos para su empresa y consulta los propios; `ADMINISTRADOR` puede consultar por ID. Usuario, estado, rol y empresa se revalidan contra BD además del JWT. Otros roles se rechazan.
- El adaptador crea Checkout alojado en `mode=payment`, tarjeta, factura posterior habilitada y metadata mínima de conciliación. Exige clave `sk_test_`, Session `cs_test_` y `livemode=false`. No existe webhook ni transición a CONFIRMADO en esta fase.
- La clave idempotente es única en PostgreSQL y su hash se reutiliza como clave idempotente de Stripe. Repetir la misma empresa/plan devuelve la sesión existente; cambiar tenant o plan con la misma clave devuelve conflicto. No se limitan pagos pendientes por empresa.
- `/api/pagos` se agregó a las excepciones explícitas de cuidado de cuenta de la política CU33. Esto permite iniciar renovación desde solo lectura, pero no omite las comprobaciones propias de rol/tenant del módulo.
- Se agregaron placeholders sin secretos y la dependencia oficial `stripe`. Para ejecutar pruebas se completó el entorno virtual local desde `requirements.txt`; no se guardaron credenciales.
- Validación: `60 passed` en `test_pagos.py`, `test_suscripciones.py`, `test_configuracion_planes.py` y `test_security_rules.py`. Incluye pago pendiente, snapshot, tenant, idempotencia, roles, body estricto, excepción de cuidado de cuenta, parámetros del gateway y rechazo de clave live. `py_compile` correcto. Única advertencia: deprecación preexistente de TestClient/httpx.
- No se conectó a PostgreSQL, no se aplicó la migración, no se llamó a Stripe, no se inició el backend y no se hizo commit/push.

## Pendientes deliberados

Implementar en una fase posterior webhook firmado, verificación administrativa, transiciones terminales, aplicación atómica a CU33, historial/listado de pagos y comprobantes. La tabla ya reserva los campos necesarios para esas operaciones.

## Operación de base autorizada (2026-10-25)

Antes de aplicar la migración se comprobó en modo de solo lectura la base PostgreSQL configurada por el backend: existen las tres tablas de CU33, sus claves son compatibles con las FK preparadas, están presentes los planes `BASICO`, `PROFESIONAL` y `EMPRESARIAL`, y las tablas de CU37 todavía no existen. La operación autorizada consiste exclusivamente en ejecutar `20261025_pagos_saas.sql` y configurar precios TEST 1:1 con esos planes: 9900, 24900 y 49900 unidades menores BOB respectivamente, período de un mes, activos y versión 1. No modifica filas ni contratos de CU33.

La aplicación y la carga se ejecutarán en una sola transacción, con `lock_timeout` y `statement_timeout`, verificación previa de los tres planes y `INSERT ... ON CONFLICT DO UPDATE` acotado a las filas comerciales. Después se comprobarán tablas, restricciones, índices, FK y relación con el catálogo, y se repetirán las pruebas aisladas de pagos. Webhook, frontend y cualquier cambio de vigencia de CU33 permanecen fuera del alcance.

## Resultado de la operación

La transacción fue confirmada en PostgreSQL 17.11, base `obras`. El catálogo posterior confirma las dos tablas, 8 y 27 columnas respectivamente, todas las restricciones validadas y los dos índices de consulta solicitados. Los tres precios se relacionan con `t_plan_suscripcion`, no existen precios huérfanos y el ledger permanece sin pagos. La regresión aislada de pagos, suscripciones, configuración de planes y seguridad finalizó con 60 pruebas aprobadas y una advertencia preexistente de deprecación Starlette/httpx. No se modificaron tablas ni filas de CU33, y no se ejecutó Stripe.

## Preparación operativa de HU124

`backend/.env` quedó con placeholders vacíos para las cinco variables Stripe, sin incluir credenciales ni URLs inventadas. El adaptador conserva tres barreras de Test Mode: exige secreto `sk_test_`, exige Session `cs_test_` y rechaza `livemode` distinto de `false`; la tabla también impide persistir `stripe_livemode=true`.

Se levantó el backend localmente y `GET /api/pagos/planes`, autenticado como un `ADMINISTRADOR_EMPRESA` activo con suscripción, respondió HTTP 200 con los tres planes y sus precios configurados. El POST real no se envió porque las variables Stripe permanecen vacías para carga manual; hacerlo así crearía un pago pendiente sin poder obtener Checkout Session. Se comprobó que el ledger continúa con cero pagos y cero sesiones almacenadas. Las 9 pruebas aisladas de pagos aprobaron; permanece la advertencia preexistente de Starlette/httpx.

## Corrección TLS para Stripe Test

La prueba real posterior confirmó que el entorno virtual usa un `certifi` actualizado y un bundle existente, pero Requests no puede construir la cadena del certificado presentado por la red local para `api.stripe.com`. No existen overrides `SSL_CERT_FILE`, `REQUESTS_CA_BUNDLE` ni proxies declarados. Se integrará `truststore` para que Python/Stripe consulte el almacén de CA confiables del sistema manteniendo verificación TLS estricta; queda prohibido `verify=false`, un contexto SSL no verificado o un bundle descargado sin procedencia.

La inicialización de confianza pertenecerá al adaptador de Stripe, antes de importar el SDK, y deberá ser idempotente. Se validará primero HTTPS sin autenticación y luego se repetirá el POST con la misma clave idempotente y el mismo pago pendiente para no duplicar registros. La regresión comprobará que Test Mode continúa exigiendo `sk_test_`, `cs_test_` y `livemode=false`.

La primera solicitud que alcanzó Stripe después de corregir TLS reveló una segunda condición: `expires_at` se calculaba en cada llamada, por lo que un reintento con la misma clave idempotente llevaba parámetros distintos y Stripe lo rechazaba. Para conservar el contrato idempotente, la expiración se reservará al insertar el pago pendiente y el adaptador reutilizará ese valor estable. La clave de la prueba fallida no se reutilizará; una nueva clave creará un intento independiente, permitido por el modelo, sin eliminar ni ocultar el registro fallido previo.

La prueba con expiración estable alcanzó la API y confirmó que la versión actual de Stripe rechaza `payment_method_types` al crear Checkout Session; los métodos habilitados se resuelven desde la configuración de Stripe. El adaptador retirará ese parámetro obsoleto y conservará `mode=payment`, metadata, importe del snapshot, factura, URLs y las barreras de Test Mode.

La validación final confirmó el bundle de `certifi`, HTTPS verificado contra `api.stripe.com`, 10 pruebas aisladas aprobadas y compilación correcta. El POST real respondió HTTP 201 y persistió un pago Profesional `PENDIENTE` por 24900 BOB, Session `cs_test_`, `livemode=false`, URL y expiración, sin completar el Checkout. Los intentos diagnósticos anteriores permanecen como pagos pendientes sin sesión y con error registrado; no se eliminaron ni se aplicaron a CU33.

## HU125: confirmación y aplicación transaccional

Se agregan dos entradas backend sin frontend: webhook público firmado `POST /api/pagos/webhooks/stripe` y verificación administrativa `POST /api/pagos/{id_pago}/verificar`. El webhook acepta exclusivamente los eventos `checkout.session.completed`, `checkout.session.async_payment_succeeded`, `checkout.session.async_payment_failed` y `checkout.session.expired`; la verificación exige `ADMINISTRADOR` y consulta Stripe, nunca recibe ni permite declarar un estado pagado desde el cuerpo.

`stripe_gateway` verifica la firma con `STRIPE_WEBHOOK_SECRET`, rechaza eventos/sesiones live y obtiene Checkout Session y PaymentIntent directamente de Stripe cuando se necesita confirmar. Antes de mutar se contrastan contra el snapshot local: ID de pago, empresa, plan, versión, Session, `client_reference_id`, importe total/recibido, moneda, PaymentIntent y estado `paid`/`succeeded`. Los eventos completados aún no pagados permanecen pendientes; fallo asíncrono pasa a `FALLIDO` y expiración a `CANCELADO`, sin tocar CU33.

La confirmación se ejecuta en una sola transacción PostgreSQL: `SELECT ... FOR UPDATE` del pago y luego de `t_suscripcion_empresa`, determinación de aplicación, actualización de la suscripción, inserción de historial `PAGO_STRIPE` y transición del pago a `CONFIRMADO` enlazando el historial. Un pago ya aplicado retorna idempotentemente sin crear otro historial; las restricciones únicas de evento, Session, PaymentIntent e historial respaldan carreras entre webhook y verificación manual.

Reglas de vigencia: mismo plan en estado `ACTIVA` es `RENOVACION`; si tiene fin vigente se amplía ese fin por `periodo_meses`, y si está vencido o tenía vigencia abierta el nuevo período se calcula desde hoy. Mismo plan suspendido/cancelado es `CONTRATACION` y reactiva desde hoy. Un plan distinto es `CAMBIO_PLAN`, activo desde hoy. Contratación y cambio terminan el día anterior al mismo día calendario tras los meses pagados; CU33 sigue siendo la autoridad persistente de estado y vigencia.

La validación prevista es aislada, sin pagos reales: firma/ruteo simulado, confirmación correcta, evento duplicado, fallido/cancelado sin escritura CU33, verificación exclusiva de administrador y reglas de renovación/cambio. No se ejecutarán migraciones.

## Resultado HU125

Se implementaron ambos endpoints y los cuatro eventos. La confirmación valida Session y PaymentIntent contra el snapshot, mantiene Test Mode y aplica pago/suscripción/historial en una sola transacción bloqueada. La verificación administrativa siempre consulta Stripe; no acepta cuerpo ni estado aportado por el cliente. Fallo y expiración solo cambian el ledger.

La regresión aislada finalizó con 69 pruebas aprobadas entre pagos, CU33, configuración de planes y seguridad; `py_compile` y `git diff --check` fueron correctos. No se invocaron webhooks reales, no se completaron pagos y no se ejecutaron migraciones. El entorno local aún requiere configurar `STRIPE_WEBHOOK_SECRET` con el secreto del endpoint Stripe Test antes de aceptar firmas reales. Persiste una advertencia preexistente de deprecación Starlette/httpx.

## Compatibilidad con Stripe SDK v16

La verificación real del pago 4 detectó que Stripe SDK v16 expone la conversión recursiva de `StripeObject` como `_to_dict_recursive`, mientras el adaptador solo reconocía el nombre anterior `to_dict_recursive`. La Session y el PaymentIntent estaban pagados y contenían metadata, pero el normalizador los convertía en diccionarios vacíos y la barrera de conciliación respondía 409 correctamente sin modificar CU33.

Se ampliará exclusivamente el adaptador para aceptar diccionarios, mappings y ambos nombres de conversión del SDK, sin relajar la validación de `id_pago`, `id_empresa`, `codigo_plan` ni `version_precio`. La prueba prevista incluye un doble de `StripeObject` v16 y dos verificaciones administrativas reales del pago 4; la segunda debe reutilizar el historial enlazado y no extender nuevamente la vigencia.

La corrección quedó aplicada y cubierta por una prueba específica de `StripeObject` v16. La Session y el PaymentIntent reales volvieron a exponer los cuatro campos y coincidieron con el snapshot. Dos llamadas administrativas consecutivas sobre el pago 4 respondieron HTTP 200: la primera lo marcó `CONFIRMADO`, guardó PaymentIntent y `aplicado_en`, cambió la suscripción de Empresarial a Profesional e insertó el historial `PAGO_STRIPE`; la segunda devolvió `aplicado=false`, el mismo historial y el mismo conteo. No se creó otra Checkout Session ni se completó otro pago.

## HU126: historial propio y comprobantes

Se agregarán dos lecturas backend sobre el ledger existente, sin cambiar el esquema ni consultar Stripe. `GET /api/pagos/mi-empresa` será exclusivo de `ADMINISTRADOR_EMPRESA`: el servicio revalidará que el usuario continúa activo con el mismo rol y empresa del JWT, y el repositorio filtrará obligatoriamente por ese `id_empresa`. La respuesta usará el snapshot comercial del pago, el nombre del catálogo y referencias Stripe ya persistidas, ordenada desde el intento más reciente.

`GET /api/pagos/{id_pago}/comprobante` permitirá al administrador de empresa consultar solo recursos de su tenant y al `ADMINISTRADOR` consultar cualquier empresa. La autorización por recurso se mantendrá en el servicio después de recuperar el pago, sin aceptar `id_empresa` del cliente. El comprobante será una proyección limitada a identificador, plan, monto, moneda, estado, confirmación, Session, PaymentIntent y recibo; no expondrá idempotencia, errores internos, actores ni URLs ajenas al contrato.

Se preserva `routes → services → repos → PostgreSQL`. Las pruebas serán aisladas y cubrirán historial propio, filtro tenant, comprobante, acceso global y rechazo 403 entre empresas. No se ejecutarán migraciones, no se llamará a Stripe y no se modificará frontend ni CU33.

La implementación quedó completada con ambos endpoints de lectura. El historial se filtra en SQL por la empresa autenticada y devuelve plan, snapshot monetario, estado, fecha y referencias Stripe persistidas; el comprobante aplica autorización por recurso y devuelve solo su proyección pública. La regresión aislada de pagos, CU33, configuración de planes y seguridad finalizó con 76 pruebas aprobadas; `py_compile` y `git diff --check` también fueron correctos. Persiste una advertencia preexistente de deprecación Starlette/httpx. No se ejecutaron migraciones, no se consultó Stripe y no se modificó frontend.

## Frontend CU37

La interfaz Angular se integrará como una evolución conservadora del shell OBRATEC: misma tipografía, paleta slate/ámbar, radios, modo oscuro, navegación declarativa y componentes standalone. No se agregarán dependencias visuales. La página `/pagos` cambiará su contenido según el rol revalidado por las rutas: `ADMINISTRADOR_EMPRESA` verá plan actual, catálogo comercial, inicio de Checkout e historial propio; `ADMINISTRADOR` podrá consultar una transacción existente por ID, abrir su comprobante y solicitar verificación al backend. El backend no expone un listado global, por lo que no se simulará una tabla global ni se ampliará el alcance de persistencia.

El frontend enviará exclusivamente `codigo_plan` y una `Idempotency-Key` nueva por intención de pago. Guardará temporalmente `id_pago` en `sessionStorage` antes de redirigir a la URL alojada por Stripe Test. `/pagos/resultado` usará el ID de query o ese contexto temporal para consultar el pago; nunca verificará, confirmará ni activará una suscripción desde el navegador. El aislamiento continúa dependiendo del JWT y de las verificaciones de recurso del backend.

La revisión contractual detectó que el historial propio no proyecta `confirmado_en`, aunque la pantalla HU126 debe mostrarlo. Se agregará esa columna a la consulta existente como corrección aditiva de lectura, sin migración ni cambio de estado. Las pruebas previstas cubren servicio HTTP, body y cabecera idempotente, planes, redirección, historial, comprobante, resultado success/cancel, menú por rol y verificación exclusiva del administrador global. Se ejecutarán las pruebas frontend y el build de producción.

El frontend quedó implementado con servicio HTTP tipado, clave idempotente reutilizable durante reintentos de una misma intención, contexto temporal de retorno en `sessionStorage`, vistas por rol, modal de comprobante y estados de carga, vacío y error. El menú y las rutas usan `roleGuard`; ningún secreto Stripe ni dato de tarjeta se incorpora al cliente. La consulta del historial ahora incluye `confirmado_en`. No se agregó un listado administrativo global porque el backend no ofrece ese contrato; el administrador consulta y verifica por ID mediante los endpoints existentes.

Validación final: 11 pruebas CU37 y 20 pruebas de navegación aprobadas, 42 pruebas backend relacionadas aprobadas, `py_compile` correcto y build Angular de producción exitoso. El build mantiene advertencias no bloqueantes ya presentes y agrega la advertencia de presupuesto del stylesheet de pagos (8.24 kB frente a 4 kB); no hay errores de compilación. No se ejecutaron migraciones, pagos ni webhooks, y no se hizo commit ni push.

## Verificación solicitada por el tenant al retornar de Checkout

El retorno `success` de Stripe puede ocurrir antes de que un webhook esté disponible. La pantalla de resultado consultaba solamente el ledger local, mientras `POST /api/pagos/{id_pago}/verificar` estaba restringido al `ADMINISTRADOR`; por ello un pago ya cobrado podía seguir visible como `PENDIENTE` para `ADMINISTRADOR_EMPRESA`.

Se conserva el mismo caso de uso de verificación y la misma aplicación transaccional a CU33. La ruta aceptará `ADMINISTRADOR` y `ADMINISTRADOR_EMPRESA`; el servicio revalidará usuario, rol y empresa desde PostgreSQL y, para el rol de tenant, exigirá que el pago pertenezca a su `id_empresa` antes de consultar Stripe. El administrador global mantiene su alcance actual. Ningún estado aportado por el navegador se considera confiable: la confirmación seguirá dependiendo de Checkout Session y PaymentIntent recuperados desde Stripe Test, con los bloqueos e idempotencia existentes.

En `/pagos/resultado`, la carga inicial continuará siendo una consulta; la acción explícita **Actualizar estado** invocará la verificación y después refrescará el detalle local. La validación cubrirá acceso del tenant propietario, rechazo 403 para otra empresa, conservación del acceso global, llamada de verificación desde la pantalla y regresión del pago TEST 7 sin webhook.

La implementación habilitó ambos roles en la ruta y aplicó la comprobación de pertenencia en el servicio antes de consultar Stripe. La pantalla invoca primero `POST /verificar` y luego refresca con `GET`. Las pruebas aisladas aprobaron para backend y frontend, incluido el 403 entre tenants. La verificación real del pago TEST 7, solicitada por el administrador de su propia empresa, cambió `PENDIENTE` a `CONFIRMADO`, guardó PaymentIntent y fecha de aplicación, renovó la vigencia de Profesional de 2026-11-24 a 2026-12-24 e insertó un historial `PAGO_STRIPE`. Una segunda ejecución devolvió `aplicado=false` y mantuvo vigencia e historial sin duplicados. No se utilizó webhook ni se cambió el esquema.

