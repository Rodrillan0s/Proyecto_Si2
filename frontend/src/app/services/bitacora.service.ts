import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface RegistroBitacora {
  id_bitacora: number;
  id_usuario: number;
  nombre: string;
  modulo: string;
  accion: string;
  descripcion: string;
  ip: string;
  estado: string;
  fecha: string | null;
  hora: string | null;
}

export interface PaginacionBitacora {
  page: number;
  limit: number;
  total: number;
  total_pages: number;
}

export interface RespuestaBitacora {
  success: boolean;
  data: RegistroBitacora[];
  pagination: PaginacionBitacora;
}

export interface FiltrosBitacora {
  fecha?: string;
  id_usuario?: number;
  usuario?: string;
  accion?: string;
  page?: number;
  limit?: number;
}

@Injectable({
  providedIn: 'root'
})
export class BitacoraService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = `${environment.apiUrl}/api/bitacora`;

  obtenerBitacora(filtros: FiltrosBitacora = {}): Observable<RespuestaBitacora> {
    let params = new HttpParams();

    for (const [nombre, valor] of Object.entries(filtros)) {
      if (valor !== undefined && valor !== null && String(valor).trim() !== '') {
        params = params.set(nombre, String(valor));
      }
    }

    return this.http.get<RespuestaBitacora>(this.apiUrl, { params });
  }
}
