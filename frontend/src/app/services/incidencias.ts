import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

// ─────────────────────────────────────────────────────────────────────────────
// Tipos e interfaces (CU19 - Gestión de incidencias)
// ─────────────────────────────────────────────────────────────────────────────
export type PrioridadIncidencia = 'BAJA' | 'MEDIA' | 'ALTA' | 'CRITICA';

export type EstadoIncidencia = 'ABIERTA' | 'ASIGNADA' | 'EN_PROCESO' | 'PENDIENTE_VALIDACION' | 'RESUELTA' | 'CERRADA';

export interface Incidencia {
  id_incidencia: number;
  id_obra: number;
  obra_codigo?: string | null;
  obra_nombre?: string | null;
  id_unidad?: number | null;
  unidad_codigo?: string | null;
  id_usuario_registro: number;
  usuario_registro_nombre?: string | null;
  id_responsable?: number | null;
  responsable_nombre?: string | null;
  titulo: string;
  descripcion: string;
  prioridad: PrioridadIncidencia;
  estado: EstadoIncidencia;
  created_at?: string;
  updated_at?: string;
  ubicacion?: string | null;
  /** Generadas por el servidor al iniciar (EN_PROCESO) y finalizar (PENDIENTE_VALIDACION). */
  fecha_inicio_atencion?: string | null;
  fecha_fin_atencion?: string | null;
  /** OT afectadas (solo viene en el detalle). */
  ordenes_trabajo?: OrdenTrabajoAfectada[];
}

/** Datos de obras.t_orden_trabajo leídos por CU19 (no se modifican desde aquí). */
export interface OrdenTrabajoResumen {
  orden_nro: number;
  id_obra: number;
  tipo_trab?: string | null;
  cuadrilla?: number | null;
  estado?: string | null;
  afectada_por_incidencia?: boolean;
  fecha_inicio?: string | null;
  fecha_fin?: string | null;
}

export interface OrdenTrabajoAfectada extends OrdenTrabajoResumen {
  fecha_vinculo?: string | null;
  usuario_vinculo_nombre?: string | null;
}

export interface OrdenTrabajoDisponible extends OrdenTrabajoResumen {
  afectada: boolean;
}

export interface OrdenesTrabajoMutationResponse {
  success: boolean;
  message: string;
  agregadas: number[];
  quitadas: number[];
}

export interface IncidenciaSeguimiento {
  id_seguimiento: number;
  id_usuario?: number | null;
  usuario_nombre?: string | null;
  estado_anterior?: EstadoIncidencia | null;
  estado_nuevo: EstadoIncidencia;
  observacion?: string | null;
  fecha: string;
}

export interface IncidenciaEvidencia {
  id_evidencia: number;
  id_incidencia: number;
  id_usuario?: number | null;
  nombre_archivo: string;
  tipo_mime?: string | null;
  tamano_bytes?: number | null;
  fecha: string;
}

export interface CrearIncidenciaPayload {
  id_obra: number;
  id_unidad?: number | null;
  titulo: string;
  descripcion: string;
  prioridad: PrioridadIncidencia;
  ubicacion?: string | null;
}

export type ActualizarIncidenciaPayload = Pick<CrearIncidenciaPayload, 'titulo' | 'descripcion' | 'prioridad' | 'ubicacion'>;

export interface IncidenciaFiltros {
  id_obra?: number;
  id_unidad?: number;
  prioridad?: PrioridadIncidencia;
  estado?: EstadoIncidencia;
  busqueda?: string;
  id_responsable?: number;
  page?: number;
  limit?: number;
}

export interface Paginacion {
  page: number;
  limit: number;
  total: number;
  total_pages: number;
}

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
}

export interface IncidenciaListResponse {
  success: boolean;
  data: Incidencia[];
  pagination: Paginacion;
}

export interface IncidenciaMutationResponse {
  success: boolean;
  message: string;
  id_incidencia?: number;
}

export interface AsignarResponsableResponse {
  success: boolean;
  message: string;
  estado: EstadoIncidencia;
}

export interface UsuarioResponsable {
  nro_usuario: number;
  nombre_usuario: string;
  nombre_completo: string;
  nombre_rol?: string | null;
}

export interface CambiarEstadoResponse {
  success: boolean;
  message: string;
  estado_anterior: EstadoIncidencia;
  estado_nuevo: EstadoIncidencia;
}

export interface SeguimientoMutationResponse {
  success: boolean;
  id_seguimiento: number;
  message: string;
}

export interface EvidenciaMutationResponse {
  success: boolean;
  id_evidencia: number;
  message: string;
}

