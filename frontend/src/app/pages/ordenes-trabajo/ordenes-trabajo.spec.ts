import { ComponentFixture, TestBed } from '@angular/core/testing';

import { OrdenesTrabajo } from './ordenes-trabajo';

describe('OrdenesTrabajo', () => {
  let component: OrdenesTrabajo;
  let fixture: ComponentFixture<OrdenesTrabajo>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [OrdenesTrabajo],
    }).compileComponents();

    fixture = TestBed.createComponent(OrdenesTrabajo);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
