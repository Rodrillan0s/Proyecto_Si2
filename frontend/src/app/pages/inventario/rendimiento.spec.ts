import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing';
import { BehaviorSubject } from 'rxjs';
import { AuthService } from '../../services/auth';
import { InventarioComponent } from './inventario';
import { MaterialesComponent } from '../materiales/materiales';
import { IncidenciasComponent } from '../incidencias/incidencias';
import { ComprasComponent } from '../compras/compras';
import { provideRouter } from '@angular/router';
import { ProyectosComponent } from '../proyectos/proyectos';

describe('Solicitudes iniciales y cambios de empresa', () => {
  let company: number; let companies: BehaviorSubject<unknown>; let http: HttpTestingController;
  beforeEach(() => {
    company = 7; companies = new BehaviorSubject<unknown>(null);
    TestBed.configureTestingModule({ providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting(), {
      provide: AuthService, useValue: {
        empresaActiva$: companies, obtenerToken: () => 'fixture', obtenerIdEmpresaActiva: () => company,
        obtenerEmpresaActiva: () => ({ id_empresa: company }), obtenerUsuario: () => ({ nro_usuario: 1, id_empresa: 7 }),
        obtenerRolNormalizado: () => 'ADMINISTRADOR_EMPRESA', esVistaGlobal: () => false, hasPermission: () => true,
      },
    }] });
    TestBed.overrideComponent(InventarioComponent, { set: { template: '' } });
    TestBed.overrideComponent(MaterialesComponent, { set: { template: '' } });
    TestBed.overrideComponent(IncidenciasComponent, { set: { template: '' } });
    TestBed.overrideComponent(ComprasComponent, { set: { template: '' } });
    TestBed.overrideComponent(ProyectosComponent, { set: { template: '' } });
    http = TestBed.inject(HttpTestingController);
  });
  afterEach(() => http.verify({ ignoreCancelled: true }));
  for (const catalogoPrimero of [true, false]) {
    it(`Obras y tipos cargan independientemente (catalogo primero: ${catalogoPrimero})`, () => {
      const fixture = TestBed.createComponent(ProyectosComponent); fixture.detectChanges();
      const listado = http.expectOne(request => request.url.endsWith('/proyectos/'));
      const tipos = http.expectOne(request => request.url.endsWith('/proyectos/tipos'));
      expect(listado.cancelled).toBe(false);
      expect(tipos.cancelled).toBe(false);
      expect(fixture.componentInstance.cargando).toBe(true);
      if (catalogoPrimero) tipos.flush({ success: true, data: [{ id_tipo_obra: 1, nombre_obra: 'Civil' }] });
      listado.flush({ success: true, data: [{ id_obra: 9, id_empresa: 7, nombre: 'Alameda', codigo: 'ALM', estado_obra: 'PLANIFICACION' }] });
      expect(fixture.componentInstance.cargando).toBe(false);
      expect(fixture.componentInstance.proyectosFiltrados[0].id_obra).toBe(9);
      expect(fixture.componentInstance.totalProyectos).toBe(1);
      if (!catalogoPrimero) tipos.flush({ success: true, data: [{ id_tipo_obra: 1, nombre_obra: 'Civil' }] });
      expect(fixture.componentInstance.tiposProyecto.length).toBe(1);
      fixture.destroy();
    });
  }
  it('Ver obras termina la carga y muestra el error si falla el listado', () => {
    const fixture = TestBed.createComponent(ProyectosComponent); fixture.detectChanges();
    const listado = http.expectOne(request => request.url.endsWith('/proyectos/'));
    http.expectOne(request => request.url.endsWith('/proyectos/tipos')).flush({ success: true, data: [] });
    listado.flush({}, { status: 500, statusText: 'Error' });
    expect(fixture.componentInstance.cargando).toBe(false);
    expect(fixture.componentInstance.mensajeError).toContain('proyectos');
    fixture.destroy();
  });
  it('Incidencias inicia un listado y sus dos filtros sin duplicar peticiones', () => {
    const fixture = TestBed.createComponent(IncidenciasComponent); fixture.detectChanges();
    const requests = http.match(() => true);
    expect(requests.length).toBe(3);
    expect(requests.filter(item => item.request.url.endsWith('/incidencias/')).length).toBe(1);
    requests.forEach(item => item.flush({ success: true, data: [], pagination: { total: 0, total_pages: 0 } }));
    fixture.destroy();
  });
  it('Compras inicia ordenes y proveedores; materiales se consultan al abrir el formulario', () => {
    const fixture = TestBed.createComponent(ComprasComponent); fixture.detectChanges();
    const requests = http.match(() => true);
    expect(requests.length).toBe(2);
    expect(requests.some(item => item.request.url.endsWith('/materiales'))).toBe(false);
    requests.forEach(item => item.flush({ success: true, data: [], pagination: { total: 0, total_pages: 0 } }));
    fixture.destroy();
  });
  it('Inventario inicia una sola consulta de stock y una de KPIs', () => {
    const fixture = TestBed.createComponent(InventarioComponent); fixture.detectChanges();
    const stock = http.expectOne(request => request.url.endsWith('/stock')); const kpis = http.expectOne(request => request.url.endsWith('/kpis'));
    stock.flush({ success: true, data: [{ id_material: 1 }], total: 1 }); kpis.flush({ success: true, data: {} });
    expect(fixture.componentInstance.stockItems.length).toBe(1); fixture.destroy();
  });
  it('Materiales carga un listado y dos catálogos, sin repetir la inicialización', () => {
    const fixture = TestBed.createComponent(MaterialesComponent); fixture.detectChanges();
    http.expectOne(request => request.url.endsWith('/materiales')).flush({ success: true, data: [], pagination: { total: 0 } });
    http.expectOne(request => request.url.endsWith('/categorias')).flush({ success: true, data: [] });
    http.expectOne(request => request.url.endsWith('/unidades-medida')).flush({ success: true, data: [] });
    fixture.destroy();
  });
  it('Inventario cancela el tenant anterior y solo acepta la respuesta nueva', () => {
    const fixture = TestBed.createComponent(InventarioComponent); fixture.detectChanges();
    const stock = http.expectOne(request => request.url.endsWith('/stock')); const kpis = http.expectOne(request => request.url.endsWith('/kpis'));
    company = 8; companies.next(8); expect(stock.cancelled).toBe(true); expect(kpis.cancelled).toBe(true);
    const next = http.expectOne(request => request.url.endsWith('/stock')); expect(next.request.params.get('id_empresa')).toBe('8');
    next.flush({ success: true, data: [{ id_material: 8 }], total: 1 });
    http.expectOne(request => request.url.endsWith('/kpis')).flush({ success: true, data: {} });
    expect(fixture.componentInstance.stockItems[0].id_material).toBe(8); fixture.destroy();
  });
});
