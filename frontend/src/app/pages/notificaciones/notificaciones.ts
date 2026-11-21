import { Component, OnInit, inject, ChangeDetectorRef, DestroyRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import {
  NotificacionesService,
  Notificacion,
  ConfiguracionAlertaEvento,
} from '../../services/notificaciones';
import { AuthService } from '../../services/auth';
import { ProyectosService, Proyecto } from '../../services/proyectos';

interface GrupoFecha {
  etiqueta: string;
  fechaClave: string;
  notificaciones: Notificacion[];
}

type FiltroLectura = 'TODAS' | 'NO_LEIDAS' | 'LEIDAS';
type TabNotificaciones = 'BANDEJA' | 'CONFIGURACION';

@Component({
  selector: 'app-notificaciones',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './notificaciones.html',
})
export class NotificacionesComponent implements OnInit {

  private notificacionesService = inject(NotificacionesService);
  private authService           = inject(AuthService);
  private proyectosService      = inject(ProyectosService);
  private cdr                   = inject(ChangeDetectorRef);
  private destroyRef            = inject(DestroyRef);

  // ── Navegación entre tabs ──
  tabActiva: TabNotificaciones = 'BANDEJA';
  puedeConfigurarAlertas       = false;

  // ── Estado de bandeja (HU142) ──
  cargando       = true;
  marcandoTodas  = false;
  errorHistorial: string | null = null;
  filtroLectura: FiltroLectura  = 'TODAS';

  todasNotificaciones: Notificacion[] = [];
  grupos: GrupoFecha[]                = [];
  totalNoLeidas                       = 0;

  // ── Estado de configuración de alertas (HU141) ──
  obrasDisponibles: Proyecto[]                     = [];
  obraSeleccionadaId: number | null                = null;
  configuraciones: ConfiguracionAlertaEvento[]     = [];
  rolesDisponibles: string[]                       = [];
  migracionPendiente                               = false;
  cargandoConfig                                   = false;
  guardandoConfig                                  = false;
  errorConfig: string | null                       = null;
  mensajeExitoConfig: string | null                = null;

  ngOnInit() {
    const rol = this.authService.obtenerRolNormalizado();
    this.puedeConfigurarAlertas =
      rol === 'ADMINISTRADOR' ||
      rol === 'ADMINISTRADOR_EMPRESA' ||
      rol === 'JEFE_DE_OBRA';

    this.notificacionesService.cargando$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((estado) => {
        this.cargando = estado;
        this.cdr.detectChanges();
      });

    this.notificacionesService.error$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((err) => {
        this.errorHistorial = err;
        this.cdr.detectChanges();
      });

    this.notificacionesService.notificaciones$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((notis) => {
        this.todasNotificaciones = notis;
        this.totalNoLeidas = notis.filter(n => !n.leida).length;
        this.aplicarFiltro();
        this.cdr.detectChanges();
      });

    this.notificacionesService.cargarHistorial();
  }

  // ─────────────────────────────────────────────
  // TABS Y FILTROS
  // ─────────────────────────────────────────────

  cambiarTab(tab: TabNotificaciones) {
    if (tab === 'CONFIGURACION' && !this.puedeConfigurarAlertas) return;
    this.tabActiva = tab;
    if (tab === 'CONFIGURACION') {
      this.cargarObrasYConfiguracion();
    }
  }

  cambiarFiltro(filtro: FiltroLectura) {
    this.filtroLectura = filtro;
    this.aplicarFiltro();
  }

  recargarHistorial() {
    this.errorHistorial = null;
    this.notificacionesService.cargarHistorial();
  }

  private aplicarFiltro() {
    let filtradas = this.todasNotificaciones;
    if (this.filtroLectura === 'NO_LEIDAS') {
      filtradas = filtradas.filter(n => !n.leida);
    } else if (this.filtroLectura === 'LEIDAS') {
      filtradas = filtradas.filter(n => n.leida);
    }
    this.grupos = this.agruparPorFecha(filtradas);
  }

  // ─────────────────────────────────────────────
  // ACCIONES BANDEJA (HU142)
  // ─────────────────────────────────────────────

  leerNotificacion(noti: Notificacion) {
    if (noti.leida) return;
    if (noti.id_notificacion) {
      this.notificacionesService.marcarUnaComoLeida(noti.id_notificacion);
    }
  }

  marcarTodas() {
    if (this.marcandoTodas) return;
    this.marcandoTodas = true;
    this.notificacionesService.marcarComoLeidas();
    setTimeout(() => {
      this.marcandoTodas = false;
      this.cdr.detectChanges();
    }, 500);
  }

  // ─────────────────────────────────────────────
  // CONFIGURACIÓN DE ALERTAS (HU141)
  // ─────────────────────────────────────────────

  private resolverIdEmpresaParaConsulta(): number | null {
    const rol = this.authService.obtenerRolNormalizado();
    if (rol === 'ADMINISTRADOR') {
      return this.authService.obtenerEmpresaActiva()?.id_empresa ?? null;
    }
    return null;
  }

  cargarObrasYConfiguracion() {
    if (this.obrasDisponibles.length === 0) {
      this.proyectosService.listarProyectos().subscribe({
        next: (res) => {
          const lista = Array.isArray(res?.data) ? res.data : [];
          const empresaActiva = this.resolverIdEmpresaParaConsulta();
          this.obrasDisponibles = empresaActiva
            ? lista.filter(p => Number(p.id_empresa) === Number(empresaActiva))
            : lista;
          this.cdr.detectChanges();
        },
        error: () => {
          this.obrasDisponibles = [];
        },
      });
    }
    this.cargarConfiguracion();
  }

  onCambioObraSeleccionada() {
    this.mensajeExitoConfig = null;
    this.errorConfig = null;
    this.cargarConfiguracion();
  }

  cargarConfiguracion() {
    this.cargandoConfig = true;
    this.errorConfig = null;
    this.mensajeExitoConfig = null;

    const idEmpresa = this.resolverIdEmpresaParaConsulta();
    this.notificacionesService
      .obtenerConfiguracionAlertas(this.obraSeleccionadaId, idEmpresa)
      .subscribe({
        next: (res) => {
          this.configuraciones = (res.data || []).map(item => ({
            ...item,
            roles_destino: [...(item.roles_destino || [])],
          }));
          this.rolesDisponibles = res.roles_disponibles || [];
          this.migracionPendiente = Boolean(res.migracion_pendiente);
          this.cargandoConfig = false;
          this.cdr.detectChanges();
        },
        error: (err) => {
          this.errorConfig = err?.error?.detail || 'No se pudo cargar la configuración de alertas.';
          this.cargandoConfig = false;
          this.cdr.detectChanges();
        },
      });
  }

  toggleRolEvento(item: ConfiguracionAlertaEvento, rol: string) {
    if (this.migracionPendiente || this.guardandoConfig) return;
    const idx = item.roles_destino.indexOf(rol);
    if (idx >= 0) {
      item.roles_destino = item.roles_destino.filter(r => r !== rol);
    } else {
      item.roles_destino = [...item.roles_destino, rol];
    }
  }

  tieneRolEvento(item: ConfiguracionAlertaEvento, rol: string): boolean {
    return item.roles_destino.includes(rol);
  }

  guardarConfiguracion() {
    if (this.guardandoConfig || this.migracionPendiente) return;
    this.guardandoConfig = true;
    this.errorConfig = null;
    this.mensajeExitoConfig = null;

    const payload = {
      id_obra: this.obraSeleccionadaId,
      id_empresa: this.resolverIdEmpresaParaConsulta(),
      configuraciones: this.configuraciones.map(c => ({
        tipo_evento: c.tipo_evento,
        activo: Boolean(c.activo),
        roles_destino: [...c.roles_destino],
      })),
    };

    this.notificacionesService.guardarConfiguracionAlertas(payload).subscribe({
      next: (res) => {
        this.configuraciones = (res.data || []).map(item => ({
          ...item,
          roles_destino: [...(item.roles_destino || [])],
        }));
        this.migracionPendiente = Boolean(res.migracion_pendiente);
        this.mensajeExitoConfig = res.message || 'Configuración de alertas guardada exitosamente.';
        this.guardandoConfig = false;
        this.cdr.detectChanges();
      },
      error: (err) => {
        this.errorConfig = err?.error?.detail || 'No se pudo guardar la configuración de alertas.';
        this.guardandoConfig = false;
        this.cdr.detectChanges();
      },
    });
  }

  restablecerConfiguracionObra() {
    if (!this.obraSeleccionadaId || this.guardandoConfig || this.migracionPendiente) return;
    this.guardandoConfig = true;
    this.errorConfig = null;
    this.mensajeExitoConfig = null;

    this.notificacionesService
      .guardarConfiguracionAlertas({
        id_obra: this.obraSeleccionadaId,
        id_empresa: this.resolverIdEmpresaParaConsulta(),
        restablecer_obra: true,
      })
      .subscribe({
        next: (res) => {
          this.configuraciones = (res.data || []).map(item => ({
            ...item,
            roles_destino: [...(item.roles_destino || [])],
          }));
          this.mensajeExitoConfig = res.message || 'Reglas de la obra restablecidas a los valores de la empresa.';
          this.guardandoConfig = false;
          this.cdr.detectChanges();
        },
        error: (err) => {
          this.errorConfig = err?.error?.detail || 'No se pudo restablecer la configuración de la obra.';
          this.guardandoConfig = false;
          this.cdr.detectChanges();
        },
      });
  }

  formatearRol(rol: string): string {
    const mapa: Record<string, string> = {
      'ADMINISTRADOR':         'Admin global',
      'ADMINISTRADOR_EMPRESA': 'Admin empresa',
      'JEFE DE OBRA':          'Jefe de obra',
      'SUPERVISOR_OBRA':       'Supervisor',
      'CLIENTE':               'Cliente',
      'ELECTRICO':             'Eléctrico',
      'PLOMERO':               'Plomero',
      'MAESTROALBAÑIL':        'Maestro albañil',
      'ALBAÑIL':               'Albañil',
    };
    return mapa[rol] ?? rol;
  }

  // ─────────────────────────────────────────────
  // AGRUPACIÓN POR FECHA
  // ─────────────────────────────────────────────

  private agruparPorFecha(notis: Notificacion[]): GrupoFecha[] {
    const mapa = new Map<string, Notificacion[]>();

    for (const noti of notis) {
      const clave = this.fechaClave(noti.fecha);
      if (!mapa.has(clave)) mapa.set(clave, []);
      mapa.get(clave)!.push(noti);
    }

    return Array.from(mapa.entries()).map(([clave, lista]) => ({
      etiqueta:       this.etiquetaFecha(new Date(clave + 'T00:00:00')),
      fechaClave:     clave,
      notificaciones: lista,
    }));
  }

  private fechaClave(fecha: Date): string {
    const d = new Date(fecha);
    if (isNaN(d.getTime())) {
      const hoy = new Date();
      return `${hoy.getFullYear()}-${String(hoy.getMonth() + 1).padStart(2, '0')}-${String(hoy.getDate()).padStart(2, '0')}`;
    }
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
  }

  private etiquetaFecha(fecha: Date): string {
    const hoy    = new Date(); hoy.setHours(0, 0, 0, 0);
    const ayer   = new Date(hoy); ayer.setDate(hoy.getDate() - 1);
    const semana = new Date(hoy); semana.setDate(hoy.getDate() - 6);

    const f = new Date(fecha); f.setHours(0, 0, 0, 0);

    if (f.getTime() === hoy.getTime())  return 'Hoy';
    if (f.getTime() === ayer.getTime()) return 'Ayer';
    if (f >= semana) {
      return fecha.toLocaleDateString('es-BO', { weekday: 'short', day: 'numeric', month: 'short' });
    }
    return fecha.toLocaleDateString('es-BO', { day: 'numeric', month: 'long', year: 'numeric' });
  }

  // ─────────────────────────────────────────────
  // HELPERS DE ESTILO PARA TODOS LOS TIPOS REALES
  // ─────────────────────────────────────────────

  getIconoClase(tipo: string): string {
    const t = (tipo || '').toUpperCase();
    const clases: Record<string, string> = {
      'INCIDENCIA':       'bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 border-red-100 dark:border-red-800/30',
      'ALERTA_OBRA':      'bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 border-red-100 dark:border-red-800/30',
      'NUEVA_EMERGENCIA': 'bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 border-red-100 dark:border-red-800/30',
      'EMERGENCIA':       'bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 border-red-100 dark:border-red-800/30',
      'AVANCE_OBRA':      'bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400 border-green-100 dark:border-green-800/30',
      'ORDEN_TRABAJO':    'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 border-blue-100 dark:border-blue-800/30',
      'CONSULTA_TECNICA': 'bg-indigo-50 dark:bg-indigo-900/20 text-indigo-600 dark:text-indigo-400 border-indigo-100 dark:border-indigo-800/30',
      'ASIGNACION_RFI':   'bg-indigo-50 dark:bg-indigo-900/20 text-indigo-600 dark:text-indigo-400 border-indigo-100 dark:border-indigo-800/30',
      'OBRA_ESTADO':      'bg-amber-50 dark:bg-amber-900/20 text-amber-600 dark:text-amber-400 border-amber-100 dark:border-amber-800/30',
      'ORDEN_CAMBIO':     'bg-amber-50 dark:bg-amber-900/20 text-amber-600 dark:text-amber-400 border-amber-100 dark:border-amber-800/30',
      'CRONOGRAMA':       'bg-cyan-50 dark:bg-cyan-900/20 text-cyan-600 dark:text-cyan-400 border-cyan-100 dark:border-cyan-800/30',
      'CRM_PROSPECTO':    'bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-400 border-emerald-100 dark:border-emerald-800/30',
      'NUEVA_OFERTA':     'bg-amber-50 dark:bg-amber-900/20 text-amber-600 dark:text-amber-400 border-amber-100 dark:border-amber-800/30',
      'RESPUESTA_OFERTA': 'bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400 border-green-100 dark:border-green-800/30',
      'ALERTA':           'bg-amber-50 dark:bg-amber-900/20 text-amber-600 dark:text-amber-400 border-amber-100 dark:border-amber-800/30',
      'INFO':             'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 border-blue-100 dark:border-blue-800/30',
      'EXITO':            'bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400 border-green-100 dark:border-green-800/30',
    };
    return clases[t] ?? clases['INFO'];
  }

  getIconoPath(tipo: string): string {
    const t = (tipo || '').toUpperCase();
    const iconos: Record<string, string> = {
      'INCIDENCIA':       'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z',
      'ALERTA_OBRA':      'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z',
      'AVANCE_OBRA':      'M13 7h8m0 0v8m0-8l-8 8-4-4-6 6',
      'ORDEN_TRABAJO':    'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4',
      'CONSULTA_TECNICA': 'M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z',
      'ASIGNACION_RFI':   'M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z',
      'OBRA_ESTADO':      'M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4',
      'ORDEN_CAMBIO':     'M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
      'CRONOGRAMA':       'M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z',
      'CRM_PROSPECTO':    'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z',
      'NUEVA_EMERGENCIA': 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z',
      'NUEVA_OFERTA':     'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4',
      'RESPUESTA_OFERTA': 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
      'ALERTA':           'M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
      'INFO':             'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
      'EXITO':            'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
    };
    return iconos[t] ?? iconos['INFO'];
  }

  getBarraClase(tipo: string): string {
    const t = (tipo || '').toUpperCase();
    const barras: Record<string, string> = {
      'INCIDENCIA':       'bg-red-500',
      'ALERTA_OBRA':      'bg-red-500',
      'NUEVA_EMERGENCIA': 'bg-red-500',
      'EMERGENCIA':       'bg-red-500',
      'AVANCE_OBRA':      'bg-green-500',
      'ORDEN_TRABAJO':    'bg-blue-500',
      'CONSULTA_TECNICA': 'bg-indigo-500',
      'ASIGNACION_RFI':   'bg-indigo-500',
      'OBRA_ESTADO':      'bg-amber-500',
      'ORDEN_CAMBIO':     'bg-amber-500',
      'CRONOGRAMA':       'bg-cyan-500',
      'CRM_PROSPECTO':    'bg-emerald-500',
      'ALERTA':           'bg-amber-500',
      'EXITO':            'bg-green-500',
    };
    return barras[t] ?? 'bg-blue-500';
  }

  getBadgeClase(tipo: string): string {
    const t = (tipo || '').toUpperCase();
    const badges: Record<string, string> = {
      'INCIDENCIA':       'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400',
      'ALERTA_OBRA':      'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400',
      'AVANCE_OBRA':      'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400',
      'ORDEN_TRABAJO':    'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400',
      'CONSULTA_TECNICA': 'bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-400',
      'ASIGNACION_RFI':   'bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-400',
      'OBRA_ESTADO':      'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400',
      'ORDEN_CAMBIO':     'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400',
      'CRONOGRAMA':       'bg-cyan-100 dark:bg-cyan-900/30 text-cyan-700 dark:text-cyan-400',
      'CRM_PROSPECTO':    'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400',
      'NUEVA_EMERGENCIA': 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400',
      'NUEVA_OFERTA':     'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400',
      'RESPUESTA_OFERTA': 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400',
      'ALERTA':           'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400',
      'INFO':             'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400',
      'EXITO':            'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400',
    };
    return badges[t] ?? badges['INFO'];
  }

  getTipoLabel(tipo: string): string {
    const t = (tipo || '').toUpperCase();
    const labels: Record<string, string> = {
      'INCIDENCIA':       'Incidencia',
      'ALERTA_OBRA':      'Alerta obra',
      'AVANCE_OBRA':      'Avance',
      'ORDEN_TRABAJO':    'Orden de trabajo',
      'CONSULTA_TECNICA': 'Consulta técnica',
      'ASIGNACION_RFI':   'Asignación RFI',
      'OBRA_ESTADO':      'Estado de obra',
      'ORDEN_CAMBIO':     'Orden de cambio',
      'CRONOGRAMA':       'Cronograma',
      'CRM_PROSPECTO':    'Prospecto CRM',
      'OBRA':             'Obra',
      'NUEVA_EMERGENCIA': 'Emergencia',
      'NUEVA_OFERTA':     'Oferta',
      'RESPUESTA_OFERTA': 'Respuesta',
      'ALERTA':           'Alerta',
      'INFO':             'Info',
      'EXITO':            'Éxito',
    };
    return labels[t] ?? tipo;
  }
}
