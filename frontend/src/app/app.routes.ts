import { Routes } from '@angular/router';

//COMPONENTES
import { LoginComponent } from './pages/login/login';
import { ListaUsuariosComponent } from './pages/usuarios/lista-usuarios/lista-usuarios';
import { HomeComponent } from './pages/home/home';
import { PerfilComponent } from './pages/perfil/perfil';
import { PanelComponent } from './pages/panel/panel';
import { RolesComponent } from './pages/roles/roles';
import { ListaEmpresasComponent } from './pages/empresas/lista-empresas/lista-empresas';
import { BackupComponent } from './pages/backup/backup';
import { NotificacionesComponent } from './pages/notificaciones/notificaciones';
import { BitacoraComponent } from './pages/bitacora/bitacora';
import { RegistroComponent } from './pages/registro/registro';
import { MainClienteComponent } from './pages/main-cliente/main-cliente';
import { ProyectosComponent } from './pages/proyectos/proyectos';
import { ProyectoDetalleComponent } from './pages/proyectos/detalle/proyecto-detalle';

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

    // RUTAS PRIVADAS ADMINISTRATIVAS (Comparten el mismo header y sidebar unificado de Procore)
    {
        path: '',
        component: AdminLayoutComponent,
        canActivate: [authGuard, roleGuard],
        data: { roles: ['ADMINISTRADOR', 'ADMINISTRADOR_EMPRESA', 'JEFE DE OBRA'] },
        children: [
            { path: 'panel', component: PanelComponent },
            { path: 'proyectos', component: ProyectosComponent },
            { path: 'proyectos/:id', component: ProyectoDetalleComponent },
            { path: 'usuarios', component: ListaUsuariosComponent, canActivate: [roleGuard], data: { roles: ['ADMINISTRADOR', 'ADMINISTRADOR_EMPRESA'] } },
            { path: 'roles', component: RolesComponent, canActivate: [roleGuard], data: { roles: ['ADMINISTRADOR', 'ADMINISTRADOR_EMPRESA'] } },
            { path: 'empresas', component: ListaEmpresasComponent, canActivate: [roleGuard], data: { roles: ['ADMINISTRADOR'] } },
            { path: 'backup', component: BackupComponent },
            { path: 'notificaciones', component: NotificacionesComponent },
            { path: 'bitacora', component: BitacoraComponent, canActivate: [roleGuard], data: { roles: ['ADMINISTRADOR'] } }
        ]
    },

    // CU09 - CONSULTAR PERFIL: Accesible para TODOS los usuarios autenticados con AdminLayout
    {
        path: '',
        component: AdminLayoutComponent,
        canActivate: [authGuard, roleGuard],
        data: { roles: ['ADMINISTRADOR', 'ADMINISTRADOR_EMPRESA', 'SUPERVISOR', 'PERSONAL_CAMPO', 'CONTRATISTA', 'PROPIETARIO', 'RESPONSABLE_PROYECTO'] },
        children: [
            { path: 'perfil', component: PerfilComponent }
        ]
    },
    { path: 'main_cliente', component: MainClienteComponent, canActivate: [authGuard, roleGuard], data: { roles: ['CLIENTE'] } },
    { path: '**', redirectTo: 'login' }
];