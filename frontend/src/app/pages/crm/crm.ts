import { LecturasVigentes } from '../../services/lecturas';
import { ContextoOperativo } from '../../services/contexto-operativo';
import { CommonModule } from '@angular/common';
import { ChangeDetectorRef, Component, DestroyRef, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Subject, debounceTime, distinctUntilChanged, finalize } from 'rxjs';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { AuthService } from '../../services/auth';
import { StatusBadgeComponent } from '../../components/ui/status-badge';
import {
  CrmService,
  ClienteCRM,
  InteraccionCRM,
  UnidadAsociadaCRM,
  MetricasCRM,
  UnidadDisponible,
  TipoCliente,
  TipoInteraccion,
  EstadoAsociacionUnidad,
  AsesorComercial,
  SolicitudConstructoraCu30
} from '../../services/crm.service';
import { AsistenteService } from '../../services/asistente.service';

@Component({
  selector: 'app-crm',
  standalone: true,
  imports: [CommonModule, FormsModule, StatusBadgeComponent],
  templateUrl: './crm.html',
  styleUrl: './crm.css'
})
export class CrmComponent implements OnInit {
  private contexto = inject(ContextoOperativo);
  private crmService = inject(CrmService);
  readonly asistente = inject(AsistenteService);
  private auth = inject(AuthService);
  private cdr = inject(ChangeDetectorRef);
  private destroyRef = inject(DestroyRef);
  private reads = new LecturasVigentes(this.destroyRef);
  private busqueda$ = new Subject<string>();

  // Pestaña activa
  pestanaActiva: 'prospectos' | 'clientes' | 'solicitudes' = 'prospectos';

  // HU117: Solicitudes de Clientes (Constructora)
  solicitudesConstructora: SolicitudConstructoraCu30[] = [];
  cargandoSolicitudes = false;
  filtroEstadoSolicitud: string = 'TODAS';
  busquedaSolicitud: string = '';
  mostrarModalResponder = false;
  solicitudSeleccionada: SolicitudConstructoraCu30 | null = null;
  guardandoRespuesta = false;
  errorRespuesta = '';
  formRespuesta = {
    estado: 'EN_PROCESO',
    respuesta: '',
    id_fotografia_evidencia: null as number | null
  };

  // Métricas
  metricas: MetricasCRM | null = null;
  cargandoMetricas = false;

  // Asesores comerciales de la empresa activa
  asesores: AsesorComercial[] = [];
  cargandoAsesores = false;
  filtroAsesor: number | null = null;

  // Listado de clientes / prospectos
  clientes: ClienteCRM[] = [];
  cargandoLista = false;
  q = '';
  filtroEstado = '';
  filtroTipo: TipoCliente = 'PROSPECTO';
  pagina = 1;
  limite = 15;
  total = 0;
  totalPaginas = 1;

  // Etapas del pipeline comercial para visualización y avance
  etapasPipeline = [
    { clave: 'NUEVO', label: 'Nuevo', icono: '🎯' },
    { clave: 'CONTACTADO', label: 'Contactado', icono: '📞' },
    { clave: 'INTERESADO', label: 'Interesado', icono: '💡' },
    { clave: 'NEGOCIACION', label: 'Negociación', icono: '💼' },
    { clave: 'RESERVADO', label: 'Reservado', icono: '📑' },
    { clave: 'VENDIDO', label: 'Vendido', icono: '🤝' },
  ];

  // Modal para avanzar de etapa con notas
  mostrarModalCambiarEtapa = false;
  clienteParaCambioEtapa: ClienteCRM | null = null;
  etapaSeleccionada = '';
  notaCambioEtapa = '';
  guardandoCambioEtapa = false;

  // Detalle e Historial (HU81)
  clienteSeleccionado: ClienteCRM | null = null;
  interacciones: InteraccionCRM[] = [];
  unidadesAsociadas: UnidadAsociadaCRM[] = [];
  cargandoDetalle = false;
  mostrarModalDetalle = false;

  // Formulario de Cliente / Prospecto
  mostrarModalFormulario = false;
  guardandoFormulario = false;
  modoEdicion = false;
  formCliente: any = {
    id_cliente: null,
    nombre_completo: '',
    ci: '',
    telefono: '',
    telefono_ref: '',
    email: '',
    direccion: '',
    ubicacion: '',
    tipo_cliente: 'PROSPECTO',
    estado: 'NUEVO',
    origen: 'DIRECTO',
    presupuesto_estimado: null,
    notas: '',
    id_usuario_asignado: null
  };

