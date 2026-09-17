import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface Presupuesto {
  id_presupuesto: number;
  id_obra: number;
  codigo: string;
  nombre: string;
  descripcion?: string | null;
  version: number;
  estado: 'BORRADOR' | 'EN_REVISION' | 'APROBADO' | 'CERRADO';
  es_vigente: boolean;
  fecha?: string | null;
  superficie_m2?: number | null;
  tipo_suelo?: string | null;
  costo_m2_estimado?: number | null;
  monto_estimado_inicial?: number | null;
  total_presupuesto: number;
  observaciones?: string | null;
  created_at?: string;
  updated_at?: string;
  partidas?: PartidaPresupuesto[];
}

export interface PartidaPresupuesto {
  id_partida: number;
  id_presupuesto: number;
  id_apu?: number | null;
  codigo: string;
  nombre: string;
  descripcion?: string | null;
  id_unidad_medida: number;
  cantidad: number;
  precio_unitario: number;
  importe_total: number;
  orden: number;
  id_estructura?: number | null;
  id_unidad_construccion?: number | null;
  unidad_medida_nombre?: string;
  unidad_medida_abrev?: string;
  apu_codigo?: string;
  apu_nombre?: string;
  incidencia_pct?: number;
}

export interface ApuComponente {
  id_componente: number;
  id_apu: number;
  tipo_recurso: 'MATERIAL' | 'MANO_OBRA' | 'EQUIPO' | 'OTRO';
  id_recurso?: number | null;
  descripcion_recurso: string;
  id_unidad_medida: number;
  cantidad: number;
  precio_unitario: number;
  subtotal: number;
  unidad_medida_nombre?: string;
  unidad_medida_abrev?: string;
}

export interface Apu {
  id_apu: number;
  id_empresa: number;
  id_obra?: number | null;
  codigo: string;
  nombre: string;
  descripcion?: string | null;
  id_unidad_medida: number;
  rendimiento_base: number;
  costo_unitario_total: number;
  estado: string;
  unidad_medida_nombre?: string;
  unidad_medida_abrev?: string;
  total_componentes?: number;
  componentes?: ApuComponente[];
}

export interface DesgloseRecurso {
  tipo_recurso: string;
  monto_total: number;
  porcentaje: number;
}

export interface MetricasParametricas {
  superficie_m2?: number | null;
  tipo_suelo?: string | null;
  costo_m2_estimado?: number | null;
  monto_estimado_inicial?: number | null;
  costo_m2_analitico_real?: number | null;
  desviacion_monto?: number | null;
  desviacion_porcentaje?: number | null;
}

export interface PresupuestoConsolidado {
  presupuesto: Presupuesto;
  total_presupuesto: number;
  total_partidas: number;
  partidas: PartidaPresupuesto[];
  desglose_recursos: DesgloseRecurso[];
  desglose_estructura: any[];
  metricas_parametricas: MetricasParametricas;
}

export interface CostoEjecutado {
  id_costo_ejecutado: number;
  id_obra: number;
  id_partida?: number | null;
  codigo_costo?: string;
  origen_costo: string;
  tipo_recurso: string;
  descripcion: string;
  id_unidad_medida?: number | null;
  cantidad: number;
  costo_unitario: number;
  importe_total: number;
  fecha: string;
  observacion?: string;
  unidad_medida_nombre?: string;
  unidad_medida_abrev?: string;
  partida_codigo?: string;
  partida_nombre?: string;
}

export interface ComparativaPartida {
  id_partida: number;
  codigo: string;
  nombre: string;
  unidad_medida?: string;
  cantidad_presupuestada: number;
  precio_unitario_presupuestado: number;
  importe_presupuestado: number;
  cantidad_ejecutada: number;
  importe_ejecutado: number;
  variacion_monto: number;
  variacion_porcentaje: number;
  estado_desvio: 'SOBRECOSTO' | 'AHORRO' | 'EN_PRESUPUESTO' | 'NO_INICIADO';
}

