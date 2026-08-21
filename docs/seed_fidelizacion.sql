-- Seed: HU28 - Programa de Fidelizacion de Clientes CRM
-- Ejecutar despues de migracion_fidelizacion.sql

BEGIN;

INSERT INTO AGROENLACE.NIVEL_FIDELIZACION
    (nombre_nivel, descripcion, min_transacciones, min_monto_acumulado, prioridad, estado, id_empresa)
SELECT 'Bronce', 'Clientes con actividad comercial inicial', 2, 500.00, 1, 'ACTIVO', 1
WHERE NOT EXISTS (SELECT 1 FROM AGROENLACE.NIVEL_FIDELIZACION WHERE nombre_nivel = 'Bronce' AND id_empresa = 1);

INSERT INTO AGROENLACE.NIVEL_FIDELIZACION
    (nombre_nivel, descripcion, min_transacciones, min_monto_acumulado, prioridad, estado, id_empresa)
SELECT 'Plata', 'Clientes frecuentes con compras recurrentes', 4, 1500.00, 2, 'ACTIVO', 1
WHERE NOT EXISTS (SELECT 1 FROM AGROENLACE.NIVEL_FIDELIZACION WHERE nombre_nivel = 'Plata' AND id_empresa = 1);

INSERT INTO AGROENLACE.NIVEL_FIDELIZACION
    (nombre_nivel, descripcion, min_transacciones, min_monto_acumulado, prioridad, estado, id_empresa)
SELECT 'Oro', 'Clientes de alto valor comercial', 8, 5000.00, 3, 'ACTIVO', 1
WHERE NOT EXISTS (SELECT 1 FROM AGROENLACE.NIVEL_FIDELIZACION WHERE nombre_nivel = 'Oro' AND id_empresa = 1);

INSERT INTO AGROENLACE.NIVEL_FIDELIZACION
    (nombre_nivel, descripcion, min_transacciones, min_monto_acumulado, prioridad, estado, id_empresa)
SELECT 'VIP', 'Clientes estratégicos con mayor recompensa', 12, 10000.00, 4, 'ACTIVO', 1
WHERE NOT EXISTS (SELECT 1 FROM AGROENLACE.NIVEL_FIDELIZACION WHERE nombre_nivel = 'VIP' AND id_empresa = 1);

INSERT INTO AGROENLACE.REGLA_FIDELIZACION
    (id_nivel, tipo_transaccion, porcentaje_descuento, monto_max_descuento, vigencia_desde, vigencia_hasta, estado)
SELECT id_nivel, 'PEDIDO_INSUMO', 3.00, 150.00, CURRENT_DATE, NULL, 'ACTIVO'
FROM AGROENLACE.NIVEL_FIDELIZACION
WHERE nombre_nivel = 'Bronce' AND id_empresa = 1
  AND NOT EXISTS (SELECT 1 FROM AGROENLACE.REGLA_FIDELIZACION r WHERE r.id_nivel = NIVEL_FIDELIZACION.id_nivel AND r.tipo_transaccion = 'PEDIDO_INSUMO');

INSERT INTO AGROENLACE.REGLA_FIDELIZACION
    (id_nivel, tipo_transaccion, porcentaje_descuento, monto_max_descuento, vigencia_desde, vigencia_hasta, estado)
SELECT id_nivel, 'PEDIDO_INSUMO', 5.00, 300.00, CURRENT_DATE, NULL, 'ACTIVO'
FROM AGROENLACE.NIVEL_FIDELIZACION
WHERE nombre_nivel = 'Plata' AND id_empresa = 1
  AND NOT EXISTS (SELECT 1 FROM AGROENLACE.REGLA_FIDELIZACION r WHERE r.id_nivel = NIVEL_FIDELIZACION.id_nivel AND r.tipo_transaccion = 'PEDIDO_INSUMO');

INSERT INTO AGROENLACE.REGLA_FIDELIZACION
    (id_nivel, tipo_transaccion, porcentaje_descuento, monto_max_descuento, vigencia_desde, vigencia_hasta, estado)
SELECT id_nivel, 'PEDIDO_INSUMO', 8.00, 600.00, CURRENT_DATE, NULL, 'ACTIVO'
FROM AGROENLACE.NIVEL_FIDELIZACION
WHERE nombre_nivel = 'Oro' AND id_empresa = 1
  AND NOT EXISTS (SELECT 1 FROM AGROENLACE.REGLA_FIDELIZACION r WHERE r.id_nivel = NIVEL_FIDELIZACION.id_nivel AND r.tipo_transaccion = 'PEDIDO_INSUMO');

INSERT INTO AGROENLACE.REGLA_FIDELIZACION
    (id_nivel, tipo_transaccion, porcentaje_descuento, monto_max_descuento, vigencia_desde, vigencia_hasta, estado)
SELECT id_nivel, 'PEDIDO_INSUMO', 12.00, 1000.00, CURRENT_DATE, NULL, 'ACTIVO'
FROM AGROENLACE.NIVEL_FIDELIZACION
WHERE nombre_nivel = 'VIP' AND id_empresa = 1
  AND NOT EXISTS (SELECT 1 FROM AGROENLACE.REGLA_FIDELIZACION r WHERE r.id_nivel = NIVEL_FIDELIZACION.id_nivel AND r.tipo_transaccion = 'PEDIDO_INSUMO');

COMMIT;

SELECT '-- NIVELES DE FIDELIZACION --' AS info;
SELECT n.id_nivel, n.nombre_nivel, n.min_transacciones, n.min_monto_acumulado, n.prioridad, r.porcentaje_descuento
FROM AGROENLACE.NIVEL_FIDELIZACION n
LEFT JOIN AGROENLACE.REGLA_FIDELIZACION r ON r.id_nivel = n.id_nivel
WHERE n.id_empresa = 1
ORDER BY n.prioridad;
