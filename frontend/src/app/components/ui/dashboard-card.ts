import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-dashboard-card',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div
      class="group relative overflow-hidden rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-4 sm:p-5 shadow-xs hover:shadow-md transition-all duration-200 hover:border-amber-400/60 dark:hover:border-amber-500/40"
      [class.cursor-pointer]="clickable"
    >
      <div
        class="absolute top-0 left-0 right-0 h-1 transition-all duration-200"
        [ngClass]="obtenerBarraColor()"
      ></div>

      <div class="flex items-start justify-between gap-3">
        <div class="space-y-1 min-w-0">
          <p class="text-[11px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 truncate">
            {{ titulo }}
          </p>
          <div class="flex items-baseline gap-1.5 flex-wrap">
            <span class="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white tabular-nums">
              {{ valor }}
            </span>
            <span *ngIf="sufijo" class="text-xs font-medium text-slate-500 dark:text-slate-400">
              {{ sufijo }}
            </span>
          </div>
        </div>

        <div
          class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg transition-transform duration-200 group-hover:scale-105"
          [ngClass]="obtenerIconoFondo()"
        >
          <ng-content select="[icon]"></ng-content>
        </div>
      </div>

      <div *ngIf="subtitulo || detalle" class="mt-3 flex items-center justify-between gap-2 pt-2.5 border-t border-slate-100 dark:border-slate-800/80 text-xs">
        <span *ngIf="subtitulo" class="text-slate-500 dark:text-slate-400 truncate">
          {{ subtitulo }}
        </span>
        <span *ngIf="detalle" class="font-semibold text-amber-600 dark:text-amber-400 ml-auto shrink-0">
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
        return 'bg-sky-600';
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
        return 'bg-sky-50 dark:bg-sky-950/40 text-sky-600 dark:text-sky-400 border border-sky-200 dark:border-sky-800/40';
      case 'emerald':
        return 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800/40';
      case 'rose':
        return 'bg-rose-50 dark:bg-rose-950/40 text-rose-600 dark:text-rose-400 border border-rose-200 dark:border-rose-800/40';
      default:
        return 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700';
    }
  }
}