export interface ComparativaPresupuesto {
  id_obra: number;
  presupuesto_evaluado?: Presupuesto;
  total_presupuestado: number;
  total_ejecutado: number;
  variacion_global_monto: number;
  variacion_global_porcentaje: number;
  indice_eficiencia_cpi: number;
  total_costos_sin_partida: number;
  cantidad_costos_sin_partida: number;
  comparativa_partidas: ComparativaPartida[];
}

@Injectable({
  providedIn: 'root'
})
export class PresupuestosService {
  private http = inject(HttpClient);
  private apiUrl = environment.apiUrl;

  // ─── HU53: Presupuestos de Obra ───
  listarPresupuestos(idObra: number): Observable<{ success: boolean; data: Presupuesto[] }> {
    return this.http.get<{ success: boolean; data: Presupuesto[] }>(
      `${this.apiUrl}/api/proyectos/${idObra}/presupuestos/`
    );
  }

  obtenerPresupuesto(idObra: number, idPresupuesto: number): Observable<{ success: boolean; data: Presupuesto }> {
    return this.http.get<{ success: boolean; data: Presupuesto }>(
      `${this.apiUrl}/api/proyectos/${idObra}/presupuestos/${idPresupuesto}`
    );
  }

  crearPresupuesto(idObra: number, data: Partial<Presupuesto>): Observable<{ success: boolean; message: string; id_presupuesto: number }> {
    return this.http.post<{ success: boolean; message: string; id_presupuesto: number }>(
      `${this.apiUrl}/api/proyectos/${idObra}/presupuestos/`,
      data
    );
  }

  actualizarPresupuesto(idObra: number, idPresupuesto: number, data: Partial<Presupuesto>): Observable<any> {
    return this.http.put(
      `${this.apiUrl}/api/proyectos/${idObra}/presupuestos/${idPresupuesto}`,
      data
    );
  }

  eliminarPresupuesto(idObra: number, idPresupuesto: number): Observable<any> {
    return this.http.delete(
      `${this.apiUrl}/api/proyectos/${idObra}/presupuestos/${idPresupuesto}`
    );
  }

  // ─── HU54: Partidas del Presupuesto ───
  crearPartida(idObra: number, idPresupuesto: number, data: any): Observable<{ success: boolean; message: string; id_partida: number }> {
    return this.http.post<{ success: boolean; message: string; id_partida: number }>(
      `${this.apiUrl}/api/proyectos/${idObra}/presupuestos/${idPresupuesto}/partidas`,
      data
    );
  }

  actualizarPartida(idObra: number, idPresupuesto: number, idPartida: number, data: any): Observable<any> {
    return this.http.put(
      `${this.apiUrl}/api/proyectos/${idObra}/presupuestos/${idPresupuesto}/partidas/${idPartida}`,
      data
    );
  }

  eliminarPartida(idObra: number, idPresupuesto: number, idPartida: number): Observable<any> {
    return this.http.delete(
      `${this.apiUrl}/api/proyectos/${idObra}/presupuestos/${idPresupuesto}/partidas/${idPartida}`
    );
  }

  asociarApuAPartida(idObra: number, idPresupuesto: number, idPartida: number, data: { id_apu: number; congelar_costo?: boolean }): Observable<any> {
    return this.http.post(
      `${this.apiUrl}/api/proyectos/${idObra}/presupuestos/${idPresupuesto}/partidas/${idPartida}/asociar-apu`,
      data
    );
  }

  // ─── HU55 & HU56: APU Corporativo y Componentes ───
  listarApus(idObra?: number, q?: string): Observable<{ success: boolean; data: Apu[] }> {
    let params = new HttpParams();
    if (idObra) params = params.set('id_obra', idObra.toString());
    if (q) params = params.set('q', q);
    return this.http.get<{ success: boolean; data: Apu[] }>(`${this.apiUrl}/api/apus/`, { params });
  }

  obtenerApu(idApu: number): Observable<{ success: boolean; data: Apu }> {
    return this.http.get<{ success: boolean; data: Apu }>(`${this.apiUrl}/api/apus/${idApu}`);
  }

  crearApu(data: any): Observable<{ success: boolean; message: string; id_apu: number }> {
    return this.http.post<{ success: boolean; message: string; id_apu: number }>(`${this.apiUrl}/api/apus/`, data);
  }

