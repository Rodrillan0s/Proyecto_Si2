import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

// ─────────────────────────────────────────────────────────────────────────────
// Interfaces
// ─────────────────────────────────────────────────────────────────────────────
export type EstadoProveedor = 'ACTIVO' | 'INACTIVO';

export interface Proveedor {
  id_proveedor: number;
  nombre: string;
  nit: string;
  telefono?: string | null;
  email?: string | null;
  direccion?: string | null;
  contacto?: string | null;
  estado: EstadoProveedor;
  id_empresa: number;
  created_at?: string;
  updated_at?: string;
}

export interface ProveedorMaterial {
  id_material: number;
  codigo: string;
  nombre_material: string;
  descripcion?: string | null;
  estado: string;
  asociado_en?: string;
}

export interface ProveedorCreatePayload {
  nombre: string;
  nit: string;
  telefono?: string | null;
  email?: string | null;
  direccion?: string | null;
  contacto?: string | null;
}

export type ProveedorUpdatePayload = ProveedorCreatePayload;

export interface ProveedorPagination {
  page: number;
  limit: number;
  total: number;
  total_pages: number;
}

export interface ProveedorListResponse {
  success: boolean;
  data: Proveedor[];
  pagination: ProveedorPagination;
}

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
}

export interface ProveedorMutationResponse {
  success: boolean;
  message: string;
  id_proveedor?: number;
}

export interface AsociarMaterialesResponse {
  success: boolean;
  nuevas_asociaciones: number;
  message: string;
}

export interface ProveedorFilters {
  q?: string;
  estado?: EstadoProveedor;
  page?: number;
  limit?: number;
}

// ─────────────────────────────────────────────────────────────────────────────
// Servicio
// ─────────────────────────────────────────────────────────────────────────────
@Injectable({ providedIn: 'root' })
export class ProveedorService {
  private http = inject(HttpClient);
  private readonly url = `${environment.apiUrl}/api/proveedores`;

  listar(filtros: ProveedorFilters): Observable<ProveedorListResponse> {
    let params = new HttpParams();
    Object.entries(filtros).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        params = params.set(key, String(value));
      }
    });
    return this.http.get<ProveedorListResponse>(this.url, { params });
  }

  obtener(id: number): Observable<ApiResponse<Proveedor>> {
    return this.http.get<ApiResponse<Proveedor>>(`${this.url}/${id}`);
  }

  registrar(payload: ProveedorCreatePayload): Observable<ProveedorMutationResponse> {
    return this.http.post<ProveedorMutationResponse>(this.url, payload);
  }

  modificar(id: number, payload: ProveedorUpdatePayload): Observable<ProveedorMutationResponse> {
    return this.http.put<ProveedorMutationResponse>(`${this.url}/${id}`, payload);
  }

  cambiarEstado(id: number, estado: EstadoProveedor): Observable<ProveedorMutationResponse> {
    return this.http.patch<ProveedorMutationResponse>(`${this.url}/${id}/estado`, { estado });
  }

  listarMateriales(id: number): Observable<ApiResponse<ProveedorMaterial[]>> {
    return this.http.get<ApiResponse<ProveedorMaterial[]>>(`${this.url}/${id}/materiales`);
  }

  asociarMateriales(id: number, ids_material: number[]): Observable<AsociarMaterialesResponse> {
    return this.http.post<AsociarMaterialesResponse>(
      `${this.url}/${id}/materiales`,
      { ids_material }
    );
  }

  desasociarMaterial(id_proveedor: number, id_material: number): Observable<ProveedorMutationResponse> {
    return this.http.delete<ProveedorMutationResponse>(
      `${this.url}/${id_proveedor}/materiales/${id_material}`
    );
  }
}
