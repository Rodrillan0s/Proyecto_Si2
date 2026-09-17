import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface CategoriaApu {
  id_categoria: number;
  nombre: string;
  descripcion?: string;
  icono?: string;
  activo: boolean;
  total_base: number;
  total_empresa: number;
}

export type TipoRecursoApu = 'MATERIAL' | 'MANO_OBRA' | 'EQUIPO';

export interface ApuComponente {
  id_componente?: number;
  id_apu: number;
  tipo_recurso: TipoRecursoApu;
  id_recurso?: number;
  id_material?: number;
  id_mano_obra?: number;
  id_equipo?: number;
  descripcion_recurso: string;
  id_unidad_medida: number;
  unidad_medida_nombre?: string;
  unidad_medida_abrev?: string;
  rendimiento: number;
  precio_unitario: number;
  subtotal: number;
  recurso_codigo?: string;
  created_at?: string;
}

export interface Apu {
  id_apu: number;
  id_empresa?: number;
  id_obra?: number;
  codigo: string;
  codigo_base: string;
  nombre: string;
  descripcion?: string;
  id_categoria: number;
  categoria_nombre?: string;
  categoria_icono?: string;
  id_unidad_medida: number;
  unidad_medida_nombre?: string;
  unidad_medida_abrev?: string;
  rendimiento_base: number;
  costo_materiales: number;
  costo_mano_obra: number;
  costo_equipos: number;
  costo_directo: number;
  porcentaje_gastos_generales: number;
  monto_gastos_generales: number;
  porcentaje_utilidad: number;
  monto_utilidad: number;
  porcentaje_impuestos: number;
  monto_impuestos: number;
  precio_unitario: number;
  costo_unitario_total?: number;
  version: number;
  estado: string;
  es_vigente: boolean;
  es_base: boolean;
  id_apu_base?: number;
  total_componentes?: number;
  total_partidas_usando?: number;
  en_uso?: boolean;
  created_at?: string;
  updated_at?: string;
  componentes?: ApuComponente[];
  materiales?: ApuComponente[];
  mano_obra?: ApuComponente[];
  equipos?: ApuComponente[];
}

export interface RecursoMaterial {
  id_material: number;
  codigo: string;
  nombre_material: string;
  precio: number;
  id_unidad_medida: number;
  unidad_medida_nombre?: string;
  unidad_medida_abrev?: string;
}

export interface RecursoManoObra {
  id_mano_obra: number;
  nombre: string;
  descripcion?: string;
  costo_unitario: number;
  id_unidad_medida: number;
  unidad_medida_nombre?: string;
  unidad_medida_abrev?: string;
}

export interface RecursoEquipo {
  id_equipo: number;
  codigo: string;
  nombre: string;
  descripcion?: string;
  costo_unitario: number;
  id_unidad_medida: number;
  unidad_medida_nombre?: string;
  unidad_medida_abrev?: string;
}

export interface UnidadMedida {
  id_unidad_medida: number;
  nombre: string;
  abreviatura: string;
  tipo?: string;
}

@Injectable({
  providedIn: 'root'
})
export class ApusService {
  private http = inject(HttpClient);
  private apiUrl = `${environment.apiUrl}/api/apus`;

  listarCategorias(): Observable<{ success: boolean; data: CategoriaApu[] }> {
    return this.http.get<{ success: boolean; data: CategoriaApu[] }>(`${this.apiUrl}/categorias`);
  }

  listarBase(idCategoria?: number, q?: string): Observable<{ success: boolean; data: Apu[] }> {
    let params = new HttpParams();
    if (idCategoria) params = params.set('id_categoria', idCategoria.toString());
    if (q) params = params.set('q', q);
    return this.http.get<{ success: boolean; data: Apu[] }>(`${this.apiUrl}/base`, { params });
  }

  copiarBase(idApuBase: number, data?: any): Observable<{ success: boolean; message: string; data: Apu }> {
    return this.http.post<{ success: boolean; message: string; data: Apu }>(
      `${this.apiUrl}/base/${idApuBase}/copiar`,
      data || {}
    );
  }

  listarMisApus(
    idCategoria?: number,
    soloVigentes: boolean = false,
    q?: string,
    idObra?: number,
    idEmpresa?: number
  ): Observable<{ success: boolean; data: Apu[] }> {
    let params = new HttpParams();
    if (idCategoria) params = params.set('id_categoria', idCategoria.toString());
    if (soloVigentes) params = params.set('solo_vigentes', 'true');
    if (q) params = params.set('q', q);
    if (idObra) params = params.set('id_obra', idObra.toString());
    if (idEmpresa) params = params.set('id_empresa', idEmpresa.toString());
    return this.http.get<{ success: boolean; data: Apu[] }>(`${this.apiUrl}/mis-apus`, { params });
  }

