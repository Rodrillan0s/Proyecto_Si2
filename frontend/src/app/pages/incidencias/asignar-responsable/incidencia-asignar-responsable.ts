import { ChangeDetectorRef, Component, EventEmitter, Input, OnInit, Output, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { finalize } from 'rxjs/operators';

import {
  AsignarResponsableResponse,
  Incidencia,
  IncidenciasService,
  UsuarioResponsable,
} from '../../../services/incidencias';

@Component({
  selector: 'app-incidencia-asignar-responsable',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './incidencia-asignar-responsable.html',
})
export class IncidenciaAsignarResponsableComponent implements OnInit {
  private incidenciasService = inject(IncidenciasService);
  private cdr = inject(ChangeDetectorRef);

  @Input({ required: true }) incidencia!: Incidencia;

  @Output() asignado = new EventEmitter<AsignarResponsableResponse>();
  @Output() cancelado = new EventEmitter<void>();

  usuariosDisponibles: UsuarioResponsable[] = [];
  usuarioSeleccionado: number | null = null;

  cargandoUsuarios = false;
  asignando = false;
  error = '';

  ngOnInit(): void {
    this.usuarioSeleccionado = this.incidencia.id_responsable ?? null;
    this.cargarUsuarios();
  }

  private cargarUsuarios(): void {
    this.cargandoUsuarios = true;
    this.error = '';
    this.usuariosDisponibles = [];

    // HU71: candidatos ya acotados por el backend al tenant real de la
    // incidencia (incidencia -> obra -> empresa), al vínculo con la obra y
    // a los roles de campo/jefatura permitidos, sin exigir permisos al candidato.
    // finalize() garantiza que loading
    // siempre termine (éxito, error o lista vacía). La app corre sin
    // zone.js, así que además hay que disparar detectChanges() a mano tras
    // el callback async (mismo patrón que incidencia-detalle.ts /
    // incidencias.ts), o la vista se queda congelada aunque el estado
    // interno ya haya cambiado.
    this.incidenciasService
      .obtenerResponsables(this.incidencia.id_incidencia)
      .pipe(
        finalize(() => {
          this.cargandoUsuarios = false;
          this.cdr.detectChanges();
        })
      )
      .subscribe({
        next: (res) => {
          if (res.success) {
            this.usuariosDisponibles = res.data || [];
            if (!this.usuariosDisponibles.some(u => u.nro_usuario === this.usuarioSeleccionado)) {
              this.usuarioSeleccionado = null;
            }
          } else {
            this.error = res.message || 'No se pudieron cargar los responsables disponibles.';
          }
        },
        error: (err) => {
          this.error = this.mensajeError(err);
        },
      });
  }

  confirmar(): void {
    if (this.asignando || this.cargandoUsuarios || !this.usuarioSeleccionado ||
        !this.usuariosDisponibles.some(u => u.nro_usuario === this.usuarioSeleccionado)) return;
    this.asignando = true;
    this.error = '';

    this.incidenciasService.asignarResponsable(this.incidencia.id_incidencia, this.usuarioSeleccionado).subscribe({
      next: (res) => {
        this.asignando = false;
        this.asignado.emit(res);
        this.cdr.detectChanges();
      },
      error: (err) => {
        this.asignando = false;
        this.error = this.mensajeError(err);
        this.cdr.detectChanges();
      },
    });
  }

  cancelar(): void {
    if (this.asignando) return;
    this.cancelado.emit();
  }

  private mensajeError(err: any): string {
    if (err?.status === 401) return 'Tu sesión ha expirado. Vuelve a iniciar sesión.';
    if (err?.status === 403) return 'No tienes permisos para asignar responsables.';
    if (err?.status === 404) return err?.error?.detail || 'La incidencia no existe o no pertenece a tu empresa.';
    if (err?.status >= 500) return 'Error interno del servidor. Intenta nuevamente.';
    return err?.error?.detail || err?.error?.message || 'No se pudo cargar la lista de responsables.';
  }
}