  // Formulario de Interacción (HU84)
  mostrarModalInteraccion = false;
  guardandoInteraccion = false;
  formInteraccion: {
    tipo: TipoInteraccion;
    asunto: string;
    detalle: string;
    fecha_interaccion: string;
    fecha_proximo_contacto: string;
  } = {
    tipo: 'LLAMADA',
    asunto: '',
    detalle: '',
    fecha_interaccion: '',
    fecha_proximo_contacto: ''
  };

  // Formulario de Asociación de Unidad (HU85)
  mostrarModalAsociarUnidad = false;
  guardandoAsociacion = false;
  unidadesDisponibles: UnidadDisponible[] = [];
  cargandoUnidadesDisp = false;
  formAsociarUnidad: {
    id_unidad: number | null;
    estado_asociacion: EstadoAsociacionUnidad;
    monto_pactado: number | null;
    observaciones: string;
  } = {
    id_unidad: null,
    estado_asociacion: 'INTERESADO',
    monto_pactado: null,
    observaciones: ''
  };

  // Formulario de Comunicación Directa al Cliente (HU116)
  mostrarModalComunicacion = false;
  guardandoComunicacion = false;
  clienteParaComunicacion: ClienteCRM | null = null;
  unidadesClienteParaComunicacion: UnidadAsociadaCRM[] = [];
  cargandoUnidadesParaComunicacion = false;
  formComunicacion: {
    id_cliente: number | null;
    id_obra: number | null;
    id_unidad: number | null;
    titulo: string;
    cuerpo: string;
    tipo_referencia: string;
  } = {
    id_cliente: null,
    id_obra: null,
    id_unidad: null,
    titulo: '',
    cuerpo: '',
    tipo_referencia: 'COMUNICACION'
  };

  get conteoSolicitudesPendientes(): number {
    return this.solicitudesConstructora.filter(s => (s.estado || '').toUpperCase() === 'PENDIENTE').length;
  }

  get solicitudesFiltradas(): SolicitudConstructoraCu30[] {
    return this.solicitudesConstructora.filter(s => {
      const e = (s.estado || '').toUpperCase();
      const coincideEstado = !this.filtroEstadoSolicitud || this.filtroEstadoSolicitud === 'TODAS'
        ? true
        : e === this.filtroEstadoSolicitud.toUpperCase();

      const q = this.busquedaSolicitud.trim().toLowerCase();
      if (!q) return coincideEstado;

      const searchable = [
        s.nombre_cliente || '',
        s.codigo_unidad || '',
        s.nombre_obra || '',
        s.titulo || s.asunto || '',
        s.descripcion || '',
        s.estado || ''
      ].join(' ').toLowerCase();

      return coincideEstado && searchable.includes(q);
    });
  }

  // Mensajes de estado
  mensajeExito = '';
  mensajeError = '';

  ngOnInit(): void {
    this.contexto.proteger(() => this.mostrarModalFormulario || this.mostrarModalInteraccion || this.mostrarModalCambiarEtapa || this.mostrarModalAsociarUnidad || this.mostrarModalComunicacion || this.mostrarModalResponder, this.destroyRef);
    this.contexto.protegerEscritura(() => this.guardandoFormulario || this.guardandoInteraccion || this.guardandoCambioEtapa || this.guardandoAsociacion || this.guardandoComunicacion || this.guardandoRespuesta, this.destroyRef);
    this.contexto.empresa$.pipe(takeUntilDestroyed(this.destroyRef)).subscribe(() => {
      this.mostrarModalFormulario = false; this.mostrarModalDetalle = false; this.mostrarModalInteraccion = false; this.mostrarModalCambiarEtapa = false; this.mostrarModalAsociarUnidad = false; this.mostrarModalComunicacion = false; this.mostrarModalResponder = false; this.solicitudSeleccionada = null; this.clienteParaComunicacion = null; this.clienteSeleccionado = null; this.unidadesDisponibles = [];
      this.reads.cancelar(); this.clientes = []; this.pagina = 1; this.filtroAsesor = null;
      this.cargarMetricas(); this.cargarAsesores(); this.cargarLista(); this.cargarSolicitudesConstructora();
    });

    // Suscripción reactiva para buscador con debounce
    this.busqueda$.pipe(
      debounceTime(350),
      distinctUntilChanged(),
      takeUntilDestroyed(this.destroyRef)
    ).subscribe(() => {
      this.pagina = 1;
      this.cargarLista();
    });


  }

