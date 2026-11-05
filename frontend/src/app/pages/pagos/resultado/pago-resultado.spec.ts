import { convertToParamMap, ActivatedRoute } from '@angular/router';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { CheckoutFlowService, PagosService } from '../../../services/pagos';
import { PagoResultadoComponent } from './pago-resultado';

describe('PagoResultadoComponent', () => {
  afterEach(() => TestBed.resetTestingModule());

  function crear(status: string, idPago: number | null = 7) {
    const pagos = {
      pago: vi.fn(() => of({ success: true, data: {
        id_pago: 7, id_empresa: 3, codigo_plan: 'PROFESIONAL', monto_menor: 24900, moneda: 'BOB',
        estado: 'PENDIENTE', creado_en: '2026-10-25T19:00:00Z', confirmado_en: null,
        stripe_checkout_session_id: 'cs_test_7', stripe_payment_intent_id: null, stripe_receipt_url: null,
      } })),
      verificar: vi.fn(() => of({ success: true, data: {
        id_pago: 7, estado: 'CONFIRMADO', tipo_aplicacion: 'RENOVACION', aplicado: true,
      } })),
    };
    TestBed.configureTestingModule({
      imports: [PagoResultadoComponent],
      providers: [provideRouter([]),
        { provide: ActivatedRoute, useValue: { snapshot: { queryParamMap: convertToParamMap({ status }) } } },
        { provide: PagosService, useValue: pagos },
        { provide: CheckoutFlowService, useValue: { ultimoPagoId: () => idPago } },
      ],
    });
    const fixture = TestBed.createComponent(PagoResultadoComponent);
    fixture.detectChanges();
    return { fixture, pagos };
  }

  it('consulta el pago guardado al volver con success', () => {
    const { fixture, pagos } = crear('success');
    expect(pagos.pago).toHaveBeenCalledWith(7);
    expect(fixture.nativeElement.textContent).toContain('Pago recibido, verificando...');
    expect(fixture.nativeElement.textContent).toContain('PENDIENTE');
  });

  it('Actualizar estado verifica en Stripe y luego refresca el pago', () => {
    const { fixture, pagos } = crear('success');
    fixture.nativeElement.querySelector('button').click();
    expect(pagos.verificar).toHaveBeenCalledWith(7);
    expect(pagos.pago).toHaveBeenCalledTimes(2);
  });

  it('muestra cancel sin consultar ni activar la suscripción', () => {
    const { fixture, pagos } = crear('cancel');
    expect(pagos.pago).not.toHaveBeenCalled();
    expect(fixture.nativeElement.textContent).toContain('El pago no se completó');
    expect(fixture.nativeElement.textContent).toContain('Volver a planes');
  });
});
