# Operación de Reportes y asistente

Si se activa Backup/Restore, el worker participa en su barrera compartida y requiere base de control disponible. Después de restaurar, programaciones/trabajos/envíos quedan pausados o en cuarentena para impedir correos duplicados. Revisar explícitamente antes de reactivar. Ver [operación de backups](OPERACION_BACKUPS.md).

Fecha: 2026-10-04. Referencia técnica: [arquitectura implementada](ARQUITECTURA_REPORTES_IA.md). La migración de Reportes ya se aplicó a la base configurada; el postflight confirma que no quedan tablas pendientes. No se inició el worker ni se enviaron correos reales durante la corrección. Los pasos siguientes describen también la instalación en otros entornos.

## Preparar el entorno

Personalización web: selecciona tipo/obra, período rápido o Desde/Hasta (ambos extremos incluidos, también admite rangos abiertos). El catálogo explica qué fecha filtra y qué reportes muestran estado actual. Abre **Personalizar presentación y exportación** para cambiar título, orientación PDF, columnas y orden; pulsa **Generar reporte** para aplicar. Abrir una ejecución restaura la configuración guardada. Las programaciones conservan esa presentación cuando calculan períodos relativos.

El asistente tiene una entrada única para proyectos, reportes y CRM. El selector **Historial** solo filtra mensajes de la sesión; no cambia capacidades. Ejemplos: «costos este mes», «incidencias críticas del mes pasado», «cuántos prospectos están en negociación» y «qué obras han generado ganancias». Esta última necesita permisos de Reportes, costos y clientes; devuelve saldo comercial estimado, no certifica cobros/ganancias realizadas. El proveedor puede proponer consultas del catálogo; no modifica obras, clientes ni permisos. Mantiene las acciones de envío/programación en sus controles explícitos.

Si `/api/reportes/catalogo` responde 404 y no aparece en `/openapi.json`, reiniciar el backend desde esta copia del proyecto (`cd backend; python run.py`). El registro está en `create_app()`; una instancia anterior puede conservar rutas antiguas incluso con recarga configurada. Sin token, la ruta cargada debe responder 401. Este problema de registro es independiente de la migración de tablas.

Si falta una tabla del módulo, la API responde 503 con `code=REPORTES_SCHEMA_MISSING` y la instrucción de aplicar la migración en ese entorno. No devuelve un historial vacío ocultando el problema. Esta condición se corrigió en la base configurada mediante aplicación transaccional de la migración; validar preflight antes de aplicar en otras bases.

En el entorno de backend seleccionado, instalar `backend/requirements.txt`. El archivo se normalizó de UTF-16 a UTF-8 conservando dependencias previas y agregando ReportLab, openpyxl y tzdata.

```powershell
cd backend
python -m pip install -r requirements.txt
python migrate_reportes.py
```

El segundo comando de Python es **revisión de solo lectura**: verifica columnas necesarias, muestra tablas de reportes pendientes y el SHA256 del script. Comprobar que la conexión corresponde a la base de pruebas/despliegue elegida antes de aplicar. No imprimir ni copiar credenciales del `.env`.

Aplicación explícita por el operador del entorno:

```powershell
python migrate_reportes.py --apply
```

La migración agrega siete tablas, un módulo y cinco permisos. Los grants se asignan por nombre y sin duplicar IDs existentes; no concede nuevos dominios financieros a clientes/trabajadores. Revisar en el administrador de roles la matriz resultante y las asignaciones de jefe de obra. La base anterior no permite reconstruir horas de personal ni consumo físico real; las etiquetas del catálogo lo explican.

La relación de cliente es cuenta → persona → `t_detalle_obra.id_cliente`. Confirmar la asignación de persona a cada cuenta antes de habilitar acceso. No asociar por coincidencias de correo/nombre. El cliente accede a las unidades de su obra vinculada; la base actual no acredita propiedad individual por unidad.

## Configuración de IA

No se modifica el `.env` del usuario. El backend ahora consume las variables existentes:

```dotenv
AI_PROVIDER=deepseek
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
AI_TIMEOUT_SECONDS=30
# DEEPSEEK_API_KEY: configurar mediante el gestor de secretos del entorno
```

