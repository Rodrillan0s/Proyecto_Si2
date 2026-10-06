# Diagramas de secuencia: CU25, CU26 y CU27

Fecha: 2026-10-04 (America/La_Paz). Diagramas Mermaid basados en el código actual de OBRATEC. Representan el flujo web implementado y sus servicios backend compartidos; no se realizaron cambios de código ni operaciones sobre la base.

Los bloques `alt` representan alternativas y los bloques `opt` operaciones opcionales. Las consultas y escrituras a PostgreSQL se muestran por responsabilidad, agrupando llamadas repetidas para mantener legibilidad. Cada solicitud HTTP incluye su JWT, aunque se omita repetirlo en las extensiones del flujo.

Referencias de arquitectura: [general y patrones](ARQUITECTURA_Y_PATRONES.md), [Reportes e IA](ARQUITECTURA_REPORTES_IA.md) y [operación de Reportes](OPERACION_REPORTES.md).

## Imágenes exportadas

| Caso de uso | PNG | SVG ampliable |
| --- | --- | --- |
| CU25 – Gestionar Clientes y CRM | [Abrir imagen](diagramas/secuencia/CU25.png) | [Abrir vector](diagramas/secuencia/CU25.svg) |
| CU26 – Consultar Asistente Inteligente (I1) | [Abrir imagen](diagramas/secuencia/CU26.png) | [Abrir vector](diagramas/secuencia/CU26.svg) |
| CU27 – Generar Reportes | [Abrir imagen](diagramas/secuencia/CU27.png) | [Abrir vector](diagramas/secuencia/CU27.svg) |

Se exportaron las secuencias completas con el parser/renderizador real de Mermaid. [Índice de imágenes](diagramas/secuencia/README.md). [Decisión y validación de las imágenes](decisiones/2026-10-04-imagenes-secuencias-cu25-cu27.md).

## 1. CU25 – Gestionar Clientes y CRM

**Actor:** usuario con permisos comerciales, por ejemplo administrador de empresa o administrador global. **Precondición:** sesión válida y acceso a la empresa/recurso de la operación. **Resultado:** clientes, prospectos, interacciones o asociaciones consultados/actualizados, con auditoría de las acciones de gestión.

```mermaid
sequenceDiagram
    autonumber
    actor U as Usuario comercial
    participant W as Interfaz CRM
    participant API as crm_routes
    participant S as crm_services
    participant R as crm_repos
    participant B as bitacora_repos
    participant DB as PostgreSQL

    U->>W: Seleccionar empresa y operación comercial
    W->>API: Solicitud HTTP con JWT, filtros o datos
    API->>API: verificar_token y exigir_permiso según operación
    alt Sesión o permiso rechazado
        API-->>W: Error de autenticación o autorización
        W-->>U: Mostrar restricción de acceso
    else Acceso inicial autorizado
        API->>S: Ejecutar caso de uso con token y empresa solicitada
        S->>S: Resolver empresa con _empresa y validar datos
        Note over S,DB: Existen validaciones SQL directas de empresa, asesor y unicidad en el servicio

        alt Consultar clientes, detalle o métricas
            S->>R: Consultar datos con empresa y filtros autorizados
            R->>DB: SELECT parametrizados del CRM
            DB-->>R: Clientes o métricas de la consulta
            R-->>S: Resultado comercial
            opt Consultar detalle de un cliente
                S->>R: Listar interacciones y unidades del cliente validado
                R->>DB: SELECT del historial y asociaciones
                DB-->>R: Interacciones y unidades
                R-->>S: Historial comercial
            end
        else Registrar cliente o prospecto
            S->>R: Buscar persona por CI si se proporcionó
            R->>DB: Consultar persona existente
            DB-->>R: Persona o ausencia
            R-->>S: Resultado de búsqueda
            S->>R: Crear persona o actualizar contacto de la existente
            R->>DB: INSERT o UPDATE de t_persona
            DB-->>R: Identificador de persona
            R-->>S: id_persona
            S->>DB: Verificar unicidad de empresa y persona
            DB-->>S: Resultado de validación
            S->>R: crear_cliente_crm con empresa y clasificación
            R->>DB: INSERT de t_crm_cliente
            DB-->>R: id_cliente
            R-->>S: Cliente o prospecto registrado
        else Actualizar, clasificar, registrar interacción o asociar unidad
            S->>R: Obtener cliente o asociación y validar pertenencia
            R->>DB: SELECT del recurso comercial
            DB-->>R: Recurso y relaciones
            R-->>S: Datos del recurso
            S->>S: Validar estado, datos y relaciones de la operación
            S->>R: Persistir la operación comercial seleccionada
            R->>DB: INSERT o UPDATE parametrizados
            DB-->>R: Resultado de la operación
            R-->>S: Datos actualizados
            opt Cambio de clasificación con seguimiento
                S->>R: Registrar interacción de evolución comercial
                R->>DB: INSERT del seguimiento en el historial
                DB-->>R: Seguimiento registrado
                R-->>S: Confirmación
            end
        end

        opt Operación de gestión con auditoría
            S->>B: _log con actor, acción, módulo e IP
            B->>DB: Registrar bitácora en llamada separada
            DB-->>B: Resultado de auditoría
            B-->>S: Retorno de la llamada
        end
        S-->>API: Resultado del caso de uso o CrmError
        API-->>W: JSON o estado HTTP de error
        W-->>U: Mostrar resultado, historial o validación
    end
```

