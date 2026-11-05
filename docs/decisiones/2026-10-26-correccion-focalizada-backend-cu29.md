# CU29: corrección focalizada del backend

Fecha: 2026-10-26, America/La_Paz. Trabajo autorizado: corregir los doce hallazgos parciales de la [validación diferencial](2026-10-26-validacion-diferencial-correcciones-cu29.md), por etapas y sin escrituras en producción.

## Contratos, capas y autorización

Se conserva routes → services → repos → PostgreSQL y los adaptadores DeepSeek/Gemini, la reserva SaaS por consulta y los consumidores existentes. El Context real no tiene obras_autorizadas: su alcance se obtiene de reportes_repos.works. La conversación recuperada ya contiene solicitud. Inventario usa SIN_STOCK y el autor de incidencia es id_usuario_registro.

Las propuestas, confirmaciones y cancelaciones deben exigir actor vigente, empresa explícita para el global, pertenencia a la empresa y permiso por operación. La confirmación exige también suscripción, IA y módulo de destino vigentes. El diagnóstico y conocimiento deben filtrar fuentes/permisos, con reautorización de datos sensibles antes de entregarlos o enviarlos al proveedor.

## Ampliación necesaria para M4/M5, justificada antes de implementar

No hay una tabla existente de operaciones del asistente. Reutilizar conversaciones exigiría cambiar el contrato ReportRequest de solicitud; reutilizar jobs de Reportes mezclaría tipos/estados y podría activar workers ajenos. Se preparará una migración aditiva exclusiva para t_asistente_operacion (UUID, actor, empresa, contexto de obra/política, parámetros tipados, estado, expiración, resultado), sin migraciones desde HTTP ni cambios en jobs/worker. No se aplicará al entorno configurado. La aplicación indicará instalación pendiente si falta esta tabla.

El ticket se bloqueará con FOR UPDATE y la creación de dominio, seguimiento, bitácora y resultado usarán la misma conexión/transacción. Las entradas de dominio y repositorios admitirán una conexión externa opcional, preservando las firmas anteriores. Ninguna capa inferior confirmará ni cerrará la conexión ajena. Un error revierte todo; un reintento de un éxito recupera el mismo resultado, aun desde otro proceso. Cancelar/confirmar exige el contexto de empresa; el cliente Angular solo se ajustará si es necesario transmitir este dato ya existente.

## Etapas y validación prevista

1. Integración: eliminar atributos/funciones inexistentes y corregir SQL. Pruebas de las cuatro reproducciones con Context y servicios reales.
2. Seguridad: permisos/capacidades, tenant/contexto, fuentes del diagnóstico/conocimiento e historial. Negativos de dos empresas y revocación entre lectura y devolución.
3. Transacciones: persistencia justificada anterior, transacción compartida, cancelación, expiración, reintentos y concurrencia entre procesos. Pruebas PostgreSQL local desechable; nunca DB de producción.
4. Interpretación: contrato estricto, intención explícita y obra desconocida/ambigua. Regresión CU29/Reportes/dominios y contratos cliente compartidos.

Se utilizará PostgreSQL 17 local aislado si el entorno lo permite. Los tests impedirán destinos de escritura que no sean un clúster local y base de pruebas designada. Se distinguirán resultados de PostgreSQL real, servicios reales y dobles de proveedor/persistencia. Cada etapa registrará resultados reales y la matriz final; ninguna prueba exclusivamente mockeada acreditará por sí sola un hallazgo corregido.

## Implementación y resultados

En curso. No se han aplicado migraciones al servidor configurado ni iniciado workers/envíos. La referencia de arquitectura/operación se actualizará al cerrar el cambio con sus requisitos de instalación.
