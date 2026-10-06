import { TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { BehaviorSubject, Subject, of } from 'rxjs';
import { vi } from 'vitest';
import { AuthService } from '../../services/auth';
import { EmpresaService } from '../../services/empresa';
import { ProyectosService } from '../../services/proyectos';
import { ReportesService } from '../../services/reportes.service';
import { NotificacionesService } from '../../services/notificaciones';
import { AsistenteService } from '../../services/asistente.service';
import { ContextoOperativo } from '../../services/contexto-operativo';
import { AdminLayoutComponent } from './admin-layout';
describe('Navegación compatible con la sesión existente', () => {
  let company: number; let companies: BehaviorSubject<unknown>; let permissions: Set<string>;
  beforeEach(() => {
    company = 7; companies = new BehaviorSubject<unknown>(null); permissions = new Set(['Visualizar_obras', 'Registrar_obras', 'Modificar_obras', 'Visualizar_reportes']);
    TestBed.configureTestingModule({ imports: [AdminLayoutComponent], providers: [provideRouter([]),
      { provide: AuthService, useValue: {
        empresaActiva$: companies, empresaSeleccionada$: companies,
        obtenerUsuario: () => ({ nombre_completo: 'Usuario de prueba', nombre_rol: 'ROL_PERSONALIZADO', nombre_empresa: 'Empresa original', id_empresa: 7 }),
        obtenerEmpresaSeleccionada: () => ({ id_empresa: company }), obtenerEmpresaActiva: () => ({ id_empresa: company }),
        obtenerIdEmpresaActiva: () => company, obtenerNombreEmpresaActiva: () => `Empresa ${company}`,
        obtenerRolNormalizado: () => 'ROL_PERSONALIZADO', hasPermission: (p: string) => permissions.has(p),
        hasAnyPermission: (p: string[]) => p.some(id => permissions.has(id)), hasAllPermissions: (p: string[]) => p.every(id => permissions.has(id)),
      } },
      { provide: NotificacionesService, useValue: { conectar: vi.fn(), notificaciones$: of([]) } },
      { provide: EmpresaService, useValue: { listarEmpresas: () => of({ data: [] }) } },
      { provide: ProyectosService, useValue: { listarProyectos: () => of({ data: [{ id_obra: 9, id_empresa: 7, nombre: 'Obra nueve', codigo: 'O9' }] }) } },
      { provide: ReportesService, useValue: { catalog: async () => ({ reportes: [{ id: 'incidencias', titulo: 'Incidencias' }], obras: [], acciones: [], id_empresa: company }) } },
    ] });
  });
  it('filtra por permisos actuales sin agregar reglas de roles al registro', async () => {
    const fixture = TestBed.createComponent(AdminLayoutComponent); fixture.detectChanges();
    fixture.componentInstance.toggleSection(fixture.componentInstance.sections.find(section => section.id === 'reportes')!);
    await fixture.whenStable(); fixture.changeDetectorRef.markForCheck(); fixture.detectChanges();
    const sections = fixture.componentInstance.sections;
    expect(sections.some(section => section.id === 'admin')).toBe(false);
    expect(sections.find(section => section.id === 'reportes')?.items.map(item => item.family)).toEqual(['incidencias']);
    expect(fixture.nativeElement.textContent).toContain('Empresa 7'); fixture.destroy();
  });
  it('colapsar conserva el sidebar y los enlaces de iconos', () => {
    const fixture = TestBed.createComponent(AdminLayoutComponent); fixture.detectChanges();
    const component = fixture.componentInstance; component.sidebarColapsado = true;
    fixture.changeDetectorRef.markForCheck(); fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('aside.is-collapsed')).not.toBeNull();
    expect(fixture.nativeElement.querySelector('a[aria-label="Ver obras"] svg')).not.toBeNull(); fixture.destroy();
  });
  it('Nuevo y Gestión tienen destinos diferentes; asignaciones usan una obra confirmada', () => {
    const fixture = TestBed.createComponent(AdminLayoutComponent); const component = fixture.componentInstance;
    const items = component.sections.flatMap(section => section.items);
    expect(component.itemQuery(items.find(item => item.id === 'nuevo')!)).toEqual({ tab: 'nuevo' });
    expect(component.itemQuery(items.find(item => item.id === 'gestion')!)).toEqual({ tab: 'gestion' });
    const context = TestBed.inject(ContextoOperativo); context.seleccionar({ id_obra: 9, id_empresa: 7, nombre: 'Obra', codigo: 'O9' });
    expect(component.itemRoute(items.find(item => item.id === 'unidades')!)).toBe('/proyectos/9');
    expect(component.itemFragment(items.find(item => item.id === 'jefes')!)).toBe('responsables-obra'); fixture.destroy();
  });
  it('una respuesta del selector de empresa anterior no repuebla obras', async () => {
    const pending = new Subject<{ data: unknown[] }>(); TestBed.overrideProvider(ProyectosService, { useValue: { listarProyectos: () => pending } });
    const fixture = TestBed.createComponent(AdminLayoutComponent); fixture.detectChanges(); const component = fixture.componentInstance;
    const loading = component.cargarObrasSelector(); company = 8; companies.next(8);
    pending.next({ data: [{ id_obra: 9, id_empresa: 7 }] }); await loading; expect(component.obras).toEqual([]); fixture.destroy();
  });
  it('la cabecera usa consulta rápida sobre el asistente compartido', () => {
    const fixture = TestBed.createComponent(AdminLayoutComponent); const component = fixture.componentInstance;
    component.consultaAsistente = 'stock'; component.abrirConsultaAsistente();
    const ui = TestBed.inject(AsistenteService); expect(ui.mode()).toBe('quick'); expect(ui.draft()).toBe('stock'); expect(ui.submissions()).toBe(1); fixture.destroy();
  });
});
