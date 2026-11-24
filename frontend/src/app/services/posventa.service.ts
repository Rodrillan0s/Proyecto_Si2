import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface GarantiaInmobiliaria {
  id_garantia: number;
  id_empresa: number;
  id_unidad: number;
  nombre_unidad: string;
  id_obra: number;
  nombre_obra: string;
  id_cliente: number;
  nombre_cliente: string;
  email_cliente?: string;
  tipo_garantia: string;
  descripcion_cobertura: string;
  condiciones?: string;
  fecha_inicio: string;
  fecha_fin: string;
  estado: 'VIGENTE' | 'VENCIDA' | 'ANULADA';
  created_at: string;
}

export interface SolicitudPosventa {
  id_solicitud: number;
  codigo_ticket: string;
  id_empresa: number;
  id_unidad: number;
  nombre_unidad: string;
  id_obra: number;
  nombre_obra: string;
  id_cliente: number;
  nombre_cliente: string;
  id_garantia?: number;
  tipo_garantia?: string;
  aplica_garantia?: boolean;
  titulo: string;
  descripcion_defecto: string;
  categoria?: string;
  prioridad: 'BAJA' | 'MEDIA' | 'ALTA' | 'URGENTE';
  estado: 'PENDIENTE' | 'CLASIFICADA' | 'ASIGNADA' | 'EN_ATENCION' | 'RESUELTA' | 'CERRADA' | 'RECHAZADA';
  id_supervisor_asignado?: number;
  nombre_supervisor?: string;
  fecha_estimada_visita?: string;
  instrucciones_tecnicas?: string;
  observaciones_clasificacion?: string;
  fecha_cierre?: string;
  created_at: string;
  updated_at: string;
  total_evidencias?: number;
  evidencias?: EvidenciaPosventa[];
  linea_tiempo?: EventoBitacoraPosventa[];
}

export interface EvidenciaPosventa {
  id_evidencia: number;
  tipo_evidencia: string;
  ruta_archivo: string;
  nombre_archivo: string;
  tipo_mime?: string;
  tamano_bytes?: number;
  id_usuario?: number;
  created_at: string;
}

export interface EventoBitacoraPosventa {
  id_bitacora: number;
  id_usuario?: number;
  nombre_usuario: string;
  tipo_evento: string;
  estado_anterior?: string;
  estado_nuevo?: string;
  detalle_acciones: string;
  materiales_utilizados?: string;
  fecha: string;
}

export interface MetricasPosventa {
  total_solicitudes: number;
  pendientes: number;
  clasificadas: number;
  asignadas: number;
  en_atencion: number;
  resueltas: number;
  cubiertas_por_garantia: number;
  urgentes: number;
  promedio_dias_resolucion: number;
  total_garantias: number;
  garantias_vigentes: number;
  garantias_vencidas: number;
}

export interface OpcionGarantiaPosventa {
  id_unidad: number;
  codigo_unidad: string;
  nombre_estructura?: string;
  id_obra: number;
  nombre_obra: string;
  id_cliente: number;
  nombre_cliente: string;
  estado_asociacion: 'RESERVADO' | 'VENDIDO' | 'ENTREGADO';
}

@Injectable({
  providedIn: 'root'
})
export class PosventaService {
  private http = inject(HttpClient);
  private apiUrl = `${environment.apiUrl}/api/posventa`;

  listarOpcionesGarantia(): Observable<OpcionGarantiaPosventa[]> {
    return this.http.get<OpcionGarantiaPosventa[]>(`${this.apiUrl}/opciones-garantia`);
  }

  // 1. Garantías (HU161, HU162)
  listarGarantias(filtros?: { id_unidad?: number; id_cliente?: number; id_obra?: number; estado?: string }): Observable<GarantiaInmobiliaria[]> {
    let params = new HttpParams();
    if (filtros?.id_unidad) params = params.set('id_unidad', filtros.id_unidad.toString());
    if (filtros?.id_cliente) params = params.set('id_cliente', filtros.id_cliente.toString());
    if (filtros?.id_obra) params = params.set('id_obra', filtros.id_obra.toString());
    if (filtros?.estado) params = params.set('estado', filtros.estado);
    return this.http.get<GarantiaInmobiliaria[]>(`${this.apiUrl}/garantias`, { params });
  }

