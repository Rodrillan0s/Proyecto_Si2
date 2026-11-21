# Decisión Arquitectónica: Poblado Coherente de Datos Multitenant para Casos de Uso y Reportes de Obras Civiles en Bolivia

**Fecha:** 2026-11-05  
**Autores:** Equipo de Arquitectura OBRATEC / Antigravity  
**Estado:** Implementado y Validado (Sembrado transaccional en PostgreSQL completado; rentabilidad y déficit verificados; consultas de IA validadas; 41/41 tests pasando)  
**Ámbito:** Base de datos relacional PostgreSQL (esquema `obras`), Cobertura de CUs (CU1 a CU39), Reportes de Rentabilidad/Déficit y Asistentes de IA.

---

## 1. Contexto y Justificación

Al consultar al asistente comercial y administrativo por reportes analíticos clave (especialmente `"Generame un reporte de las obras con mas deficit"` o consultas de stock crítico e inventario), el sistema reportaba falta de datos suficientes o respuestas vacías (`SIN_DATOS_SUFICIENTES`).

Una inspección técnica detallada del esquema relacional `obras` (93 tablas) reveló:
1. `t_unidad_construccion` contenía solo 6 registros en toda la base de datos.
2. `t_crm_cliente_unidad` contenía solo 1 registro (en estado `RESERVADO`, sin ventas formalizadas).
3. `t_control_costo_obra` tenía líneas base activas únicamente en 4 obras, con solo 11 registros dispersos en `t_costo_ejecutado`.
4. El repositorio `backend/app/repos/reportes_repos.py` calcula el `saldo_comercial` evaluando estrictamente:
   - $Monto\ Pactado = \sum (cu.monto\_pactado)$ donde `cu.estado_asociacion IN ('VENDIDO', 'ENTREGADO')`.
   - $Costos\ Registrados = \sum (ce.monto)$ donde `cc.estado = 'ACTIVO'` y `ce.estado = 'REGISTRADO'`.
   - $Saldo\ Estimado = Monto\ Pactado - Costos\ Registrados$.
   - Si no existen unidades vendidas o costos registrados, clasifica la obra como `SIN_DATOS_SUFICIENTES`.
   - Si $Costos > Ventas$, clasifica como `SALDO_NEGATIVO` (déficit).
   - Si $Ventas \ge Costos$, clasifica como `SALDO_POSITIVO` (ganancia).

Para que todos los casos de uso (CU1 a CU39), el catálogo de reportes analíticos y los asistentes de lenguaje natural funcionen con total verosimilitud operativa, se requiere poblar datos coherentes y calibrados basados en estadísticas de la industria de la construcción civil en Bolivia (Santa Cruz, La Paz y Cochabamba).

---

## 2. Principios de Diseño y Restricciones de Dominio

Conforme a las directrices de `AGENTS.md` y `docs/ARQUITECTURA_BASE_DATOS.md`:
1. **Aislamiento Multi-Tenant Estricto (`id_empresa`):** Toda entidad pertenece a su tenant correspondiente (1: OBRATEC, 2: Clientes Sin Empresa, 3: LA ROCA, 4: EL GRAN PIRAI). No se cruzan referencias entre empresas.
2. **Restricción de Unicidad 1 a 1 de Estructura-Unidad:** `obras.t_unidad_construccion` posee una restricción única `uq_unidad_estructura (id_estructura)`. Toda unidad debe vincularse a un nodo terminal único de `obras.t_estructura_obra`.
3. **Consistencia Financiera en Costos Ejecutados:** `obras.t_costo_ejecutado` exige la restricción `chk_costo_ejecutado_monto: monto = round(cantidad * costo_unitario, 2)`. El `monto` se computa con precisión exacta. Cada costo ejecutado debe referenciar a una partida válida de `t_estimacion_analisis_precio_unitario`.
4. **Restricciones de Estado de Incidencias:** `chk_incidencia_fechas_estado` exige que incidencias `ABIERTA`/`ASIGNADA` no tengan fechas de atención; `EN_PROCESO` tenga `fecha_inicio_atencion`; y `RESUELTA`/`CERRADA` tengan tanto inicio como fin con fin $\ge$ inicio.
5. **Calibración Financiera Realista Bolivia:**
   - **Pocas obras con Déficit Realista (`SALDO_NEGATIVO`):**
     - *Obra 17 (Garden Zen - OBRATEC, BOB):* Déficit de -15.01% por nivel freático alto, lluvias atípicas y necesidad de bombeo continuo y micropilotes.
     - *Obra 7 (Edificio Laguna - LA ROCA, USD):* Déficit de -13.27% por cimentación en suelo arcilloso blando y demoras con penalidad en importación de muro cortina.
     - *Obra 28 (Módulo Educativo Plan 3000 - EL GRAN PIRAI, BOB):* Déficit de -9.16% por escalamiento de precios de acero de importación y fallas de subcontratista eléctrico.
   - **Obras con Margen Positivo Saludable (`SALDO_POSITIVO`, 15% a 25% de utilidad):**
     - *Obra 26 (Edificio Sky Equipetrol - OBRATEC, BOB):* +22.26% margen.
     - *Obra 8 (Green Tower - OBRATEC, BOB):* +19.07% margen.
     - *Obra 27 (Condominio Campestre Urubo Village - LA ROCA, BOB):* +25.02% margen.
     - *Obra 12 (Parque Residencial - LA ROCA, USD):* +19.17% margen.
     - *Obra 9 (Parque Los Mangales - EL GRAN PIRAI, BOB):* +15.38% margen.
     - *Obra 29 (Centro de Salud Villa 1ro de Mayo - EL GRAN PIRAI, BOB):* +19.67% margen.
     - *Obra 4 (Edificaciones P2026-08-0003 - Tenant 2, BOB):* +18.98% margen.
     - *Obra 6 (Edificio Solaris - Tenant 2, USD):* +18.09% margen.

