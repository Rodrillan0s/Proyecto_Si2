import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-alert-banner',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div
      *ngIf="mensaje"
      [attr.role]="tipo === 'error' ? 'alert' : 'status'"
      class="flex items-start justify-between gap-3 rounded-xl border px-4 py-3 text-sm transition-all"
      [ngClass]="obtenerClases()"
    >
      <div class="flex items-start gap-2.5 min-w-0">
        <svg class="h-5 w-5 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" [attr.d]="obtenerIcono()" />
        </svg>
        <div class="min-w-0">
          <p *ngIf="titulo" class="font-semibold leading-snug">{{ titulo }}</p>
          <p class="leading-relaxed" [class.mt-0.5]="titulo">{{ mensaje }}</p>
        </div>
      </div>
      <button
        *ngIf="cerrable"
        type="button"
        (click)="onCerrar.emit()"
        aria-label="Cerrar mensaje"
        class="shrink-0 rounded-lg p-1 opacity-70 hover:opacity-100 transition"
      >
        <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
  `
})
export class AlertBannerComponent {
  @Input() tipo: 'error' | 'exito' | 'advertencia' | 'info' = 'info';
  @Input() titulo?: string;
  @Input() mensaje: string = '';
  @Input() cerrable: boolean = false;
  @Output() onCerrar = new EventEmitter<void>();

  obtenerClases(): string {
    switch (this.tipo) {
      case 'error':
        return 'bg-rose-50 border-rose-200 text-rose-800 dark:bg-rose-950/40 dark:border-rose-800/60 dark:text-rose-200';
      case 'exito':
        return 'bg-emerald-50 border-emerald-200 text-emerald-800 dark:bg-emerald-950/40 dark:border-emerald-800/60 dark:text-emerald-200';
      case 'advertencia':
        return 'bg-amber-50 border-amber-200 text-amber-900 dark:bg-amber-950/40 dark:border-amber-800/60 dark:text-amber-200';
      default:
        return 'bg-sky-50 border-sky-200 text-sky-900 dark:bg-sky-950/40 dark:border-sky-800/60 dark:text-sky-200';
    }
  }

  obtenerIcono(): string {
    switch (this.tipo) {
      case 'error':
        return 'M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z';
      case 'exito':
        return 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z';
      case 'advertencia':
        return 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z';
      default:
        return 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z';
    }
  }
}
