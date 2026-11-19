import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import { AuthService } from './auth';

export interface EmpresaComercial {
  id_empresa: number;
  slug: string;
  nombre_empresa: string;
  nit?: number;
  descripcion?: string;
  total_obras: number;
  total_unidades: number;
}

export interface UnidadComercial {
  id_unidad: number;
  codigo_unidad: string;
  nombre_unidad: string;
  descripcion_unidad?: string;
  tipo_unidad: string;
  superficie_m2: string;
  superficie_m2_num: number;
  cantidad_plantas: number;
  dormitorios: number;
  banos: number;
  ambientes_resumen: string;
  especificacion_acabado: string;
  estado_construccion: string;
  disponibilidad_comercial: string;
  id_obra: number;
  nombre_obra: string;
  ubicacion?: string;
  zona?: string;
  precio_bob: string;
  precio_usd: string;
  costo_m2_bob: string;
  costo_m2_usd: string;
  fuente_precio: string;
  afinidad_score?: number;
  razones_recomendacion?: string[];
  observaciones_criterio?: string[];
  ventajas_competitivas?: string[];
}

export interface EstiloAcabadoInfo {
  codigo: string;
  nombre: string;
  factor_referencial: string;
  acabados_incluidos: string[];
}

export interface LeadContactPayload {
  nombre_completo: string;
  telefono?: string;
  email?: string;
  ci?: string;
  presupuesto_estimado?: number | null;
  moneda?: string;
  unidades_interes?: number[];
  notas?: string;
  horario_preferido?: string;
  conversacion_id?: string | null;
}

export interface CommercialChatPayload {
  mensaje: string;
  conversacion_id?: string | null;
  presupuesto_max?: number | null;
  moneda?: string;
  tipo_unidad_preferido?: string | null;
  estilo_preferido?: string | null;
  min_dormitorios?: number | null;
  ids_unidades_comparar?: number[];
  contacto?: LeadContactPayload | null;
}

export interface CostEstimationPayload {
  superficie_m2: number;
  tipo_inmueble: string;
  estilo_acabado: string;
  cantidad_plantas: number;
  dormitorios: number;
  banos: number;
  presupuesto_objetivo?: number | null;
  moneda: string;
  incluir_parqueo: boolean;
  incluir_baulera: boolean;
  incluir_domotica: boolean;
}

export interface MensajeComercialPersistido {
  id: string;
  rol: 'user' | 'assistant';
  texto: string;
  intencion?: string;
  planoPreviewUrl?: string | null;
  planoNombre?: string | null;
  estiloPlano?: string | null;
  unidades?: UnidadComercial[];
  comparativa?: any;
  estimacionCosto?: any;
  lecturaPlano?: any;
  registroCrm?: any;
  requiereContacto?: boolean;
  mostrarFormularioContacto?: boolean;
  sugerencias?: string[];
  fecha: string;
}

export interface SesionChatComercial {
  conversacionId: string | null;
  mensajes: MensajeComercialPersistido[];
  mensajeInput: string;
  archivoPlano: File | null;
  previewPlanoUrl: string | null;
  estiloPlanoSeleccionado: string;
  unidadesSeleccionadasComparar: number[];
  unidadesInteresContacto: number[];
  formContacto: {
    nombre_completo: string;
    telefono: string;
    email: string;
    ci: string;
    presupuesto_estimado: number | null;
    moneda: string;
    horario_preferido: string;
    notas: string;
  };
  catalogo?: any;
}

@Injectable({
  providedIn: 'root',
})
export class AsistenteComercialService {
  private http = inject(HttpClient);
  private auth = inject(AuthService);
  private baseUrl = `${environment.apiUrl}/api/public/comercial`;

  empresasCache: EmpresaComercial[] = [];
  empresaRefActiva: string | number = '';
  private sesiones = new Map<string, SesionChatComercial>();
  private ultimoUsuarioId: string | number | null = null;

  constructor() {
    const usuarioInicial = this.auth.obtenerUsuario();
    this.ultimoUsuarioId = usuarioInicial?.id_usuario ?? (usuarioInicial?.id ?? null);

    this.auth.usuario$.subscribe((user) => {
      const nuevoId = user?.id_usuario ?? (user?.id ?? null);
      if (nuevoId !== this.ultimoUsuarioId) {
        this.ultimoUsuarioId = nuevoId;
        this.limpiarTodasLasSesiones();
      }
    });
  }

