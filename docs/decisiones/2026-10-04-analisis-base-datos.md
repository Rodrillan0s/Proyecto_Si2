# Análisis de arquitectura de base de datos

## Solicitud y alcance

Analizar roles, tablas, relaciones, funciones, procedimientos y demás objetos de PostgreSQL, y conservar una referencia Markdown para cambios posteriores.

## Contexto y decisión previa

Se consultaron `AGENTS.md` y `docs/ARQUITECTURA_Y_PATRONES.md`. La aplicación comparte el esquema `obras` y aplica aislamiento por empresa. Se revisarán migraciones, repositorios, seguridad y, si la conexión configurada está disponible, catálogos de PostgreSQL y catálogos funcionales de roles/permisos mediante consultas de solo lectura. No se leerán contraseñas ni datos comerciales o personales, ni se ejecutarán migraciones.

## Patrones y capas afectados

Persistencia SQL/DAO, reglas en funciones y triggers, RBAC y discriminación multiempresa. El resultado será documentación; no se cambiarán contratos ni lógica del sistema.

## Validación prevista

Contrastar definiciones disponibles, llamadas del backend y objetos de la base accesible; marcar diferencias y límites de evidencia. Revisar enlaces y cambios documentales al finalizar.

## Implementación y validación

Se inspeccionó la base configurada `obras` (PostgreSQL 17.11), mediante consultas de catálogos y roles/permisos, con transacciones de solo lectura y rollback. Se obtuvieron 68 tablas, 599 columnas, 73 funciones, 1 procedimiento, 38 triggers, 316 restricciones, 177 índices y 64 secuencias. Una consulta complementaria verificó columnas generadas, privilegios del esquema, tipos y validez de índices.

Se crearon `docs/ARQUITECTURA_BASE_DATOS.md`, `docs/BASE_DATOS_INVENTARIO.md` y `docs/BASE_DATOS_RUTINAS.md`. Se enlazó la revisión desde la referencia general y `AGENTS.md`. Se contrastaron roles reales, llamadas y columnas de repositorios, scripts y definiciones SQL; se documentaron divergencias de permisos, APU/costos, autenticación e instalación reproducible.

La revisión no ejecutó funciones de negocio, procedimientos, migraciones ni pruebas mutadoras; no cambió datos, permisos o esquema. La conexión configurada no identifica por sí sola el ambiente como desarrollo o producción. Los inventarios son una fotografía y requieren actualización al cambiar la base.

Validación documental completada: 68 entradas de tabla y 74 definiciones de rutina contrastadas con el catálogo capturado; enlaces locales y bloques Markdown comprobados. Se normalizaron finales de línea de las definiciones conservando su contenido. `git diff --check` no reportó errores en los cambios rastreados; los nuevos documentos siguen sin commit.
