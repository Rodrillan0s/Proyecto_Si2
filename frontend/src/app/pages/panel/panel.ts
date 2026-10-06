import { LecturasVigentes } from '../../services/lecturas';
import { ContextoOperativo } from '../../services/contexto-operativo';
import { Incidencia, IncidenciasService } from '../../services/incidencias';
import { Component, OnInit, inject, PLATFORM_ID, ChangeDetectorRef, NgZone, DestroyRef } from '@angular/core';
import { CommonModule, isPlatformBrowser } from '@angular/common';
import { Router, ActivatedRoute, RouterModule } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { environment } from '../../../environments/environment';

import { AuthService } from '../../services/auth';
import { ProyectosService, Proyecto } from '../../services/proyectos';
import { MaterialsService, Material } from '../../services/materials.service';
import { ProveedorService } from '../../services/proveedor.service';
import { EmpresaService, Empresa } from '../../services/empresa';
import { BitacoraService, RegistroBitacora } from '../../services/bitacora.service';

import { DashboardCardComponent } from '../../components/ui/dashboard-card';
import { StatusBadgeComponent } from '../../components/ui/status-badge';
import { PageHeaderComponent } from '../../components/ui/page-header';
import { EmptyStateComponent } from '../../components/ui/empty-state';

@Component({
  selector: 'app-panel',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    DashboardCardComponent,
    StatusBadgeComponent,
    PageHeaderComponent,
    EmptyStateComponent
  ],
  templateUrl: './panel.html',
  styleUrl: './panel.css'
})
export class PanelComponent implements OnInit {
  resourceErrors: Record<string, string> = {};
  get errorCarga() { return Object.values(this.resourceErrors).join(' '); }
  get nombreEmpresaActual() { return this.authService.obtenerNombreEmpresaActiva(); }
  private contexto = inject(ContextoOperativo);
  
  private authService = inject(AuthService);
  private proyectosService = inject(ProyectosService);
  private materialsService = inject(MaterialsService);
  private proveedorService = inject(ProveedorService);
  private empresaService = inject(EmpresaService);
  private bitacoraService = inject(BitacoraService);
  private http = inject(HttpClient);
  private router = inject(Router);
  private route = inject(ActivatedRoute);
  private platformId = inject(PLATFORM_ID);
  private cdr = inject(ChangeDetectorRef);
  private ngZone = inject(NgZone);
  private destroyRef = inject(DestroyRef);
  private reads = new LecturasVigentes(this.destroyRef);

  incidenciasAsignadas: Incidencia[] = [];
  paginaIncidencias = 1;
  totalPaginasIncidencias = 0;
  cargandoIncidencias = false;
  errorIncidencias = '';
  private incidenciasService = inject(IncidenciasService);

