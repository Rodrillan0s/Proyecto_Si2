import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export type EstadoMaterial = 'ACTIVO' | 'INACTIVO';

export interface CategoriaMaterial { id_categoria: number; nombre: string; descripcion?: string | null; }
export interface UnidadMedida { id_unidad_medida: number; nombre: string; abreviatura: string; }
export interface MaterialCaracteristica { id_caracteristica?: number; nombre: string; valor: string; }

export interface Material {
  id_material: number;
  codigo: string;
  nombre_material: string;
  descripcion?: string | null;
  categoria: CategoriaMaterial;
  unidad_medida: UnidadMedida;
  precio: number;
  stock_actual: number;
  stock_minimo: number;
  stock_bajo: boolean;
  estado: EstadoMaterial;
  caracteristicas?: MaterialCaracteristica[];
  fecha_ingreso?: string;
  created_at?: string;
  updated_at?: string;
}

export interface MaterialCreatePayload {
  codigo: string;
  nombre_material: string;
  descripcion: string | null;
  id_categoria: number;
  id_unidad_medida: number;
  precio: number | null;
  caracteristicas: MaterialCaracteristica[];
  cantidad_inicial: number;
  stock_minimo: number;
  fecha_ingreso: string;
}

export type MaterialUpdatePayload = Omit<MaterialCreatePayload, 'cantidad_inicial' | 'fecha_ingreso'>;
export interface MaterialPagination { page: number; limit: number; total: number; total_pages: number; }
export interface MaterialListResponse { success: boolean; data: Material[]; pagination: MaterialPagination; }
export interface ApiResponse<T> { success: boolean; data: T; message?: string; }
export interface MaterialMutationResponse { success: boolean; message: string; id_material?: number; }
export interface MaterialFilters { q?: string; id_categoria?: number; estado?: EstadoMaterial; stock_bajo?: boolean; page?: number; limit?: number; }
export interface CategoriaCreatePayload { nombre: string; descripcion: string | null; }
export interface CategoriaMutationResponse { success: boolean; data: CategoriaMaterial; message: string; }

@Injectable({ providedIn: 'root' })
export class MaterialsService {
  private http = inject(HttpClient);
  private readonly url = `${environment.apiUrl}/api/materiales`;

  listar(filtros: MaterialFilters): Observable<MaterialListResponse> {
    let params = new HttpParams();
    Object.entries(filtros).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') params = params.set(key, String(value));
    });
    return this.http.get<MaterialListResponse>(this.url, { params });
  }

  obtener(id: number): Observable<ApiResponse<Material>> { return this.http.get<ApiResponse<Material>>(`${this.url}/${id}`); }
  registrar(payload: MaterialCreatePayload): Observable<MaterialMutationResponse> { return this.http.post<MaterialMutationResponse>(this.url, payload); }
  modificar(id: number, payload: MaterialUpdatePayload): Observable<MaterialMutationResponse> { return this.http.put<MaterialMutationResponse>(`${this.url}/${id}`, payload); }
  cambiarEstado(id: number, estado: EstadoMaterial): Observable<MaterialMutationResponse> { return this.http.patch<MaterialMutationResponse>(`${this.url}/${id}/estado`, { estado }); }
  categorias(): Observable<ApiResponse<CategoriaMaterial[]>> { return this.http.get<ApiResponse<CategoriaMaterial[]>>(`${this.url}/categorias`); }
  crearCategoria(payload: CategoriaCreatePayload): Observable<CategoriaMutationResponse> { return this.http.post<CategoriaMutationResponse>(`${this.url}/categorias`, payload); }
  unidadesMedida(): Observable<ApiResponse<UnidadMedida[]>> { return this.http.get<ApiResponse<UnidadMedida[]>>(`${this.url}/unidades-medida`); }
}
