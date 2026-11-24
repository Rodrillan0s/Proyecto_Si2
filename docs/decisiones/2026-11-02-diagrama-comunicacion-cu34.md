# Nota de Arquitectura: Diagrama de Comunicación UML (CU34)

**Fecha:** 2026-11-02  
**Autor:** Antigravity  
**Caso de Uso:** **CU34 — Consultar asistente comercial y recomendaciones**  
**Actor:** Cliente potencial (Web)  
**Alcance:** Modelado formal de colaboración/comunicación UML 2.5+ en estricto blanco y negro.

---

## 1. Mapeo de Objetos y Roles de Comunicación

En concordancia con el Diagrama de Secuencia y el Diagrama de Análisis de Clases (BCE):
- `:Actor` $\rightarrow$ `user : Cliente_Potencial`
- `:Boundary` $\rightarrow$ `ui : Form_Asistente_Comercial`
- `:Router` $\rightarrow$ `router : ai_routes`
- `:Control` $\rightarrow$ `service : Control_Asistente_Comercial`
- `:Entity` $\rightarrow$ `t_asistente_conversacion`
- `:Entity` $\rightarrow$ `t_unidad_construccion`
- `:Entity` $\rightarrow$ `t_crm_cliente`

---

## 2. Flujo Secuencial Numerado de Mensajes

1. `user` $\rightarrow$ `ui`: `1: ingresar_consulta("Busco depto 2 dorms", presupuesto)`
2. `ui` $\rightarrow$ `router`: `2: POST /api/ai/crm/consulta (pregunta, presupuesto)`
3. `router` $\rightarrow$ `service`: `3: consultar_crm_ia(pregunta, presupuesto, token, ip)`
4. `service` $\rightarrow$ `t_asistente_conversacion`: `4: SELECT / INSERT sesion_conversacion(id_cliente)`
5. `t_asistente_conversacion` $\rightarrow$ `service`: `5: return id_conversacion`
6. `service` $\rightarrow$ `t_unidad_construccion`: `6: SELECT * FROM t_unidad_construccion WHERE estado='DISPONIBLE'`
7. `t_unidad_construccion` $\rightarrow$ `service`: `7: return lista_unidades_compatibles`
8. `service` $\rightarrow$ `service`: `8: generar_analisis_recomendaciones_ia()`
9. `service` $\rightarrow$ `t_asistente_conversacion`: `9: INSERT INTO t_asistente_mensaje (conversacion, texto, respuesta)`
10. `service` $\rightarrow$ `t_crm_cliente`: `10: UPDATE t_crm_cliente SET clasificacion='INTERESADO'`
11. `service` $\rightarrow$ `router`: `11: return {respuesta_ia, unidades_recomendadas, sugerencias}`
12. `router` $\rightarrow$ `ui`: `12: 200 OK (Mensaje IA y tarjetas de unidades)`
13. `ui` $\rightarrow$ `ui`: `13: renderizar_mensajes_y_tarjetas_inmuebles()`
14. `ui` $\rightarrow$ `user`: `14: visualizar_recomendaciones_comerciales()`

---

## 3. Criterios Visuales y Entregables
- Esquema monocromático estricto (blanco y negro).
- Nodos rectangulares con borde nítido `#000000` y fondo blanco `#FFFFFF`.
- Trazado de enlaces estructurales y mensajes direccionales adyacentes a cada enlace con flechas indicativas de flujo (`→` / `←`).
- Entregables: SVG, PNG de alta definición y archivo editable nativo para Draw.io (`.drawio`).

