import { DestroyRef, Injectable, inject } from '@angular/core';
import { MonoTypeOperatorFunction, Observable, Subject, defer, finalize, shareReplay, takeUntil } from 'rxjs';
import { AuthService } from './auth';

/** Comparte solo lecturas pendientes. No conserva respuestas ni cambia contratos HTTP. */
@Injectable({ providedIn: 'root' })
export class LecturasCompartidas {
  private auth = inject(AuthService);
  private token: string | null = null;
  private pending = new Map<string, Observable<unknown>>();
  constructor() { this.auth.empresaActiva$.subscribe(() => this.pending.clear()); }
  obtener<T>(key: string, source: () => Observable<T>): Observable<T> {
    return defer(() => {
      const token = this.auth.obtenerToken();
      if (token !== this.token) { this.pending.clear(); this.token = token; }
      const scope = `${this.auth.obtenerIdEmpresaActiva() ?? 'global'}:${key}`;
      const existing = this.pending.get(scope);
      if (existing) return existing as Observable<T>;
      const request = defer(source).pipe(
        finalize(() => { if (this.pending.get(scope) === request) this.pending.delete(scope); }),
        shareReplay({ bufferSize: 1, refCount: true }),
      );
      this.pending.set(scope, request);
      return request;
    });
  }
}

/** Cancela la lectura anterior del mismo recurso, y todas al destruir la página. */
export class LecturasVigentes {
  private pending = new Map<string, Subject<void>>();
  private destroyed = new Subject<void>();
  constructor(destroy: DestroyRef) { destroy.onDestroy(() => { this.cancelar(); this.destroyed.next(); this.destroyed.complete(); }); }
  reemplazar<T>(key: string): MonoTypeOperatorFunction<T> {
    this.pending.get(key)?.next();
    this.pending.get(key)?.complete();
    const cancel = new Subject<void>();
    this.pending.set(key, cancel);
    return source => source.pipe(takeUntil(cancel), takeUntil(this.destroyed));
  }
  cancelar() { this.pending.forEach(subject => { subject.next(); subject.complete(); }); this.pending.clear(); }
}
