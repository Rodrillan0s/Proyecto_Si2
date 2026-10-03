import { ChangeDetectorRef, Component, DestroyRef, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { AuthService } from '../../../services/auth';
import { Incidencia, IncidenciasService } from '../../../services/incidencias';
import { PageHeaderComponent } from '../../../components/ui/page-header';
import { StatusBadgeComponent } from '../../../components/ui/status-badge';

@Component({
  selector: 'app-incidencias-asignadas',
  standalone: true,
  imports: [CommonModule, RouterModule, PageHeaderComponent, StatusBadgeComponent],
  template: `
    <div class="space-y-6">
      <app-page-header titulo="Incidencias asignadas" subtitulo="Consulta y atiende las incidencias donde eres responsable." categoria="CU19"></app-page-header>
      <p *ngIf="cargando" role="status">Cargando incidencias...</p>
      <div *ngIf="error" role="alert">{{ error }} <button (click)="cargar(pagina)">Reintentar</button></div>
      <p *ngIf="!cargando && !error && !incidencias.length">No tienes incidencias asignadas actualmente.</p>
      <div *ngIf="!cargando && !error" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <article *ngFor="let inc of incidencias" class="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5 space-y-3">
          <h2 class="font-semibold">#{{ inc.id_incidencia }} · {{ inc.titulo }}</h2>
          <p class="text-sm text-slate-500">{{ inc.obra_nombre }} · {{ inc.obra_codigo }}</p>
          <div class="flex gap-2">
            <app-status-badge [estado]="inc.prioridad" [texto]="inc.prioridad"></app-status-badge>
            <app-status-badge [estado]="inc.estado" [texto]="inc.estado"></app-status-badge>
          </div>
          <a [routerLink]="['/incidencias', inc.id_incidencia]" class="inline-flex px-3 py-2 rounded-lg bg-amber-600 text-white text-sm font-bold">Ver incidencia</a>
        </article>
      </div>
      <nav class="flex gap-4" aria-label="Paginación de incidencias asignadas">
        <button *ngIf="pagina > 1" [disabled]="cargando" (click)="cargar(pagina - 1)">Anterior</button>
        <button *ngIf="pagina < totalPaginas" [disabled]="cargando" (click)="cargar(pagina + 1)">Siguiente</button>
      </nav>
    </div>
  `,
})
export class IncidenciasAsignadasComponent implements OnInit {
  private service = inject(IncidenciasService);
  private auth = inject(AuthService);
  private cdr = inject(ChangeDetectorRef);
  private destroyRef = inject(DestroyRef);
  incidencias: Incidencia[] = [];
  pagina = 1;
  totalPaginas = 0;
  cargando = false;
  error = '';

  ngOnInit(): void { this.cargar(); }

  cargar(page = 1): void {
    this.cargando = true;
    this.error = '';
    this.incidencias = [];
    this.service.listar({ id_responsable: Number(this.auth.obtenerUsuario()?.nro_usuario), page, limit: 20 })
      .pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
        next: res => {
          this.incidencias = res.data;
          this.pagina = res.pagination.page;
          this.totalPaginas = res.pagination.total_pages;
          this.cargando = false;
          this.cdr.markForCheck();
        },
        error: () => {
          this.error = 'No se pudieron cargar las incidencias asignadas.';
          this.cargando = false;
          this.cdr.markForCheck();
        },
      });
  }
}
