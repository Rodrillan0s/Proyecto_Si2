import { Component, ChangeDetectorRef, DestroyRef, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { Subject, debounceTime, distinctUntilChanged } from 'rxjs';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';

import { environment } from '../../../environments/environment';
import { AuthService } from '../../services/auth';
import { ProyectosService, Proyecto } from '../../services/proyectos';
import { UnidadesService, UnidadConstruccion } from '../../services/unidades';
import {
  EstadoIncidencia,
  Incidencia,
  IncidenciasService,
  Paginacion,
  PrioridadIncidencia,
} from '../../services/incidencias';

import { PageHeaderComponent } from '../../components/ui/page-header';
import { DashboardCardComponent } from '../../components/ui/dashboard-card';
import { StatusBadgeComponent } from '../../components/ui/status-badge';
import { EmptyStateComponent } from '../../components/ui/empty-state';
import { IncidenciaFormularioComponent } from './formulario/incidencia-formulario';

interface UsuarioFiltro {
  nro_usuario: number;
  nombre_completo: string;
  estado: string;
}

const LIMITE_MAXIMO = 100;

@Component({
  selector: 'app-incidencias',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    PageHeaderComponent,
    DashboardCardComponent,
    StatusBadgeComponent,
    EmptyStateComponent,
    IncidenciaFormularioComponent,
  ],
  templateUrl: './incidencias.html',
  styleUrl: './incidencias.css',
})
export class IncidenciasComponent implements OnInit {
  private incidenciasService = inject(IncidenciasService);
  private proyectosService = inject(ProyectosService);
  private unidadesService = inject(UnidadesService);
  private authService = inject(AuthService);
  private http = inject(HttpClient);
  private router = inject(Router);
  private cdr = inject(ChangeDetectorRef);
  private destroyRef = inject(DestroyRef);
  private busqueda$ = new Subject<string>();

  readonly prioridades: PrioridadIncidencia[] = ['BAJA', 'MEDIA', 'ALTA', 'CRITICA'];
  readonly estados: EstadoIncidencia[] = ['ABIERTA', 'ASIGNADA', 'EN_PROCESO', 'RESUELTA', 'CERRADA'];

  // ── Datos ──────────────────────────────────────────────────────────────
  private todasLasIncidencias: Incidencia[] = [];
  incidenciasFiltradas: Incidencia[] = [];
  pagination: Paginacion = { page: 1, limit: LIMITE_MAXIMO, total: 0, total_pages: 0 };

  proyectos: Proyecto[] = [];
  unidadesFiltro: UnidadConstruccion[] = [];
  usuarios: UsuarioFiltro[] = [];

  empresaActiva: any = null;

  // ── Resumen (calculado únicamente sobre la respuesta real recibida) ─────
  resumen = { total: 0, abiertas: 0, enProceso: 0, resueltas: 0, cerradas: 0 };
  resumenParcial = false;

  // ── Filtros ───────────────────────────────────────────────────────────
  busqueda = '';
  filtroObra: number | null = null;
  filtroUnidad: number | null = null;
  filtroPrioridad: PrioridadIncidencia | '' = '';
  filtroEstado: EstadoIncidencia | '' = '';
  filtroResponsable: number | null = null;

  // ── Estado de interfaz ────────────────────────────────────────────────
  cargando = false;
  error = '';
  exito = '';

  mostrarFormulario = false;

  ngOnInit(): void {
    this.busqueda$
      .pipe(debounceTime(400), distinctUntilChanged(), takeUntilDestroyed(this.destroyRef))
      .subscribe(() => this.cargarIncidencias());

    this.authService.empresaActiva$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((empresa) => {
        this.empresaActiva = empresa;
        this.cargarIncidencias();
      });

    this.cargarProyectos();
    this.cargarUsuarios();
    this.cargarIncidencias();
  }

  esVistaGlobal(): boolean {
    return this.authService.esVistaGlobal();
  }

  hasPermission(permiso: string): boolean {
    return this.authService.hasPermission(permiso);
  }

  puedeRegistrar(): boolean {
    return this.hasPermission('Registrar_incidencias');
  }

  // ─────────────────────────────────────────────────────────────────────
  // CARGA DE CATALOGOS
  // ─────────────────────────────────────────────────────────────────────
  private cargarProyectos(): void {
    this.proyectosService.listarProyectos().subscribe({
      next: (res) => { this.proyectos = res?.data || []; this.cdr.detectChanges(); },
      error: () => {},
    });
  }

  private cargarUsuarios(): void {
    this.http.get<{ success: boolean; data: UsuarioFiltro[] }>(`${environment.apiUrl}/api/usuarios/`).subscribe({
      next: (res) => {
        this.usuarios = (res?.data || []).filter((u) => u.estado === 'ACTIVO');
        this.cdr.detectChanges();
      },
      error: () => {},
    });
  }

  onCambiarFiltroObra(): void {
    this.filtroUnidad = null;
    this.unidadesFiltro = [];
    if (this.filtroObra) {
      this.unidadesService.listar(this.filtroObra).subscribe({
        next: (res) => { this.unidadesFiltro = res?.data || []; this.cdr.detectChanges(); },
        error: () => {},
      });
    }
    this.filtrar();
  }

