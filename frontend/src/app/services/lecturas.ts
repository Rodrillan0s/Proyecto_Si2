import { DestroyRef, Injectable, inject } from '@angular/core';
import { MonoTypeOperatorFunction, Observable, Subject, defer, finalize, of, shareReplay, takeUntil, tap } from 'rxjs';
import { AuthService } from './auth';

interface CacheEntry {
  data: unknown;
  expiresAt: number;
}

/**
 * Comparte lecturas en vuelo y ofrece caché en memoria con TTL configurable.
 * Aísla estrictamente por empresa y token (se limpia automáticamente al cambiar de tenant o cerrar sesión).
 */
@Injectable({ providedIn: 'root' })
export class LecturasCompartidas {
  private auth = inject(AuthService);
  private token: string | null = null;
  private pending = new Map<string, Observable<unknown>>();
  private cache = new Map<string, CacheEntry>();

  constructor() {
    this.auth.empresaActiva$.subscribe(() => this.limpiarTodo());
  }

  obtener<T>(key: string, source: () => Observable<T>, ttlMs: number = 0): Observable<T> {
    return defer(() => {
      const token = this.auth.obtenerToken();
      if (token !== this.token) {
        this.limpiarTodo();
        this.token = token;
      }
      const scope = `${this.auth.obtenerIdEmpresaActiva() ?? 'global'}:${key}`;

      // 1. Si hay caché vigente (ttlMs > 0), responder inmediatamente desde memoria
      if (ttlMs > 0) {
        const cached = this.cache.get(scope);
        if (cached && Date.now() < cached.expiresAt) {
          return of(cached.data as T);
        }
      }

      // 2. Si ya hay una lectura idéntica en vuelo, reutilizarla (deduplicación simultánea)
      const existing = this.pending.get(scope);
      if (existing) return existing as Observable<T>;

      // 3. Crear petición y guardar en caché si ttlMs > 0
      const request = defer(source).pipe(
        tap((data: T) => {
          if (ttlMs > 0) {
            this.cache.set(scope, { data, expiresAt: Date.now() + ttlMs });
          }
        }),
        finalize(() => {
          if (this.pending.get(scope) === request) {
            this.pending.delete(scope);
          }
        }),
        shareReplay({ bufferSize: 1, refCount: true })
      );

      this.pending.set(scope, request);
      return request;
    });
  }

  /** Invalida una clave específica o un prefijo de recurso */
  limpiar(key: string): void {
    const scopePrefix = `${this.auth.obtenerIdEmpresaActiva() ?? 'global'}:${key}`;
    for (const k of Array.from(this.cache.keys())) {
      if (k === scopePrefix || k.startsWith(scopePrefix)) {
        this.cache.delete(k);
      }
    }
    for (const k of Array.from(this.pending.keys())) {
      if (k === scopePrefix || k.startsWith(scopePrefix)) {
        this.pending.delete(k);
      }
    }
  }

  /** Invalida toda la memoria caché */
  limpiarTodo(): void {
    this.cache.clear();
    this.pending.clear();
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
