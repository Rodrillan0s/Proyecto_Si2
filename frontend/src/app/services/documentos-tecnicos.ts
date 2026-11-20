
import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface DocumentoTecnico {
  id_documento: number;
  id_obra: number;
  nombre: string;
  descripcion?: string | null;
  tipo_documento: string;
  version_actual: number;
  estado: string;
  id_version?: number;
  numero_version?: number;
  nombre_archivo?: string;
  tipo_archivo?: string;
  tamano_bytes?: number;
  observaciones?: string;
  username?: string;
  created_at?: string;
  updated_at?: string;
}

export interface VersionDocumento {
  id_version: number;
  id_documento: number;
  numero_version: number;
  nombre_archivo: string;
  ruta_archivo?: string;
  tipo_archivo?: string;
  tamano_bytes: number;
  observaciones?: string;
  id_usuario?: number;
  username?: string;
  created_at?: string;
}

export interface HistorialDocumento {
  documento: DocumentoTecnico;
  versiones: VersionDocumento[];
}

export interface DocumentoResponse<T> {
  success: boolean;
  data: T;
  message?: string;
  id_documento?: number;
  id_version?: number;
}

export interface DocumentoMutationResponse {
  success: boolean;
  message: string;
  id_documento?: number;
  id_version?: number;
}

@Injectable({
  providedIn: 'root'
})
export class DocumentosTecnicosService {
  private http = inject(HttpClient);
  private readonly url = `${environment.apiUrl}/api/documentos-tecnicos`;

  listarPorObra(
    idObra: number
  ): Observable<DocumentoResponse<DocumentoTecnico[]>> {
    return this.http.get<DocumentoResponse<DocumentoTecnico[]>>(
      `${this.url}/obra/${idObra}`
    );
  }

  obtener(
    idDocumento: number
  ): Observable<DocumentoResponse<DocumentoTecnico>> {
    return this.http.get<DocumentoResponse<DocumentoTecnico>>(
      `${this.url}/${idDocumento}`
    );
  }

  registrar(formData: FormData): Observable<DocumentoMutationResponse> {
    return this.http.post<DocumentoMutationResponse>(
      this.url,
      formData
    );
  }

  historial(
    idDocumento: number
  ): Observable<DocumentoResponse<HistorialDocumento>> {
    return this.http.get<DocumentoResponse<HistorialDocumento>>(
      `${this.url}/${idDocumento}/historial`
    );
  }

  crearVersion(
    idDocumento: number,
    formData: FormData
  ): Observable<DocumentoMutationResponse> {
    return this.http.post<DocumentoMutationResponse>(
      `${this.url}/${idDocumento}/versiones`,
      formData
    );
  }

  descargar(
    idDocumento: number,
    idVersion: number
  ): Observable<Blob> {
    return this.http.get(
      `${this.url}/${idDocumento}/versiones/${idVersion}/descargar`,
      { responseType: 'blob' }
    );
  }

  cambiarEstado(
    idDocumento: number,
    estado: 'ACTIVO' | 'INACTIVO'
  ): Observable<DocumentoMutationResponse> {
    return this.http.patch<DocumentoMutationResponse>(
      `${this.url}/${idDocumento}/estado`,
      { estado }
    );
  }
}
