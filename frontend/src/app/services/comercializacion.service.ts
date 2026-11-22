import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export type EstadoComercial = 'DISPONIBLE' | 'RESERVADA' | 'VENDIDA' | 'NO_DISPONIBLE';
export type EstadoConstructivo = 'PLANIFICADO' | 'EN_CONSTRUCCION' | 'FINALIZADO' | 'SUSPENDIDO';
export type MonedaComercial = 'BOB' | 'USD';

export interface UnidadComercial {
  id_unidad: number;
  codigo: string;
  tipo_unidad: string;
  superficie?: number | null;
  estado_constructivo: string;
  estado_comercial: EstadoComercial;
  publicado_comercial: boolean;
  precio_venta?: number | null;
  moneda_comercial: MonedaComercial;
  descripcion_comercial?: string | null;
  id_estructura: number;
  nombre_estructura: string;
  id_obra: number;
  nombre_obra: string;
  codigo_obra: string;
  disponible_efectiva: boolean;
  total_fotos: number;
  foto_principal?: string | null;
  estado_crm_activo?: string | null;
}

export interface AsociacionCrmActiva {
  id_cliente_unidad: number;
  id_cliente: number;
  estado_asociacion: string;
  monto_pactado?: number | null;
  monto_reserva?: number | null;
  fecha_vencimiento_reserva?: string | null;
  fecha_asociacion?: string | null;
  observaciones?: string | null;
  nombre_cliente: string;
  telefono_cliente?: string | null;
  email_cliente?: string | null;
  id_usuario_registro?: number | null;
}

export interface FotografiaUnidad {
  id_fotografia: number;
  id_unidad: number;
  ruta_archivo: string;
  nombre_archivo: string;
  tipo_mime?: string;
  tamano_bytes?: number;
  es_principal: boolean;
  orden: number;
  id_usuario?: number | null;
  created_at?: string;
}

export interface HistorialComercialUnidad {
  id_historial: number;
  id_unidad: number;
  tipo_evento: string;
  estado_anterior?: string | null;
  estado_nuevo?: string | null;
  precio_venta?: number | null;
  monto_pactado?: number | null;
  observacion?: string | null;
  fecha: string;
  usuario_registro?: string | null;
  cliente_relacionado?: string | null;
  id_cliente?: number | null;
  id_cliente_unidad?: number | null;
  id_usuario?: number | null;
  monto_reserva?: number | null;
  fecha_vencimiento_reserva?: string | null;
  estado_asociacion_crm?: string | null;
}

export interface ResumenComercial {
  total_unidades: number;
  total_publicadas: number;
  total_no_publicadas: number;
  por_estado_comercial: {
    DISPONIBLE: number;
    RESERVADA: number;
    VENDIDA: number;
    NO_DISPONIBLE: number;
  };
  disponibles_efectivas: number;
  kpis_financieros?: {
    valor_inventario_disponible: number;
    valor_inventario_reservado: number;
    valor_inventario_vendido: number;
  };
}

export interface DetalleUnidadComercial extends UnidadComercial {
  id_empresa?: number;
  asociacion_crm?: AsociacionCrmActiva | null;
  fotografias: FotografiaUnidad[];
  historial_reciente: HistorialComercialUnidad[];
}

export interface DisponibilidadUnidad {
  id_unidad: number;
  codigo: string;
  estado_constructivo: string;
  estado_comercial: EstadoComercial;
  publicado_comercial: boolean;
  disponible_efectiva: boolean;
  bloqueada_por_crm: boolean;
  asociacion_crm?: AsociacionCrmActiva | null;
  transiciones_permitidas: string[];
}

export interface FiltrosUnidadesComerciales {
  id_obra?: number;
  estado_comercial?: string;
  publicado?: boolean;
  tipo_unidad?: string;
  solo_disponibles?: boolean;
  q?: string;
  precio_min?: number;
  precio_max?: number;
  page?: number;
  limit?: number;
  id_empresa?: number;
}

export interface RespuestaListaUnidades {
  data: UnidadComercial[];
  total: number;
  page: number;
  limit: number;
}

