# Documentación del Diagrama de Tiempo: CU33 (Gestión de Garantías y Posventa)

**Caso de Uso:** CU33 – Gestionar Garantías y Servicio Posventa Inmobiliario  
**Objeto Principal de Ciclo de Vida:** `SolicitudPosventa` (`t_posventa_solicitud`)  
**Fecha:** 2026-11-24  

---

## 1. Estados de la Solicitud y Transiciones

El ciclo de vida del ticket de posventa contempla una máquina de estados estricta orientada a garantizar trazabilidad y calidad de servicio:

```
[Cliente reporta]
       │
       ▼
  (PENDIENTE) ────────► [Rechazo] ────► (RECHAZADA)
       │
 [Admin clasifica]
       │
       ▼
 (CLASIFICADA) ───────► [Rechazo] ────► (RECHAZADA)
       │
[Jefe Obra asigna]
       │
       ▼
   (ASIGNADA)
       │
[Supervisor visita]
       │
       ▼
 (EN_ATENCION)
       │
[Supervisor repara]
       │
       ▼
   (RESUELTA)
       │
[Cierre administrativo]
       │
       ▼
   (CERRADA)
```

### Tabla de Estados y Eventos Desencadenantes

| Estado | Actor Responsable | Evento Desencadenante | Acciones Asociadas |
|---|---|---|---|
| **PENDIENTE** | `Cliente` | Creación de Solicitud (HU163) | Generación de ticket `POST-YYYYMMDD-XXXX`, carga de evidencia inicial, inserción en `t_posventa_bitacora`. |
| **CLASIFICADA** | `Administrador_empresa` | Clasificación Técnica (HU164) | Asignación de especialidad (plomería, electricidad, acabados), prioridad (baja a urgente) y validación de cobertura de garantía. |
| **ASIGNADA** | `Jefe de Obra` | Asignación de Responsable (HU165) | Designación del supervisor/técnico de obra, definición de fecha estimada de inspección e instrucciones técnicas. |
| **EN_ATENCION** | `Supervisor` | Inicio de Visita/Trabajo (HU166) | Registro de bitácora de inspección en campo, diagnóstico y planificación de intervenciones. |
| **RESUELTA** | `Supervisor` | Ejecución de Reparación (HU166) | Registro de acciones correctivas, consumo de materiales, adjunción de evidencias fotográficas de trabajo terminado y fecha efectiva de solución. |
| **CERRADA** | `Administrador_empresa` / `Cliente` | Conformidad y Cierre | Validación final de satisfacción y archivo de trazabilidad histórica (HU167/HU168). |
| **RECHAZADA** | `Administrador_empresa` / `Jefe de Obra` | No cobertura / Improcedente | Registro del motivo justificado de improcedencia legal o técnica en bitácora. |

---

## 2. Artefacto Gráfico Asociado

El diagrama nativo de tiempos se encuentra modelado y exportado en:
- `docs/diagramas/CU33-tiempo.drawio` (Líneas de tiempo de estados con eventos e hitos de interacción de los 4 actores).
