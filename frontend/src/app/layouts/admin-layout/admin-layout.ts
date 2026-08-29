import {
  Component,
  OnInit,
  inject,
  PLATFORM_ID,
  HostListener,
  ChangeDetectorRef,
  NgZone,
  DestroyRef
} from '@angular/core';
import { CommonModule, isPlatformBrowser } from '@angular/common';
import { Router, RouterOutlet, RouterModule } from '@angular/router';
import { AuthService } from '../../services/auth';
import { NotificacionesService, Notificacion } from '../../services/notificaciones';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';

@Component({
  selector: 'app-admin-layout',
  standalone: true,
  imports: [CommonModule, RouterOutlet, RouterModule],
  templateUrl: './admin-layout.html',
  styleUrl: './admin-layout.css'
})
export class AdminLayoutComponent implements OnInit {

  private authService           = inject(AuthService);
  private notificacionesService  = inject(NotificacionesService);
  private router                = inject(Router);
  private platformId            = inject(PLATFORM_ID);
  private cdr                   = inject(ChangeDetectorRef);
  private ngZone                = inject(NgZone);
  private destroyRef            = inject(DestroyRef);

  // ---- Estado general ----
  usuarioActual: any      = null;
  modoOscuro: boolean     = false;
  sidebarAbierto: boolean   = false;
  sidebarColapsado: boolean = false;

  // ---- Estado notificaciones ----
  mostrarNotificaciones: boolean = false;
  listaNotificaciones: Notificacion[] = [];
  cantidadNoLeidas: number = 0;

  ngOnInit() {
    if (!isPlatformBrowser(this.platformId)) return;

    this.usuarioActual = this.authService.obtenerUsuario();

    if (!this.usuarioActual) {
      this.cerrarSesion();
      return;
    }

    // Restaurar tema guardado
    if (localStorage.getItem('tema_sistema') === 'dark') {
      this.modoOscuro = true;
      document.documentElement.classList.add('dark');
    }

    // Iniciar WS + cargar historial desde BD
    this.notificacionesService.conectar();

    // Suscribirse al stream reactivo (mezcla BD + WS en tiempo real)
    this.notificacionesService.notificaciones$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((notis) => {
        this.ngZone.run(() => {
          this.listaNotificaciones = notis;
          this.cantidadNoLeidas   = notis.filter(n => !n.leida).length;
          this.cdr.detectChanges();
        });
      });
  }

  esAdministrador(): boolean {
    return ['ADMINISTRADOR', 'ADMINISTRADOR_EMPRESA'].includes(this.usuarioActual?.nombre_rol);
  }

  esAdministradorSistema(): boolean {
    return this.usuarioActual?.nombre_rol === 'ADMINISTRADOR';
  }

  puedeVerProyectos(): boolean {
    return ['ADMINISTRADOR', 'ADMINISTRADOR_EMPRESA', 'JEFE DE OBRA'].includes(this.usuarioActual?.nombre_rol);
  }

  // ------------------------------------------------------------------
  // SIDEBAR & NAVEGACION
  // ------------------------------------------------------------------

  toggleSidebar() {
    this.sidebarColapsado = !this.sidebarColapsado;
    this.cdr.detectChanges();
  }

  navegarA(ruta: string, tab?: string) {
    this.ngZone.run(() => {
      if (tab) {
        this.router.navigate([ruta], { queryParams: { tab } });
      } else {
        this.router.navigate([ruta]);
      }
      this.cdr.detectChanges();
    });
  }

  // ------------------------------------------------------------------
  // TEMA
  // ------------------------------------------------------------------

  alternarModoOscuro() {
    if (!isPlatformBrowser(this.platformId)) return;

    this.modoOscuro = !this.modoOscuro;
    if (this.modoOscuro) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('tema_sistema', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('tema_sistema', 'light');
    }
    this.cdr.detectChanges();
  }

  // ------------------------------------------------------------------
  // NOTIFICACIONES
  // ------------------------------------------------------------------

  toggleNotificaciones() {
    this.mostrarNotificaciones = !this.mostrarNotificaciones;

    if (this.mostrarNotificaciones && this.cantidadNoLeidas > 0) {
      this.notificacionesService.marcarComoLeidas();
      this.cantidadNoLeidas = 0;
      this.cdr.detectChanges();
    }
  }

  marcarTodasLeidas() {
    this.notificacionesService.marcarComoLeidas();
    this.cantidadNoLeidas = 0;
    this.cdr.detectChanges();
  }

  leerNotificacion(noti: Notificacion) {
    if (!noti.leida && noti.id_notificacion) {
      this.notificacionesService.marcarUnaComoLeida(noti.id_notificacion);
    }
  }

  irANotificaciones() {
    this.mostrarNotificaciones = false;
    this.router.navigate(['/notificaciones']);
  }

  // ------------------------------------------------------------------
  // HELPERS DE ICONOS
  // ------------------------------------------------------------------

  getIconoClase(tipo: string): string {
    const clases: Record<string, string> = {
      'NUEVA_EMERGENCIA': 'bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 border-red-100 dark:border-red-800/30',
      'NUEVA_OFERTA':     'bg-amber-50 dark:bg-amber-900/20 text-amber-600 dark:text-amber-400 border-amber-100 dark:border-amber-800/30',
      'RESPUESTA_OFERTA': 'bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400 border-green-100 dark:border-green-800/30',
      'EMERGENCIA': 'bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 border-red-100 dark:border-red-800/30',
      'ALERTA':     'bg-amber-50 dark:bg-amber-900/20 text-amber-600 dark:text-amber-400 border-amber-100 dark:border-amber-800/30',
      'INFO':       'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 border-blue-100 dark:border-blue-800/30',
      'EXITO':      'bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400 border-green-100 dark:border-green-800/30',
    };
    return clases[tipo] ?? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 border-blue-100 dark:border-blue-800/30';
  }

  getIconoPath(tipo: string): string {
    const iconos: Record<string, string> = {
      'NUEVA_EMERGENCIA': 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z',
      'NUEVA_OFERTA':     'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4',
      'RESPUESTA_OFERTA': 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
      'EMERGENCIA': 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z',
      'ALERTA':     'M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
      'INFO':       'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
      'EXITO':      'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
    };
    return iconos[tipo] ?? 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z';
  }

  // ------------------------------------------------------------------
  // SESION
  // ------------------------------------------------------------------

  cerrarSesion() {
    this.notificacionesService.desconectar();
    this.authService.cerrarSesion();
    this.router.navigate(['/login']);
  }
}