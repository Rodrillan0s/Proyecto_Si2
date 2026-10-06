import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ReportesService } from './reportes.service';

describe('Reportes: contratos compartidos', () => {
  let api: ReportesService;
  let http: HttpTestingController;
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    api = TestBed.inject(ReportesService);
    http = TestBed.inject(HttpTestingController);
  });
  afterEach(() => http.verify());
  it('transporta la obra como contexto separado sin alterar la pregunta', async () => {
    const result = api.assistant('Stock de materiales', 7, undefined, undefined, 9);
    const request = http.expectOne(r => r.url.endsWith('/api/ai/consulta'));
    expect(request.request.body.texto).toBe('Stock de materiales');
    expect(request.request.body.id_obra_contexto).toBe(9);
    request.flush({ estado: 'ready', mensaje: 'Listo' });
    await result;
  });
  it('consulta al asistente con empresa y conversación mediante el contrato común', async () => {
    const result = api.assistant('reporte de stock', 7, 'conversation-id');
    const request = http.expectOne((r) => r.url.endsWith('/api/ai/consulta'));
    expect(request.request.params.get('id_empresa')).toBe('7');
    expect(request.request.body).toEqual({
      texto: 'reporte de stock',
      conversacion: 'conversation-id',
    });
    request.flush({
      estado: 'ready',
      mensaje: 'Listo',
      conversacion: 'conversation-id',
      ejecucion: { id: 'exec' },
    });
    expect((await result).ejecucion?.id).toBe('exec');
  });
  it('envía el tenant seleccionado sin añadir SQL a la solicitud', async () => {
    const result = api.create({ reporte: 'incidencias', filtros: { id_obra: 9 } }, 7);
    const req = http.expectOne((r) => r.url.endsWith('/api/reportes/ejecuciones'));
    expect(req.request.params.get('id_empresa')).toBe('7');
    expect(req.request.body).toEqual({ reporte: 'incidencias', filtros: { id_obra: 9 } });
    req.flush({ id: 'exec', estado: 'LISTO', resultado: null });
    expect((await result).id).toBe('exec');
  });
  it('descarga por autenticación HTTP el archivo del mismo resultado', async () => {
    const result = api.download('exec', 'xlsx');
    const generate = http.expectOne((r) => r.url.endsWith('/exec/exportaciones'));
    expect(generate.request.params.get('formato')).toBe('xlsx');
    generate.flush({ id: 'file', nombre: 'stock.xlsx' });
    await Promise.resolve();
    const download = http.expectOne((r) => r.url.endsWith('/archivos/file'));
    expect(download.request.responseType).toBe('blob');
    download.flush(new Blob(['xlsx']));
    expect((await result).name).toBe('stock.xlsx');
  });
  it('mantiene una identidad de envío estable para reintentar', async () => {
    const result = api.send('exec', [2], ['pdf'], 'stable-key');
    const req = http.expectOne((r) => r.url.endsWith('/exec/envios'));
    expect(req.request.headers.get('Idempotency-Key')).toBe('stable-key');
    expect(req.request.body.destinatarios).toEqual([2]);
    req.flush({ estado: 'PENDIENTE' });
    await result;
  });
});
