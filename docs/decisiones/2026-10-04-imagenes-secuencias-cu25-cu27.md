# Imágenes de secuencia de CU25, CU26 y CU27

Fecha: 2026-10-04 (America/La_Paz). El usuario solicita imágenes de los tres diagramas ya documentados.

Se revisaron las instrucciones del proyecto, arquitectura general, Reportes/IA y el Markdown de secuencias. Se exportarán sus tres bloques Mermaid a PNG y SVG, conservando participantes, mensajes, alternativas, permisos y contexto empresarial. La fuente sigue siendo el Markdown; los `.mmd` de exportación son copias derivadas. No cambia arquitectura, código de aplicación ni contratos.

La representación se genera con el renderizador Mermaid para conservar los textos y flechas del diagrama. Las dependencias de exportación se mantienen en una carpeta de herramientas separada del frontend/backend y el navegador se utiliza sin ventana visible. No se inicia la API, se accede a datos o se envían correos.

Validación prevista: compilar los tres diagramas con el parser real de Mermaid, verificar que PNG/SVG existan con dimensiones válidas e inspeccionar visualmente el resultado. Enlazar las imágenes desde el documento original y registrar los resultados.

Referencia de exportación: [Mermaid CLI oficial](https://github.com/mermaid-js/mermaid-cli).

## Resultado

Generadas las seis imágenes PNG/SVG y tres fuentes `.mmd` en [diagramas/secuencia](../diagramas/secuencia/README.md), mediante Mermaid CLI 11.17.0 y Edge headless local. Configuración visual y script de regeneración incluidos. Las dependencias de documentación quedaron aisladas en `scratch/sequence-renderer`, sin modificar dependencias frontend/backend.

Los tres diagramas pasaron el parser y el renderizador reales. Se verificó integridad de PNG, dimensiones válidas, XML de SVG, enlaces locales y revisión visual de títulos, participantes, mensajes, alternativas y final de las secuencias. PNG a escala 2: CU25 2814 × 7112, CU26 3234 × 9526 y CU27 3636 × 12002 píxeles. Los SVG conservan ampliación sin rasterizar. Los diagramas largos mantienen sus flujos completos; para lectura ampliada usar SVG o PNG original.

La ejecución de exportación y sus navegadores terminaron. No se inició backend/worker ni se accedió a la base/proveedor IA/correos. La referencia principal del análisis sigue siendo el Markdown enlazado y ahora incluye las imágenes.

## Limpieza solicitada

El usuario solicita retirar las herramientas utilizadas. Se eliminarán únicamente `scratch/sequence-renderer` (renderizador y dependencias) y las copias `.mmd`, configuraciones JSON y `exportar.py` de esta exportación. Se conservarán las seis imágenes PNG/SVG, su índice y los bloques Mermaid editables del documento original. Se retirarán las instrucciones de regeneración que dependían de esos archivos.

Esta limpieza documental no modifica capas, contratos, contexto de tenant, permisos ni datos de la aplicación. Validación prevista: comprobar los límites de las rutas antes de borrar, verificar ausencia de los auxiliares, comparar SHA256 de las imágenes y revisar enlaces locales de los documentos afectados.

Resultado: eliminados el directorio del renderizador y los seis archivos auxiliares indicados, tras verificar sus rutas absolutas dentro del proyecto. Las seis imágenes conservaron su SHA256. El índice y el documento original mantienen los enlaces a las imágenes y la fuente editable.
