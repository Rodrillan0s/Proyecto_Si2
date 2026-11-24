import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-loading-state',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div role="status" aria-live="polite" class="w-full space-y-4">
      <span class="sr-only">{{ mensaje }}</span>

      <!-- Skeleton de tarjetas KPI -->
      <div *ngIf="variante === 'cards'" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div *ngFor="let i of items" class="ob-card p-5 space-y-3">
          <div class="flex items-center justify-between">
            <div class="ob-skeleton h-3.5 w-24"></div>
            <div class="ob-skeleton h-9 w-9 rounded-lg"></div>
          </div>
          <div class="ob-skeleton h-8 w-20"></div>
          <div class="ob-skeleton h-3 w-32"></div>
        </div>
      </div>

      <!-- Skeleton de tabla -->
      <div *ngIf="variante === 'table'" class="ob-card overflow-hidden">
        <div class="px-4 py-3 border-b border-slate-200 dark:border-slate-800 flex gap-4">
          <div class="ob-skeleton h-3.5 w-1/4"></div>
          <div class="ob-skeleton h-3.5 w-1/4"></div>
          <div class="ob-skeleton h-3.5 w-1/6"></div>
          <div class="ob-skeleton h-3.5 w-1/6 ml-auto"></div>
        </div>
        <div *ngFor="let i of items" class="px-4 py-4 border-b border-slate-100 dark:border-slate-800/60 flex items-center gap-4">
          <div class="ob-skeleton h-4 w-1/3"></div>
          <div class="ob-skeleton h-4 w-1/4"></div>
          <div class="ob-skeleton h-6 w-20 rounded-full"></div>
          <div class="ob-skeleton h-8 w-20 ml-auto"></div>
        </div>
      </div>

      <!-- Skeleton de lista -->
      <div *ngIf="variante === 'list'" class="space-y-3">
        <div *ngFor="let i of items" class="ob-card p-4 flex items-center gap-4">
          <div class="ob-skeleton h-10 w-10 rounded-lg shrink-0"></div>
          <div class="flex-1 space-y-2">
            <div class="ob-skeleton h-4 w-2/5"></div>
            <div class="ob-skeleton h-3 w-3/5"></div>
          </div>
        </div>
      </div>

      <!-- Variante compacta -->
      <div *ngIf="variante === 'inline'" class="flex items-center justify-center gap-3 py-8 text-sm text-slate-500 dark:text-slate-400">
        <span class="h-4 w-4 rounded-full border-2 border-amber-500 border-t-transparent animate-spin"></span>
        <span>{{ mensaje }}</span>
      </div>
    </div>
  `
})
export class LoadingStateComponent {
  @Input() variante: 'cards' | 'table' | 'list' | 'inline' = 'table';
  @Input() filas: number = 4;
  @Input() mensaje: string = 'Cargando información...';

  get items(): number[] {
    return Array.from({ length: Math.max(1, this.filas) }, (_, i) => i);
  }
}