  obtenerClaveSesion(empresaRef: string | number): string {
    const usuario = this.auth.obtenerUsuario();
    const userPrefix = usuario?.id_usuario ? `user_${usuario.id_usuario}` : 'anon';
    return `${userPrefix}:${empresaRef || 'default'}`;
  }

  obtenerSesion(empresaRef: string | number): SesionChatComercial {
    const key = this.obtenerClaveSesion(empresaRef);
    let sesion = this.sesiones.get(key);
    if (!sesion) {
      sesion = this.crearSesionVacia();
      this.sesiones.set(key, sesion);
    }
    return sesion;
  }

  reiniciarSesion(empresaRef: string | number): SesionChatComercial {
    const key = this.obtenerClaveSesion(empresaRef);
    const anterior = this.sesiones.get(key);
    const nueva = this.crearSesionVacia();
    if (anterior?.catalogo) {
      nueva.catalogo = anterior.catalogo;
    }
    this.sesiones.set(key, nueva);
    return nueva;
  }

  limpiarTodasLasSesiones(): void {
    this.sesiones.clear();
    this.empresaRefActiva = '';
  }

  private crearSesionVacia(): SesionChatComercial {
    return {
      conversacionId: null,
      mensajes: [],
      mensajeInput: '',
      archivoPlano: null,
      previewPlanoUrl: null,
      estiloPlanoSeleccionado: 'MINIMALISTA',
      unidadesSeleccionadasComparar: [],
      unidadesInteresContacto: [],
      formContacto: {
        nombre_completo: '',
        telefono: '',
        email: '',
        ci: '',
        presupuesto_estimado: null,
        moneda: 'USD',
        horario_preferido: 'Mañana (09:00 - 12:00)',
        notas: '',
      },
    };
  }

  listarEmpresas(): Observable<{ success: boolean; data: EmpresaComercial[] }> {
    return this.http.get<{ success: boolean; data: EmpresaComercial[] }>(`${this.baseUrl}/empresas`);
  }

  obtenerCatalogo(empresaRef: string | number): Observable<{ success: boolean; data: any }> {
    return this.http.get<{ success: boolean; data: any }>(
      `${this.baseUrl}/${encodeURIComponent(String(empresaRef))}/catalogo`
    );
  }

  enviarConsultaChat(
    empresaRef: string | number,
    payload: CommercialChatPayload
  ): Observable<any> {
    return this.http.post<any>(
      `${this.baseUrl}/${encodeURIComponent(String(empresaRef))}/chat`,
      payload
    );
  }

  estimarCosto(
    empresaRef: string | number,
    payload: CostEstimationPayload
  ): Observable<any> {
    return this.http.post<any>(
      `${this.baseUrl}/${encodeURIComponent(String(empresaRef))}/estimar-costo`,
      payload
    );
  }

  analizarPlano(
    empresaRef: string | number,
    archivo: File,
    opciones: {
      mensaje?: string;
      presupuesto_max?: number | null;
      moneda?: string;
      estilo_preferido?: string | null;
      conversacion_id?: string | null;
    }
  ): Observable<any> {
    const formData = new FormData();
    formData.append('archivo', archivo, archivo.name);
    if (opciones.mensaje) formData.append('mensaje', opciones.mensaje);
    if (opciones.presupuesto_max != null && opciones.presupuesto_max > 0) {
      formData.append('presupuesto_max', String(opciones.presupuesto_max));
    }
    formData.append('moneda', opciones.moneda || 'USD');
    if (opciones.estilo_preferido) {
      formData.append('estilo_preferido', opciones.estilo_preferido);
    }
    if (opciones.conversacion_id) {
      formData.append('conversacion_id', opciones.conversacion_id);
    }
    return this.http.post<any>(
      `${this.baseUrl}/${encodeURIComponent(String(empresaRef))}/analizar-plano`,
      formData
    );
  }

  solicitarContacto(
    empresaRef: string | number,
    payload: LeadContactPayload
  ): Observable<any> {
    return this.http.post<any>(
      `${this.baseUrl}/${encodeURIComponent(String(empresaRef))}/solicitar-contacto`,
      payload
    );
  }
}