  // ─────────────────────────────────────────────────────────────────────
  // CARGA DE INCIDENCIAS
  //
  // Se solicita al backend con el límite máximo permitido (100) y sin el
  // filtro de estado, para poder calcular el resumen por estado a partir de
  // una única respuesta real. El filtro de estado se aplica en cliente sobre
  // ese mismo conjunto. El total del backend (pagination.total) sí refleja
  // siempre el conteo real y exacto de la BD para los demás filtros.
  // ─────────────────────────────────────────────────────────────────────
  cargarIncidencias(): void {
    this.cargando = true;
    this.error = '';

    this.incidenciasService
      .listar({
        id_obra: this.filtroObra || undefined,
        id_unidad: this.filtroUnidad || undefined,
        prioridad: (this.filtroPrioridad || undefined) as PrioridadIncidencia | undefined,
        busqueda: this.busqueda.trim() || undefined,
        id_responsable: this.filtroResponsable || undefined,
        page: 1,
        limit: LIMITE_MAXIMO,
      })
      .subscribe({
        next: (res) => {
          this.cargando = false;
          this.todasLasIncidencias = res.data || [];
          this.pagination = res.pagination;
          this.resumenParcial = res.pagination.total > this.todasLasIncidencias.length;
          this.calcularResumen();
          this.aplicarFiltroEstado();
          this.cdr.detectChanges();
        },
        error: (err) => {
          this.cargando = false;
          this.todasLasIncidencias = [];
          this.incidenciasFiltradas = [];
          this.mostrarError(this.mensajeError(err, 'No se pudieron cargar las incidencias.'));
          this.cdr.detectChanges();
        },
      });
  }

  private calcularResumen(): void {
    const base = this.todasLasIncidencias;
    this.resumen = {
      total: this.pagination.total,
      abiertas: base.filter((i) => i.estado === 'ABIERTA').length,
      enProceso: base.filter((i) => i.estado === 'ASIGNADA' || i.estado === 'EN_PROCESO').length,
      resueltas: base.filter((i) => i.estado === 'RESUELTA').length,
      cerradas: base.filter((i) => i.estado === 'CERRADA').length,
    };
  }

  aplicarFiltroEstado(): void {
    this.incidenciasFiltradas = this.filtroEstado
      ? this.todasLasIncidencias.filter((i) => i.estado === this.filtroEstado)
      : this.todasLasIncidencias;
  }

  buscar(): void {
    this.busqueda$.next(this.busqueda.trim());
  }

  filtrar(): void {
    this.cargarIncidencias();
  }

  filtrarPorEstado(estado: EstadoIncidencia | ''): void {
    this.filtroEstado = this.filtroEstado === estado ? '' : estado;
    this.aplicarFiltroEstado();
  }

  limpiarFiltros(): void {
    this.busqueda = '';
    this.filtroObra = null;
    this.filtroUnidad = null;
    this.unidadesFiltro = [];
    this.filtroPrioridad = '';
    this.filtroEstado = '';
    this.filtroResponsable = null;
    this.cargarIncidencias();
  }

  // ─────────────────────────────────────────────────────────────────────
  // NAVEGACION / MODAL DE REGISTRO
  // ─────────────────────────────────────────────────────────────────────
  verIncidencia(incidencia: Incidencia): void {
    this.router.navigate(['/incidencias', incidencia.id_incidencia]);
  }

  abrirNueva(): void {
    this.error = '';
    this.mostrarFormulario = true;
  }

  cerrarFormulario(): void {
    this.mostrarFormulario = false;
  }

  incidenciaRegistrada(evento: { id_incidencia?: number }): void {
    this.mostrarFormulario = false;
    this.mostrarExito('Incidencia registrada exitosamente.');
    this.cargarIncidencias();
    if (evento?.id_incidencia) {
      this.router.navigate(['/incidencias', evento.id_incidencia]);
    }
  }

  // ─────────────────────────────────────────────────────────────────────
  // MENSAJES
  // ─────────────────────────────────────────────────────────────────────
  private mensajeError(err: any, fallback: string): string {
    if (err?.status === 401) return 'Tu sesión ha expirado. Vuelve a iniciar sesión.';
    if (err?.status === 403) return 'No tienes permisos para realizar esta acción.';
    if (err?.status >= 500) return 'Error interno del servidor. Intenta nuevamente.';
    return err?.error?.detail || err?.error?.message || fallback;
  }

  private mostrarError(mensaje: string): void {
    this.error = mensaje;
    setTimeout(() => { this.error = ''; this.cdr.detectChanges(); }, 6000);
  }

  private mostrarExito(mensaje: string): void {
    this.exito = mensaje;
    setTimeout(() => { this.exito = ''; this.cdr.detectChanges(); }, 4500);
  }

  trackByIncidencia(_index: number, item: Incidencia): number {
    return item.id_incidencia;
  }
}
