import { NAVIGATION, NavItem, NavSection, REPORT_FAMILIES } from './navegacion';
import { ContextoOperativo } from '../../services/contexto-operativo';
import { ProyectosService, Proyecto } from '../../services/proyectos';
import { ReportesService } from '../../services/reportes.service';
import { filter, firstValueFrom } from 'rxjs';
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
import { Router, RouterOutlet, RouterModule, NavigationEnd } from '@angular/router';
import { AuthService } from '../../services/auth';
import { NotificacionesService, Notificacion } from '../../services/notificaciones';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';

import { FormsModule } from '@angular/forms';
import { EmpresaService } from '../../services/empresa';
import { AsistenteComponent } from '../../components/asistente/asistente';
import { AsistenteService, ASSISTANT_PERMISSIONS } from '../../services/asistente.service';

@Component({
  selector: 'app-admin-layout',
  standalone: true,
  imports: [CommonModule, RouterOutlet, RouterModule, FormsModule, AsistenteComponent],
  templateUrl: './admin-layout.html',
  styleUrl: './admin-layout.css'
})
export class AdminLayoutComponent implements OnInit {
  readonly assistantPermissions = ASSISTANT_PERMISSIONS;
  readonly contexto = inject(ContextoOperativo);
  private proyectos = inject(ProyectosService);
  private reportes = inject(ReportesService);
  obras: Proyecto[] = [];
  cargandoObras = false;
  errorObras = '';
  mostrarSelectorObras = false;
  private workVersion = 0;
  private reportIds: string[] | undefined;
  private reportVersion = 0;
  currentUrl = '';
  expanded = new Set(['principal', 'proyectos']);
  get nombreEmpresa() { return this.authService.obtenerNombreEmpresaActiva(); }
  get sections() { return NAVIGATION.map(section => ({ ...section, items: section.items.filter(item =>
    (!item.global || this.esAdministradorGlobal()) && (!item.permissions || this.hasAnyPermission(item.permissions)) &&
    (!item.all || this.authService.hasAllPermissions(item.all)) &&
    (!item.family || this.reportIds === undefined || REPORT_FAMILIES[item.family].some(id => this.reportIds!.includes(id)))
  ) })).filter(section => section.items.length); }
  trackSection(_index: number, section: NavSection) { return section.id; }
  trackItem(_index: number, item: NavItem) { return item.id; }
  toggleSection(section: NavSection) { this.expanded.has(section.id) ? this.expanded.delete(section.id) : this.expanded.add(section.id); if (section.id === 'reportes' && this.expanded.has('reportes')) void this.cargarFamilias(); }
  itemRoute(item: NavItem) { return item.context && this.contexto.obra ? '/proyectos/'+this.contexto.obra.id_obra : item.route; }
  itemQuery(item: NavItem) { return item.context ? (this.contexto.obra ? (item.context === 'estructura' ? { tab: 'estructura' } : {}) : { accion: item.context, tab: 'gestion' }) : (item.query || {}); }
  itemFragment(item: NavItem) { return item.context === 'responsables' && this.contexto.obra ? 'responsables-obra' : undefined; }
  itemActive(item: NavItem) {
    const url = this.router.parseUrl(this.currentUrl || this.router.url);
    const path = '/'+(url.root.children['primary']?.segments.map(segment => segment.path).join('/') || '');
    if (item.context) return (path === this.itemRoute(item) && (url.queryParams['accion'] === item.context || (item.context === 'estructura' ? url.queryParams['tab'] === 'estructura' : url.fragment === 'responsables-obra')));
    return path === item.route && Object.entries(item.query || {}).every(([key,value]) => url.queryParams[key] === value) &&
      (item.id !== 'obras' || (!url.queryParams['tab'] && !url.queryParams['accion'])) && (item.id !== 'panel' || !url.queryParams['tab']);
  }
  sectionActive(section: NavSection) { return section.items.some(item => this.itemActive(item)) || (section.id === 'reportes' && this.currentUrl.split('?')[0] === '/reportes'); }
  get moduloActual() { return this.sections.flatMap(section => section.items).find(item => this.itemActive(item))?.label || (this.currentUrl.startsWith('/proyectos/') ? 'Detalle de obra' : this.currentUrl.startsWith('/reportes') ? 'Reportes' : 'Panel'); }
  private updateNavigation() { this.currentUrl = this.router.url; this.sections.filter(section => this.sectionActive(section)).forEach(section => this.expanded.add(section.id)); this.sidebarAbierto = false; if (this.currentUrl.startsWith('/reportes') && this.reportIds === undefined) void this.cargarFamilias(); }
  toggleSelectorObras() { this.mostrarSelectorObras = !this.mostrarSelectorObras; if (this.mostrarSelectorObras) void this.cargarObrasSelector(); }
  async cargarObrasSelector() {
    const version = ++this.workVersion; this.cargandoObras = true; this.errorObras = '';
    try {
      const result = await firstValueFrom(this.proyectos.listarProyectos());
      if (version !== this.workVersion) return;
      const company = this.authService.obtenerIdEmpresaActiva();
      this.obras = (result.data || []).filter(work => !company || Number(work.id_empresa) === company);
    } catch { if (version === this.workVersion) this.errorObras = 'No se pudieron cargar las obras.'; }
    finally { if (version === this.workVersion) { this.cargandoObras = false; this.cdr.markForCheck(); } }
  }
  seleccionarObra(id: string) {
    if (!this.contexto.confirmarCambio()) return;
    this.contexto.seleccionar(this.obras.find(work => work.id_obra === Number(id)) || null);
    this.mostrarSelectorObras = false;
    if (/^\/proyectos\/\d+/.test(this.router.url) && this.contexto.obra) void this.router.navigate(['/proyectos', this.contexto.obra.id_obra]);
    this.cdr.markForCheck();
  }
  private async cargarFamilias() {
    if (!this.hasPermission('Visualizar_reportes')) return;
    const company = this.authService.obtenerIdEmpresaActiva(); const version = ++this.reportVersion;
    this.reportIds = undefined;
    if (!company && this.esAdministradorGlobal()) return;
    try { const catalog = await this.reportes.catalog(company); if (version === this.reportVersion) this.reportIds = catalog.reportes.map(report => report.id); }
    catch { /* Un error de catálogo no modifica los permisos ni bloquea navegación. */ }
    this.cdr.markForCheck();
  }


