import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface RespuestaConsultaIA {
  success: boolean;
  pregunta: string;
  respuesta: string;
  empresa_autorizada?: string;
  metricas?: any;
}

export interface SugerenciasIA {
  success: boolean;
  sugerencias: string[];
}

@Injectable({
  providedIn: 'root'
})
export class AiService {
  private http = inject(HttpClient);
  private apiUrl = `${environment.apiUrl}/api/ai`;

  consultarCRM(pregunta: string, id_empresa?: number): Observable<RespuestaConsultaIA> {
    let params = new HttpParams();
    if (id_empresa) params = params.set('id_empresa', id_empresa.toString());
    return this.http.post<RespuestaConsultaIA>(`${this.apiUrl}/crm/consulta`, { pregunta }, { params });
  }

  obtenerSugerencias(): Observable<SugerenciasIA> {
    return this.http.get<SugerenciasIA>(`${this.apiUrl}/crm/sugerencias`);
  }
}
