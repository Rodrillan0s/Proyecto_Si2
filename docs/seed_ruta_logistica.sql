-- Seed: Datos de prueba para HU27 - Gestion de Rutas y Logistica de Distribucion
-- Ejecutar DESPUES de migracion_ruta_logistica.sql
--
-- Uso: psql -U tu_usuario -d tu_db -f docs/seed_ruta_logistica.sql
--
-- Empresa destino: AgroExport S.A. (id_empresa = 1)
-- Reutiliza usuarios existentes: Diego Melgar (4), Roberto Diaz (8), Lucia Ramirez (18)
-- Nuevos registros: usuarios 108-113 | transacciones 105-109 | rutas 102-103

BEGIN;

-- ============================================================================
-- 0. EMPRESA DESTINO (ya existe — no se inserta)
-- ============================================================================
-- AgroExport S.A. | id_empresa = 1 | NIT 900123456-7

-- ============================================================================
-- 1. CHOFERES (id_rol = 3) — AgroExport no tenia empleados/choferes
-- ============================================================================
INSERT INTO AGROENLACE.USUARIO (id_usuario, user_name, password_hash, documento_identidad, nombre_razon_social, direccion, correo, telefono, id_rol, id_empresa, estado_cuenta)
SELECT 108, 'mcondori.ae', '$pbkdf2-sha256$100000$w8jnFPJgrJVVl5XZW8uZsw$ZQr/jXFROhaQz5CbqmBjX6VHm8ufiV5YjP7GYRC7GjU', '71352841', 'Mario Condori Apaza', 'Calle Nuflo de Chavez 890, Centro, Santa Cruz de la Sierra', 'mcondori@agroexport.bo', '70134567', 3, 1, 'ACTIVO'
WHERE NOT EXISTS (SELECT 1 FROM AGROENLACE.USUARIO WHERE id_usuario = 108);

INSERT INTO AGROENLACE.USUARIO (id_usuario, user_name, password_hash, documento_identidad, nombre_razon_social, direccion, correo, telefono, id_rol, id_empresa, estado_cuenta)
SELECT 109, 'ezurita.ae', '$pbkdf2-sha256$100000$w8jnFPJgrJVVl5XZW8uZsw$ZQr/jXFROhaQz5CbqmBjX6VHm8ufiV5YjP7GYRC7GjU', '82461932', 'Elena Zurita Vargas', 'Av. San Martin 234, Barrio Hamacas, Santa Cruz de la Sierra', 'ezurita@agroexport.bo', '71245678', 3, 1, 'ACTIVO'
WHERE NOT EXISTS (SELECT 1 FROM AGROENLACE.USUARIO WHERE id_usuario = 109);

INSERT INTO AGROENLACE.USUARIO (id_usuario, user_name, password_hash, documento_identidad, nombre_razon_social, direccion, correo, telefono, id_rol, id_empresa, estado_cuenta)
SELECT 110, 'rsalvatierra.ae', '$pbkdf2-sha256$100000$w8jnFPJgrJVVl5XZW8uZsw$ZQr/jXFROhaQz5CbqmBjX6VHm8ufiV5YjP7GYRC7GjU', '93570218', 'Ruben Salvatierra Lopez', 'Av. Grigota 567, Barrio Sirari, Santa Cruz de la Sierra', 'rsalvatierra@agroexport.bo', '72356789', 3, 1, 'ACTIVO'
WHERE NOT EXISTS (SELECT 1 FROM AGROENLACE.USUARIO WHERE id_usuario = 110);

-- ============================================================================
-- 2. CLIENTES AGRICOLAS ADICIONALES (id_rol = 4)
--    (Lucia Ramirez id=18 ya existe en AgroExport)
-- ============================================================================
INSERT INTO AGROENLACE.USUARIO (id_usuario, user_name, password_hash, documento_identidad, nombre_razon_social, direccion, correo, telefono, id_rol, id_empresa, estado_cuenta)
SELECT 111, 'jpereira.ae', '$pbkdf2-sha256$100000$w8jnFPJgrJVVl5XZW8uZsw$ZQr/jXFROhaQz5CbqmBjX6VHm8ufiV5YjP7GYRC7GjU', '45678912', 'Hacienda Los Llanos — Jose Antonio Pereira', 'Km 12 Doble Via La Guardia, Santa Cruz de la Sierra', 'jpereira@clientes.agroexport.bo', '74467890', 4, 1, 'ACTIVO'
WHERE NOT EXISTS (SELECT 1 FROM AGROENLACE.USUARIO WHERE id_usuario = 111);

