import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { BackupService, BackupSchedule } from './backup';

describe('Backup: contratos del plano de control', () => {
  let api: BackupService;
  let http: HttpTestingController;
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    api = TestBed.inject(BackupService);
    http = TestBed.inject(HttpTestingController);
  });
  afterEach(() => http.verify());
  it('encola una copia global con idempotencia y sin empresa', async () => {
    const result = api.crear('base_datos', 'key-123456');
    const req = http.expectOne((r) => r.url.endsWith('/api/backup/ejecuciones'));
    expect(req.request.body).toEqual({ alcance: 'base_datos' });
    expect(req.request.headers.get('Idempotency-Key')).toBe('key-123456');
    expect(req.request.params.has('id_empresa')).toBe(false);
    req.flush({ id: 'job', estado: 'PENDIENTE' });
    expect((await result).estado).toBe('PENDIENTE');
  });
  it('guarda la programación real con zona y retención', async () => {
    const config: BackupSchedule = {
      habilitada: true,
      alcance: 'base_datos',
      frecuencia: 'semanal',
      hora: '02:00',
      zona_horaria: 'America/La_Paz',
      dia_semana: 2,
      dia_mes: 1,
      retencion_dias: 30,
    };
    const result = api.guardar(config);
    const req = http.expectOne((r) => r.url.endsWith('/programacion'));
    expect(req.request.method).toBe('PUT');
    expect(req.request.body).toEqual(config);
    req.flush({ configuracion: config, next_run: '2026-10-07T06:00:00Z' });
    expect((await result).next_run).toBeTruthy();
  });
  it('importa el paquete como stream binario autenticado', async () => {
    const file = new File(['encrypted'], 'test.obratec');
    const result = api.importar(file);
    const req = http.expectOne((r) => r.url.endsWith('/importaciones'));
    expect(req.request.body).toBe(file);
    expect(req.request.headers.get('Content-Type')).toBe('application/octet-stream');
    req.flush({ id: 'archive' });
    expect((await result).id).toBe('archive');
  });
  it('la aplicación vincula desafío y nueva autenticación a una restauración', async () => {
    const result = api.aplicar(
      'restore-id',
      'RESTAURAR TODOS LOS TENANTS restore-id',
      'challenge',
      'fresh-token',
    );
    const req = http.expectOne((r) => r.url.endsWith('/restauraciones/restore-id/aplicar'));
    expect(req.request.body).toEqual({
      confirmacion: 'RESTAURAR TODOS LOS TENANTS restore-id',
      desafio: 'challenge',
      token_reautenticacion: 'fresh-token',
    });
    req.flush({ estado: 'VALIDADA', aplicar_en: 'now' });
    expect((await result).aplicar_en).toBe('now');
  });
  it('solicita el PAR mediante POST sin enviar objeto, empresa ni URL', async () => {
    const result = api.descargar('9223372036854775807');
    const req = http.expectOne((r) => r.url.endsWith('/ejecuciones/9223372036854775807/archivo'));
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({});
    expect(req.request.responseType).toBe('json');
    req.flush({ id: '2', estado: 'PENDIENTE', url: null }, { status: 202, statusText: 'Accepted' });
    expect((await result).url).toBeNull();
  });
  it('consulta la solicitud autenticada sin descargar el objeto con HttpClient', async () => {
    const result = api.descarga('2');
    const req = http.expectOne((r) => r.url.endsWith('/descargas/2'));
    expect(req.request.method).toBe('GET');
    req.flush({ id: '2', estado: 'COMPLETADO', url: 'https://objectstorage.example/p/token' });
    expect((await result).estado).toBe('COMPLETADO');
  });
  it('el despachador solo solicita el encolado de una ocurrencia vencida', async () => {
    const result = api.despachar();
    const req = http.expectOne((r) => r.url.endsWith('/programacion/ejecutar'));
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({});
    req.flush({ encolado: false, trabajo: null });
    expect((await result).encolado).toBe(false);
  });
});
