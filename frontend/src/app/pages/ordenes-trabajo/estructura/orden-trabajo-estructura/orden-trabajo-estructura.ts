import {
  Component,
  EventEmitter,
  Input,
  Output,
  inject
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import {
  OrdenesTrabajoService,
  OrdenTrabajo,
  OrdenTrabajoPayload
} from '../../../../services/ordenes-trabajo';

@Component({
  selector: 'app-orden-trabajo-estructura',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './orden-trabajo-estructura.html',
  styleUrl: './orden-trabajo-estructura.css'
})
export class OrdenTrabajoEstructuraComponent {

  private ordenesTrabajoService = inject(OrdenesTrabajoService);

  @Input() orden: OrdenTrabajo | null = null;
  @Input() modoEdicion = false;

  @Output() cerrar = new EventEmitter<void>();
  @Output() guardado = new EventEmitter<void>();

  guardando = false;
  mensajeError = '';

  formulario: OrdenTrabajoPayload = {
    id_obra: 0,
    tipo_trab: '',
    cuadrilla: 0,
    estado: 'PENDIENTE',
    fecha_inicio: '',
    fecha_fin: '',
    observacion: '',
    id_usuarios: []
  };

  ngOnInit(): void {
    this.cargarFormulario();
  }

  private cargarFormulario(): void {

    if (!this.orden) {
      this.formulario = {
        id_obra: 0,
        tipo_trab: '',
        cuadrilla: 0,
        estado: 'PENDIENTE',
        fecha_inicio: '',
        fecha_fin: '',
        observacion: '',
        id_usuarios: []
      };

      return;
    }

    this.formulario = {
      id_obra: this.orden.id_obra,
      tipo_trab: this.orden.tipo_trab || '',
      cuadrilla: this.orden.cuadrilla || 0,
      estado: this.orden.estado || 'PENDIENTE',
      fecha_inicio: this.orden.fecha_inicio || '',
      fecha_fin: this.orden.fecha_fin || '',
      observacion: this.orden.observacion || '',
      id_usuarios: []
    };
  }

  guardar(): void {

    if (!this.validarFormulario()) {
      return;
    }

    this.guardando = true;
    this.mensajeError = '';

    if (this.modoEdicion && this.orden) {

      this.ordenesTrabajoService
        .actualizarOrdenTrabajo(
          this.orden.orden_nro,
          this.formulario
        )
        .subscribe({

          next: () => {
            this.guardando = false;
            this.guardado.emit();
          },

          error: (error) => {
            this.guardando = false;

            this.mensajeError =
              error?.error?.detail ||
              error?.error?.message ||
              'No se pudo actualizar la orden de trabajo.';
          }

        });

      return;
    }

    this.ordenesTrabajoService
      .crearOrdenTrabajo(this.formulario)
      .subscribe({

        next: () => {
          this.guardando = false;
          this.guardado.emit();
        },

        error: (error) => {
          this.guardando = false;

          this.mensajeError =
            error?.error?.detail ||
            error?.error?.message ||
            'No se pudo crear la orden de trabajo.';
        }

      });
  }

  validarFormulario(): boolean {

    if (!this.formulario.id_obra || this.formulario.id_obra <= 0) {
      this.mensajeError = 'Debe ingresar una obra válida.';
      return false;
    }

    if (!this.formulario.tipo_trab.trim()) {
      this.mensajeError = 'Debe ingresar el tipo de trabajo.';
      return false;
    }

    if (
      this.formulario.cuadrilla === null ||
      this.formulario.cuadrilla === undefined ||
      this.formulario.cuadrilla < 0
    ) {
      this.mensajeError =
        'La cantidad de cuadrilla no puede ser negativa.';
      return false;
    }

    if (!this.formulario.estado.trim()) {
      this.mensajeError = 'Debe seleccionar un estado.';
      return false;
    }

    if (!this.formulario.fecha_inicio) {
      this.mensajeError = 'Debe ingresar la fecha de inicio.';
      return false;
    }

    if (
      this.formulario.fecha_fin &&
      this.formulario.fecha_fin < this.formulario.fecha_inicio
    ) {
      this.mensajeError =
        'La fecha de fin no puede ser anterior a la fecha de inicio.';
      return false;
    }

    return true;
  }

  cerrarFormulario(): void {
    if (this.guardando) {
      return;
    }

    this.cerrar.emit();
  }
}