**Contratos y límites del flujo:**

| Operación | Ruta principal | Permiso |
| --- | --- | --- |
| Listar y consultar detalle | `GET /api/crm/clientes`, `GET /api/crm/clientes/{id_cliente}` | `Visualizar_clientes` |
| Consultar métricas | `GET /api/crm/clientes/metricas` | `Visualizar_clientes` |
| Registrar | `POST /api/crm/clientes` | `Registrar_clientes` |
| Actualizar y clasificar | `PUT /api/crm/clientes/{id_cliente}`, `PATCH /api/crm/clientes/{id_cliente}/clasificacion` | `Modificar_clientes` |
| Registrar interacción | `POST /api/crm/clientes/{id_cliente}/interacciones` | `Modificar_clientes` |
| Asociar unidad y cambiar su estado | `POST /api/crm/clientes/{id_cliente}/unidades`, `PATCH /api/crm/asociaciones/{id_cliente_unidad}/estado` | `Modificar_clientes` |

Los usuarios de empresa quedan ligados a la empresa del JWT. El CRM actual permite al administrador global consultas sin filtro empresarial cuando no indica empresa; en escrituras conserva un fallback a su empresa o a 1. El diagrama muestra la variante con empresa seleccionada. Esa excepción existente difiere del asistente y Reportes, que requieren empresa explícita para el administrador global.

El registro de persona puede preceder a la validación de duplicidad comercial. Las operaciones de CRM y bitácora no forman una transacción única: `_log` tolera fallos de auditoría. Un `CrmError` interrumpe el flujo restante y se traduce en su estado HTTP; el diagrama no presupone rollback de todas las operaciones anteriores. No se dibuja eliminación de clientes porque estas rutas no la implementan.

Fuentes: [rutas](../backend/app/routes/crm_routes.py), [servicios](../backend/app/services/crm_services.py), [repositorio CRM](../backend/app/repos/crm_repos.py) y [bitácora](../backend/app/repos/bitacora_repos.py).

## 2. CU26 – Consultar Asistente Inteligente (I1)

**Actor:** usuario autenticado con acceso a consultas de Reportes o CRM. **Precondición:** contexto empresarial válido y capacidades autorizadas. **Resultado:** respuesta en lenguaje natural, reporte reutilizable cuando corresponde, o solicitud concreta de aclaración. La burbuja es única; el tema permite filtrar el historial visible.

