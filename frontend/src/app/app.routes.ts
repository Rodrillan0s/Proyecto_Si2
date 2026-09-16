import { Routes } from '@angular/router';

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
import { OrdenesTrabajoComponent } from './pages/ordenes-trabajo/ordenes-trabajo';

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
                path: 'proveedores', 
                component: ProveedoresComponent, 
                canActivate: [roleGuard], 
                data: { permissions: ['Visualizar_proveedores'] } 
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
                data: { permissions: ['Visualizar_empresa'] } 
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
                path: 'perfil', 
                component: PerfilComponent 
            }
        ]
    },
    { path: '**', redirectTo: 'login' }
];