  cargarIncidenciasAsignadas(page = 1): void {
    this.cargandoIncidencias = true;
    this.errorIncidencias = '';
    this.incidenciasService.listar({id_responsable: Number(this.usuarioActual.nro_usuario), page, limit: 20})
      .pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
        next: res => {
          this.incidenciasAsignadas = res.data;
          this.paginaIncidencias = page;
          this.totalPaginasIncidencias = res.pagination.total_pages;
          this.cargandoIncidencias = false;
          this.cdr.markForCheck();
        },
        error: () => {
          this.errorIncidencias = 'No se pudieron cargar las incidencias asignadas.';
          this.cargandoIncidencias = false;
          this.cdr.markForCheck();
        }
      });
  }

  usuarioActual: any = null;
  rolUsuario: string = '';
  modoOscuro: boolean = false;
  vistaActiva: string = 'resumen';

  // Obras / Proyectos
  proyectos: Proyecto[] = [];
  cargandoProyectos: boolean = false;
  totalProyectos = 0;
  proyectosActivos = 0;
  proyectosPlanificacion = 0;
  proyectosFinalizados = 0;

  // Materiales / Inventario
  materiales: Material[] = [];
  totalMateriales = 0;
  materialesStockBajo = 0;
  cargandoMateriales: boolean = false;

  // Proveedores
  totalProveedores = 0;

  // Empresas (Para Administrador)
  empresas: Empresa[] = [];
  totalEmpresas = 0;
  empresasActivas = 0;
  cargandoEmpresas: boolean = false;

  // Bitácora / Auditoría (Para Administrador)
  eventosBitacora: RegistroBitacora[] = [];
  totalEventosBitacora = 0;
  cargandoBitacora: boolean = false;

  // Usuarios globales
  totalUsuarios = 0;

  // Sesión y Dispositivos
  dispositivosConocidos: any[] = [];

  // Multi-tenant & Empresa Activa
  empresaActiva: any = null;
  obrasFiltradasPorEmpresa: Proyecto[] = [];
  obrasActivasEmpresa: number = 0;
  materialesFiltradosPorEmpresa: Material[] = [];
  materialesStockBajoEmpresa: number = 0;

  ngOnInit() {
    if (!isPlatformBrowser(this.platformId)) return;

    this.usuarioActual = this.authService.obtenerUsuario();
    
    if (!this.usuarioActual || this.authService.tokenExpirado()) {
      this.authService.cerrarSesion();
      this.router.navigate(['/login']);
      return;
    }

    this.rolUsuario = this.authService.obtenerRolNormalizado();
    if (['ELECTRICO', 'PLOMERO', 'MAESTRO_ALBANIL', 'ALBANIL'].includes(this.rolUsuario)) {
      this.cargarIncidenciasAsignadas();
    }

    // Escuchar empresa activa reactiva
    this.contexto.empresa$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((empresa) => {
        this.ngZone.run(() => {
          this.resourceErrors = {}; this.materiales = []; this.totalMateriales = 0; this.totalProveedores = 0;
          this.empresaActiva = this.authService.obtenerEmpresaActiva();
          this.filtrarDatosEmpresaActiva();
          if (this.hasPermission('Visualizar_materiales') || this.hasPermission('Visualizar_inventario')) {
            this.cargarMateriales();
          }
          if (this.hasPermission('Visualizar_proveedores')) {
            this.cargarProveedores();
          }
          this.cdr.detectChanges();
        });
      });

    // Escuchar query params para cambiar de pestaña si aplica (ej. seguridad)
    this.route.queryParams
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(params => {
        this.ngZone.run(() => {
          this.vistaActiva = params['tab'] || 'resumen';
          this.cdr.detectChanges();
        });
      });

    // Cargar datos según permisos pertinentes
    this.cargarDatosPorRol();

    // Información de sesión
    this.cargarInfoDispositivo();

    // Tema
    if (localStorage.getItem('tema_sistema') === 'dark') {
      this.modoOscuro = true;
      document.documentElement.classList.add('dark');
    }
  }

  hasPermission(permiso: string): boolean {
    return this.authService.hasPermission(permiso);
  }

  cargarDatosPorRol() {
    // 1. Obras (si tiene Visualizar_obras)
    if (this.hasPermission('Visualizar_obras')) {
      this.cargarObras();
    }

    // 4. Empresas (si tiene Visualizar_empresa)
    if (this.hasPermission('Visualizar_empresa')) {
      this.cargarEmpresas();
    }

    // 5. Bitácora / Usuarios (si tiene Visualizar_usuarios)
    if (this.hasPermission('Visualizar_usuarios')) {
      this.cargarUsuariosConteo();
      if (this.rolUsuario === 'ADMINISTRADOR') {
        this.cargarBitacora();
      }
    }
  }

  cargarObras() {
    delete this.resourceErrors['obras'];
    this.cargandoProyectos = true;
    this.proyectosService.listarProyectos().pipe(this.reads.reemplazar('obras')).subscribe({
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
          this.filtrarDatosEmpresaActiva();
          this.cdr.detectChanges();
        });
      },
      error: () => {
        this.resourceErrors['obras'] = 'No se pudieron consultar las obras.';
        this.ngZone.run(() => {
          this.cargandoProyectos = false;
          this.filtrarDatosEmpresaActiva();
          this.cdr.detectChanges();
        });
      }
    });
  }

  cargarMateriales() {
    delete this.resourceErrors['materiales'];
    this.cargandoMateriales = true;
    const idEmpresa = this.empresaActiva?.id_empresa ? Number(this.empresaActiva.id_empresa) : undefined;
    this.materialsService.listar({ limit: 8, id_empresa: idEmpresa }).pipe(this.reads.reemplazar('materiales')).subscribe({
      next: (res) => {
        this.ngZone.run(() => {
          if (res && res.data) {
            this.materiales = res.data;
            this.totalMateriales = res.pagination?.total || res.data.length;
            this.materialesStockBajo = this.materiales.filter(m => (m.stock_actual || 0) <= (m.stock_minimo || 0)).length;
          }
          this.cargandoMateriales = false;
          this.filtrarDatosEmpresaActiva();
          this.cdr.detectChanges();
        });
      },
      error: () => {
        this.resourceErrors['materiales'] = 'No se pudieron consultar los materiales.';
        this.ngZone.run(() => {
          this.cargandoMateriales = false;
          this.filtrarDatosEmpresaActiva();
          this.cdr.detectChanges();
        });
      }
    });
  }

  cargarProveedores() {
    delete this.resourceErrors['proveedores'];
    const idEmpresa = this.empresaActiva?.id_empresa ? Number(this.empresaActiva.id_empresa) : undefined;
    this.proveedorService.listar({ limit: 1, id_empresa: idEmpresa }).pipe(this.reads.reemplazar('proveedores')).subscribe({
      next: (res) => {
        this.ngZone.run(() => {
          if (res && res.pagination) {
            this.totalProveedores = res.pagination.total || 0;
          }
          this.cdr.detectChanges();
        });
      },
      error: () => {
        this.resourceErrors['proveedores'] = 'No se pudieron consultar los proveedores.';}
    });
  }

  cargarEmpresas() {
    this.cargandoEmpresas = true;
    this.empresaService.listarEmpresas().pipe(this.reads.reemplazar('empresas')).subscribe({
      next: (res) => {
        this.ngZone.run(() => {
          if (res && res.success) {
            this.empresas = res.data || [];
            this.totalEmpresas = this.empresas.length;
            this.empresasActivas = this.empresas.filter(e => e.estado === 'ACTIVO').length;
          }
          this.cargandoEmpresas = false;
          this.cdr.detectChanges();
        });
      },
      error: () => {
        this.ngZone.run(() => {
          this.cargandoEmpresas = false;
          this.cdr.detectChanges();
        });
      }
    });
  }

  cargarBitacora() {
    this.cargandoBitacora = true;
    this.bitacoraService.obtenerBitacora({ limit: 6 }).pipe(this.reads.reemplazar('bitacora')).subscribe({
      next: (res) => {
        this.ngZone.run(() => {
          if (res && res.success) {
            this.eventosBitacora = res.data || [];
            this.totalEventosBitacora = res.pagination?.total || 0;
          }
          this.cargandoBitacora = false;
          this.cdr.detectChanges();
        });
      },
      error: () => {
        this.ngZone.run(() => {
          this.cargandoBitacora = false;
          this.cdr.detectChanges();
        });
      }
    });
  }

  cargarUsuariosConteo() {
    const token = this.authService.obtenerToken();
    this.http.get<any>(`${environment.apiUrl}/api/usuarios/`, {
      headers: { Authorization: `Bearer ${token}` }
    }).pipe(this.reads.reemplazar('usuarios')).subscribe({
      next: (res) => {
        this.ngZone.run(() => {
          if (res && res.success && Array.isArray(res.data)) {
            this.totalUsuarios = res.data.length;
          }
          this.cdr.detectChanges();
        });
      },
      error: () => {}
    });
  }

  cargarInfoDispositivo() {
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
  }

  navegarA(ruta: string, param?: any) {
    if (param) {
      this.router.navigate([ruta], { queryParams: param });
    } else {
      this.router.navigate([ruta]);
    }
  }

  verProyecto(id?: number) {
    if (id) {
      this.router.navigate([`/proyectos/${id}`]);
    }
  }

  filtrarDatosEmpresaActiva() {
    if (this.empresaActiva) {
      const id = Number(this.empresaActiva.id_empresa);
      this.obrasFiltradasPorEmpresa = this.proyectos.filter(p => p.id_empresa === id || !p.id_empresa);
      this.obrasActivasEmpresa = this.obrasFiltradasPorEmpresa.filter(p => p.estado_obra === 'ACTIVO').length;
      this.materialesFiltradosPorEmpresa = this.materiales.filter(m => m.id_empresa === id || !m.id_empresa);
      this.materialesStockBajoEmpresa = this.materialesFiltradosPorEmpresa.filter(m => (m.stock_actual || 0) <= (m.stock_minimo || 0)).length;
    } else {
      this.obrasFiltradasPorEmpresa = [...this.proyectos];
      this.obrasActivasEmpresa = this.proyectosActivos;
      this.materialesFiltradosPorEmpresa = [...this.materiales];
      this.materialesStockBajoEmpresa = this.materialesStockBajo;
    }
  }

  esVistaGlobal(): boolean {
    return this.authService.esVistaGlobal();
  }

  activarEmpresa(emp: any) {
    this.authService.seleccionarEmpresaActiva(emp);
  }

  volverAVistaGlobal() {
    this.authService.seleccionarEmpresaActiva(null);
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