# Asistente: consultas modulares y contexto explícito

## Análisis previo

Solicitud: ampliar las consultas naturales a los módulos implementados y permitir consultas nuevas excepcionalmente, priorizando las consultas existentes. Se revisaron arquitectura general, Reportes/operación, base/inventario, autorización y repositorios actuales. El coordinador solo permite `reportes/crm/ayuda`. Además, el frontend añade obra como texto: contamina stock empresarial y puede competir con una obra escrita explícitamente. El intérprete hereda filtros de manera insuficiente y depende de alias cortos.

## Diseño y contratos previstos

Se conserva routes → services → repos → PostgreSQL. El proveedor común genera un plan declarativo de lectura (fuente, filtros, campos, agrupación, métricas y orden), nunca controla tablas, SQL ejecutable, identidad o empresa. El backend ejecuta consultas existentes de Reportes y un registro de lecturas parametrizadas de módulos: obras, materiales, proveedores, compras, maquinaria, OT y CRM. La composición excepcional ocurre sobre resultados autorizados completos y acotados. Operaciones tipadas sustituyen expresiones SQL libres; no se promete consultar datos que el sistema no registra.

Permisos/empresa se recargan del actor actual antes de leer y antes de devolver. Reportes conserva `authorize` y sus restricciones de recurso/actor; fuentes de obra intersectan `repo.works`, fuentes empresariales excluyen clientes/trabajadores. Se excluyen credenciales, contactos personales y control Backup. Campos/operadores deben pertenecer al registro; límites de entradas/salida, sumas Decimal separadas por moneda y versiones. Consultas en READ ONLY con timeout, sin funciones elegidas por el modelo ni escrituras de negocio. No migraciones ni pruebas en bases desconocidas.

`AssistantRequest.id_obra_contexto` opcional transporta contexto de navegación sin mezclarlo con la pregunta. La obra explícita prevalece; stock ignora la obra contextual y explica su alcance. Flutter/consumidores antiguos siguen funcionando al omitir el nuevo campo.

Validación: intérprete y seguimiento, stock crítico, nombres/errores de escritura, precedencia de obras, planes fuera de catálogo, campos desconocidos, permisos revocados, límites, filtros y agrupaciones exactas, moneda/versiones, consultas parametrizadas, contrato frontend y suites existentes. HTTP/DB/proveedor simulados, sin envíos ni workers. Documentar capacidades reales y pendientes al finalizar.
