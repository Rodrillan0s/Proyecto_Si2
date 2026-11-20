# Reportes web y asistente flotante

Fecha: 2026-10-04. Alcance autorizado: frontend web y documentación. Se consultaron AGENTS.md, arquitectura general, arquitectura de Reportes/IA, operación y código afectado antes de modificarlo.

## Diagnóstico y decisión previa

Angular standalone mantiene servicios HTTP y componentes de presentación dentro del shell autenticado. Reportes ya consume el catálogo autorizado y las ejecuciones del backend. Su pantalla mezcla preparación, resultados, correo e historial; faltan validaciones locales, estados vacíos y protección de respuestas tardías en programación. CRM tiene un chat independiente que no transmite la empresa seleccionada en sus consultas.

Se introduce un único componente de asistente flotante en AdminLayout y un servicio de coordinación de apertura, sin dependencia de un proveedor específico. El asistente conserva la conversación durante la navegación del shell, la elimina al cambiar empresa y consume los endpoints existentes de Reportes y CRM. No escribe SQL, no envía correos ni crea programaciones desde el chat. Las ejecuciones generadas se abren en Reportes mediante un parámetro de ruta y se vuelven a consultar al backend, que autoriza su acceso.

Reportes mantiene formularios deterministas independientes de IA. Se presentan tres vistas: preparación, historial y programaciones. Los permisos de acción proceden del catálogo; las guardas visuales no sustituyen la autorización del servidor. Se validan fechas, obra obligatoria y horarios antes de enviar solicitudes. Toda respuesta asíncrona se vincula a la generación del contexto de empresa. Las claves de envío se conservan en reintentos de la misma combinación de ejecución, destinatarios y formato.

La voz se concentra en el asistente: reconocimiento del navegador o transcripción de audio mediante el endpoint existente. Cerrar/cambiar contexto cancela la captura; la denegación del micrófono mantiene disponible el texto. No se almacenan conversaciones ni datos de reportes en localStorage.

## Límites de activación

La inspección visual detectó que el shell existente no tenía navegación lateral adaptable y desbordaba el ancho en teléfonos. Se amplía el ajuste web al contenedor: ancho mínimo de contenido, menú móvil desplegable y cabecera compacta. Se conserva el comportamiento de colapsar el menú en escritorio. La validación del tema utiliza el control real del panel, que sincroniza la clase del shell y la raíz.

Esta intervención no aplica migraciones, modifica backend/móvil, activa workers ni envía correos reales. La disponibilidad operativa de consultas, IA, STT y automatización depende del despliegue documentado en OPERACION_REPORTES.md. La interfaz debe informar fallos y estados pendientes, sin presentar un correo encolado como entregado.

## Validación

18 pruebas focalizadas pasan: contratos HTTP/empresa, exportación, interacción del asistente, borrador del panel, recuperación ante error, aislamiento de consultas/programaciones, cambio de tema, validación de fechas/obra/horarios y claves de envío. Se prueba también la liberación del micrófono cuando el permiso llega después de cerrar el asistente. No se ejecutan specs históricos ajenos al módulo.

Build de desarrollo y producción pasan. La producción requiere descargar las fuentes externas que ya usa el proyecto; se concedió acceso para esa compilación. Se conservan advertencias de estilos y Leaflet existentes; no se elevaron los presupuestos Angular. Los estilos nuevos se organizan en archivos menores de 4 kB.

La comprobación local en Edge usa datos sintéticos, intercepta HTTP y sustituye WebSocket: generación, envío simulado, programación, consulta de chat, capturas en escritorio/móvil y tema oscuro, sin errores JavaScript. La inspección visual detectó y corrigió desbordamiento móvil, cabecera superpuesta al chat y transiciones de tema que debían terminar antes de capturar. Capturas locales en `frontend/.angular/reportes-preview`, script reproducible en `frontend/scripts/reportes-browser-check.cjs`.

No se ejecutaron consultas contra PostgreSQL, migraciones, workers, correos reales, STT real ni API externa de IA en esta intervención. La prueba con fixtures valida el frontend; la activación externa sigue el documento de operación.
