import {
  Component, Input, OnInit, OnChanges, SimpleChanges,
  inject, ChangeDetectorRef, NgZone
} from '@angular/core';
import { CommonModule, DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import {
  AvancesService, Avance, ResumenAvance, NuevoAvance
} from '../../../services/avances.service';
import { AuthService } from '../../../services/auth';
import { UnidadesService } from '../../../services/unidades';

interface UnidadItem {
  id_unidad: number;
  codigo: string;
  nombre: string;
  tipo_unidad: string;
  estado: string;
}

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
  private unidadesService = inject(UnidadesService);
  private cdr = inject(ChangeDetectorRef);
  private ngZone = inject(NgZone);

  // ── Estado de datos ─────────────────────────────────────────────────────
  avances: Avance[] = [];
  avancesFiltrados: Avance[] = [];
  resumenUnidades: ResumenAvance[] = [];
  avanceGlobal: number = 0;
  unidades: UnidadItem[] = [];

  // ── Estado de UI ─────────────────────────────────────────────────────────
  cargando: boolean = false;
  cargandoResumen: boolean = false;
  procesando: boolean = false;
  mensajeError: string = '';
  mensajeExito: string = '';
  mostrarFormulario: boolean = false;
  vistaActiva: 'historial' | 'resumen' = 'resumen';

  // ── Filtros ───────────────────────────────────────────────────────────────
  filtroUnidad: number | null = null;

  // ── Formulario nuevo avance ───────────────────────────────────────────────
  nuevoAvance: NuevoAvance = {
    id_unidad: 0,
    porcentaje_avance: 0,
    fecha_registro: new Date().toISOString().substring(0, 10),
    observacion: ''
  };
  erroresForm: { [key: string]: string } = {};

  // ── Permisos ──────────────────────────────────────────────────────────────
  get puedeRegistrar(): boolean {
    const rol = this.authService.obtenerUsuario()?.nombre_rol || '';
    return ['ADMINISTRADOR', 'ADMINISTRADOR_EMPRESA', 'JEFE DE OBRA'].includes(rol);
  }

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

  // ── Carga de datos ────────────────────────────────────────────────────────

  cargarDatos() {
    this.cargarResumen();
    this.cargarAvances();
    this.cargarUnidades();
  }

  cargarResumen() {
    this.cargandoResumen = true;
    this.avancesService.resumenAvances(this.idObra).subscribe({
      next: (res) => this.ngZone.run(() => {
        if (res.success) {
          this.avanceGlobal = res.avance_global || 0;
          this.resumenUnidades = res.unidades || [];
        }
        this.cargandoResumen = false;
        this.cdr.detectChanges();
      }),
      error: () => this.ngZone.run(() => {
        this.cargandoResumen = false;
        this.cdr.detectChanges();
      })
    });
  }

  cargarAvances(idUnidad?: number) {
    this.cargando = true;
    this.avancesService.listarAvances(this.idObra, idUnidad).subscribe({
      next: (res) => this.ngZone.run(() => {
        if (res.success) {
          this.avances = res.data || [];
          this.aplicarFiltros();
        }
        this.cargando = false;
        this.cdr.detectChanges();
      }),
      error: (err) => this.ngZone.run(() => {
        this.mostrarError(err.error?.detail || 'Error al cargar los avances.');
        this.cargando = false;
        this.cdr.detectChanges();
      })
    });
  }

  cargarUnidades() {
    this.unidadesService.listar(this.idObra).subscribe({
      next: (res: any) => this.ngZone.run(() => {
        const data = res?.data || res || [];
        this.unidades = (Array.isArray(data) ? data : []).map((u: any) => ({
          id_unidad: u.id_unidad,
          codigo: u.codigo,
          nombre: u.nombre,
          tipo_unidad: u.tipo_unidad,
          estado: u.estado
        }));
        this.cdr.detectChanges();
      }),
      error: () => {}
    });
  }

  aplicarFiltros() {
    if (this.filtroUnidad) {
      this.avancesFiltrados = this.avances.filter(a => a.id_unidad === Number(this.filtroUnidad));
    } else {
      this.avancesFiltrados = [...this.avances];
    }
  }

  onFiltroUnidadChange() {
    this.cargarAvances(this.filtroUnidad || undefined);
  }

  // ── Formulario ────────────────────────────────────────────────────────────

  abrirFormulario() {
    this.nuevoAvance = {
      id_unidad: this.unidades[0]?.id_unidad || 0,
      porcentaje_avance: 0,
      fecha_registro: new Date().toISOString().substring(0, 10),
      observacion: ''
    };
    this.erroresForm = {};
    this.mostrarFormulario = true;
  }

  cerrarFormulario() {
    this.mostrarFormulario = false;
    this.erroresForm = {};
  }

  validarFormulario(): boolean {
    this.erroresForm = {};
    if (!this.nuevoAvance.id_unidad) {
      this.erroresForm['id_unidad'] = 'Seleccione una unidad de construcción.';
    }
    const pct = Number(this.nuevoAvance.porcentaje_avance);
    if (isNaN(pct) || pct < 0 || pct > 100) {
      this.erroresForm['porcentaje_avance'] = 'El porcentaje debe estar entre 0 y 100.';
    }
    if (!this.nuevoAvance.fecha_registro) {
      this.erroresForm['fecha_registro'] = 'La fecha de registro es obligatoria.';
    }
    return Object.keys(this.erroresForm).length === 0;
  }

  guardarAvance() {
    if (!this.validarFormulario() || this.procesando) return;

    this.procesando = true;
    const payload: NuevoAvance = {
      id_unidad: Number(this.nuevoAvance.id_unidad),
      porcentaje_avance: Number(this.nuevoAvance.porcentaje_avance),
      fecha_registro: this.nuevoAvance.fecha_registro,
      observacion: this.nuevoAvance.observacion || ''
    };

    this.avancesService.registrarAvance(this.idObra, payload).subscribe({
      next: (res) => this.ngZone.run(() => {
        this.procesando = false;
        if (res.success) {
          this.mostrarExito('Avance registrado exitosamente.');
          this.cerrarFormulario();
          this.cargarDatos();
        } else {
          this.mostrarError(res.message || 'No se pudo registrar el avance.');
        }
        this.cdr.detectChanges();
      }),
      error: (err) => this.ngZone.run(() => {
        this.procesando = false;
        this.mostrarError(err.error?.detail || 'Error al registrar el avance.');
        this.cdr.detectChanges();
      })
    });
  }

  eliminarAvance(idAvance: number) {
    if (!confirm('¿Está seguro de que desea eliminar este avance?')) return;
    this.avancesService.eliminarAvance(this.idObra, idAvance).subscribe({
      next: (res) => this.ngZone.run(() => {
        if (res.success) {
          this.mostrarExito('Avance eliminado correctamente.');
          this.cargarDatos();
        } else {
          this.mostrarError(res.message || 'Error al eliminar.');
        }
        this.cdr.detectChanges();
      }),
      error: (err) => this.ngZone.run(() => {
        this.mostrarError(err.error?.detail || 'Error al eliminar el avance.');
        this.cdr.detectChanges();
      })
    });
  }

  // ── Helpers de UI ─────────────────────────────────────────────────────────

  colorEstado(estado: string): string {
    const map: { [k: string]: string } = {
      PLANIFICADO: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300',
      EN_CONSTRUCCION: 'bg-amber-100 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300',
      FINALIZADO: 'bg-green-100 text-green-700 dark:bg-green-950/60 dark:text-green-300',
      SUSPENDIDO: 'bg-red-100 text-red-700 dark:bg-red-950/60 dark:text-red-300'
    };
    return map[estado] || 'bg-gray-100 text-gray-600';
  }

  colorBarra(pct: number): string {
    if (pct >= 100) return 'bg-green-500';
    if (pct >= 60) return 'bg-amber-500';
    if (pct > 0) return 'bg-orange-500';
    return 'bg-slate-300';
  }

  mostrarError(msg: string) {
    this.mensajeError = msg;
    setTimeout(() => { this.mensajeError = ''; this.cdr.detectChanges(); }, 5000);
  }

  mostrarExito(msg: string) {
    this.mensajeExito = msg;
    setTimeout(() => { this.mensajeExito = ''; this.cdr.detectChanges(); }, 4000);
  }

  trackByAvance(_: number, a: Avance) { return a.id_avance; }
  trackByUnidad(_: number, u: ResumenAvance) { return u.id_unidad; }
}
