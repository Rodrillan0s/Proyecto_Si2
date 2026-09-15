import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import { AuthService } from './auth';

export interface OrdenTrabajo {
  orden_nro: number;
  id_obra: number;
  codigo?: string;
  nombre?: string;
  id_empresa?: number;
  nombre_empresa?: string;
  tipo_trab?: string;
  cuadrilla?: number;
  estado?: string;
  fecha_inicio?: string;
  fecha_fin?: string;
  observacion?: string;
}

export interface ResponsableOrdenTrabajo {
  id_usuario: number;
  username: string;
  nombre_completo: string;
  correo: string;
  telefono: string;
  id_rol: number;
  nombre_rol: string;
  id_empresa: number;
  nombre_empresa: string;
  fecha_asignacion: string;
}
export interface RespuestaApiOrdenesTrabajo {
  success: boolean;
  message?: string;
  data: OrdenTrabajo[];
}
export interface RespuestaApiResponsablesOrdenTrabajo {
  success: boolean;
  message?: string;
  data: ResponsableOrdenTrabajo[];
}

export interface OrdenTrabajoPayload {
  id_obra: number;
  tipo_trab: string;
  cuadrilla: number;
  estado: string;
  fecha_inicio: string;
  fecha_fin?: string;
  observacion?: string;
  id_usuarios: number[];
}

export interface EstadoOrdenTrabajo {
  estado: string;
}

@Injectable({
  providedIn: 'root'
})
export class OrdenesTrabajoService {

  private http = inject(HttpClient);
  private authService = inject(AuthService);
  private apiUrl = environment.apiUrl;

  private getHeaders(): HttpHeaders {
    const token = this.authService.obtenerToken();

    return token
      ? new HttpHeaders({
          Authorization: `Bearer ${token}`
        })
      : new HttpHeaders();
  }

  listarOrdenesTrabajo(id_empresa?: number, id_obra?: number): Observable<RespuestaApiOrdenesTrabajo> {
    let params = new HttpParams();
    if (id_empresa) {
      params = params.set('id_empresa', id_empresa.toString());
    }
    if (id_obra) {
      params = params.set('id_obra', id_obra.toString());
    }

    return this.http.get<RespuestaApiOrdenesTrabajo>(
      `${this.apiUrl}/api/ordenes-trabajo/`,
      {
        headers: this.getHeaders(),
        params
      }
    );
  }

  obtenerOrdenTrabajo(orden_nro: number): Observable<OrdenTrabajo> {
    return this.http.get<OrdenTrabajo>(
      `${this.apiUrl}/api/ordenes-trabajo/${orden_nro}`,
      {
        headers: this.getHeaders()
      }
    );
  }

  crearOrdenTrabajo(datos: OrdenTrabajoPayload): Observable<any> {
    return this.http.post(
      `${this.apiUrl}/api/ordenes-trabajo/`,
      datos,
      {
        headers: this.getHeaders()
      }
    );
  }

  actualizarOrdenTrabajo(
    orden_nro: number,
    datos: OrdenTrabajoPayload
  ): Observable<any> {
    return this.http.put(
      `${this.apiUrl}/api/ordenes-trabajo/${orden_nro}`,
      datos,
      {
        headers: this.getHeaders()
      }
    );
  }

  eliminarOrdenTrabajo(orden_nro: number): Observable<any> {
    return this.http.delete(
      `${this.apiUrl}/api/ordenes-trabajo/${orden_nro}`,
      {
        headers: this.getHeaders()
      }
    );
  }

  actualizarEstado(
    orden_nro: number,
    datos: EstadoOrdenTrabajo
  ): Observable<any> {
    return this.http.put(
      `${this.apiUrl}/api/ordenes-trabajo/${orden_nro}/estado`,
      datos,
      {
        headers: this.getHeaders()
      }
    );
  }

  obtenerHistorial(
    orden_nro: number
  ): Observable<OrdenTrabajo[]> {
    return this.http.get<OrdenTrabajo[]>(
      `${this.apiUrl}/api/ordenes-trabajo/${orden_nro}/historial`,
      {
        headers: this.getHeaders()
      }
    );
  }

 listarResponsablesOrdenTrabajo(
  orden_nro: number
): Observable<RespuestaApiResponsablesOrdenTrabajo> {
  return this.http.get<RespuestaApiResponsablesOrdenTrabajo>(
    `${this.apiUrl}/api/ordenes-trabajo/${orden_nro}/responsables`,
    {
      headers: this.getHeaders()
    }
  );
}
  asignarResponsableOrdenTrabajo(
    orden_nro: number,
    id_usuario: number
  ): Observable<any> {
    return this.http.post(
      `${this.apiUrl}/api/ordenes-trabajo/${orden_nro}/responsables`,
      {
        id_usuario
      },
      {
        headers: this.getHeaders()
      }
    );
  }

  eliminarResponsableOrdenTrabajo(
    orden_nro: number,
    id_usuario: number
  ): Observable<any> {
    return this.http.delete(
      `${this.apiUrl}/api/ordenes-trabajo/${orden_nro}/responsables/${id_usuario}`,
      {
        headers: this.getHeaders()
      }
    );
  }
}