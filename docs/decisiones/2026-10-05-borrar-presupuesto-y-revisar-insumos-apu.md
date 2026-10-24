# Borrado de presupuestos y revisión de insumos APU

## Solicitud y alcance

Agregar en la pantalla de presupuesto la acción para borrar presupuestos y verificar si los insumos APU se vinculan al catálogo de materiales incluyendo su unidad y precio unitario.

Ampliación del 2026-10-05: mostrar precios de material y APU acompañados explícitamente por su unidad; para materiales del APU, importar unidad/precio desde el catálogo y permitir ingresar únicamente la cantidad consumida por unidad de actividad.

## Contexto actual y archivos revisados

- La pantalla Angular de presupuesto ya tiene un método cliente para `DELETE`, y el backend expone la ruta. La interfaz no ofrecía la acción.
- El servicio backend permite borrar solo presupuestos `BORRADOR`; el repositorio también restringe el `DELETE` al mismo estado, pero no confirma que una fila se haya eliminado.
- La eliminación de presupuesto se limita a una obra de la empresa autorizada; la operación debe comprobar también que el identificador del presupuesto pertenece a la obra recibida.
- El inventario documentado describe `t_partida_presupuesto.id_presupuesto` con `ON DELETE CASCADE`. No se consultará ni modificará una base de datos durante este cambio.
- El flujo vigente de estimaciones/APU usa `t_analisi_precio_unitario_insumo`: conserva `id_material` con FK a `t_material`, y guarda nombre, unidad y precio unitario. El repositorio obtiene nombre y unidad del material; toma el precio del catálogo como valor predeterminado, pero permite un precio unitario editado para conservar el snapshot del análisis.
- La pantalla APU incluida en Presupuesto usa el modelo antiguo `t_apu`/`t_apu_componente`. Su formulario permite editar nombre, unidad y precio libremente; aunque envía el id del material al seleccionarlo, el backend solo valida ese id si está presente y no fuerza la unidad ni el precio del catálogo. La arquitectura e inventario documentan que esas tablas fueron retiradas y que el backend conserva rutas antiguas; no se recrearán ni se redirigirán a estimaciones en este cambio.

## Patrones, capas y tenants afectados

- Se mantiene `routes → services → repos → PostgreSQL`; el servicio verifica estado, obra y tenant, mientras el repositorio confirma el resultado del borrado.
- Se mantiene el permiso existente `Modificar_presupuesto` y se expone la acción solo para estado `BORRADOR`.
- Para usuarios de empresa se requiere una empresa en el JWT y se compara con la empresa autorizada de la obra/presupuesto. El rol global `ADMINISTRADOR` mantiene su ámbito actual.

## Decisión y efectos sobre contratos/datos

- No cambia el contrato HTTP existente ni se agrega una migración.
- El borrado es explícito y confirmado por el usuario; no se amplía a presupuestos aprobados/en revisión/cerrados.
- Si entre la lectura y el `DELETE` el presupuesto deja de ser borrador o ya no existe, el backend devuelve un error y no registra éxito.
- En la pantalla de Presupuesto/APU, los selectores y tablas indicarán el precio y unidad como `Bs./unidad`; tanto el wizard como el formulario para añadir componentes a un APU existente retiran los campos editables de descripción, unidad y precio para materiales, dejando editable solo la cantidad consumida por unidad de APU.
- El backend resolverá por `id_material` el nombre, unidad y precio vigentes del catálogo, comprobará la pertenencia a la empresa del APU y persistirá esos datos; los valores de unidad/precio/descripción recibidos del cliente no serán fuente de verdad. No cambia el flujo APU vigente de Estimaciones.

## Validación prevista

- Pruebas unitarias aisladas de pertenencia a obra, tenant y resultado de borrado; sin conexión a PostgreSQL.
- Pruebas unitarias aisladas de validación de vínculo catálogo/unidad/precio para materiales APU.
- Build Angular para comprobar el template y tipos.
- No ejecutar migraciones ni pruebas funcionales que escriban en una base de datos.

## Implementación final y validación realizada

- Se añadió la acción **Eliminar borrador** solo cuando existe un presupuesto en `BORRADOR` y el usuario posee `Modificar_presupuesto`. La confirmación advierte que también se borrarán sus partidas.
- El selector conserva el presupuesto elegido aunque falle la carga del detalle, y oculta el borrado mientras esa carga está en curso; así la acción no depende de que funcionen las consultas del modelo APU retirado.
- El backend ahora rechaza empresa ausente en usuarios no globales, verifica que el presupuesto pertenezca a la obra de la URL y solo informa éxito si PostgreSQL devuelve la fila eliminada. Una carrera con cambio de estado/no existencia produce HTTP 409 y no deja evento de éxito en bitácora.
- Pruebas aisladas: `python -m unittest discover -s tests -p test_presupuesto_delete.py -v` — 8 pruebas aprobadas (borrado, empresa, cantidad y uso de unidad/precio/nombre del catálogo). No se usó PostgreSQL.
- Frontend: `npm run build` — aprobado tras el cambio final. Solo hubo advertencias existentes de presupuesto CSS y CommonJS de Leaflet; no bloquearon la compilación.
- `pytest` no está instalado en el entorno virtual; se usó el runner estándar `unittest`, sin instalar paquetes.
- No se ejecutaron migraciones ni pruebas que escriban en bases de datos.
- Se añadieron pruebas de regresión para comprobar que el servicio ignora la unidad/precio/nombre enviados por el cliente y usa los del catálogo tanto al crear un APU como al agregar un componente.

## Limitaciones o trabajo pendiente

El APU heredado de la pantalla Presupuesto depende de tablas retiradas. Los cambios de esta ampliación hacen que su contrato de backend valide los componentes si ese modelo está disponible, pero no recrean las tablas ni acreditan que el flujo heredado esté operativo en la base desplegada. El precio de insumo del flujo vigente de Estimaciones puede diferir del precio actual del catálogo porque se guarda como snapshot editable por unidad del material.
