# Nota de Arquitectura y Diseño: Diagrama Relacional UML de la Base de Datos (Esquema `obras`)

**Fecha:** 2026-11-02  
**Autor:** Antigravity  
**Contexto:** Generación formal del Diagrama de Entidad-Relación bajo notación estándar UML (Clases / Tablas relacionales con visibilidad de atributos, llaves PK/FK y cardinalidades) en formato vectorial SVG y formato rasterizado de alta definición PNG/JPEG, a partir del volcado exhaustivo del esquema `obras` (92 tablas, 196 claves foráneas).

---

## 1. Contexto y Objetivos

El sistema OBRATEC opera con una base de datos PostgreSQL multi-inquilino (`id_empresa`) bajo el esquema `obras`. Se requiere documentar visual y formalmente la totalidad de entidades, atributos, claves primarias, claves foráneas y relaciones cardinales en concordancia con el modelo visual estándar de diagramas UML relacionales (estilo Enterprise Architect / Visual Paradigm):
- Caja rectangular con fondo blanco `#FFFFFF`, borde nítido `#222222` y sombra sutil.
- Encabezado con icono representativo UML `[=]` y nombre de entidad en mayúsculas centradas en negrita.
- Separador horizontal continuo.
- Lista vertical de atributos con prefijo `+` (visibilidad pública UML) indicando nombres de atributos, tipo y marcas de clave `[PK]` y `[FK]`.
- Enlaces relacionales ortogonales con anotación explícita de cardinalidad (`1` a `0..*`, `1..*`).

---

## 2. Segmentación de Dominios y Módulos

Debido a la magnitud del esquema (92 tablas), la arquitectura relacional se estructura en 9 dominios cohesivos:

1. **Seguridad, Usuarios y SaaS Multitenant**:
   - Tablas: `t_persona`, `t_usuario`, `t_seguridad_usuario`, `t_rol`, `t_permiso`, `t_rol_permiso`, `t_modulo`, `t_bitacora`, `t_empresa`, `t_plan_suscripcion`, `t_plan_precio_saas`, `t_plan_suscripcion_historial`, `t_suscripcion_empresa`, `t_suscripcion_cupo`, `t_suscripcion_historial`, `t_suscripcion_ia_uso`, `t_pago_suscripcion`.
2. **Gestión de Obras y Proyectos**:
   - Tablas: `t_obra`, `t_tipo_obra`, `t_detalle_obra`, `t_estructura_obra`, `t_obra_usuario`, `t_avance_obra`, `t_consulta_tecnica`, `t_consulta_tecnica_respuesta`, `t_consulta_tecnica_historial`, `t_incidencia`, `t_incidencia_evidencia`, `t_incidencia_seguimiento`, `t_incidencia_orden_trabajo`.
3. **Planificación y Cronogramas (CU39)**:
   - Tablas: `t_cronograma`, `t_cronograma_actividad`, `t_cronograma_dependencia`.
4. **Presupuestos, APU y Estimaciones**:
   - Tablas: `t_unidad_medida`, `t_presupuesto`, `t_partida_presupuesto`, `t_analisis_precio_unitario`, `t_analisi_precio_unitario_insumo`, `t_estimacion`, `t_estimacion_analisis_precio_unitario`, `t_parametro_estimacion`, `t_obra_estimacion`, `t_apu_detalle_mano_obra_archivo`, `t_apu_legacy_archive`.
5. **Control de Costos y Órdenes de Trabajo / Cambio**:
   - Tablas: `t_control_costo_obra`, `t_costo_ejecutado`, `t_costo_ejecutado_legacy`, `t_orden_cambio`, `t_orden_cambio_detalle`, `t_orden_cambio_historial`, `t_orden_trabajo`, `t_orden_trabajo_usuario`, `t_orden_trabajo_permiso`, `t_usuario_orden_trabajo_permiso`.
6. **Mano de Obra y Jornadas (CU32)**:
   - Tablas: `t_mano_obra`, `t_salario_trabajador`, `t_jornada_trabajador_obra`, `t_cu32_mano_obra_cierre`.
7. **Materiales, Compras y Almacén**:
   - Tablas: `t_categoria_material`, `t_material_base`, `t_material`, `t_material_caracteristica`, `t_materiales_almacen`, `t_movimiento_almacen`, `t_proveedor`, `t_proveedor_material`, `t_orden_compra`, `t_orden_compra_detalle`, `t_recepcion_compra`, `t_recepcion_compra_detalle`, `t_equipo`, `t_equipo_maquinaria`, `t_equipo_maquinaria_obra`.
8. **Inmobiliaria, Unidades y CRM**:
   - Tablas: `t_unidad_construccion`, `t_modelo_unidad`, `t_modelo_caracteristica`, `t_unidad_ambiente`, `t_unidad_caracteristica`, `t_unidad_material`, `t_unidad_personalizacion`, `t_unidad_seguimiento`, `t_crm_cliente`, `t_crm_cliente_unidad`, `t_crm_interaccion`.
9. **Reportes, Asistente IA y Notificaciones**:
   - Tablas: `notificacion`, `t_asistente_conversacion`, `t_asistente_mensaje`, `t_reporte_ejecucion`, `t_reporte_archivo`, `t_reporte_envio`, `t_reporte_programacion`, `t_reporte_programacion_destinatario`.

---

## 3. Estrategia de Renderizado y Enrutamiento Ortogonal

1. **Eliminación de Cruzamientos en Telaraña ("Hilos")**:
   - Se eliminaron las curvas y diagonales caóticas.
   - Implementación de **enrutamiento ortogonal Manhattan (estricto a 90°)** transitando exclusivamente por los canales/calles entre cajas.
   - Co-localización topológica: Las tablas con dependencias directas están situadas contiguas (adyacencia horizontal y vertical inmediata).
   - Manejo del multi-inquilino y auditoría: Las claves globales `id_empresa` y atributos recurrentes de auditoría se documentan de forma limpia directamente en el listado de atributos de cada clase (`+ id_empresa [FK]`, `+ creado_por [FK]`), evitando que 60 líneas diagonales crucen sobre otras clases.
   - Trazado de relaciones estructurales de negocio mediante canales ortogonales limpios con multiplicidades `1` a `0..*`.

2. **Entregables y Formatos Soportados**:
   - Vectorial SVG: `docs/diagramas/diagrama_clases_completo.svg`.
   - Imagen PNG de alta definición: `docs/diagramas/diagrama_clases_completo.png`.
   - **Formato editable nativo para Draw.io (`.drawio` / `.xml`)**: `docs/diagramas/diagrama_clases_completo.drawio` y `docs/diagramas/diagrama_clases_completo.xml`. Cada tabla es un componente interactivo tipo `swimlane`, con filas editables individualmente para cada atributo y conectores ortogonales dinámicos con etiquetas de cardinalidad (`1`, `0..*`).

