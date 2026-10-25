import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../environments/environment';

export interface ActividadPlan {
  clave: string; nombre: string; descripcion: string; tipo: 'ACTIVIDAD' | 'HITO';
  fecha_inicio: string; fecha_fin: string; inicio_real: string | null; fin_real: string | null;
  avance: number; dependencias: string[];
  estado?: string; dias_retraso?: number; inicio_retrasado?: boolean; bloqueada?: boolean;
}
export interface PlanDraft {
  nombre: string; descripcion: string; fecha_inicio: string; fecha_fin: string;
  actividades: ActividadPlan[]; version?: number;
}
export interface Cronograma extends PlanDraft {
  id_cronograma: number; id_obra: number; version: number;
  programadas: ActividadPlan[]; corte: string;
  resumen: { total: number; completadas: number; retrasadas: number; pendientes_inicio: number };
}
export interface Respuesta<T> { success: boolean; data: T; obra?: { nombre: string; id_empresa: number }; }

/** Nunca envía campos calculados de lectura al contrato de escritura. */
export function actividadesPayload(items: ActividadPlan[]) {
  return items.map(a => ({ clave: a.clave, nombre: a.nombre, descripcion: a.descripcion,
    tipo: a.tipo, fecha_inicio: a.fecha_inicio, fecha_fin: a.fecha_fin,
    inicio_real: a.inicio_real || null, fin_real: a.fin_real || null,
    avance: Number(a.avance), dependencias: [...a.dependencias] }));
}
@Injectable({ providedIn: 'root' })
export class CronogramaService {
  private http = inject(HttpClient);
  private url(obra: number) { return `${environment.apiUrl}/api/obras/${obra}/cronogramas`; }
  listarCronogramas(obra: number) { return this.http.get<Respuesta<Cronograma[]>>(`${this.url(obra)}/`); }
  obtener(obra: number, id: number, filtros: Record<string, string> = {}) {
    return this.http.get<Respuesta<Cronograma>>(`${this.url(obra)}/${id}`, { params: filtros });
  }
  guardar(obra: number, id: number | null, plan: PlanDraft, soloPlanificacion = false) {
    const actividades = actividadesPayload(plan.actividades);
    if (id && soloPlanificacion) return this.http.put<Respuesta<Cronograma>>(`${this.url(obra)}/${id}/planificacion`, { version: plan.version, actividades });
    const payload = { nombre: plan.nombre, descripcion: plan.descripcion, fecha_inicio: plan.fecha_inicio, fecha_fin: plan.fecha_fin, actividades };
    return id ? this.http.put<Respuesta<Cronograma>>(`${this.url(obra)}/${id}`, { ...payload, version: plan.version })
      : this.http.post<Respuesta<Cronograma>>(`${this.url(obra)}/`, payload);
  }
  eliminar(obra: number, plan: Cronograma) {
    return this.http.delete<Respuesta<never>>(`${this.url(obra)}/${plan.id_cronograma}`, { params: { version: plan.version } });
  }
}
