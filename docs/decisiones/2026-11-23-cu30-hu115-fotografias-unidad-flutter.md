# Decisión Arquitectónica: HU115 – Ver fotografías actualizadas de su unidad (Frontend Flutter)

**Fecha:** 2026-11-23  
**Estado:** Aprobada / En implementación  
**Contexto:** CU30 – Consultar proyectos y unidades como cliente (Etapa 3 - HU115)  

---

## 1. Contexto y Objetivos

Habiendo implementado la navegación base de `CLIENTE` (Etapa 1) y la consulta del avance físico (HU114), se requiere incorporar la visualización de fotografías autorizadas y actualizadas asociadas a la unidad inmobiliaria seleccionada por el cliente.

Flujo del usuario:
```text
CLIENTE (autenticado)
  └── HomeScreen ("Mis Proyectos y Unidades")
        └── ClienteUnidadesScreen (selección de unidad)
              └── ClienteUnidadDetalleScreen
                    ├── Resumen de Unidad
                    ├── Avance Físico (HU114)
                    └── Fotografías de la Unidad (HU115)
                          ├── Galería / Malla de miniaturas autenticadas
                          ├── Indicador de fotografía principal y metadatos (fecha, nombre)
                          └── Visualizador en modal/diálogo a mayor tamaño
```

---

## 2. Contratos y Endpoints del Backend

Se verificó en `backend/app/routes/crm_routes.py` y `crm_services.py` la existencia y comportamiento de los endpoints:

1. **Listado de fotografías autorizadas:**
   - **Método y Ruta:** `GET /api/crm/cliente/unidades/{id_unidad}/fotografias`
   - **Autenticación:** Bearer Token JWT (Rol `CLIENTE`).
   - **Validación backend:** El backend valida que la unidad pertenezca al tenant del JWT y que esté asignada al cliente en `t_crm_cliente_unidad`.
   - **Respuesta (JSON):**
     ```json
     {
       "success": true,
       "data": [
         {
           "id_fotografia": 51,
           "id_unidad": 9,
           "nombre_archivo": "fachada_noviembre.jpg",
           "tipo_mime": "image/jpeg",
           "tamano_bytes": 1048576,
           "es_principal": true,
           "orden": 1,
           "created_at": "2026-11-21T18:00:00Z",
           "url_archivo": "/api/crm/cliente/unidades/9/fotografias/51/archivo"
         }
       ]
     }
     ```

2. **Descarga autenticada del binario de imagen:**
   - **Método y Ruta:** `GET /api/crm/cliente/unidades/{id_unidad}/fotografias/{id_fotografia}/archivo`
   - **Autenticación:** Bearer Token JWT (Rol `CLIENTE`).
   - **Respuesta:** Binario directo `Response(content=..., media_type=mime)`.
   - **Restricción de seguridad:** Las imágenes son privadas del tenant y de la unidad. `Image.network` nativo de Flutter no envía cabecera `Authorization: Bearer`, por lo que las imágenes deben obtenerse a través del cliente HTTP configurado (`ApiClient.dio`) con `ResponseType.bytes` y renderizarse en memoria (`Image.memory`).

---

## 3. Capas y Responsabilidades

1. **Capa de Servicios (`UnidadService` / `mobile/lib/services/unidad_service.dart`):**
   - Método `listarFotografiasUnidadCliente(int idUnidad)`: Invoca `GET /api/crm/cliente/unidades/{id_unidad}/fotografias` mediante `ApiClient.dio`.
   - Método `descargarArchivoFotografia(String urlArchivo)`: Invoca `GET {urlArchivo}` con `Options(responseType: ResponseType.bytes)` retornando `Uint8List`.
2. **Capa de Presentación (`ClienteUnidadDetalleScreen` y widgets auxiliares):**
   - Sección "Fotografías de la unidad":
     - Estado de carga (`CircularProgressIndicator`).
     - Estado de error con reintento (`IconButton` o `ElevatedButton`).
     - Estado vacío informativo si `data.isEmpty`.
     - Cuadrícula/galería con tarjetas mostrando:
       - Miniatura autenticada cargada en memoria.
       - Badge "Principal" si `es_principal == true`.
       - Nombre de archivo y fecha formateada (`created_at`).
     - Al tocar una miniatura: Diálogo o pantalla modal (`Dialog` / `showDialog`) con imagen ampliada, nombre, fecha y botón de cierre.

---

## 4. Contexto de Tenant y Seguridad

- No se agregan roles ni permisos nuevos.
- El cliente solo puede consultar fotos de unidades que le pertenezcan según la validación del backend en `t_crm_cliente_unidad`.
- No se exponen rutas públicas en la nube ni URLs temporales sin expiración.
- Los bytes descargados se retienen en memoria durante el ciclo de vida de la pantalla sin persistencia insegura en almacenamiento externo.

---

## 5. Delimitación de Alcance

- **Incluido en esta etapa (HU115):**
  - Consulta de metadatos de fotografías de la unidad.
  - Carga y visualización de imágenes autenticadas.
  - Indicador de foto principal y metadatos disponibles.
  - Vista previa a mayor tamaño.
  - Manejo de estados de carga, vacío y error.
- **Excluido deliberadamente (NO implementar en esta etapa):**
  - HU116: Comunicaciones directas de la constructora.
  - HU117: Solicitudes y PQRS del cliente.
  - Subida de fotografías desde la app móvil.
  - Chat o mensajería bidireccional.
  - Modificaciones en backend o base de datos.

---

## 6. Plan de Validación

1. Análisis estático con `flutter analyze` verificando 0 issues.
2. Pruebas de widgets y unitarias en `mobile/test/cliente_unidades_test.dart` cubriendo:
   - Carga exitosa de fotografías con badge principal y formato de fecha.
   - Estado vacío cuando la unidad no tiene fotografías.
   - Manejo de error de red con opción de reintento.
   - Interacción de apertura de imagen ampliada.
   - Mantenimiento de pruebas previas de Etapa 1 y HU114.
