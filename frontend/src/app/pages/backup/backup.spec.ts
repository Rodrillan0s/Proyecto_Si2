import { TestBed } from '@angular/core/testing';
import { vi } from 'vitest';
import { BackupComponent } from './backup';
import { BackupService } from '../../services/backup';

function setup(overrides: Record<string, unknown> = {}) {
  const status = {
    configurado: true,
    control_disponible: true,
    cola_disponible: true,
    requisitos: [] as string[],
    worker_activo: false,
    ultimo_latido: null,
    entorno: 'pruebas',
    mantenimiento: false,
    motivo: null,
    replica_remota: false,
    heartbeat_integrado: false,
    almacenamiento: 'oci_object_storage',
    descarga_habilitada: false,
    requisitos_descarga: [],
    importacion_habilitada: false,
    advertencias: [],
    restauracion_habilitada: true,
    requisitos_restauracion: [],
  };
  const config = {
    habilitada: false,
    alcance: 'base_datos',
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
    despachar: vi.fn(async () => ({ encolado: false, trabajo: null })),
    descargar: vi.fn(),
    descarga: vi.fn(),
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
  afterEach(() => { TestBed.resetTestingModule(); vi.restoreAllMocks(); vi.useRealTimers(); });
  it('presenta requisitos del servidor y deshabilita creación cuando falta instalación', async () => {
    const { fixture, api, component, status } = setup();
    await fixture.whenStable();
    status.configurado = false;
    status.control_disponible = false;
    status.requisitos = ['Configura permisos de backup_jobs'];
    await component.actualizar();
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Configura permisos de backup_jobs');
    await component.crear();
    expect(api.crear).not.toHaveBeenCalled();
  });
  it('guardar usa el backend y no declara el worker operativo por guardar', async () => {
    const { fixture, api, component } = setup();
    await fixture.whenStable();
    await component.guardar();
    fixture.detectChanges();
    expect(api.guardar).toHaveBeenCalledWith(component.programacion);
    expect(fixture.nativeElement.textContent).toContain('Heartbeat pendiente de integración');
  });
  it('un respaldo en cola conserva su etapa hasta que el worker termine', async () => {
    const { fixture, api, component } = setup();
    await fixture.whenStable();
    await component.crear();
    expect(api.crear).toHaveBeenCalledWith('base_datos', expect.any(String));
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
    expect(component.mensaje).toContain('confirmada');
  });
  it('mantenimiento impide nuevos respaldos', async () => {
    const { fixture, api, component, status } = setup();
    await fixture.whenStable();
    status.mantenimiento = true;
    await component.actualizar();
    await component.crear();
    expect(api.crear).not.toHaveBeenCalled();
  });
  it('no inicia importaciones legacy cuando la capacidad está retirada', async () => {
    const { fixture, api, component } = setup();
    await fixture.whenStable();
    await component.importar({
      target: { files: [new File(['SQL'], 'dump.sql')], value: 'dump.sql' },
    } as unknown as Event);
    expect(api.importar).not.toHaveBeenCalled();
    expect(component.error).toBe(false);
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
  it('no permite restaurar ni descargar cuando el backend declara la capacidad pendiente', async () => {
    const { fixture, api, component, status } = setup();
    await fixture.whenStable();
    status.restauracion_habilitada = false;
    await component.actualizar();
    component.seleccion = { id: '1', estado: 'VALIDADA', confirmacion_requerida: 'CONFIRM' } as any;
    component.confirmacion = 'CONFIRM';
    component.identificador = 'admin';
    component.password = 'secret';
    await component.aplicar();
    await component.validar('1');
    expect(api.reautenticar).not.toHaveBeenCalled();
    expect(api.validar).not.toHaveBeenCalled();
    await component.descargar({ id: '1', estado: 'COMPLETADO' } as any);
    expect(api.descargar).not.toHaveBeenCalled();
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('producción no está habilitada');
  });
  it('consulta estados y metadatos reales de la cola sin truncar el ID bigint', async () => {
    const row = { id: '9223372036854775807', estado: 'COMPLETADO', origen: 'MANUAL', solicitud: { alcance: 'base_datos' },
      etapa: 'Completado', object_name: 'obras/test.dump', sha256: 'a'.repeat(64), size_bytes: 2048 };
    const { fixture, component } = setup({ historial: vi.fn(async () => ({ items: [row], total: 1, pagina: 1 })) });
    await fixture.whenStable();
    await vi.waitFor(() => expect(component.historial.length).toBe(1));
    fixture.detectChanges();
    const text = fixture.nativeElement.textContent;
    expect(text).toContain('9223372036854775807');
    expect(text).toContain('COMPLETADO');
    expect(text).toContain('obras/test.dump');
  });
  it('espera al daemon y ofrece el enlace sin persistirlo ni enviar JWT a OCI', async () => {
    const ready = { id: '2', job_id: '9223372036854775807', estado: 'COMPLETADO',
      url: 'https://objectstorage.sa-saopaulo-1.oraclecloud.com/p/test/n/ns/b/bucket/o/test.dump',
      expira_en: new Date(Date.now() + 600000).toISOString(), nombre: 'test.dump', error: null };
    const { fixture, api, component, status } = setup({
      descargar: vi.fn(async () => ({ id: '2', estado: 'PENDIENTE', url: null })),
      descarga: vi.fn(async () => ready),
    });
    await fixture.whenStable();
    status.descarga_habilitada = true;
    await component.actualizar();
    vi.useFakeTimers();
    const click = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {});
    const storage = vi.spyOn(Storage.prototype, 'setItem');
    const task = component.descargar({ id: ready.job_id, estado: 'COMPLETADO' } as any);
    await vi.advanceTimersByTimeAsync(2000);
    await task;
    fixture.detectChanges();
    expect(api.descargar).toHaveBeenCalledWith(ready.job_id);
    expect(api.descarga).toHaveBeenCalledWith('2');
    expect(component.descargaLista?.url).toBe(ready.url);
    expect(click).toHaveBeenCalledOnce();
    expect(storage).not.toHaveBeenCalled();
    const link = fixture.nativeElement.querySelector('a[referrerpolicy="no-referrer"]');
    expect(link.getAttribute('href')).toBe(ready.url);
    expect(link.getAttribute('rel')).toBe('noopener noreferrer');
    await vi.advanceTimersByTimeAsync(600000);
    expect(component.descargaLista).toBeNull();
  });
  it('deja de consultar y abrir enlaces al abandonar la pantalla', async () => {
    const { fixture, api, component, status } = setup({
      descargar: vi.fn(async () => ({ id: '2', estado: 'PROCESANDO', url: null })),
    });
    await fixture.whenStable();
    status.descarga_habilitada = true;
    await component.actualizar();
    vi.useFakeTimers();
    const click = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {});
    const task = component.descargar({ id: '1', estado: 'COMPLETADO' } as any);
    await vi.advanceTimersByTimeAsync(1);
    fixture.destroy();
    await task;
    expect(api.descarga).not.toHaveBeenCalled();
    expect(click).not.toHaveBeenCalled();
    expect(component.descargaLista).toBeNull();
  });
  it('limita la espera y permite reintentar sin declarar la descarga completada', async () => {
    const pending = { id: '2', estado: 'PENDIENTE', url: null };
    const { fixture, api, component, status } = setup({ descargar: vi.fn(async () => pending), descarga: vi.fn(async () => pending) });
    await fixture.whenStable();
    status.descarga_habilitada = true;
    await component.actualizar();
    vi.useFakeTimers();
    const task = component.descargar({ id: '1', estado: 'COMPLETADO' } as any);
    await vi.advanceTimersByTimeAsync(122000);
    await task;
    expect(api.descarga.mock.calls.length).toBeLessThanOrEqual(60);
    expect(component.error).toBe(true);
    expect(component.mensaje).toContain('misma solicitud');
    expect(component.descargaLista).toBeNull();
    expect(component.ocupada).toBe('');
  });
  it('no abre enlaces fallidos, vencidos o pertenecientes a otro job', async () => {
    const { fixture, api, component, status } = setup();
    await fixture.whenStable();
    status.descarga_habilitada = true;
    await component.actualizar();
    const click = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {});
    for (const result of [
      { estado: 'FALLIDO', error: 'No se pudo generar el PAR.' },
      { estado: 'EXPIRADO', error: 'Enlace vencido.' },
      { estado: 'COMPLETADO', job_id: '1', url: 'https://example.test', expira_en: new Date(0).toISOString() },
      { estado: 'COMPLETADO', job_id: 'other', url: 'https://example.test', expira_en: new Date(Date.now()+600000).toISOString() },
    ]) {
      api.descargar.mockResolvedValue(result);
      await component.descargar({ id: '1', estado: 'COMPLETADO' } as any);
      expect(component.error).toBe(true);
      expect(component.descargaLista).toBeNull();
    }
    click.mockRestore();
    expect(api.descarga).not.toHaveBeenCalled();
  });
});
