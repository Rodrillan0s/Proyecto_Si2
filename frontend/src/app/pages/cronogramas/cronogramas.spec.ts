import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing';
import { ActivatedRoute, convertToParamMap, provideRouter } from '@angular/router';
import { BehaviorSubject, of } from 'rxjs';
import { CronogramasComponent } from './cronogramas';
import { CronogramaService, Cronograma } from '../../services/cronograma.service';
import { AuthService } from '../../services/auth';
import { ContextoOperativo } from '../../services/contexto-operativo';
import { ProyectosService } from '../../services/proyectos';
import { environment } from '../../../environments/environment';

const base = `${environment.apiUrl}/api/obras/10/cronogramas`;
const plan: Cronograma = { id_cronograma: 7, id_obra: 10, nombre: 'Etapa 1', descripcion: '',
  fecha_inicio: '2026-01-01', fecha_fin: '2026-12-31', version: 3, corte: '2026-10-25',
  actividades: [{ clave: 'a', nombre: 'Excavación', descripcion: '', tipo: 'ACTIVIDAD', fecha_inicio: '2026-01-01', fecha_fin: '2026-01-03', inicio_real: null, fin_real: null, avance: 0, dependencias: [], dias_retraso: 3 }],
  programadas: [], resumen: { total: 1, completadas: 0, retrasadas: 1, pendientes_inicio: 1 } };

