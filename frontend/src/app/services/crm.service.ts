import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export type TipoCliente = 'PROSPECTO' | 'CLIENTE';

export type EstadoProspecto = 
  | 'NUEVO'
  | 'CONTACTADO'
  | 'INTERESADO'
  | 'NEGOCIACION'
  | 'EN_NEGOCIACION'
  | 'RESERVADO'
  | 'VENDIDO'
  | 'CONVERTIDO'
  | 'PERDIDO';

export type EstadoCliente = 
  | 'ACTIVO'
  | 'INACTIVO'
  | 'NUEVO'
  | 'CONTACTADO'
  | 'INTERESADO'
  | 'NEGOCIACION'
  | 'RESERVADO'
  | 'VENDIDO';

export type TipoInteraccion = 
  | 'LLAMADA'
  | 'MENSAJE'
  | 'REUNION'
  | 'VISITA'
  | 'CONSULTA'
  | 'SEGUIMIENTO'
  | 'OBSERVACION'
  | 'CORREO'
  | 'NOTA'
  | 'OTRO';

export interface AsesorComercial {
  id_usuario: number;
  nombre_completo: string;
  username: string;
  email: string;
  rol?: string;
}

export type EstadoAsociacionUnidad = 
  | 'INTERESADO'
  | 'RESERVADO'
  | 'VENDIDO'
  | 'ENTREGADO'
  | 'CANCELADO';

export interface ClienteCRM {
  id_cliente: number;
  id_empresa: number;
  id_persona: number;
  email?: string | null;
  tipo_cliente: TipoCliente;
  estado: string;
  origen: string;
  presupuesto_estimado?: number | null;
  notas?: string | null;
  id_usuario_asignado?: number | null;
  created_at: string;
  updated_at: string;
  nombre_completo: string;
  ci?: string | null;
  telefono?: string | null;
  telefono_ref?: string | null;
  direccion?: string | null;
  ubicacion?: string | null;
  nombre_empresa?: string;
  asesor_nombre?: string | null;
  asesor_username?: string | null;
}

export interface InteraccionCRM {
  id_interaccion: number;
  id_cliente: number;
  id_usuario: number;
  tipo: TipoInteraccion;
  asunto: string;
  detalle: string;
  fecha_interaccion: string;
  fecha_proximo_contacto?: string | null;
  created_at: string;
  usuario_username: string;
  usuario_nombre: string;
}

export interface UnidadAsociadaCRM {
  id_cliente_unidad: number;
  id_cliente: number;
  id_unidad: number;
  estado_asociacion: EstadoAsociacionUnidad;
  monto_pactado?: number | null;
  fecha_asociacion: string;
  observaciones?: string | null;
  codigo_unidad: string;
  tipo_unidad: string;
  superficie?: number | null;
  estado_unidad_actual: string;
  id_obra: number;
  nombre_obra: string;
  codigo_obra: string;
}

export interface DetalleHistorialCliente {
  cliente: ClienteCRM;
  interacciones: InteraccionCRM[];
  unidades_asociadas: UnidadAsociadaCRM[];
}

export interface UnidadClienteCu30 {
  id_cliente_unidad: number;
  id_cliente: number;
  id_unidad: number;
  estado_asociacion: string;
  monto_pactado?: number | null;
  fecha_asociacion?: string | null;
  observaciones?: string | null;
  codigo_unidad: string;
  tipo_unidad: string;
  superficie?: number | null;
  estado_unidad_actual: string;
  id_obra: number;
  nombre_obra: string;
  codigo_obra: string;
}

export interface FotografiaClienteCu30 {
  id_fotografia?: number;
  id_evidencia?: number;
  id_unidad?: number;
  nombre_archivo: string;
  tipo_mime: string;
  tamano_bytes: number;
  fecha: string | null;
  created_at?: string | null;
  es_principal?: boolean;
  orden?: number;
  url_archivo: string;
  blobUrl?: string;
  cargandoBlob?: boolean;
  errorBlob?: boolean;
}

