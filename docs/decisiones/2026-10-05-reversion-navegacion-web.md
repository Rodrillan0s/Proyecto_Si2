# Reversión de la refactorización de navegación web

Fecha: 2026-10-05. El usuario solicita recuperar el estado anterior y confirma que el backend estaba fuera del alcance autorizado.

## Análisis previo y alcance

Se revisaron la arquitectura general, Reportes/IA, operación, arquitectura de base de datos, la decisión de navegación y los diffs actuales. La refactorización añadió una dependencia de sesión (`GET /api/auth/contexto`) entre el shell/guards Angular y las capas routes → services → repos; también cambió navegación y contexto Empresa/Obra. Se revierte esa intervención completa, incluidos el endpoint y sus pruebas, los guards, AuthService, contexto operativo, navegación, selectores y modos nuevos del asistente. Se recuperan los contratos y el comportamiento anteriores de permisos, tenants y módulos.

La restauración es selectiva por archivos/hunks de esta intervención. Se conservan los cambios previos del usuario, especialmente Backup/descarga OCI, AGENTS.md y documentos/eliminaciones ajenos a la navegación. No se usa reset global, no se modifica la base de datos ni se inician servicios, workers o restauraciones. La documentación compartida pierde únicamente las referencias a esta implementación retirada; la decisión original queda identificada como histórica.

## Validación prevista

Comprobar que los archivos de código restaurados coincidan con su versión previa en Git, que desaparezcan las referencias al contexto/registro nuevos y que no se modifique el conjunto de cambios de Backup. Compilar el frontend restaurado y documentar el resultado real. No probar escrituras en bases ni alterar sesiones guardadas del navegador del usuario.

## Resultado

Reversión completada: se restauraron selectivamente 29 archivos existentes y se retiraron cinco archivos nuevos de la intervención (prueba backend de sesión, registro de navegación, módulo amplio de IA, contexto operativo y configuración de pruebas). Se retiraron únicamente los párrafos nuevos de arquitectura compartida; la nota original quedó marcada como retirada. `git diff --name-only -- backend` está vacío: el backend coincide con su versión anterior en Git. En frontend solo permanecen los cinco archivos modificados de Backup que ya existían antes de esta refactorización; no se tocaron esos archivos ni los cambios documentales previos.

No quedan referencias a cargarContexto, ContextoOperativo, REPORT_FAMILIES, auth/contexto, obtener_contexto_sesion o AsistenteWorkspace en frontend/src, backend/app, package.json o el script de navegador. `git diff --check` terminó correctamente. `npm run build` de la versión restaurada terminó correctamente a las 18:19 UTC; conserva avisos previos de presupuestos CSS y Leaflet/CommonJS y reemplazó la salida de compilación anterior.

No se inició ni detuvo la terminal backend del usuario, se accedió a PostgreSQL ni se modificaron datos o variables de entorno. Una instancia de la API sin recarga automática debe reiniciarse para descargar de memoria el endpoint retirado; la interfaz puede recargarse después de que el servidor de desarrollo detecte la reversión.
