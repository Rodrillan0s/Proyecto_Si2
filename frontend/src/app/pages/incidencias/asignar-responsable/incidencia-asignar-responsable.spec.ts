import { TestBed, ComponentFixture } from '@angular/core/testing';
import { of, throwError } from 'rxjs';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { IncidenciaAsignarResponsableComponent } from './incidencia-asignar-responsable';
import { Incidencia, IncidenciasService } from '../../../services/incidencias';

describe('Selección de responsable de incidencia', () => {
  let fixture: ComponentFixture<IncidenciaAsignarResponsableComponent>;
  let service: { obtenerResponsables: ReturnType<typeof vi.fn>; asignarResponsable: ReturnType<typeof vi.fn> };
  const jhon = { nro_usuario: 14, nombre_usuario: 'JHON JONES', nombre_completo: 'JHON JONES', nombre_rol: 'ELECTRICO' };

  beforeEach(async () => {
    service = {
      obtenerResponsables: vi.fn(() => of({ success: true, data: [jhon] })),
      asignarResponsable: vi.fn(() => of({ success: true, message: 'Asignado', estado: 'ASIGNADA' }))
    };
    await TestBed.configureTestingModule({
      imports: [IncidenciaAsignarResponsableComponent],
      providers: [{ provide: IncidenciasService, useValue: service }]
    }).compileComponents();
    fixture = TestBed.createComponent(IncidenciaAsignarResponsableComponent);
    fixture.componentRef.setInput('incidencia', {
      id_incidencia: 9, id_obra: 8, estado: 'ABIERTA', id_responsable: null
    } as Incidencia);
    fixture.detectChanges();
  });

  it('muestra nombre y rol recibidos para la incidencia de Green Tower', () => {
    expect(service.obtenerResponsables).toHaveBeenCalledWith(9);
    expect(fixture.nativeElement.textContent).toContain('JHON JONES');
    expect(fixture.nativeElement.textContent).toContain('ELECTRICO');
    expect(fixture.nativeElement.querySelectorAll('input[type=radio]').length).toBe(1);
  });

  it('selecciona el trabajador y envía únicamente incidencia y responsable', () => {
    const emitted = vi.spyOn(fixture.componentInstance.asignado, 'emit');
    const radio: HTMLInputElement = fixture.nativeElement.querySelector('input[type=radio]');
    radio.click();
    fixture.detectChanges();
    fixture.componentInstance.confirmar();
    expect(service.asignarResponsable).toHaveBeenCalledWith(9, 14);
    expect(emitted).toHaveBeenCalledWith({ success: true, message: 'Asignado', estado: 'ASIGNADA' });
  });

  it('no permite enviar un responsable que no está en la lista válida', () => {
    fixture.componentInstance.usuarioSeleccionado = 99;
    fixture.componentInstance.confirmar();
    expect(service.asignarResponsable).not.toHaveBeenCalled();
  });

  it('elimina la selección anterior si ya no es elegible y explica la lista vacía', () => {
    service.obtenerResponsables.mockReturnValue(of({ success: true, data: [] }));
    fixture.componentInstance.incidencia.id_responsable = 14;
    fixture.componentInstance.ngOnInit();
    fixture.detectChanges();
    expect(fixture.componentInstance.usuarioSeleccionado).toBeNull();
    expect(fixture.nativeElement.textContent).toContain('vinculados a esta obra');
    fixture.componentInstance.confirmar();
    expect(service.asignarResponsable).not.toHaveBeenCalled();
  });

  it('muestra el rechazo del backend sin emitir asignación', () => {
    service.asignarResponsable.mockReturnValue(throwError(() => ({ status: 404, error: { detail: 'Responsable no elegible' } })));
    fixture.componentInstance.usuarioSeleccionado = 14;
    const emitted = vi.spyOn(fixture.componentInstance.asignado, 'emit');
    fixture.componentInstance.confirmar();
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Responsable no elegible');
    expect(emitted).not.toHaveBeenCalled();
  });
});
