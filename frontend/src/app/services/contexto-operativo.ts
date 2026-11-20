import { DestroyRef, Injectable, inject } from '@angular/core';
import { BehaviorSubject, combineLatest, distinctUntilChanged, map, shareReplay } from 'rxjs';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { AuthService } from './auth';
import { Proyecto } from './proyectos';
export type ObraContexto = Pick<Proyecto, 'id_obra' | 'id_empresa' | 'nombre' | 'codigo'>;

@Injectable({ providedIn: 'root' })
export class ContextoOperativo {
  private auth = inject(AuthService);
  private destroy = inject(DestroyRef);
  private selected = new BehaviorSubject<ObraContexto | null>(null);
  readonly obra$ = this.selected.asObservable();
  readonly empresa$ = this.auth.empresaActiva$.pipe(map(() => this.auth.obtenerIdEmpresaActiva()), distinctUntilChanged(), shareReplay({ bufferSize: 1, refCount: true }));
  readonly operativo$ = combineLatest([this.empresa$, this.obra$]).pipe(
    map(() => ({ empresa: this.auth.obtenerIdEmpresaActiva(), obra: this.obra?.id_obra ?? null })),
    distinctUntilChanged((a, b) => a.empresa === b.empresa && a.obra === b.obra),
    shareReplay({ bufferSize: 1, refCount: true }),
  );
  private dirty = new Set<() => boolean>();
  private writing = new Set<() => boolean>();
  get obra() { return this.selected.value; }
  constructor() {
    this.auth.obtenerIdEmpresaActiva();
    this.empresa$.pipe(takeUntilDestroyed(this.destroy)).subscribe(() => this.selected.next(null));
  }
  proteger(check: () => boolean, destroy: DestroyRef) { this.dirty.add(check); destroy.onDestroy(() => this.dirty.delete(check)); }
  protegerEscritura(check: () => boolean, destroy: DestroyRef) { this.writing.add(check); destroy.onDestroy(() => this.writing.delete(check)); }
  confirmarCambio() {
    if ([...this.writing].some(check => check())) { window.alert('Espera a que termine la operación antes de cambiar de contexto.'); return false; }
    return ![...this.dirty].some(check => check()) || window.confirm('Hay un formulario abierto. ¿Descartar sus cambios y cambiar de contexto?');
  }
  seleccionar(obra: ObraContexto | null) {
    const company = this.auth.obtenerIdEmpresaActiva();
    if (obra && (!obra.id_obra || !obra.id_empresa || (company && Number(obra.id_empresa) !== company))) return false;
    if (this.obra?.id_obra === obra?.id_obra && this.obra?.nombre === obra?.nombre) return true;
    this.selected.next(obra);
    return true;
  }
}
