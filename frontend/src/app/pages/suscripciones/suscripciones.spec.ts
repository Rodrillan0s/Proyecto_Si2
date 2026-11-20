import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing';
import { describe, it, expect, afterEach } from 'vitest';
import { AuthService } from '../../services/auth';
import { provideRouter } from '@angular/router';
import { SuscripcionesComponent } from './suscripciones';

describe('Suscripciones por empresa', () => {
  let http: HttpTestingController;
  function crear(global: boolean, planes: { codigo: string; nombre: string; prestaciones: string[] }[] = []) {
    TestBed.configureTestingModule({
      imports: [SuscripcionesComponent],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([]), {
        provide: AuthService, useValue: { obtenerRolNormalizado: () => global ? 'ADMINISTRADOR' : 'ADMINISTRADOR_EMPRESA' },
      }],
    });
    const fixture = TestBed.createComponent(SuscripcionesComponent);
    http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
    http.expectOne(r => r.url.endsWith('/planes')).flush({ data: planes });
    return fixture;
  }
  afterEach(() => { http.verify(); TestBed.resetTestingModule(); });
  const empresa = { id_empresa: 3, nombre_empresa: 'La Roca', codigo_plan: 'PROFESIONAL', nombre_plan: 'Profesional', estado: 'ACTIVA' as const,
    estado_efectivo: 'ACTIVA', fecha_inicio: '2026-10-24', fecha_fin: null, usuarios: 2 };

  it('muestra solo el plan propio sin controles administrativos', () => {
    const f = crear(false);
    http.expectOne(r => r.url.endsWith('/mi-empresa')).flush({ data: empresa });
    f.detectChanges();
    expect(f.nativeElement.querySelector('[data-testid="plan-propio"]').textContent).toContain('Plan vigente: Profesional');
    expect(f.nativeElement.textContent).not.toContain('Gestionar');
    expect(f.nativeElement.querySelector('form')).toBeNull();
  });

  it('resuelve el nombre desde el catálogo cuando la suscripción solo trae código y marca el plan propio', () => {
    const f=crear(false, [{ codigo:'PROFESIONAL',nombre:'Profesional',prestaciones:[] }]);
    http.expectOne(r => r.url.endsWith('/mi-empresa')).flush({ data:{...empresa,nombre_plan:null} });
    f.detectChanges();
    expect(f.nativeElement.querySelector('[data-testid="plan-propio"]').textContent).toContain('Plan vigente: Profesional');
    expect(f.nativeElement.querySelector('article').textContent).toContain('Plan vigente');
  });

  it('muestra textualmente los planes de empresas asignadas desde la administración', () => {
    const f=crear(true);
    http.expectOne(r => r.url.endsWith('/empresas')).flush({ data:[empresa,
      {...empresa,id_empresa:4,nombre_empresa:'El Gran Piraí',codigo_plan:'EMPRESARIAL',nombre_plan:'Empresarial'}] });
    f.detectChanges();
    const resumen=f.nativeElement.querySelector('[aria-label="Planes asignados por empresa"]').textContent;
    expect(resumen).toContain('La Roca');
    expect(resumen).toContain('Plan vigente: Profesional');
    expect(resumen).toContain('El Gran Piraí');
    expect(resumen).toContain('Plan vigente: Empresarial');
  });

  it('no presenta un plan cancelado como vigente', () => {
    const f=crear(false);
    http.expectOne(r => r.url.endsWith('/mi-empresa')).flush({ data:{...empresa,estado:'CANCELADA',estado_efectivo:'CANCELADA'} });
    f.detectChanges();
    expect(f.nativeElement.querySelector('[data-testid="plan-propio"]').textContent).toContain('Plan asignado: Profesional');
  });

  it('guarda el plan en la empresa elegida y actualiza la lista', () => {
    const f = crear(true);
    http.expectOne(r => r.url.endsWith('/empresas')).flush({ data: [empresa] });
    f.componentInstance.editar(empresa);
    f.componentInstance.form.codigo_plan = 'BASICO';
    f.componentInstance.guardar();
    const req = http.expectOne(r => r.method === 'PUT' && r.url.endsWith('/empresas/3'));
    expect(req.request.body.codigo_plan).toBe('BASICO');
    expect(req.request.body.fecha_fin).toBeNull();
    req.flush({ data: { ...empresa, codigo_plan: 'BASICO', nombre_plan: 'Básico' } });
    expect(f.componentInstance.empresas()[0].codigo_plan).toBe('BASICO');
    expect(f.componentInstance.seleccionada).toBeNull();
  });

  it('conserva el formulario y presenta el error si falla la asignación', () => {
    const f = crear(true);
    http.expectOne(r => r.url.endsWith('/empresas')).flush({ data: [empresa] });
    f.componentInstance.editar(empresa);
    f.componentInstance.guardar();
    http.expectOne(r => r.method === 'PUT').flush({ detail: 'Sin autorización' }, { status: 403, statusText: 'Forbidden' });
    expect(f.componentInstance.error()).toBe('Sin autorización');
    expect(f.componentInstance.seleccionada?.id_empresa).toBe(3);
    expect(f.componentInstance.guardando()).toBe(false);
  });
});
