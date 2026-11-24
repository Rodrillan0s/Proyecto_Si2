# Nota de Arquitectura: Diagramas de Secuencia (CU35, CU36, CU23, CU34)

**Fecha:** 2026-11-02  
**Autor:** Antigravity  
**Contexto:** Generación formal de los Diagramas de Secuencia UML 2.5+ para los 4 casos de uso solicitados, directamente alineados con los Diagramas de Análisis de Clases (BCE) previamente definidos:
1. **CU35:** Registrar entrada de material (Jefe de Obra / Supervisor | Web)
2. **CU36:** Registrar salida de material (Jefe de Obra / Supervisor | Web)
3. **CU23:** Gestionar solicitudes técnicas y aclaraciones de obra - RFI (Jefe de Obra / Supervisor | Web / Móvil)
4. **CU34:** Consultar asistente comercial y recomendaciones (Cliente potencial | Web)

---

## 1. Criterios de Diseño Visual y Estándar UML

- **Esquema cromático:** Estricto blanco y negro / monocromático (fondos blancos `#FFFFFF`, trazos negros `#000000`, textos negros `#000000` y barras de activación estándar sin rellenos de color).
- **Líneas de vida (Lifelines):**
  - Actor inicial (figura humana UML).
  - Componente de interfaz de usuario (`ui : Form ...`).
  - Capa de enrutamiento API (`router : ..._routes`).
  - Capa de servicio y orquestación (`service : ..._services`).
  - Entidades de persistencia PostgreSQL (`schema: obras`).
- **Mensajería:** Mensajes síncronos continuos con flecha sólida (`->`), mensajes de retorno con trazo discontinuo (`-->`), barras de activación verticales y fragmentos combinados `alt` con etiquetas de guardia para flujos alternativos.
- **Entregables:** Vectorial SVG, Imagen PNG de alta definición y formato editable nativo Draw.io (`.drawio`).

