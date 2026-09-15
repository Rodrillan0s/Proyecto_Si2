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

    // Escuchar empresa activa reactiva
    this.authService.empresaActiva$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((empresa) => {
        this.ngZone.run(() => {
          this.empresaActiva = empresa;
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

    // 2. Materiales e Inventario (si tiene permisos)
    if (this.hasPermission('Visualizar_materiales') || this.hasPermission('Visualizar_inventario')) {
      this.cargarMateriales();
    }

    // 3. Proveedores (si tiene permiso)
    if (this.hasPermission('Visualizar_proveedores')) {
      this.cargarProveedores();
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

  cargarMateriales() {
    this.cargandoMateriales = true;
    const idEmpresa = this.empresaActiva?.id_empresa ? Number(this.empresaActiva.id_empresa) : undefined;
    this.materialsService.listar({ limit: 8, id_empresa: idEmpresa }).subscribe({
      next: (res) => {
        this.ngZone.run(() => {
          if (res && res.data) {
            this.materiales = res.data;
            this.totalMateriales = res.pagination?.total || res.data.length;
            this.materialesStockBajo = this.materiales.filter(m => (m.stock_actual || 0) <= (m.stock_minimo || 0)).length;
          }
          this.cargandoMateriales = false;
          this.cdr.detectChanges();
        });
      },
      error: () => {
        this.ngZone.run(() => {
          this.cargandoMateriales = false;
          this.cdr.detectChanges();
        });
      }
    });
  }

  cargarProveedores() {
    const idEmpresa = this.empresaActiva?.id_empresa ? Number(this.empresaActiva.id_empresa) : undefined;
    this.proveedorService.listar({ limit: 1, id_empresa: idEmpresa }).subscribe({
      next: (res) => {
        this.ngZone.run(() => {
          if (res && res.pagination) {
            this.totalProveedores = res.pagination.total || 0;
          }
          this.cdr.detectChanges();
        });
      },
      error: () => {}
    });
  }

  cargarEmpresas() {
    this.cargandoEmpresas = true;
    this.empresaService.listarEmpresas().subscribe({
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
    this.bitacoraService.obtenerBitacora({ limit: 6 }).subscribe({
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
    }).subscribe({
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