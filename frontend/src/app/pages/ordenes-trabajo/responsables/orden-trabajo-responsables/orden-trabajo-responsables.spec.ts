import { ComponentFixture, TestBed } from '@angular/core/testing';

import { OrdenTrabajoResponsables } from './orden-trabajo-responsables';

describe('OrdenTrabajoResponsables', () => {
  let component: OrdenTrabajoResponsables;
  let fixture: ComponentFixture<OrdenTrabajoResponsables>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [OrdenTrabajoResponsables],
    }).compileComponents();

    fixture = TestBed.createComponent(OrdenTrabajoResponsables);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