  actualizarApu(idApu: number, data: any): Observable<any> {
    return this.http.put(`${this.apiUrl}/api/apus/${idApu}`, data);
  }

  agregarComponenteApu(idApu: number, data: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/api/apus/${idApu}/componentes`, data);
  }

  actualizarComponenteApu(idApu: number, idComponente: number, data: any): Observable<any> {
    return this.http.put(`${this.apiUrl}/api/apus/${idApu}/componentes/${idComponente}`, data);
  }

  eliminarComponenteApu(idApu: number, idComponente: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/api/apus/${idApu}/componentes/${idComponente}`);
  }

  // ─── HU58: Consolidado, Aprobación de Línea Base y Versionado ───
  obtenerConsolidado(idObra: number, idPresupuesto: number): Observable<{ success: boolean; data: PresupuestoConsolidado }> {
    return this.http.get<{ success: boolean; data: PresupuestoConsolidado }>(
      `${this.apiUrl}/api/proyectos/${idObra}/presupuestos/${idPresupuesto}/consolidado`
    );
  }

  aprobarLineaBase(idObra: number, idPresupuesto: number): Observable<{ success: boolean; message: string; data: any }> {
    return this.http.post<{ success: boolean; message: string; data: any }>(
      `${this.apiUrl}/api/proyectos/${idObra}/presupuestos/${idPresupuesto}/aprobar`,
      {}
    );
  }

  cambiarEstado(idObra: number, idPresupuesto: number, estado: string): Observable<any> {
    return this.http.patch(
      `${this.apiUrl}/api/proyectos/${idObra}/presupuestos/${idPresupuesto}/estado`,
      { estado }
    );
  }

  versionarPresupuesto(idObra: number, idPresupuesto: number, data?: { codigo?: string; nombre?: string }): Observable<{ success: boolean; message: string; data: Presupuesto }> {
    return this.http.post<{ success: boolean; message: string; data: Presupuesto }>(
      `${this.apiUrl}/api/proyectos/${idObra}/presupuestos/${idPresupuesto}/versionar`,
      data || {}
    );
  }

  // ─── HU59: Costos Ejecutados Reales ───
  listarCostosEjecutados(idObra: number, filters?: any): Observable<{ success: boolean; data: { total_registros: number; monto_total_ejecutado: number; costos: CostoEjecutado[] } }> {
    let params = new HttpParams();
    if (filters?.id_partida) params = params.set('id_partida', filters.id_partida.toString());
    if (filters?.tipo_recurso) params = params.set('tipo_recurso', filters.tipo_recurso);
    if (filters?.origen_costo) params = params.set('origen_costo', filters.origen_costo);
    if (filters?.fecha_inicio) params = params.set('fecha_inicio', filters.fecha_inicio);
    if (filters?.fecha_fin) params = params.set('fecha_fin', filters.fecha_fin);

    return this.http.get<any>(
      `${this.apiUrl}/api/proyectos/${idObra}/costos-ejecutados/`,
      { params }
    );
  }

  registrarCostoEjecutado(idObra: number, data: any): Observable<{ success: boolean; message: string; id_costo_ejecutado: number }> {
    return this.http.post<{ success: boolean; message: string; id_costo_ejecutado: number }>(
      `${this.apiUrl}/api/proyectos/${idObra}/costos-ejecutados/`,
      data
    );
  }

  eliminarCostoEjecutado(idObra: number, idCosto: number): Observable<any> {
    return this.http.delete(
      `${this.apiUrl}/api/proyectos/${idObra}/costos-ejecutados/${idCosto}`
    );
  }

  // ─── HU60: Comparativa Presupuestado vs Ejecutado ───
  obtenerComparativa(idObra: number, idPresupuesto?: number): Observable<{ success: boolean; data: ComparativaPresupuesto }> {
    let params = new HttpParams();
    if (idPresupuesto) params = params.set('id_presupuesto', idPresupuesto.toString());
    return this.http.get<{ success: boolean; data: ComparativaPresupuesto }>(
      `${this.apiUrl}/api/proyectos/${idObra}/presupuestos/comparativa`,
      { params }
    );
  }
}
