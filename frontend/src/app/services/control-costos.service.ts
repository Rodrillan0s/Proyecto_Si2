import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export type EstadoCosto = 'REGISTRADO' | 'ANULADO';
export type CategoriaCosto = 'MATERIAL' | 'MANO_OBRA' | 'EQUIPO' | 'SUBCONTRATO' | 'OTRO';
export type EstadoOrden = 'PENDIENTE' | 'APROBADA' | 'RECHAZADA';
export type TipoCambio = 'AUMENTO_CANTIDAD' | 'DISMINUCION_CANTIDAD' | 'CAMBIO_COSTO' | 'NUEVA_PARTIDA' | 'ELIMINACION_PARTIDA';

export interface ApiResponse<T> { success: boolean; data: T; }

export interface PresupuestoAprobado {
  id_estimacion: number;
  id_obra: number;
  nombre: string;
  version: number;
  estado: 'APROBADA';
  descripcion?: string | null;
  cliente: string;
  monto_total: number;
  obra_codigo: string;
  obra_nombre: string;
  moneda: string;
  costo_directo_presupuestado: number;
  total_partidas: number;
}

export interface LineaBase {
  id_control_costo: number;
  id_empresa: number;
  id_obra: number;
  id_estimacion_base: number;
  version_presupuesto: number;
  moneda: string;
  estado: 'ACTIVO' | 'CERRADO';
  seleccionado_por: number;
  seleccionado_en: string;
  presupuesto_nombre?: string;
  presupuesto_estado?: string;
  obra_codigo?: string;
  obra_nombre?: string;
}

export interface CostoEjecutado {
  id_costo_ejecutado: number;
  id_control_costo: number;
  id_empresa: number;
  id_obra: number;
  id_partida_presupuestaria: number;
  fecha: string;
  concepto: string;
  categoria: CategoriaCosto;
  cantidad: number;
  costo_unitario: number;
  monto: number;
  documento?: string | null;
  observacion?: string | null;
  estado: EstadoCosto;
  registrado_por: number;
  anulado_por?: number | null;
  anulado_en?: string | null;
  motivo_anulacion?: string | null;
  item_codigo?: string;
  partida_nombre?: string;
  unidad?: string;
  presupuesto_version?: number;
}

export interface CostoCreatePayload {
  id_control_costo: number;
  id_partida_presupuestaria: number;
  fecha: string;
  concepto: string;
  categoria: CategoriaCosto;
  cantidad: number;
  costo_unitario: number;
  monto: number;
  documento?: string | null;
  observacion?: string | null;
}

export interface ComparacionPartida {
  id_partida_presupuestaria: number | null;
  item_codigo: string;
  partida: string;
  unidad: string;
  cantidad_presupuestada: number;
  costo_directo_unitario: number;
  costo_presupuestado: number;
  impacto_ordenes_aprobadas: number;
  presupuesto_revisado: number;
  costo_ejecutado: number;
  nueva_partida: boolean;
  variacion_original: number;
  variacion_original_porcentaje: number | null;
  variacion_revisada: number;
  variacion_revisada_porcentaje: number | null;
}

export interface TotalesControl {
  costo_presupuestado_original: number;
  impacto_ordenes_aprobadas: number;
  presupuesto_revisado: number;
  costo_ejecutado: number;
  variacion_original: number;
  variacion_original_porcentaje: number | null;
  variacion_revisada: number;
  variacion_revisada_porcentaje: number | null;
  total_partidas?: number;
  total_costos_registrados?: number;
  total_costos_anulados?: number;
  ordenes_pendientes?: number;
  ordenes_aprobadas?: number;
  ordenes_rechazadas?: number;
}

export interface ComparacionControl {
  linea_base: LineaBase;
  partidas: ComparacionPartida[];
  totales: TotalesControl;
}

export interface ResumenControl { linea_base: LineaBase; resumen: TotalesControl; }

// Campos devueltos por CU32; no se derivan importes en el cliente.
export interface ResumenFinalControl extends ResumenControl {
  obra: {
    id_obra: number;
    id_empresa: number;
    codigo: string;
    nombre: string;
    estado_obra: 'FINALIZADO';
    moneda: string;
  };
  resumen: TotalesControl & {
    costo_final_registrado: number;
    costo_mano_obra_calculado?: number;
    total_trabajadores_con_costo?: number;
    total_jornadas_trabajadas?: number;
  };
  desglose_por_categoria?: Partial<Record<CategoriaCosto, number>>;
  mano_obra_trabajadores?: JornadaCierreManoObra[];
}

