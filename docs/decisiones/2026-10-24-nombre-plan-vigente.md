# Nombre visible del plan vigente

## Solicitud y contexto
El usuario ve cupos en Suscripción pero no identifica textualmente el plan asignado. Revisados arquitectura general, componente/plantilla/servicio y pruebas de Suscripciones, y respuesta actual del repositorio: ya existen `codigo_plan`, `nombre_plan` y `estado_efectivo`.

## Decisión previa
Cambio de presentación Angular: encabezado explícito «Plan vigente: Profesional» para ACTIVA/GRACIA, «Plan asignado» para otros estados, resumen inicial por empresa para administrador global y marca del plan propio en catálogo. Resolver nombre primero desde la suscripción y después desde el catálogo/código si el nombre no llega. No inferir plan por límites. Sin cambios de API, SQL, permisos ni contexto tenant: consulta propia sigue ligada al usuario y global usa el listado autorizado.

## Validación prevista
Pruebas de texto visible con nombre normal y con solo código, resumen de empresas para global y selección del plan propio; compilación Angular. No requiere conexiones ni migraciones. Flutter no contiene esta pantalla y el contrato permanece igual.

## Resultado
Implementado encabezado explícito en suscripción propia, resumen inicial para el administrador global y marca del plan propio en el catálogo. La tabla de gestión reutiliza el mismo resolutor del nombre. Planes suspendidos/cancelados/programados/vencidos se etiquetan como asignados, sin afirmar vigencia. No se modificaron datos ni contratos.

Validación: 6 pruebas de Suscripciones aprobadas, incluyendo resolución desde catálogo sin `nombre_plan`, texto Profesional/Empresarial por empresa y plan cancelado sin etiqueta de vigente. Compilación Angular development verificada; `git diff --check` sin errores.
