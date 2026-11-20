import {
  Component, Input, OnInit, OnChanges, SimpleChanges,
  inject, ChangeDetectorRef, NgZone
} from '@angular/core';
import { CommonModule, DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import {
  AvancesService, OrdenAvance, ResumenAvancesResponse, CuadrillaResumen
} from '../../../services/avances.service';
import { AuthService } from '../../../services/auth';

@Component({
  selector: 'app-proyecto-avances',
  standalone: true,
  imports: [CommonModule, FormsModule, DatePipe],
  templateUrl: './proyecto-avances.html',
  styleUrl: './proyecto-avances.css'
})
export class ProyectoAvancesComponent implements OnInit, OnChanges {
  @Input() idObra!: number;

  private avancesService = inject(AvancesService);
  private authService = inject(AuthService);
  private cdr = inject(ChangeDetectorRef);
  private ngZone = inject(NgZone);

  // ── Datos de la Bitácora ────────────────────────────────────────────────
  resumen: ResumenAvancesResponse | null = null;
  ordenes: OrdenAvance[] = [];
  ordenesFiltradas: OrdenAvance[] = [];
  cuadrillas: CuadrillaResumen[] = [];

  // ── Métricas Calculadas ─────────────────────────────────────────────────
  porcentajeAvance: number = 0;
  totalOrdenes: number = 0;
  ordenesCumplidas: number = 0;
  ordenesPendientes: number = 0;

  // ── Estado de UI ─────────────────────────────────────────────────────────
  cargando: boolean = false;
  mensajeError: string = '';
  vistaTab: 'todas' | 'cumplidas' | 'pendientes' = 'todas';

  // ── Filtros ───────────────────────────────────────────────────────────────
  filtroCuadrilla: number | null = null;
  busquedaTexto: string = '';

  ngOnInit() {
    if (this.idObra) {
      this.cargarDatos();
    }
  }

  ngOnChanges(changes: SimpleChanges) {
    if (changes['idObra'] && this.idObra) {
      this.cargarDatos();
    }
  }

  cargarDatos() {
    this.cargando = true;
    this.mensajeError = '';

    // 1. Cargar resumen cuantitativo (% global, conteos, cuadrillas)
    this.avancesService.resumenAvances(this.idObra).subscribe({
      next: (res) => this.ngZone.run(() => {
        if (res.success) {
          this.resumen = res;
          this.porcentajeAvance = Number(res.porcentaje_avance || 0);
          this.totalOrdenes = res.total_ordenes || 0;
          this.ordenesCumplidas = res.ordenes_cumplidas || 0;
          this.ordenesPendientes = res.ordenes_pendientes || 0;
          this.cuadrillas = res.cuadrillas || [];
        }
        this.cargarOrdenes();
      }),
      error: (err) => this.ngZone.run(() => {
        this.mensajeError = err.error?.detail || 'Error al obtener el resumen de avance.';
        this.cargando = false;
        this.cdr.detectChanges();
      })
    });
  }

  cargarOrdenes() {
    this.avancesService.listarAvances(this.idObra).subscribe({
      next: (res) => this.ngZone.run(() => {
        if (res.success) {
          this.ordenes = res.data || [];
          this.aplicarFiltros();
        }
        this.cargando = false;
        this.cdr.detectChanges();
      }),
      error: (err) => this.ngZone.run(() => {
        this.mensajeError = err.error?.detail || 'Error al cargar la bitácora de órdenes.';
        this.cargando = false;
        this.cdr.detectChanges();
      })
    });
  }

  cambiarTab(tab: 'todas' | 'cumplidas' | 'pendientes') {
    this.vistaTab = tab;
    this.aplicarFiltros();
  }

  aplicarFiltros() {
    let filtradas = [...this.ordenes];

    // Filtro por pestaña de estado
    if (this.vistaTab === 'cumplidas') {
      filtradas = filtradas.filter(o => o.es_cumplida);
    } else if (this.vistaTab === 'pendientes') {
      filtradas = filtradas.filter(o => !o.es_cumplida);
    }

    // Filtro por cuadrilla
    if (this.filtroCuadrilla !== null) {
      filtradas = filtradas.filter(o => o.cuadrilla === this.filtroCuadrilla);
    }

    // Búsqueda por texto (tipo de trabajo, observaciones o personal)
    if (this.busquedaTexto.trim()) {
      const q = this.busquedaTexto.toLowerCase().trim();
      filtradas = filtradas.filter(o =>
        (o.tipo_trab || '').toLowerCase().includes(q) ||
        (o.observacion || '').toLowerCase().includes(q) ||
        o.orden_nro.toString().includes(q) ||
        (o.responsables || []).some(r => (r.nombre_completo || '').toLowerCase().includes(q))
      );
    }

    this.ordenesFiltradas = filtradas;
    this.cdr.detectChanges();
  }

  limpiarFiltros() {
    this.filtroCuadrilla = null;
    this.busquedaTexto = '';
    this.vistaTab = 'todas';
    this.aplicarFiltros();
  }

  recargar() {
    this.cargarDatos();
  }
}
