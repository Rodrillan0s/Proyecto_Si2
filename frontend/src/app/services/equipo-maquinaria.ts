import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface EquipoMaquinaria {
  id_equipo_maquinaria: number;
  codigo: string;
  nombre: string;
  tipo?: string | null;
  marca?: string | null;
  modelo?: string | null;
  numero_serie?: string | null;
  descripcion?: string | null;
  estado: string;
  id_empresa: number;
  nombre_empresa?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface AsignacionEquipoMaquinaria {
  id_asignacion: number;
  id_equipo_maquinaria: number;
  id_obra: number;
  codigo_equipo?: string | null;
  nombre_equipo?: string | null;
  tipo_equipo?: string | null;
  marca_equipo?: string | null;
  modelo_equipo?: string | null;
  codigo_obra?: string | null;
  nombre_obra?: string | null;
  fecha_asignacion: string;
  fecha_retiro?: string | null;
  estado: string;
  observacion?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface EquipoMaquinariaPayload {
  codigo: string;
  nombre: string;
  tipo?: string | null;
  marca?: string | null;
  modelo?: string | null;
  numero_serie?: string | null;
  descripcion?: string | null;
  estado?: string;
}

export interface AsignarEquipoPayload {
  id_equipo_maquinaria: number;
  id_obra: number;
  observacion?: string | null;
}

export interface RetirarEquipoPayload {
  observacion?: string | null;
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
export class EquipoMaquinariaService {
  private http = inject(HttpClient);
  private apiUrl = `${environment.apiUrl}/api/equipos-maquinaria`;

  listarEquipos(params?: {
    tipo?: string;
    estado?: string;
  }): Observable<ApiResponse<EquipoMaquinaria[]>> {
    let httpParams = new HttpParams();

    if (params?.tipo) {
      httpParams = httpParams.set('tipo', params.tipo);
    }

    if (params?.estado) {
      httpParams = httpParams.set('estado', params.estado);
    }

    return this.http.get<ApiResponse<EquipoMaquinaria[]>>(
      `${this.apiUrl}/`,
      { params: httpParams }
    );
  }

  obtenerEquipo(
    id_equipo_maquinaria: number
  ): Observable<ApiResponse<EquipoMaquinaria>> {
    return this.http.get<ApiResponse<EquipoMaquinaria>>(
      `${this.apiUrl}/${id_equipo_maquinaria}`
    );
  }

  registrarEquipo(
    payload: EquipoMaquinariaPayload
  ): Observable<ApiResponse<any>> {
    return this.http.post<ApiResponse<any>>(
      `${this.apiUrl}/`,
      payload
    );
  }

  actualizarEquipo(
    id_equipo_maquinaria: number,
    payload: EquipoMaquinariaPayload
  ): Observable<ApiResponse<any>> {
    return this.http.put<ApiResponse<any>>(
      `${this.apiUrl}/${id_equipo_maquinaria}`,
      payload
    );
  }

  actualizarEstado(
    id_equipo_maquinaria: number,
    estado: string
  ): Observable<ApiResponse<any>> {
    return this.http.put<ApiResponse<any>>(
      `${this.apiUrl}/${id_equipo_maquinaria}/estado`,
      { estado }
    );
  }

  listarAsignaciones(params?: {
    id_obra?: number;
    id_equipo_maquinaria?: number;
    estado?: string;
  }): Observable<ApiResponse<AsignacionEquipoMaquinaria[]>> {
    let httpParams = new HttpParams();

    if (params?.id_obra) {
      httpParams = httpParams.set('id_obra', params.id_obra);
    }

    if (params?.id_equipo_maquinaria) {
      httpParams = httpParams.set(
        'id_equipo_maquinaria',
        params.id_equipo_maquinaria
      );
    }

    if (params?.estado) {
      httpParams = httpParams.set('estado', params.estado);
    }

    return this.http.get<ApiResponse<AsignacionEquipoMaquinaria[]>>(
      `${this.apiUrl}/asignaciones/`,
      { params: httpParams }
    );
  }

  obtenerAsignacion(
    id_asignacion: number
  ): Observable<ApiResponse<AsignacionEquipoMaquinaria>> {
    return this.http.get<ApiResponse<AsignacionEquipoMaquinaria>>(
      `${this.apiUrl}/asignaciones/${id_asignacion}`
    );
  }

  asignarEquipo(
    payload: AsignarEquipoPayload
  ): Observable<ApiResponse<any>> {
    return this.http.post<ApiResponse<any>>(
      `${this.apiUrl}/asignaciones/`,
      payload
    );
  }

  retirarEquipo(
    id_asignacion: number,
    payload: RetirarEquipoPayload
  ): Observable<ApiResponse<any>> {
    return this.http.put<ApiResponse<any>>(
      `${this.apiUrl}/asignaciones/${id_asignacion}/retirar`,
      payload
    );
  }
}