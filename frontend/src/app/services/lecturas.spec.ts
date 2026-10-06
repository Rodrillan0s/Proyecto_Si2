import { TestBed } from '@angular/core/testing';
import { provideHttpClient, HttpClient } from '@angular/common/http';
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing';
import { BehaviorSubject, Subject } from 'rxjs';
import { AuthService } from './auth';
import { ContextoOperativo } from './contexto-operativo';
import { LecturasCompartidas, LecturasVigentes } from './lecturas';
import { DestroyRef } from '@angular/core';

describe('Lecturas y contexto sin cambios de API', () => {
  let company: number | null; let token: string; let companies: BehaviorSubject<unknown>;
  let http: HttpClient; let requests: HttpTestingController;
  beforeEach(() => {
    company = 7; token = 'session-a'; companies = new BehaviorSubject<unknown>(null);
    TestBed.configureTestingModule({ providers: [provideHttpClient(), provideHttpClientTesting(), {
      provide: AuthService, useValue: { empresaActiva$: companies, obtenerToken: () => token, obtenerIdEmpresaActiva: () => company },
    }] });
    http = TestBed.inject(HttpClient); requests = TestBed.inject(HttpTestingController);
  });
  afterEach(() => requests.verify());
  it('comparte dos lecturas simultáneas y vuelve a consultar tras completar', () => {
    const shared = TestBed.inject(LecturasCompartidas); const values: unknown[] = [];
    shared.obtener('obras', () => http.get('/obras')).subscribe(value => values.push(value));
    shared.obtener('obras', () => http.get('/obras')).subscribe(value => values.push(value));
    requests.expectOne('/obras').flush([1]); expect(values).toEqual([[1], [1]]);
    shared.obtener('obras', () => http.get('/obras')).subscribe(); requests.expectOne('/obras').flush([2]);
  });
  it('no comparte solicitudes entre sesiones o empresas', () => {
    const shared = TestBed.inject(LecturasCompartidas);
    shared.obtener('datos', () => http.get('/datos')).subscribe(); const a = requests.expectOne('/datos');
    company = 8; companies.next(8);
    shared.obtener('datos', () => http.get('/datos')).subscribe(); const b = requests.expectOne('/datos');
    token = 'session-b'; shared.obtener('datos', () => http.get('/datos')).subscribe(); const c = requests.expectOne('/datos');
    a.flush('a'); b.flush('b'); c.flush('c');
  });
  it('un error se elimina y permite reintentar', () => {
    const shared = TestBed.inject(LecturasCompartidas);
    shared.obtener('datos', () => http.get('/datos')).subscribe({ error: () => {} });
    requests.expectOne('/datos').flush({}, { status: 503, statusText: 'Unavailable' });
    shared.obtener('datos', () => http.get('/datos')).subscribe(); requests.expectOne('/datos').flush([]);
  });
  it('cancela respuestas sustituidas y al destruir sin tocar escrituras', () => {
    let dispose!: () => void;
    const scope = new LecturasVigentes({ onDestroy: (fn: () => void) => { dispose = fn; return () => {}; } } as DestroyRef);
    const a = new Subject<number>(); const b = new Subject<number>(); const values: number[] = [];
    a.pipe(scope.reemplazar('lista')).subscribe(value => values.push(value));
    b.pipe(scope.reemplazar('lista')).subscribe(value => values.push(value));
    a.next(1); b.next(2); dispose(); b.next(3); expect(values).toEqual([2]);
  });
  it('el contexto rechaza obra de otra empresa y elimina selección al cambiar empresa', () => {
    const context = TestBed.inject(ContextoOperativo);
    expect(context.seleccionar({ id_obra: 2, id_empresa: 8, nombre: 'Ajena', codigo: 'B' })).toBe(false);
    context.seleccionar({ id_obra: 1, id_empresa: 7, nombre: 'Obra', codigo: 'A' });
    companies.next(7); expect(context.obra?.id_obra).toBe(1);
    company = 8; companies.next(8); expect(context.obra).toBeNull();
  });
  it('el stream operativo emite una sola inicialización y un cambio efectivo', () => {
    const context = TestBed.inject(ContextoOperativo); const values: unknown[] = [];
    context.operativo$.subscribe(value => values.push(value)); companies.next(7);
    company = 8; companies.next(8); expect(values).toEqual([{ empresa: 7, obra: null }, { empresa: 8, obra: null }]);
  });
});
