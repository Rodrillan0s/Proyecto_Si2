import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-empty-state',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="flex flex-col items-center justify-center p-8 lg:p-12 text-center rounded-xl border border-dashed border-slate-300 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/30">
      <div class="flex h-14 w-14 items-center justify-center rounded-full bg-amber-50 dark:bg-amber-950/40 text-amber-600 dark:text-amber-400 mb-4 border border-amber-200 dark:border-amber-800/40">
        <svg class="h-7 w-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" [attr.d]="iconoPath" />
        </svg>
      </div>
      <h3 class="text-base font-bold text-slate-900 dark:text-white">
        {{ titulo }}
      </h3>
      <p *ngIf="descripcion" class="mt-1 text-sm text-slate-500 dark:text-slate-400 max-w-sm">
        {{ descripcion }}
      </p>
      <div *ngIf="accionTexto" class="mt-5">
        <button
          type="button"
          (click)="onAccion.emit()"
          class="inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-lg bg-amber-600 text-white hover:bg-amber-700 transition shadow-xs"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          {{ accionTexto }}
        </button>
      </div>
      <ng-content></ng-content>
    </div>
  `
})
export class EmptyStateComponent {
  @Input() titulo: string = 'No hay datos disponibles';
  @Input() descripcion?: string;
  @Input() accionTexto?: string;
  @Input() iconoPath: string = 'M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4';
  @Output() onAccion = new EventEmitter<void>();
}
