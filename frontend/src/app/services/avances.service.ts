import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import { AuthService } from './auth';

// ─── Interfaces ────────────────────────────────────────────────────────────

export interface Avance {
  id_avance: number;
  id_obra: number;
  id_unidad: number;
  codigo_unidad: string;
  nombre_unidad: string;
  tipo_unidad: string;
  estado_unidad: string;
  porcentaje_avance: number;
  fecha_registro: string;
  observacion?: string;
  id_usuario: number;
  usuario_nombre: string;
  created_at: string;
}

export interface ResumenAvance {
  id_unidad: number;
  codigo_unidad: string;
  nombre_unidad: string;
  tipo_unidad: string;
  estado_unidad: string;
  ultimo_avance: number;
  fecha_ultimo?: string;
}

export interface ResumenAvancesResponse {
  success: boolean;
  avance_global: number;
  unidades: ResumenAvance[];
}

export interface AvancesListResponse {
  success: boolean;
  data: Avance[];
}

export interface AvanceCreateResponse {
  success: boolean;
  id_avance?: number;
  message?: string;
}

export interface NuevoAvance {
  id_unidad: number;
  porcentaje_avance: number;
  fecha_registro?: string;
  observacion?: string;
}

// ─── Service ────────────────────────────────────────────────────────────────

@Injectable({ providedIn: 'root' })
export class AvancesService {
  private http = inject(HttpClient);
  private authService = inject(AuthService);
  private apiUrl = environment.apiUrl;

  private getHeaders(): HttpHeaders {
    const token = this.authService.obtenerToken();
    return token ? new HttpHeaders({ 'Authorization': `Bearer ${token}` }) : new HttpHeaders();
  }

  /** Lista el historial completo de avances de una obra. */
  listarAvances(idObra: number, idUnidad?: number): Observable<AvancesListResponse> {
    let url = `${this.apiUrl}/api/proyectos/${idObra}/avances/`;
    if (idUnidad) url += `?id_unidad=${idUnidad}`;
    return this.http.get<AvancesListResponse>(url, { headers: this.getHeaders() });
  }

  /** Devuelve el resumen de avance global y por unidad. */
  resumenAvances(idObra: number): Observable<ResumenAvancesResponse> {
    return this.http.get<ResumenAvancesResponse>(
      `${this.apiUrl}/api/proyectos/${idObra}/avances/resumen`,
      { headers: this.getHeaders() }
    );
  }

  /** Registra un nuevo avance de obra. */
  registrarAvance(idObra: number, avance: NuevoAvance): Observable<AvanceCreateResponse> {
    return this.http.post<AvanceCreateResponse>(
      `${this.apiUrl}/api/proyectos/${idObra}/avances/`,
      avance,
      { headers: this.getHeaders() }
    );
  }

  /** Elimina un avance registrado. */
  eliminarAvance(idObra: number, idAvance: number): Observable<{ success: boolean; message?: string }> {
    return this.http.delete<{ success: boolean; message?: string }>(
      `${this.apiUrl}/api/proyectos/${idObra}/avances/${idAvance}`,
      { headers: this.getHeaders() }
    );
  }
}