export interface TrabajadorManoObra {
  id_usuario: number;
  nombre_completo: string;
  nombre_rol: string;
  id_salario?: number | null;
  salario_diario?: number | null;
  salario_vigente_desde?: string | null;
}

export interface JornadaManoObra {
  id_jornada: number;
  id_usuario: number;
  nombre_completo: string;
  fecha: string;
  dias_trabajados: number;
  salario_diario: number;
  costo_calculado: number;
}

export interface JornadaCierreManoObra extends Omit<JornadaManoObra, 'id_jornada'> {
  nombre_rol: string;
  id_salario: number;
}

export interface ResumenManoObra {
  trabajadores: TrabajadorManoObra[];
  jornadas: JornadaManoObra[];
}

export interface OrdenCambioDetalle {
  id_orden_cambio_detalle: number;
  id_orden_cambio: number;
  id_partida_presupuestaria?: number | null;
  id_analisis_precio_unitario?: number | null;
  tipo_cambio: TipoCambio;
  item_codigo_snapshot: string;
  descripcion_snapshot: string;
  unidad_snapshot: string;
  cantidad_anterior: number;
  cantidad_delta: number;
  cantidad_revisada: number;
  costo_anterior: number;
  costo_nuevo: number;
  impacto_costo: number;
  observacion?: string | null;
}

export interface OrdenCambio {
  id_orden_cambio: number;
  codigo: string;
  id_control_costo: number;
  id_empresa: number;
  id_obra: number;
  id_estimacion_base: number;
  titulo: string;
  descripcion?: string | null;
  justificacion: string;
  fecha: string;
  impacto_costo: number;
  impacto_plazo_dias: number;
  estado: EstadoOrden;
  solicitado_por: number;
  decidido_por?: number | null;
  fecha_decision?: string | null;
  motivo_decision?: string | null;
  obra_codigo?: string;
  obra_nombre?: string;
  presupuesto_nombre?: string;
  presupuesto_version?: number;
  total_detalles?: number;
  detalles?: OrdenCambioDetalle[];
}

export interface OrdenDetallePayload {
  id_partida_presupuestaria?: number | null;
  id_analisis_precio_unitario?: number | null;
  tipo_cambio: TipoCambio;
  item_codigo_snapshot?: string | null;
  descripcion_snapshot?: string | null;
  unidad_snapshot?: string | null;
  cantidad_delta: number;
  costo_nuevo?: number | null;
  observacion?: string | null;
}

export interface OrdenCreatePayload {
  id_control_costo: number;
  codigo: string;
  titulo: string;
  descripcion?: string | null;
  justificacion: string;
  fecha: string;
  impacto_plazo_dias: number;
  detalles: OrdenDetallePayload[];
}

export type OrdenUpdatePayload = Omit<OrdenCreatePayload, 'id_control_costo' | 'codigo'>;

export interface HistorialOrden {
  id_orden_cambio_historial: number;
  id_orden_cambio: number;
  estado_anterior?: EstadoOrden | null;
  estado_nuevo: EstadoOrden;
  accion: 'CREACION' | 'MODIFICACION' | 'APROBACION' | 'RECHAZO';
  comentario?: string | null;
  id_usuario: number;
  fecha_evento: string;
  ip_origen?: string | null;
  usuario: string;
}

@Injectable({ providedIn: 'root' })
export class ControlCostosService {
  private readonly http = inject(HttpClient);
  private readonly api = `${environment.apiUrl}/api/control-costos`;

  private params(values: Record<string, string | number | undefined>): HttpParams {
    let params = new HttpParams();
    Object.entries(values).forEach(([key, value]) => {
      if (value !== undefined && value !== '') params = params.set(key, String(value));
    });
    return params;
  }

  presupuestosAprobados(idObra: number): Observable<ApiResponse<PresupuestoAprobado[]>> {
    return this.http.get<ApiResponse<PresupuestoAprobado[]>>(`${this.api}/obras/${idObra}/presupuestos-aprobados`);
  }

  crearLineaBase(idObra: number, idEstimacionBase: number): Observable<ApiResponse<LineaBase>> {
    return this.http.post<ApiResponse<LineaBase>>(`${this.api}/lineas-base`, { id_obra: idObra, id_estimacion_base: idEstimacionBase });
  }

  lineaBase(idObra: number): Observable<ApiResponse<LineaBase>> {
    return this.http.get<ApiResponse<LineaBase>>(`${this.api}/obras/${idObra}/linea-base`);
  }