---

## 3. Cobertura por Casos de Uso (CUs)

| Caso de Uso | Módulo / Tablas Afectadas | Datos Poblados |
| :--- | :--- | :--- |
| **CU1 - CU10, CU12** | Estructuras, Unidades, Modelos, Ambientes, Características | `t_estructura_obra`, `t_modelo_unidad`, `t_unidad_construccion`, `t_unidad_ambiente`, `t_unidad_caracteristica`, `t_unidad_personalizacion`, `t_avance_obra`. Metrajes y acabados reales. |
| **CU11, CU13, CU14, CU15, CU35, CU36** | Proveedores, Materiales, Almacenes, Movimientos, Órdenes de Compra | `t_proveedor` (Soboce, Las Lomas, Warnes, Incacer), `t_material`, `t_materiales_almacen` (artículos normales, `STOCK_BAJO` y `SIN_STOCK` para HU111), `t_movimiento_almacen`, `t_orden_compra`, `t_orden_compra_detalle`. |
| **CU16, CU17, CU18, CU22, CU39** | Estimaciones, APUs, Control de Costos, Costos Ejecutados | `t_parametro_estimacion`, `t_analisis_precio_unitario`, `t_estimacion`, `t_estimacion_analisis_precio_unitario`, `t_control_costo_obra` (`ACTIVO`), `t_costo_ejecutado` (`REGISTRADO`). |
| **CU19, CU20, CU23, CU24, CU25** | Órdenes de Trabajo, Incidencias, Consultas Técnicas, Asignación Personal | `t_orden_trabajo`, `t_orden_trabajo_usuario`, `t_obra_usuario`, `t_incidencia`, `t_incidencia_seguimiento`. Estados acordes al ciclo de vida. |
| **CU21, CU34** | CRM Clientes, Ventas, Reservas, Interacciones | `t_persona`, `t_crm_cliente`, `t_crm_cliente_unidad` (`VENDIDO`, `ENTREGADO`, `RESERVADO`), `t_crm_interaccion`. |
| **CU28, CU32, CU33** | Cronogramas, WBS, Maquinaria y Equipos | `t_cronograma`, `t_cronograma_actividad` (claves WBS válidas), `t_equipo_maquinaria`, `t_equipo_maquinaria_obra`. |

---

## 4. Plan de Ejecución y Validación

1. **Script de Sembrado Idempotente:** Desarrollar `backend/database/poblar_datos_coherentes_bolivia.py` con transaccionalidad por bloques y control de duplicados (`ON CONFLICT` o verificación previa).
2. **Ejecución y Verificación de Tablas:** Ejecutar contra la base de datos activa y registrar el conteo final de filas.
3. **Verificación de `saldo_comercial`:** Correr consulta SQL de rentabilidad para certificar que las obras deficitarias (17, 7, 28) reportan saldo negativo y las demás reportan saldo positivo saludable.
4. **Verificación Asistente de IA:** Probar la consulta `"Generame un reporte de las obras con mas deficit"` con el motor de IA / contingency resolver para garantizar que devuelve las obras deficitarias ordenadas por severidad de pérdida.
5. **Regresión Automatizada:** Ejecutar la suite de pruebas unitarias (`pytest tests/test_cu34_asistente_comercial.py tests/test_reportes.py`) para ratificar 100% de aprobación.

