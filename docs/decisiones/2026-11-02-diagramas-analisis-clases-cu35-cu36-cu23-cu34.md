# Nota de Arquitectura: Diagramas de Análisis de Clases (CU35, CU36, CU23, CU34)

**Fecha:** 2026-11-02  
**Autor:** Antigravity  
**Contexto:** Generación formal de los Diagramas de Análisis de Clases (patrón Boundary - Control - Entity / BCE) para los siguientes casos de uso:
1. **CU35:** Registrar entrada de material (Jefe de Obra / Supervisor | Web)
2. **CU36:** Registrar salida de material (Jefe de Obra / Supervisor | Web)
3. **CU23:** Gestionar solicitudes técnicas y aclaraciones de obra - RFI (Jefe de Obra / Supervisor | Web / Móvil)
4. **CU34:** Consultar asistente comercial y recomendaciones (Cliente potencial | Web)

---

## 1. Patrón Arquitectónico del Diagrama de Análisis

Siguiendo el estándar visual UML solicitado:
- **Boundary (Formulario / Interfaz Front):** Modela el componente visual que captura los datos de entrada del usuario y dispara las acciones del cliente (`Form ...`).
- **Control (Controlador / Servicio Back):** Modela la lógica de negocio y orquestación del backend en FastAPI (`Control ...`).
- **Entity (Entidad Central y Relacionadas):** Modela la persistencia en base de datos PostgreSQL (`schema: obras`), con sus atributos reales, llaves y cardinalidades.

---

## 2. Casos de Uso Modelados

### CU35: Registrar entrada de material
- **Actor:** Jefe de Obra / Supervisor (Web).
- **Boundary:** `Form Registrar_Entrada_Material`.
- **Control:** `Control_Inventario`.
- **Entidades:** `MATERIAL` (Central), `MOVIMIENTO_ALMACEN`, `CATEGORIA_MATERIAL`, `UNIDAD_MEDIDA`, `USUARIO`, `EMPRESA`.

### CU36: Registrar salida de material
- **Actor:** Jefe de Obra / Supervisor (Web).
- **Boundary:** `Form Registrar_Salida_Material`.
- **Control:** `Control_Despacho_Inventario`.
- **Entidades:** `MATERIAL` (Central), `MOVIMIENTO_ALMACEN`, `CATEGORIA_MATERIAL`, `UNIDAD_MEDIDA`, `USUARIO`, `EMPRESA`.

### CU23: Gestionar solicitudes técnicas y aclaraciones de obra (RFI)
- **Actor:** Jefe de Obra / Supervisor (Web / Móvil).
- **Boundary:** `Form Consultas_Tecnicas_RFI`.
- **Control:** `Control_Consultas_Tecnicas`.
- **Entidades:** `CONSULTA_TECNICA` (Central), `CONSULTA_TECNICA_RESPUESTA`, `CONSULTA_TECNICA_HISTORIAL`, `OBRA`, `USUARIO`, `EMPRESA`.

### CU34: Consultar asistente comercial y recomendaciones
- **Actor:** Cliente potencial (Web).
- **Boundary:** `Form Asistente_Comercial_Recomendaciones`.
- **Control:** `Control_Asistente_Comercial`.
- **Entidades:** `CRM_CLIENTE` (Central), `CRM_INTERACCION`, `UNIDAD_CONSTRUCCION`, `MODELO_UNIDAD`, `ASISTENTE_CONVERSACION`, `ASISTENTE_MENSAJE`, `EMPRESA`.

---

## 3. Entregables
- Formatos vectoriales SVG individuales y consolidados.
- Formatos de imagen PNG en alta definición (renderizados con `resvg_py`).
- Formatos editables nativos `.drawio` con soporte multipágina para Diagrams.net.

