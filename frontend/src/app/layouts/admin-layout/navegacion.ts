import { ASSISTANT_PERMISSIONS } from '../../services/asistente.service';

export const REPORT_FAMILIES: Record<string, string[]> = {
  finanzas: ['presupuestario', 'comparativo_costos', 'costos_periodo', 'saldo_comercial'],
  inventario: ['stock', 'consumo_materiales'], personal: ['asignacion_personal', 'utilizacion_personal'],
  obras: ['avance_ejecutivo', 'estado_unidades'], incidencias: ['incidencias', 'incidencias_criticas'],
};
export interface NavItem { id: string; label: string; route: string; icon: string; permissions?: string[]; all?: string[]; global?: boolean; query?: Record<string, string>; family?: string; context?: 'estructura' | 'responsables'; }
export interface NavSection { id: string; label: string; icon: string; items: NavItem[]; }
const home = 'M3 12l9-9 9 9M5 10v11h5v-6h4v6h5V10';
const work = 'M3 21h18M5 21V3h14v18M9 7h1m4 0h1M9 11h1m4 0h1M10 21v-6h4v6';
const cost = 'M3 21h18M6 17V9m6 8V5m6 12v-6';
const stock = 'M21 8l-9 5-9-5m9 5v9M3 8l9-5 9 5v10l-9 5-9-5V8';
const people = 'M16 21v-2a4 4 0 00-4-4H6a4 4 0 00-4 4v2M13 7a4 4 0 11-8 0 4 4 0 018 0';
const settings = 'M12 3v3m0 12v3M3 12h3m12 0h3M5 5l2 2m10 10l2 2M5 19l2-2M17 7l2-2M16 12a4 4 0 11-8 0 4 4 0 018 0';
const chat = 'M21 11a9 9 0 01-9 9H3l-2 2V11a10 10 0 0120 0M6 9h10M6 13h7';
const alert = 'M12 3L2 21h20L12 3m0 6v5m0 3h.01';
export const NAVIGATION: NavSection[] = [
  { id: 'principal', label: 'PRINCIPAL', icon: home, items: [{ id: 'panel', label: 'Dashboard', route: '/panel', icon: home }] },
  { id: 'proyectos', label: 'PROYECTOS Y OBRAS', icon: work, items: [
    { id: 'obras', label: 'Ver obras', route: '/proyectos', icon: work, permissions: ['Visualizar_obras'] },
    { id: 'gestion', label: 'Gestión de proyectos', route: '/proyectos', query: { tab: 'gestion' }, icon: settings, all: ['Visualizar_obras', 'Modificar_obras'] },
    { id: 'nuevo', label: 'Nuevo proyecto', route: '/proyectos', query: { tab: 'nuevo' }, icon: 'M12 5v14M5 12h14', all: ['Visualizar_obras', 'Registrar_obras'] },
    { id: 'unidades', label: 'Asignación de unidades', route: '/proyectos', icon: stock, context: 'estructura', all: ['Visualizar_obras', 'Modificar_obras'] },
    { id: 'jefes', label: 'Asignar jefes de obra', route: '/proyectos', icon: people, context: 'responsables', all: ['Visualizar_obras', 'Modificar_obras'] },
    { id: 'ordenes', label: 'Órdenes de trabajo', route: '/ordenes-trabajo', icon: settings, permissions: ['Visualizar_obras'] },
    { id: 'incidencias', label: 'Incidencias', route: '/incidencias', icon: alert, permissions: ['Visualizar_incidencias'] },
  ] },
  { id: 'costos', label: 'PRESUPUESTOS Y COSTOS', icon: cost, items: [
    { id: 'apu', label: 'Presupuestos / APU', route: '/estimaciones', icon: cost, permissions: ['Visualizar_estimaciones'] },
    { id: 'control', label: 'Control de costos', route: '/control-costos', icon: cost, permissions: ['Visualizar_control_costos'] },
  ] },
  { id: 'comercial', label: 'COMERCIAL & CLIENTES', icon: people, items: [{ id: 'crm', label: 'CRM & Clientes', route: '/crm', icon: people, permissions: ['Visualizar_clientes'] }] },
  { id: 'inventario', label: 'INVENTARIO & LOGÍSTICA', icon: stock, items: [
    { id: 'stock', label: 'Inventario / Stock', route: '/inventario', icon: stock, permissions: ['Visualizar_inventario', 'Visualizar_materiales'] },
    { id: 'materiales', label: 'Materiales', route: '/materiales', icon: stock, permissions: ['Visualizar_materiales'] },
    { id: 'proveedores', label: 'Proveedores', route: '/proveedores', icon: people, permissions: ['Visualizar_proveedores'] },
    { id: 'compras', label: 'Órdenes de compra', route: '/compras', icon: stock, permissions: ['Visualizar_ordenes_compra'] },
    { id: 'equipos', label: 'Equipos y maquinaria', route: '/equipos-maquinaria', icon: settings, permissions: ['Visualizar_materiales'] },
  ] },
  { id: 'reportes', label: 'REPORTES & ANALÍTICA', icon: cost, items: Object.keys(REPORT_FAMILIES).map(family => ({
    id: `reportes-${family}`, label: 'Reportes ' + ({ finanzas: 'financieros', inventario: 'de inventario', personal: 'de personal', obras: 'de obras', incidencias: 'de incidencias' } as Record<string, string>)[family],
    route: '/reportes', query: { familia: family }, family, icon: ({ finanzas: cost, inventario: stock, personal: people, obras: work, incidencias: alert } as Record<string, string>)[family], permissions: ['Visualizar_reportes'],
  })) },
  { id: 'ia', label: 'INTELIGENCIA ARTIFICIAL', icon: chat, items: [{ id: 'asistente', label: 'Asistente Inteligente', route: '/asistente', icon: chat, permissions: ASSISTANT_PERMISSIONS }] },
  { id: 'admin', label: 'ADMINISTRACIÓN', icon: settings, items: [
    { id: 'usuarios', label: 'Usuarios', route: '/usuarios', icon: people, permissions: ['Visualizar_usuarios'] },
    { id: 'roles', label: 'Roles y permisos', route: '/roles', icon: settings, permissions: ['Visualizar_usuarios'] },
    { id: 'empresas', label: 'Empresas', route: '/empresas', icon: work, permissions: ['Visualizar_empresa'] },
    { id: 'bitacora', label: 'Bitácora', route: '/bitacora', icon: settings, permissions: ['Visualizar_usuarios'] },
    { id: 'backup', label: 'Copias de respaldo', route: '/backup', icon: stock, global: true },
  ] },
  { id: 'cuenta', label: 'CUENTA', icon: people, items: [
    { id: 'perfil', label: 'Mi perfil', route: '/perfil', icon: people },
    { id: 'seguridad', label: 'Seguridad y sesión', route: '/panel', query: { tab: 'seguridad' }, icon: settings },
  ] },
];
