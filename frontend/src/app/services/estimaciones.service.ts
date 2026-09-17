import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface Apu {
  id_analisis_precio_unitario: number;
  id_obra?: number | null;
  id_padre?: number | null;
  id_estructura?: number | null;
  nombre: string;
  descripcion?: string | null;
  id_unidad_medida?: number;
  abreviatura?: string;
  unidad_nombre?: string;
  tipo_analisis_precio_unitario: string;
  calidad?: string | null;
  activo: boolean;
  costo_directo_unitario: number;
}

export interface ApuInsumo {
  id_analisis_precio_unitario_insumo: number;
  id_analisis_precio_unitario?: number;
  tipo_insumo: string;
  id_material?: number | null;
  id_mano_obra?: number | null;
  nombre: string;
  id_unidad_medida: number;
  cantidad: number;
  precio_unitario: number;
  orden: number;
}

export interface ApuDetalle {
  id_analisis_precio_unitario: number;
  nombre: string;
  descripcion?: string | null;
  id_unidad_medida?: number;
  tipo_analisis_precio_unitario: string;
  calidad?: string | null;
  activo: boolean;
  insumos: ApuInsumo[];
  calculo?: { costo_directo_unitario: number; apu?: any; insumos?: any[] };
}

export interface ManoObra {
  id_mano_obra: number;
  nombre: string;
  descripcion?: string | null;
  id_unidad_medida: number;
  costo_unitario: number;
  activo: boolean;
}

export interface Estimacion {
  id_estimacion: number;
  id_obra: number;
  nombre: string;
  version: number;
  estado: string;
  descripcion?: string | null;
  factor_utilidad?: number | null;
  monto_total?: number;
  calculo?: { monto_total: number; subtotal_directo: number; utilidad: number; detalle?: EstimacionDetalle[] } | null;
}

export interface EstimacionDetalle {
  id_analisis_precio_unitario: number;
  id_estimacion_analisis_precio_unitario?: number;
  nombre: string;
  unidad: string;
  costo_unitario: number;
  cantidad: number;
  subtotal: number;
}

export interface ApiResponse<T> { success: boolean; data: T; }

@Injectable({ providedIn: 'root' })
export class EstimacionesService {
  private readonly http = inject(HttpClient);
  private readonly api = `${environment.apiUrl}/api/estimaciones`;

  private params(filtros: Record<string, any>): HttpParams {
    let params = new HttpParams();
    Object.entries(filtros).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') params = params.set(key, String(value));
    });
    return params;
  }

  listarApu(filtros: { id_obra?: number; tipo_analisis_precio_unitario?: string; calidad?: string } = {}): Observable<ApiResponse<Apu[]>> {
    return this.http.get<ApiResponse<Apu[]>>(`${this.api}/analisis_precio_unitario`, { params: this.params(filtros) });
  }

  detalleApu(idApu: number): Observable<ApiResponse<ApuDetalle>> {
    return this.http.get<ApiResponse<ApuDetalle>>(`${this.api}/analisis_precio_unitario/${idApu}`);
  }

  crearApu(data: any): Observable<ApiResponse<{ id_analisis_precio_unitario: number }>> {
    return this.http.post<ApiResponse<{ id_analisis_precio_unitario: number }>>(`${this.api}/analisis_precio_unitario`, data);
  }

  actualizarApu(idApu: number, data: any): Observable<ApiResponse<any>> {
    return this.http.put<ApiResponse<any>>(`${this.api}/analisis_precio_unitario/${idApu}`, data);
  }

  duplicarApu(idApu: number): Observable<ApiResponse<{ id_analisis_precio_unitario: number }>> {
    return this.http.post<ApiResponse<{ id_analisis_precio_unitario: number }>>(`${this.api}/analisis_precio_unitario/${idApu}/duplicar`, {});
  }

  listarInsumos(idApu: number): Observable<ApiResponse<ApuInsumo[]>> {
    return this.http.get<ApiResponse<ApuInsumo[]>>(`${this.api}/analisis_precio_unitario/${idApu}/insumos`);
  }

  crearInsumo(idApu: number, data: any): Observable<ApiResponse<{ id_analisis_precio_unitario_insumo: number }>> {
    return this.http.post<ApiResponse<{ id_analisis_precio_unitario_insumo: number }>>(`${this.api}/analisis_precio_unitario/${idApu}/insumos`, data);
  }

  actualizarInsumo(idApu: number, insumoId: number, data: any): Observable<ApiResponse<any>> {
    return this.http.put<ApiResponse<any>>(`${this.api}/analisis_precio_unitario/${idApu}/insumos/${insumoId}`, data);
  }

  eliminarInsumo(idApu: number, insumoId: number): Observable<ApiResponse<any>> {
    return this.http.delete<ApiResponse<any>>(`${this.api}/analisis_precio_unitario/${idApu}/insumos/${insumoId}`);
  }

  listarManoObra(): Observable<ApiResponse<ManoObra[]>> {
    return this.http.get<ApiResponse<ManoObra[]>>(`${this.api}/mano-obra`);
  }

  crearManoObra(data: any): Observable<ApiResponse<{ id_mano_obra: number }>> {
    return this.http.post<ApiResponse<{ id_mano_obra: number }>>(`${this.api}/mano-obra`, data);
  }

  listarEstimaciones(idObra?: number): Observable<ApiResponse<Estimacion[]>> {
    return this.http.get<ApiResponse<Estimacion[]>>(this.api, { params: this.params({ id_obra: idObra }) });
  }

  detalleEstimacion(id: number): Observable<ApiResponse<Estimacion>> {
    return this.http.get<ApiResponse<Estimacion>>(`${this.api}/${id}`);
  }

  crearEstimacion(data: any): Observable<ApiResponse<{ id_estimacion: number }>> {
    return this.http.post<ApiResponse<{ id_estimacion: number }>>(this.api, data);
  }

  actualizarEstimacion(id: number, data: any): Observable<ApiResponse<any>> {
    return this.http.put<ApiResponse<any>>(`${this.api}/${id}`, data);
  }

  aprobarEstimacion(id: number): Observable<ApiResponse<any>> {
    return this.http.post<ApiResponse<any>>(`${this.api}/${id}/aprobar`, {});
  }

  agregarApuEstimacion(id: number, data: any): Observable<ApiResponse<{ id_estimacion_analisis_precio_unitario: number }>> {
    return this.http.post<ApiResponse<{ id_estimacion_analisis_precio_unitario: number }>>(`${this.api}/${id}/analisis_precio_unitario`, data);
  }

  actualizarDetalleEstimacion(idEstimacion: number, detId: number, data: any): Observable<ApiResponse<any>> {
    return this.http.put<ApiResponse<any>>(`${this.api}/${idEstimacion}/analisis_precio_unitario/${detId}`, data);
  }

  eliminarDetalleEstimacion(id: number, detId: number): Observable<ApiResponse<any>> {
    return this.http.delete<ApiResponse<any>>(`${this.api}/${id}/analisis_precio_unitario/${detId}`);
  }
}