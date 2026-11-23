import { ChangeDetectorRef } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap } from '@angular/router';
import { of, Subject, throwError } from 'rxjs';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ControlCostosComponent } from './control-costos';
import { ControlCostosService, ResumenFinalControl } from '../../services/control-costos.service';
import { ProyectosService, Proyecto } from '../../services/proyectos';
import { AuthService } from '../../services/auth';

const obra = { id_obra: 9, codigo: 'OB-9', nombre: 'Obra nueve', estado_obra: 'FINALIZADO', moneda: 'BOB' } as Proyecto;
const final: ResumenFinalControl = {
  obra: { id_obra: 9, id_empresa: 7, codigo: 'OB-9', nombre: 'Obra nueve', estado_obra: 'FINALIZADO', moneda: 'BOB' },
  linea_base: { id_control_costo: 3, id_empresa: 7, id_obra: 9, id_estimacion_base: 15,
    version_presupuesto: 2, moneda: 'BOB', estado: 'ACTIVO', seleccionado_por: 21,
    seleccionado_en: '2026-10-23', presupuesto_nombre: 'Base aprobada' },
  resumen: { costo_presupuestado_original: 250, impacto_ordenes_aprobadas: 50,
    presupuesto_revisado: 300, costo_ejecutado: 330, costo_final_registrado: 330,
    costo_mano_obra_calculado: 0,
    variacion_original: 80, variacion_original_porcentaje: 32,
    variacion_revisada: 30, variacion_revisada_porcentaje: 10,
    total_costos_registrados: 2, total_costos_anulados: 1 },
  desglose_por_categoria: { MATERIAL: 100.1, MANO_OBRA: 229.9, EQUIPO: 0, SUBCONTRATO: 0, OTRO: 0 }
};