Mantener el valor del modelo ya elegido por el usuario; el ejemplo no obliga a reemplazarlo. `AI_PROVIDER=gemini` usa `GEMINI_API_KEY`/`GEMINI_MODEL`. Sin selector, la presencia de la clave DeepSeek lo elige; en otro caso se selecciona Gemini. Solo hay adaptadores para estos dos protocolos. El catálogo, consulta local, PDF/XLSX y automatización no requieren claves IA. Si falla el proveedor, el asistente mantiene su resumen determinista.

## Worker y correo

```powershell
cd backend
python reportes_worker.py
# Para un ciclo controlado, si la cola del entorno puede procesarse:
python reportes_worker.py --once
```

**Estos comandos procesan programaciones y pueden enviar correos reales.** Usar primero una base de pruebas y remitente/destinatarios de prueba designados. Configurar `BREVO_API_KEY`, `BREVO_SENDER_EMAIL`, `BREVO_SENDER_NAME` y timeout según el servicio de correo ya existente.

Desplegar como proceso de background separado de Uvicorn. El proceso debe permanecer activo para programaciones; si el hosting no ofrece workers, ejecutar ciclos con un cron del entorno. No crear un scheduler en cada proceso HTTP. El worker limpia archivos/conversaciones/resultados caducados, además de generar/enviar.

La UI crea programaciones y selecciona IDs de cuentas autorizadas de la empresa. Las direcciones son las de las cuentas activas; no hay verificación de email representada en el esquema actual. Validarlas administrativamente antes de uso. El worker vuelve a comprobar cuenta, permiso de reporte/exportación, empresa, obras, filas, correo y pausa, y reconstruye el archivo para cada destinatario.

Estados visibles: PENDIENTE, ENVIANDO, ACEPTADO, FALLIDO, INCIERTO. ACEPTADO incluye messageId y significa aceptación por Brevo. No hay estado de entrega final sin webhook configurado/verificado. Un envío INCIERTO requiere revisar el proveedor antes de decidir un envío manual nuevo; no se reintenta automáticamente. El cliente conserva la misma `Idempotency-Key` en reintentos de la misma acción; iniciar una acción distinta tiene identidad distinta.

Frecuencias: diaria, semanal y mensual. Zona IANA por defecto America/La_Paz; próximas ejecuciones en UTC. Para mensualidad inexistente se utiliza último día del mes. Tras caídas se recupera una sola ocurrencia reciente de las últimas 24 horas. Revisar errores/omisiones en Programaciones y estados de envío desde la ejecución.

## Web y móvil

Web: menú **Reportes**, ruta `/reportes`, con vistas **Generar reporte**, **Historial** y **Programaciones**. El catálogo/acciones provienen del backend; los mapas de rol son navegación, no autorización. Seleccionar empresa si se usa ADMINISTRADOR global. El formulario genera reportes sin IA; «Preparar filtros escribiendo» permite revisar una solicitud antes de generarla. La pantalla pagina 50 filas; exportaciones contienen todo el resultado autorizado.

La burbuja **Asistente** aparece en la esquina inferior derecha de las páginas del panel, según permisos. «Reportes y proyectos» consulta métricas y genera ejecuciones con el backend existente; «Clientes y ventas» consulta CRM. También se abre desde el botón de Reportes o desde CRM. La entrada de consulta de la cabecera abre el chat con un borrador para revisar y enviar. Escribir, pulsar Enter o usar **Dictar**; revisar el texto reconocido antes de enviarlo. Shift+Enter agrega una línea. Cerrar o pulsar Escape conserva la conversación dentro del mismo contexto; cambiar empresa/tema la limpia. «Ver reporte completo» lleva a la ejecución para exportar o compartir. PDF y Excel también están disponibles en el chat cuando el catálogo permite exportación.

Para envío: generar/abrir una ejecución, seleccionar destinatarios y formato, pulsar **Enviar reporte** y revisar sus estados. Para automatización: preparar el tipo/obra/filtros, seleccionar destinatarios y abrir **Programar este reporte** para configurar frecuencia, hora y período. Los destinatarios provienen de cuentas autorizadas; máximo 30. Historial actualiza trabajos pendientes y envíos abiertos cada 15 segundos si la pestaña está visible; **Actualizar** consulta también las programaciones. Guardar una programación o registrar un envío no demuestra que el worker esté activo.

```powershell
cd frontend
npm run build
npm run test:reportes
```

La configuración específica evita compilar specs antiguos que importan clases eliminadas. No demuestra que toda la suite histórica funcione.