  private authService           = inject(AuthService);
  private notificacionesService  = inject(NotificacionesService);
  private empresaService        = inject(EmpresaService);
  private router                = inject(Router);
  private platformId            = inject(PLATFORM_ID);
  private cdr                   = inject(ChangeDetectorRef);
  private ngZone                = inject(NgZone);
  private destroyRef            = inject(DestroyRef);
  private asistente             = inject(AsistenteService);
  consultaAsistente = '';

  // ---- Estado general ----
  usuarioActual: any      = null;
  modoOscuro: boolean     = false;
  sidebarAbierto: boolean   = false;
  sidebarColapsado: boolean = false;
  empresaSeleccionada: any  = null;

  // ---- Selector de Empresa Activa ----
  mostrarSelectorEmpresas: boolean = false;
  listaEmpresas: any[] = [];
  empresasFiltradasSelector: any[] = [];
  busquedaEmpresa: string = '';

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

    this.authService.obtenerEmpresaSeleccionada();
    this.empresaSeleccionada = this.authService.obtenerEmpresaActiva();
    this.updateNavigation();
    this.router.events.pipe(filter(event => event instanceof NavigationEnd), takeUntilDestroyed(this.destroyRef)).subscribe(() => { this.updateNavigation(); this.cdr.markForCheck(); });
    let initialCompany = true;
    this.contexto.empresa$.pipe(takeUntilDestroyed(this.destroyRef)).subscribe(() => {
      this.workVersion++; this.obras = []; this.cargandoObras = false; this.mostrarSelectorObras = false;
      this.reportVersion++; this.reportIds = undefined;
      if (this.expanded.has('reportes')) void this.cargarFamilias();
      if (!initialCompany && /^\/proyectos\/\d+/.test(this.router.url)) void this.router.navigate(['/proyectos']);
      initialCompany = false;
    });
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

