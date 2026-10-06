import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of, throwError } from 'rxjs';
import { describe, expect, it, vi } from 'vitest';
import { AuthService } from '../../../services/auth';
import { IncidenciasService } from '../../../services/incidencias';
import { IncidenciasAsignadasComponent } from './incidencias-asignadas';

describe('Incidencias asignadas web', () => {
  function crear(data: unknown[] = []) {
    const listar = vi.fn().mockReturnValue(of({data, pagination: {page: 1, total_pages: 1}}));
    TestBed.configureTestingModule({providers: [
      provideRouter([]),
      {provide: AuthService, useValue: {obtenerUsuario: () => ({nro_usuario: 14})}},
      {provide: IncidenciasService, useValue: {listar}},
    ]});
    const fixture = TestBed.createComponent(IncidenciasAsignadasComponent);
    fixture.detectChanges();
    return {fixture, listar};
  }

  it('consulta por Jhon y muestra la incidencia con enlace al detalle', () => {
    const {fixture, listar} = crear([{id_incidencia: 9, titulo: 'Filtración segundo piso', obra_nombre: 'Green Tower', prioridad: 'MEDIA', estado: 'ASIGNADA'}]);
    expect(listar).toHaveBeenCalledWith({id_responsable: 14, page: 1, limit: 20});
    expect(fixture.nativeElement.textContent).toContain('Filtración segundo piso');
    expect(fixture.nativeElement.querySelector('article a').getAttribute('href')).toBe('/incidencias/9');
  });

  it('muestra el mensaje vacío', () => {
    const {fixture} = crear();
    expect(fixture.nativeElement.textContent).toContain('No tienes incidencias asignadas actualmente.');
  });

  it('limpia resultados anteriores cuando falla una nueva consulta', () => {
    const {fixture, listar} = crear([{id_incidencia: 9}]);
    listar.mockReturnValue(throwError(() => ({status: 403})));
    fixture.componentInstance.cargar(2);
    fixture.detectChanges();
    expect(fixture.componentInstance.incidencias).toEqual([]);
    expect(fixture.nativeElement.textContent).toContain('No se pudieron cargar');
  });
});
