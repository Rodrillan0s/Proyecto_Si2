import { isPlatformBrowser } from '@angular/common';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Injectable, PLATFORM_ID, inject } from '@angular/core';
import { environment } from '../../environments/environment';

export type EstadoPago = 'PENDIENTE' | 'CONFIRMADO' | 'FALLIDO' | 'CANCELADO';

export interface PlanPago {
  codigo: string;
  nombre: string;
  descripcion: string;
  precio_menor: number;
  moneda: string;
  periodo_meses: number;
  version_precio: number;
}

export interface InicioCheckout {
  id_pago: number;
  estado: EstadoPago;
  checkout_url: string;
  checkout_expira_en: string | null;
}

export interface PagoEmpresa {
  id_pago: number;
  codigo_plan: string;
  nombre_plan: string;
  monto_menor: number;
  moneda: string;
  estado: EstadoPago;
  fecha: string;
  confirmado_en: string | null;
  stripe_checkout_session_id: string | null;
  stripe_payment_intent_id: string | null;
  stripe_checkout_url: string | null;
  stripe_receipt_url: string | null;
}

export interface PagoDetalle {
  id_pago: number;
  id_empresa: number;
  codigo_plan: string;
  monto_menor: number;
  moneda: string;
  estado: EstadoPago;
  creado_en: string;
  confirmado_en: string | null;
  stripe_checkout_session_id: string | null;
  stripe_payment_intent_id: string | null;
  stripe_receipt_url: string | null;
}

export interface ComprobantePago {
  id_pago: number;
  codigo_plan: string;
  nombre_plan: string;
  monto_menor: number;
  moneda: string;
  estado: EstadoPago;
  confirmado_en: string | null;
  stripe_checkout_session_id: string | null;
  stripe_payment_intent_id: string | null;
  stripe_receipt_url: string | null;
}

export interface VerificacionPago {
  id_pago: number;
  estado: EstadoPago;
  tipo_aplicacion: 'CONTRATACION' | 'RENOVACION' | 'CAMBIO_PLAN' | null;
  aplicado: boolean;
}

interface RespuestaApi<T> {
  success: boolean;
  data: T;
}

@Injectable({ providedIn: 'root' })
export class PagosService {
  private http = inject(HttpClient);
  private url = `${environment.apiUrl}/api/pagos`;

  planes() {
    return this.http.get<RespuestaApi<PlanPago[]>>(`${this.url}/planes`);
  }

  iniciarCheckout(codigoPlan: string, idempotencyKey = this.nuevaClaveIdempotencia()) {
    const headers = new HttpHeaders({ 'Idempotency-Key': idempotencyKey });
    return this.http.post<RespuestaApi<InicioCheckout>>(
      `${this.url}/checkout-sessions`,
      { codigo_plan: codigoPlan },
      { headers },
    );
  }

  pago(idPago: number) {
    return this.http.get<RespuestaApi<PagoDetalle>>(`${this.url}/${idPago}`);
  }

  miEmpresa() {
    return this.http.get<RespuestaApi<PagoEmpresa[]>>(`${this.url}/mi-empresa`);
  }

  comprobante(idPago: number) {
    return this.http.get<RespuestaApi<ComprobantePago>>(`${this.url}/${idPago}/comprobante`);
  }

  verificar(idPago: number) {
    return this.http.post<RespuestaApi<VerificacionPago>>(`${this.url}/${idPago}/verificar`, {});
  }

  nuevaClaveIdempotencia(): string {
    if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
      return `cu37-${crypto.randomUUID()}`;
    }
    return `cu37-${Date.now()}-${Math.random().toString(36).slice(2)}`;
  }
}

@Injectable({ providedIn: 'root' })
export class CheckoutFlowService {
  private platformId = inject(PLATFORM_ID);
  private readonly storageKey = 'cu37_ultimo_pago';

  redirigir(idPago: number, checkoutUrl: string): void {
    if (!isPlatformBrowser(this.platformId)) return;
    sessionStorage.setItem(this.storageKey, String(idPago));
    window.location.assign(checkoutUrl);
  }

  ultimoPagoId(): number | null {
    if (!isPlatformBrowser(this.platformId)) return null;
    const valor = Number(sessionStorage.getItem(this.storageKey));
    return Number.isInteger(valor) && valor > 0 ? valor : null;
  }
}
