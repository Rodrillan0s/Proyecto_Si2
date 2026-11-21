import { Injectable, inject, PLATFORM_ID, NgZone } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { BehaviorSubject, Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import { AuthService } from './auth';

// ============================================================
// INTERFACES
// ============================================================

export interface Notificacion {
  id_notificacion?: number;
  tipo_alerta: string;
  tipo_referencia?: string;
  titulo: string;
  cuerpo: string;
  data?: any;
  leida: boolean;
  leido?: boolean;
  fecha: Date;
  nro_emergencia?: number;
  id_obra?: number;
}

export interface ConfiguracionAlertaEvento {
  tipo_evento: string;
  nombre: string;
  descripcion: string;
  categoria: string;
  activo: boolean;
  roles_destino: string[];
  origen: 'OBRA' | 'EMPRESA' | 'DEFAULT';
  heredado_de_empresa: boolean;
  actualizado_en?: string | null;
}

export interface RespuestaConfiguracionAlertas {
  success: boolean;
  message?: string;
  id_empresa: number;
  id_obra: number | null;
  nombre_obra: string | null;
  migracion_pendiente: boolean;
  roles_disponibles: string[];
  data: ConfiguracionAlertaEvento[];
}

interface RespuestaHistorial {
  success: boolean;
  message: string;
  no_leidas?: number;
  data: any[];
}

// ============================================================
// SERVICIO
// ============================================================

@Injectable({ providedIn: 'root' })
export class NotificacionesService {

  private http        = inject(HttpClient);
  private authService = inject(AuthService);
  private platformId  = inject(PLATFORM_ID);
  private ngZone      = inject(NgZone);

  private socket: WebSocket | null = null;
  private stopped = false;
  private retry?: ReturnType<typeof setTimeout>;
  private cargandoHistorial = false;

  // Estado reactivo central: mezcla de historial (BD) + push (WS)
  private notificacionesSource = new BehaviorSubject<Notificacion[]>([]);
  notificaciones$: Observable<Notificacion[]> = this.notificacionesSource.asObservable();

  private cargandoSource = new BehaviorSubject<boolean>(false);
  cargando$: Observable<boolean> = this.cargandoSource.asObservable();

  private errorSource = new BehaviorSubject<string | null>(null);
  error$: Observable<string | null> = this.errorSource.asObservable();

  // ----------------------------------------------------------------
  // CONEXIÓN WEBSOCKET
  // ----------------------------------------------------------------

  conectar() {
    this.stopped = false;
    if (!isPlatformBrowser(this.platformId)) return;
    if (this.socket) return;

    const token = this.authService.obtenerToken();
    if (!token) return;
    if (this.authService.tokenExpirado()) return;

    // 1. Cargar historial desde BD antes de abrir el canal en tiempo real
    this.cargarHistorial();

    // 2. Abrir canal WebSocket
    const wsBaseUrl = environment.apiUrl.replace(/^http/, 'ws');
    const wsUrl     = `${wsBaseUrl}/api/ws/notificaciones?token=${encodeURIComponent(token)}`;

    this.ngZone.runOutsideAngular(() => {
      this.socket = new WebSocket(wsUrl);

      this.socket.onopen = () => {
        console.log('WebSocket Notificaciones Conectado');
      };

      this.socket.onmessage = (event) => {
        this.ngZone.run(() => {
          try {
            const dataBackend = JSON.parse(event.data);
            if (!dataBackend || dataBackend.type === 'pong') return;

            const tipo = dataBackend.tipo_referencia || dataBackend.tipo_alerta || dataBackend.tipo || 'GENERAL';
            const idNotif = dataBackend.id_notificacion ? Number(dataBackend.id_notificacion) : undefined;
            const fechaRaw = dataBackend.fecha_creacion || dataBackend.created_at;

            const nuevaNotificacion: Notificacion = {
              id_notificacion: idNotif,
              tipo_alerta:     tipo,
              tipo_referencia: tipo,
              titulo:          dataBackend.titulo || 'Notificación',
              cuerpo:          dataBackend.cuerpo || dataBackend.mensaje || '',
              data:            dataBackend.data,
              leida:           Boolean(dataBackend.leido),
              leido:           Boolean(dataBackend.leido),
              fecha:           fechaRaw ? new Date(fechaRaw) : new Date(),
              nro_emergencia:  dataBackend.nro_emergencia ?? dataBackend.data?.nro_referencia,
              id_obra:         dataBackend.id_obra ?? dataBackend.data?.id_obra,
            };

            const listaActual = this.notificacionesSource.getValue();
            const sinDuplicado = idNotif
              ? listaActual.filter(n => n.id_notificacion !== idNotif)
              : listaActual;
            this.notificacionesSource.next([nuevaNotificacion, ...sinDuplicado]);
          } catch (e) {
            console.error('Error al parsear notificación WS:', e);
          }
        });
      };

      this.socket.onclose = () => {
        this.socket = null;
        if (this.stopped || this.authService.tokenExpirado()) {
          return;
        }
        this.retry = setTimeout(() => { if (!this.stopped) this.conectar(); }, 5000);
      };

      this.socket.onerror = (err) => {
        console.error('WebSocket Error:', err);
      };
    });
  }

  desconectar() {
    this.stopped = true;
    if (this.retry) clearTimeout(this.retry);
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
  }

  // ----------------------------------------------------------------
  // HISTORIAL DESDE BASE DE DATOS (HU142)
  // ----------------------------------------------------------------

  cargarHistorial() {
    if (this.cargandoHistorial) return;
    this.cargandoHistorial = true;
    this.cargandoSource.next(true);
    this.errorSource.next(null);

    const headers = this.getAuthHeaders();
    if (!headers) {
      this.cargandoHistorial = false;
      this.cargandoSource.next(false);
      return;
    }

    this.http.get<RespuestaHistorial>(
      `${environment.apiUrl}/api/ws/historial`,
      { headers }
    ).subscribe({
      next: (res) => {
        if (res.success && Array.isArray(res.data)) {
          const notificaciones: Notificacion[] = res.data.map(n => {
            const tipo = n.tipo_referencia || n.tipo || 'GENERAL';
            return {
              id_notificacion: n.id_notificacion,
              tipo_alerta:     tipo,
              tipo_referencia: tipo,
              titulo:          n.titulo,
              cuerpo:          n.cuerpo || n.mensaje || '',
              leida:           Boolean(n.leido),
              leido:           Boolean(n.leido),
              fecha:           n.fecha_creacion ? new Date(n.fecha_creacion) : new Date(),
              nro_emergencia:  n.nro_emergencia,
              data:            { nro_emergencia: n.nro_emergencia },
            };
          });
          this.notificacionesSource.next(notificaciones);
        }
        this.cargandoHistorial = false;
        this.cargandoSource.next(false);
      },
      error: (err) => {
        console.error('Error cargando historial de notificaciones:', err);
        const msg = err?.error?.detail || 'No se pudieron cargar las notificaciones. Intenta nuevamente.';
        this.errorSource.next(msg);
        this.cargandoHistorial = false;
        this.cargandoSource.next(false);
      }
    });
  }

  // ----------------------------------------------------------------
  // MARCAR COMO LEÍDAS — sincronizado con el backend (HU142)
  // ----------------------------------------------------------------

  marcarComoLeidas() {
    const headers = this.getAuthHeaders();
    if (!headers) return;

    const estadoPrevio = this.notificacionesSource.getValue();
    const listaActualizada = estadoPrevio.map(n => ({ ...n, leida: true, leido: true }));
    this.notificacionesSource.next(listaActualizada);

    this.http.put(
      `${environment.apiUrl}/api/ws/leer`,
      { marcar_todo: true },
      { headers }
    ).subscribe({
      error: (err) => {
        console.error('Error al marcar todas como leídas en BD:', err);
        this.notificacionesSource.next(estadoPrevio);
        this.errorSource.next(err?.error?.detail || 'No se pudieron marcar todas las notificaciones como leídas.');
      }
    });
  }

  marcarUnaComoLeida(id_notificacion: number) {
    const headers = this.getAuthHeaders();
    if (!headers) return;

    const estadoPrevio = this.notificacionesSource.getValue();
    const listaActualizada = estadoPrevio.map(n =>
      n.id_notificacion === id_notificacion ? { ...n, leida: true, leido: true } : n
    );
    this.notificacionesSource.next(listaActualizada);

    this.http.put(
      `${environment.apiUrl}/api/ws/leer`,
      { id_notificacion },
      { headers }
    ).subscribe({
      error: (err) => {
        console.error(`Error al marcar notificación ${id_notificacion} como leída:`, err);
        this.notificacionesSource.next(estadoPrevio);
        this.errorSource.next(err?.error?.detail || 'No se pudo actualizar el estado de la notificación.');
      }
    });
  }

  // ----------------------------------------------------------------
  // CONFIGURACIÓN DE ALERTAS POR EVENTOS (HU141)
  // ----------------------------------------------------------------

  obtenerConfiguracionAlertas(
    idObra?: number | null,
    idEmpresa?: number | null
  ): Observable<RespuestaConfiguracionAlertas> {
    const headers = this.getAuthHeaders() ?? new HttpHeaders();
    let params = new HttpParams();
    if (idObra !== null && idObra !== undefined) {
      params = params.set('id_obra', String(idObra));
    }
    if (idEmpresa !== null && idEmpresa !== undefined) {
      params = params.set('id_empresa', String(idEmpresa));
    }
    return this.http.get<RespuestaConfiguracionAlertas>(
      `${environment.apiUrl}/api/ws/configuracion-alertas`,
      { headers, params }
    );
  }

  guardarConfiguracionAlertas(payload: {
    id_obra?: number | null;
    id_empresa?: number | null;
    configuraciones?: Array<{ tipo_evento: string; activo: boolean; roles_destino: string[] }>;
    restablecer_obra?: boolean;
  }): Observable<RespuestaConfiguracionAlertas> {
    const headers = this.getAuthHeaders() ?? new HttpHeaders();
    return this.http.put<RespuestaConfiguracionAlertas>(
      `${environment.apiUrl}/api/ws/configuracion-alertas`,
      payload,
      { headers }
    );
  }

  // ----------------------------------------------------------------
  // HELPERS
  // ----------------------------------------------------------------

  private getAuthHeaders(): HttpHeaders | null {
    const token = this.authService.obtenerToken();
    if (!token) return null;
    return new HttpHeaders({ Authorization: `Bearer ${token}` });
  }
}