  // ── Cargar Asesores Comerciales de la Empresa ─────────────────────────────
  cargarAsesores() {
    this.cargandoAsesores = true;
    this.crmService.listarAsesores(this.auth.obtenerIdEmpresaActiva() || undefined).pipe(this.reads.reemplazar('asesores')).subscribe({
      next: (res) => {
        if (res && res.success) {
          this.asesores = res.data || [];
        }
        this.cargandoAsesores = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.cargandoAsesores = false;
        this.cdr.detectChanges();
      }
    });
  }

  // ── Navegación entre pestañas ─────────────────────────────────────────────
  cambiarPestana(p: 'prospectos' | 'clientes' | 'solicitudes' | 'asistente_ia') {
    if (p === 'asistente_ia') { this.asistente.open(); return; }
    this.pestanaActiva = p;
    this.limpiarMensajes();
    if (p === 'prospectos') {
      this.filtroTipo = 'PROSPECTO';
      this.filtroEstado = '';
      this.pagina = 1;
      this.cargarLista();
    } else if (p === 'clientes') {
      this.filtroTipo = 'CLIENTE';
      this.filtroEstado = '';
      this.pagina = 1;
      this.cargarLista();
    } else if (p === 'solicitudes') {
      this.cargarSolicitudesConstructora();
    }
  }