INSERT INTO AGROENLACE.USUARIO (id_usuario, user_name, password_hash, documento_identidad, nombre_razon_social, direccion, correo, telefono, id_rol, id_empresa, estado_cuenta)
SELECT 112, 'rmontano.ae', '$pbkdf2-sha256$100000$w8jnFPJgrJVVl5XZW8uZsw$ZQr/jXFROhaQz5CbqmBjX6VHm8ufiV5YjP7GYRC7GjU', '56789023', 'Agricola Guapay S.R.L. — Ricardo Montano Encinas', 'Carretera a Warnes Km 8, Santa Cruz de la Sierra', 'rmontano@clientes.agroexport.bo', '75578901', 4, 1, 'ACTIVO'
WHERE NOT EXISTS (SELECT 1 FROM AGROENLACE.USUARIO WHERE id_usuario = 112);

INSERT INTO AGROENLACE.USUARIO (id_usuario, user_name, password_hash, documento_identidad, nombre_razon_social, direccion, correo, telefono, id_rol, id_empresa, estado_cuenta)
SELECT 113, 'pencinas.ae', '$pbkdf2-sha256$100000$w8jnFPJgrJVVl5XZW8uZsw$ZQr/jXFROhaQz5CbqmBjX6VHm8ufiV5YjP7GYRC7GjU', '67890134', 'Finca El Tropico — Patricia Encinas Soliz', 'Av. San Aurelio 320, Plan 3000, Santa Cruz de la Sierra', 'pencinas@clientes.agroexport.bo', '76689012', 4, 1, 'ACTIVO'
WHERE NOT EXISTS (SELECT 1 FROM AGROENLACE.USUARIO WHERE id_usuario = 113);

-- ============================================================================
-- 3. TRANSACCIONES COMERCIALES (pedidos PEDIDO_INSUMO para logistica)
--    Supervisores: Diego Melgar (4) y Roberto Diaz (8)
-- ============================================================================
-- Pedido PENDIENTE #105 — Hacienda Los Llanos
INSERT INTO AGROENLACE.TRANSACCION_COMERCIAL
    (nro_transaccion, tipo_transaccion, estado_transaccion, monto_total, id_cliente, id_supervisor_admin, id_empresa, fecha_hora)
SELECT 105, 'PEDIDO_INSUMO', 'PENDIENTE', 675.00, 111, 4, 1, NOW() - INTERVAL '2 days'
WHERE NOT EXISTS (SELECT 1 FROM AGROENLACE.TRANSACCION_COMERCIAL WHERE nro_transaccion = 105);

-- Pedido PENDIENTE #106 — Agricola Guapay
INSERT INTO AGROENLACE.TRANSACCION_COMERCIAL
    (nro_transaccion, tipo_transaccion, estado_transaccion, monto_total, id_cliente, id_supervisor_admin, id_empresa, fecha_hora)
SELECT 106, 'PEDIDO_INSUMO', 'PENDIENTE', 1230.00, 112, 4, 1, NOW() - INTERVAL '1 day'
WHERE NOT EXISTS (SELECT 1 FROM AGROENLACE.TRANSACCION_COMERCIAL WHERE nro_transaccion = 106);

-- Pedido PENDIENTE #107 — Lucia Ramirez (cliente existente)
INSERT INTO AGROENLACE.TRANSACCION_COMERCIAL
    (nro_transaccion, tipo_transaccion, estado_transaccion, monto_total, id_cliente, id_supervisor_admin, id_empresa, fecha_hora)
SELECT 107, 'PEDIDO_INSUMO', 'PENDIENTE', 540.00, 18, 8, 1, NOW() - INTERVAL '12 hours'
WHERE NOT EXISTS (SELECT 1 FROM AGROENLACE.TRANSACCION_COMERCIAL WHERE nro_transaccion = 107);

-- Pedido EN_RUTA #108 — Hacienda Los Llanos
INSERT INTO AGROENLACE.TRANSACCION_COMERCIAL
    (nro_transaccion, tipo_transaccion, estado_transaccion, monto_total, id_cliente, id_supervisor_admin, id_empresa, fecha_hora)
SELECT 108, 'PEDIDO_INSUMO', 'EN_RUTA', 890.00, 111, 4, 1, NOW() - INTERVAL '3 days'
WHERE NOT EXISTS (SELECT 1 FROM AGROENLACE.TRANSACCION_COMERCIAL WHERE nro_transaccion = 108);

-- Pedido ENTREGADO #109 — Agricola Guapay
INSERT INTO AGROENLACE.TRANSACCION_COMERCIAL
    (nro_transaccion, tipo_transaccion, estado_transaccion, monto_total, id_cliente, id_supervisor_admin, id_empresa, fecha_hora)
