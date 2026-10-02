import { ChangeDetectorRef, Component, EventEmitter, Input, OnInit, Output, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { finalize } from 'rxjs/operators';

import {
  Incidencia,
  IncidenciasService,
  OrdenTrabajoDisponible,
  OrdenesTrabajoMutationResponse,
} from '../../../services/incidencias';

/**
 * CU19: selección de las órdenes de trabajo afectadas por una incidencia.
 * Solo se listan las OT de la MISMA obra de la incidencia: el backend deriva
 * la obra y la empresa (nunca se envían desde aquí) y vuelve a validar cada
 * OT al guardar.
 */
@Component({
  selector: 'app-incidencia-ordenes-trabajo',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './incidencia-ordenes-trabajo.html',
})
export class IncidenciaOrdenesTrabajoComponent implements OnInit {
  private incidenciasService = inject(IncidenciasService);
  private cdr = inject(ChangeDetectorRef);

  @Input({ required: true }) incidencia!: Incidencia;

  @Output() guardado = new EventEmitter<OrdenesTrabajoMutationResponse>();
  @Output() cancelado = new EventEmitter<void>();

  ordenes: OrdenTrabajoDisponible[] = [];
  seleccionadas = new Set<number>();

  cargando = false;
  guardando = false;
  error = '';

  ngOnInit(): void {
    this.cargarOrdenes();
  }

  private cargarOrdenes(): void {
    this.cargando = true;
    this.error = '';
    // La app corre sin zone.js: detectChanges() manual tras cada callback async.
    this.incidenciasService
      .listarOrdenesTrabajoDisponibles(this.incidencia.id_incidencia)
      .pipe(
        finalize(() => {
          this.cargando = false;
          this.cdr.detectChanges();
        })
      )
      .subscribe({
        next: (res) => {
          this.ordenes = res.data || [];
          this.seleccionadas = new Set(this.ordenes.filter((o) => o.afectada).map((o) => o.orden_nro));
        },
        error: (err) => {
          this.error = this.mensajeError(err, 'No se pudieron cargar las órdenes de trabajo de la obra.');
        },
      });
  }

  etiqueta(ordenNro: number): string {
    return 'OT-' + String(ordenNro).padStart(3, '0');
  }

  estaSeleccionada(ordenNro: number): boolean {
    return this.seleccionadas.has(ordenNro);
  }

  alternar(ordenNro: number): void {
    if (this.seleccionadas.has(ordenNro)) {
      this.seleccionadas.delete(ordenNro);
    } else {
      this.seleccionadas.add(ordenNro);
    }
  }

  confirmar(): void {
    if (this.guardando) return;
    this.guardando = true;
    this.error = '';

    this.incidenciasService
      .actualizarOrdenesTrabajo(this.incidencia.id_incidencia, [...this.seleccionadas].sort((a, b) => a - b))
      .subscribe({
        next: (res) => {
          this.guardando = false;
          this.guardado.emit(res);
          this.cdr.detectChanges();
        },
        error: (err) => {
          this.guardando = false;
          this.error = this.mensajeError(err, 'No se pudieron guardar las órdenes de trabajo afectadas.');
          this.cdr.detectChanges();
        },
      });
  }

  cancelar(): void {
    if (this.guardando) return;
    this.cancelado.emit();
  }

  private mensajeError(err: any, fallback: string): string {
    if (err?.status === 401) return 'Tu sesión ha expirado. Vuelve a iniciar sesión.';
    if (err?.status === 403) return 'No tienes permisos para seleccionar órdenes de trabajo afectadas.';
    if (err?.status === 404) return err?.error?.detail || 'La incidencia no existe o no pertenece a tu empresa.';
    if (err?.status >= 500) return 'Error interno del servidor. Intenta nuevamente.';
    return err?.error?.detail || err?.error?.message || fallback;
  }
}