// ─────────────────────────────────────────────────────────────────────────────
// Servicio
//
// Importante: ninguna llamada de este servicio envía id_empresa. El backend
// (CU19) obtiene siempre la empresa desde el JWT de sesión (ver
// incidencia_services._empresa_id en el backend); el token se adjunta
// automáticamente vía authInterceptor.
// ─────────────────────────────────────────────────────────────────────────────
@Injectable({ providedIn: 'root' })
export class IncidenciasService {
  private http = inject(HttpClient);
  private readonly url = `${environment.apiUrl}/api/incidencias`;

  listar(filtros: IncidenciaFiltros): Observable<IncidenciaListResponse> {
    let params = new HttpParams();
    Object.entries(filtros).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        params = params.set(key, String(value));
      }
    });
    return this.http.get<IncidenciaListResponse>(`${this.url}/`, { params });
  }

  obtener(id: number): Observable<ApiResponse<Incidencia>> {
    return this.http.get<ApiResponse<Incidencia>>(`${this.url}/${id}`);
  }

  registrar(payload: CrearIncidenciaPayload): Observable<IncidenciaMutationResponse> {
    return this.http.post<IncidenciaMutationResponse>(`${this.url}/`, payload);
  }

  actualizar(id: number, payload: ActualizarIncidenciaPayload): Observable<IncidenciaMutationResponse> {
    return this.http.put<IncidenciaMutationResponse>(`${this.url}/${id}`, payload);
  }

  /**
   * HU71: candidatos a responsable del MISMO tenant que la incidencia
   * (el backend deriva la empresa vía incidencia -> obra -> empresa; nunca
   * se envía id_empresa desde el cliente). Reemplaza el uso del endpoint
   * genérico /api/usuarios/, que no está acotado a este caso de uso.
   */
  obtenerResponsables(id: number): Observable<ApiResponse<UsuarioResponsable[]>> {
    return this.http.get<ApiResponse<UsuarioResponsable[]>>(`${this.url}/${id}/responsables`);
  }

  asignarResponsable(id: number, id_responsable: number): Observable<AsignarResponsableResponse> {
    return this.http.patch<AsignarResponsableResponse>(`${this.url}/${id}/responsable`, { id_responsable });
  }

  cambiarEstado(id: number, estado: EstadoIncidencia, observacion?: string): Observable<CambiarEstadoResponse> {
    return this.http.patch<CambiarEstadoResponse>(`${this.url}/${id}/estado`, { estado, observacion: observacion || undefined });
  }

  /** OT de la MISMA obra de la incidencia (el backend la deriva; nunca se envía id_obra). */
  listarOrdenesTrabajoDisponibles(id: number): Observable<ApiResponse<OrdenTrabajoDisponible[]>> {
    return this.http.get<ApiResponse<OrdenTrabajoDisponible[]>>(`${this.url}/${id}/ordenes-trabajo/disponibles`);
  }

  /** Reemplaza el conjunto de OT afectadas por `ordenes` (lista vacía = ninguna). */
  actualizarOrdenesTrabajo(id: number, ordenes: number[]): Observable<OrdenesTrabajoMutationResponse> {
    return this.http.put<OrdenesTrabajoMutationResponse>(`${this.url}/${id}/ordenes-trabajo`, { ordenes });
  }

  listarSeguimiento(id: number):Observable<ApiResponse<IncidenciaSeguimiento[]>> {
    return this.http.get<ApiResponse<IncidenciaSeguimiento[]>>(`${this.url}/${id}/seguimiento`);
  }

  registrarSeguimiento(id: number, observacion: string): Observable<SeguimientoMutationResponse> {
    return this.http.post<SeguimientoMutationResponse>(`${this.url}/${id}/seguimiento`, { observacion });
  }

  listarEvidencias(id: number): Observable<ApiResponse<IncidenciaEvidencia[]>> {
    return this.http.get<ApiResponse<IncidenciaEvidencia[]>>(`${this.url}/${id}/evidencias`);
  }

  subirEvidencia(id: number, archivo: File): Observable<EvidenciaMutationResponse> {
    const formData = new FormData();
    formData.append('archivo', archivo, archivo.name);
    return this.http.post<EvidenciaMutationResponse>(`${this.url}/${id}/evidencias`, formData);
  }

  /**
   * Las evidencias no son públicas: siempre se descargan mediante este
   * endpoint autenticado (el interceptor adjunta el Bearer token) y se
   * consumen como blob en el componente. Nunca construir una URL directa
   * a la carpeta de uploads del backend.
   */
  descargarEvidencia(id: number, idEvidencia: number): Observable<Blob> {
    return this.http.get(`${this.url}/${id}/evidencias/${idEvidencia}/archivo`, { responseType: 'blob' });
  }
}
