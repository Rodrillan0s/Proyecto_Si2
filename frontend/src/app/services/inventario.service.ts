import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export type EstadoStock = 'EN_STOCK' | 'STOCK_BAJO' | 'SIN_STOCK';

export interface ItemInventario {
  id_material: number;
  codigo: string;
  nombre_material: string;
  descripcion?: string | null;
  id_categoria?: number | null;
  categoria_nombre?: string | null;
  id_unidad_medida?: number | null;
  unidad_nombre?: string | null;
  unidad_abreviatura?: string | null;
  precio: number;
  stock_actual: number;
  stock_minimo: number;
  valor_total: number;
  estado_stock: EstadoStock;
  id_empresa: number;
  nombre_empresa?: string | null;
  total_count?: number;
}

export interface KpisInventario {
  total_materiales: number;
  total_con_stock: number;
  total_sin_stock: number;
  total_stock_bajo: number;
  valor_total_inventario: number;
  total_movimientos_mes: number;
}

export interface MovimientoAlmacen {
  id_movimiento: number;
  fecha_movimiento: string;
  created_at: string;
  tipo_movimiento: string;
  cantidad_asignada: number;
  id_material: number;
  material_codigo: string;
  material_nombre: string;
  unidad_abreviatura?: string | null;
  id_orden_compra?: number | null;
  numero_orden?: string | null;
  id_recepcion?: number | null;
  numero_recepcion?: string | null;
  id_usuario?: number | null;
  nombre_usuario?: string | null;
  observaciones?: string | null;
  total_count?: number;
}

export interface AjusteStockPayload {
  id_empresa?: number | null;
  id_material: number;
  cantidad: number;
  tipo_movimiento: 'ENTRADA_AJUSTE' | 'SALIDA_AJUSTE' | 'AJUSTE_INVENTARIO';
  observaciones: string;
  stock_minimo?: number | null;
}

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  total?: number;
  page?: number;
  limit?: number;
  message?: string;
}

@Injectable({
  providedIn: 'root'
})
export class InventarioService {
  private http = inject(HttpClient);
  private apiUrl = `${environment.apiUrl}/api/inventario`;

  listarStock(params?: {
    id_categoria?: number;
    estado_stock?: string;
    q?: string;
    page?: number;
    limit?: number;
    id_empresa?: number;
  }): Observable<ApiResponse<ItemInventario[]>> {
    let httpParams = new HttpParams();
    if (params?.id_categoria) httpParams = httpParams.set('id_categoria', params.id_categoria);
    if (params?.estado_stock) httpParams = httpParams.set('estado_stock', params.estado_stock);
    if (params?.q) httpParams = httpParams.set('q', params.q);
    if (params?.page) httpParams = httpParams.set('page', params.page);
    if (params?.limit) httpParams = httpParams.set('limit', params.limit);
    if (params?.id_empresa) httpParams = httpParams.set('id_empresa', params.id_empresa);

    return this.http.get<ApiResponse<ItemInventario[]>>(`${this.apiUrl}/stock`, { params: httpParams });
  }

  obtenerKpis(id_empresa?: number): Observable<ApiResponse<KpisInventario>> {
    let httpParams = new HttpParams();
    if (id_empresa) httpParams = httpParams.set('id_empresa', id_empresa);

    return this.http.get<ApiResponse<KpisInventario>>(`${this.apiUrl}/kpis`, { params: httpParams });
  }

  listarMovimientos(params?: {
    id_material?: number;
    tipo_movimiento?: string;
    page?: number;
    limit?: number;
    id_empresa?: number;
  }): Observable<ApiResponse<MovimientoAlmacen[]>> {
    let httpParams = new HttpParams();
    if (params?.id_material) httpParams = httpParams.set('id_material', params.id_material);
    if (params?.tipo_movimiento) httpParams = httpParams.set('tipo_movimiento', params.tipo_movimiento);
    if (params?.page) httpParams = httpParams.set('page', params.page);
    if (params?.limit) httpParams = httpParams.set('limit', params.limit);
    if (params?.id_empresa) httpParams = httpParams.set('id_empresa', params.id_empresa);

    return this.http.get<ApiResponse<MovimientoAlmacen[]>>(`${this.apiUrl}/movimientos`, { params: httpParams });
  }

  registrarAjuste(payload: AjusteStockPayload): Observable<ApiResponse<any>> {
    return this.http.post<ApiResponse<any>>(`${this.apiUrl}/ajuste`, payload);
  }
}
