import { LecturasCompartidas } from './lecturas';
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

export interface PersonalObra extends ResponsableObra {
  nombre_rol: string;
  estado: string;
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
}

@Injectable({
  providedIn: 'root'
})
export class ProyectosService {
  private shared = inject(LecturasCompartidas);
  private http = inject(HttpClient);
  private authService = inject(AuthService);
  private apiUrl = environment.apiUrl;

  private getHeaders(): HttpHeaders {
    const token = this.authService.obtenerToken();
    return token ? new HttpHeaders({ 'Authorization': `Bearer ${token}` }) : new HttpHeaders();
  }

  listarProyectos(): Observable<ApiResponseList> {
    return this.shared.obtener('obras', () => this.http.get<ApiResponseList>(`${this.apiUrl}/api/proyectos/`, { headers: this.getHeaders() }));
  }

  obtenerSiguienteCodigo(): Observable<{ success: boolean; codigo: string }> {
    return this.http.get<{ success: boolean; codigo: string }>(`${this.apiUrl}/api/proyectos/siguiente-codigo`, { headers: this.getHeaders() });
  }

  obtenerTiposProyecto(): Observable<ApiResponseTipos> {
    return this.shared.obtener('tipos', () => this.http.get<ApiResponseTipos>(`${this.apiUrl}/api/proyectos/tipos`, { headers: this.getHeaders() }));
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

  listarPersonal(idObra: number): Observable<{ success: boolean; data: PersonalObra[] }> {
    return this.http.get<{ success: boolean; data: PersonalObra[] }>(
      `${this.apiUrl}/api/proyectos/${idObra}/personal`, { headers: this.getHeaders() }
    );
  }

  candidatosPersonal(idObra: number): Observable<{ success: boolean; data: PersonalObra[] }> {
    return this.http.get<{ success: boolean; data: PersonalObra[] }>(
      `${this.apiUrl}/api/proyectos/${idObra}/personal/candidatos`, { headers: this.getHeaders() }
    );
  }

  asignarPersonal(idObra: number, idUsuario: number): Observable<ApiResponseSimple> {
    return this.http.post<ApiResponseSimple>(
      `${this.apiUrl}/api/proyectos/${idObra}/personal`,
      { id_usuario: idUsuario }, { headers: this.getHeaders() }
    );
  }

  retirarResponsable(idObra: number, idUsuario: number): Observable<ApiResponseSimple> {
    return this.http.delete<ApiResponseSimple>(
      `${this.apiUrl}/api/proyectos/${idObra}/responsables/${idUsuario}`,
      { headers: this.getHeaders() }
    );
  }
}