describe('Control de costos — resumen final CU32', () => {
  let component: ControlCostosComponent;
  let service: { resumenFinal: ReturnType<typeof vi.fn>; presupuestosAprobados: ReturnType<typeof vi.fn>;
    lineaBase: ReturnType<typeof vi.fn>; comparacion: ReturnType<typeof vi.fn>; resumen: ReturnType<typeof vi.fn>;
    costos: ReturnType<typeof vi.fn>; ordenes: ReturnType<typeof vi.fn> };
  let auth: { hasPermission: ReturnType<typeof vi.fn> };
  beforeEach(() => {
    service = {
      resumenFinal: vi.fn(() => of({ success: true, data: structuredClone(final) })),
      presupuestosAprobados: vi.fn(() => of({ success: true, data: [] })),
      lineaBase: vi.fn(() => of({ success: true, data: final.linea_base })),
      comparacion: vi.fn(() => of({ success: true, data: { partidas: [] } })),
      resumen: vi.fn(() => of({ success: true, data: { resumen: final.resumen } })),
      costos: vi.fn(() => of({ success: true, data: [] })),
      ordenes: vi.fn(() => of({ success: true, data: [] }))
    };
    auth = { hasPermission: vi.fn(() => true) };
    TestBed.configureTestingModule({ imports: [ControlCostosComponent], providers: [
      { provide: ControlCostosService, useValue: service },
      { provide: ProyectosService, useValue: { listarProyectos: vi.fn(() => of({ success: true, data: [obra] })) } },
      { provide: AuthService, useValue: auth },
      { provide: ActivatedRoute, useValue: { queryParamMap: of(convertToParamMap({ id_obra: '9', final: 'true' })) } },
      { provide: ChangeDetectorRef, useValue: { detectChanges: vi.fn() } }
    ] });
    component = TestBed.runInInjectionContext(() => new ControlCostosComponent());
    component.proyectos = [structuredClone(obra)];
    component.idObra = 9;
  });

  it('abre automáticamente CU32 para una obra finalizada y no carga gastos individuales', () => {
    component.cambiarObra();
    expect(component.tab).toBe('final');
    expect(component.resumenFinal?.resumen).toEqual(final.resumen);
    expect(component.resumenFinal?.desglose_por_categoria).toEqual(final.desglose_por_categoria);
    expect(service.resumenFinal).toHaveBeenCalledExactlyOnceWith(9);
    expect(service.costos).not.toHaveBeenCalled();
  });

  it('mantiene CU17 y no pide final=true para una obra en ejecución', () => {
    component.proyectos = [{ ...obra, estado_obra: 'ACTIVO' }];
    component.cambiarObra();
    expect(service.resumenFinal).not.toHaveBeenCalled();
    expect(service.resumen).toHaveBeenCalledWith(9);
    expect(service.comparacion).toHaveBeenCalledWith(9);
    expect(component.totales).toEqual(final.resumen);
  });

  it('muestra obra no finalizada sin consultar CU32', () => {
    component.proyectos = [{ ...obra, estado_obra: 'ACTIVO' }];
    component.seleccionarTab('final');
    expect(component.estadoFinal).toBe('no-finalizada');
    expect(component.resumenFinal).toBeNull();
    expect(service.resumenFinal).not.toHaveBeenCalled();
  });

  it('respeta el permiso existente sin consultar importes', () => {
    auth.hasPermission.mockReturnValue(false);
    component.cargarResumenFinal();
    expect(component.estadoFinal).toBe('autorizacion');
    expect(service.resumenFinal).not.toHaveBeenCalled();
  });

  it.each([
    [403, 'Sin acceso', 'autorizacion'],
    [401, 'Token caducado', 'autorizacion'],
    [404, 'La obra no tiene una linea base ACTIVA.', 'sin-linea-base'],
    [409, 'El resumen requiere una obra FINALIZADO.', 'no-finalizada'],
    [500, 'Error interno', 'error']
  ])('muestra el rechazo %s del backend y elimina el resumen anterior', (status, detail, estado) => {
    component.cargarResumenFinal();
    service.resumenFinal.mockReturnValue(throwError(() => ({ status, error: { detail } })));
    component.cargarResumenFinal();
    expect(component.resumenFinal).toBeNull();
    expect(component.estadoFinal).toBe(estado);
    expect(component.errorFinal).toBe(detail);
    expect(component.cargandoFinal).toBe(false);
  });

  it('distingue desconexión de ausencia de costos y permite reintentar', () => {
    service.resumenFinal.mockReturnValue(throwError(() => ({ status: 0 })));
    component.cargarResumenFinal();
    expect(component.estadoFinal).toBe('conexion');
    expect(component.errorFinal).toContain('conectar');
    service.resumenFinal.mockReturnValue(of({ success: true, data: final }));
    component.cargarResumenFinal();
    expect(component.estadoFinal).toBe('listo');
    expect(component.errorFinal).toBe('');
  });

  it('gestiona carga y descarta la respuesta pendiente de otra obra', () => {
    const pendiente = new Subject<{ success: boolean; data: ResumenFinalControl }>();
    service.resumenFinal.mockReturnValue(pendiente);
    component.cambiarObra();
    expect(component.cargandoFinal).toBe(true);
    component.idObra = 0;
    component.cambiarObra();
    pendiente.next({ success: true, data: final });
    pendiente.complete();
    expect(component.resumenFinal).toBeNull();
    expect(component.cargandoFinal).toBe(false);
  });

  it('no publica respuestas de una obra distinta ni de una obra no finalizada', () => {
    for (const datos of [{ ...final, obra: { ...final.obra, id_obra: 10 } },
      { ...final, obra: { ...final.obra, estado_obra: 'ACTIVO' } }]) {
      service.resumenFinal.mockReturnValue(of({ success: true, data: datos }));
      component.cargarResumenFinal();
      expect(component.resumenFinal).toBeNull();
      expect(component.estadoFinal).toBe('error');
    }
  });

  it('el acceso desde proyectos selecciona la obra y el resumen final', () => {
    component.ngOnInit();
    expect(component.idObra).toBe(9);
    expect(component.tab).toBe('final');
    expect(component.estadoFinal).toBe('listo');
    component.ngOnDestroy();
  });

  it('renderiza el aviso sin costos, porcentajes nulos y categorías en cero', () => {
    service.resumenFinal.mockReturnValue(of({ success: true, data: { ...final,
      resumen: { ...final.resumen, costo_final_registrado: 0, total_costos_registrados: 0,
        variacion_original_porcentaje: null, variacion_revisada_porcentaje: null },
      desglose_por_categoria: { MATERIAL: 0, MANO_OBRA: 0, EQUIPO: 0, SUBCONTRATO: 0, OTRO: 0 }
    } }));
    const fixture = TestBed.createComponent(ControlCostosComponent);
    fixture.detectChanges();
    const text = fixture.nativeElement.textContent;
    expect(text).toContain('Sin costos registrados');
    expect(text).toContain('No disponible: presupuesto cero');
    expect(text).toContain('Costo final registrado');
    expect(text).toContain('MANO OBRA');
    expect(fixture.nativeElement.querySelectorAll('tbody tr').length).toBe(5);
    expect(text).not.toContain('Registrar costo');
    fixture.destroy();
  });

  it('muestra la trazabilidad de jornadas y salario guardada por el backend', () => {
    const data: ResumenFinalControl = {
      ...final,
      resumen: { ...final.resumen, costo_mano_obra_calculado: 3200, costo_final_registrado: 3530 },
      desglose_por_categoria: {
        MATERIAL: 100, MANO_OBRA: 3200, EQUIPO: 100, SUBCONTRATO: 100, OTRO: 30
      },
      mano_obra_trabajadores: [{
        id_usuario: 31, nombre_completo: 'Trabajador A', nombre_rol: 'ALBAÑIL',
        fecha: '2026-10-10', dias_trabajados: 10, salario_diario: 200,
        costo_calculado: 2000, id_salario: 7
      }]
    };
    service.resumenFinal.mockReturnValue(of({ success: true, data }));
    const fixture = TestBed.createComponent(ControlCostosComponent);
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Mano de obra por trabajador');
    expect(fixture.nativeElement.textContent).toContain('Trabajador A');
    expect(fixture.nativeElement.textContent).toContain('2.000,00');
    fixture.destroy();
  });
});
