import { ComponentFixture, TestBed } from '@angular/core/testing';

import { OrdenTrabajoEstructura } from './orden-trabajo-estructura';

describe('OrdenTrabajoEstructura', () => {
  let component: OrdenTrabajoEstructura;
  let fixture: ComponentFixture<OrdenTrabajoEstructura>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [OrdenTrabajoEstructura],
    }).compileComponents();

    fixture = TestBed.createComponent(OrdenTrabajoEstructura);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
