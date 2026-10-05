import { inject, Injectable } from '@angular/core';
import { HttpClient, HttpResponse } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../environments/environment';

export type BackupScope = 'base_datos' | 'sistema_completo';
export interface BackupStatus {
  configurado: boolean;
  control_disponible: boolean;
  requisitos: string[];
  worker_activo: boolean;
  ultimo_latido: string | null;
  entorno: string;
  mantenimiento: boolean;
  motivo: string | null;
  replica_remota: boolean;
  almacenamiento_persistente: boolean;
  restauracion_habilitada: boolean;
  requisitos_restauracion: string[];
}
export interface BackupSchedule {
  habilitada: boolean;
  alcance: BackupScope;
  frecuencia: 'diario' | 'semanal' | 'mensual';
  hora: string;
  zona_horaria: string;
  dia_semana: number;
  dia_mes: number;
  retencion_dias: 7 | 15 | 30 | 90;
}
export interface BackupArchive {
  id: string;
  nombre: string;
  bytes: number;
  sha256: string;
  alcance: BackupScope;
  corte: string;
  entorno_origen: string;
  release_sha256: string;
  verificado_en: string | null;
  eliminado_en: string | null;
  replica_remota: boolean;
}
export interface BackupJob {
  id: string;
  estado: 'PENDIENTE' | 'GENERANDO' | 'VERIFICANDO' | 'LISTO' | 'FALLIDO';
  etapa: string;
  error: string | null;
  archivo: string | null;
  origen: string;
  solicitud: { alcance: BackupScope };
  created_at: string;
  finished_at: string | null;
  respaldo?: BackupArchive;
}
export interface BackupRestore {
  id: string;
  estado: string;
  etapa: string;
  error: string | null;
  archivo: string;
  desafio: string;
  validada_en: string | null;
  aplicar_en: string | null;
  confirmacion_requerida: string;
  respaldo: BackupArchive;
  pasos: { paso: string; estado: string }[];
}

@Injectable({ providedIn: 'root' })
export class BackupService {
  private http = inject(HttpClient);
  private url = `${environment.apiUrl}/api/backup`;
  estado() {
    return firstValueFrom(this.http.get<BackupStatus>(`${this.url}/estado`));
  }
  historial(pagina = 1, estado = '') {
    return firstValueFrom(
      this.http.get<{ items: BackupJob[]; total: number; pagina: number }>(
        `${this.url}/ejecuciones`,
        { params: { pagina, limite: 20, ...(estado ? { estado } : {}) } },
      ),
    );
  }
  crear(alcance: BackupScope, key: string) {
    return firstValueFrom(
      this.http.post<BackupJob>(
        `${this.url}/ejecuciones`,
        { alcance },
        { headers: { 'Idempotency-Key': key } },
      ),
    );
  }
  ejecucion(id: string) {
    return firstValueFrom(this.http.get<BackupJob>(`${this.url}/ejecuciones/${id}`));
  }
  descargar(id: string): Promise<HttpResponse<Blob>> {
    return firstValueFrom(
      this.http.get(`${this.url}/ejecuciones/${id}/archivo`, {
        observe: 'response',
        responseType: 'blob',
      }),
    );
  }
  programacion() {
    return firstValueFrom(
      this.http.get<{ configuracion: BackupSchedule; next_run: string | null }>(
        `${this.url}/programacion`,
      ),
    );
  }
  guardar(config: BackupSchedule) {
    return firstValueFrom(
      this.http.put<{ configuracion: BackupSchedule; next_run: string | null }>(
        `${this.url}/programacion`,
        config,
      ),
    );
  }
  importar(file: File) {
    return firstValueFrom(
      this.http.post<BackupArchive>(`${this.url}/importaciones`, file, {
        headers: { 'Content-Type': 'application/octet-stream' },
      }),
    );
  }
  restauraciones() {
    return firstValueFrom(this.http.get<BackupRestore[]>(`${this.url}/restauraciones`));
  }
  validar(archivo: string) {
    return firstValueFrom(
      this.http.post<BackupRestore>(`${this.url}/restauraciones/validar`, { archivo }),
    );
  }
  reautenticar(identificador: string, password: string) {
    return firstValueFrom(
      this.http.post<{ token: string }>(`${this.url}/reautenticacion`, { identificador, password }),
    );
  }
  aplicar(id: string, confirmacion: string, desafio: string, token_reautenticacion: string) {
    return firstValueFrom(
      this.http.post<BackupRestore>(`${this.url}/restauraciones/${id}/aplicar`, {
        confirmacion,
        desafio,
        token_reautenticacion,
      }),
    );
  }
}
