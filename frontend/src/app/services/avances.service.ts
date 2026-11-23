import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import { AuthService } from './auth';

// ─── Interfaces ────────────────────────────────────────────────────────────

export interface ResponsableOrden {
  id_usuario: number;
  username: string;
  nombre_completo: string;
}

export interface OrdenAvance {
  orden_nro: number;
  id_obra: number;
  tipo_trab: string;
  cuadrilla: number;
  estado: string;
  es_cumplida: boolean;
  fecha_inicio: string;
  fecha_fin?: string;
  observacion?: string;
  peso_porcentual: number;
  responsables: ResponsableOrden[];
}

export interface CuadrillaResumen {
  cuadrilla: number;
  total_ordenes: number;
  cumplidas: number;
  pendientes: number;
}

export interface ResumenAvancesResponse {
  success: boolean;
  id_obra: number;
  total_ordenes: number;
  ordenes_cumplidas: number;
  ordenes_pendientes: number;
  porcentaje_avance: number;
  cuadrillas: CuadrillaResumen[];
}

export interface AvancesListResponse {
  success: boolean;
  data: OrdenAvance[];
}

export interface AvanceFisicoUnidadCu30 {
  id_avance: number;
  id_obra: number;
  id_unidad: number;
  porcentaje_avance: number;
  estado_unidad: string;
  fecha_registro: string | null;
  observacion: string | null;
}

export interface AvanceFisicoUnidadCu30Response {
  success: boolean;
  data: AvanceFisicoUnidadCu30[];
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

  /**
   * Lista la bitácora de órdenes de trabajo de la obra con su estado y cuadrillas.
   * Filtro opcional: 'FINALIZADO' (cumplidas) o 'PENDIENTE' (faltantes por cumplir).
   */
  listarAvances(idObra: number, estado?: string): Observable<AvancesListResponse> {
    let url = `${this.apiUrl}/api/proyectos/${idObra}/avances/`;
    if (estado) url += `?estado=${estado}`;
    return this.http.get<AvancesListResponse>(url, { headers: this.getHeaders() });
  }

  /**
   * Obtiene el resumen consolidado de avances: % global (cumplidas/total),
   * conteo de órdenes cumplidas y faltantes, y cuadrillas involucradas.
   */
  resumenAvances(idObra: number): Observable<ResumenAvancesResponse> {
    return this.http.get<ResumenAvancesResponse>(
      `${this.apiUrl}/api/proyectos/${idObra}/avances/resumen`,
      { headers: this.getHeaders() }
    );
  }

  /**
   * HU114: Consulta el avance físico autorizado de una unidad para el rol CLIENTE.
   * No requiere id_cliente ni id_empresa ya que el backend los obtiene del JWT.
   */
  consultarAvanceFisicoUnidadCliente(idObra: number, idUnidad: number): Observable<AvanceFisicoUnidadCu30Response> {
    return this.http.get<AvanceFisicoUnidadCu30Response>(
      `${this.apiUrl}/api/proyectos/${idObra}/avances/cliente/unidades/${idUnidad}`,
      { headers: this.getHeaders() }
    );
  }
}
