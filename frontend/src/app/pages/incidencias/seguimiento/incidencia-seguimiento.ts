import { Component, Input, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { IncidenciaSeguimiento, IncidenciasService } from '../../../services/incidencias';

@Component({
  selector: 'app-incidencia-seguimiento',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './incidencia-seguimiento.html',
})
export class IncidenciaSeguimientoComponent implements OnInit {
  private incidenciasService = inject(IncidenciasService);

  @Input({ required: true }) idIncidencia!: number;
  @Input() puedeComentar = false;

  seguimientos: IncidenciaSeguimiento[] = [];
  cargando = false;
  error = '';

  nuevaObservacion = '';
  enviando = false;

  ngOnInit(): void {
    this.cargar();
  }

  cargar(): void {
    this.cargando = true;
    this.error = '';
    this.incidenciasService.listarSeguimiento(this.idIncidencia).subscribe({
      next: (res) => {
        this.cargando = false;
        this.seguimientos = res.data || [];
      },
      error: (err) => {
        this.cargando = false;
        this.error = err?.error?.detail || 'No se pudo cargar el historial de seguimiento.';
      },
    });
  }

  agregar(): void {
    if (this.enviando) return;
    const texto = this.nuevaObservacion.trim();
    if (!texto) {
      this.error = 'La observación no puede estar vacía.';
      return;
    }
    this.error = '';
    this.enviando = true;
    this.incidenciasService.registrarSeguimiento(this.idIncidencia, texto).subscribe({
      next: () => {
        this.enviando = false;
        this.nuevaObservacion = '';
        this.cargar();
      },
      error: (err) => {
        this.enviando = false;
        this.error = err?.error?.detail || 'No se pudo registrar la observación.';
      },
    });
  }

  trackBySeguimiento(_index: number, item: IncidenciaSeguimiento): number {
    return item.id_seguimiento;
  }
}
