import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../environments/environment';
import { AuthService } from './auth';

export interface PlanSuscripcion {
  codigo: string;
  nombre: string;
  descripcion: string;
  prestaciones: string[];
  limite_usuarios?: number;
  limite_obras?: number;
  consultas_ia_mes?: number;
  nivel_reportes?: string;
  exportar_reportes?: boolean;
  automatizar_reportes?: boolean;
  modulos?: string[];
  version?: number;
  actualizado_en?: string;
}
export interface ModuloPlan { codigo: string; nombre: string; }
export interface ConfiguracionPlan {
  version: number; nombre: string; descripcion: string; modulos: string[];
  limite_usuarios: number; limite_obras: number; consultas_ia_mes: number;
  nivel_reportes: 'NINGUNO' | 'OPERATIVOS' | 'TODOS';
  exportar_reportes: boolean; automatizar_reportes: boolean;
}
export interface EmpresaImpactada {
  id_empresa: number; nombre_empresa: string; estado: string; usuarios_activos: number; obras_activas: number;
}
export interface ImpactoPlan {
  empresas: EmpresaImpactada[]; total_empresas: number; empresas_sobre_cupo: EmpresaImpactada[];
  modulos_retirados: ModuloPlan[]; confirmacion: string; mensaje: string;
}
export interface HistorialPlan {
  id: number; version: number; id_actor: number | null; creado_en: string;
  antes: PlanSuscripcion; despues: PlanSuscripcion; empresas_afectadas: EmpresaImpactada[];
}
export interface SuscripcionEmpresa {
  id_empresa: number;
  nombre_empresa: string;
  codigo_plan: string | null;
  nombre_plan: string | null;
  estado: 'ACTIVA' | 'SUSPENDIDA' | 'CANCELADA' | null;
  estado_efectivo: string;
  fecha_inicio: string | null;
  fecha_fin: string | null;
  usuarios: number;
  usuarios_activos?: number;
  obras_activas?: number;
  limite_usuarios?: number;
  limite_obras?: number;
  consultas_ia_mes?: number;
  consultas_ia_usadas?: number;
  solo_lectura?: boolean;
  ia_habilitada?: boolean;
  gracia_hasta?: string | null;
  modulos?: string[];
  modulos_solo_lectura?: ModuloPlan[];
}
export interface AsignacionSuscripcion {
  codigo_plan: string;
  estado: 'ACTIVA' | 'SUSPENDIDA' | 'CANCELADA';
  fecha_inicio: string;
  fecha_fin: string | null;
}

@Injectable({ providedIn: 'root' })
export class SuscripcionService {
  private auth = inject(AuthService);
  readonly acceso = signal<SuscripcionEmpresa | null>(null);
  private version = 0;
  get global() { return this.auth.obtenerRolNormalizado() === 'ADMINISTRADOR'; }
  get iaPermitida() { return this.global || this.acceso()?.ia_habilitada === true; }
  cargarAcceso() {
    const version = ++this.version;
    this.acceso.set(null);
    if (this.global || !this.auth.obtenerToken()) return;
    this.propia().subscribe({ next: res => { if (version === this.version) this.acceso.set(res.data); }, error: () => {} });
  }
  private http = inject(HttpClient);
  private url = `${environment.apiUrl}/api/suscripciones`;
  planes() { return this.http.get<{ data: PlanSuscripcion[] }>(`${this.url}/planes`); }
  modulos() { return this.http.get<{ data: ModuloPlan[] }>(`${this.url}/configuracion/modulos`); }
  previsualizarPlan(codigo: string, datos: ConfiguracionPlan) {
    return this.http.post<{ data: ImpactoPlan }>(`${this.url}/planes/${encodeURIComponent(codigo)}/previsualizar`, datos);
  }
  configurarPlan(codigo: string, datos: ConfiguracionPlan, confirmacion: string) {
    return this.http.put<{ data: PlanSuscripcion }>(`${this.url}/planes/${encodeURIComponent(codigo)}`, { ...datos, confirmacion });
  }
  historialPlan(codigo: string) {
    return this.http.get<{ data: HistorialPlan[] }>(`${this.url}/planes/${encodeURIComponent(codigo)}/historial`);
  }
  empresas() { return this.http.get<{ data: SuscripcionEmpresa[] }>(`${this.url}/empresas`); }
  propia() { return this.http.get<{ data: SuscripcionEmpresa }>(`${this.url}/mi-empresa`); }
  guardar(id: number, datos: AsignacionSuscripcion) {
    return this.http.put<{ data: SuscripcionEmpresa }>(`${this.url}/empresas/${id}`, datos);
  }
}
