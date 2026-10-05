import { Routes } from '@angular/router';
import { ReportesComponent } from './pages/reportes/reportes';

//COMPONENTES
import { LoginComponent } from './pages/login/login';
import { ListaUsuariosComponent } from './pages/usuarios/lista-usuarios/lista-usuarios';
import { HomeComponent } from './pages/home/home';
import { PerfilComponent } from './pages/perfil/perfil';
import { PanelComponent } from './pages/panel/panel';
import { RolesComponent } from './pages/roles/roles';
import { ListaEmpresasComponent } from './pages/empresas/lista-empresas/lista-empresas';
import { DetalleEmpresaComponent } from './pages/empresas/detalle-empresa/detalle-empresa';
import { BackupComponent } from './pages/backup/backup';
import { NotificacionesComponent } from './pages/notificaciones/notificaciones';
import { BitacoraComponent } from './pages/bitacora/bitacora';
import { RegistroComponent } from './pages/registro/registro';
import { MainClienteComponent } from './pages/main-cliente/main-cliente';
import { ProyectosComponent } from './pages/proyectos/proyectos';
import { ProyectoDetalleComponent } from './pages/proyectos/detalle/proyecto-detalle';
import { MaterialesComponent } from './pages/materiales/materiales';
import { ProveedoresComponent } from './pages/proveedores/proveedores';             
import { ComprasComponent } from './pages/compras/compras';
import { OrdenesTrabajoComponent } from './pages/ordenes-trabajo/ordenes-trabajo';
import { CrmComponent } from './pages/crm/crm';
import { InventarioComponent } from './pages/inventario/inventario';
import { EquipoMaquinariaComponent } from './pages/equipo-maquinaria/equipo-maquinaria';
import { EstimacionesComponent } from './pages/estimaciones/estimaciones';
import { ControlCostosComponent } from './pages/control-costos/control-costos';
import { IncidenciasComponent } from './pages/incidencias/incidencias';
import { IncidenciasAsignadasComponent } from './pages/incidencias/asignadas/incidencias-asignadas';
import { IncidenciaDetalleComponent } from './pages/incidencias/detalle/incidencia-detalle';

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
            { path: 'reportes', component: ReportesComponent },
            { path: 'panel', component: PanelComponent },
            { 
                path: 'proyectos', 
                component: ProyectosComponent, 
                canActivate: [roleGuard], 
                data: { permissions: ['Visualizar_obras'] } 
            },
            { 
                path: 'proyectos/:id', 
                component: ProyectoDetalleComponent, 
                canActivate: [roleGuard], 
                data: { permissions: ['Visualizar_obras'] } 
            },
            { 
                path: 'materiales',  
                component: MaterialesComponent, 
                canActivate: [roleGuard], 
                data: { permissions: ['Visualizar_materiales'] } 
            },
            { 
                path: 'crm', 
                component: CrmComponent, 
                canActivate: [roleGuard], 
                data: { permissions: ['Visualizar_clientes'] } 
            },
            { 
                path: 'proveedores', 
                component: ProveedoresComponent, 
                canActivate: [roleGuard], 
                data: { permissions: ['Visualizar_proveedores'] } 
            },
            { 
                path: 'inventario', 
                component: InventarioComponent, 
                canActivate: [roleGuard], 
                data: { permissions: ['Visualizar_inventario', 'Visualizar_materiales'] } 
            },
            { 
                path: 'compras', 
                component: ComprasComponent, 
                canActivate: [roleGuard], 
                data: { permissions: ['Visualizar_ordenes_compra'] } 
            },
            { 
                path: 'usuarios', 
                component: ListaUsuariosComponent, 
                canActivate: [roleGuard], 
                data: { permissions: ['Visualizar_usuarios'] } 
            },
            { 
                path: 'roles', 
                component: RolesComponent, 
                canActivate: [roleGuard], 
                data: { permissions: ['Visualizar_usuarios'] } 
            },
            { 
                path: 'empresas', 
                component: ListaEmpresasComponent, 
                canActivate: [roleGuard], 
                data: { permissions: ['Visualizar_empresa'] } 
            },
            { 
                path: 'empresas/:id', 
                component: DetalleEmpresaComponent, 
                canActivate: [roleGuard], 
                data: { permissions: ['Visualizar_empresa'] } 
            },
            { 
                path: 'backup', 
                component: BackupComponent, 
                canActivate: [roleGuard], 
                data: { roles: ['ADMINISTRADOR'] }
            },
            { 
                path: 'notificaciones', 
                component: NotificacionesComponent 
            },
            { 
                path: 'bitacora', 
                component: BitacoraComponent, 
                canActivate: [roleGuard], 
                data: { permissions: ['Visualizar_usuarios'] } 
            },
            {
                path: 'ordenes-trabajo',
                component: OrdenesTrabajoComponent,
                canActivate: [roleGuard],
                data: { permissions: ['Visualizar_obras'] }
            },
            {
                path: 'incidencias',
                component: IncidenciasComponent,
                canActivate: [roleGuard],
                data: { permissions: ['Visualizar_incidencias'] }
            },
            {
                path: 'incidencias/asignadas',
                component: IncidenciasAsignadasComponent
            },
            {
                path: 'incidencias/:id',
                component: IncidenciaDetalleComponent
            },
            {
                path: 'estimaciones',
                component: EstimacionesComponent,
                canActivate: [roleGuard],
                data: { permissions: ['Visualizar_estimaciones'] }
            },
            {
                path: 'control-costos',
                component: ControlCostosComponent,
                canActivate: [roleGuard],
                data: { permissions: ['Visualizar_control_costos'] }
            },
            { 
                path: 'perfil', 
                component: PerfilComponent 
            },
            {   path: 'equipos-maquinaria',
                component: EquipoMaquinariaComponent,
                canActivate: [roleGuard],
                data: { permissions: ['Visualizar_materiales'] }
            },
            {    path :'estimaciones',
                component: EstimacionesComponent,
                canActivate: [roleGuard],}
                
        ]
    },
    { path: '**', redirectTo: 'login' }
];
