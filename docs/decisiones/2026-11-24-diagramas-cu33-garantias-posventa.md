# Decisión Arquitectónica: Modelado y Generación de Diagramas para CU33 (Garantías y Posventa Inmobiliario)

**Fecha:** 2026-11-24 (America/La_Paz)  
**Autor:** Agente Antigravity / Hassan Clemente  
**Alcance:** Modelado UML 2.5.1 e ICONIX para el caso de uso **CU33: Gestionar Garantías y Servicio Posventa Inmobiliario** (Historias de Usuario HU161 a HU168).

---

## 1. Contexto y Objetivos

El caso de uso **CU33: Gestionar Garantías y Servicio Posventa Inmobiliario** centraliza la atención posentrega de unidades habitacionales comercializadas, estableciendo la trazabilidad técnica, legal y comercial entre el propietario (`Cliente`), la constructora (`Administrador_empresa`, `Jefe de Obra`) y el personal técnico de campo (`Supervisor`).

Tras la implementación completa del módulo en Backend (FastAPI + PostgreSQL `obras`), Frontend (Angular 20) y Móvil (Flutter), se requiere generar los artefactos formales de análisis y diseño conforme a los estándares de UML 2.5.1 y el kit reusable ICONIX v1:
1. **Diagrama de Robustez ICONIX (BCE):** Mapeo de objetos límite (Boundary), controles de proceso y entidades de dominio para las 8 operaciones.
2. **Diagrama de Secuencia UML 2.5.1 (MVC):** Interacción temporal ordenada entre Actores, Interfaz, Controlador y Entidades de dominio.
3. **Diagrama de Comunicación UML 2.5.1:** Red topológica de colaboración entre objetos con mensajes numerados sobre los enlaces de conexión.
4. **Diagrama de Clases de Análisis UML 2.5.1:** Estructura estática de clases de análisis con atributos tipados, operaciones y relaciones de cardinalidad y asociación.
5. **Diagrama de Tiempo UML 2.5.1:** Ciclo de vida y transición de estados del ticket de servicio de posventa (`t_posventa_solicitud`).

---

## 2. Decisiones Arquitectónicas y Reglas Aplicadas

### 2.1 Regla "Un Caso de Uso = Un Diagrama por Tipo"
Siguiendo las directrices normativas del kit de análisis:
- No se fragmentan las operaciones en múltiples subdiagramas por pantalla o CRUD.
- Las 8 operaciones (HU161 a HU168) se articulan en **un único lienzo por tipo de diagrama**, garantizando la visión integral del flujo de negocio.

### 2.2 Perfil de Análisis MVC
- **Actores:** `Administrador_empresa`, `Cliente`, `Jefe de Obra`, `Supervisor`.
- **Interfaces (`«boundary»`):** `UIPosventa` (unifica las vistas web Angular y móviles Flutter: formularios, bandejas de clasificación, asignación, bitácora técnica y línea de tiempo).
- **Controlador (`«control»`):** `GestorPosventa` (abstrae la capa de coordinación de FastAPI `posventa_routes` y `posventa_services`).
- **Entidades de Dominio (`«entity»`):**
  - `UnidadGarantia` (`t_unidad_garantia`): Pólizas de cobertura, tipo y vigencia.
  - `SolicitudPosventa` (`t_posventa_solicitud`): Ticket único de seguimiento posventa.
  - `BitacoraPosventa` (`t_posventa_bitacora`): Registro cronológico de acciones técnicas y materiales.
  - `EvidenciaPosventa` (`t_posventa_evidencia`): Soporte documental y multimedia (fotos).
  - `UnidadConstruccion` (`t_unidad_construccion`): Unidad inmobiliaria entregada.
  - `ClienteCRM` (`t_crm_cliente`): Propietario comprador.
  - `Usuario` (`t_usuario`): Supervisor técnico asignado.

### 2.3 Formato de Salida y Validaciones
- **PlantUML (`.puml`):** Notación estándar declarativa ejecutable con `plantuml.jar`.
- **Draw.io (`.drawio`):** XML nativo puro `<mxGraphModel>`, completamente editable, sin imágenes incrustadas ni mapas de bits empaquetados.
- **Validación Estructural:** Ejecución obligatoria de `validate_drawio.py` (geometría, celdas y referencias de aristas) y `check_box_collisions.py`.

---

## 3. Matriz de Operaciones del CU33

| ID | Operación Funcional | Actor Principal | Métodos de Control / Entidad | Entidades Involucradas |
|---|---|---|---|---|
| HU161 | Registrar Garantía | `Administrador_empresa` | `registrarGarantia(...)` | `UnidadGarantia`, `UnidadConstruccion`, `ClienteCRM` |
| HU162 | Consultar Garantías | `Cliente` / `Admin` | `consultarGarantias(...)` | `UnidadGarantia` |
| HU163 | Registrar Solicitud Posventa | `Cliente` | `registrarSolicitud(...)`, `adjuntarEvidencia(...)` | `SolicitudPosventa`, `EvidenciaPosventa`, `BitacoraPosventa` |
| HU164 | Clasificar Solicitud | `Administrador_empresa` | `clasificarSolicitud(...)`, `validarCobertura(...)` | `SolicitudPosventa`, `UnidadGarantia`, `BitacoraPosventa` |
| HU165 | Asignar Responsable | `Jefe de Obra` | `asignarResponsable(...)` | `SolicitudPosventa`, `Usuario`, `BitacoraPosventa` |
| HU166 | Gestionar Atención y Cierre | `Supervisor` | `gestionarAtencion(...)`, `registrarBitacora(...)` | `SolicitudPosventa`, `BitacoraPosventa`, `EvidenciaPosventa` |
| HU167 | Consultar Seguimiento | `Cliente` | `consultarDetalleSolicitud(...)` | `SolicitudPosventa`, `BitacoraPosventa`, `EvidenciaPosventa` |
| HU168 | Historial y Métricas | `Administrador_empresa` | `consultarMetricasHistorial(...)` | `SolicitudPosventa`, `UnidadGarantia` |

---

## 4. Validación Prevista

1. Estructura XML sin celdas huérfanas y con conectores enlazados a nodos reales.
2. Concordancia exacta de signaturas entre PlantUML y Draw.io.
3. Respeto de la regla de no-colisión de etiquetas y figuras editables.
