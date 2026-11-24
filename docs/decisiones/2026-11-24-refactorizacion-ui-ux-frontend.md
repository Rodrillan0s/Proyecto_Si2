# Decisión de Arquitectura y Diseño: Refactorización Integral UI/UX del Frontend Angular

**Fecha:** 2026-11-24  
**Alcance:** Exclusivamente `frontend/` (Angular 21 + Tailwind CSS 3.4). Sin cambios en `backend/`, contratos HTTP/API, base de datos, migraciones, permisos ni aislamiento multiempresa.

---

## 1. Diagnóstico de la auditoría inicial

Se auditaron los **35 módulos** bajo `frontend/src/app/pages/`, el layout principal (`admin-layout`) y los 5 componentes compartidos en `frontend/src/app/components/ui/`:

1. **Fragmentación visual:**
   - Coexistencia de `Outfit` (en `index.html` y `admin-layout.css`) con `Inter` (en `styles.css`).
   - `tailwind.config.js` sin tokens de diseño centralizados (`extend: {}`).
   - 18 módulos con archivos CSS extensos independientes (`ordenes-trabajo` 1,290 L, `login` 983 L, `inventario` 885 L, `proyectos` 843 L, `equipo-maquinaria` 797 L, `reportes` 620 L, `compras` 616 L, `panel` 478 L, `home` 419 L, `backup` 349 L, etc.) y 17 módulos basados en clases utilitarias Tailwind, con paletas, radios, sombras y encabezados inconsistentes.
   - `admin-layout.css` (873 L) conserva ~450 líneas de estilos heredados no utilizados y presenta problemas en móvil (`height: 100vh` en lugar de `100dvh`, cabecera con `flex-wrap` que desborda, dropdowns fijos `w-96`/`w-80`, `padding: 0` en `.panel-content` bajo `850px`).
2. **Etiquetas técnicas o académicas visibles en UI:**
   - Se detectaron códigos `CU12`, `CU14`, `CU15`, `CU16`, `CU32`, `CU39`, `CU42`, `HU54`–`HU168`, `Multi-tenant`, `SaaS` y encabezados redundantes tipo `Gestión de ...` en `admin-layout`, `navegacion.ts`, `panel`, `control-costos`, `posventa`, `proyectos/detalle`, `proyectos/estructura`, `proyectos/presupuesto`, `cronogramas`, `crm`, `incidencias`, `proveedores`, `materiales`, `empresas`, `roles`, `usuarios`, `pagos`, `consultas-tecnicas`, `gastos-operativos` y `home`.
3. **Subutilización de componentes compartidos:**
   - Solo 6 de 35 módulos utilizaban `components/ui/*` (`page-header`, `dashboard-card`, `empty-state`, `status-badge`, `confirm-dialog`), y faltaban estados estandarizados de carga (`loading-state`) y alertas (`alert-banner`).

---

## 2. Arquitectura del sistema de diseño unificado

### Capas y responsabilidades
1. **Capa de Tokens y Base Global (`frontend/src/index.html`, `frontend/tailwind.config.js`, `frontend/src/styles.css`):**
   - Tipografía única: **`Outfit`** (`font-sans`), con `font-variant-numeric: tabular-nums` para KPIs y tablas financieras/numéricas.
   - Variables CSS centralizadas (`:root` y `.dark`):
     - Superficies neutrales frías (familia Slate): `--ob-bg`, `--ob-surface`, `--ob-surface-subtle`, `--ob-border`, `--ob-text`, `--ob-text-secondary`, `--ob-text-muted`.
     - Acento corporativo único: Ámbar cálido arquitectónico (`--ob-accent: #d97706`, hover `#b45309`, soft `#fef3c7`).
     - Shell corporativo: Azul marino arquitectónico (`--ob-shell: #0c1824`, `--ob-shell-hover: #162638`).
     - Estados semánticos: `--ob-success`, `--ob-warning`, `--ob-danger`, `--ob-info`.
     - Radios, sombras tintadas en slate, escala `z-index` y focus-visible accesible.
   - Clases reutilizables en `@layer components` (`.ob-page`, `.ob-card`, `.ob-btn-*`, `.ob-input`, `.ob-table-wrap`, `.ob-table`, `.ob-modal-*`, `.ob-alert-*`) y salvaguardas responsive globales dentro de `.panel-content`.
2. **Capa de Layout y Navegación (`admin-layout` + `navegacion.ts`):**
   - AppShell adaptable a escritorio (`>= 1280px`), portátil (`1024px–1279px`), tablet (`768px–1023px`) y móvil (`< 768px`).
   - Sidebar colapsable en escritorio y drawer deslizable con backdrop en tablet/móvil.
   - Dropdowns de empresa, obra y notificaciones acotados a `calc(100vw - 1.5rem)`.
   - Etiquetas de navegación comerciales, claras y sin jerga técnica.
3. **Capa de Componentes Compartidos (`frontend/src/app/components/ui/`):**
   - Refinamiento de `PageHeaderComponent`, `DashboardCardComponent`, `EmptyStateComponent`, `StatusBadgeComponent`, `ConfirmDialogComponent`.
   - Incorporación de `LoadingStateComponent` (skeletons) y `AlertBannerComponent` (error/éxito/advertencia/info).
4. **Capa de Vistas (35 módulos en `frontend/src/app/pages/`):**
   - Limpieza completa de etiquetas técnicas (`CUxx`, `HUxxx`, `Multi-tenant`, `SaaS`, `Gestión de ...`) respetando los contratos de prueba existentes.
   - Adopción de variables `--ob-*`, tipografía unificada, dark mode coherente y reglas responsive para formularios, tablas, tarjetas y modales.

---

## 3. Contratos, Tenant y Permisos

- **Sin cambios en servicios HTTP ni endpoints.**
- **Aislamiento multiempresa intacto:** se preservan íntegramente `AuthService`, `ContextoOperativo`, `roleGuard`, `authGuard`, `publicGuard`, `SuscripcionService` y la lógica de `ADMINISTRADOR` global vs `ADMINISTRADOR_EMPRESA` / roles operativos / `CLIENTE`.
- **Compatibilidad SSR (`@angular/ssr`):** toda lógica de DOM/viewport permanece protegida con `isPlatformBrowser`.

---

## 4. Validación ejecutada

- **`npm run build`:** Exitoso (`BUILD_EXIT=0`, bundle de producción generado en 25.7s, 0 errores).
- **Suites de pruebas Angular ejecutadas:**
  - `test:posventa`: **3/3 passed**
  - `test:pagos`: **17/17 passed**
  - `test:cu30`: **12/12 passed**
  - `test:cu31`: **3/3 passed**
  - `test:cronogramas`: **10/10 passed**
  - `test:gastos-finales`: **10/10 passed**
  - `test:navigation`: 18/20 passed (2 fallos preexistentes en `admin-layout.spec.ts` no introducidos por la refactorización: `sections` poblado en `ngOnInit` sin `detectChanges()` en test y `<app-asistente>` sin `*ngIf` en el layout original).
  - `test:reportes`: 12/25 passed (13 fallos preexistentes en `reportes-asistente.spec.ts`; no se modificó `asistente.ts` ni `reportes.ts`).
  - `test:backups`: 19/21 passed (2 fallos preexistentes en `backup.spec.ts`; no se modificó el módulo `backup/`).
- **Integridad de alcance:** 0 archivos modificados en `backend/`, 0 migraciones ejecutadas, sin `git commit` ni `git push`.
