import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { environment } from '../../environments/environment';

export interface GarantiaInmobiliaria {
  id_garantia: number;
  id_empresa: number;
  id_unidad: number;
  unidad_codigo?: string;
  unidad_nombre?: string;
  id_obra?: number;
  obra_nombre?: string;
  codigo: string | null;
  tipo_garantia: string;
  descripcion: string;
  fecha_inicio: string;
  fecha_fin: string | null;
  observaciones: string | null;
  creado_en: string;
}

export interface SeguimientoPosventa {
  id_seguimiento: number;
  id_solicitud_posventa: number;
  id_usuario: number;
  usuario_nombre?: string;
  accion: string;
  estado_anterior: string | null;
  estado_nuevo: string | null;
  observacion: string;
  creado_en: string;
}

export interface SolicitudPosventa {
  id_solicitud_posventa: number;
  id_empresa: number;
  id_unidad: number;
  unidad_codigo?: string;
  unidad_nombre?: string;
  id_obra?: number;
  obra_nombre?: string;
  id_cliente: number;
  cliente_nombre?: string;
  id_garantia: number | null;
  garantia_codigo?: string | null;
  garantia_tipo?: string | null;
  titulo: string;
  descripcion: string;
  categoria: string | null;
  estado: string;
  id_responsable: number | null;
  responsable_nombre?: string | null;
  creado_en: string;
  actualizado_en: string;
  seguimiento?: SeguimientoPosventa[];
}

export interface HistorialUnidadPosventa {
  unidad: {
    id_unidad: number;
    unidad_codigo: string;
    unidad_nombre: string;
    id_obra: number;
    obra_nombre: string;
    id_empresa: number;
  };
  garantias: GarantiaInmobiliaria[];
  solicitudes: SolicitudPosventa[];
}

interface RespuestaApi<T> {
  success: boolean;
  data: T;
}

@Injectable({ providedIn: 'root' })
export class PosventaService {
  private http = inject(HttpClient);
  private url = `${environment.apiUrl}/api/posventa`;

  catalogos() {
    return this.http.get<RespuestaApi<{ categorias: string[]; estados: string[] }>>(`${this.url}/catalogos`);
  }

  listarGarantias(idUnidad?: number) {
    let params = new HttpParams();
    if (idUnidad) params = params.set('id_unidad', String(idUnidad));
    return this.http.get<RespuestaApi<GarantiaInmobiliaria[]>>(`${this.url}/garantias`, { params });
  }

  registrarGarantia(payload: {
    id_unidad: number;
    codigo?: string | null;
    tipo_garantia: string;
    descripcion: string;
    fecha_inicio: string;
    fecha_fin?: string | null;
    observaciones?: string | null;
  }) {
    return this.http.post<RespuestaApi<GarantiaInmobiliaria>>(`${this.url}/garantias`, payload);
  }

  listarSolicitudes(filtros: { id_unidad?: number; estado?: string; categoria?: string } = {}) {
    let params = new HttpParams();
    if (filtros.id_unidad) params = params.set('id_unidad', String(filtros.id_unidad));
    if (filtros.estado) params = params.set('estado', filtros.estado);
    if (filtros.categoria) params = params.set('categoria', filtros.categoria);
    return this.http.get<RespuestaApi<SolicitudPosventa[]>>(`${this.url}/solicitudes`, { params });
  }

  obtenerSolicitud(idSolicitud: number) {
    return this.http.get<RespuestaApi<SolicitudPosventa>>(`${this.url}/solicitudes/${idSolicitud}`);
  }

  registrarSolicitud(payload: {
    id_unidad: number;
    id_garantia?: number | null;
    titulo: string;
    descripcion: string;
  }) {
    return this.http.post<RespuestaApi<SolicitudPosventa>>(`${this.url}/solicitudes`, payload);
  }

  clasificarSolicitud(idSolicitud: number, payload: { categoria: string; observacion?: string }) {
    return this.http.patch<RespuestaApi<SolicitudPosventa>>(
      `${this.url}/solicitudes/${idSolicitud}/clasificar`,
      payload,
    );
  }

  asignarResponsable(idSolicitud: number, payload: { id_responsable: number; observacion?: string }) {
    return this.http.patch<RespuestaApi<SolicitudPosventa>>(
      `${this.url}/solicitudes/${idSolicitud}/asignar`,
      payload,
    );
  }

  gestionarAtencion(idSolicitud: number, payload: { estado?: string; observacion: string }) {
    return this.http.patch<RespuestaApi<SolicitudPosventa>>(
      `${this.url}/solicitudes/${idSolicitud}/atencion`,
      payload,
    );
  }

  historialUnidad(idUnidad: number) {
    return this.http.get<RespuestaApi<HistorialUnidadPosventa>>(
      `${this.url}/unidades/${idUnidad}/historial`,
    );
  }
}
