import { TestBed } from '@angular/core/testing';

import { EquipoMaquinaria } from './equipo-maquinaria';

describe('EquipoMaquinaria', () => {
  let service: EquipoMaquinaria;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(EquipoMaquinaria);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
