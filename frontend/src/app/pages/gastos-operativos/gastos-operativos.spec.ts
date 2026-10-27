import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ActivatedRoute, convertToParamMap, provideRouter } from '@angular/router';
import { BehaviorSubject, of } from 'rxjs';
import { GastosOperativosComponent } from './gastos-operativos';
import { AuthService } from '../../services/auth';
import { ContextoOperativo } from '../../services/contexto-operativo';
import { ProyectosService } from '../../services/proyectos';
import { environment } from '../../../environments/environment';

describe('CU32 integrado con el contexto de eddy', () => {
  let http: HttpTestingController;
  let empresa: number;
  let permisos: Set<string>;
  let operativo: BehaviorSubject<unknown>;
  let params: BehaviorSubject<ReturnType<typeof convertToParamMap>>;
  const api = `${environment.apiUrl}/api/control-costos/obras`;
  beforeEach(() => {
    empresa = 1; permisos = new Set(['Visualizar_control_costos', 'Modificar_obras']);
    operativo = new BehaviorSubject<unknown>({ empresa: 1, obra: 10 });
    params = new BehaviorSubject(convertToParamMap({ id: '10' }));
    TestBed.configureTestingModule({ imports: [GastosOperativosComponent], providers: [
      provideRouter([]), provideHttpClient(), provideHttpClientTesting(),
      { provide: ActivatedRoute, useValue: { paramMap: params } },
      { provide: AuthService, useValue: { hasPermission: (p: string) => permisos.has(p), obtenerIdEmpresaActiva: () => empresa, obtenerUsuario: () => ({ id_empresa: 1 }) } },
      { provide: ContextoOperativo, useValue: { operativo$: operativo, obra: null, protegerEscritura: () => {}, confirmarCambio: () => true, seleccionar: () => true } },
      { provide: ProyectosService, useValue: { listarProyectos: () => of({ data: [
        { id_obra: 10, id_empresa: 1, codigo: 'A', nombre: 'Obra A', moneda: 'BOB', estado_obra: 'FINALIZADO' },
        { id_obra: 11, id_empresa: 1, codigo: 'B', nombre: 'Obra B', moneda: 'BOB', estado_obra: 'EN_PROCESO' },
        { id_obra: 20, id_empresa: 2, codigo: 'C', nombre: 'Obra ajena', estado_obra: 'FINALIZADO' },
      ] }) } },
    ] });
    http = TestBed.inject(HttpTestingController);
  });
  afterEach(() => http.verify({ ignoreCancelled: true }));
  function pantalla() {
    const f = TestBed.createComponent(GastosOperativosComponent); f.detectChanges(); return f;
  }
  function final() {
    http.expectOne(r => r.url === `${api}/10/resumen` && r.params.get('final') === 'true').flush({ success: true, data: {
      linea_base: { moneda: 'BOB', presupuesto_nombre: 'Presupuesto aprobado', version_presupuesto: 1 },
      resumen: { costo_final_registrado: 250, costo_presupuestado_original: 300, presupuesto_revisado: 300, variacion_revisada: -50 },
      desglose_por_categoria: { MATERIAL: 50, MANO_OBRA: 200 }, mano_obra_trabajadores: [],
    } });
  }
  it('muestra importes recibidos del backend y usa el contrato final=true', () => {
    const f = pantalla(); final(); f.detectChanges();
    expect(f.nativeElement.textContent).toContain('Presupuesto aprobado');
    expect(f.nativeElement.textContent).toContain('250');
    expect(f.nativeElement.textContent).not.toContain('Obra ajena');
  });
  it('cancela un resumen pendiente al cambiar de empresa y borra sus importes', () => {
    const f = pantalla(); const anterior = http.expectOne(r => r.url === `${api}/10/resumen`);
    empresa = 2; operativo.next({ empresa: 2, obra: null });
    expect(anterior.cancelled).toBe(true); expect(f.componentInstance.resumen).toBeNull();
    http.expectNone(r => r.url.includes('/mano-obra') || r.url.includes('/resumen'));
  });
  it('rechaza obras desconocidas o de otro tenant sin solicitar sus costos', () => {
    params.next(convertToParamMap({ id: '20' })); const f = pantalla();
    expect(f.componentInstance.idObra).toBe(0); expect(f.componentInstance.error).toContain('no pertenece');
    http.expectNone(r => r.url.includes('/resumen'));
  });
  it('obra abierta muestra el aviso y permite salario y jornada por sus contratos HTTP', () => {
    params.next(convertToParamMap({ id: '11' })); const f = pantalla(); const c = f.componentInstance;
    expect(c.aviso).toContain('finalice'); http.expectNone(r => r.url.includes('/resumen'));
    c.cambiarTab('mano-obra');
    const datos = { trabajadores: [{ id_usuario: 7, nombre_completo: 'Trabajador', nombre_rol: 'ALBAÑIL' }], jornadas: [] };
    http.expectOne(`${api}/11/mano-obra`).flush({ data: datos }); f.detectChanges();
    c.salario = { id_usuario: 7, salario_diario: 200, fecha_vigencia: '2026-10-27' }; c.guardarSalario();
    const salario = http.expectOne(`${api}/11/trabajadores/7/salarios`);
    expect(salario.request.body).toEqual({ salario_diario: 200, fecha_vigencia: '2026-10-27' });
    salario.flush({ success: true }); http.expectOne(`${api}/11/mano-obra`).flush({ data: datos });
    c.jornada = { id_usuario: 7, fecha: '2026-10-27', dias_trabajados: 0.5 }; c.guardarJornada();
    const jornada = http.expectOne(`${api}/11/jornadas`);
    expect(jornada.request.body).toEqual({ id_usuario: 7, fecha: '2026-10-27', dias_trabajados: 0.5 });
    jornada.flush({ success: true }); http.expectOne(`${api}/11/mano-obra`).flush({ data: datos });
  });
  it('sin Modificar_obras no muestra formularios ni envía escrituras aunque se invoque el método', () => {
    permisos.delete('Modificar_obras'); const f = pantalla(); final(); f.componentInstance.cambiarTab('mano-obra');
    http.expectOne(`${api}/10/mano-obra`).flush({ data: { trabajadores: [{ id_usuario: 7, nombre_completo: 'Trabajador' }], jornadas: [] } });
    f.detectChanges(); expect(f.nativeElement.querySelector('form')).toBeNull();
    f.componentInstance.guardarSalario(); f.componentInstance.guardarJornada(); http.expectNone(r => r.method === 'POST');
  });
  it('conserva el mensaje de conflicto y permite reintentar la consulta', () => {
    const f = pantalla(); http.expectOne(r => r.url === `${api}/10/resumen`).flush({ detail: 'No hay línea base aprobada.' }, { status: 409, statusText: 'Conflict' });
    f.detectChanges(); expect(f.nativeElement.textContent).toContain('No hay línea base aprobada.');
    f.componentInstance.cargar(); final(); expect(f.componentInstance.error).toBe('');
  });
});
