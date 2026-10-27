# Decisión Arquitectónica: Registro Masivo de Grupo de Usuarios y Selector de Respaldo por Empresa

**Fecha:** 2026-10-26  
**Autor:** Antigravity Pairing Assistant  
**Alcance:** Frontend Web Angular (`src/app/pages/usuarios/`, `src/app/pages/backup/`)  
**Archivos Afectados:**
- `src/app/pages/usuarios/lista-usuarios/lista-usuarios.html`
- `src/app/pages/usuarios/lista-usuarios/lista-usuarios.ts`
- `src/app/pages/backup/backup.html`
- `src/app/pages/backup/backup.ts`

---

## 1. Contexto y Objetivos

1. **Gestión de Usuarios:**
   - La creación manual de usuarios uno a uno resulta lenta cuando una empresa incorpora un equipo completo de obra (jefes de obra, electricistas, plomeros, albañiles).
   - Se requería un asistente de **"Crear Grupo de Usuarios"** para realizar un registro en lote con asignación a una única empresa destino.
   - Restricciones de Dominio y Seguridad cumplidas:
     - `ADMINISTRADOR_EMPRESA`: Empresa obligatoriamente fijada a su tenant; sólo puede asignar roles operativos de su empresa (`JEFE DE OBRA`, `ELECTRICO`, `PLOMERO`, `MAESTROALBAÑIL`, `ALBAÑIL`).
     - `ADMINISTRADOR` (Global): Puede seleccionar la empresa destino del lote y asignar roles de empresa.
     - Credenciales temporales individuales seguras (sin contraseña común), cumpliendo las reglas criptográficas del sistema (`password_cumple_requisitos`: mayúsculas, minúsculas, números y símbolos con longitud >= 10).
     - Resumen final de altas y credenciales descargables (archivo TXT) y copiables al portapapeles.
     - **Sin tablas nuevas en BD**: "Grupo" es estrictamente una operación masiva transaccional en el cliente, no un modelo persistido.
     - Modernización estética del panel (KPIs bento, búsqueda en vivo multifiltro, badges cromáticos de roles, avatares estilizados).
     - Conservación del registro individual ("Nuevo Usuario") y del modal de edición existente.
2. **Panel de Respaldos:**
   - Enriquecido visualmente el selector de la copia de seguridad para reflejar opciones por empresa mediante `<optgroup>` sin modificar el contrato con FastAPI ni el daemon Oracle (despachando alcance `'base_datos'`).
   - Respetada la directiva de no añadir leyendas adicionales debajo del selector.

---

## 2. Decisiones de Arquitectura y Patrones

### 2.1. Asistente «Crear Grupo de Usuarios» en `lista-usuarios.ts`
- **Estructura de Fila (`FilaGrupoUsuario`):**
  - `ci`, `nombre_completo`, `nombre_usuario`, `correo`, `telefono`, `direccion`, `nro_rol`, `password_temporal`, `estado_registro` ('PENDIENTE' | 'CREANDO' | 'EXITO' | 'ERROR'), `error_detalle`.
- **Generación de Contraseñas:**
  - Generador criptográfico individual que asegura la coexistencia de mayúsculas, minúsculas, dígitos y símbolos.
- **Validaciones:**
  - Control de duplicados en caliente dentro del lote (mismo CI, username o correo) antes de enviar.
  - Validación cruzada contra la lista en memoria de usuarios del sistema.
- **Ejecución y Resumen:**
  - Envío secuencial con barra de progreso, captura de respuestas y pantalla final de resumen con exportación y copiado rápido.

### 2.2. Selector de Respaldo en `backup.ts`
- Inyección de `EmpresaService` para obtener empresas cacheadas.
- El selector expone la base de datos completa y las opciones por empresa.
- El método `crear()` continúa enviando `base_datos` cumpliendo estrictamente con la arquitectura de `docs/ARQUITECTURA_BACKUP_RESTORE.md`.

---

## 3. Resultados de Validación
- Verificación estricta de compilación TypeScript (`npx tsc --noEmit`): Código de salida 0.
- Compilación de producción Angular (`npm run build`): Código de salida 0 ([16.52s], bundle generado exitosamente en `dist/frontend`).