  costos(filters: { id_obra?: number; id_control_costo?: number; id_partida?: number; estado?: EstadoCosto } = {}): Observable<ApiResponse<CostoEjecutado[]>> {
    return this.http.get<ApiResponse<CostoEjecutado[]>>(`${this.api}/costos`, { params: this.params(filters) });
  }

  registrarCosto(payload: CostoCreatePayload): Observable<ApiResponse<CostoEjecutado>> {
    return this.http.post<ApiResponse<CostoEjecutado>>(`${this.api}/costos`, payload);
  }

  anularCosto(id: number, motivo: string): Observable<ApiResponse<CostoEjecutado>> {
    return this.http.post<ApiResponse<CostoEjecutado>>(`${this.api}/costos/${id}/anular`, { motivo });
  }

  resumen(idObra: number): Observable<ApiResponse<ResumenControl>> {
    return this.http.get<ApiResponse<ResumenControl>>(`${this.api}/obras/${idObra}/resumen`);
  }

  resumenFinal(idObra: number): Observable<ApiResponse<ResumenFinalControl>> {
    return this.http.get<ApiResponse<ResumenFinalControl>>(`${this.api}/obras/${idObra}/resumen`, {
      params: new HttpParams().set('final', 'true')
    });
  }

  manoObra(idObra: number): Observable<ApiResponse<ResumenManoObra>> {
    return this.http.get<ApiResponse<ResumenManoObra>>(`${this.api}/obras/${idObra}/mano-obra`);
  }

  registrarSalario(
    idObra: number,
    idUsuario: number,
    payload: { salario_diario: number; fecha_vigencia: string }
  ): Observable<ApiResponse<{ id_salario: number; id_usuario: number; salario_diario: number; fecha_vigencia: string }>> {
    return this.http.post<ApiResponse<{ id_salario: number; id_usuario: number; salario_diario: number; fecha_vigencia: string }>>(
      `${this.api}/obras/${idObra}/trabajadores/${idUsuario}/salarios`, payload
    );
  }

  registrarJornada(
    idObra: number,
    payload: { id_usuario: number; fecha: string; dias_trabajados: number }
  ): Observable<ApiResponse<{ id_jornada: number; id_usuario: number; fecha: string; dias_trabajados: number; id_salario: number }>> {
    return this.http.post<ApiResponse<{ id_jornada: number; id_usuario: number; fecha: string; dias_trabajados: number; id_salario: number }>>(
      `${this.api}/obras/${idObra}/jornadas`, payload
    );
  }

  comparacion(idObra: number): Observable<ApiResponse<ComparacionControl>> {
    return this.http.get<ApiResponse<ComparacionControl>>(`${this.api}/obras/${idObra}/comparacion`);
  }

  ordenes(filters: { id_obra?: number; id_control_costo?: number; estado?: EstadoOrden } = {}): Observable<ApiResponse<OrdenCambio[]>> {
    return this.http.get<ApiResponse<OrdenCambio[]>>(`${this.api}/ordenes-cambio`, { params: this.params(filters) });
  }

  orden(id: number): Observable<ApiResponse<OrdenCambio>> {
    return this.http.get<ApiResponse<OrdenCambio>>(`${this.api}/ordenes-cambio/${id}`);
  }

  crearOrden(payload: OrdenCreatePayload): Observable<ApiResponse<OrdenCambio>> {
    return this.http.post<ApiResponse<OrdenCambio>>(`${this.api}/ordenes-cambio`, payload);
  }

  actualizarOrden(id: number, payload: OrdenUpdatePayload): Observable<ApiResponse<OrdenCambio>> {
    return this.http.put<ApiResponse<OrdenCambio>>(`${this.api}/ordenes-cambio/${id}`, payload);
  }

  aprobarOrden(id: number, comentario?: string): Observable<ApiResponse<OrdenCambio>> {
    return this.http.post<ApiResponse<OrdenCambio>>(`${this.api}/ordenes-cambio/${id}/aprobar`, { comentario: comentario?.trim() || null });
  }

  rechazarOrden(id: number, motivo: string): Observable<ApiResponse<OrdenCambio>> {
    return this.http.post<ApiResponse<OrdenCambio>>(`${this.api}/ordenes-cambio/${id}/rechazar`, { motivo });
  }

  historial(id: number): Observable<ApiResponse<HistorialOrden[]>> {
    return this.http.get<ApiResponse<HistorialOrden[]>>(`${this.api}/ordenes-cambio/${id}/historial`);
  }
}
