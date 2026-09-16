import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-status-badge',
  standalone: true,
  imports: [CommonModule],
  template: `
    <span
      class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold tracking-wide border transition-colors shadow-xs"
      [ngClass]="obtenerClases()"
    >
      <span class="w-1.5 h-1.5 rounded-full" [ngClass]="obtenerPuntoClase()"></span>
      {{ texto || estado }}
    </span>
  `
})
export class StatusBadgeComponent {
  @Input() estado: string = 'ACTIVO';
  @Input() texto?: string;

  obtenerClases(): string {
    const e = (this.estado || '').toUpperCase();
    switch (e) {
      case 'ACTIVO':
      case 'EN_PROCESO':
      case 'EJECUCION':
      case 'DISPONIBLE':
      case 'EXITOSO':
        return 'bg-emerald-50 text-emerald-800 border-emerald-300 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-800';

      case 'PLANIFICACION':
      case 'PENDIENTE':
      case 'EN_ESPERA':
        return 'bg-amber-50 text-amber-800 border-amber-300 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-800';

      case 'PAUSADO':
      case 'SUSPENDIDO':
      case 'STOCK_BAJO':
      case 'BAJO':
        return 'bg-orange-50 text-orange-800 border-orange-300 dark:bg-orange-950/40 dark:text-orange-300 dark:border-orange-800';

      case 'FINALIZADO':
      case 'COMPLETADO':
      case 'ENTREGADO':
        return 'bg-blue-50 text-blue-800 border-blue-300 dark:bg-blue-950/40 dark:text-blue-300 dark:border-blue-800';

      case 'INACTIVO':
      case 'CANCELADO':
      case 'BLOQUEADO':
      case 'ELIMINADO':
      case 'CRITICO':
      case 'AGOTADO':
        return 'bg-rose-50 text-rose-800 border-rose-300 dark:bg-rose-950/40 dark:text-rose-300 dark:border-rose-800';

      default:
        return 'bg-slate-100 text-slate-800 border-slate-300 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700';
    }
  }

  obtenerPuntoClase(): string {
    const e = (this.estado || '').toUpperCase();
    switch (e) {
      case 'ACTIVO':
      case 'EN_PROCESO':
      case 'EJECUCION':
      case 'DISPONIBLE':
      case 'EXITOSO':
        return 'bg-emerald-500 animate-pulse';

      case 'PLANIFICACION':
      case 'PENDIENTE':
      case 'EN_ESPERA':
        return 'bg-amber-500';

      case 'PAUSADO':
      case 'SUSPENDIDO':
      case 'STOCK_BAJO':
      case 'BAJO':
        return 'bg-orange-500';

      case 'FINALIZADO':
      case 'COMPLETADO':
      case 'ENTREGADO':
        return 'bg-blue-500';

      case 'INACTIVO':
      case 'CANCELADO':
      case 'BLOQUEADO':
      case 'ELIMINADO':
      case 'CRITICO':
      case 'AGOTADO':
        return 'bg-rose-500';

      default:
        return 'bg-slate-400';
    }
  }
}