```mermaid
sequenceDiagram
    autonumber
    actor U as Usuario autorizado
    participant W as Burbuja del asistente
    participant API as ai_routes
    participant A as assistant_service
    participant S as Servicios de consulta
    participant R as reportes_repos y crm_repos
    participant DB as PostgreSQL
    participant IA as Proveedor IA configurado

    U->>W: Escribir consulta o dictar por voz
    opt Consulta por voz
        W->>W: Reconocer voz del navegador y obtener texto
        Note over W,API: Alternativa de grabación, POST /api/voz/transcribir si está disponible
    end
    W->>API: POST /api/ai/consulta con texto, conversación y empresa
    API->>API: Validar JWT y AssistantRequest
    API->>A: reportes_services.assistant delega a consult
    A->>R: Cargar actor actual, empresa, permisos y obras
    R->>DB: Consultas parametrizadas de autorización
    DB-->>R: Contexto y recursos del actor
    R-->>A: Capacidades permitidas

    alt Actor o empresa sin acceso
        A-->>API: Error 403 o empresa requerida/inexistente
        API-->>W: Error HTTP de acceso
        W-->>U: Mostrar restricción o pedir empresa
    else Contexto válido
        opt Continuación de conversación
            A->>R: Cargar conversación de este usuario y empresa
            R->>DB: Consultar conversación e inputs recientes
            DB-->>R: Contexto conversacional vigente
            R-->>A: Solicitud anterior y tema
            A->>A: Reautorizar solicitud previa
        end
        A->>A: Normalizar texto e interpretar contra catálogo autorizado
        opt La interpretación local no encuentra capacidad suficiente
            A->>IA: Proponer plan JSON de lectura con catálogo permitido
            IA-->>A: Plan reportes, CRM o ayuda
            A->>A: Validar ReadPlan y capacidades propuestas
            Note over A,IA: La IA no genera SQL ni concede permisos
        end

        alt Solicitud de uno o varios reportes
            loop Por cada solicitud autorizada del plan
                A->>S: reportes_services.create con ReportRequest
                S->>R: Consultar datasets y revalidar acceso
                R->>DB: Leer datos de empresa y obras autorizadas
                DB-->>R: Datos del reporte
                R-->>S: Filas y ámbito
                S->>S: Calcular resúmenes y recomendaciones deterministas
                S->>R: Persistir ejecución LISTO tras reautorización
                R->>DB: INSERT de resultado, política y alcance
                DB-->>R: Identificador de ejecución
                R-->>S: Ejecución persistida
                S-->>A: ReportResult y ejecución
            end
            opt Redacción mediante IA de reportes disponibles
                A->>IA: Pregunta y resultados autorizados del backend
                IA-->>A: Explicación sin recalcular ni inventar datos
            end
            Note over A,S: Saldo comercial usa respuesta determinista y distingue ventas pactadas de ganancias reales
        else Solicitud comercial CRM
            A->>S: Revalidar Visualizar_clientes y construir ContextBuilder
            S->>R: Consultar métricas CRM existentes
            R->>DB: SELECT del contexto comercial de la empresa
            DB-->>R: Métricas
            R-->>S: Métricas comerciales
            S->>DB: Leer contexto CRM adicional filtrado por empresa
            DB-->>S: Prospectos, interacciones y asociaciones acotados
            S-->>A: Contexto comercial autorizado
            A->>R: Revalidar permiso antes de compartir contexto
            R->>DB: Consultar autorización actual
            DB-->>R: Acceso vigente
            R-->>A: Autorización
            A->>IA: Pregunta y contexto CRM autorizado
            IA-->>A: Respuesta comercial
        else Faltan detalles para resolver la consulta
            A->>A: Preparar aclaración con opciones y obras permitidas
        end

        A->>R: Revalidar acceso y guardar input/metadata de conversación
        R->>DB: Crear o actualizar conversación y registrar mensaje
        DB-->>R: Conversación persistida
        R-->>A: Confirmación
        A-->>API: Respuesta, tema, conversación y ejecuciones si existen
        API-->>W: JSON de la consulta
        W-->>U: Mostrar respuesta o aclaración
        opt Hay un reporte para consultar o exportar
            U->>W: Abrir resultado en Reportes
            W->>W: Transferir la ejecución al apartado Reportes
        end
    end
```

El proveedor se selecciona mediante `get_provider()` y adaptadores DeepSeek/Gemini; el diagrama no fija el modelo ni expone configuración secreta. Si falla el proveedor, el coordinador conserva la interpretación local o devuelve el resumen determinista disponible. Una aclaración puede pedir obra, fechas o precisión; no ejecuta escrituras comerciales.

En la rama Reportes se reutiliza CU27: no son queries creadas por el modelo. En la rama CRM, `ContextBuilder` combina el repositorio existente con SQL parametrizado propio ya implementado. Durante solicitudes al proveedor no se mantiene abierta la transacción del coordinador único. El historial persiste texto solicitado y metadata/referencias; no guarda las filas ni la respuesta completa del modelo en los mensajes.

Una conversación ajena o vencida termina con error; una capacidad no permitida se rechaza aunque la proponga la IA. `ADMINISTRADOR` requiere empresa explícita; los demás actores quedan en su empresa actual y obras permitidas. La etiqueta **I1** se conserva como parte del nombre del caso de uso solicitado.

La ruta antigua `/api/ai/crm/consulta` sigue disponible, pero la burbuja actual utiliza `/api/ai/consulta`; el diagrama representa esta entrada unificada.

Fuentes: [burbuja web](../frontend/src/app/components/asistente/asistente.ts), [contrato HTTP web](../frontend/src/app/services/reportes.service.ts), [rutas IA](../backend/app/routes/ai_routes.py), [coordinador único](../backend/app/services/ai/assistant_service.py), [contexto CRM](../backend/app/services/ai/context_builder.py), [autorización](../backend/app/services/reportes/authorization.py) y [adaptadores](../backend/app/services/ai/providers.py).

