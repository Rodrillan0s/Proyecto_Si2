# Backup de base con evidencias externas ausentes

Fecha: 2026-10-04 (America/La_Paz).

El usuario autoriza ignorar por ahora los tres archivos de evidencias ausentes, que atribuye a su colega, y continuar la prueba de backups. Se revisaron arquitectura general, Backup/Restore, operación, referencias de PostgreSQL y código de captura/restauración/diagnóstico. La comprobación actual confirmó tres referencias válidas, tres archivos ausentes, control instalado, sin mantenimiento ni restauraciones en cola.

El alcance `base_datos` permitirá crear el dump y el paquete cifrado aunque falten esos archivos. Conservará los registros originales en PostgreSQL, las huellas de archivos disponibles y una lista explícita `evidencias_no_disponibles` en el manifiesto autenticado. No se borrarán filas de negocio ni se inventarán archivos. La ausencia solo se tolera en ese alcance: `sistema_completo`, rutas inseguras, enlaces y archivos modificados siguen sujetos a las validaciones existentes.

El contrato HTTP incorpora advertencias del archivo y la etapa del trabajo LISTO indica las evidencias ausentes. El catálogo almacena esta metadata en su JSONB actual; no cambia el esquema ni requiere migración. Se mantienen `routes → services → repos`, ADMINISTRADOR global, snapshot de todos los tenants, control independiente y barrera de captura. Angular ya muestra la etapa; Flutter no consume este módulo.

La creación de una copia PostgreSQL no certifica recuperación de los archivos externos ausentes. El flujo existente de ensayo/promoción conservará esa distinción y rechazará certificar recuperación completa de estos paquetes; la comprobación de integridad/catálogo del dump podrá verificarlos sin restaurar la base actual. Paquetes antiguos sin el campo mantienen su comportamiento.

Validación prevista: casos reales de cifrado/paquete base con evidencia faltante, conservación de inventario de negocio y bloqueo de certificación de recuperación completa; copia completa sigue estricta. Repetir pruebas backend, encolar una nueva copia manual con el actor del trabajo anterior revalidado como administrador, ejecutar una pasada acotada y comprobar archivo, cifrado, manifiesto y catálogo del dump. No cambiar `.env`, programación, registros de evidencias, restaurar PostgreSQL ni dejar worker/backend ocultos.

## Resultado implementado y verificado

Se implementó tolerancia de archivos ausentes únicamente para `base_datos`, metadata autenticada de omisión, advertencias públicas y etapa del trabajo. El parser de rutas y la captura completa siguen estrictos. Paquetes con ausencias registradas no pasan como recuperación completa en el flujo de restauración. La consola distingue verificación de integridad de ese ensayo y mantiene las comprobaciones de huellas de evidencias disponibles.

**47 pruebas backend aprobadas.** Los casos nuevos descifran y desempaquetan realmente una copia base con ausencia, comprueban el dump y el inventario original, la advertencia pública y el bloqueo de certificación completa; mantienen rechazo de traversal. No se modificó frontend: Angular ya muestra `etapa`; los campos HTTP agregados son compatibles con sus consumidores actuales. Flutter no tiene consumidor del módulo.

Prueba real: copia manual `e0077463-1e21-41c2-939a-1d548baeb267` llegó a **LISTO**. Archivo `obratec_e0077463-1e21-41c2-939a-1d548baeb267.obratec`, 978864 bytes, 132 tablas del inventario global y tres evidencias ausentes registradas. SHA256 `83b95fdd96f4a47c711208354fcb4582e5cea114159cce7a3dd5c9f862a301de`. Verificados almacenamiento, tamaño/huella, descifrado autenticado, igualdad de manifiesto/control y catálogo mediante `pg_restore --list`. El temporal de comprobación se limpió. Se conservó el historial previo.

El worker ejecutó una sola pasada visible y terminó. Control sin mantenimiento ni escritores; latido reciente puede mostrarse activo en UI hasta vencer su ventana de dos minutos, sin significar que exista un proceso continuo. No se aplicaron migraciones, se restauró PostgreSQL, se inició backend adicional ni se guardó programación. Automatización continua, restauración y recuperación externa siguen pendientes. [Resultado actualizado](../PRUEBA_BACKUPS_UBUNTU_2026-10-04.md).
