# Nota de Arquitectura: Diagramas de Actividades del Sprint — Sprint Planning

**Fecha:** 2026-11-22  
**Contexto del Sistema — Sprint Planning:**  
- Estructura de Casos de Uso del Sprint
- Diagramas de Actividades UML para los 6 Casos de Uso del Sprint (Geometría rigurosa, Cero Solapamientos, Renderizado de Alta Definición y Estilo Académico en Blanco y Negro)

---

## 1. Casos de Uso del Sprint Modelados

1. **CU22 (W/M) – Gestionar comunicaciones y notificaciones:**  
   Representa la redacción de comunicados, selección de canales (push, email, in-app), validación de preferencias, despacho prioritario/asíncrono y confirmación de lectura.
2. **CU30 (W/M) – Consultar proyectos y unidades como cliente:**  
   Representa la exploración del catálogo inmobiliario, consulta de fichas técnicas y planos, verificación de disponibilidad, simulación de pagos y solicitud de cotización/atención comercial.
3. **CU31W – Gestionar comercialización de unidades inmobiliarias:**  
   Representa el ciclo de reserva, validación de solvencia, aprobación gerencial y formalización de la venta con contrato y actualización de inventario.
4. **CU40 (W/M) – Gestionar inspecciones y control de calidad:**  
   Representa la inspección técnica en terreno, registro de observaciones y defectos, evaluación de conformidad y bucle de acciones correctivas con reinspección.
5. **CU41M – Gestionar operación offline y sincronización:**  
   Representa la operación sin conexión en faena, almacenamiento local en SQLite, detección de red y sincronización atómica con resolución de conflictos de concurrencia.
6. **CU42 (W/M) – Gestionar garantías y servicio posventa inmobiliaria:**  
   Representa el registro de reclamos por el propietario, clasificación de póliza, asignación de técnico, atención en sitio y resolución formal del ticket de garantía.

---

## 2. Correcciones Geométricas y Estándar Visual

- **Cero superposición de cabeceras:** El nodo de inicio (`start` circle) se ubica holgadamente por debajo de la cabecera de los carriles (`y = 135` px con cabecera a `y = 58..96` px), eliminando cualquier colisión visual con la pestaña de roles.
- **Cero superposición en flujos condicionales:** Todas las etiquetas de bifurcación (`[Sí]`, `[No]`, condiciones de guarda) cuentan con cajas de fondo blanco opaco (`fill="#FFFFFF"` / `labelBackgroundColor=#FFFFFF`), garantizando legibilidad nítida sin cortar ni chocar con las flechas ortogonales.
- **Ruteo Manhattan Limpio y Bucles Exteriores:** Conectores a 90 grados con terminación de flecha estándar. Los ciclos de retroalimentación (como reinspección o reintento sin conexión) se enrutan por la canaleta exterior (`x = 22` px) para no cruzar ninguna caja de actividad existente.
- **Formato Nativo Draw.io:** Archivo unificado `.drawio` con 6 pestañas independientes (`mxGraphModel`), proporciones libres (`locked=0`) y edición al 100% en cualquier editor draw.io.

---

## 3. Artefactos Generados

- **Archivo Unificado Draw.io (6 Pestañas):**  
  [`docs/diagramas/diagramas_actividades.drawio`](../diagramas/diagramas_actividades.drawio)
- **Vistas Previas en Alta Definición:**
  - `act_cu22_comunicaciones.png` / `.svg`
  - `act_cu30_consulta_proyectos.png` / `.svg`
  - `act_cu31_comercializacion.png` / `.svg`
  - `act_cu40_inspecciones_calidad.png` / `.svg`
  - `act_cu41_operacion_offline.png` / `.svg`
  - `act_cu42_garantias_posventa.png` / `.svg`