## 3. CU27 – Generar Reportes

**Actor:** usuario con permiso de consulta del reporte y su dominio. **Precondición:** sesión válida, empresa autorizada, filtros compatibles y obras dentro del alcance. **Resultado principal:** ejecución `LISTO` con resultado determinista, corte, ámbito y advertencias. **Extensiones:** exportar PDF/Excel, enviar o programar con sus permisos adicionales. Las rutas abreviadas de las extensiones usan el prefijo `/api/reportes`.

```mermaid
sequenceDiagram
    autonumber
    actor U as Usuario autorizado
    participant W as Interfaz Reportes
    participant API as reportes_routes
    participant S as reportes_services
    participant R as reportes_repos
    participant DB as PostgreSQL
    participant X as Exportadores PDF y Excel
    participant K as Worker de Reportes
    participant E as Brevo mediante email_service

    U->>W: Abrir Reportes y seleccionar empresa
    W->>API: GET /api/reportes/catalogo con JWT y empresa
    API->>S: catalog
    S->>R: Recargar actor, permisos, empresa y obras
    R->>DB: Consultar autorización y ámbito actual
    DB-->>R: Contexto y obras
    R-->>S: Recursos permitidos
    S-->>API: Catálogo, filtros y acciones disponibles
    API-->>W: Catálogo autorizado
    W-->>U: Mostrar tipos de reporte y filtros compatibles

    U->>W: Elegir reporte, obra, fechas y presentación
    opt Solicitud por texto desde la preparación del reporte
        W->>API: POST /api/reportes/interpretar
        API->>S: interpretation con catálogo autorizado
        S-->>API: ReportRequest propuesto o aclaración
        API-->>W: Filtros para revisar antes de generar
        U->>W: Revisar y confirmar solicitud
    end
    W->>API: POST /api/reportes/ejecuciones con ReportRequest y JWT
    API->>API: Validar JWT y contrato Pydantic
    API->>S: create
    S->>S: Abrir snapshot y ejecutar context y authorize
    S->>R: Cargar actor actual y obras autorizadas
    R->>DB: Leer actor actual y obras autorizadas
    DB-->>R: Contexto de acceso
    R-->>S: Definición y ámbito de la consulta

    alt Permiso, alcance o filtros rechazados
        S-->>API: Error de autorización o validación
        API-->>W: 403 o 422 según condición
        W-->>U: Mostrar restricción o filtro por corregir
    else Solicitud autorizada
        S->>R: datasets según catálogo y solicitud
        R->>DB: Query o función SQL existente con parámetros
        DB-->>R: Filas de empresa y obras autorizadas
        R-->>S: Datos del snapshot
        S->>S: Calcular resúmenes, ordenar y construir ReportResult
        Note over S,DB: Los cálculos y recomendaciones del reporte no requieren IA
        S->>R: Nueva transacción para revalidar y persistir ejecución
        R->>DB: Releer autorización e INSERT de resultado LISTO
        DB-->>R: Ejecución guardada
        R-->>S: Confirmación
        S-->>API: id, estado LISTO y resultado
        API-->>W: JSON del reporte generado
        W-->>U: Mostrar resumen, filas y advertencias

        opt Exportar a PDF o Excel
            U->>W: Elegir formato
            W->>API: POST /ejecuciones/id/exportaciones con formato pdf o xlsx
            API->>S: export_execution
            S->>S: owned con Exportar_reportes y resultado vigente
            S->>R: Obtener ejecución, actor y ámbito para revalidar
            R->>DB: Validar actor propietario, política y ámbito
            DB-->>R: Resultado autorizado
            R-->>S: Snapshot del reporte
            S->>X: export del resultado persistido
            X-->>S: Bytes PDF o XLSX
            S->>R: Revalidar y guardar archivo con SHA256
            R->>DB: Persistir archivo BYTEA y metadata
            DB-->>R: Identificador de archivo
            R-->>S: Referencia de exportación
            S-->>API: Archivo generado
            API-->>W: id del archivo
            W->>API: GET /api/reportes/archivos/id con JWT
            API->>S: download y revalidar acceso
            S->>R: Leer archivo tras validación de propiedad y permisos
            R->>DB: SELECT del archivo autorizado
            DB-->>R: Bytes y metadata
            R-->>S: Archivo
            S-->>API: Contenido, nombre y formato
            API-->>W: Binario con Content-Disposition
            W-->>U: Descargar PDF o Excel
        end

        opt Enviar manualmente a actores autorizados
            U->>W: Seleccionar destinatarios y formatos
            W->>API: POST /ejecuciones/id/envios con Idempotency-Key
            API->>S: send con Enviar_reportes
            S->>R: Validar destinatarios y encolar envíos deduplicados
            R->>DB: INSERT de entregas PENDIENTE
            DB-->>R: Trabajos registrados
            R-->>S: Confirmación de cola
            S-->>API: estado PENDIENTE
            API-->>W: Envío encolado
            K->>R: Reclamar entrega y recargar emisor/destinatario
            R->>DB: Consultar trabajo y autorizaciones actuales
            DB-->>R: Trabajo y contexto vigente
            R-->>K: Entrega reclamada
            K->>S: Reutilizar build para datos del ámbito compartido
            S->>R: Datasets filtrados por emisor y destinatario
            R->>DB: Consultar datos actuales autorizados
            DB-->>R: Filas para el envío
            R-->>S: Datos filtrados
            S-->>K: Resultado específico del destinatario
            K->>X: Exportar adjuntos PDF o XLSX
            X-->>K: Archivos del destinatario
            K->>R: Revalidar permisos inmediatamente antes del correo
            R-->>K: Autorización vigente
            K->>E: enviar_reporte a un destinatario con adjuntos
            E-->>K: messageId o error del proveedor
            K->>R: Registrar ACEPTADO, reintento, FALLIDO o INCIERTO
            R->>DB: Actualizar entrega
            DB-->>R: Estado persistido
            R-->>K: Confirmación
        end
    end
```

