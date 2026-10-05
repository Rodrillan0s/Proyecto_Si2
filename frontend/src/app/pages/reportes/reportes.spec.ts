import { TestBed } from '@angular/core/testing';
import { BehaviorSubject } from 'rxjs';
import { vi } from 'vitest';
import { AuthService } from '../../services/auth';
import { ReportesService, Execution, ReportResult } from '../../services/reportes.service';
import { ReportesComponent } from './reportes';

describe('Reportes: cambio de empresa durante una consulta', () => {
  it('borra conversación y descarta el resultado tardío del tenant anterior', async () => {
    let company = 7;
    const selected = new BehaviorSubject({ id_empresa: company });
    let finish!: (value: Execution) => void;
    const pending = new Promise<Execution>((resolve) => (finish = resolve));
    const api = {
      catalog: vi.fn(async () => ({
        reportes: [
          {
            id: 'stock',
            titulo: 'Stock',
            descripcion: 'Actual',
            fechas: false,
            requiere_obra: false,
          },
        ],
        obras: [],
        acciones: ['Visualizar_reportes'],
        id_empresa: company,
      })),
      history: vi.fn(async () => []),
      create: vi.fn(() => pending),
    };
    TestBed.configureTestingModule({
      imports: [ReportesComponent],
      providers: [
        {
          provide: AuthService,
          useValue: { empresaActiva$: selected, obtenerIdEmpresaActiva: () => company },
        },
        { provide: ReportesService, useValue: api },
      ],
    });
    const fixture = TestBed.createComponent(ReportesComponent);
    fixture.detectChanges();
    await fixture.whenStable();
    const component = fixture.componentInstance;
    await vi.waitFor(() => expect(component.loading).toBe(false));
    component.texto = 'Datos de empresa anterior';
    component.generate();
    expect(api.create).toHaveBeenCalled();
    company = 8;
    selected.next({ id_empresa: company });
    await Promise.resolve();
    finish({ id: 'tenant-anterior', estado: 'LISTO', resultado: null });
    await Promise.resolve();
    await Promise.resolve();
    expect(component.execution).toBeUndefined();
    expect(component.response).toBeUndefined();
    expect(component.texto).toBe('');
    expect(component.catalog.id_empresa).toBe(8);
    fixture.destroy();
  });
});

