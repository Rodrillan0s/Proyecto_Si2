# Decisión Arquitectónica: CU35 y CU36 — Gestión de Entradas y Salidas de Materiales

**Fecha:** 2026-10-26  
**Autor:** Antigravity Pairing Assistant  
**Casos de Uso:**
- **CU35:** Registrar entrada de material (Recepción, cantidades, proveedor y supervisión)
- **CU36:** Registrar salida de material (Solicitud/autorización, despacho y descuento de stock)
**Actores:**
- **Supervisor:** Registra recepción física de insumos y ejecuta salidas/despachos físicos actualizando el inventario.
- **Jefe de Obra:** Consulta y supervisa ingresos al proyecto; solicita y autoriza la utilización de materiales para frentes de trabajo.
**Alcance:** PostgreSQL (`schema: obras`), FastAPI (`inventario_routes`), Angular, Flutter.  
**Estado:** Especificado y modelado bajo UML 2.5+.

---

## 1. Contexto de Negocio y Responsabilidades

En la ejecución de obras civiles, el flujo de insumos y materiales es crítico para el control de costos y cumplimiento de cronogramas:
1. **CU35 — Registrar entrada de material:**
   - **Supervisor:** Realiza el cotejo físico de la remisión/guía contra los materiales recibidos (cemento, acero, áridos, tuberías), valida cantidades, proveedor, lote y fecha de ingreso, incrementando el stock físico disponible en almacén de obra.
   - **Jefe de Obra:** Monitorea y audita el historial de recepciones en tiempo real para contrastarlo contra el plan de adquisiciones y avances del proyecto.
2. **CU36 — Registrar salida de material:**
   - **Jefe de Obra:** Evalúa las necesidades de las cuadrillas y autoriza la utilización de materiales para un frente o tarea específica, emitiendo la solicitud/orden de entrega.
   - **Supervisor:** Despacha físicamente el material, verifica la existencia de stock disponible suficiente y descuenta el inventario, previniendo sobreconsumos o desvíos.

---

## 2. Aislamiento Multitenant y Patrón de Arquitectura

El flujo preserva la arquitectura establecida:
`Cliente UI (Angular / Flutter) → Security / SaaS Barrier → Router → Service → Repositorio → PostgreSQL (schema: obras)`

- **Aislamiento Multitenant:** Toda operación de entrada o salida valida estrictamente `id_empresa` extraído del JWT criptográfico y la pertenencia de la obra asociada (`id_obra`).
- **Transaccionalidad Atómica:** El incremento o decremento de stock en `t_material` se ejecuta en la misma transacción que la inserción del registro histórico en `t_movimiento_almacen` y el evento de auditoría en `bitacora`.
- **Integridad de Stock:** Se aplica validación estricta (`stock_actual >= cantidad_salida`), bloqueando salidas que generen inventario negativo.

---

## 3. Diagramas de Diseño UML 2.5+ Separados

Se han generado diagramas vectoriales independientes para cada caso de uso:

### CU35 — Registrar entrada de material
- **Diagrama de Comunicación (BCE):** [docs/diagramas/diagrama_comunicacion_cu35.svg](../diagramas/diagrama_comunicacion_cu35.svg)  
  *(Flechas normales en color negro, roles: Supervisor y Jefe de Obra).*
- **Diagrama de Secuencia (UML 2.5+):** [docs/diagramas/diagrama_secuencia_cu35.svg](../diagramas/diagrama_secuencia_cu35.svg)  
  *(Recepción por Supervisor y supervisión de kardex por Jefe de Obra).*

### CU36 — Registrar salida de material
- **Diagrama de Comunicación (BCE):** [docs/diagramas/diagrama_comunicacion_cu36.svg](../diagramas/diagrama_comunicacion_cu36.svg)  
  *(Flechas normales en color negro, roles: Jefe de Obra y Supervisor).*
- **Diagrama de Secuencia (UML 2.5+):** [docs/diagramas/diagrama_secuencia_cu36.svg](../diagramas/diagrama_secuencia_cu36.svg)  
  *(Autorización por Jefe de Obra, fragmento alt para validación de stock y descuento por Supervisor).*