describe('CU39: integración de obra y contrato', () => {
  let requests: HttpTestingController;
  let permisos: Set<string>;
  let params: BehaviorSubject<ReturnType<typeof convertToParamMap>>;
  beforeEach(() => {
    permisos = new Set(['Visualizar_cronograma', 'Registrar_cronograma', 'Modificar_cronograma', 'Planificar_cronograma']);
    params = new BehaviorSubject(convertToParamMap({ id: '10' }));
    TestBed.configureTestingModule({ imports: [CronogramasComponent], providers: [
      provideRouter([]), provideHttpClient(), provideHttpClientTesting(),
      { provide: ActivatedRoute, useValue: { paramMap: params } },
      { provide: AuthService, useValue: { empresaActiva$: new BehaviorSubject(null), hasPermission: (p: string) => permisos.has(p), obtenerIdEmpresaActiva: () => 1 } },
      { provide: ContextoOperativo, useValue: { proteger: () => {}, protegerEscritura: () => {} } },
      { provide: ProyectosService, useValue: { listarProyectos: () => of({ data: [] }) } },
    ] });
    requests = TestBed.inject(HttpTestingController);
  });
  afterEach(() => requests.verify({ ignoreCancelled: true }));
  function pantalla() {
    const fixture = TestBed.createComponent(CronogramasComponent); fixture.detectChanges();
    requests.expectOne(`${base}/`).flush({ success: true, data: [plan], obra: { nombre: 'Obra A', id_empresa: 1 } });
    requests.expectOne(r => r.url === `${base}/7`).flush({ success: true, data: structuredClone(plan) });
    fixture.detectChanges(); return fixture;
  }
  it('toma el ID de ruta, consulta la URL real y ofrece edición', async () => {
    const fixture = pantalla();
    expect(fixture.componentInstance.idObra).toBe(10);
    expect(fixture.nativeElement.textContent).toContain('Etapa 1');
    expect(fixture.nativeElement.textContent).toContain('Crear cronograma');
    fixture.componentInstance.editar(); fixture.detectChanges();
    await fixture.whenStable();
    expect(fixture.nativeElement.querySelector('input[name="nombre"]').value).toBe('Etapa 1');
  });
  it('supervisor solo envía planificación y versión, sin cabecera ni campos derivados', () => {
    permisos = new Set(['Visualizar_cronograma', 'Planificar_cronograma']);
    const fixture = pantalla(); const c = fixture.componentInstance;
    expect(fixture.nativeElement.textContent).not.toContain('Crear cronograma');
    c.editar(); c.guardar();
    const request = requests.expectOne(`${base}/7/planificacion`);
    expect(request.request.method).toBe('PUT');
    expect(Object.keys(request.request.body).sort()).toEqual(['actividades', 'version']);
    expect(request.request.body.version).toBe(3);
    expect(request.request.body.actividades[0].dias_retraso).toBeUndefined();
    request.flush({ detail: 'Otra persona modificó este cronograma.' }, { status: 409, statusText: 'Conflict' });
    expect(c.editor()).toBe(true); expect(c.error()).toContain('Otra persona'); expect(c.guardando()).toBe(false);
  });
  it('cancela la consulta de la obra anterior al cambiar de ruta', () => {
    const fixture = TestBed.createComponent(CronogramasComponent); fixture.detectChanges();
    const vieja = requests.expectOne(`${base}/`);
    params.next(convertToParamMap({ id: '20' }));
    expect(vieja.cancelled).toBe(true);
    requests.expectOne(`${environment.apiUrl}/api/obras/20/cronogramas/`).flush({ data: [], obra: { nombre: 'B', id_empresa: 1 } });
    expect(fixture.componentInstance.actual()).toBeNull();
  });
  it('no permite quitar una predecesora referenciada', () => {
    const c = pantalla().componentInstance; c.editar();
    c.borrador.actividades.push({ ...c.borrador.actividades[0], clave: 'b', dependencias: ['a'] });
    c.quitar(c.borrador.actividades[0]);
    expect(c.borrador.actividades.length).toBe(2); expect(c.error()).toContain('dependencias');
  });
  it('mantiene la versión para eliminar y el alcance de obra', () => {
    TestBed.inject(CronogramaService).eliminar(10, plan).subscribe();
    const r = requests.expectOne(req => req.url === `${base}/7` && req.params.get('version') === '3');
    expect(r.request.method).toBe('DELETE'); r.flush({ success: true });
  });
  it('marca y desmarca predecesoras con clic conservando las otras y guarda la lista vacía', async () => {
    const fixture = pantalla(); const c = fixture.componentInstance;
    c.editar();
    const a = c.borrador.actividades[0];
    a.dependencias = ['b'];
    c.borrador.actividades.push({ ...a, clave: 'b', nombre: 'Armado', dependencias: [] },
      { ...a, clave: 'c', nombre: 'Vaciado', dependencias: [] });
    fixture.detectChanges(); await fixture.whenStable();
    const opciones: HTMLInputElement[] = Array.from(fixture.nativeElement.querySelector('fieldset.predecessors').querySelectorAll('input[type="checkbox"]'));
    expect(opciones).toHaveLength(2); // nunca ofrece la propia actividad
    expect(opciones[0].checked).toBe(true);
    opciones[1].click(); fixture.detectChanges();
    expect(a.dependencias).toEqual(['b', 'c']);
    opciones[0].click(); fixture.detectChanges();
    expect(a.dependencias).toEqual(['c']);
    expect(opciones[0].checked).toBe(false); expect(opciones[1].checked).toBe(true);
    opciones[1].click(); fixture.detectChanges();
    expect(a.dependencias).toEqual([]);
    opciones[0].click(); fixture.detectChanges(); opciones[0].click(); fixture.detectChanges();
    expect(a.dependencias).toEqual([]);
    c.guardar();
    const request = requests.expectOne(`${base}/7`);
    expect(request.request.body.actividades[0].dependencias).toEqual([]);
    request.flush({ detail: 'Conflicto de prueba' }, { status: 409, statusText: 'Conflict' });
  });
  it('permite corregir un filtro inválido conservando el detalle anterior', () => {
    const c = pantalla().componentInstance;
    c.desde = '2026-12-31'; c.hasta = '2026-01-01'; c.filtrar();
    requests.expectOne(r => r.url === `${base}/7`).flush({ detail: 'Período inválido' }, { status: 400, statusText: 'Bad Request' });
    expect(c.actual()?.id_cronograma).toBe(7); expect(c.error()).toBe('Período inválido');
    c.hasta = '2026-12-31'; c.filtrar();
    requests.expectOne(r => r.url === `${base}/7`).flush({ data: plan });
    expect(c.error()).toBe('');
  });
  it('muestra una sola fecha prevista para el hito y guarda ambos campos sincronizados', async () => {
    const fixture = pantalla(); const c = fixture.componentInstance;
    c.editar(); const a = c.borrador.actividades[0];
    a.tipo = 'HITO'; a.fecha_inicio = '2026-01-10'; a.fecha_fin = '2026-01-10';
    fixture.detectChanges(); await fixture.whenStable();
    const editor: HTMLElement = fixture.nativeElement.querySelector('article.activity-editor');
    const fechaHito = editor.querySelector<HTMLInputElement>('input[type="date"]')!;
    expect(editor.querySelectorAll('input[type="date"]')).toHaveLength(3); // prevista, inicio real, fin real
    expect(editor.textContent).not.toContain('Inicio previsto');
    expect(editor.textContent).not.toContain('Fin previsto');
    expect(fechaHito.readOnly).toBe(false); expect(fechaHito.min).toBe('2026-01-01');
    for (const fecha of ['2026-01-15', '2026-01-05']) {
      fechaHito.value = fecha; fechaHito.dispatchEvent(new Event('input'));
      fixture.detectChanges(); await fixture.whenStable();
      expect(a.fecha_inicio).toBe(fecha); expect(a.fecha_fin).toBe(fecha);
    }
    c.guardar(); const request = requests.expectOne(`${base}/7`);
    expect(request.request.body.actividades[0].fecha_inicio).toBe('2026-01-05');
    expect(request.request.body.actividades[0].fecha_fin).toBe('2026-01-05');
    request.flush({ detail: 'Conflicto de prueba' }, { status: 409, statusText: 'Conflict' });
  });
  it('conserva fechas independientes para una actividad común', async () => {
    const fixture = pantalla(); const c = fixture.componentInstance; c.editar();
    fixture.detectChanges(); await fixture.whenStable();
    const fechas: NodeListOf<HTMLInputElement> = fixture.nativeElement.querySelector('article.activity-editor').querySelectorAll('input[type="date"]');
    expect(fechas).toHaveLength(4);
    const fin = fechas[1];
    fin.value = '2026-01-20'; fin.dispatchEvent(new Event('input'));
    fixture.detectChanges(); await fixture.whenStable();
    expect(c.borrador.actividades[0].fecha_inicio).toBe('2026-01-01');
    expect(c.borrador.actividades[0].fecha_fin).toBe('2026-01-20');
  });
  it('descarta el resultado de una escritura anterior al cambiar la obra de ruta', () => {
    const c = pantalla().componentInstance; c.editar(); c.guardar();
    const anterior = requests.expectOne(`${base}/7`);
    params.next(convertToParamMap({ id: '20' }));
    requests.expectOne(`${environment.apiUrl}/api/obras/20/cronogramas/`).flush({ data: [], obra: { nombre: 'Nueva obra', id_empresa: 1 } });
    anterior.flush({ success: true, data: plan });
    expect(c.idObra).toBe(20); expect(c.actual()).toBeNull(); expect(c.mensaje()).toBe('');
    expect(c.guardando()).toBe(false);
    requests.expectNone(`${environment.apiUrl}/api/obras/20/cronogramas/7`);
  });
});