  // ── HU117: Gestión de Solicitudes de Clientes ─────────────────────────────
  cargarSolicitudesConstructora(): void {
    this.cargandoSolicitudes = true;
    this.crmService.listarSolicitudesConstructora()
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => {
          this.cargandoSolicitudes = false;
          this.cdr.markForCheck();
        })
      )
      .subscribe({
        next: res => {
          this.solicitudesConstructora = (res && res.success) ? (res.data || []) : [];
          this.cdr.detectChanges();
        },
        error: err => {
          console.error('Error al cargar solicitudes de constructora:', err);
          this.solicitudesConstructora = [];
          this.cdr.detectChanges();
        }
      });
  }

  abrirModalResponder(sol: SolicitudConstructoraCu30): void {
    this.solicitudSeleccionada = sol;
    this.errorRespuesta = '';
    const actual = (sol.estado || '').toUpperCase();
    let estadoSugerido = 'EN_PROCESO';
    if (actual === 'PENDIENTE') {
      estadoSugerido = 'EN_PROCESO';
    } else if (actual === 'EN_PROCESO') {
      estadoSugerido = 'ATENDIDA';
    } else {
      estadoSugerido = actual;
    }

    this.formRespuesta = {
      estado: estadoSugerido,
      respuesta: sol.respuesta || '',
      id_fotografia_evidencia: sol.id_fotografia_evidencia || null
    };
    this.mostrarModalResponder = true;
  }

  cerrarModalResponder(): void {
    this.mostrarModalResponder = false;
    this.solicitudSeleccionada = null;
    this.errorRespuesta = '';
    this.guardandoRespuesta = false;
  }

  obtenerEstadosDisponibles(estadoActual: string): { valor: string; label: string }[] {
    const actual = (estadoActual || '').toUpperCase();
    if (actual === 'PENDIENTE') {
      return [
        { valor: 'EN_PROCESO', label: '🟡 EN PROCESO' },
        { valor: 'ATENDIDA', label: '🟢 ATENDIDA' },
        { valor: 'RECHAZADA', label: '🔴 RECHAZADA' }
      ];
    }
    if (actual === 'EN_PROCESO') {
      return [
        { valor: 'EN_PROCESO', label: '🟡 EN PROCESO' },
        { valor: 'ATENDIDA', label: '🟢 ATENDIDA' },
        { valor: 'RECHAZADA', label: '🔴 RECHAZADA' }
      ];
    }
    return [
      { valor: actual, label: actual === 'ATENDIDA' ? '🟢 ATENDIDA' : '🔴 RECHAZADA' },
      { valor: 'EN_PROCESO', label: '🟡 REABRIR (EN PROCESO)' }
    ];
  }

  guardarRespuestaSolicitud(): void {
    if (!this.solicitudSeleccionada) return;
    this.errorRespuesta = '';

    const estadoNuevo = (this.formRespuesta.estado || '').trim().toUpperCase();
    const textoRespuesta = (this.formRespuesta.respuesta || '').trim();

    if (estadoNuevo === 'ATENDIDA' && !textoRespuesta) {
      this.errorRespuesta = 'Debe ingresar la respuesta oficial de la constructora para dar por ATENDIDA la solicitud.';
      return;
    }

    if (estadoNuevo === 'RECHAZADA' && !textoRespuesta) {
      this.errorRespuesta = 'Debe ingresar el motivo o justificación para dar por RECHAZADA la solicitud.';
      return;
    }

    this.guardandoRespuesta = true;
    const payload = {
      estado: estadoNuevo,
      respuesta: textoRespuesta || undefined,
      id_fotografia_evidencia: this.formRespuesta.id_fotografia_evidencia || undefined
    };

    this.crmService.responderSolicitudConstructora(this.solicitudSeleccionada.id_solicitud, payload)
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => {
          this.guardandoRespuesta = false;
          this.cdr.markForCheck();
        })
      )
      .subscribe({
        next: () => {
          this.mostrarExito(`Solicitud #${this.solicitudSeleccionada?.id_solicitud} actualizada a estado ${estadoNuevo} correctamente.`);
          this.cerrarModalResponder();
          this.cargarSolicitudesConstructora();
        },
        error: err => {
          this.errorRespuesta = err?.error?.detail || 'No se pudo registrar la respuesta de la constructora.';
        }
      });
  }

  onSearch(event: Event) {
    const val = (event.target as HTMLInputElement).value;
    this.busqueda$.next(val);
  }

  cargarMetricas() {
    this.cargandoMetricas = true;
    this.crmService.obtenerMetricas(this.auth.obtenerIdEmpresaActiva() || undefined).pipe(this.reads.reemplazar('metricas')).subscribe({
      next: (res) => {
        if (res && res.success) {
          this.metricas = res.data;
        }
        this.cargandoMetricas = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.cargandoMetricas = false;
        this.cdr.detectChanges();
      }
    });
  }

  cargarLista() {
    this.cargandoLista = true;
    this.crmService.listarClientes({
      id_empresa: this.auth.obtenerIdEmpresaActiva() || undefined,
      tipo_cliente: this.filtroTipo,
      estado: this.filtroEstado || undefined,
      q: this.q.trim() || undefined,
      id_usuario_asignado: this.filtroAsesor || undefined,
      page: this.pagina,
      limit: this.limite
    }).pipe(this.reads.reemplazar('clientes')).subscribe({
      next: (res) => {
        if (res && res.success) {
          this.clientes = res.data || [];
          this.total = res.pagination.total;
          this.totalPaginas = res.pagination.total_pages;
        }
        this.cargandoLista = false;
        this.cdr.detectChanges();
      },
      error: (err) => {
        this.mostrarError(err.error?.detail || 'Error al cargar la lista de clientes/prospectos.');
        this.cargandoLista = false;
        this.cdr.detectChanges();
      }
    });
  }

  filtrarPorEstado(estado: string) {
    this.filtroEstado = estado;
    this.pagina = 1;
    this.cargarLista();
  }

  filtrarPorAsesor(idAsesor: any) {
    this.filtroAsesor = idAsesor ? Number(idAsesor) : null;
    this.pagina = 1;
    this.cargarLista();
  }

  // ── Detalle e Historial (HU81) ─────────────────────────────────────────────
  verDetalleCliente(c: ClienteCRM) {
    this.clienteSeleccionado = c;
    this.cargandoDetalle = true;
    this.mostrarModalDetalle = true;
    this.interacciones = [];
    this.unidadesAsociadas = [];

    this.crmService.obtenerDetalleHistorial(c.id_cliente, this.auth.obtenerIdEmpresaActiva() || undefined).pipe(this.reads.reemplazar('detalle')).subscribe({
      next: (res) => {
        if (res && res.success) {
          this.clienteSeleccionado = res.data.cliente;
          this.interacciones = res.data.interacciones || [];
          this.unidadesAsociadas = res.data.unidades_asociadas || [];
        }
        this.cargandoDetalle = false;
        this.cdr.detectChanges();
      },
      error: (err) => {
        this.mostrarError(err.error?.detail || 'Error al consultar historial del cliente.');
        this.cargandoDetalle = false;
        this.cdr.detectChanges();
      }
    });
  }

  cerrarModalDetalle() {
    this.mostrarModalDetalle = false;
    this.clienteSeleccionado = null;
  }

  // ── Formulario de Registro / Edición (HU80, HU82) ──────────────────────────
  abrirModalNuevo(tipo: TipoCliente) {
    this.modoEdicion = false;
    this.formCliente = {
      id_cliente: null,
      nombre_completo: '',
      ci: '',
      telefono: '',
      telefono_ref: '',
      email: '',
      direccion: '',
      ubicacion: '',
      tipo_cliente: tipo,
      estado: tipo === 'PROSPECTO' ? 'NUEVO' : 'ACTIVO',
      origen: 'DIRECTO',
      presupuesto_estimado: null,
      notas: '',
      id_usuario_asignado: null
    };
    this.limpiarMensajes();
    this.mostrarModalFormulario = true;
  }

  abrirModalEditar(c: ClienteCRM) {
    this.modoEdicion = true;
    this.formCliente = {
      id_cliente: c.id_cliente,
      nombre_completo: c.nombre_completo,
      ci: c.ci || '',
      telefono: c.telefono || '',
      telefono_ref: c.telefono_ref || '',
      email: c.email || '',
      direccion: c.direccion || '',
      ubicacion: c.ubicacion || '',
      tipo_cliente: c.tipo_cliente,
      estado: c.estado,
      origen: c.origen || 'DIRECTO',
      presupuesto_estimado: c.presupuesto_estimado,
      notas: c.notas || '',
      id_usuario_asignado: c.id_usuario_asignado || null
    };
    this.limpiarMensajes();
    this.mostrarModalFormulario = true;
  }

  guardarCliente() {
    if (!this.formCliente.nombre_completo || !this.formCliente.nombre_completo.trim()) {
      this.mostrarError('El nombre completo es obligatorio.');
      return;
    }

    this.guardandoFormulario = true;
    this.limpiarMensajes();

    if (this.modoEdicion && this.formCliente.id_cliente) {
      this.crmService.actualizarCliente(this.formCliente.id_cliente, this.formCliente, this.auth.obtenerIdEmpresaActiva() || undefined).subscribe({
        next: (res) => {
          this.mostrarExito(res.message || 'Datos actualizados exitosamente.');
          this.guardandoFormulario = false;
          this.mostrarModalFormulario = false;
          this.cargarLista();
          this.cargarMetricas();
          if (this.clienteSeleccionado && this.clienteSeleccionado.id_cliente === this.formCliente.id_cliente) {
            this.verDetalleCliente(this.clienteSeleccionado);
          }
        },
        error: (err) => {
          this.mostrarError(err.error?.detail || 'Error al actualizar el cliente.');
          this.guardandoFormulario = false;
          this.cdr.detectChanges();
        }
      });
    } else {
      this.crmService.registrarCliente(this.formCliente, this.auth.obtenerIdEmpresaActiva() || undefined).subscribe({
        next: (res) => {
          this.mostrarExito(res.message || 'Registrado exitosamente.');
          this.guardandoFormulario = false;
          this.mostrarModalFormulario = false;
          this.cargarLista();
          this.cargarMetricas();
        },
        error: (err) => {
          this.mostrarError(err.error?.detail || 'Error al registrar.');
          this.guardandoFormulario = false;
          this.cdr.detectChanges();
        }
      });
    }
  }

  // ── Avance del Pipeline y Gestión de Etapas (HU83) ─────────────────────────
  abrirModalCambiarEtapa(c: ClienteCRM, nuevaEtapa: string) {
    this.clienteParaCambioEtapa = c;
    this.etapaSeleccionada = nuevaEtapa;
    this.notaCambioEtapa = '';
    this.mostrarModalCambiarEtapa = true;
  }

  cerrarModalCambiarEtapa() {
    this.mostrarModalCambiarEtapa = false;
    this.clienteParaCambioEtapa = null;
    this.etapaSeleccionada = '';
    this.notaCambioEtapa = '';
  }

  confirmarCambioEtapa() {
    if (!this.clienteParaCambioEtapa || !this.etapaSeleccionada) return;

    this.guardandoCambioEtapa = true;
    this.crmService.clasificarProspecto(
      this.clienteParaCambioEtapa.id_cliente,
      this.etapaSeleccionada,
      this.notaCambioEtapa.trim() || undefined,
      this.auth.obtenerIdEmpresaActiva() || undefined
    ).subscribe({
      next: (res) => {
        this.mostrarExito(res.message || 'Etapa comercial actualizada con éxito.');
        this.guardandoCambioEtapa = false;
        this.mostrarModalCambiarEtapa = false;
        this.cargarLista();
        this.cargarMetricas();
        if (this.clienteSeleccionado && this.clienteSeleccionado.id_cliente === this.clienteParaCambioEtapa?.id_cliente) {
          this.verDetalleCliente(this.clienteSeleccionado);
        }
        this.clienteParaCambioEtapa = null;
      },
      error: (err) => {
        this.mostrarError(err.error?.detail || 'Error al actualizar etapa comercial.');
        this.guardandoCambioEtapa = false;
        this.cdr.detectChanges();
      }
    });
  }

  // ── Registrar Interacción (HU84) ──────────────────────────────────────────
  abrirModalInteraccion(c: ClienteCRM) {
    this.clienteSeleccionado = c;
    this.formInteraccion = {
      tipo: 'LLAMADA',
      asunto: '',
      detalle: '',
      fecha_interaccion: new Date().toISOString().split('T')[0],
      fecha_proximo_contacto: ''
    };
    this.limpiarMensajes();
    this.mostrarModalInteraccion = true;
  }

  guardarInteraccion() {
    if (!this.clienteSeleccionado) return;
    if (!this.formInteraccion.asunto.trim() || !this.formInteraccion.detalle.trim()) {
      this.mostrarError('El asunto y el detalle de la interacción son obligatorios.');
      return;
    }

    this.guardandoInteraccion = true;
    this.crmService.registrarInteraccion(this.clienteSeleccionado.id_cliente, {
      tipo: this.formInteraccion.tipo,
      asunto: this.formInteraccion.asunto.trim(),
      detalle: this.formInteraccion.detalle.trim(),
      fecha_interaccion: this.formInteraccion.fecha_interaccion || null,
      fecha_proximo_contacto: this.formInteraccion.fecha_proximo_contacto || null
    }, this.auth.obtenerIdEmpresaActiva() || undefined).subscribe({
      next: (res) => {
        this.mostrarExito(res.message || 'Interacción registrada exitosamente.');
        this.guardandoInteraccion = false;
        this.mostrarModalInteraccion = false;
        if (this.clienteSeleccionado) {
          this.verDetalleCliente(this.clienteSeleccionado);
        }
      },
      error: (err) => {
        this.mostrarError(err.error?.detail || 'Error al registrar interacción.');
        this.guardandoInteraccion = false;
        this.cdr.detectChanges();
      }
    });
  }

  // ── Asociar Unidad Inmobiliaria (HU85) ─────────────────────────────────────
  abrirModalAsociarUnidad(c: ClienteCRM) {
    this.clienteSeleccionado = c;
    this.formAsociarUnidad = {
      id_unidad: null,
      estado_asociacion: 'INTERESADO',
      monto_pactado: null,
      observaciones: ''
    };
    this.unidadesDisponibles = [];
    this.cargandoUnidadesDisp = true;
    this.limpiarMensajes();
    this.mostrarModalAsociarUnidad = true;

    this.crmService.listarUnidadesDisponibles(undefined, this.auth.obtenerIdEmpresaActiva() || undefined).pipe(this.reads.reemplazar('unidades')).subscribe({
      next: (res) => {
        if (res && res.success) {
          this.unidadesDisponibles = res.data || [];
        }
        this.cargandoUnidadesDisp = false;
        this.cdr.detectChanges();
      },
      error: (err) => {
        this.mostrarError(err.error?.detail || 'Error al cargar unidades disponibles.');
        this.cargandoUnidadesDisp = false;
        this.cdr.detectChanges();
      }
    });
  }

  guardarAsociacionUnidad() {
    if (!this.clienteSeleccionado) return;
    if (!this.formAsociarUnidad.id_unidad) {
      this.mostrarError('Debes seleccionar una unidad inmobiliaria.');
      return;
    }

    this.guardandoAsociacion = true;
    this.crmService.asociarUnidad(this.clienteSeleccionado.id_cliente, this.formAsociarUnidad, this.auth.obtenerIdEmpresaActiva() || undefined).subscribe({
      next: (res) => {
        this.mostrarExito(res.message || 'Unidad asociada exitosamente.');
        this.guardandoAsociacion = false;
        this.mostrarModalAsociarUnidad = false;
        this.cargarMetricas();
        if (this.clienteSeleccionado) {
          this.verDetalleCliente(this.clienteSeleccionado);
        }
      },
      error: (err) => {
        this.mostrarError(err.error?.detail || 'Error al asociar la unidad.');
        this.guardandoAsociacion = false;
        this.cdr.detectChanges();
      }
    });
  }

  actualizarEstadoAsociacion(asoc: UnidadAsociadaCRM, nuevoEstado: any) {
    this.crmService.cambiarEstadoAsociacion(asoc.id_cliente_unidad, nuevoEstado, undefined, this.auth.obtenerIdEmpresaActiva() || undefined).subscribe({
      next: (res) => {
        this.mostrarExito(res.message || `Estado de la unidad actualizado a ${nuevoEstado}.`);
        asoc.estado_asociacion = nuevoEstado as EstadoAsociacionUnidad;
        this.cargarMetricas();
        if (this.clienteSeleccionado) {
          this.verDetalleCliente(this.clienteSeleccionado);
        }
        this.cdr.detectChanges();
      },
      error: (err) => {
        this.mostrarError(err.error?.detail || 'Error al actualizar estado de la asociación.');
      }
    });
  }

  // ── Emisión de Comunicaciones Directas (HU116) ───────────────────────────
  abrirModalComunicacion(c: ClienteCRM, unidadPrevia?: UnidadAsociadaCRM) {
    this.clienteParaComunicacion = c;
    this.formComunicacion = {
      id_cliente: c.id_cliente,
      id_obra: unidadPrevia ? unidadPrevia.id_obra : null,
      id_unidad: unidadPrevia ? unidadPrevia.id_unidad : null,
      titulo: '',
      cuerpo: '',
      tipo_referencia: 'COMUNICACION'
    };
    this.limpiarMensajes();
    this.mostrarModalComunicacion = true;

    if (this.clienteSeleccionado && this.clienteSeleccionado.id_cliente === c.id_cliente && this.unidadesAsociadas.length > 0) {
      this.unidadesClienteParaComunicacion = this.unidadesAsociadas;
    } else {
      this.cargandoUnidadesParaComunicacion = true;
      this.crmService.obtenerDetalleHistorial(c.id_cliente, this.auth.obtenerIdEmpresaActiva() || undefined)
        .pipe(takeUntilDestroyed(this.destroyRef))
        .subscribe({
          next: (res) => {
            if (res && res.success) {
              this.unidadesClienteParaComunicacion = res.data.unidades_asociadas || [];
            }
            this.cargandoUnidadesParaComunicacion = false;
            this.cdr.detectChanges();
          },
          error: () => {
            this.unidadesClienteParaComunicacion = [];
            this.cargandoUnidadesParaComunicacion = false;
            this.cdr.detectChanges();
          }
        });
    }
  }

  alSeleccionarUnidadComunicacion(idUnidad: any) {
    if (!idUnidad) {
      this.formComunicacion.id_unidad = null;
      return;
    }
    const id = Number(idUnidad);
    this.formComunicacion.id_unidad = id;
    const u = this.unidadesClienteParaComunicacion.find(item => item.id_unidad === id);
    if (u && u.id_obra) {
      this.formComunicacion.id_obra = u.id_obra;
    }
  }

  cerrarModalComunicacion() {
    this.mostrarModalComunicacion = false;
    this.clienteParaComunicacion = null;
    this.unidadesClienteParaComunicacion = [];
    this.guardandoComunicacion = false;
    this.formComunicacion = {
      id_cliente: null,
      id_obra: null,
      id_unidad: null,
      titulo: '',
      cuerpo: '',
      tipo_referencia: 'COMUNICACION'
    };
  }

  enviarComunicacion() {
    if (!this.clienteParaComunicacion || !this.formComunicacion.id_cliente) return;
    if (!this.formComunicacion.titulo.trim()) {
      this.mostrarError('El título de la comunicación es obligatorio.');
      return;
    }
    if (!this.formComunicacion.cuerpo.trim()) {
      this.mostrarError('El mensaje de la comunicación es obligatorio.');
      return;
    }

    this.guardandoComunicacion = true;
    this.limpiarMensajes();

    const payload = {
      id_cliente: this.formComunicacion.id_cliente,
      id_obra: this.formComunicacion.id_obra ? Number(this.formComunicacion.id_obra) : null,
      id_unidad: this.formComunicacion.id_unidad ? Number(this.formComunicacion.id_unidad) : null,
      titulo: this.formComunicacion.titulo.trim(),
      cuerpo: this.formComunicacion.cuerpo.trim(),
      tipo_referencia: this.formComunicacion.tipo_referencia || 'COMUNICACION'
    };

    this.crmService.enviarComunicacionCliente(payload)
      .pipe(
        finalize(() => {
          this.guardandoComunicacion = false;
          this.cdr.detectChanges();
        })
      )
      .subscribe({
        next: (res) => {
          this.guardandoComunicacion = false;
          this.cerrarModalComunicacion();
          this.mostrarExito(res?.message || 'Comunicación enviada exitosamente al cliente.');
          this.cdr.detectChanges();
        },
        error: (err) => {
          this.guardandoComunicacion = false;
          this.mostrarError(err.error?.detail || 'Error al enviar comunicación al cliente.');
          this.cdr.detectChanges();
        }
      });
  }

  // ── Helpers UI y Pipeline ────────────────────────────────────────────────
  getIndiceEtapa(estado: string): number {
    const orden = ['NUEVO', 'CONTACTADO', 'INTERESADO', 'NEGOCIACION', 'RESERVADO', 'VENDIDO'];
    const norm = (estado === 'EN_NEGOCIACION' ? 'NEGOCIACION' : estado || '').toUpperCase();
    return orden.indexOf(norm);
  }

  getIconoInteraccion(tipo: string): string {
    switch (tipo) {
      case 'LLAMADA': return '📞';
      case 'MENSAJE': return '💬';
      case 'REUNION': return '👥';
      case 'VISITA': return '🏡';
      case 'CONSULTA': return '❓';
      case 'SEGUIMIENTO': return '🔄';
      case 'OBSERVACION': return '📝';
      case 'CORREO': return '✉️';
      case 'NOTA': return '📌';
      default: return '📋';
    }
  }

  cambiarPagina(nueva: number) {
    if (nueva < 1 || nueva > this.totalPaginas) return;
    this.pagina = nueva;
    this.cargarLista();
  }

  mostrarExito(msg: string) {
    this.mensajeExito = msg;
    this.mensajeError = '';
    setTimeout(() => { this.mensajeExito = ''; this.cdr.detectChanges(); }, 4500);
    this.cdr.detectChanges();
  }

  mostrarError(msg: string) {
    this.mensajeError = msg;
    this.mensajeExito = '';
    setTimeout(() => { this.mensajeError = ''; this.cdr.detectChanges(); }, 6000);
    this.cdr.detectChanges();
  }

  limpiarMensajes() {
    this.mensajeExito = '';
    this.mensajeError = '';
  }

  getBadgeEstadoClass(estado: string): string {
    const norm = (estado || '').toUpperCase();
    switch (norm) {
      case 'NUEVO':
        return 'bg-blue-100 dark:bg-blue-950/40 text-blue-700 dark:text-blue-300 border-blue-200 dark:border-blue-800';
      case 'CONTACTADO':
        return 'bg-purple-100 dark:bg-purple-950/40 text-purple-700 dark:text-purple-300 border-purple-200 dark:border-purple-800';
      case 'INTERESADO':
        return 'bg-amber-100 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300 border-amber-200 dark:border-amber-800';
      case 'NEGOCIACION':
      case 'EN_NEGOCIACION':
        return 'bg-orange-100 dark:bg-orange-950/40 text-orange-800 dark:text-orange-300 border-orange-200 dark:border-orange-800 font-bold';
      case 'RESERVADO':
        return 'bg-indigo-100 dark:bg-indigo-950/40 text-indigo-800 dark:text-indigo-300 border-indigo-200 dark:border-indigo-800 font-bold';
      case 'VENDIDO':
      case 'CONVERTIDO':
      case 'ACTIVO':
        return 'bg-emerald-100 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800 font-bold';
      case 'PERDIDO':
      case 'INACTIVO':
        return 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border-slate-200 dark:border-slate-700';
      default:
        return 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300';
    }
  }

  getBadgeAsocClass(estado: string): string {
    switch (estado) {
      case 'INTERESADO': return 'bg-amber-100 text-amber-800 border-amber-200';
      case 'RESERVADO': return 'bg-indigo-100 text-indigo-800 border-indigo-200 font-bold';
      case 'VENDIDO': return 'bg-emerald-100 text-emerald-800 border-emerald-200 font-bold';
      case 'ENTREGADO': return 'bg-teal-100 text-teal-800 border-teal-200';
      case 'CANCELADO': return 'bg-red-100 text-red-800 border-red-200';
      default: return 'bg-slate-100 text-slate-800';
    }
  }
}