La generación manual es síncrona: retorna `LISTO` cuando terminó lectura, cálculo y persistencia. Se separan el snapshot de lectura y la transacción de persistencia, con reautorización entre ambos. El permiso base actual es `Visualizar_reportes` junto al permiso del dominio; no se inventa un permiso `Generar_reportes` que el flujo no usa. Rango de fechas solo cuando la definición del catálogo lo admite.

La exportación reutiliza el resultado persistido. El envío vuelve a consultar datos y prepara un resultado para cada destinatario según la intersección de permisos, obras y filas; por eso su corte puede diferir del reporte visto inicialmente. `ACEPTADO` significa que Brevo aceptó el envío, no que el actor haya recibido o leído el correo. Una respuesta incierta no se trata como éxito ni se reenvía indiscriminadamente.

**Extensión programada:** `POST /api/reportes/programaciones` guarda solicitud, destinatarios, formatos, frecuencia, zona y próximo vencimiento, tras validar `Programar_reportes`, `Enviar_reportes` y los permisos de las fuentes. El worker consulta programaciones vencidas, crea una ejecución `PENDIENTE`, genera mediante `build` y continúa con la misma rama de entrega del diagrama. Guardar una programación no arranca el worker. El proceso requiere configuración operativa y participa en la barrera de Backup/Restore; no genera ni envía durante mantenimiento.

**Otras salidas:** resultado demasiado grande o exportación superior a 5 MiB requiere acotar filtros; permisos revocados invalidan consulta, descarga o envío; tablas propias de Reportes ausentes producen `503 REPORTES_SCHEMA_MISSING`. Estas condiciones interrumpen la extensión correspondiente y no conceden acceso a otro tenant.

Fuentes: [pantalla web](../frontend/src/app/pages/reportes/reportes.ts), [rutas](../backend/app/routes/reportes_routes.py), [servicios](../backend/app/services/reportes_services.py), [repositorio](../backend/app/repos/reportes_repos.py), [catálogo](../backend/app/services/reportes/catalog.py), [autorización](../backend/app/services/reportes/authorization.py), [exportadores](../backend/app/services/reportes/exporters.py), [worker](../backend/app/services/reportes/worker.py), [calendario](../backend/app/services/reportes/scheduling.py) y [correo](../backend/app/services/email_service.py).

## Alcance del análisis y validación

Se revisaron instrucciones del proyecto, referencias arquitectónicas y código actual de rutas, servicios, repositorios, contexto, proveedores, exportación, worker y clientes web. Los diagramas describen capas existentes, adaptadores de IA/exportación, contexto autorizado por tenant, persistencia de conversaciones y cola de entregas. No sustituyen contratos de aceptación ni demuestran activación operativa de proveedor, voz o correos.

Se comprobaron enlaces locales y estructura de los tres bloques Mermaid. No se consultó la base real, aplicó migración, inició backend/worker ni se enviaron correos para esta entrega documental.
