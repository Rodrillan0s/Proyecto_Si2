import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { AuthService } from '../../services/auth';
import { CheckoutFlowService, PagosService } from '../../services/pagos';
import { SuscripcionService } from '../../services/suscripcion';
import { NAVIGATION } from '../../layouts/admin-layout/navegacion';
import { PagosComponent } from './pagos';

const plan = {
  codigo: 'PROFESIONAL', nombre: 'Profesional', descripcion: 'Plan profesional',
  precio_menor: 24900, moneda: 'BOB', periodo_meses: 1, version_precio: 1,
};
const suscripcion = {
  id_empresa: 3, nombre_empresa: 'La Roca', codigo_plan: 'PROFESIONAL', nombre_plan: 'Profesional',
  estado: 'ACTIVA', estado_efectivo: 'ACTIVA', fecha_inicio: '2026-10-25', fecha_fin: '2026-11-24', usuarios: 2,
};
const historial = [{
  id_pago: 4, codigo_plan: 'PROFESIONAL', nombre_plan: 'Profesional', monto_menor: 24900,
  moneda: 'BOB', estado: 'CONFIRMADO', fecha: '2026-10-25T19:00:00Z', confirmado_en: '2026-10-25T19:02:00Z',
  stripe_checkout_session_id: 'cs_test_4', stripe_payment_intent_id: 'pi_4',
  stripe_checkout_url: null, stripe_receipt_url: 'https://pay.stripe.com/receipt/4',
}];

describe('PagosComponent', () => {
  afterEach(() => TestBed.resetTestingModule());

  function crear(rol: 'ADMINISTRADOR' | 'ADMINISTRADOR_EMPRESA') {
    const pagos = {
      planes: vi.fn(() => of({ success: true, data: [plan] })),
      miEmpresa: vi.fn(() => of({ success: true, data: historial })),
      iniciarCheckout: vi.fn(() => of({ success: true, data: {
        id_pago: 5, estado: 'PENDIENTE', checkout_url: 'https://checkout.stripe.com/c/pay/test', checkout_expira_en: null,
      } })),
      nuevaClaveIdempotencia: vi.fn(() => 'cu37-component-test'),
      comprobante: vi.fn(() => of({ success: true, data: {
        ...historial[0], confirmado_en: historial[0].confirmado_en,
      } })),
      pago: vi.fn(() => of({ success: true, data: {
        id_pago: 9, id_empresa: 3, codigo_plan: 'PROFESIONAL', monto_menor: 24900, moneda: 'BOB',
        estado: 'PENDIENTE', creado_en: '2026-10-25T19:00:00Z', confirmado_en: null,
        stripe_checkout_session_id: 'cs_test_9', stripe_payment_intent_id: null, stripe_receipt_url: null,
      } })),
      verificar: vi.fn(() => of({ success: true, data: {
        id_pago: 9, estado: 'CONFIRMADO', tipo_aplicacion: 'RENOVACION', aplicado: true,
      } })),
    };
    const suscripcionesApi = {
      planes: vi.fn(() => of({ data: [{ ...plan, prestaciones: ['Gestión de obras'], limite_usuarios: 15, limite_obras: 10 }] })),
      propia: vi.fn(() => of({ data: suscripcion })),
    };
    const flujo = { redirigir: vi.fn(), ultimoPagoId: vi.fn(() => 5) };
    TestBed.configureTestingModule({
      imports: [PagosComponent],
      providers: [provideRouter([]),
        { provide: AuthService, useValue: { obtenerRolNormalizado: () => rol } },
        { provide: PagosService, useValue: pagos },
        { provide: SuscripcionService, useValue: suscripcionesApi },
        { provide: CheckoutFlowService, useValue: flujo },
      ],
    });
    const fixture = TestBed.createComponent(PagosComponent);
    fixture.detectChanges();
    return { fixture, component: fixture.componentInstance, pagos, flujo };
  }

  it('carga planes, plan actual e historial propio', () => {
    const { fixture } = crear('ADMINISTRADOR_EMPRESA');
    expect(fixture.nativeElement.textContent).toContain('Profesional');
    expect(fixture.nativeElement.textContent).toContain('Gestión de obras');
    expect(fixture.nativeElement.textContent).toContain('Historial de pagos');
    expect(fixture.nativeElement.textContent).toContain('#4');
  });

  it('inicia Checkout y delega la redirección a la URL recibida', () => {
    const { component, pagos, flujo } = crear('ADMINISTRADOR_EMPRESA');
    component.iniciarPago({ ...plan, prestaciones: [] });
    expect(pagos.iniciarCheckout).toHaveBeenCalledWith('PROFESIONAL', 'cu37-component-test');
    expect(flujo.redirigir).toHaveBeenCalledWith(5, 'https://checkout.stripe.com/c/pay/test');
  });

  it('carga un comprobante con referencias Stripe', () => {
    const { component, pagos } = crear('ADMINISTRADOR_EMPRESA');
    component.verComprobante(4);
    expect(pagos.comprobante).toHaveBeenCalledWith(4);
    expect(component.comprobante()?.stripe_payment_intent_id).toBe('pi_4');
  });

  it('permite al ADMINISTRADOR consultar y verificar un pendiente', () => {
    const { component, pagos } = crear('ADMINISTRADOR');
    component.idConsulta = 9;
    component.buscarPago();
    component.verificarPago();
    expect(pagos.verificar).toHaveBeenCalledWith(9);
  });

  it('no permite verificación global desde ADMINISTRADOR_EMPRESA', () => {
    const { component, pagos } = crear('ADMINISTRADOR_EMPRESA');
    component.pagoConsultado.set({
      id_pago: 9, id_empresa: 3, codigo_plan: 'PROFESIONAL', monto_menor: 24900, moneda: 'BOB',
      estado: 'PENDIENTE', creado_en: '2026-10-25T19:00:00Z', confirmado_en: null,
      stripe_checkout_session_id: 'cs_test_9', stripe_payment_intent_id: null, stripe_receipt_url: null,
    });
    component.verificarPago();
    expect(pagos.verificar).not.toHaveBeenCalled();
  });

  it('declara opciones de menú aisladas por rol', () => {
    const items = NAVIGATION.flatMap(seccion => seccion.items);
    expect(items.find(item => item.id === 'pagos-saas')?.roles).toEqual(['ADMINISTRADOR']);
    expect(items.find(item => item.id === 'pagos-empresa')?.roles).toEqual(['ADMINISTRADOR_EMPRESA']);
  });
});