export interface ComunicacionClienteCu30 {
  id_notificacion: number;
  titulo: string;
  cuerpo: string;
  mensaje?: string;
  tipo_referencia: string;
  tipo?: string;
  leido: boolean;
  fecha_creacion: string | null;
  created_at?: string | null;
  nro_emergencia?: number | null;
}

export interface SolicitudEvidenciaCu30 {
  id_fotografia: number;
  nombre_archivo: string;
  tipo_mime?: string | null;
  tamano_bytes?: number | null;
  url_archivo?: string | null;
}

export interface SolicitudClienteCu30 {
  id_solicitud: number;
  id_cliente?: number;
  id_usuario?: number;
  id_empresa?: number;
  id_obra: number;
  nombre_obra?: string;
  codigo_obra?: string;
  id_unidad?: number | null;
  codigo_unidad?: string | null;
  tipo_unidad?: string | null;
  nombre_cliente?: string;
  titulo?: string;
  asunto: string;
  descripcion: string;
  estado: string;
  respuesta?: string | null;
  id_usuario_respuesta?: number | null;
  id_fotografia_evidencia?: number | null;
  evidencia?: SolicitudEvidenciaCu30 | null;
  fecha_creacion: string | null;
  fecha_actualizacion?: string | null;
  fecha_respuesta?: string | null;
}

export type SolicitudConstructoraCu30 = SolicitudClienteCu30;

export interface MetricasCRM {
  total_clientes: number;
  total_prospectos: number;
  prospectos_por_estado: {
    NUEVO: number;
    CONTACTADO: number;
    INTERESADO: number;
    EN_NEGOCIACION?: number;
    NEGOCIACION?: number;
    RESERVADO?: number;
    VENDIDO?: number;
    CONVERTIDO: number;
    PERDIDO: number;
    [key: string]: number | undefined;
  };
  unidades_asociadas: {
    INTERESADO: number;
    RESERVADO: number;
    VENDIDO: number;
    [key: string]: number | undefined;
  };
}

export interface UnidadDisponible {
  id_unidad: number;
  codigo: string;
  tipo_unidad: string;
  superficie?: number | null;
  estado: string;
  id_obra: number;
  nombre_obra: string;
  codigo_obra: string;
  nombre_estructura: string;
}

@Injectable({
  providedIn: 'root'
})
export class CrmService {
  private http = inject(HttpClient);
  private apiUrl = `${environment.apiUrl}/api/crm`;

  listarClientes(paramsObj?: {
    tipo_cliente?: string;
    estado?: string;
    q?: string;
    id_usuario_asignado?: number;
    page?: number;
    limit?: number;
    id_empresa?: number;
  }): Observable<{ success: boolean; data: ClienteCRM[]; pagination: any }> {
    let params = new HttpParams();
    if (paramsObj) {
      if (paramsObj.tipo_cliente) params = params.set('tipo_cliente', paramsObj.tipo_cliente);
      if (paramsObj.estado) params = params.set('estado', paramsObj.estado);
      if (paramsObj.q) params = params.set('q', paramsObj.q);
      if (paramsObj.id_usuario_asignado) params = params.set('id_usuario_asignado', paramsObj.id_usuario_asignado.toString());
      if (paramsObj.page) params = params.set('page', paramsObj.page.toString());
      if (paramsObj.limit) params = params.set('limit', paramsObj.limit.toString());
      if (paramsObj.id_empresa) params = params.set('id_empresa', paramsObj.id_empresa.toString());
    }
    return this.http.get<{ success: boolean; data: ClienteCRM[]; pagination: any }>(`${this.apiUrl}/clientes`, { params });
  }

  obtenerMetricas(id_empresa?: number): Observable<{ success: boolean; data: MetricasCRM }> {
    let params = new HttpParams();
    if (id_empresa) params = params.set('id_empresa', id_empresa.toString());
    return this.http.get<{ success: boolean; data: MetricasCRM }>(`${this.apiUrl}/clientes/metricas`, { params });
  }

