import { Component, OnInit, inject, PLATFORM_ID, ChangeDetectorRef, NgZone } from '@angular/core';
import { CommonModule, isPlatformBrowser } from '@angular/common';
import { Router, ActivatedRoute } from '@angular/router';
import { AuthService } from '../../services/auth';
import { ProyectosService, Proyecto } from '../../services/proyectos';

@Component({
  selector: 'app-panel',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './panel.html',
  styleUrl: './panel.css'
})
export class PanelComponent implements OnInit {
  
  private authService = inject(AuthService);
  private proyectosService = inject(ProyectosService);
  private router = inject(Router);
  private route = inject(ActivatedRoute);
  private platformId = inject(PLATFORM_ID);
  private cdr = inject(ChangeDetectorRef);
  private ngZone = inject(NgZone);

  usuarioActual: any = null;
  modoOscuro: boolean = false;
  
  // Variables del panel
  vistaActiva: string = 'resumen';
  dispositivosConocidos: any[] = [];
  proyectos: Proyecto[] = [];
  cargandoProyectos: boolean = false;

  // KPIs
  totalProyectos = 0;
  proyectosActivos = 0;
  proyectosPlanificacion = 0;
  proyectosFinalizados = 0;

  ngOnInit() {
    if (isPlatformBrowser(this.platformId)) {
      this.usuarioActual = this.authService.obtenerUsuario();
      
      if (!this.usuarioActual || this.authService.tokenExpirado()) {
        this.authService.cerrarSesion();
        this.router.navigate(['/login']);
        return;
      }

      // Escuchar query params para cambiar de pestaña reactivamente
      this.route.queryParams.subscribe(params => {
        this.ngZone.run(() => {
          if (params['tab']) {
            this.vistaActiva = params['tab'];
          } else {
            this.vistaActiva = 'resumen';
          }
          this.cdr.detectChanges();
        });
      });

      // Cargar Proyectos para KPIs del Dashboard
      this.cargarMetricas();

      // Mockup de dispositivo
      const userAgent = navigator.userAgent;
      let browserName = 'Navegador Chrome (Windows)';
      if (userAgent.indexOf('Safari') > -1 && userAgent.indexOf('Chrome') === -1) {
        browserName = 'Navegador Safari (macOS)';
      } else if (userAgent.indexOf('Firefox') > -1) {
        browserName = 'Navegador Firefox (Linux)';
      } else if (userAgent.indexOf('Brave') > -1 || userAgent.indexOf('Chromium') > -1) {
        browserName = 'Navegador Brave/Chromium (Windows)';
      }
      
      this.dispositivosConocidos = [
        {
          hash: 'sha256:8bc57e5e7decf6d0d21051515f45851458e0a3592bc1ff4b98fae85295c52c502f6b',
          navegador: browserName,
          fecha: new Date()
        }
      ];

      // Tema
      if (localStorage.getItem('tema_sistema') === 'dark') {
        this.modoOscuro = true;
        document.documentElement.classList.add('dark');
      }
      this.cdr.detectChanges();
    }
  }

  cargarMetricas() {
    this.cargandoProyectos = true;
    this.proyectosService.listarProyectos().subscribe({
      next: (res) => {
        this.ngZone.run(() => {
          if (res && res.success) {
            this.proyectos = res.data || [];
            this.totalProyectos = this.proyectos.length;
            this.proyectosActivos = this.proyectos.filter(p => p.estado_obra === 'ACTIVO').length;
            this.proyectosPlanificacion = this.proyectos.filter(p => p.estado_obra === 'PLANIFICACION').length;
            this.proyectosFinalizados = this.proyectos.filter(p => p.estado_obra === 'FINALIZADO').length;
          }
          this.cargandoProyectos = false;
          this.cdr.detectChanges();
        });
      },
      error: () => {
        this.ngZone.run(() => {
          this.cargandoProyectos = false;
          this.cdr.detectChanges();
        });
      }
    });
  }

  esAdministrador(): boolean {
    return ['ADMINISTRADOR', 'ADMINISTRADOR_EMPRESA'].includes(this.usuarioActual?.nombre_rol);
  }

  esJefeDeObra(): boolean {
    return this.usuarioActual?.nombre_rol === 'JEFE DE OBRA';
  }

  irAProyectos() {
    this.router.navigate(['/proyectos']);
  }

  verProyecto(id?: number) {
    if (id) {
      this.router.navigate([`/proyectos/${id}`]);
    }
  }

  alternarModoOscuro() {
    this.ngZone.run(() => {
      this.modoOscuro = !this.modoOscuro;
      if (this.modoOscuro) {
        document.documentElement.classList.add('dark');
        localStorage.setItem('tema_sistema', 'dark');
      } else {
        document.documentElement.classList.remove('dark');
        localStorage.setItem('tema_sistema', 'light');
      }
      this.cdr.detectChanges();
    });
  }
}