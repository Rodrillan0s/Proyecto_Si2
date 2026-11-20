import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { PagosService } from './pagos';

describe('PagosService', () => {
  let service: PagosService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({ providers: [provideHttpClient(), provideHttpClientTesting()] });
    service = TestBed.inject(PagosService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('carga los planes comerciales', () => {
    service.planes().subscribe(respuesta => expect(respuesta.data[0].codigo).toBe('PROFESIONAL'));
    const req = http.expectOne(request => request.method === 'GET' && request.url.endsWith('/api/pagos/planes'));
    req.flush({ success: true, data: [{ codigo: 'PROFESIONAL' }] });
  });

  it('inicia Checkout enviando solo codigo_plan y la cabecera idempotente', () => {
    service.iniciarCheckout('PROFESIONAL', 'cu37-prueba-123').subscribe();
    const req = http.expectOne(request => request.method === 'POST' && request.url.endsWith('/checkout-sessions'));
    expect(req.request.body).toEqual({ codigo_plan: 'PROFESIONAL' });
    expect(req.request.headers.get('Idempotency-Key')).toBe('cu37-prueba-123');
    expect(req.request.body).not.toHaveProperty('monto_menor');
    expect(req.request.body).not.toHaveProperty('id_empresa');
    req.flush({ success: true, data: { id_pago: 5, checkout_url: 'https://checkout.stripe.com/test' } });
  });

  it('consume historial, comprobante y verificación sin estado manual', () => {
    service.miEmpresa().subscribe();
    http.expectOne(request => request.method === 'GET' && request.url.endsWith('/mi-empresa')).flush({ success: true, data: [] });
    service.comprobante(8).subscribe();
    http.expectOne(request => request.method === 'GET' && request.url.endsWith('/8/comprobante')).flush({ success: true, data: {} });
    service.verificar(8).subscribe();
    const verificar = http.expectOne(request => request.method === 'POST' && request.url.endsWith('/8/verificar'));
    expect(verificar.request.body).toEqual({});
    verificar.flush({ success: true, data: { id_pago: 8, estado: 'CONFIRMADO', aplicado: true } });
  });
});