  obtenerDetalleHistorial(idCliente: number, id_empresa?: number): Observable<{ success: boolean; data: DetalleHistorialCliente }> {
    let params = new HttpParams();
    if (id_empresa) params = params.set('id_empresa', id_empresa.toString());
    return this.http.get<{ success: boolean; data: DetalleHistorialCliente }>(`${this.apiUrl}/clientes/${idCliente}`, { params });
  }

  registrarCliente(payload: any, id_empresa?: number): Observable<{ success: boolean; message: string; id_cliente: number }> {
    let params = new HttpParams();
    if (id_empresa) params = params.set('id_empresa', id_empresa.toString());
    return this.http.post<{ success: boolean; message: string; id_cliente: number }>(`${this.apiUrl}/clientes`, payload, { params });
  }

  actualizarCliente(idCliente: number, payload: any, id_empresa?: number): Observable<{ success: boolean; message: string }> {
    let params = new HttpParams();
    if (id_empresa) params = params.set('id_empresa', id_empresa.toString());
    return this.http.put<{ success: boolean; message: string }>(`${this.apiUrl}/clientes/${idCliente}`, payload, { params });
  }

  clasificarProspecto(idCliente: number, nuevoEstado: string, nota?: string, id_empresa?: number): Observable<any> {
    let params = new HttpParams();
    if (id_empresa) params = params.set('id_empresa', id_empresa.toString());
    return this.http.patch<any>(`${this.apiUrl}/clientes/${idCliente}/clasificacion`, { estado: nuevoEstado, nota }, { params });
  }

  listarAsesores(id_empresa?: number): Observable<{ success: boolean; data: AsesorComercial[] }> {
    let params = new HttpParams();
    if (id_empresa) params = params.set('id_empresa', id_empresa.toString());
    return this.http.get<{ success: boolean; data: AsesorComercial[] }>(`${this.apiUrl}/asesores`, { params });
  }

  registrarInteraccion(idCliente: number, payload: any, id_empresa?: number): Observable<{ success: boolean; message: string; id_interaccion: number }> {
    let params = new HttpParams();
    if (id_empresa) params = params.set('id_empresa', id_empresa.toString());
    return this.http.post<{ success: boolean; message: string; id_interaccion: number }>(`${this.apiUrl}/clientes/${idCliente}/interacciones`, payload, { params });
  }

  asociarUnidad(idCliente: number, payload: any, id_empresa?: number): Observable<{ success: boolean; message: string; id_cliente_unidad: number }> {
    let params = new HttpParams();
    if (id_empresa) params = params.set('id_empresa', id_empresa.toString());
    return this.http.post<{ success: boolean; message: string; id_cliente_unidad: number }>(`${this.apiUrl}/clientes/${idCliente}/unidades`, payload, { params });
  }

  cambiarEstadoAsociacion(idAsociacion: number, estado_asociacion: string, observaciones?: string, id_empresa?: number): Observable<any> {
    let params = new HttpParams();
    if (id_empresa) params = params.set('id_empresa', id_empresa.toString());
    return this.http.patch<any>(`${this.apiUrl}/asociaciones/${idAsociacion}/estado`, { estado_asociacion, observaciones }, { params });
  }

  listarUnidadesDisponibles(id_obra?: number, id_empresa?: number): Observable<{ success: boolean; data: UnidadDisponible[] }> {
    let params = new HttpParams();
    if (id_obra) params = params.set('id_obra', id_obra.toString());
    if (id_empresa) params = params.set('id_empresa', id_empresa.toString());
    return this.http.get<{ success: boolean; data: UnidadDisponible[] }>(`${this.apiUrl}/clientes/unidades-disponibles`, { params });
  }