  registrarGarantia(dto: {
    id_unidad: number;
    id_cliente: number;
    tipo_garantia: string;
    descripcion_cobertura: string;
    fecha_inicio: string;
    fecha_fin: string;
    condiciones?: string;
  }): Observable<{ success: boolean; message: string; garantia: GarantiaInmobiliaria }> {
    return this.http.post<{ success: boolean; message: string; garantia: GarantiaInmobiliaria }>(`${this.apiUrl}/garantias`, dto);
  }

  // 2. Solicitudes de Posventa (HU163 a HU168)
  listarSolicitudes(filtros?: {
    id_cliente?: number;
    id_supervisor?: number;
    id_obra?: number;
    id_unidad?: number;
    estado?: string;
    prioridad?: string;
    categoria?: string;
  }): Observable<SolicitudPosventa[]> {
    let params = new HttpParams();
    if (filtros?.id_cliente) params = params.set('id_cliente', filtros.id_cliente.toString());
    if (filtros?.id_supervisor) params = params.set('id_supervisor', filtros.id_supervisor.toString());
    if (filtros?.id_obra) params = params.set('id_obra', filtros.id_obra.toString());
    if (filtros?.id_unidad) params = params.set('id_unidad', filtros.id_unidad.toString());
    if (filtros?.estado) params = params.set('estado', filtros.estado);
    if (filtros?.prioridad) params = params.set('prioridad', filtros.prioridad);
    if (filtros?.categoria) params = params.set('categoria', filtros.categoria);
    return this.http.get<SolicitudPosventa[]>(`${this.apiUrl}/solicitudes`, { params });
  }

  obtenerDetalleSolicitud(idSolicitud: number): Observable<SolicitudPosventa> {
    return this.http.get<SolicitudPosventa>(`${this.apiUrl}/solicitudes/${idSolicitud}`);
  }

  registrarSolicitud(dto: {
    id_unidad: number;
    titulo: string;
    descripcion_defecto: string;
    id_cliente?: number;
    id_garantia?: number;
  }): Observable<{ success: boolean; message: string; codigo_ticket: string; solicitud: SolicitudPosventa }> {
    return this.http.post<{ success: boolean; message: string; codigo_ticket: string; solicitud: SolicitudPosventa }>(`${this.apiUrl}/solicitudes`, dto);
  }

  clasificarSolicitud(idSolicitud: number, dto: {
    categoria: string;
    prioridad: string;
    aplica_garantia: boolean;
    id_garantia?: number;
    observaciones?: string;
  }): Observable<{ success: boolean; message: string; solicitud: SolicitudPosventa }> {
    return this.http.post<{ success: boolean; message: string; solicitud: SolicitudPosventa }>(`${this.apiUrl}/solicitudes/${idSolicitud}/clasificar`, dto);
  }

  asignarResponsable(idSolicitud: number, dto: {
    id_supervisor: number;
    fecha_estimada_visita: string;
    instrucciones_tecnicas?: string;
  }): Observable<{ success: boolean; message: string; solicitud: SolicitudPosventa }> {
    return this.http.post<{ success: boolean; message: string; solicitud: SolicitudPosventa }>(`${this.apiUrl}/solicitudes/${idSolicitud}/asignar`, dto);
  }

  atenderSolicitud(idSolicitud: number, dto: {
    nuevo_estado: string;
    acciones_realizadas: string;
    materiales_utilizados?: string;
    motivo_cierre?: string;
  }): Observable<{ success: boolean; message: string; solicitud: SolicitudPosventa }> {
    return this.http.post<{ success: boolean; message: string; solicitud: SolicitudPosventa }>(`${this.apiUrl}/solicitudes/${idSolicitud}/atender`, dto);
  }

  adjuntarEvidencia(idSolicitud: number, archivo: File, tipoEvidencia: string = 'CLIENTE_REPORTE'): Observable<any> {
    const formData = new FormData();
    formData.append('archivo', archivo);
    formData.append('tipo_evidencia', tipoEvidencia);
    return this.http.post(`${this.apiUrl}/solicitudes/${idSolicitud}/evidencias`, formData);
  }

  listarSupervisores(idObra?: number): Observable<{ id_usuario: number; nombre_completo: string; nombre_rol: string; username: string }[]> {
    let params = new HttpParams();
    if (idObra) params = params.set('id_obra', idObra.toString());
    return this.http.get<{ id_usuario: number; nombre_completo: string; nombre_rol: string; username: string }[]>(`${this.apiUrl}/supervisores`, { params });
  }

  consultarMetricas(): Observable<{ success: boolean; metricas: MetricasPosventa }> {
    return this.http.get<{ success: boolean; metricas: MetricasPosventa }>(`${this.apiUrl}/metricas`);
  }
}
