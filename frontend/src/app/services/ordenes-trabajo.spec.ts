import { TestBed } from '@angular/core/testing';

import { OrdenesTrabajo } from './ordenes-trabajo';

describe('OrdenesTrabajo', () => {
  let service: OrdenesTrabajo;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(OrdenesTrabajo);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
