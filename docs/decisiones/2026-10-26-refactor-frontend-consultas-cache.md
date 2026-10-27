# Decisión Arquitectónica: Refactorización de Consultas y Rendimiento en Frontend (Angular)

**Fecha:** 2026-10-26  
**Autor:** Antigravity Pairing Assistant  
**Alcance:** Frontend Web Angular (`src/app/`)  
**Componentes y Servicios afectados:**
- `src/app/services/lecturas.ts` (`LecturasCompartidas` con TTL en memoria e invalidación por mutación/tenant)
- `src/app/layouts/admin-layout/admin-layout.ts` (Memoización de `sections`, eliminación de consultas redundantes en selectores y reportes)
- `src/app/pages/panel/panel.ts` (Sincronización de observables, eliminación de doble carga inicial y reutilización de caché)
- `src/app/pages/usuarios/lista-usuarios/lista-usuarios.ts` (Eliminación de bucle polling artificial y uso de `EmpresaService` compartido)
- `src/app/services/proyectos.ts`, `src/app/services/materials.service.ts`, `src/app/services/empresa.ts`, `src/app/services/reportes.service.ts` (Retención de catálogos estáticos e invalidación automática en mutaciones)

---

## 1. Contexto y Problema

Durante la navegación en el cliente web se identificó una saturación de llamadas HTTP redundantes que generaban latencia innecesaria y sobrecarga en el backend:
1. `LecturasCompartidas` únicamente deduplicaba llamadas en vuelo simultáneas (`finalize` eliminaba la entrada inmediatamente tras completarse). No existía retención en memoria, forzando la repetición de peticiones idénticas al alternar entre pestañas o pantallas.
2. `AdminLayoutComponent` evaluaba la propiedad `get sections()` en cada ciclo de detección de cambios (tick de Angular), ejecutando verificaciones de permisos repetitivas y disparando peticiones al catálogo de reportes y al selector de obras cada vez que se abría el menú.
3. `PanelComponent` (Dashboard) ejecutaba una ráfaga desincronizada de 5 a 7 peticiones simultáneas en el inicio debido a la emisión temprana de `contexto.empresa$` combinada con `cargarDatosPorRol()` en `ngOnInit`.
4. `ListaUsuariosComponent` ejecutaba un bucle de espera artificial con `setTimeout` y peticiones directas vía `HttpClient` desconectadas de los servicios con caché.

---

## 2. Decisiones de Arquitectura y Patrones Implementados

### 2.1. Memoria Caché con TTL en `LecturasCompartidas`
Se extendió `LecturasCompartidas` para admitir un parámetro opcional `ttlMs` (Time-To-Live en milisegundos):
- **Catálogos estáticos** (Tipos de obra, unidades de medida, categorías de material, catálogo de reportes): TTL de 5 minutos (300,000 ms).
- **Listados operativos** (Obras de la empresa, empresas activas, conteo de usuarios): TTL de 60 segundos (60,000 ms).
- **Invalidación estricta por Tenant:** Si `empresaActiva$` o `auth.obtenerToken()` cambian, toda la caché de memoria se vacía inmediatamente, garantizando aislamiento estricto de datos entre empresas.
- **Invalidación explícita por Mutación:** Métodos `limpiar(key)` o `limpiarTodo()` invocados mediante operadores RxJS `tap` en mutaciones de `ProyectosService`, `EmpresaService` y `MaterialsService`.

### 2.2. Memoización en `AdminLayoutComponent`
- La propiedad `sections` se convirtió en un arreglo plano recalculado únicamente cuando:
  - Inicializa el componente o cambia el usuario autenticado.
  - Cambia la empresa activa en `contexto.empresa$`.
  - Se obtienen las familias del catálogo de reportes (`cargarFamilias`).
- Las obras y empresas para los selectores superiores evitan reconsultas si ya se encuentran en memoria y cuentan con el TTL de `LecturasCompartidas`.

### 2.3. Optimización en `PanelComponent`
- Reutilización de `ProyectosService.listarProyectos()`, `EmpresaService.listarEmpresas()`, `MaterialsService.listar()` y conteo de usuarios mediante `LecturasCompartidas` con TTL.
- Eliminación de consultas repetitivas al navegar hacia y desde el dashboard.

### 2.4. Refactorización de `ListaUsuariosComponent`
- Eliminación del polling artificial `while (!token) setTimeout` sustituyéndolo por validación síncrona contra `AuthService`.
- Reemplazo de llamadas directas a `/api/empresas` por `EmpresaService.listarEmpresas()`.

---

## 3. Contratos y Validación

- **Cero cambios en Backend:** Los endpoints, rutas, esquemas SQL y respuestas JSON permanecen 100% inalterados.
- **Resultados de Validación:**
  1. `npx tsc --noEmit` finalizado exitosamente con código de salida 0 (sin errores de tipos ni firmas).
  2. `npm run build` finalizado exitosamente con código de salida 0 (`Application bundle generation complete [16.083s]`).
