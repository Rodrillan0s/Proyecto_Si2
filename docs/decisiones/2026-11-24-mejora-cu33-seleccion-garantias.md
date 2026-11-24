# Mejora CU33: seleccion usable de unidades y clientes para garantias

Fecha: 2026-11-24

## Contexto

El flujo web de CU33 pedía al usuario escribir IDs de unidad y cliente manualmente.
La consulta backend de unidad usaba `u.nombre`, columna que no existe en
`obras.t_unidad_construccion`; el modelo real identifica unidades por `codigo`
y estructura. Ademas, CU33 tiene una migracion preparada que no esta acreditada
como aplicada en la base configurada.

## Cambios

- Registrar unidades vendidas, reservadas o entregadas y sus clientes propietarios
  mediante una opcion compuesta, no mediante IDs libres.
- Exponer una consulta autenticada por tenant para cargar esas opciones.
- Mantener la pertenencia de unidad y cliente en el backend; el desplegable no
  sustituye las validaciones del servicio ni permite seleccionar recursos de
  otra empresa.
- Usar `u.codigo` como identificador visible de unidad y recuperar el nombre
  de la estructura/obra con las consultas existentes.
- Mantener `routes -> services -> repos -> PostgreSQL`.
- Mostrar errores HTTP legibles en los formularios sin exponer trazas internas.

## Migracion

La migracion `20261123_cu33_garantias_posventa.sql` permanece preparada hasta
que se confirme su aplicacion al entorno designado. Esta mejora corrige el
contrato y prepara el formulario, pero no ejecuta SQL ni escribe datos de
negocio.

## Validacion prevista

- Pruebas aisladas de CU33.
- Compilacion backend mediante `compileall`.
- Compilacion Angular.
- Prueba HTTP manual con usuario administrador de empresa, sin aplicar datos
  hasta que existan las tablas CU33 en la base configurada.