SELECT 109, 'PEDIDO_INSUMO', 'ENTREGADO', 1500.00, 112, 8, 1, NOW() - INTERVAL '5 days'
WHERE NOT EXISTS (SELECT 1 FROM AGROENLACE.TRANSACCION_COMERCIAL WHERE nro_transaccion = 109);

-- ============================================================================
-- 4. DETALLE_VENTA (productos de bodega existentes de AgroExport)
--    id_producto 1=Urea | 2=Maiz DK-390 | 4=Imidacloprid | 9=NPK 15-15-15
-- ============================================================================
-- Pedido 105: Urea 30 KG + Maiz 5 KG
INSERT INTO AGROENLACE.detalle_venta (cantidad, precio_venta, nro_transaccion, id_producto)
SELECT 30, 12.50, 105, 1
WHERE NOT EXISTS (SELECT 1 FROM AGROENLACE.detalle_venta WHERE nro_transaccion = 105 AND id_producto = 1);

INSERT INTO AGROENLACE.detalle_venta (cantidad, precio_venta, nro_transaccion, id_producto)
SELECT 5, 45.00, 105, 2
WHERE NOT EXISTS (SELECT 1 FROM AGROENLACE.detalle_venta WHERE nro_transaccion = 105 AND id_producto = 2);

-- Pedido 106: NPK 50 KG + Urea 30 KG
INSERT INTO AGROENLACE.detalle_venta (cantidad, precio_venta, nro_transaccion, id_producto)
SELECT 50, 15.00, 106, 9
WHERE NOT EXISTS (SELECT 1 FROM AGROENLACE.detalle_venta WHERE nro_transaccion = 106 AND id_producto = 9);

INSERT INTO AGROENLACE.detalle_venta (cantidad, precio_venta, nro_transaccion, id_producto)
SELECT 30, 12.50, 106, 1
WHERE NOT EXISTS (SELECT 1 FROM AGROENLACE.detalle_venta WHERE nro_transaccion = 106 AND id_producto = 1);

-- Pedido 107: Imidacloprid 10 L + Maiz 5 KG
INSERT INTO AGROENLACE.detalle_venta (cantidad, precio_venta, nro_transaccion, id_producto)
SELECT 10, 38.00, 107, 4
WHERE NOT EXISTS (SELECT 1 FROM AGROENLACE.detalle_venta WHERE nro_transaccion = 107 AND id_producto = 4);

INSERT INTO AGROENLACE.detalle_venta (cantidad, precio_venta, nro_transaccion, id_producto)
SELECT 5, 45.00, 107, 2
WHERE NOT EXISTS (SELECT 1 FROM AGROENLACE.detalle_venta WHERE nro_transaccion = 107 AND id_producto = 2);

-- Pedido 108 (EN_RUTA): Maiz 10 KG + NPK 20 KG
INSERT INTO AGROENLACE.detalle_venta (cantidad, precio_venta, nro_transaccion, id_producto)
SELECT 10, 45.00, 108, 2
WHERE NOT EXISTS (SELECT 1 FROM AGROENLACE.detalle_venta WHERE nro_transaccion = 108 AND id_producto = 2);

INSERT INTO AGROENLACE.detalle_venta (cantidad, precio_venta, nro_transaccion, id_producto)
SELECT 20, 15.00, 108, 9
WHERE NOT EXISTS (SELECT 1 FROM AGROENLACE.detalle_venta WHERE nro_transaccion = 108 AND id_producto = 9);

-- Pedido 109 (ENTREGADO): Urea 50 KG + Imidacloprid 15 L
INSERT INTO AGROENLACE.detalle_venta (cantidad, precio_venta, nro_transaccion, id_producto)
SELECT 50, 12.50, 109, 1
WHERE NOT EXISTS (SELECT 1 FROM AGROENLACE.detalle_venta WHERE nro_transaccion = 109 AND id_producto = 1);

INSERT INTO AGROENLACE.detalle_venta (cantidad, precio_venta, nro_transaccion, id_producto)
SELECT 15, 38.00, 109, 4
WHERE NOT EXISTS (SELECT 1 FROM AGROENLACE.detalle_venta WHERE nro_transaccion = 109 AND id_producto = 4);

-- ============================================================================
-- 5. RUTAS LOGISTICAS
-- ============================================================================
-- Ruta ASIGNADA #102 — chofer Mario Condori, pedido 108
INSERT INTO AGROENLACE.RUTA_LOGISTICA
    (id_ruta, id_transaccion, id_chofer, id_empresa, origen, destino, fecha_asignacion, fecha_entrega_estimada, estado)
