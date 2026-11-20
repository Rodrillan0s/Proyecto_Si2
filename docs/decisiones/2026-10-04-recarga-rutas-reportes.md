# 404 del catálogo de Reportes

El servidor local en el puerto 5000 no publica Reportes en su OpenAPI, mientras una instancia nueva de `create_app()` sí publica `/api/reportes/catalogo` y responde 401 sin autenticación. Se identificó un proceso `python run.py` con hijo Uvicorn: el proceso activo conserva una aplicación anterior al registro de Reportes.

Se mantiene Application Factory y `routes → services → repos`; no se duplican rutas, alteran permisos/tenants ni aplican migraciones. La corrección consiste en recargar el servidor local y agregar una comprobación de integración sobre la fábrica completa, porque las pruebas anteriores componían únicamente el router aislado.

Validación prevista: test de catálogo con dependencia de autenticación y servicio sustituidos; comprobar OpenAPI y respuesta sin credenciales del proceso activo. Sin lecturas de datos de negocio ni envío de correos.

Resultado: cuatro pruebas API pasan, incluida la nueva prueba de la fábrica completa y transmisión de `id_empresa=3`. La actualización de archivos no recargó la instancia activa; se verificó que el puerto 5000 pertenecía al proceso `python run.py` y se reinició únicamente ese servidor desde el backend de este proyecto. OpenAPI ahora publica el catálogo; la petición sin token devuelve 401, en lugar de 404. El servidor queda ejecutándose en segundo plano. No se validaron consultas autenticadas ni se modificó la base de datos.
