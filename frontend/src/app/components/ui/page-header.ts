import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-page-header',
  standalone: true,
  imports: [CommonModule],
  template: `
    <header class="mb-6 flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-5">
      <div class="min-w-0">
        <div *ngIf="categoria || codigo" class="flex flex-wrap items-center gap-2 mb-1.5">
          <span *ngIf="categoria" class="text-[11px] font-bold uppercase tracking-wider text-amber-600 dark:text-amber-400">
            {{ categoria }}
          </span>
          <span *ngIf="categoria && codigo" class="text-slate-300 dark:text-slate-600">•</span>
          <span *ngIf="codigo" class="text-xs font-mono px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
            {{ codigo }}
          </span>
        </div>
        <h1 class="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 dark:text-white flex flex-wrap items-center gap-2.5">
          <span>{{ titulo }}</span>
          <ng-content select="[badge]"></ng-content>
        </h1>
        <p *ngIf="subtitulo" class="text-sm text-slate-600 dark:text-slate-400 mt-1.5 max-w-2xl leading-relaxed">
          {{ subtitulo }}
        </p>
      </div>

      <div class="flex flex-wrap items-center gap-2 shrink-0">
        <ng-content select="[actions]"></ng-content>
      </div>
    </header>
  `
})
export class PageHeaderComponent {
  @Input() titulo: string = '';
  @Input() subtitulo?: string;
  @Input() categoria?: string;
  @Input() codigo?: string;
}
