# CU30: cliente autenticado y unidades autorizadas

## Análisis previo

- **Capas y contrato:** no se cambia autenticación ni JWT. Para HU114, una ruta bajo el router de avances exigirá el rol `CLIENTE`; el servicio resolverá el cliente desde los claims, comprobará la unidad en la lista CU30 y delegará el historial físico al repositorio de avances.
- **Relación:** `t_usuario.id_persona` enlaza con `t_crm_cliente.id_persona`; ambas entidades contienen `id_empresa`. La unicidad CRM por `(id_empresa, id_persona)` limita la relación a un cliente por persona y empresa.
- **Tenant y permisos:** validar `id_unidad` e `id_obra` contra `listar_unidades_cliente_cu30(id_cliente, id_empresa)`; la consulta de avances volverá a exigir asociación del cliente, coherencia unidad → estructura → obra y empresa autorizada. No se filtra `estado_asociacion`.
- **Contrato de HU114:** devolver historial físico ordenado de nuevo a antiguo con porcentaje, estado actual de unidad, fecha y observación; el listado vacío representa unidad autorizada sin registros de avance.
- **Alcance:** no alterar rutas actuales de CU18, resolver identidad, listado CU30, tablas ni migraciones. Se usa el patrón de tests de servicio existente en `backend/tests/test_avance_services.py`.
- **Validación prevista:** ejecutar tests unitarios focalizados con dependencias simuladas y comprobación de sintaxis; no consultar una base de datos.

## Implementación y validación

Se implementaron `obtener_id_cliente_por_usuario_empresa` y `listar_unidades_cliente_cu30` en `backend/app/repos/crm_repos.py`. El nuevo listado enlaza cliente → asociación → unidad → estructura → obra, y exige el cliente y la obra dentro de `id_empresa`. Conserva el formato de `listar_unidades_cliente` y no filtra por `estado_asociacion`. El listado existente y la autenticación no se modificaron.

- Pylance: sin errores de sintaxis; no encontró call sites existentes para el nuevo listado.
- Validación aislada con `PostgreSQL` simulado: verificó filtros/joins tenant, forma de salida y lista vacía; comprobó que devuelve asociaciones sin filtrar estado y cierra la conexión.
- `git diff --check`: correcto. No se consultó ni modificó ninguna base de datos.

