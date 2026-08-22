import { Routes } from '@angular/router';

//COMPONENTES
import { LoginComponent } from './pages/login/login';
import { ListaUsuariosComponent } from './pages/usuarios/lista-usuarios/lista-usuarios';
import { HomeComponent } from './pages/home/home';
import { PerfilComponent } from './pages/perfil/perfil';
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
    //RUTAS PUBLICAS
    { path: '', component: HomeComponent },
    { path: 'login', component: LoginComponent, canActivate: [publicGuard] },

    //RUTAS SIN SIDEBAR
    { path: 'home', redirectTo: '', pathMatch: 'full' },
    { path: 'perfil', component: PerfilComponent, canActivate: [authGuard] },

    //RUTAS CONSIDEBAR
    {
        path: '',
        component: AdminLayoutComponent,
        canActivate: [authGuard],
        children: [
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