import { Component, EventEmitter, Input, OnChanges, OnInit, Output, SimpleChanges, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { ProyectosService, Proyecto } from '../../../services/proyectos';
import { UnidadesService, UnidadConstruccion } from '../../../services/unidades';
import {
  Incidencia,
  IncidenciasService,
  PrioridadIncidencia,
} from '../../../services/incidencias';

interface IncidenciaFormModel {
  id_obra: number | null;
  id_unidad: number | null;
  titulo: string;
  descripcion: string;
  prioridad: PrioridadIncidencia | '';
  ubicacion: string;
}

@Component({
  selector: 'app-incidencia-formulario',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './incidencia-formulario.html',
})
export class IncidenciaFormularioComponent implements OnInit, OnChanges {
  private proyectosService = inject(ProyectosService);
  private unidadesService = inject(UnidadesService);
  private incidenciasService = inject(IncidenciasService);

  /** Si se recibe una incidencia, el formulario trabaja en modo edición. */
  @Input() incidencia: Incidencia | null = null;
  /** Preselecciona un proyecto al registrar (opcional, ej. desde el detalle de una obra). */
  @Input() idObraInicial?: number;

  @Output() guardado = new EventEmitter<{ id_incidencia?: number }>();
  @Output() cancelado = new EventEmitter<void>();

  readonly prioridades: PrioridadIncidencia[] = ['BAJA', 'MEDIA', 'ALTA', 'CRITICA'];

  proyectos: Proyecto[] = [];
  unidades: UnidadConstruccion[] = [];
  cargandoProyectos = false;
  cargandoUnidades = false;

  guardando = false;
  error = '';

  form: IncidenciaFormModel = this.formularioVacio();

  get editando(): boolean {
    return !!this.incidencia;
  }

  ngOnInit(): void {
    this.cargarProyectos();
    if (this.incidencia) {
      this.cargarDesdeIncidencia(this.incidencia);
    } else if (this.idObraInicial) {
      this.form.id_obra = this.idObraInicial;
      this.cargarUnidades(this.idObraInicial);
    }
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['incidencia'] && !changes['incidencia'].firstChange) {
      if (this.incidencia) {
        this.cargarDesdeIncidencia(this.incidencia);
      } else {
        this.form = this.formularioVacio();
      }
    }
  }

  private formularioVacio(): IncidenciaFormModel {
    return { id_obra: null, id_unidad: null, titulo: '', descripcion: '', prioridad: '', ubicacion: '' };
  }

  private cargarDesdeIncidencia(incidencia: Incidencia): void {
    this.form = {
      id_obra: incidencia.id_obra,
      id_unidad: incidencia.id_unidad ?? null,
      titulo: incidencia.titulo,
      descripcion: incidencia.descripcion,
      prioridad: incidencia.prioridad,
      ubicacion: incidencia.ubicacion || '',
    };
    if (incidencia.id_obra) {
      this.cargarUnidades(incidencia.id_obra);
    }
  }

  private cargarProyectos(): void {
    this.cargandoProyectos = true;
    this.proyectosService.listarProyectos().subscribe({
      next: (res) => {
        this.proyectos = res?.data || [];
        this.cargandoProyectos = false;
      },
      error: () => {
        this.cargandoProyectos = false;
        this.error = 'No se pudo cargar la lista de proyectos.';
      },
    });
  }

  /** HU69: al cambiar de proyecto, se limpia la unidad y se recargan solo las de ese proyecto. */
  onCambiarObra(): void {
    this.form.id_unidad = null;
    this.unidades = [];
    if (this.form.id_obra) {
      this.cargarUnidades(this.form.id_obra);
    }
  }

  private cargarUnidades(idObra: number): void {
    this.cargandoUnidades = true;
    this.unidadesService.listar(idObra).subscribe({
      next: (res) => {
        this.unidades = res?.data || [];
        this.cargandoUnidades = false;
      },
      error: () => {
        this.unidades = [];
        this.cargandoUnidades = false;
      },
    });
  }

  private validar(): string | null {
    if (!this.editando && !this.form.id_obra) return 'Debe seleccionar el proyecto/obra.';
    if (!this.form.titulo || !this.form.titulo.trim()) return 'El título es obligatorio.';
    if (this.form.titulo.trim().length > 200) return 'El título no puede superar 200 caracteres.';
    if (!this.form.descripcion || !this.form.descripcion.trim()) return 'La descripción es obligatoria.';
    if (!this.form.prioridad) return 'Debe seleccionar una prioridad.';
    if (this.form.ubicacion && this.form.ubicacion.trim().length > 255) return 'La ubicación no puede superar 255 caracteres.';
    return null;
  }

  guardar(): void {
    if (this.guardando) return;
    const err = this.validar();
    if (err) {
      this.error = err;
      return;
    }
    this.error = '';
    this.guardando = true;

    if (this.editando && this.incidencia) {
      this.incidenciasService
        .actualizar(this.incidencia.id_incidencia, {
          titulo: this.form.titulo.trim(),
          descripcion: this.form.descripcion.trim(),
          prioridad: this.form.prioridad as PrioridadIncidencia,
          ubicacion: this.form.ubicacion.trim() || null,
        })
        .subscribe({
          next: () => {
            this.guardando = false;
            this.guardado.emit({ id_incidencia: this.incidencia!.id_incidencia });
          },
          error: (err) => {
            this.guardando = false;
            this.error = this.mensajeError(err, 'No se pudo actualizar la incidencia.');
          },
        });
    } else {
      this.incidenciasService
        .registrar({
          id_obra: this.form.id_obra as number,
          id_unidad: this.form.id_unidad,
          titulo: this.form.titulo.trim(),
          descripcion: this.form.descripcion.trim(),
          prioridad: this.form.prioridad as PrioridadIncidencia,
          ubicacion: this.form.ubicacion.trim() || null,
        })
        .subscribe({
          next: (res) => {
            this.guardando = false;
            this.form = this.formularioVacio();
            this.guardado.emit({ id_incidencia: res.id_incidencia });
          },
          error: (err) => {
            this.guardando = false;
            this.error = this.mensajeError(err, 'No se pudo registrar la incidencia.');
          },
        });
    }
  }

  cancelar(): void {
    if (this.guardando) return;
    this.cancelado.emit();
  }

  private mensajeError(err: any, fallback: string): string {
    if (err?.status === 401) return 'Tu sesión ha expirado. Vuelve a iniciar sesión.';
    if (err?.status === 403) return 'No tienes permisos para realizar esta acción.';
    if (err?.status === 404) return err?.error?.detail || 'El proyecto o la unidad no existen o no pertenecen a tu empresa.';
    if (err?.status >= 500) return 'Error interno del servidor. Intenta nuevamente.';
    return err?.error?.detail || err?.error?.message || fallback;
  }
}
