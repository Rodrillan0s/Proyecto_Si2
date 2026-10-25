# CU39: cronogramas y planificación

## Instalación
La migración es `backend/database/20261025_cu39_cronogramas.sql`. No se ejecuta automáticamente al arrancar. El comando de inspección solo lee catálogos:

```powershell
cd backend
python manage_cronogramas.py --check
python manage_cronogramas.py --apply --database obras
```

El segundo comando modifica exclusivamente la base identificada en `DB_NAME` y exige el nombre explícito; usar únicamente el destino autorizado. Crea tablas con FK/CHECK, índices y permisos, en una transacción con bloqueo de instalación. Puede repetirse sin duplicar permisos/roles. No reasigna usuarios. Reiniciar el backend después de desplegar el código y renovar sesión si el cliente conserva permisos anteriores. La caché de permisos del backend puede tardar hasta 120 segundos si no se reinicia.

El rol `SUPERVISOR_OBRA` se crea si no hay Supervisor existente. Un administrador debe asignarlo a las cuentas correspondientes mediante Usuarios; CU39 no elige qué personas deben tenerlo.

## Acceso
Web: Proyectos y obras → Cronogramas y planificación → seleccionar obra. También hay acceso en el detalle de cada obra. Móvil: abrir la obra → Cronogramas y planificación.

| Actor | Consultar | Crear/editar cabecera/eliminar | Planificar y registrar ejecución |
| --- | --- | --- | --- |
| Jefe de Obra | Sí | Sí | Sí |
| Supervisor | Sí | No | Sí |
| Administrador de empresa | Empresa propia | Empresa propia | Empresa propia |
| Administrador global | Global | Global | Global |

Los permisos efectivos del servidor y la empresa de la obra son obligatorios; la selección visual no autoriza otra empresa. Tener un permiso accidental en otro rol no habilita CU39.

## Contrato y reglas
Base API: `/api/obras/{id_obra}/cronogramas`.

- GET/POST `/`: listar/crear; GET/PUT/DELETE `/{id}`: consultar/actualizar/eliminar. DELETE exige query `version`.
- PUT `/{id}/planificacion`: actualizar únicamente actividades con `version`, para Supervisor/Jefe.
- GET `/retrasos?corte=AAAA-MM-DD`: desviaciones de todos los cronogramas de la obra.
- GET `/{id}?desde=...&hasta=...&corte=...`: período por solapamiento. `actividades` conserva el agregado completo y `programadas` es la selección para consulta. No guardar una lista filtrada como plan completo.

La actualización envía el agregado completo con su versión; 409 indica conflicto y exige recargar, evitando sobrescribir trabajo ajeno. Un guardado confirma cabecera, actividades, dependencias y auditoría juntos.

Cada actividad tiene clave estable local al cronograma, nombre, descripción, tipo ACTIVIDAD/HITO, inicio/fin previstos, inicio/fin reales, avance entero 0–100 y claves predecesoras. Máximo 500 actividades y 200 predecesoras por actividad. Fechas previstas dentro de la cabecera; hitos en un solo día y avance 0/100. Finalizar exige inicio real, fin real y 100%. No hay fechas reales futuras. Un inicio real requiere que sus predecesoras hayan finalizado. No hay dependencia consigo misma, ajena ni ciclos. Las dependencias son fin-inicio, admitiendo el mismo día de fin/inicio.

La fecha de corte predeterminada es hoy en America/La_Paz. Retraso de finalización = máximo(0, fin real al corte o corte − fin previsto), en días calendario. Inicio vencido señala actividades no iniciadas al corte cuya fecha de inicio pasó. Las completadas conservan retraso histórico. La consulta de un corte pasado reconstruye estado/fechas, pero el porcentaje mostrado es el último registrado: no hay historial diario de porcentajes. No calcula predicciones ni altera órdenes de trabajo.

503 indica que falta instalar el esquema; 403 indica rol/permiso/contexto inválido; 404 evita revelar obras o cronogramas ajenos. Se conserva la barrera general de mantenimiento y las restricciones del módulo `obras` en el plan.

## Verificación reproducible
Angular: `npm test -- --watch=false --ts-config=tsconfig.cronogramas.spec.json --include=src/app/pages/cronogramas/cronogramas.spec.ts`, `npm run build`.

Flutter: `flutter test test/cronogramas_test.dart`; analizar los archivos CU39, auth_provider, app_config y detalle de proyecto.

Backend: `backend/tests/test_cronogramas.py`, unitarias sin red. La integración solo acepta `CU39_TEST_DSN` dirigido a `127.0.0.1:55439/cu39_test`: crea baseline mínimo en esa base de pruebas, instala dos veces la migración y prueba persistencia, rollback, permisos y versiones. Nunca ejecutar ese baseline en una base de negocio.
