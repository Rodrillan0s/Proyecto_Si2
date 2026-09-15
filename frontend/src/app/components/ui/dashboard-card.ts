import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-dashboard-card',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div
      class="group relative overflow-hidden rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-5 shadow-xs hover:shadow-md transition-all duration-200 hover:border-amber-400/60 dark:hover:border-amber-500/40"
      [class.cursor-pointer]="clickable"
    >
      <!-- Subtle top construction accent line -->
      <div
        class="absolute top-0 left-0 right-0 h-1 transition-all duration-300 group-hover:h-1.5"
        [ngClass]="obtenerBarraColor()"
      ></div>

      <div class="flex items-start justify-between gap-3">
        <div class="space-y-1">
          <p class="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
            {{ titulo }}
          </p>
          <div class="flex items-baseline gap-2">
            <span class="text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white font-mono">
              {{ valor }}
            </span>
            <span *ngIf="sufijo" class="text-xs font-medium text-slate-500 dark:text-slate-400">
              {{ sufijo }}
            </span>
          </div>
        </div>

        <div
          class="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg transition-transform duration-200 group-hover:scale-105"
          [ngClass]="obtenerIconoFondo()"
        >
          <ng-content select="[icon]"></ng-content>
        </div>
      </div>

      <div *ngIf="subtitulo || detalle" class="mt-3 flex items-center justify-between pt-2 border-t border-slate-100 dark:border-slate-800/80 text-xs">
        <span *ngIf="subtitulo" class="text-slate-500 dark:text-slate-400 truncate">
          {{ subtitulo }}
        </span>
        <span *ngIf="detalle" class="font-medium text-amber-600 dark:text-amber-400 ml-auto shrink-0">
          {{ detalle }}
        </span>
      </div>
    </div>
  `
})
export class DashboardCardComponent {
  @Input() titulo: string = '';
  @Input() valor: string | number = '0';
  @Input() sufijo?: string;
  @Input() subtitulo?: string;
  @Input() detalle?: string;
  @Input() tipo: 'default' | 'amber' | 'blue' | 'emerald' | 'rose' = 'default';
  @Input() clickable: boolean = false;

  obtenerBarraColor(): string {
    switch (this.tipo) {
      case 'amber':
        return 'bg-amber-500';
      case 'blue':
        return 'bg-blue-600';
      case 'emerald':
        return 'bg-emerald-500';
      case 'rose':
        return 'bg-rose-500';
      default:
        return 'bg-slate-300 dark:bg-slate-700 group-hover:bg-amber-500';
    }
  }

  obtenerIconoFondo(): string {
    switch (this.tipo) {
      case 'amber':
        return 'bg-amber-50 dark:bg-amber-950/40 text-amber-600 dark:text-amber-400 border border-amber-200 dark:border-amber-800/40';
      case 'blue':
        return 'bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-blue-800/40';
      case 'emerald':
        return 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800/40';
      case 'rose':
        return 'bg-rose-50 dark:bg-rose-950/40 text-rose-600 dark:text-rose-400 border border-rose-200 dark:border-rose-800/40';
      default:
        return 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700';
    }
  }
}
