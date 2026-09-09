import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import { AuthService } from './auth';

export interface UnidadAmbiente {
  id_ambiente?: number;
  nombre: string;
  cantidad: number;
}

export interface UnidadCaracteristica {
  id_caracteristica?: number;
  nombre: string;
  valor: string;
}

export interface UnidadPersonalizacion {
  id_personalizacion?: number;
  tipo: string;
  descripcion: string;
  created_at?: string;
}

export interface UnidadSeguimiento {
  id_seguimiento?: number;
  estado_anterior?: string;
  estado_nuevo: string;
  id_usuario?: number;
  observacion?: string;
  fecha?: string;
}

export interface UnidadMaterial {
  id_unidad_material?: number;
  id_material: number;
  nombre_material?: string;
  cantidad: number;
  unidad_medida?: string;
  uso_ubicacion?: string;
  acabado?: string;
  observacion?: string;
}

export interface UnidadConstruccion {
  id_unidad?: number;
  id_estructura?: number;
  id_padre?: number | null;
  codigo?: string;
  nombre: string;
  tipo_estructura?: string;
  descripcion?: string;
  tipo_unidad: string;
  superficie: number | null;
  cantidad_plantas: number | null;
  estado: string;
  id_modelo?: number | null;
  modelo_nombre?: string;
  id_obra?: number;
  proyecto_nombre?: string;
  proyecto_codigo?: string;
  ruta_jerarquica?: string;
  ambientes: UnidadAmbiente[];
  caracteristicas: UnidadCaracteristica[];
  personalizaciones?: UnidadPersonalizacion[];
  seguimiento?: UnidadSeguimiento[];
  materiales?: UnidadMaterial[];
  created_at?: string;
  updated_at?: string;
}

export interface ModeloUnidad {
  id_modelo?: number;
  id_empresa?: number;
  nombre: string;
  descripcion?: string;
  tipo_unidad: string;
  superficie_base: number | null;
  cantidad_plantas_base: number | null;
  activo?: boolean;
  caracteristicas?: UnidadCaracteristica[];
}

export interface MaterialDisponible {
  id_material: number;
  nombre_material: string;
  precio?: number;
}

export interface RespuestaApi<T> {
  success: boolean;
  data: T;
  error?: string;
  message?: string;
}

@Injectable({ providedIn: 'root' })
export class UnidadesService {
  private http = inject(HttpClient);
  private authService = inject(AuthService);
  private apiUrl = environment.apiUrl;

  private headers(): HttpHeaders {
    const token = this.authService.obtenerToken();
    return token ? new HttpHeaders({ Authorization: `Bearer ${token}` }) : new HttpHeaders();
  }

  listar(idObra: number): Observable<RespuestaApi<UnidadConstruccion[]>> {
    return this.http.get<RespuestaApi<UnidadConstruccion[]>>(
      `${this.apiUrl}/api/proyectos/${idObra}/unidades/`, { headers: this.headers() }
    );
  }

  obtener(idObra: number, idUnidad: number): Observable<RespuestaApi<UnidadConstruccion>> {
    return this.http.get<RespuestaApi<UnidadConstruccion>>(
      `${this.apiUrl}/api/proyectos/${idObra}/unidades/${idUnidad}`, { headers: this.headers() }
    );
  }

  crear(idObra: number, data: Partial<UnidadConstruccion>): Observable<any> {
    return this.http.post(
      `${this.apiUrl}/api/proyectos/${idObra}/unidades/`, data, { headers: this.headers() }
    );
  }

  actualizar(idObra: number, idUnidad: number, data: Partial<UnidadConstruccion>): Observable<any> {
    return this.http.put(
      `${this.apiUrl}/api/proyectos/${idObra}/unidades/${idUnidad}`, data, { headers: this.headers() }
    );
  }

  eliminar(idObra: number, idUnidad: number): Observable<any> {
    return this.http.delete(
      `${this.apiUrl}/api/proyectos/${idObra}/unidades/${idUnidad}`, { headers: this.headers() }
    );
  }

  cambiarEstado(idObra: number, idUnidad: number, estado: string, observacion: string): Observable<any> {
    return this.http.patch(
      `${this.apiUrl}/api/proyectos/${idObra}/unidades/${idUnidad}/estado`,
      { estado, observacion }, { headers: this.headers() }
    );
  }

  listarModelos(idObra: number): Observable<RespuestaApi<ModeloUnidad[]>> {
    return this.http.get<RespuestaApi<ModeloUnidad[]>>(
      `${this.apiUrl}/api/proyectos/${idObra}/unidades/modelos`, { headers: this.headers() }
    );
  }

  crearModelo(idObra: number, data: ModeloUnidad): Observable<any> {
    return this.http.post(
      `${this.apiUrl}/api/proyectos/${idObra}/unidades/modelos`, data, { headers: this.headers() }
    );
  }

  actualizarModelo(idObra: number, idModelo: number, data: ModeloUnidad): Observable<any> {
    return this.http.put(
      `${this.apiUrl}/api/proyectos/${idObra}/unidades/modelos/${idModelo}`, data,
      { headers: this.headers() }
    );
  }

  agregarPersonalizacion(idObra: number, idUnidad: number, data: UnidadPersonalizacion): Observable<any> {
    return this.http.post(
      `${this.apiUrl}/api/proyectos/${idObra}/unidades/${idUnidad}/personalizaciones`,
      data, { headers: this.headers() }
    );
  }

  eliminarPersonalizacion(idObra: number, idUnidad: number, idPersonalizacion: number): Observable<any> {
    return this.http.delete(
      `${this.apiUrl}/api/proyectos/${idObra}/unidades/${idUnidad}/personalizaciones/${idPersonalizacion}`,
      { headers: this.headers() }
    );
  }

  listarMateriales(idObra: number): Observable<RespuestaApi<MaterialDisponible[]>> {
    return this.http.get<RespuestaApi<MaterialDisponible[]>>(
      `${this.apiUrl}/api/proyectos/${idObra}/unidades/materiales-disponibles`,
      { headers: this.headers() }
    );
  }

  guardarMateriales(idObra: number, idUnidad: number, materiales: UnidadMaterial[]): Observable<any> {
    return this.http.put(
      `${this.apiUrl}/api/proyectos/${idObra}/unidades/${idUnidad}/materiales`,
      { materiales }, { headers: this.headers() }
    );
  }
}
