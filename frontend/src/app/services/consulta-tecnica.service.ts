import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export type EstadoConsultaTecnica = 'ABIERTA' | 'ASIGNADA' | 'RESPONDIDA' | 'CERRADA';

export interface ConsultaTecnica {
  id_consulta_tecnica: number;
  id_empresa: number;
  id_obra: number;
  obra_codigo?: string | null;
  obra_nombre?: string | null;
  codigo: string;
  asunto: string;
  descripcion: string;
  referencia_tecnica?: string | null;
  estado: EstadoConsultaTecnica;
  creado_por: number;
  creador_nombre?: string | null;
  asignado_a?: number | null;
  responsable_nombre?: string | null;
  fecha_asignacion?: string | null;
  asignado_por?: number | null;
  fecha_cierre?: string | null;
  cerrado_por?: number | null;
  cerrador_nombre?: string | null;
  motivo_cierre?: string | null;
  created_at?: string;
  updated_at?: string;
  total_respuestas?: number;
}

export interface ConsultaTecnicaRespuesta {
  id_consulta_tecnica_respuesta: number;
  id_consulta_tecnica: number;
  id_usuario_respuesta: number;
  autor_nombre?: string | null;
  autor_rol?: string | null;
  es_responsable_asignado?: boolean;
  respuesta: string;
  created_at?: string;
}

export interface ConsultaTecnicaHistorial {
  id_historial: number;
  id_consulta_tecnica: number;
  estado_anterior?: EstadoConsultaTecnica | null;
  estado_nuevo?: EstadoConsultaTecnica | null;
  id_responsable_anterior?: number | null;
  responsable_anterior_nombre?: string | null;
  id_responsable_nuevo?: number | null;
  responsable_nuevo_nombre?: string | null;
  id_usuario_accion: number;
  usuario_accion_nombre?: string | null;
  tipo_accion: string;
  detalle?: string | null;
  created_at?: string;
}

export interface ConsultaTecnicaDetalle extends ConsultaTecnica {
  respuestas: ConsultaTecnicaRespuesta[];
  historial: ConsultaTecnicaHistorial[];
}

export interface UsuarioAsignable {
  id_usuario: number;
  nombre_completo: string;
  rol: string;
  email?: string;
}

export interface ConsultaTecnicaFiltros {
  id_obra?: number;
  estado?: EstadoConsultaTecnica | string;
  id_responsable?: number;
  busqueda?: string;
  page?: number;
  limit?: number;
}

export interface ConsultaTecnicaListResponse {
  items: ConsultaTecnica[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

export interface CrearConsultaTecnicaPayload {
  asunto: string;
  descripcion: string;
  referencia_tecnica?: string | null;
  asignado_a?: number | null;
}

export interface ResponderConsultaTecnicaPayload {
  respuesta: string;
}

export interface AsignarResponsablePayload {
  id_responsable: number;
  motivo?: string;
}

export interface CambiarEstadoPayload {
  estado: EstadoConsultaTecnica;
  motivo?: string;
}

@Injectable({ providedIn: 'root' })
export class ConsultaTecnicaService {
  private http = inject(HttpClient);
  private readonly baseUrl = `${environment.apiUrl}/api`;

  listar(filtros?: ConsultaTecnicaFiltros): Observable<ConsultaTecnicaListResponse> {
    let params = new HttpParams();
    if (filtros) {
      Object.entries(filtros).forEach(([key, val]) => {
        if (val !== undefined && val !== null && val !== '') {
          params = params.set(key, String(val));
        }
      });
    }
    return this.http.get<ConsultaTecnicaListResponse>(`${this.baseUrl}/consultas-tecnicas`, { params });
  }

  listarPorObra(idObra: number, filtros?: ConsultaTecnicaFiltros): Observable<ConsultaTecnicaListResponse> {
    let params = new HttpParams();
    if (filtros) {
      Object.entries(filtros).forEach(([key, val]) => {
        if (val !== undefined && val !== null && val !== '') {
          params = params.set(key, String(val));
        }
      });
    }
    return this.http.get<ConsultaTecnicaListResponse>(`${this.baseUrl}/proyectos/${idObra}/consultas-tecnicas`, { params });
  }

  obtenerDetalle(idConsultaTecnica: number): Observable<ConsultaTecnicaDetalle> {
    return this.http.get<ConsultaTecnicaDetalle>(`${this.baseUrl}/consultas-tecnicas/${idConsultaTecnica}`);
  }

  registrar(idObra: number, payload: CrearConsultaTecnicaPayload): Observable<ConsultaTecnica> {
    return this.http.post<ConsultaTecnica>(`${this.baseUrl}/proyectos/${idObra}/consultas-tecnicas`, payload);
  }

  obtenerUsuariosAsignables(idObra: number): Observable<UsuarioAsignable[]> {
    return this.http.get<UsuarioAsignable[]>(`${this.baseUrl}/proyectos/${idObra}/consultas-tecnicas/usuarios-asignables`);
  }

  asignarResponsable(idConsultaTecnica: number, payload: AsignarResponsablePayload): Observable<ConsultaTecnica> {
    return this.http.patch<ConsultaTecnica>(`${this.baseUrl}/consultas-tecnicas/${idConsultaTecnica}/asignacion`, payload);
  }

  responder(idConsultaTecnica: number, payload: ResponderConsultaTecnicaPayload): Observable<ConsultaTecnicaRespuesta> {
    return this.http.post<ConsultaTecnicaRespuesta>(`${this.baseUrl}/consultas-tecnicas/${idConsultaTecnica}/respuestas`, payload);
  }

  cambiarEstado(idConsultaTecnica: number, payload: CambiarEstadoPayload): Observable<ConsultaTecnica> {
    return this.http.patch<ConsultaTecnica>(`${this.baseUrl}/consultas-tecnicas/${idConsultaTecnica}/estado`, payload);
  }

  obtenerHistorial(idConsultaTecnica: number): Observable<ConsultaTecnicaHistorial[]> {
    return this.http.get<ConsultaTecnicaHistorial[]>(`${this.baseUrl}/consultas-tecnicas/${idConsultaTecnica}/historial`);
  }
}