SELECT 102, 108, 108, 1,
    'Planta AgroExport S.A., Km 9 Carretera al Norte, Santa Cruz de la Sierra',
    'Km 12 Doble Via La Guardia, Santa Cruz de la Sierra',
    NOW() - INTERVAL '1 day',
    CURRENT_DATE + INTERVAL '2 days',
    'ASIGNADA'
WHERE NOT EXISTS (SELECT 1 FROM AGROENLACE.RUTA_LOGISTICA WHERE id_ruta = 102);

-- Ruta ENTREGADA #103 — chofer Elena Zurita, pedido 109
INSERT INTO AGROENLACE.RUTA_LOGISTICA
    (id_ruta, id_transaccion, id_chofer, id_empresa, origen, destino, fecha_asignacion, fecha_entrega_estimada, fecha_entrega_real, estado, observaciones, url_evidencia_imagen)
SELECT 103, 109, 109, 1,
    'Planta AgroExport S.A., Km 9 Carretera al Norte, Santa Cruz de la Sierra',
    'Carretera a Warnes Km 8, Santa Cruz de la Sierra',
    NOW() - INTERVAL '4 days',
    CURRENT_DATE - INTERVAL '2 days',
    NOW() - INTERVAL '1 day',
    'ENTREGADA',
    'Entrega confirmada por Ricardo Montano Encinas. Insumos recibidos en buen estado.',
    'data:image/jpeg;base64,<base64_placeholder>'
WHERE NOT EXISTS (SELECT 1 FROM AGROENLACE.RUTA_LOGISTICA WHERE id_ruta = 103);

-- ============================================================================
-- 6. AJUSTE DE STOCK (bodega AgroExport)
-- ============================================================================
UPDATE AGROENLACE.bodega SET stock_actual = stock_actual - 110 WHERE id_producto = 1 AND id_empresa = 1;
UPDATE AGROENLACE.bodega SET stock_actual = stock_actual - 20  WHERE id_producto = 2 AND id_empresa = 1;
UPDATE AGROENLACE.bodega SET stock_actual = stock_actual - 25  WHERE id_producto = 4 AND id_empresa = 1;
UPDATE AGROENLACE.bodega SET stock_actual = stock_actual - 70  WHERE id_producto = 9 AND id_empresa = 1;

-- ============================================================================
-- 7. SINCRONIZAR SECUENCIAS
-- ============================================================================
SELECT setval(pg_get_serial_sequence('agroenlace.usuario', 'id_usuario'),
    COALESCE((SELECT MAX(id_usuario) FROM AGROENLACE.USUARIO), 1));

SELECT setval(pg_get_serial_sequence('agroenlace.transaccion_comercial', 'nro_transaccion'),
    COALESCE((SELECT MAX(nro_transaccion) FROM AGROENLACE.TRANSACCION_COMERCIAL), 1));

SELECT setval(pg_get_serial_sequence('agroenlace.ruta_logistica', 'id_ruta'),
    COALESCE((SELECT MAX(id_ruta) FROM AGROENLACE.RUTA_LOGISTICA), 1));

COMMIT;

-- ============================================================================
-- VERIFICACION
-- ============================================================================
SELECT 'Seed AgroExport S.A. ejecutado correctamente' AS resultado;

SELECT '-- EMPRESA --' AS info;
SELECT id_empresa, nombre_empresa, nit, estado
FROM AGROENLACE.empresa WHERE id_empresa = 1;

SELECT '-- USUARIOS AgroExport --' AS info;
SELECT u.id_usuario, u.nombre_razon_social, u.user_name, r.nombre_rol
FROM AGROENLACE.USUARIO u
INNER JOIN AGROENLACE.ROL r ON r.id = u.id_rol
WHERE u.id_empresa = 1
ORDER BY u.id_usuario;

SELECT '-- PEDIDOS PENDIENTES (logistica) --' AS info;
SELECT t.nro_transaccion, t.estado_transaccion, t.monto_total, u.nombre_razon_social AS cliente
FROM AGROENLACE.TRANSACCION_COMERCIAL t
INNER JOIN AGROENLACE.USUARIO u ON u.id_usuario = t.id_cliente
WHERE t.id_empresa = 1 AND t.tipo_transaccion = 'PEDIDO_INSUMO'
ORDER BY t.nro_transaccion;

SELECT '-- RUTAS LOGISTICAS AgroExport --' AS info;
SELECT r.id_ruta, r.id_transaccion, c.nombre_razon_social AS chofer, r.estado, r.destino
FROM AGROENLACE.RUTA_LOGISTICA r
INNER JOIN AGROENLACE.USUARIO c ON c.id_usuario = r.id_chofer
WHERE r.id_empresa = 1
ORDER BY r.id_ruta;