  obtenerDetalle(idApu: number): Observable<{ success: boolean; data: Apu }> {
    return this.http.get<{ success: boolean; data: Apu }>(`${this.apiUrl}/${idApu}`);
  }

  crearApu(data: any): Observable<{ success: boolean; message: string; data: Apu }> {
    return this.http.post<{ success: boolean; message: string; data: Apu }>(`${this.apiUrl}/`, data);
  }

  actualizarApu(idApu: number, data: any): Observable<{ success: boolean; message: string; data: Apu }> {
    return this.http.put<{ success: boolean; message: string; data: Apu }>(`${this.apiUrl}/${idApu}`, data);
  }

  versionarApu(idApu: number): Observable<{ success: boolean; message: string; data: Apu }> {
    return this.http.post<{ success: boolean; message: string; data: Apu }>(`${this.apiUrl}/${idApu}/versionar`, {});
  }

  duplicarApu(idApu: number, data?: any): Observable<{ success: boolean; message: string; data: Apu }> {
    return this.http.post<{ success: boolean; message: string; data: Apu }>(`${this.apiUrl}/${idApu}/duplicar`, data || {});
  }

  cambiarEstado(idApu: number, estado: 'ACTIVO' | 'INACTIVO'): Observable<{ success: boolean; message: string }> {
    return this.http.patch<{ success: boolean; message: string }>(`${this.apiUrl}/${idApu}/estado`, { estado });
  }

  siguienteCodigo(idEmpresa?: number): Observable<{ success: boolean; codigo: string }> {
    let params = new HttpParams();
    if (idEmpresa) params = params.set('id_empresa', idEmpresa.toString());
    return this.http.get<{ success: boolean; codigo: string }>(`${this.apiUrl}/siguiente-codigo`, { params });
  }

  // Componentes
  agregarComponente(idApu: number, data: any): Observable<{ success: boolean; message: string; id_componente: number; apu: Apu }> {
    return this.http.post<{ success: boolean; message: string; id_componente: number; apu: Apu }>(
      `${this.apiUrl}/${idApu}/componentes`,
      data
    );
  }

  actualizarComponente(idApu: number, idComponente: number, data: any): Observable<{ success: boolean; message: string; apu: Apu }> {
    return this.http.put<{ success: boolean; message: string; apu: Apu }>(
      `${this.apiUrl}/${idApu}/componentes/${idComponente}`,
      data
    );
  }

  eliminarComponente(idApu: number, idComponente: number): Observable<{ success: boolean; message: string; apu: Apu }> {
    return this.http.delete<{ success: boolean; message: string; apu: Apu }>(
      `${this.apiUrl}/${idApu}/componentes/${idComponente}`
    );
  }

  // Catálogos auxiliares
  recursosMateriales(q?: string, idEmpresa?: number): Observable<{ success: boolean; data: RecursoMaterial[] }> {
    let params = new HttpParams();
    if (q) params = params.set('q', q);
    if (idEmpresa) params = params.set('id_empresa', idEmpresa.toString());
    return this.http.get<{ success: boolean; data: RecursoMaterial[] }>(`${this.apiUrl}/recursos/materiales`, { params });
  }

  recursosManoObra(q?: string, idEmpresa?: number): Observable<{ success: boolean; data: RecursoManoObra[] }> {
    let params = new HttpParams();
    if (q) params = params.set('q', q);
    if (idEmpresa) params = params.set('id_empresa', idEmpresa.toString());
    return this.http.get<{ success: boolean; data: RecursoManoObra[] }>(`${this.apiUrl}/recursos/mano-obra`, { params });
  }

  recursosEquipos(q?: string, idEmpresa?: number): Observable<{ success: boolean; data: RecursoEquipo[] }> {
    let params = new HttpParams();
    if (q) params = params.set('q', q);
    if (idEmpresa) params = params.set('id_empresa', idEmpresa.toString());
    return this.http.get<{ success: boolean; data: RecursoEquipo[] }>(`${this.apiUrl}/recursos/equipos`, { params });
  }

  recursosUnidadesMedida(): Observable<{ success: boolean; data: UnidadMedida[] }> {
    return this.http.get<{ success: boolean; data: UnidadMedida[] }>(`${this.apiUrl}/recursos/unidades-medida`);
  }
}
