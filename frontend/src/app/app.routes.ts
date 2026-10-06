import { Routes } from '@angular/router';
import { ASSISTANT_PERMISSIONS } from './services/asistente.service';

//COMPONENTES
import { LoginComponent } from './pages/login/login';
import { HomeComponent } from './pages/home/home';
import { RegistroComponent } from './pages/registro/registro';
import { MainClienteComponent } from './pages/main-cliente/main-cliente';
import { ProveedoresComponent } from './pages/proveedores/proveedores';

//LAYOUTS
import { AdminLayoutComponent } from './layouts/admin-layout/admin-layout';

//GUARDS
import { publicGuard } from './guards/public-guard';
import { authGuard } from './guards/auth-guard';
import { roleGuard } from './guards/role-guard';

export const routes: Routes = [
    // RUTAS PUBLICAS (Redirigen si ya existe sesion activa)
    { path: '', component: HomeComponent, canActivate: [publicGuard] },
    { path: 'login', component: LoginComponent, canActivate: [publicGuard] },
    { path: 'registro', component: RegistroComponent, canActivate: [publicGuard] },

    // Redireccion de home
    { path: 'home', redirectTo: 'panel', pathMatch: 'full' },
    { path: 'main_cliente', redirectTo: 'panel', pathMatch: 'full' },

    // RUTAS PRIVADAS UNIFICADAS (AppShell corporativo protegido por permisos)
    {
        path: '',
        component: AdminLayoutComponent,
        canActivate: [authGuard],
        children: [
            { path: 'reportes', loadComponent: () => import('./pages/reportes/reportes').then(module => module.ReportesComponent) },
            { path: 'asistente', loadComponent: () => import('./pages/asistente/asistente-workspace').then(module => module.AsistenteWorkspace), canActivate: [roleGuard], data: { permissions: ASSISTANT_PERMISSIONS } },
            { path: 'panel', loadComponent: () => import('./pages/panel/panel').then(module => module.PanelComponent) },
            {
                path: 'proyectos',
                loadComponent: () => import('./pages/proyectos/proyectos').then(module => module.ProyectosComponent),
                canActivate: [roleGuard],
                data: { permissions: ['Visualizar_obras'] }
            },
            {
                path: 'proyectos/:id',
                loadComponent: () => import('./pages/proyectos/detalle/proyecto-detalle').then(module => module.ProyectoDetalleComponent),
                canActivate: [roleGuard],
                data: { permissions: ['Visualizar_obras'] }
            },
            {
                path: 'materiales',
                loadComponent: () => import('./pages/materiales/materiales').then(module => module.MaterialesComponent),
                canActivate: [roleGuard],
                data: { permissions: ['Visualizar_materiales'] }
            },
            {
                path: 'crm',
                loadComponent: () => import('./pages/crm/crm').then(module => module.CrmComponent),
                canActivate: [roleGuard],
                data: { permissions: ['Visualizar_clientes'] }
            },
            {
                path: 'proveedores',
                loadComponent: () => import('./pages/proveedores/proveedores').then(module => module.ProveedoresComponent),
                canActivate: [roleGuard],
                data: { permissions: ['Visualizar_proveedores'] }
            },
            {
                path: 'inventario',
                loadComponent: () => import('./pages/inventario/inventario').then(module => module.InventarioComponent),
                canActivate: [roleGuard],
                data: { permissions: ['Visualizar_inventario', 'Visualizar_materiales'] }
            },
            {
                path: 'compras',
                loadComponent: () => import('./pages/compras/compras').then(module => module.ComprasComponent),
                canActivate: [roleGuard],
                data: { permissions: ['Visualizar_ordenes_compra'] }
            },
            {
                path: 'usuarios',
                loadComponent: () => import('./pages/usuarios/lista-usuarios/lista-usuarios').then(module => module.ListaUsuariosComponent),
                canActivate: [roleGuard],
                data: { permissions: ['Visualizar_usuarios'] }
            },
            {
                path: 'roles',
                loadComponent: () => import('./pages/roles/roles').then(module => module.RolesComponent),
                canActivate: [roleGuard],
                data: { permissions: ['Visualizar_usuarios'] }
            },
            {
                path: 'empresas',
                loadComponent: () => import('./pages/empresas/lista-empresas/lista-empresas').then(module => module.ListaEmpresasComponent),
                canActivate: [roleGuard],
                data: { permissions: ['Visualizar_empresa'] }
            },
            {
                path: 'empresas/:id',
                loadComponent: () => import('./pages/empresas/detalle-empresa/detalle-empresa').then(module => module.DetalleEmpresaComponent),
                canActivate: [roleGuard],
                data: { permissions: ['Visualizar_empresa'] }
            },
            {
                path: 'backup',
                loadComponent: () => import('./pages/backup/backup').then(module => module.BackupComponent),
                canActivate: [roleGuard],
                data: { roles: ['ADMINISTRADOR'] }
            },
            {
                path: 'notificaciones',
                loadComponent: () => import('./pages/notificaciones/notificaciones').then(module => module.NotificacionesComponent)
            },
            {
                path: 'bitacora',
                loadComponent: () => import('./pages/bitacora/bitacora').then(module => module.BitacoraComponent),
                canActivate: [roleGuard],
                data: { permissions: ['Visualizar_usuarios'] }
            },
            {
                path: 'ordenes-trabajo',
                loadComponent: () => import('./pages/ordenes-trabajo/ordenes-trabajo').then(module => module.OrdenesTrabajoComponent),
                canActivate: [roleGuard],
                data: { permissions: ['Visualizar_obras'] }
            },
            {
                path: 'incidencias',
                loadComponent: () => import('./pages/incidencias/incidencias').then(module => module.IncidenciasComponent),
                canActivate: [roleGuard],
                data: { permissions: ['Visualizar_incidencias'] }
            },
            {
                path: 'incidencias/asignadas',
                loadComponent: () => import('./pages/incidencias/asignadas/incidencias-asignadas').then(module => module.IncidenciasAsignadasComponent)
            },
            {
                path: 'incidencias/:id',
                loadComponent: () => import('./pages/incidencias/detalle/incidencia-detalle').then(module => module.IncidenciaDetalleComponent)
            },
            {
                path: 'estimaciones',
                loadComponent: () => import('./pages/estimaciones/estimaciones').then(module => module.EstimacionesComponent),
                canActivate: [roleGuard],
                data: { permissions: ['Visualizar_estimaciones'] }
            },
            {
                path: 'control-costos',
                loadComponent: () => import('./pages/control-costos/control-costos').then(module => module.ControlCostosComponent),
                canActivate: [roleGuard],
                data: { permissions: ['Visualizar_control_costos'] }
            },
            {
                path: 'perfil',
                loadComponent: () => import('./pages/perfil/perfil').then(module => module.PerfilComponent)
            },
            {   path: 'equipos-maquinaria',
                loadComponent: () => import('./pages/equipo-maquinaria/equipo-maquinaria').then(module => module.EquipoMaquinariaComponent),
                canActivate: [roleGuard],
                data: { permissions: ['Visualizar_materiales'] }
            },
]
    },
    { path: '**', redirectTo: 'login' }
];
