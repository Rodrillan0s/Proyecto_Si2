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

//LAYOUTS
import { AdminLayoutComponent } from './layouts/admin-layout/admin-layout';

//GUARDS
import { publicGuard } from './guards/public-guard';
import { authGuard } from './guards/auth-guard';

export const routes: Routes = [
    // RUTAS PUBLICAS (Redirigen si ya existe sesion activa)
    { path: '', component: HomeComponent, canActivate: [publicGuard] },
    { path: 'login', component: LoginComponent, canActivate: [publicGuard] },

    // Redireccion de home
    { path: 'home', redirectTo: 'panel', pathMatch: 'full' },

    // RUTAS PRIVADAS ADMINISTRATIVAS (Comparten el mismo header y sidebar unificado de Procore)
    {
        path: '',
        component: AdminLayoutComponent,
        canActivate: [authGuard],
        children: [
            { path: 'panel', component: PanelComponent },
            { path: 'perfil', component: PerfilComponent },
            { path: 'usuarios', component: ListaUsuariosComponent },
            { path: 'roles', component: RolesComponent },
            { path: 'empresas', component: ListaEmpresasComponent },
            { path: 'backup', component: BackupComponent },
            { path: 'notificaciones', component: NotificacionesComponent },
            { path: 'bitacora', component: BitacoraComponent }
        ]
    },
    { path: '**', redirectTo: 'login' }
];