import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { ControlCostosService } from './control-costos.service';
import { environment } from '../../environments/environment';

describe('ControlCostosService — CU32', () => {
  let service: ControlCostosService;
  let http: HttpTestingController;
  beforeEach(() => {
    TestBed.configureTestingModule({ providers: [provideHttpClient(), provideHttpClientTesting()] });
    service = TestBed.inject(ControlCostosService);
    http = TestBed.inject(HttpTestingController);
  });
  afterEach(() => http.verify());

  it('consulta el endpoint existente con final=true, sin enviar escrituras', () => {
    service.resumenFinal(9).subscribe();
    const request = http.expectOne(`${environment.apiUrl}/api/control-costos/obras/9/resumen?final=true`);
    expect(request.request.method).toBe('GET');
    request.flush({ success: true, data: {} });
  });

  it('conserva la consulta habitual sin final=true', () => {
    service.resumen(9).subscribe();
    const request = http.expectOne(`${environment.apiUrl}/api/control-costos/obras/9/resumen`);
    expect(request.request.params.has('final')).toBe(false);
    request.flush({ success: true, data: {} });
  });

  it('consulta trabajadores y jornadas en la obra seleccionada', () => {
    service.manoObra(9).subscribe();
    const request = http.expectOne(`${environment.apiUrl}/api/control-costos/obras/9/mano-obra`);
    expect(request.request.method).toBe('GET');
    request.flush({ success: true, data: { trabajadores: [], jornadas: [] } });
  });

  it('registra salario diario y jornada mediante la API existente de control de costos', () => {
    service.registrarSalario(9, 31, { salario_diario: 200, fecha_vigencia: '2026-10-25' }).subscribe();
    const salary = http.expectOne(`${environment.apiUrl}/api/control-costos/obras/9/trabajadores/31/salarios`);
    expect(salary.request.method).toBe('POST');
    expect(salary.request.body).toEqual({ salario_diario: 200, fecha_vigencia: '2026-10-25' });
    salary.flush({ success: true, data: {} });

    service.registrarJornada(9, {
      id_usuario: 31, fecha: '2026-10-25', dias_trabajados: 0.5
    }).subscribe();
    const jornada = http.expectOne(`${environment.apiUrl}/api/control-costos/obras/9/jornadas`);
    expect(jornada.request.method).toBe('POST');
    expect(jornada.request.body).toEqual({
      id_usuario: 31, fecha: '2026-10-25', dias_trabajados: 0.5
    });
    jornada.flush({ success: true, data: {} });
  });
});
