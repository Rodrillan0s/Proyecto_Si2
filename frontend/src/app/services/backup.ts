import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom, timeout } from 'rxjs';
import { environment } from '../../environments/environment';

export type BackupScope = 'base_datos';
export interface BackupStatus {
  configurado: boolean;
  control_disponible: boolean;
  cola_disponible: boolean;
  requisitos: string[];
  worker_activo: boolean;
  ultimo_latido: string | null;
  entorno: string;
  mantenimiento: boolean;
  motivo: string | null;
  replica_remota: boolean;
  heartbeat_integrado: boolean;
  almacenamiento: 'oci_object_storage';
  descarga_habilitada: boolean;
  requisitos_descarga: string[];
  importacion_habilitada: boolean;
  retencion_gestionada: boolean;
  advertencias: string[];
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
export interface BackupDownload {
  id: string;
  job_id: string;
  estado: 'PENDIENTE' | 'PROCESANDO' | 'COMPLETADO' | 'FALLIDO' | 'EXPIRADO';
  url: string | null;
  expira_en: string | null;
  nombre: string;
  error: string | null;
}
export interface BackupArchive {
  id: string;
  nombre: string;
  bytes: number | null;
  sha256: string;
  alcance: BackupScope;
  corte: string;
  entorno_origen: string;
  verificado_en: string | null;
  eliminado_en: string | null;
  replica_remota: boolean;
}
export interface BackupJob {
  id: string;
  estado: 'PENDIENTE' | 'PROCESANDO' | 'COMPLETADO' | 'FALLIDO';
  tipo: 'BACKUP' | 'RESTORE' | 'DELETE';
  object_name: string | null;
  sha256: string | null;
  size_bytes: number | null;
  job_relacionado_id: string | null;
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
  respaldo: BackupArchive | null;
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
  descargar(id: string) {
    return firstValueFrom(this.http.post<BackupDownload>(`${this.url}/ejecuciones/${id}/archivo`, {}).pipe(timeout(15000)));
  }
  descarga(id: string) {
    return firstValueFrom(this.http.get<BackupDownload>(`${this.url}/descargas/${id}`).pipe(timeout(15000)));
  }
  programacion() {
    return firstValueFrom(
      this.http.get<{ configuracion: BackupSchedule; next_run: string | null; advertencias?: string[] }>(
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
  despachar() {
    return firstValueFrom(
      this.http.post<{ encolado: boolean; trabajo: BackupJob | null }>(
        `${this.url}/programacion/ejecutar`, {},
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
