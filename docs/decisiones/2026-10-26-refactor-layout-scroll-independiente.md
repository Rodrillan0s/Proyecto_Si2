# Decisión Arquitectónica: Aislamiento de Scroll Independiente (Sidebar vs Main Content)

**Fecha:** 2026-10-26  
**Autor:** Antigravity Pairing Assistant  
**Alcance:** Frontend Web Angular (`src/app/layouts/admin-layout/`)  
**Archivos Afectados:**
- `src/app/layouts/admin-layout/admin-layout.css`
- `src/app/layouts/admin-layout/admin-layout.html`
- `src/app/layouts/admin-layout/admin-layout.ts`

---

## 1. Contexto y Problema

En la disposición anterior del layout administrativo (`AdminLayoutComponent`):
1. El contenedor raíz `.home-container` y el cuerpo `.panel-body` utilizaban `min-height: 100vh` sin restricción de altura (`height: 100vh; overflow: hidden`).
2. Esto provocaba que el scroll se ejecutara a nivel de la ventana global (`window.scrollY`), arrastrando la barra lateral (`.panel-sidebar`) junto con el contenido al hacer scroll en cualquier sección.
3. Al interactuar con elementos ubicados en la parte inferior de la barra de navegación (como "Usuarios" o "Configuración"), el usuario debía desplazar toda la ventana hacia abajo. Al hacer clic, la nueva ruta se renderizaba manteniendo la posición de scroll de la ventana (`scrollY` elevado), cargando la vista "abajo" y obligando a scrollear de vuelta a la cabecera, lo que a su vez reseteaba y desorientaba la posición del menú lateral.

---

## 2. Decisión de Arquitectura y Diseño UI

### 2.1. Aislamiento Físico de Paneles (Dual-Pane Independent Scroll)
- **Viewport Lock:** `.home-container` se configura con `height: 100vh; max-height: 100vh; overflow: hidden; display: flex; flex-direction: column;`. El `body` de la aplicación nunca realiza scroll.
- **Header Fijo:** `.panel-header` mantiene altura fija con `flex-shrink: 0`.
- **Panel Body:** `.panel-body` consume el espacio restante con `flex: 1; height: calc(100vh - 4.5rem); max-height: calc(100vh - 4.5rem); overflow: hidden;`.
- **Sidebar Container:** `.panel-sidebar` posee `height: 100%; max-height: 100%; overflow-y: auto; overflow-x: hidden; overscroll-behavior: contain;`. Su scroll es 100% independiente del contenido central con scrollbar personalizado sutil en tema oscuro.
- **Main Content Container:** `.panel-content` posee `height: 100%; max-height: 100%; overflow-y: auto; overflow-x: hidden; overscroll-behavior: contain;`.

### 2.2. Restablecimiento Automático de Scroll en Navegación
- Se expone `#panelContent` en la plantilla de `main.panel-content`.
- Al recibirse un evento `NavigationEnd` en `admin-layout.ts`, se restablece el desplazamiento del panel principal a `scrollTop = 0`.
- La posición de scroll del sidebar se preserva completamente intacta en memoria del DOM, manteniendo al usuario ubicado en la sección de navegación seleccionada.

---

## 3. Resultados de Validación
- Compilación de tipos TypeScript: `npx tsc --noEmit` completado con éxito (código 0).
- Compilación de bundle de producción Angular: `npm run build` completado con éxito (código 0, [18.39s]).