@Injectable({
  providedIn: 'root'
})
export class ComercializacionService {
  private http = inject(HttpClient);
  readonly apiUrl = `${environment.apiUrl}/api/comercializacion`;

  listarUnidades(filtros?: FiltrosUnidadesComerciales): Observable<RespuestaListaUnidades> {
    let params = new HttpParams();
    if (filtros) {
      if (filtros.id_obra) params = params.set('id_obra', filtros.id_obra.toString());
      if (filtros.estado_comercial) params = params.set('estado_comercial', filtros.estado_comercial);
      if (filtros.publicado !== undefined && filtros.publicado !== null) {
        params = params.set('publicado', filtros.publicado.toString());
      }
      if (filtros.tipo_unidad) params = params.set('tipo_unidad', filtros.tipo_unidad);
      if (filtros.solo_disponibles) params = params.set('solo_disponibles', 'true');
      if (filtros.q) params = params.set('q', filtros.q);
      if (filtros.precio_min !== undefined && filtros.precio_min !== null) {
        params = params.set('precio_min', filtros.precio_min.toString());
      }
      if (filtros.precio_max !== undefined && filtros.precio_max !== null) {
        params = params.set('precio_max', filtros.precio_max.toString());
      }
      if (filtros.page) params = params.set('page', filtros.page.toString());
      if (filtros.limit) params = params.set('limit', filtros.limit.toString());
      if (filtros.id_empresa) params = params.set('id_empresa', filtros.id_empresa.toString());
    }
    return this.http.get<RespuestaListaUnidades>(`${this.apiUrl}/unidades`, { params });
  }

  obtenerResumen(id_obra?: number, id_empresa?: number): Observable<ResumenComercial> {
    let params = new HttpParams();
    if (id_obra) params = params.set('id_obra', id_obra.toString());
    if (id_empresa) params = params.set('id_empresa', id_empresa.toString());
    return this.http.get<ResumenComercial>(`${this.apiUrl}/resumen`, { params });
  }

  obtenerDetalle(id_unidad: number, id_empresa?: number): Observable<DetalleUnidadComercial> {
    let params = new HttpParams();
    if (id_empresa) params = params.set('id_empresa', id_empresa.toString());
    return this.http.get<DetalleUnidadComercial>(`${this.apiUrl}/unidades/${id_unidad}`, { params });
  }

  consultarDisponibilidad(id_unidad: number, id_empresa?: number): Observable<DisponibilidadUnidad> {
    let params = new HttpParams();
    if (id_empresa) params = params.set('id_empresa', id_empresa.toString());
    return this.http.get<DisponibilidadUnidad>(`${this.apiUrl}/unidades/${id_unidad}/disponibilidad`, { params });
  }

  actualizarComercializacion(id_unidad: number, datos: {
    publicado_comercial?: boolean;
    precio_venta?: number | null;
    moneda_comercial?: MonedaComercial;
    descripcion_comercial?: string | null;
    estado_comercial?: EstadoComercial;
    observacion?: string;
  }, id_empresa?: number): Observable<DetalleUnidadComercial> {
    let params = new HttpParams();
    if (id_empresa) params = params.set('id_empresa', id_empresa.toString());
    return this.http.patch<DetalleUnidadComercial>(`${this.apiUrl}/unidades/${id_unidad}`, datos, { params });
  }

  cambiarPublicacion(id_unidad: number, publicado: boolean, id_empresa?: number): Observable<DetalleUnidadComercial> {
    let params = new HttpParams();
    if (id_empresa) params = params.set('id_empresa', id_empresa.toString());
    return this.http.patch<DetalleUnidadComercial>(`${this.apiUrl}/unidades/${id_unidad}/publicacion`, {
      publicado_comercial: publicado
    }, { params });
  }

  cambiarEstado(id_unidad: number, datos: {
    estado_comercial: EstadoComercial;
    observacion?: string;
    observaciones?: string;
    cancelar_reserva?: boolean;
  }, id_empresa?: number): Observable<any> {
    let params = new HttpParams();
    if (id_empresa) params = params.set('id_empresa', id_empresa.toString());
    return this.http.patch<any>(`${this.apiUrl}/unidades/${id_unidad}/estado`, datos, { params });
  }

