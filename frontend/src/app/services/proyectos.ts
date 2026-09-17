import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import { AuthService } from './auth';

export interface ResponsableObra {
  id_usuario: number;
  username: string;
  nombre_completo: string;
  fecha_asignacion?: string;
}

export interface RequisitosEstimacion {
  tipo_obra: string;
  superficie_m2: number;
  niveles: number;
  tipo_terreno: string;
  complejidad: string;
  ubicacion?: string;
  caracteristicas_generales?: string;
  moneda?: string;
}

export interface CalculoEstimacion {
  tipo_obra: string;
  codigo_tipo_obra: string;
  superficie_m2: number;
  niveles: number;
  clave_niveles: string;
  tipo_terreno: string;
  codigo_tipo_terreno: string;
  complejidad: string;
  codigo_complejidad: string;
  ubicacion?: string;
  caracteristicas_generales?: string;
  costo_referencial_m2: number;
  factor_niveles: number;
  factor_terreno: number;
  factor_complejidad: number;
  factor_combinado: number;
  costo_base: number;
  monto_estimado: number;
  moneda: string;
}

export interface EstimacionObra {
  id_estimacion: number;
  id_obra: number;
  tipo_obra: string;
  superficie_m2: number;
  niveles: number;
  tipo_terreno: string;
  complejidad: string;
  ubicacion?: string;
  caracteristicas_generales?: string;
  costo_referencial_m2: number;
  factor_niveles: number;
  factor_terreno: number;
  factor_complejidad: number;
  costo_base: number;
  monto_estimado: number;
  moneda: string;
  fecha_estimacion?: string;
}

export interface Proyecto {
  id_obra?: number;
  codigo: string;
  nombre: string;
  id_tipo_obra: number;
  tipo_obra_nombre?: string;
  estado_obra: string;
  fecha_inicio: string;
  fecha_fin?: string;
  id_empresa?: number;
  moneda: string;
  descripcion?: string;
  created_at?: string;
  updated_at?: string;
  ubicacion?: string;
  zona?: string;
  distrito?: string;
  uv?: string;
  manzana?: string;
  latitud?: number;
  longitud?: number;
  id_supervisor?: number;
  supervisor_nombre?: string;
  id_cliente?: number;
  cliente_nombre?: string;
  valor_estimado?: number;
  descripcion_cliente?: string;
  observacion?: string;
  responsables?: ResponsableObra[];
  estimacion?: EstimacionObra | CalculoEstimacion;
  requisitos_estimacion?: RequisitosEstimacion;
}

export interface TipoProyecto {
  id_tipo_obra: number;
  nombre_obra: string;
}

export interface ApiResponseList {
  success: boolean;
  data: Proyecto[];
}

export interface ApiResponseDetail {
  success: boolean;
  data: Proyecto;
}

export interface ApiResponseTipos {
  success: boolean;
  data: TipoProyecto[];
}

export interface ApiResponseSimple {
  success: boolean;
  message: string;
  id_obra?: number;
  id_estimacion?: number;
  estimacion?: CalculoEstimacion;
}


@Injectable({
  providedIn: 'root'
})
export class ProyectosService {
  private http = inject(HttpClient);
  private authService = inject(AuthService);
  private apiUrl = environment.apiUrl;

  private getHeaders(): HttpHeaders {
    const token = this.authService.obtenerToken();
    return token ? new HttpHeaders({ 'Authorization': `Bearer ${token}` }) : new HttpHeaders();
  }

  listarProyectos(): Observable<ApiResponseList> {
    return this.http.get<ApiResponseList>(`${this.apiUrl}/api/proyectos/`, { headers: this.getHeaders() });
  }

  obtenerSiguienteCodigo(): Observable<{ success: boolean; codigo: string }> {
    return this.http.get<{ success: boolean; codigo: string }>(`${this.apiUrl}/api/proyectos/siguiente-codigo`, { headers: this.getHeaders() });
  }

  obtenerTiposProyecto(): Observable<ApiResponseTipos> {
    return this.http.get<ApiResponseTipos>(`${this.apiUrl}/api/proyectos/tipos`, { headers: this.getHeaders() });
  }

  obtenerProyectoDetalle(id: number): Observable<ApiResponseDetail> {
    return this.http.get<ApiResponseDetail>(`${this.apiUrl}/api/proyectos/${id}`, { headers: this.getHeaders() });
  }

  crearProyecto(proyecto: Proyecto): Observable<ApiResponseSimple> {
    return this.http.post<ApiResponseSimple>(`${this.apiUrl}/api/proyectos/`, proyecto, { headers: this.getHeaders() });
  }

  actualizarProyecto(id: number, proyecto: Proyecto): Observable<ApiResponseSimple> {
    return this.http.put<ApiResponseSimple>(`${this.apiUrl}/api/proyectos/${id}`, proyecto, { headers: this.getHeaders() });
  }

  actualizarEstadoProyecto(id: number, estado: string): Observable<ApiResponseSimple> {
    return this.http.patch<ApiResponseSimple>(
      `${this.apiUrl}/api/proyectos/${id}/estado`,
      { estado_obra: estado },
      { headers: this.getHeaders() }
    );
  }

  asignarResponsable(idObra: number, idUsuario: number): Observable<ApiResponseSimple> {
    return this.http.post<ApiResponseSimple>(
      `${this.apiUrl}/api/proyectos/${idObra}/responsables`,
      { id_usuario: idUsuario },
      { headers: this.getHeaders() }
    );
  }

  retirarResponsable(idObra: number, idUsuario: number): Observable<ApiResponseSimple> {
    return this.http.delete<ApiResponseSimple>(
      `${this.apiUrl}/api/proyectos/${idObra}/responsables/${idUsuario}`,
      { headers: this.getHeaders() }
    );
  }

  obtenerParametrosEstimacion(): Observable<{ success: boolean; data: any }> {
    return this.http.get<{ success: boolean; data: any }>(
      `${this.apiUrl}/api/proyectos/estimacion/parametros`,
      { headers: this.getHeaders() }
    );
  }

  calcularPreviewEstimacion(requisitos: RequisitosEstimacion): Observable<{ success: boolean; data: CalculoEstimacion }> {
    return this.http.post<{ success: boolean; data: CalculoEstimacion }>(
      `${this.apiUrl}/api/proyectos/estimar-preview`,
      requisitos,
      { headers: this.getHeaders() }
    );
  }

  obtenerEstimacionObra(idObra: number): Observable<{ success: boolean; data: EstimacionObra }> {
    return this.http.get<{ success: boolean; data: EstimacionObra }>(
      `${this.apiUrl}/api/proyectos/${idObra}/estimacion`,
      { headers: this.getHeaders() }
    );
  }
}
