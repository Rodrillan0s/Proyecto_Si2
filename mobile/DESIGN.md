# OBRATEC Mobile — Design System Contract

## Product Overview
- **App Name:** OBRATEC Mobile (Plataforma de Gestión de Obras y Construcción)
- **Primary Audience:** Directores de Obra, Jefes de Cuadrilla, Supervisores de Campo, Administradores de Empresa.
- **Register:** Utility (Professional Field & Construction Tool).

## Visual Dials
- **DESIGN_VARIANCE:** 4 (Strict visual consistency, clean hierarchy, platform-adaptive mechanics).
- **MOTION_INTENSITY:** 3 (Subtle press feedback, smooth in-place state transitions 150-250ms, zero decorative lag).
- **VISUAL_DENSITY:** 6 (Field-readable information density, clear contrast, high scannability).

## Color Palette (Harmonized with Web)
- **Primary Brand (Safety Orange):** `Color(0xFFEA580C)` / Dark: `Color(0xFFC2410C)` / Light Tint: `Color(0xFFFFF7ED)`.
- **Secondary Brand (Deep Industrial Slate):** `Color(0xFF0F172A)` / Dark Surface: `Color(0xFF1E293B)`.
- **Neutral Background (Light):** `Color(0xFFF8FAFC)` / Surface Card: `Color(0xFFFFFFFF)`.
- **Neutral Background (Dark):** `Color(0xFF0B0F19)` / Surface Card: `Color(0xFF161F30)`.
- **Borders & Dividers:** `Color(0xFFE2E8F0)` / Dark: `Color(0xFF334155)`.
- **Semantic Accents:**
  - Active / Success: Emerald `Color(0xFF10B981)`
  - Planificación / Info: Sky Blue `Color(0xFF0284C7)`
  - Pausado / Warning: Amber `Color(0xFFF59E0B)`
  - Error / Destructive: Rose `Color(0xFFEF4444)`

## Typography & Iconography
- **Font Family:** Roboto / Outfit / Inter system font.
- **Headings:** Bold 700-900, tight tracking (-0.5 to 0.0), height >= 1.2.
- **Body & Labels:** Regular 400 & Medium 500, height 1.4-1.5, body >= 13-14sp.
- **Radius Family:** Soft Industrial (12px - 16px cards, 10px inputs, 12px buttons).
- **Touch Targets:** Minimum 48x48dp on all interactive elements.

## Rule Enforcement
- Zero inline arbitrary colors in screens; all styling via `AppTheme`.
- No generic placeholder data or stock template text.
- Full error, loading, empty, and offline state coverage.
