# Reporte de Validación de Diagramas — CU33: Gestionar Garantías y Servicio Posventa Inmobiliario

**Fecha:** 2026-11-24  
**Caso de Uso:** CU33 – Gestionar Garantías y Servicio Posventa Inmobiliario  
**Historias de Usuario Cubiertas:** HU161, HU162, HU163, HU164, HU165, HU166, HU167, HU168  
**Estándar Aplicado:** UML 2.5.1 y Kit Reusable ICONIX v1 (Regla: *Un Caso de Uso = Un Diagrama por Tipo*)

---

## 1. Inventario de Artefactos Generados

| Diagrama | Formato Editable (.drawio) | Fuente PlantUML (.puml) | Vector (.svg) | Imagen (.png) |
|---|---|---|---|---|
| **Robustez ICONIX (BCE)** | [CU33-robustez.drawio](CU33-robustez.drawio) | [CU33-robustez.puml](CU33-robustez.puml) | [CU33-robustez.svg](CU33-robustez.svg) | [CU33-robustez.png](CU33-robustez.png) |
| **Secuencia UML 2.5.1 (MVC)** | [CU33-secuencia.drawio](CU33-secuencia.drawio) | [CU33-secuencia.puml](CU33-secuencia.puml) | [CU33-secuencia.svg](CU33-secuencia.svg) | [CU33-secuencia.png](CU33-secuencia.png) |
| **Comunicación UML 2.5.1** | [CU33-comunicacion.drawio](CU33-comunicacion.drawio) | [CU33-comunicacion.puml](CU33-comunicacion.puml) | [CU33-comunicacion.svg](CU33-comunicacion.svg) | [CU33-comunicacion.png](CU33-comunicacion.png) |
| **Clases de Análisis UML 2.5.1** | [CU33-clases-analisis.drawio](CU33-clases-analisis.drawio) | [CU33-clases-analisis.puml](CU33-clases-analisis.puml) | [CU33-clases-analisis.svg](CU33-clases-analisis.svg) | [CU33-clases-analisis.png](CU33-clases-analisis.png) |
| **Diagrama de Tiempo UML 2.5.1** | [CU33-tiempo.drawio](CU33-tiempo.drawio) | N/A (Nativo Draw.io) | N/A | N/A |
| **Matriz Canónica de Mensajes** | [CU33-matriz.csv](CU33-matriz.csv) | N/A | N/A | N/A |

---

## 2. Resultados de las Pruebas de Validación Estructural

Se ejecutaron las herramientas del kit reusable sobre los archivos `.drawio` nativos:

### 2.1 Validación Estructural XML (`validate_drawio.py`)
```text
=== Validando: CU33-clases-analisis.drawio
Found 10 editable vertices and 11 editable edges.
PASS XML structure and edge references.

=== Validando: CU33-comunicacion.drawio
Found 13 editable vertices and 11 editable edges.
PASS XML structure and edge references.

=== Validando: CU33-robustez.drawio
Found 14 editable vertices and 12 editable edges.
PASS XML structure and edge references.

=== Validando: CU33-secuencia.drawio
Found 139 editable vertices and 55 editable edges.
PASS XML structure and edge references.

=== Validando: CU33-tiempo.drawio
Found 31 editable vertices and 7 editable edges.
PASS XML structure and edge references.

Resultado: 5 de 5 diagramas aprobados (0 fallos).
```

### 2.2 Verificación de Solapamientos (`check_box_collisions.py`)
- Todos los elementos hijos se encuentran correctamente anidados dentro de los marcos o cuadros swimlane contenedores (`frame`).
- Cero solapamientos espurios entre etiquetas de texto, nodos o aristas de mensajes.

---

## 3. Trazabilidad con Código y Requisitos

1. **Actores:** `Administrador_empresa`, `Cliente`, `Jefe de Obra`, `Supervisor`.
2. **Límite («boundary»):** `UIPosventa` encapsula las vistas web (`frontend/src/app/pages/posventa/`) y móvil (`mobile/lib/screens/posventa_screen.dart`).
3. **Control («control»):** `GestorPosventa` coordina las reglas de negocio descritas en `posventa_services.py` y expuestas por `posventa_routes.py`.
4. **Entidades («entity»):** Mapeo 1:1 con las tablas de PostgreSQL `obras`:
   - `UnidadGarantia` ↔ `t_unidad_garantia`
   - `SolicitudPosventa` ↔ `t_posventa_solicitud`
   - `BitacoraPosventa` ↔ `t_posventa_bitacora`
   - `EvidenciaPosventa` ↔ `t_posventa_evidencia`
   - `UnidadConstruccion` ↔ `t_unidad_construccion`
   - `ClienteCRM` ↔ `t_crm_cliente`
   - `Usuario` ↔ `t_usuario`
