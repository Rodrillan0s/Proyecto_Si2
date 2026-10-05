import { TestBed } from '@angular/core/testing';
import { vi } from 'vitest';
import { BackupComponent } from './backup';
import { BackupService } from '../../services/backup';

function setup(overrides: Record<string, unknown> = {}) {
  const status = {
    configurado: true,
    control_disponible: true,
    requisitos: [] as string[],
    worker_activo: false,
    ultimo_latido: null,
    entorno: 'pruebas',
    mantenimiento: false,
    motivo: null,
    replica_remota: false,
    almacenamiento_persistente: true,
    restauracion_habilitada: true,
    requisitos_restauracion: [],
  };
  const config = {
    habilitada: false,
    alcance: 'sistema_completo',
    frecuencia: 'diario',
    hora: '02:00',
    zona_horaria: 'America/La_Paz',
    dia_semana: 0,
    dia_mes: 1,
    retencion_dias: 30,
  };
  const api = {
    estado: vi.fn(async () => status),
    historial: vi.fn(async () => ({ items: [], total: 0, pagina: 1 })),
    restauraciones: vi.fn(async () => []),
    programacion: vi.fn(async () => ({ configuracion: config, next_run: null })),
    crear: vi.fn(async (_scope: string, _key: string) => ({ id: 'job-123', estado: 'PENDIENTE' })),
    guardar: vi.fn(async () => ({ configuracion: config, next_run: null })),
    importar: vi.fn(),
    validar: vi.fn(),
    reautenticar: vi.fn(async () => ({ token: 'fresh' })),
    aplicar: vi.fn(),
    ...overrides,
  };
  TestBed.configureTestingModule({
    imports: [BackupComponent],
    providers: [{ provide: BackupService, useValue: api }],
  });
  const fixture = TestBed.createComponent(BackupComponent);
  fixture.detectChanges();
  return { api, fixture, component: fixture.componentInstance, status, config };
}

describe('Copias de respaldo: operaciones reales', () => {
  afterEach(() => TestBed.resetTestingModule());
  it('presenta requisitos del servidor y deshabilita creación cuando falta instalación', async () => {
    const { fixture, api, component, status } = setup();
    await fixture.whenStable();
    status.configurado = false;
    status.control_disponible = false;
    status.requisitos = ['Instala pg_dump'];
    await component.actualizar();
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Instala pg_dump');
    await component.crear();
    expect(api.crear).not.toHaveBeenCalled();
  });
  it('guardar usa el backend y no declara el worker operativo por guardar', async () => {
    const { fixture, api, component } = setup();
    await fixture.whenStable();
    await component.guardar();
    fixture.detectChanges();
    expect(api.guardar).toHaveBeenCalledWith(component.programacion);
    expect(fixture.nativeElement.textContent).toContain('Worker sin latido reciente');
  });
  it('un respaldo en cola conserva su etapa hasta que el worker termine', async () => {
    const { fixture, api, component } = setup();
    await fixture.whenStable();
    await component.crear();
    expect(api.crear).toHaveBeenCalledWith('sistema_completo', expect.any(String));
    expect(component.mensaje).toContain('en cola');
    expect(component.ocupada).toBe('');
  });
  it('mantiene la clave de idempotencia ante un fallo de conexión', async () => {
    const { fixture, api, component } = setup({ crear: vi.fn().mockRejectedValue({ status: 0 }) });
    await fixture.whenStable();
    await component.crear();
    await component.crear();
    expect(api.crear.mock.calls[0][1]).toBe(api.crear.mock.calls[1][1]);
    expect(component.error).toBe(true);
    expect(component.ocupada).toBe('');
  });
  it('exige la frase exacta y nueva autenticación; borra la contraseña', async () => {
    const selected = {
      id: 'restore-id',
      estado: 'VALIDADA',
      confirmacion_requerida: 'RESTAURAR TODOS LOS TENANTS restore-id',
      desafio: 'challenge',
    };
    const { fixture, api, component } = setup({
      aplicar: vi.fn(async () => ({ ...selected, aplicar_en: 'now' })),
    });
    await fixture.whenStable();
    component.seleccion = selected as any;
    component.identificador = 'admin';
    component.password = 'secret';
    component.confirmacion = 'sí';
    await component.aplicar();
    expect(api.reautenticar).not.toHaveBeenCalled();
    component.confirmacion = selected.confirmacion_requerida;
    await component.aplicar();
    expect(api.reautenticar).toHaveBeenCalledWith('admin', 'secret');
    expect(api.aplicar).toHaveBeenCalledWith(
      'restore-id',
      selected.confirmacion_requerida,
      'challenge',
      'fresh',
    );
    expect(component.password).toBe('');
    expect(component.mensaje).toContain('mantenimiento');
  });
  it('mantenimiento impide nuevos respaldos', async () => {
    const { fixture, api, component, status } = setup();
    await fixture.whenStable();
    status.mantenimiento = true;
    await component.actualizar();
    await component.crear();
    expect(api.crear).not.toHaveBeenCalled();
  });
  it('rechaza SQL antes de iniciar la importación', async () => {
    const { fixture, api, component } = setup();
    await fixture.whenStable();
    await component.importar({
      target: { files: [new File(['SQL'], 'dump.sql')], value: 'dump.sql' },
    } as unknown as Event);
    expect(api.importar).not.toHaveBeenCalled();
    expect(component.error).toBe(true);
  });
  it('limpia la contraseña también si reautenticar falla', async () => {
    const { fixture, component } = setup({
      reautenticar: vi.fn().mockRejectedValue({ status: 401 }),
    });
    await fixture.whenStable();
    component.seleccion = {
      id: 'id',
      estado: 'VALIDADA',
      confirmacion_requerida: 'CONFIRM',
      desafio: 'challenge',
    } as any;
    component.confirmacion = 'CONFIRM';
    component.identificador = 'admin';
    component.password = 'secret';
    await component.aplicar();
    expect(component.password).toBe('');
    expect(component.error).toBe(true);
  });
});
