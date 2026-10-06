import { TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { BehaviorSubject, of } from 'rxjs';
import { vi } from 'vitest';
import { AsistenteComponent } from './asistente';
import { AsistenteService } from '../../services/asistente.service';
import { AuthService } from '../../services/auth';
import { AiService } from '../../services/ai.service';
import { AssistantResponse, ReportesService } from '../../services/reportes.service';
import { ContextoOperativo } from '../../services/contexto-operativo';

describe('Asistente flotante', () => {
  let company: number;
  let role: string;
  let companies: BehaviorSubject<number>;
  let api: {
    catalog: ReturnType<typeof vi.fn>;
    assistant: ReturnType<typeof vi.fn>;
    create: ReturnType<typeof vi.fn>;
  };
  const crm = { consultarCRM: vi.fn(() => of({ respuesta: 'Dos prospectos.' })) };
  it('consulta con permiso de proveedor sin exigir un catalogo de Reportes', async () => {
    vi.spyOn(TestBed.inject(AuthService), 'hasPermission').mockImplementation(permission => permission === 'Visualizar_proveedores');
    const fixture = TestBed.createComponent(AsistenteComponent); fixture.detectChanges();
    TestBed.inject(AsistenteService).open(); fixture.detectChanges();
    expect(fixture.componentInstance.available).toBe(true);
    await fixture.componentInstance.send('Cuantos proveedores activos tenemos');
    expect(api.catalog).not.toHaveBeenCalled();
    expect(api.assistant).toHaveBeenCalled();
    fixture.destroy();
  });
  it('la obra seleccionada se envia separada del texto de stock', async () => {
    const fixture = TestBed.createComponent(AsistenteComponent); fixture.detectChanges();
    TestBed.inject(ContextoOperativo).seleccionar({ id_empresa: 7, id_obra: 9, nombre: 'Laguna', codigo: 'LAG' });
    await fixture.componentInstance.send('Stock de materiales');
    expect(api.assistant).toHaveBeenLastCalledWith('Stock de materiales', 7, undefined, undefined, 9);
    fixture.destroy();
  });
  beforeEach(() => {
    company = 7;
    role = 'ADMINISTRADOR_EMPRESA';
    companies = new BehaviorSubject(company);
    api = {
      catalog: vi.fn(async () => ({
        reportes: [],
        obras: [],
        acciones: ['Exportar_reportes'],
        id_empresa: company,
      })),
      assistant: vi.fn(async () => ({
        estado: 'ready',
        mensaje: 'Listo',
        respuesta: 'Stock actual',
        conversacion: 'c',
        ejecucion: { id: 'exec', estado: 'LISTO', resultado: null },
      })),
      create: vi.fn(async () => ({ id: 'with-work', estado: 'LISTO', resultado: null })),
    };
    TestBed.configureTestingModule({
      imports: [AsistenteComponent],
      providers: [
        provideRouter([]),
        { provide: ReportesService, useValue: api },
        { provide: AiService, useValue: crm },
        {
          provide: AuthService,
          useValue: {
            empresaActiva$: companies,
            obtenerIdEmpresaActiva: () => company,
            obtenerNombreEmpresaActiva: () => 'Empresa de prueba',
            obtenerRolNormalizado: () => role,
            hasPermission: () => true,
          },
        },
      ],
    });
    crm.consultarCRM.mockClear();
  });
  it('abre la burbuja, consulta datos y lleva el resultado al apartado Reportes', async () => {
    const fixture = TestBed.createComponent(AsistenteComponent);
    fixture.detectChanges();
    const root: HTMLElement = fixture.nativeElement;
    root.querySelector<HTMLButtonElement>('.launcher')!.click();
    fixture.detectChanges();
    expect(root.querySelector('[role="dialog"]')).not.toBeNull();
    await fixture.componentInstance.send('reporte de stock');
    fixture.detectChanges();
    expect(api.assistant).toHaveBeenCalledWith('reporte de stock', 7, undefined, undefined, undefined);
    expect(root.textContent).toContain('Stock actual');
    const navigate = vi.spyOn(TestBed.inject(Router), 'navigate').mockResolvedValue(true);
    await fixture.componentInstance.view({ id: 'exec', estado: 'LISTO', resultado: null });
    expect(navigate).toHaveBeenCalledWith(['/reportes'], { queryParams: { ejecucion: 'exec' } });
    expect(TestBed.inject(AsistenteService).opened()).toBe(false);
    fixture.destroy();
  });
  it('recibe una consulta del panel como borrador para revisión sin ejecutarla', () => {
    const fixture = TestBed.createComponent(AsistenteComponent);
    fixture.detectChanges();
    TestBed.inject(AsistenteService).open('consulta por revisar');
    fixture.detectChanges();
    expect(fixture.componentInstance.text).toBe('consulta por revisar');
    expect(api.assistant).not.toHaveBeenCalled();
    expect(crm.consultarCRM).not.toHaveBeenCalled();
    fixture.destroy();
  });
  it('descarta la respuesta del tenant anterior y permite una consulta nueva', async () => {
    const fixture = TestBed.createComponent(AsistenteComponent);
    fixture.detectChanges();
    let resolve!: (value: AssistantResponse) => void;
    api.assistant.mockImplementationOnce(
      () => new Promise<AssistantResponse>((done) => (resolve = done)),
    );
    const request = fixture.componentInstance.send('stock anterior');
    company = 8;
    companies.next(company);
    expect(fixture.componentInstance.busy).toBe(false);
    resolve({ estado: 'ready', mensaje: 'datos anteriores', conversacion: 'old' });
    await request;
    expect(fixture.componentInstance.messages).toEqual([]);
    await fixture.componentInstance.send('stock nuevo');
    expect(api.assistant).toHaveBeenLastCalledWith('stock nuevo', 8, undefined, undefined, undefined);
    fixture.destroy();
  });
  it('transmite la empresa seleccionada al asistente comercial', async () => {
    const fixture = TestBed.createComponent(AsistenteComponent);
    fixture.detectChanges();
    TestBed.inject(AsistenteService).open();
    fixture.detectChanges();
    await fixture.componentInstance.send('prospectos');
    expect(api.assistant).toHaveBeenCalledWith('prospectos', 7, undefined, undefined, undefined);
    expect(crm.consultarCRM).not.toHaveBeenCalled();
    fixture.destroy();
  });
  it('completa la obra elegida sin depender de que el intérprete recuerde una ambigüedad', async () => {
    const fixture = TestBed.createComponent(AsistenteComponent);
    fixture.detectChanges();
    await fixture.componentInstance.selectWork(
      {
        author: 'assistant',
        text: 'Elige obra',
        request: { reporte: 'comparativo_costos', filtros: {} },
      },
      { id_obra: 9, nombre: 'Obra nueve', codigo: '9' },
    );
    expect(api.assistant).toHaveBeenCalledWith('Obra nueve', 7, undefined, {
      reporte: 'comparativo_costos',
      filtros: { id_obra: 9 },
    });
    fixture.destroy();
  });
  it('exige selección de empresa para administrador global', async () => {
    company = 0;
    role = 'ADMINISTRADOR';
    const fixture = TestBed.createComponent(AsistenteComponent);
    fixture.detectChanges();
    await fixture.componentInstance.send('stock');
    expect(api.assistant).not.toHaveBeenCalled();
    expect(fixture.componentInstance.needsCompany).toBe(true);
    fixture.destroy();
  });
  it('mantiene el texto cuando el servidor falla para permitir un reintento', async () => {
    api.assistant.mockRejectedValueOnce({ status: 503 });
    const fixture = TestBed.createComponent(AsistenteComponent);
    fixture.detectChanges();
    await fixture.componentInstance.send('reporte de stock');
    expect(fixture.componentInstance.text).toBe('reporte de stock');
    expect(fixture.componentInstance.error).toContain('no está disponible');
    expect(fixture.componentInstance.busy).toBe(false);
    fixture.destroy();
  });
  it('conserva conversación y respuesta pendiente al abrir desde otra página', async () => {
    const fixture = TestBed.createComponent(AsistenteComponent);
    fixture.detectChanges();
    let resolve!: (value: AssistantResponse) => void;
    api.assistant.mockImplementationOnce(
      () => new Promise<AssistantResponse>((done) => (resolve = done)),
    );
    const request = fixture.componentInstance.send('stock');
    TestBed.inject(AsistenteService).open();
    fixture.detectChanges();
    resolve({ estado: 'ready', mensaje: 'stock anterior', conversacion: 'old' });
    await request;
    expect(fixture.componentInstance.messages.map((m) => m.text)).toEqual([
      'stock',
      'stock anterior',
    ]);
    expect(fixture.componentInstance.busy).toBe(false);
    fixture.destroy();
  });
  it('filtra el historial por tema sin perder contexto para preguntas posteriores', async () => {
    const fixture = TestBed.createComponent(AsistenteComponent);
    fixture.detectChanges();
    api.assistant.mockResolvedValueOnce({
      estado: 'ready',
      mensaje: 'Ventas',
      tema: 'crm',
      conversacion: 'unica',
    });
    await fixture.componentInstance.send('ventas');
    api.assistant.mockResolvedValueOnce({
      estado: 'ready',
      mensaje: 'Costos',
      tema: 'finanzas',
      conversacion: 'unica',
    });
    await fixture.componentInstance.send('ganancias');
    fixture.componentInstance.historyFilter = 'crm';
    expect(fixture.componentInstance.visibleMessages.map((m) => m.text)).toEqual([
      'ventas',
      'Ventas',
    ]);
    expect(fixture.componentInstance.messages.length).toBe(4);
    await fixture.componentInstance.send('¿Y los avances?');
    expect(api.assistant).toHaveBeenLastCalledWith('¿Y los avances?', 7, 'unica', undefined, undefined);
    expect(fixture.componentInstance.historyFilter).toBe('todos');
    fixture.destroy();
  });
  it('libera un micrófono autorizado después de cerrar la burbuja', async () => {
    const fixture = TestBed.createComponent(AsistenteComponent);
    fixture.detectChanges();
    const ui = TestBed.inject(AsistenteService);
    ui.open();
    fixture.detectChanges();
    let allow!: (stream: MediaStream) => void;
    const stop = vi.fn();
    const oldDevices = Object.getOwnPropertyDescriptor(navigator, 'mediaDevices');
    const oldRecognition = Object.getOwnPropertyDescriptor(window, 'SpeechRecognition');
    const oldWebkit = Object.getOwnPropertyDescriptor(window, 'webkitSpeechRecognition');
    Object.defineProperty(navigator, 'mediaDevices', {
      configurable: true,
      value: { getUserMedia: () => new Promise<MediaStream>((resolve) => (allow = resolve)) },
    });
    Object.defineProperty(window, 'SpeechRecognition', { configurable: true, value: undefined });
    Object.defineProperty(window, 'webkitSpeechRecognition', {
      configurable: true,
      value: undefined,
    });
    vi.stubGlobal('MediaRecorder', class {});
    try {
      const request = fixture.componentInstance.voice();
      ui.close();
      fixture.detectChanges();
      allow({ getTracks: () => [{ stop }] } as unknown as MediaStream);
      await request;
      expect(stop).toHaveBeenCalled();
      expect(fixture.componentInstance.listening).toBe(false);
    } finally {
      if (oldDevices) Object.defineProperty(navigator, 'mediaDevices', oldDevices);
      else Reflect.deleteProperty(navigator, 'mediaDevices');
      if (oldRecognition) Object.defineProperty(window, 'SpeechRecognition', oldRecognition);
      else Reflect.deleteProperty(window, 'SpeechRecognition');
      if (oldWebkit) Object.defineProperty(window, 'webkitSpeechRecognition', oldWebkit);
      else Reflect.deleteProperty(window, 'webkitSpeechRecognition');
      vi.unstubAllGlobals();
      fixture.destroy();
    }
  });
});
