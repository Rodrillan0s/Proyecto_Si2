import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export type EstadoOrdenCompra =
  | 'BORRADOR'
  | 'PENDIENTE_APROBACION'
  | 'APROBADA'
  | 'RECHAZADA'
  | 'CANCELADA'
  | 'RECIBIDA_PARCIAL'
  | 'RECIBIDA';

export interface OrdenCompraDetalle {
  id_detalle: number;
  id_orden_compra: number;
  id_material: number;
  codigo_material: string;
  nombre_material: string;
  unidad_medida: string;
  cantidad_solicitada: number;
  cantidad_recibida: number;
  cantidad_pendiente: number;
  precio_unitario: number;
  subtotal: number;
}

export interface RecepcionCompra {
  id_recepcion: number;
  id_orden_compra: number;
  id_empresa: number;
  numero_recepcion: string;
  fecha_recepcion: string;
  id_usuario_recepcion: number;
  nombre_usuario_recepcion: string;
  observaciones?: string | null;
  total_items: number;
  total_cantidad_recibida: number;
  created_at: string;
}

export interface OrdenCompra {
  id_orden_compra: number;
  id_empresa: number;
  nombre_empresa?: string;
  id_proveedor: number;
  proveedor_razon_social: string;
  proveedor_nit: string;
  numero_orden: string;
  fecha: string;
  observaciones?: string | null;
  estado: EstadoOrdenCompra;
  id_usuario_solicitante: number;
  nombre_solicitante: string;
  email_solicitante?: string;
  subtotal: number;
  total: number;
  id_usuario_aprobacion?: number | null;
  nombre_aprobador?: string | null;
  fecha_aprobacion?: string | null;
  observacion_aprobacion?: string | null;
  created_at: string;
  updated_at: string;
  detalles?: OrdenCompraDetalle[];
  recepciones?: RecepcionCompra[];
}

export interface DetalleItemPayload {
  id_material: number;
  cantidad_solicitada: number;
  precio_unitario: number;
}

export interface OrdenCompraCreatePayload {
  id_empresa?: number;
  id_proveedor: number;
  fecha?: string;
  observaciones?: string;
  enviar_aprobacion?: boolean;
  detalles: DetalleItemPayload[];
}

export interface RecepcionItemPayload {
  id_material: number;
  cantidad_recibida: number;
  precio_unitario?: number;
}

export interface RecepcionCreatePayload {
  observaciones?: string;
  detalles: RecepcionItemPayload[];
}

export interface ComprasPagination {
  page: number;
  limit: number;
  total: number;
  total_pages: number;
}

export interface ComprasResponse<T> {
  success: boolean;
  data: T;
  message?: string;
  pagination?: ComprasPagination;
}

@Injectable({
  providedIn: 'root'
})
export class ComprasService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.apiUrl}/api/compras`;

  listar(filtros?: {
    id_empresa?: number;
    estado?: string;
    id_proveedor?: number;
    fecha_desde?: string;
    fecha_hasta?: string;
    q?: string;
    page?: number;
    limit?: number;
  }): Observable<ComprasResponse<OrdenCompra[]>> {
    let params = new HttpParams();
    if (filtros) {
      if (filtros.id_empresa) params = params.set('id_empresa', filtros.id_empresa.toString());
      if (filtros.estado) params = params.set('estado', filtros.estado);
      if (filtros.id_proveedor) params = params.set('id_proveedor', filtros.id_proveedor.toString());
      if (filtros.fecha_desde) params = params.set('fecha_desde', filtros.fecha_desde);
      if (filtros.fecha_hasta) params = params.set('fecha_hasta', filtros.fecha_hasta);
      if (filtros.q) params = params.set('q', filtros.q);
      if (filtros.page) params = params.set('page', filtros.page.toString());
      if (filtros.limit) params = params.set('limit', filtros.limit.toString());
    }
    return this.http.get<ComprasResponse<OrdenCompra[]>>(this.baseUrl, { params });
  }

  obtener(id_orden: number): Observable<ComprasResponse<OrdenCompra>> {
    return this.http.get<ComprasResponse<OrdenCompra>>(`${this.baseUrl}/${id_orden}`);
  }

  crear(payload: OrdenCompraCreatePayload): Observable<ComprasResponse<number>> {
    return this.http.post<ComprasResponse<number>>(this.baseUrl, payload);
  }

  cambiarEstado(id_orden: number, estado: 'PENDIENTE_APROBACION' | 'CANCELADA', observacion?: string): Observable<ComprasResponse<void>> {
    return this.http.patch<ComprasResponse<void>>(`${this.baseUrl}/${id_orden}/estado`, { estado, observacion });
  }

  aprobar(id_orden: number, observacion?: string): Observable<ComprasResponse<void>> {
    return this.http.post<ComprasResponse<void>>(`${this.baseUrl}/${id_orden}/aprobar`, { observacion });
  }

  rechazar(id_orden: number, observacion: string): Observable<ComprasResponse<void>> {
    return this.http.post<ComprasResponse<void>>(`${this.baseUrl}/${id_orden}/rechazar`, { observacion });
  }

  registrarRecepcion(id_orden: number, payload: RecepcionCreatePayload): Observable<ComprasResponse<{ id_recepcion: number }>> {
    return this.http.post<ComprasResponse<{ id_recepcion: number }>>(`${this.baseUrl}/${id_orden}/recepciones`, payload);
  }
}
