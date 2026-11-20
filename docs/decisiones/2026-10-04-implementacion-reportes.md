# Implementación de Reportes e IA

Estado: implementación preparada; plan aprobado por el usuario el 2026-10-04. Activación y aceptación integrada pendientes de entorno designado.

## Contexto previo

Se leyeron AGENTS.md, arquitectura general, análisis de PostgreSQL y plan de Reportes. Se preserva routes → services → repos; se introducen catálogo de capacidades, autorización explícita por actor/recurso, adaptadores de exportación/proveedor y cola persistente. Los reportes usarán el esquema actual de estimaciones/CU17, sin consumidores APU antiguos.

## Alcance y validación

Implementar las fases aprobadas y pruebas aisladas de permisos, consultas, interpretación, archivos, proveedores y automatización. Mantener compatibilidad de CRM y recuperación de contraseña. No enviar correos reales ni activar cron externo durante las pruebas. Registrar aquí decisiones, cambios, resultados y límites al finalizar.

## Cambios realizados

- Nuevo catálogo de diez reportes y contratos Pydantic; capa routes/services/repos. Se movieron todas las operaciones SQL de persistencia/cola al repositorio. El comparativo CU17 admite conexión opcional, conservando consumidores anteriores.
- Contexto de actor recargado, tenant explícito para global, ámbito de jefe por asignación, cliente mediante FK persona y trabajador por sus filas. Descargas/envíos revalidan permisos y política. Se incorporaron cinco permisos de acción al catálogo y mapas de navegación Angular/Flutter.
- Consultas deterministas, resultados JSONB con corte REPEATABLE READ y Decimal; PDF/XLSX sobre el mismo resultado, límites explícitos y sanitización. Tabla de pantalla paginada a 50 filas sin limitar exportaciones.
- Interpretación local con difflib, tildes, alias, fechas, errores frecuentes y aclaraciones. Conversaciones actor/tenant con retención; DeepSeek/Gemini mediante factory/puerto común y fallback. CRM conserva contrato y ahora exige autorización actual y tenant global explícito.
- Voz web/móvil y fallback Whisper opcional. Inicialización única del plugin de voz con callbacks de pantalla activa; permisos de micrófono/reconocimiento. Audio temporal eliminado.
- Migración de siete tablas, grants por nombre, índices/constraints y reversión que rechaza datos existentes. Revisión/aplicación por CLI separada de la API. No se aplicó a la base configurada.
- Worker PostgreSQL separado: claims SKIP LOCKED, leases, reintentos, programación UTC/IANA, omisiones tras caídas y deduplicación. Brevo con adjuntos/messageId, un correo por destinatario y estado incierto sin reenvío automático. Recuperación de contraseña conserva su función original.
- Recomendaciones de sobrecosto y reposición mínima. Se descuentan compras aprobadas pendientes únicamente con autorización de esa fuente; el envío intersecta permisos y filas de emisor/receptor.
- Se resolvieron marcadores de conflicto ya presentes en home móvil conservando imports de CRM/incidencias. Se normalizó requirements de UTF-16 a UTF-8 y se agregaron dependencias de exportación/zona horaria.

## Refinamientos respecto al plan

Se usa difflib de biblioteca estándar, evitando dependencia RapidFuzz. La primera entrega almacena archivos acotados mediante repositorio BYTEA; no tiene object storage. Reportes/exportaciones manuales síncronos con límite de 20.000 filas/5 MiB; programación y envío asíncronos. No se implementó exportación masiva ni vínculo para adjuntos mayores. Retención fija: archivos 7 días, resultados/conversación 30; hacerla configurable queda como extensión.

Stock empresarial se restringe a administración; jefe trabaja sobre obras asignadas. Cliente usa la relación canónica de persona a obra y ve sus unidades; no se presume autorización individual por CRM. El esquema no acredita correo verificado, horas efectivas, consumo físico, capacidad de reasignación ni predicción de retrasos. HU98/HU100/HU111 mantienen los límites semánticos publicados; HU112/HU113 no se declaran completas.

## Validación realizada

- 53 pruebas unittest aisladas: reportes, API y regresión CU17. Tres reglas de seguridad existentes verificadas adicionalmente. Sin DB/IA/Brevo reales en estas pruebas.
- 41 consultas pasaron EXPLAIN PostgreSQL de solo lectura, sin ANALYZE, registros de negocio ni migraciones.
- Angular: compilación de desarrollo y producción exitosas; cuatro pruebas nuevas de contratos HTTP/cambio de empresa pasaron mediante `npm run test:reportes`. La ejecución estándar incluye specs anteriores con imports rotos; la configuración focalizada evita mezclarlas. Producción conserva avisos CSS/Leaflet anteriores.
- Dart: análisis focalizado sin errores de los archivos móviles afectados. pub resolvió dependencias, pero la generación de enlaces de plugins en Windows exige modo desarrollador. No se cambió la configuración del sistema ni se compiló/probó Android/iOS.
- Falta aplicar migración en base de pruebas designada y validar datos, concurrencia real/reinicio de dos workers, correo controlado y voz/compartir en dispositivo. STT local no se instaló; sigue desactivado por defecto. No se probó una llamada real al nuevo proveedor ni se mostraron secretos del `.env`.
- `python migrate_reportes.py` pasó la revisión de precondiciones de solo lectura y confirmó las siete tablas pendientes. SHA256 de la migración revisada: `720c2265132f5e64c314c75ce93035bc776edd0260ede05be63c0d052ecb0ee2`.

Referencia final: [arquitectura](../ARQUITECTURA_REPORTES_IA.md), [manual operativo](../OPERACION_REPORTES.md).