  // ─────────────────────────────────────────────────────────────────────────────
  // CU30: Portal del Cliente (HU114, HU115, HU116, HU117)
  // Ningún método envía id_cliente ni id_empresa; el backend resuelve identidad
  // y tenant exclusivamente desde los claims del token JWT.
  // ─────────────────────────────────────────────────────────────────────────────

  listarUnidadesCliente(): Observable<{ success: boolean; data: UnidadClienteCu30[] }> {
    return this.http.get<{ success: boolean; data: UnidadClienteCu30[] }>(
      `${this.apiUrl}/cliente/unidades`
    );
  }

  listarFotografiasUnidad(idUnidad: number): Observable<{ success: boolean; data: FotografiaClienteCu30[] }> {
    return this.http.get<{ success: boolean; data: FotografiaClienteCu30[] }>(
      `${this.apiUrl}/cliente/unidades/${idUnidad}/fotografias`
    );
  }

  descargarFotografiaUnidad(idUnidad: number, idFotografia: number): Observable<Blob> {
    return this.http.get(
      `${this.apiUrl}/cliente/unidades/${idUnidad}/fotografias/${idFotografia}/archivo`,
      { responseType: 'blob' }
    );
  }

  listarComunicacionesCliente(): Observable<{ success: boolean; no_leidas: number; data: ComunicacionClienteCu30[] }> {
    return this.http.get<{ success: boolean; no_leidas: number; data: ComunicacionClienteCu30[] }>(
      `${this.apiUrl}/cliente/comunicaciones`
    );
  }

  listarSolicitudesCliente(): Observable<{ success: boolean; data: SolicitudClienteCu30[] }> {
    return this.http.get<{ success: boolean; data: SolicitudClienteCu30[] }>(
      `${this.apiUrl}/cliente/solicitudes`
    );
  }

  obtenerDetalleSolicitud(idSolicitud: number): Observable<{ success: boolean; data: SolicitudClienteCu30 }> {
    return this.http.get<{ success: boolean; data: SolicitudClienteCu30 }>(
      `${this.apiUrl}/cliente/solicitudes/${idSolicitud}`
    );
  }

  crearSolicitudCliente(payload: { id_unidad?: number | null; id_obra?: number | null; titulo: string; descripcion: string }): Observable<{ success: boolean; message: string; data: SolicitudClienteCu30 }> {
    return this.http.post<{ success: boolean; message: string; data: SolicitudClienteCu30 }>(
      `${this.apiUrl}/cliente/solicitudes`,
      payload
    );
  }

  listarSolicitudesConstructora(filtros?: { id_obra?: number; estado?: string }): Observable<{ success: boolean; data: SolicitudConstructoraCu30[] }> {
    let params = new HttpParams();
    if (filtros?.id_obra) {
      params = params.set('id_obra', filtros.id_obra.toString());
    }
    if (filtros?.estado) {
      params = params.set('estado', filtros.estado);
    }
    return this.http.get<{ success: boolean; data: SolicitudConstructoraCu30[] }>(
      `${this.apiUrl}/solicitudes`,
      { params }
    );
  }

  responderSolicitudConstructora(idSolicitud: number, payload: { estado: string; respuesta?: string; id_fotografia_evidencia?: number | null }): Observable<{ success: boolean; message: string; data: any }> {
    return this.http.post<{ success: boolean; message: string; data: any }>(
      `${this.apiUrl}/solicitudes/${idSolicitud}/responder`,
      payload
    );
  }

  // HU116: Emisión de comunicaciones hacia clientes
  enviarComunicacionCliente(payload: {
    id_cliente: number;
    id_obra?: number | null;
    id_unidad?: number | null;
    titulo: string;
    cuerpo: string;
    tipo_referencia?: string;
  }): Observable<{ success: boolean; message?: string; data: any }> {
    return this.http.post<{ success: boolean; message?: string; data: any }>(
      `${this.apiUrl}/comunicaciones`,
      payload
    );
  }
}