Validación visual opcional y sin backend real: iniciar `ng serve --host 127.0.0.1 --port 4201`, un Edge/Chromium de pruebas con `--headless=new --remote-debugging-port=9223` y perfil temporal independiente; ejecutar `node scripts/reportes-browser-check.cjs` dentro de frontend. El script inyecta una sesión ficticia, intercepta todos los endpoints locales del backend y sustituye WebSocket; no usa credenciales reales ni envía correos. Capturas en `.angular/reportes-preview/`, fuera del código versionado. No ejecutar el script con un perfil de navegador personal.

Móvil: acceso Reportes en la pantalla principal, consulta, tabla paginada, PDF/Excel mediante guardar/compartir del dispositivo, envío, programaciones e historial. Dependencias speech_to_text/share_plus y permisos Android/iOS incluidos. Se resolvieron marcadores de conflicto previos en home conservando imports de CRM e incidencias.

```powershell
cd mobile
flutter pub get
flutter analyze
```

En este equipo `flutter pub get` resolvió/descargó dependencias, pero informó que Windows requiere **modo desarrollador para enlaces simbólicos** de plugins. Activarlo mediante la configuración del sistema antes de compilar una app nativa en Windows. No se cambió esa configuración del sistema. El análisis focalizado Dart de los archivos afectados pasó; Android/iOS y compartir/voz requieren prueba en dispositivo.

## Voz y fallback STT

Web usa reconocimiento del navegador cuando está disponible; Flutter usa reconocimiento del dispositivo. El sistema operativo puede usar servicios externos para reconocer la voz. Si no hay reconocimiento, la grabación se envía al endpoint común de transcripción. El rechazo del micrófono deja disponible el texto.

STT del servidor está desactivado por defecto. Para un entorno con recursos de CPU y modelo local:

```powershell
cd backend
python -m pip install -r requirements-voice.txt
```

```dotenv
SPEECH_PROVIDER=whisper
WHISPER_MODEL=/ruta/al/modelo/local
```

Descargar/provisionar el modelo previamente siguiendo [faster-whisper](https://github.com/SYSTRAN/faster-whisper). El backend usa `local_files_only=True`; no descarga modelos al atender una solicitud. La transcripción es independiente de DeepSeek/Gemini; audio temporal eliminado tras la petición, límite de 5 MiB/60 segundos, texto hasta 2.000 caracteres. Dimensionar el proceso para CPU/STT y probar formatos del navegador/dispositivo antes de exigir cobertura universal. No se instalaron ni descargaron modelos durante esta implementación.

## Límites y retención

20.000 filas por reporte; archivo/adjuntos hasta 5 MiB, sin omisión silenciosa. PDF rechaza celdas muy extensas y ofrece Excel. No hay exportación masiva por lotes ni vínculos para archivos mayores en esta entrega. Todos los importes se calculan con Decimal; JSON conserva decimales como cadena, y XLSX usa números del formato Excel.

Archivos caducan en 7 días, resultados se vacían a los 30 y conversaciones se eliminan a los 30 días desde creación. Estos valores están fijados en la primera implementación. Los metadatos de ejecución/envío quedan para trazabilidad. Si el worker no está activo, no ocurre la limpieza física; las descargas/conversaciones verifican caducidad igualmente.

## Validación antes de activar

Backend sin conexiones externas:

```powershell
cd backend
python -m unittest tests.test_reportes tests.test_reportes_api tests.test_control_costos_services -v
```

Validación SQL adicional y explícita, solo metadatos/EXPLAIN:

```powershell
python tests/reportes_sql_readonly_check.py
```

Para aceptación integrada en una **base de pruebas designada**: aplicar migración, preparar actores/obras/cliente, comprobar consultas y archivos para dos tenants, revocar permisos entre generación y descarga/envío, ejecutar dos workers y reiniciar uno tras claim, comprobar una ocurrencia por horario y resultado incierto sin duplicado. Confirmar voz y compartir en Android/iOS/navegador. Estos ensayos de escritura, concurrencia real y correo no se ejecutaron sobre la base configurada por desconocer su clasificación de entorno.

## Reversión

Pausar programaciones y detener el worker antes de revertir código. Conservar tablas/historial si hubo uso. `20261004_reportes_rollback.sql` permite reversión estructural solo si no hay ejecuciones, programaciones ni conversaciones; rechaza la operación si existen datos y no elimina permisos globales por nombre. Archivar datos y preparar una migración de reversión específica si el entorno ya produjo reportes. No se ejecutó la reversión.
