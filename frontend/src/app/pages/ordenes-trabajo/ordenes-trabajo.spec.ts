import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { of } from 'rxjs';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { OrdenesTrabajoComponent } from './ordenes-trabajo';
import { OrdenesTrabajoService, OrdenTrabajo } from '../../services/ordenes-trabajo';
import { AuthService } from '../../services/auth';

const orden: OrdenTrabajo = {
  orden_nro: 5, id_obra: 8, nombre: 'Green Tower', estado: 'EN_PROCESO',
  afectada_por_incidencia: true
};

describe('OT afectada por incidencia', () => {
  let servicio: { listarOrdenesTrabajo: ReturnType<typeof vi.fn>; obtenerOrdenTrabajo: ReturnType<typeof vi.fn> };
  beforeEach(() => {
    servicio = {
      listarOrdenesTrabajo: vi.fn(() => of({success: true, data: [{...orden}]})),
      obtenerOrdenTrabajo: vi.fn(() => of({success: true, data: {...orden}}))
    };
    TestBed.configureTestingModule({
      imports: [OrdenesTrabajoComponent],
      providers: [
        {provide: OrdenesTrabajoService, useValue: servicio},
        {provide: Router, useValue: {navigate: vi.fn()}},
        {provide: AuthService, useValue: {
          empresaActiva$: of(null), obtenerIdEmpresaActiva: () => 1,
          esVistaGlobal: () => false
        }}
      ]
    });
  });

  it('muestra estado operativo y etiqueta independiente en lista y detalle', () => {
    const fixture = TestBed.createComponent(OrdenesTrabajoComponent);
    fixture.detectChanges();
    fixture.componentInstance.verOrden(orden);
    fixture.detectChanges();
    const contenido = fixture.nativeElement.textContent;
    expect(contenido.match(/AFECTADA POR INCIDENCIA/g)?.length).toBe(2);
    expect(contenido).toContain('En proceso');
    expect(fixture.componentInstance.estadisticas.enProceso).toBe(1);
    expect(fixture.componentInstance.obtenerEstados()).toEqual(['EN_PROCESO']);
  });

  it('consulta nuevamente backend al abrir detalle y oculta la etiqueta al resolver', () => {
    const fixture = TestBed.createComponent(OrdenesTrabajoComponent);
    fixture.detectChanges();
    servicio.obtenerOrdenTrabajo.mockReturnValue(of({success: true, data: {
      ...orden, afectada_por_incidencia: false
    }}));
    fixture.componentInstance.verOrden(orden);
    fixture.detectChanges();
    expect(servicio.obtenerOrdenTrabajo).toHaveBeenCalledWith(5);
    expect(fixture.componentInstance.ordenSeleccionada?.afectada_por_incidencia).toBe(false);
    expect(fixture.nativeElement.querySelector('.detail-card').textContent).not.toContain('AFECTADA POR INCIDENCIA');
    expect(fixture.componentInstance.ordenSeleccionada?.estado).toBe('EN_PROCESO');
  });

  it.each(['FINALIZADO', 'CANCELADO'])('conserva el estado terminal %s con afectacion', (estado) => {
    const fixture = TestBed.createComponent(OrdenesTrabajoComponent);
    servicio.listarOrdenesTrabajo.mockReturnValue(of({success: true, data: [{...orden, estado}]}));
    fixture.detectChanges();
    expect(fixture.componentInstance.ordenes[0].estado).toBe(estado);
    expect(fixture.nativeElement.textContent).toContain('AFECTADA POR INCIDENCIA');
  });
});