describe('Reportes: validaciones y operaciones de entrega', () => {
  let company: number;
  let companies: BehaviorSubject<number>;
  let api: Record<string, ReturnType<typeof vi.fn>>;
  const result: ReportResult = {
    titulo: 'Stock',
    corte: '2026-10-04T18:00:00Z',
    columnas: [],
    filas: [],
    resumen: {},
    advertencias: [],
    recomendaciones: [],
    solicitud: { reporte: 'stock', filtros: {} },
  };
  beforeEach(() => {
    company = 7;
    companies = new BehaviorSubject(company);
    api = {
      catalog: vi.fn(async () => ({
        reportes: [
          {
            id: 'stock',
            titulo: 'Stock',
            descripcion: 'Actual',
            fechas: false,
            requiere_obra: false,
          },
          {
            id: 'incidencias',
            titulo: 'Incidencias',
            descripcion: 'Actual',
            fechas: true,
            requiere_obra: false,
          },
          {
            id: 'comparativo_costos',
            titulo: 'Costos',
            descripcion: 'Actual',
            fechas: false,
            requiere_obra: true,
          },
        ],
        obras: [],
        acciones: ['Visualizar_reportes', 'Enviar_reportes', 'Programar_reportes'],
        id_empresa: company,
      })),
      history: vi.fn(async () => []),
      recipients: vi.fn(async () => [{ id_usuario: 2, nombre: 'Receptor' }]),
      schedules: vi.fn(async () => []),
      create: vi.fn(async () => ({ id: 'exec', estado: 'LISTO', resultado: result })),
      schedule: vi.fn(async () => ({})),
      send: vi.fn(async () => ({})),
      deliveries: vi.fn(async () => []),
    };
    TestBed.configureTestingModule({
      imports: [ReportesComponent],
      providers: [
        {
          provide: AuthService,
          useValue: { empresaActiva$: companies, obtenerIdEmpresaActiva: () => company },
        },
        { provide: ReportesService, useValue: api },
      ],
    });
  });
  async function prepare() {
    const fixture = TestBed.createComponent(ReportesComponent);
    fixture.detectChanges();
    await vi.waitFor(() => expect(fixture.componentInstance.loading).toBe(false));
    return fixture;
  }
  it('rechaza obra ausente y fechas invertidas antes de consultar al servidor', async () => {
    const fixture = await prepare();
    const component = fixture.componentInstance;
    component.selected = 'comparativo_costos';
    component.generate();
    expect(component.error).toContain('necesita una obra');
    component.selected = 'incidencias';
    component.desde = '2026-10-05';
    component.hasta = '2026-10-01';
    component.generate();
    expect(api['create']).not.toHaveBeenCalled();
    expect(component.error).toContain('fecha inicial');
    fixture.destroy();
  });
  it('envía fechas y presentación en consulta y programación', async () => {
    const fixture = await prepare();
    const component = fixture.componentInstance;
    component.selected = 'incidencias';
    component.desde = '2026-09-01';
    component.hasta = '2026-09-30';
    component.customTitle = 'Septiembre';
    component.orientation = 'vertical';
    component.customColumns = true;
    component.selectedColumns = ['titulo', 'estado'];
    component.sortField = 'titulo';
    component.sortOrder = 'desc';
    component.generate();
    await vi.waitFor(() => expect(component.busy).toBe(false));
    const request = api['create'].mock.calls[0][0];
    expect(request.filtros).toEqual({ desde: '2026-09-01', hasta: '2026-09-30' });
    expect(request.presentacion).toEqual({
      titulo: 'Septiembre',
      orientacion: 'vertical',
      columnas: ['titulo', 'estado'],
      ordenar_por: 'titulo',
      orden: 'desc',
    });
    component.receiverIds = [2];
    component.saveSchedule();
    await vi.waitFor(() => expect(component.busy).toBe(false));
    expect(api['schedule'].mock.calls[0][0].solicitud).toEqual(request);
    fixture.destroy();
  });
  it('permite rango abierto y bloquea selección de columnas vacía', async () => {
    const fixture = await prepare();
    const component = fixture.componentInstance;
    component.selected = 'incidencias';
    component.desde = '2026-09-01';
    expect(component.filters()).toEqual({ desde: '2026-09-01' });
    component.customColumns = true;
    component.generate();
    expect(api['create']).not.toHaveBeenCalled();
    expect(component.error).toContain('una columna');
    fixture.destroy();
  });
  it('rechaza horario, zona y día inválidos sin crear programaciones', async () => {
    const fixture = await prepare();
    const component = fixture.componentInstance;
    component.receiverIds = [2];
    component.hour = '25:00';
    component.saveSchedule();
    expect(component.error).toContain('hora válida');
    component.hour = '08:00';
    component.timezone = 'zona-inexistente';
    component.saveSchedule();
    expect(component.error).toContain('zona horaria');
    component.timezone = 'America/La_Paz';
    component.frequency = 'semanal';
    component.day = 8;
    component.saveSchedule();
    expect(api['schedule']).not.toHaveBeenCalled();
    expect(component.error).toContain('día');
    fixture.destroy();
  });
  it('descarta una programación terminada después de cambiar empresa', async () => {
    const fixture = await prepare();
    const component = fixture.componentInstance;
    let finish!: (value: object) => void;
    api['schedule'].mockImplementationOnce(() => new Promise((resolve) => (finish = resolve)));
    component.receiverIds = [2];
    component.saveSchedule();
    expect(api['schedule']).toHaveBeenCalled();
    company = 8;
    companies.next(company);
    finish({});
    await vi.waitFor(() => expect(component.loading).toBe(false));
    expect(component.notice).toBe('');
    expect(component.tab).toBe('generar');
    expect(component.receiverIds).toEqual([]);
    fixture.destroy();
  });
  it('reutiliza la clave tras un fallo de envío y la cambia al seleccionar otro formato', async () => {
    const fixture = await prepare();
    const component = fixture.componentInstance;
    component.execution = { id: 'exec', estado: 'LISTO', resultado: result };
    component.receiverIds = [2];
    api['send'].mockRejectedValueOnce({ status: 0 });
    component.send();
    await vi.waitFor(() => expect(component.busy).toBe(false));
    const key = api['send'].mock.calls[0][3];
    component.send();
    await vi.waitFor(() => expect(component.busy).toBe(false));
    expect(api['send'].mock.calls[1][3]).toBe(key);
    component.formato = 'xlsx';
    component.send();
    await vi.waitFor(() => expect(component.busy).toBe(false));
    expect(api['send'].mock.calls[2][3]).not.toBe(key);
    fixture.destroy();
  });
});
