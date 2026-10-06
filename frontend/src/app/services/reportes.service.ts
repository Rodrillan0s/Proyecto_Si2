import { LecturasCompartidas } from './lecturas';
import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../environments/environment';

export interface ReportFilters {
  id_obra?: number;
  desde?: string;
  hasta?: string;
  estado?: string;
  q?: string;
  id_categoria?: number;
  prioridad?: 'BAJA' | 'MEDIA' | 'ALTA' | 'CRITICA';
}
export interface ReportRequest {
  reporte: string;
  filtros: ReportFilters;
  presentacion?: ReportPresentation;
}
export interface ReportPresentation {
  titulo?: string;
  columnas?: string[];
  ordenar_por?: string;
  orden?: 'asc' | 'desc';
  orientacion?: 'vertical' | 'horizontal';
}
export interface ReportDefinition {
  id: string;
  titulo: string;
  descripcion: string;
  requiere_obra: boolean;
  fechas: boolean;
  fecha_campo?: string;
  campos?: { campo: string; titulo: string }[];
}
export interface Work {
  id_obra: number;
  nombre: string;
  codigo: string;
}
export interface ReportCatalog {
  reportes: ReportDefinition[];
  obras: Work[];
  acciones: string[];
  id_empresa: number;
}
export interface ReportResult {
  titulo: string;
  corte: string;
  columnas: { campo: string; titulo: string; tipo: string }[];
  columnas_disponibles?: { campo: string; titulo: string; tipo: string }[];
  filas: Record<string, unknown>[];
  resumen: Record<string, unknown>;
  advertencias: string[];
  recomendaciones: Record<string, unknown>[];
  solicitud: ReportRequest;
}
export interface Execution {
  id: string;
  estado: string;
  resultado: ReportResult | null;
  error?: string;
  solicitud?: ReportRequest;
  created_at?: string;
}
export interface Interpretation {
  estado: string;
  mensaje: string;
  solicitud?: ReportRequest;
  conversacion: string;
  opciones?: string[];
  obras?: Work[];
}
export interface AssistantResponse extends Interpretation {
  respuesta?: string;
  ejecucion?: Execution;
  ejecuciones?: Execution[];
  tema?: 'reportes' | 'crm' | 'finanzas';
}
export interface Recipient {
  id_usuario: number;
  nombre: string;
}
export interface ReportSchedule {
  id: string;
  habilitada: boolean;
  next_run: string;
  estado: string;
  error?: string;
  configuracion: Record<string, unknown>;
}
export interface ReportDelivery {
  id: string;
  id_usuario: number;
  estado: string;
  error?: string;
  message_id?: string;
}

@Injectable({ providedIn: 'root' })
export class ReportesService {
  private shared = inject(LecturasCompartidas);
  private http = inject(HttpClient);
  private base = `${environment.apiUrl}/api/reportes`;
  private params(company: number | null) {
    return company ? new HttpParams().set('id_empresa', company) : new HttpParams();
  }
  catalog(company: number | null) {
    return firstValueFrom(
      this.shared.obtener(`reportes-catalogo:${company ?? 'global'}`, () => this.http.get<ReportCatalog>(`${this.base}/catalogo`, { params: this.params(company) })),
    );
  }
  interpret(texto: string, company: number | null, conversacion?: string, usar_ia = false) {
    return firstValueFrom(
      this.http.post<Interpretation>(
        `${this.base}/interpretar`,
        { texto, conversacion, usar_ia },
        { params: this.params(company) },
      ),
    );
  }
  assistant(
    texto: string,
    company: number | null,
    conversacion?: string,
      solicitud?: ReportRequest,
      idObraContexto?: number,
  ) {
    return firstValueFrom(
      this.http.post<AssistantResponse>(
        `${environment.apiUrl}/api/ai/consulta`,
          { texto, conversacion, ...(solicitud ? { solicitud } : {}), ...(idObraContexto ? { id_obra_contexto: idObraContexto } : {}) },
        { params: this.params(company) },
      ),
    );
  }
  create(request: ReportRequest, company: number | null) {
    return firstValueFrom(
      this.http.post<Execution>(`${this.base}/ejecuciones`, request, {
        params: this.params(company),
      }),
    );
  }
  execution(id: string) {
    return firstValueFrom(this.http.get<Execution>(`${this.base}/ejecuciones/${id}`));
  }
  history(company: number | null) {
    return firstValueFrom(
      this.http.get<Execution[]>(`${this.base}/ejecuciones`, { params: this.params(company) }),
    );
  }
  recipients(company: number | null) {
    return firstValueFrom(
      this.http.get<Recipient[]>(`${this.base}/destinatarios`, { params: this.params(company) }),
    );
  }
  async download(id: string, formato: 'pdf' | 'xlsx') {
    const file = await firstValueFrom(
      this.http.post<{ id: string; nombre: string }>(
        `${this.base}/ejecuciones/${id}/exportaciones`,
        {},
        { params: { formato } },
      ),
    );
    const bytes = await firstValueFrom(
      this.http.get(`${this.base}/archivos/${file.id}`, { responseType: 'blob' }),
    );
    return { bytes, name: file.nombre };
  }
  send(id: string, destinatarios: number[], formatos: string[], key: string) {
    return firstValueFrom(
      this.http.post(
        `${this.base}/ejecuciones/${id}/envios`,
        { destinatarios, formatos },
        { headers: { 'Idempotency-Key': key } },
      ),
    );
  }
  deliveries(id: string) {
    return firstValueFrom(this.http.get<ReportDelivery[]>(`${this.base}/ejecuciones/${id}/envios`));
  }
  schedules(company: number | null) {
    return firstValueFrom(
      this.http.get<ReportSchedule[]>(`${this.base}/programaciones`, {
        params: this.params(company),
      }),
    );
  }
  schedule(config: Record<string, unknown>, company: number | null) {
    return firstValueFrom(
      this.http.post(`${this.base}/programaciones`, config, { params: this.params(company) }),
    );
  }
  pause(id: string, habilitada: boolean) {
    return firstValueFrom(this.http.patch(`${this.base}/programaciones/${id}`, { habilitada }));
  }
  run(id: string) {
    return firstValueFrom(this.http.post(`${this.base}/programaciones/${id}/ejecutar`, {}));
  }
  transcribe(audio: Blob, company: number | null) {
    const data = new FormData();
    data.append('audio', audio, 'comando.webm');
    return firstValueFrom(
      this.http.post<{ texto: string }>(`${environment.apiUrl}/api/voz/transcribir`, data, {
        params: this.params(company),
      }),
    );
  }
}
