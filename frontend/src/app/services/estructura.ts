import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { AuthService } from './auth';
import { environment } from '../../environments/environment';

export interface EstructuraNodo {
  id_estructura?: number;
  id_obra: number;
  id_padre?: number | null;
  nombre: string;
  tipo: string;
  descripcion?: string;
  orden?: number;
  created_at?: string;
  updated_at?: string;
  // Propiedades UI para el árbol
  hijos?: EstructuraNodo[];
  expandido?: boolean;
}

export interface ApiResponseEstructura {
  success: boolean;
  data: EstructuraNodo[];
  arbol: EstructuraNodo[];
  message?: string;
}

export interface ApiResponseSimple {
  success: boolean;
  message?: string;
  id_estructura?: number;
}

@Injectable({
  providedIn: 'root'
})
export class EstructuraService {
  private http = inject(HttpClient);
  private authService = inject(AuthService);
  private apiUrl = environment.apiUrl;

  private getHeaders(): HttpHeaders {
    const token = this.authService.obtenerToken();
    return token ? new HttpHeaders({ 'Authorization': `Bearer ${token}` }) : new HttpHeaders();
  }

  listarEstructura(idObra: number): Observable<ApiResponseEstructura> {
    return this.http.get<ApiResponseEstructura>(
      `${this.apiUrl}/api/proyectos/${idObra}/estructuras/`,
      { headers: this.getHeaders() }
    );
  }

  crearElemento(idObra: number, data: Partial<EstructuraNodo>): Observable<ApiResponseSimple> {
    return this.http.post<ApiResponseSimple>(
      `${this.apiUrl}/api/proyectos/${idObra}/estructuras/`,
      data,
      { headers: this.getHeaders() }
    );
  }

  actualizarElemento(idObra: number, idEstructura: number, data: Partial<EstructuraNodo>): Observable<ApiResponseSimple> {
    return this.http.put<ApiResponseSimple>(
      `${this.apiUrl}/api/proyectos/${idObra}/estructuras/${idEstructura}`,
      data,
      { headers: this.getHeaders() }
    );
  }

  eliminarElemento(idObra: number, idEstructura: number): Observable<ApiResponseSimple> {
    return this.http.delete<ApiResponseSimple>(
      `${this.apiUrl}/api/proyectos/${idObra}/estructuras/${idEstructura}`,
      { headers: this.getHeaders() }
    );
  }

  reordenarElemento(idObra: number, idEstructura: number, direccion: 'UP' | 'DOWN'): Observable<ApiResponseSimple> {
    return this.http.put<ApiResponseSimple>(
      `${this.apiUrl}/api/proyectos/${idObra}/estructuras/${idEstructura}/reordenar`,
      { direccion },
      { headers: this.getHeaders() }
    );
  }
}
