# Decisión Arquitectónica: HU116 – Recibir comunicaciones directas de la constructora (Frontend Flutter)

**Fecha:** 2026-11-23  
**Estado:** Aprobada / En implementación  
**Contexto:** CU30 – Consultar proyectos y unidades como cliente (Etapa 4 - HU116)  

---

## 1. Contexto y Objetivos

Con la navegación base de `CLIENTE` (Etapa 1), la consulta de avance físico (HU114) y la galería de fotografías (HU115) consolidadas, se requiere implementar la **HU116: Recibir comunicaciones directas de la constructora**.

Flujo del usuario:
```text
CLIENTE (autenticado)
  └── HomeScreen ("Mis Proyectos y Unidades")
        └── ClienteUnidadesScreen (Portal Cliente)
              ├── Acceso directo a "Comunicaciones de la Constructora" (con badge HU116)
              └── ClienteComunicacionesScreen
                    ├── Cabecera informativa y contador de comunicados
                    ├── Listado cronológico de comunicaciones oficiales
                    │     ├── Asunto / Título
                    │     ├── Badge de estado leído / no leído
                    │     ├── Tipo de comunicado / referencia
                    │     ├── Fecha de emisión
                    │     └── Contenido textual íntegro
                    └── Estados de carga, vacío y error con reintento
```

---

## 2. Contratos y Endpoints del Backend

Se verificó en `backend/app/routes/crm_routes.py`, `backend/app/services/crm_services.py` y `backend/app/repos/notificaciones_repos.py`:

- **Método y Ruta:** `GET /api/crm/cliente/comunicaciones`
- **Autenticación:** Bearer Token JWT (Rol `CLIENTE`).
- **Validación backend:**
  1. Extrae `id_cliente`, `nro_usuario` e `id_empresa` del token del cliente.
  2. Filtra en `notificacion` por `nro_usuario` y tenant `id_empresa`.
  3. Si la notificación referencia a una obra, valida que el cliente tenga al menos una unidad asociada en dicha obra vía `t_crm_cliente_unidad`.
- **Estructura real de la respuesta (JSON):**
  ```json
  {
    "success": true,
    "no_leidas": 1,
    "data": [
      {
        "id_notificacion": 101,
        "titulo": "Aviso de avance en Edificio Los Sauces",
        "cuerpo": "Estimado cliente, le informamos que se completó el vaciado...",
        "mensaje": "Estimado cliente, le informamos que se completó el vaciado...",
        "tipo_referencia": "COMUNICACION_CLIENTE",
        "tipo": "COMUNICACION_CLIENTE",
        "leido": false,
        "fecha_creacion": "2026-11-23T10:30:00",
        "created_at": "2026-11-23T10:30:00",
        "nro_emergencia": null
      }
    ]
  }
  ```

---

## 3. Capas y Responsabilidades

1. **Capa de Servicios (`CrmService` / `mobile/lib/services/crm_service.dart`):**
   - Método `listarComunicacionesCliente()`: Invoca `GET /api/crm/cliente/comunicaciones` mediante `ApiClient.dio` utilizando el Bearer Token existente.
2. **Capa de Presentación:**
   - **`ClienteUnidadesScreen` (`mobile/lib/screens/cliente_unidades_screen.dart`):**
     - Añade tarjeta de acceso directo a **"Comunicaciones de la Constructora"** con badge semántico `HU116` y acción de navegación en AppBar.
     - Preserva íntegramente la lista de inmuebles y la navegación a `ClienteUnidadDetalleScreen`.
   - **`ClienteComunicacionesScreen` (`mobile/lib/screens/cliente_comunicaciones_screen.dart`):**
     - Pantalla dedicada para visualización y lectura de comunicados.
     - Soporta `RefreshIndicator` (pull-to-refresh).
     - Estados contemplados:
       - Carga (`CircularProgressIndicator`).
       - Vacío (`Icon(Icons.mark_email_read_outlined)` con texto claro de ausencia de avisos).
       - Error con botón de reintento.
       - Tarjetas individuales con título, badge de estado (`NO LEÍDO` / `LEÍDO`), tipo de comunicación, fecha formateada y contenido.
     - **Modo Solo Lectura:** No incluye inputs de texto, botones de respuesta, chat ni modificación alguna.

---

## 4. Seguridad y Aislamiento de Tenant

- Acceso exclusivo para el rol `CLIENTE`.
- La petición HTTP incluye automáticamente `Authorization: Bearer <token>` mediante el interceptor de `ApiClient`.
- No se exponen datos de otros clientes ni de otras empresas.
- No se agregan roles ni permisos adicionales en frontend ni backend.

---

## 5. Delimitación de Alcance

- **Incluido en esta etapa (HU116):**
  - Consulta y recepción de comunicaciones emitidas por la constructora hacia el cliente autenticado.
  - Renderizado de metadatos reales devueltos por el backend (`titulo`, `cuerpo`, `leido`, `fecha_creacion`, `tipo_referencia`).
  - Navegación integrada desde el Portal Cliente.
  - Compatibilidad total con temas Claro y Oscuro.
- **Excluido deliberadamente (NO implementar en esta etapa):**
  - HU117: Solicitudes y PQRS de cliente.
  - Chat o mensajería instantánea bidireccional.
  - Enviar respuestas o crear comunicaciones desde la app móvil.
  - Modificaciones en base de datos o lógica de backend.

---

## 6. Plan de Validación

1. Análisis estático con `flutter analyze` asegurando 0 issues.
2. Pruebas de widgets y unitarias en `mobile/test/cliente_unidades_test.dart` y `cliente_comunicaciones_test.dart`:
   - Visualización de la opción de comunicaciones en el Portal Cliente.
   - Navegación hacia `ClienteComunicacionesScreen`.
   - Renderizado de comunicación con título, cuerpo, fecha y badges.
   - Estado vacío y estado de error con reintento.
   - Verificación de no regresión en Etapa 1, HU114 y HU115.
3. Ejecución de la suite completa `flutter test`.
4. Comprobación `git diff --check`.