    // Suscribirse a la empresa seleccionada en el contexto de sesión
    this.authService.empresaSeleccionada$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((empresa) => {
        this.ngZone.run(() => {
          this.empresaSeleccionada = empresa;
          this.cdr.detectChanges();
        });
      });
  }

  menuObrasAbierto: boolean = true;
  menuConfiguracionAbierto: boolean = false;

  hasPermission(permiso: string): boolean {
    return this.authService.hasPermission(permiso);
  }

  hasAnyPermission(permisos: string[]): boolean {
    return this.authService.hasAnyPermission(permisos);
  }

  toggleSubmenuObras() {
    this.menuObrasAbierto = !this.menuObrasAbierto;
  }

  esAdministradorGlobal(): boolean {
    return this.authService.obtenerRolNormalizado() === 'ADMINISTRADOR';
  }

  limpiarEmpresaContexto() {
    this.authService.limpiarEmpresaSeleccionada();
  }

  irAEmpresaActual() {
    if (this.empresaSeleccionada) {
      this.router.navigate(['/empresas', this.empresaSeleccionada.id_empresa]);
    }
  }

  irAEmpresaOLista() {
    if (this.esAdministradorGlobal()) {
      this.navegarA('/empresas');
    } else if (this.usuarioActual?.id_empresa) {
      this.navegarA(`/empresas/${this.usuarioActual.id_empresa}`);
    } else {
      this.navegarA('/empresas');
    }
  }

  // ------------------------------------------------------------------
  // GESTION DE SELECTOR DE EMPRESA ACTIVA (MULTI-TENANT)
  // ------------------------------------------------------------------

  toggleSelectorEmpresas() {
    this.mostrarSelectorEmpresas = !this.mostrarSelectorEmpresas;
    if (this.mostrarSelectorEmpresas && this.listaEmpresas.length === 0) {
      this.cargarEmpresasParaSelector();
    }
  }

  cargarEmpresasParaSelector() {
    this.empresaService.listarEmpresas().subscribe({
      next: (res) => {
        this.ngZone.run(() => {
          if (res && res.data) {
            this.listaEmpresas = res.data;
            this.filtrarEmpresasSelector();
            this.cdr.detectChanges();
          }
        });
      },
      error: () => {}
    });
  }

  filtrarEmpresasSelector() {
    const q = (this.busquedaEmpresa || '').toLowerCase().trim();
    if (!q) {
      this.empresasFiltradasSelector = [...this.listaEmpresas];
    } else {
      this.empresasFiltradasSelector = this.listaEmpresas.filter(e => 
        (e.nombre_empresa && e.nombre_empresa.toLowerCase().includes(q)) ||
        (e.nit && e.nit.toLowerCase().includes(q))
      );
    }
  }

  seleccionarEmpresa(empresa: any | null) {
    if (!this.contexto.confirmarCambio()) return;
    this.authService.seleccionarEmpresaActiva(empresa);
    this.mostrarSelectorEmpresas = false;
    this.cdr.detectChanges();
  }

  @HostListener('document:click', ['$event'])
  onDocumentClick(event: MouseEvent) {
    const target = event.target as HTMLElement;
    if (this.mostrarSelectorObras && !target.closest('[data-work-selector]')) this.mostrarSelectorObras = false;
    if (this.mostrarSelectorEmpresas && !target.closest('[data-company-selector]')) {
      this.mostrarSelectorEmpresas = false;
      this.cdr.detectChanges();
    }
    if (this.mostrarNotificaciones && !target.closest('[data-notif-panel]')) {
      this.mostrarNotificaciones = false;
      this.cdr.detectChanges();
    }
  }

  // Compatibilidad hacia atrás
  esAdministrador(): boolean {
    return this.hasPermission('Visualizar_usuarios');
  }

  esAdministradorSistema(): boolean {
    return this.esAdministradorGlobal();
  }

  puedeVerProyectos(): boolean {
    return this.hasPermission('Visualizar_obras');
  }

  // ------------------------------------------------------------------
  // SIDEBAR & NAVEGACION
  // ------------------------------------------------------------------

  toggleSidebar() {
    if (isPlatformBrowser(this.platformId) && window.matchMedia('(max-width: 850px)').matches) {
      this.sidebarColapsado = false;
      this.sidebarAbierto = !this.sidebarAbierto;
    } else this.sidebarColapsado = !this.sidebarColapsado;
    this.cdr.detectChanges();
  }

  abrirConsultaAsistente() {
    this.asistente.quick(this.consultaAsistente.trim());
    this.consultaAsistente = '';
  }

  navegarA(ruta: string, tab?: string) {
    this.ngZone.run(() => {
      this.sidebarAbierto = false;
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