  registrarReserva(id_unidad: number, datos: {
    id_cliente: number;
    monto_reserva: number;
    monto_pactado?: number | null;
    fecha_vencimiento_reserva?: string | null;
    observaciones?: string | null;
  }, id_empresa?: number): Observable<any> {
    let params = new HttpParams();
    if (id_empresa) params = params.set('id_empresa', id_empresa.toString());
    return this.http.post<any>(`${this.apiUrl}/unidades/${id_unidad}/reservas`, datos, { params });
  }

  cancelarReserva(id_unidad: number, datos?: { motivo?: string; observaciones?: string }, id_empresa?: number): Observable<any> {
    let params = new HttpParams();
    if (id_empresa) params = params.set('id_empresa', id_empresa.toString());
    return this.http.post<any>(`${this.apiUrl}/unidades/${id_unidad}/cancelar-reserva`, datos || {}, { params });
  }

  confirmarVenta(id_unidad: number, datos?: {
    id_cliente?: number;
    monto_pactado?: number | null;
    observaciones?: string | null;
  }, id_empresa?: number): Observable<any> {
    let params = new HttpParams();
    if (id_empresa) params = params.set('id_empresa', id_empresa.toString());
    return this.http.post<any>(`${this.apiUrl}/unidades/${id_unidad}/confirmar-venta`, datos || {}, { params });
  }

  listarFotografias(id_unidad: number, id_empresa?: number): Observable<{ id_unidad: number; fotografias: FotografiaUnidad[]; total: number }> {
    let params = new HttpParams();
    if (id_empresa) params = params.set('id_empresa', id_empresa.toString());
    return this.http.get<{ id_unidad: number; fotografias: FotografiaUnidad[]; total: number }>(`${this.apiUrl}/unidades/${id_unidad}/fotografias`, { params });
  }

  subirFotografia(id_unidad: number, archivo: File, es_principal = false, orden = 1, id_empresa?: number): Observable<FotografiaUnidad> {
    const formData = new FormData();
    formData.append('archivo', archivo);
    formData.append('es_principal', es_principal ? 'true' : 'false');
    formData.append('orden', orden.toString());

    let params = new HttpParams();
    if (id_empresa) params = params.set('id_empresa', id_empresa.toString());

    return this.http.post<FotografiaUnidad>(`${this.apiUrl}/unidades/${id_unidad}/fotografias`, formData, { params });
  }

  marcarFotografiaPrincipal(id_unidad: number, id_fotografia: number, id_empresa?: number): Observable<any> {
    let params = new HttpParams();
    if (id_empresa) params = params.set('id_empresa', id_empresa.toString());
    return this.http.patch<any>(`${this.apiUrl}/unidades/${id_unidad}/fotografias/${id_fotografia}/principal`, {}, { params });
  }

  eliminarFotografia(id_unidad: number, id_fotografia: number, id_empresa?: number): Observable<any> {
    let params = new HttpParams();
    if (id_empresa) params = params.set('id_empresa', id_empresa.toString());
    return this.http.delete<any>(`${this.apiUrl}/unidades/${id_unidad}/fotografias/${id_fotografia}`, { params });
  }

  obtenerUrlFotografia(id_unidad: number, id_fotografia: number): string {
    return `${this.apiUrl}/unidades/${id_unidad}/fotografias/${id_fotografia}/archivo`;
  }

  listarHistorial(id_unidad: number, tipo_evento?: string, limit = 100, id_empresa?: number): Observable<{ id_unidad: number; historial: HistorialComercialUnidad[]; total: number }> {
    let params = new HttpParams().set('limit', limit.toString());
    if (tipo_evento) params = params.set('tipo_evento', tipo_evento);
    if (id_empresa) params = params.set('id_empresa', id_empresa.toString());
    return this.http.get<{ id_unidad: number; historial: HistorialComercialUnidad[]; total: number }>(`${this.apiUrl}/unidades/${id_unidad}/historial`, { params });
  }
}
