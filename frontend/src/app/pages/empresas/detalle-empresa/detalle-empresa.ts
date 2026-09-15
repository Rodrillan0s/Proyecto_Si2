import { Component, OnInit, inject, PLATFORM_ID, ChangeDetectorRef, NgZone, DestroyRef } from '@angular/core';
import { CommonModule, isPlatformBrowser } from '@angular/common';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { environment } from '../../../../environments/environment';

import { AuthService } from '../../../services/auth';
import { EmpresaService, Empresa } from '../../../services/empresa';
import { ProyectosService, Proyecto } from '../../../services/proyectos';
import { MaterialsService, Material } from '../../../services/materials.service';
import { ProveedorService, Proveedor } from '../../../services/proveedor.service';

import { DashboardCardComponent } from '../../../components/ui/dashboard-card';
import { StatusBadgeComponent } from '../../../components/ui/status-badge';
import { PageHeaderComponent } from '../../../components/ui/page-header';
import { EmptyStateComponent } from '../../../components/ui/empty-state';

@Component({
  selector: 'app-detalle-empresa',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    DashboardCardComponent,
    StatusBadgeComponent,
    PageHeaderComponent,
    EmptyStateComponent
  ],
  templateUrl: './detalle-empresa.html',
  styleUrl: './detalle-empresa.css'
})
export class DetalleEmpresaComponent implements OnInit {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private authService = inject(AuthService);
  private empresaService = inject(EmpresaService);
  private proyectosService = inject(ProyectosService);
  private materialsService = inject(MaterialsService);
  private proveedorService = inject(ProveedorService);
  private http = inject(HttpClient);
  private platformId = inject(PLATFORM_ID);
  private cdr = inject(ChangeDetectorRef);
  private ngZone = inject(NgZone);
  private destroyRef = inject(DestroyRef);

  idEmpresa: number = 0;
  empresa: Empresa | null = null;
  cargando: boolean = true;
  tabActiva: 'resumen' | 'obras' | 'usuarios' | 'materiales' | 'proveedores' = 'resumen';

  // Datos del Tenant
  obras: Proyecto[] = [];
  usuarios: any[] = [];
  materiales: Material[] = [];
  proveedores: Proveedor[] = [];

  // Conteo
  totalObras = 0;
  obrasActivas = 0;
  totalUsuarios = 0;
  totalMateriales = 0;
  totalProveedores = 0;

  ngOnInit() {
    if (!isPlatformBrowser(this.platformId)) return;

    this.route.paramMap
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(params => {
        const idParam = params.get('id');
        if (idParam) {
          this.idEmpresa = +idParam;
          this.cargarEmpresaYDatos();
        }
      });
  }

  hasPermission(permiso: string): boolean {
    return this.authService.hasPermission(permiso);
  }

  cargarEmpresaYDatos() {
    this.cargando = true;
    this.empresaService.listarEmpresas().subscribe({
      next: (res) => {
        this.ngZone.run(() => {
          if (res.success && res.data) {
            this.empresa = res.data.find(e => e.id_empresa === this.idEmpresa) || null;
            if (this.empresa) {
              // Establecer en contexto de sesión
              this.authService.seleccionarEmpresa(this.empresa);
            }
          }
          this.cargarSubmodulos();
        });
      },
      error: () => {
        this.ngZone.run(() => {
          this.cargando = false;
          this.cdr.detectChanges();
        });
      }
    });
  }

  cargarSubmodulos() {
    // 1. Obras del tenant
    this.proyectosService.listarProyectos().subscribe({
      next: (res) => {
        this.ngZone.run(() => {
          if (res && res.data) {
            // Filtrar por esta empresa si es administrador
            this.obras = res.data.filter(o => o.id_empresa === this.idEmpresa || !o.id_empresa);
            this.totalObras = this.obras.length;
            this.obrasActivas = this.obras.filter(o => o.estado_obra === 'ACTIVO').length;
          }
          this.cdr.detectChanges();
        });
      }
    });

    // 2. Usuarios del tenant
    const token = this.authService.obtenerToken();
    this.http.get<any>(`${environment.apiUrl}/api/usuarios/`, {
      headers: { Authorization: `Bearer ${token}` }
    }).subscribe({
      next: (res) => {
        this.ngZone.run(() => {
          if (res && res.success && Array.isArray(res.data)) {
            this.usuarios = res.data.filter((u: any) => u.id_empresa === this.idEmpresa);
            this.totalUsuarios = this.usuarios.length;
          }
          this.cdr.detectChanges();
        });
      }
    });

    // 3. Materiales
    this.materialsService.listar({ limit: 10 }).subscribe({
      next: (res) => {
        this.ngZone.run(() => {
          if (res && res.data) {
            this.materiales = res.data;
            this.totalMateriales = res.pagination?.total || res.data.length;
          }
          this.cdr.detectChanges();
        });
      }
    });

    // 4. Proveedores
    this.proveedorService.listar({ limit: 10 }).subscribe({
      next: (res) => {
        this.ngZone.run(() => {
          if (res && res.data) {
            this.proveedores = res.data;
            this.totalProveedores = res.pagination?.total || res.data.length;
          }
          this.cargando = false;
          this.cdr.detectChanges();
        });
      },
      error: () => {
        this.ngZone.run(() => {
          this.cargando = false;
          this.cdr.detectChanges();
        });
      }
    });
  }

  cambiarTab(tab: 'resumen' | 'obras' | 'usuarios' | 'materiales' | 'proveedores') {
    this.tabActiva = tab;
  }

  volverAEmpresas() {
    this.authService.limpiarEmpresaSeleccionada();
    this.router.navigate(['/empresas']);
  }

  irA(ruta: string, params?: any) {
    if (params) {
      this.router.navigate([ruta], { queryParams: params });
    } else {
      this.router.navigate([ruta]);
    }
  }

  verObra(id?: number) {
    if (id) {
      this.router.navigate([`/proyectos/${id}`]);
    }
  }
}
