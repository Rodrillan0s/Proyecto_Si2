import { CommonModule } from '@angular/common';
import { ChangeDetectorRef, Component, DestroyRef, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Subject, debounceTime, distinctUntilChanged } from 'rxjs';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';

import { AuthService } from '../../services/auth';
import { ContextoOperativo } from '../../services/contexto-operativo';
import { ProyectosService, Proyecto } from '../../services/proyectos';
import { CrmService, ClienteCRM } from '../../services/crm.service';
import {
  ComercializacionService,
  UnidadComercial,
  ResumenComercial,
  FotografiaUnidad,
  HistorialComercialUnidad,
  DetalleUnidadComercial,
  DisponibilidadUnidad,
  EstadoComercial,
  MonedaComercial
} from '../../services/comercializacion.service';

@Component({
  selector: 'app-comercializacion',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './comercializacion.html',
  styleUrl: './comercializacion.css'
})
export class ComercializacionComponent implements OnInit {
  private comercializacionService = inject(ComercializacionService);
  private proyectosService = inject(ProyectosService);
  private crmService = inject(CrmService);
  readonly auth = inject(AuthService);
  readonly contexto = inject(ContextoOperativo);
  private cdr = inject(ChangeDetectorRef);
  private destroyRef = inject(DestroyRef);

  // KPIs y métricas resumen (HU145)
  resumen: ResumenComercial | null = null;
  cargandoResumen = false;

  // Catálogo de proyectos para filtrado
  obras: Proyecto[] = [];
  cargandoObras = false;

  // Listado de unidades comerciales (HU143, HU145)
  unidades: UnidadComercial[] = [];
  cargandoLista = false;
  pagina = 1;
  limite = 15;
  total = 0;
  totalPaginas = 1;

  // Filtros de búsqueda reactivos
  filtroObra: number | null = null;
  filtroEstadoComercial = '';
  filtroPublicado: '' | 'true' | 'false' = '';
  filtroTipoUnidad = '';
  filtroSoloDisponibles = false;
  busquedaTexto = '';
  precioMin: number | null = null;
  precioMax: number | null = null;
  private busqueda$ = new Subject<string>();

  // Notificaciones y alertas
  mensajeExito = '';
  mensajeError = '';

  // Unidad en foco para acciones y modales
  unidadSeleccionada: UnidadComercial | null = null;
  cargandoAccion = false;

  // MODAL 1: Edición y Publicación Comercial (HU143)
  mostrarModalEditar = false;
  formEdicion = {
    publicado_comercial: false,
    precio_venta: null as number | null,
    moneda_comercial: 'BOB' as MonedaComercial,
    descripcion_comercial: '',
    estado_comercial: 'DISPONIBLE' as EstadoComercial,
    observacion: ''
  };

  // MODAL 2: Galería de Fotografías (HU143)
  mostrarModalFotos = false;
  fotografias: FotografiaUnidad[] = [];
  cargandoFotos = false;
  subiendoFoto = false;
  archivoSeleccionado: File | null = null;
  esFotoPrincipal = false;
  ordenFoto = 1;
  errorFoto = '';

  // MODAL 3: Registrar Reserva (HU144)
  mostrarModalReserva = false;
  clientesCrm: ClienteCRM[] = [];
  cargandoClientes = false;
  busquedaCliente = '';
  clienteSeleccionado: ClienteCRM | null = null;
  formReserva = {
    id_cliente: null as number | null,
    monto_reserva: 0,
    monto_pactado: null as number | null,
    fecha_vencimiento_reserva: '',
    observaciones: ''
  };

  // MODAL 4: Cancelar / Liberar Reserva (HU145)
  mostrarModalCancelarReserva = false;
  motivoCancelacion = '';

  // MODAL 5: Confirmar Venta (HU145)
  mostrarModalConfirmarVenta = false;
  formVenta = {
    id_cliente: null as number | null,
    monto_pactado: null as number | null,
    observaciones: ''
  };

  // MODAL 6: Cambiar Estado Comercial Directo (HU145)
  mostrarModalEstado = false;
  nuevoEstadoComercial: EstadoComercial = 'DISPONIBLE';
  motivoCambioEstado = '';

  // MODAL 7: Historial Comercial (HU146)
  mostrarModalHistorial = false;
  historialEventos: HistorialComercialUnidad[] = [];
  cargandoHistorial = false;
  filtroEventoHistorial = '';

  ngOnInit(): void {
    // Escuchar búsqueda con debounce
    this.busqueda$.pipe(
      debounceTime(350),
      distinctUntilChanged(),
      takeUntilDestroyed(this.destroyRef)
    ).subscribe(valor => {
      this.busquedaTexto = valor;
      this.pagina = 1;
      this.cargarUnidades();
    });

    // Cargar dependencias iniciales
    this.cargarObras();
    this.cargarResumen();
    this.cargarUnidades();
  }

  onBuscarTexto(termino: string): void {
    this.busqueda$.next(termino);
  }

  limpiarAlertas(): void {
    this.mensajeExito = '';
    this.mensajeError = '';
  }

  mostrarExito(mensaje: string): void {
    this.mensajeExito = mensaje;
    this.mensajeError = '';
    setTimeout(() => {
      if (this.mensajeExito === mensaje) this.mensajeExito = '';
      this.cdr.markForCheck();
    }, 4500);
  }

  mostrarFallo(mensaje: string): void {
    this.mensajeError = mensaje;
    this.mensajeExito = '';
  }

  cargarObras(): void {
    this.cargandoObras = true;
    this.proyectosService.listarProyectos().pipe(
      takeUntilDestroyed(this.destroyRef)
    ).subscribe({
      next: (resp) => {
        this.obras = resp.data || [];
        this.cargandoObras = false;
        this.cdr.markForCheck();
      },
      error: () => {
        this.cargandoObras = false;
        this.cdr.markForCheck();
      }
    });
  }

  cargarResumen(): void {
    this.cargandoResumen = true;
    const idObra = this.filtroObra ? Number(this.filtroObra) : undefined;
    this.comercializacionService.obtenerResumen(idObra).pipe(
      takeUntilDestroyed(this.destroyRef)
    ).subscribe({
      next: (data) => {
        this.resumen = data;
        this.cargandoResumen = false;
        this.cdr.markForCheck();
      },
      error: (err) => {
        this.cargandoResumen = false;
        this.cdr.markForCheck();
      }
    });
  }

  cargarUnidades(limpiar: boolean = false): void {
    this.cargandoLista = true;
    if (limpiar) {
      this.limpiarAlertas();
    }

    const filtros: any = {
      page: this.pagina,
      limit: this.limite
    };

    if (this.filtroObra) filtros.id_obra = Number(this.filtroObra);
    if (this.filtroEstadoComercial) filtros.estado_comercial = this.filtroEstadoComercial;
    if (this.filtroPublicado !== '') filtros.publicado = this.filtroPublicado === 'true';
    if (this.filtroTipoUnidad) filtros.tipo_unidad = this.filtroTipoUnidad;
    if (this.filtroSoloDisponibles) filtros.solo_disponibles = true;
    if (this.busquedaTexto.trim()) filtros.q = this.busquedaTexto.trim();
    if (this.precioMin !== null && this.precioMin >= 0) filtros.precio_min = this.precioMin;
    if (this.precioMax !== null && this.precioMax >= 0) filtros.precio_max = this.precioMax;

    this.comercializacionService.listarUnidades(filtros).pipe(
      takeUntilDestroyed(this.destroyRef)
    ).subscribe({
      next: (resp) => {
        this.unidades = resp.data || [];
        this.total = resp.total || 0;
        this.totalPaginas = Math.ceil(this.total / this.limite) || 1;
        this.cargandoLista = false;
        this.cdr.markForCheck();
      },
      error: (err) => {
        this.mostrarFallo(err?.error?.detail || 'Error al cargar unidades comerciales.');
        this.cargandoLista = false;
        this.cdr.markForCheck();
      }
    });
  }

  cambiarFiltro(): void {
    this.pagina = 1;
    this.cargarResumen();
    this.cargarUnidades();
  }

  limpiarFiltros(): void {
    this.filtroObra = null;
    this.filtroEstadoComercial = '';
    this.filtroPublicado = '';
    this.filtroTipoUnidad = '';
    this.filtroSoloDisponibles = false;
    this.busquedaTexto = '';
    this.precioMin = null;
    this.precioMax = null;
    this.pagina = 1;
    this.cargarResumen();
    this.cargarUnidades();
  }

  irPagina(p: number): void {
    if (p >= 1 && p <= this.totalPaginas && p !== this.pagina) {
      this.pagina = p;
      this.cargarUnidades();
    }
  }

  // ─────────────────────────────────────────────────────────────────────────────
  // HU143: PUBLICACIÓN Y ACTUALIZACIÓN
  // ─────────────────────────────────────────────────────────────────────────────
  alternarPublicacion(u: UnidadComercial): void {
    const nuevoValor = !u.publicado_comercial;
    this.cargandoAccion = true;
    this.comercializacionService.cambiarPublicacion(u.id_unidad, nuevoValor).subscribe({
      next: () => {
        u.publicado_comercial = nuevoValor;
        this.mostrarExito(`Unidad ${u.codigo} ${nuevoValor ? 'publicada' : 'despublicada'} correctamente.`);
        this.cargandoAccion = false;
        this.cargarResumen();
        this.cdr.markForCheck();
      },
      error: (err) => {
        this.mostrarFallo(err?.error?.detail || 'No se pudo cambiar el estado de publicación.');
        this.cargandoAccion = false;
        this.cdr.markForCheck();
      }
    });
  }

  abrirModalEditar(u: UnidadComercial): void {
    this.unidadSeleccionada = u;
    this.formEdicion = {
      publicado_comercial: u.publicado_comercial,
      precio_venta: u.precio_venta ?? null,
      moneda_comercial: u.moneda_comercial || 'BOB',
      descripcion_comercial: u.descripcion_comercial || '',
      estado_comercial: u.estado_comercial,
      observacion: ''
    };
    this.mostrarModalEditar = true;
  }

  guardarEdicion(): void {
    if (!this.unidadSeleccionada) return;
    this.cargandoAccion = true;

    const payload: any = {
      publicado_comercial: this.formEdicion.publicado_comercial,
      precio_venta: this.formEdicion.precio_venta,
      moneda_comercial: this.formEdicion.moneda_comercial,
      descripcion_comercial: this.formEdicion.descripcion_comercial
    };

    if (this.formEdicion.observacion.trim()) {
      payload.observacion = this.formEdicion.observacion.trim();
    }

    this.comercializacionService.actualizarComercializacion(this.unidadSeleccionada.id_unidad, payload).subscribe({
      next: (actualizada) => {
        this.mostrarModalEditar = false;
        this.mostrarExito(`Datos comerciales de ${this.unidadSeleccionada?.codigo} actualizados.`);
        this.cargandoAccion = false;
        this.cargarResumen();
        this.cargarUnidades();
        this.cdr.markForCheck();
      },
      error: (err) => {
        this.mostrarFallo(err?.error?.detail || 'Error al actualizar información comercial.');
        this.cargandoAccion = false;
        this.cdr.markForCheck();
      }
    });
  }

  // ─────────────────────────────────────────────────────────────────────────────
  // HU143: GALERÍA DE FOTOGRAFÍAS
  // ─────────────────────────────────────────────────────────────────────────────
  abrirModalFotos(u: UnidadComercial): void {
    this.unidadSeleccionada = u;
    this.fotografias = [];
    this.archivoSeleccionado = null;
    this.esFotoPrincipal = false;
    this.ordenFoto = (u.total_fotos || 0) + 1;
    this.errorFoto = '';
    this.mostrarModalFotos = true;
    this.cargarFotosUnidad(u.id_unidad);
  }

  cargarFotosUnidad(idUnidad: number): void {
    this.cargandoFotos = true;
    this.comercializacionService.listarFotografias(idUnidad).subscribe({
      next: (resp) => {
        this.fotografias = resp.fotografias || [];
        this.cargandoFotos = false;
        if (this.unidadSeleccionada) {
          this.unidadSeleccionada.total_fotos = this.fotografias.length;
        }
        this.cdr.markForCheck();
      },
      error: (err) => {
        this.errorFoto = err?.error?.detail || 'Error al cargar galería fotográfica.';
        this.cargandoFotos = false;
        this.cdr.markForCheck();
      }
    });
  }

  onArchivoFotoSeleccionado(evento: any): void {
    const file = evento.target.files?.[0];
    this.errorFoto = '';
    if (!file) {
      this.archivoSeleccionado = null;
      return;
    }

    const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
    const validas = ['.jpg', '.jpeg', '.png', '.webp'];
    if (!validas.includes(ext)) {
      this.errorFoto = 'Formato no permitido. Solo imágenes JPG, PNG o WEBP.';
      this.archivoSeleccionado = null;
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      this.errorFoto = 'El archivo supera el tamaño máximo permitido de 10 MB.';
      this.archivoSeleccionado = null;
      return;
    }

    this.archivoSeleccionado = file;
  }

  subirFoto(): void {
    if (!this.unidadSeleccionada || !this.archivoSeleccionado) return;
    this.subiendoFoto = true;
    this.errorFoto = '';

    this.comercializacionService.subirFotografia(
      this.unidadSeleccionada.id_unidad,
      this.archivoSeleccionado,
      this.esFotoPrincipal,
      this.ordenFoto
    ).subscribe({
      next: () => {
        this.subiendoFoto = false;
        this.archivoSeleccionado = null;
        this.esFotoPrincipal = false;
        this.cargarFotosUnidad(this.unidadSeleccionada!.id_unidad);
        this.cargarUnidades();
        this.mostrarExito('Fotografía subida exitosamente.');
        this.cdr.markForCheck();
      },
      error: (err) => {
        this.subiendoFoto = false;
        this.errorFoto = err?.error?.detail || 'Error al subir la fotografía.';
        this.cdr.markForCheck();
      }
    });
  }

  marcarPrincipal(foto: FotografiaUnidad): void {
    if (!this.unidadSeleccionada || foto.es_principal) return;
    this.cargandoAccion = true;
    this.comercializacionService.marcarFotografiaPrincipal(this.unidadSeleccionada.id_unidad, foto.id_fotografia).subscribe({
      next: () => {
        this.cargarFotosUnidad(this.unidadSeleccionada!.id_unidad);
        this.cargarUnidades();
        this.mostrarExito('Fotografía marcada como principal.');
        this.cargandoAccion = false;
        this.cdr.markForCheck();
      },
      error: (err) => {
        this.mostrarFallo(err?.error?.detail || 'Error al marcar fotografía principal.');
        this.cargandoAccion = false;
        this.cdr.markForCheck();
      }
    });
  }

  eliminarFoto(foto: FotografiaUnidad): void {
    if (!this.unidadSeleccionada) return;
    if (!confirm(`¿Eliminar la fotografía "${foto.nombre_archivo}"?`)) return;

    this.cargandoAccion = true;
    this.comercializacionService.eliminarFotografia(this.unidadSeleccionada.id_unidad, foto.id_fotografia).subscribe({
      next: () => {
        this.cargarFotosUnidad(this.unidadSeleccionada!.id_unidad);
        this.cargarUnidades();
        this.mostrarExito('Fotografía eliminada.');
        this.cargandoAccion = false;
        this.cdr.markForCheck();
      },
      error: (err) => {
        this.mostrarFallo(err?.error?.detail || 'Error al eliminar fotografía.');
        this.cargandoAccion = false;
        this.cdr.markForCheck();
      }
    });
  }

  urlFoto(idFoto: number): string {
    if (!this.unidadSeleccionada) return '';
    return this.comercializacionService.obtenerUrlFotografia(this.unidadSeleccionada.id_unidad, idFoto);
  }

  // ─────────────────────────────────────────────────────────────────────────────
  // HU144: REGISTRAR RESERVA
  // ─────────────────────────────────────────────────────────────────────────────
  abrirModalReserva(u: UnidadComercial): void {
    if (u.estado_comercial !== 'DISPONIBLE' || !u.disponible_efectiva) {
      this.mostrarFallo(`La unidad ${u.codigo} no está disponible para reserva.`);
      return;
    }

    this.unidadSeleccionada = u;
    this.clienteSeleccionado = null;
    this.busquedaCliente = '';
    this.formReserva = {
      id_cliente: null,
      monto_reserva: 1000,
      monto_pactado: u.precio_venta || null,
      fecha_vencimiento_reserva: this.calcularFechaSugerida(),
      observaciones: ''
    };
    this.mostrarModalReserva = true;
    this.buscarClientesCrm();
  }

  calcularFechaSugerida(): string {
    const d = new Date();
    d.setDate(d.getDate() + 15);
    return d.toISOString().split('T')[0];
  }

  buscarClientesCrm(): void {
    this.cargandoClientes = true;
    this.crmService.listarClientes({
      q: this.busquedaCliente.trim() || undefined,
      limit: 10
    }).subscribe({
      next: (resp) => {
        this.clientesCrm = resp.data || [];
        this.cargandoClientes = false;
        this.cdr.markForCheck();
      },
      error: () => {
        this.clientesCrm = [];
        this.cargandoClientes = false;
        this.cdr.markForCheck();
      }
    });
  }

  seleccionarClienteReserva(c: ClienteCRM): void {
    this.clienteSeleccionado = c;
    this.formReserva.id_cliente = c.id_cliente;
  }

  confirmarReserva(): void {
    if (!this.unidadSeleccionada || !this.formReserva.id_cliente) {
      this.mostrarFallo('Debe seleccionar un cliente del CRM.');
      return;
    }
    if (this.formReserva.monto_reserva <= 0) {
      this.mostrarFallo('El monto de reserva debe ser mayor a 0.');
      return;
    }

    this.cargandoAccion = true;
    const payload = {
      id_cliente: this.formReserva.id_cliente,
      monto_reserva: this.formReserva.monto_reserva,
      monto_pactado: this.formReserva.monto_pactado,
      fecha_vencimiento_reserva: this.formReserva.fecha_vencimiento_reserva || null,
      observaciones: this.formReserva.observaciones.trim() || null
    };

    this.comercializacionService.registrarReserva(this.unidadSeleccionada.id_unidad, payload).subscribe({
      next: (res) => {
        this.mostrarModalReserva = false;
        this.mostrarExito(`Reserva de unidad ${this.unidadSeleccionada?.codigo} registrada exitosamente.`);
        this.cargandoAccion = false;
        this.cargarResumen();
        this.cargarUnidades();
        this.cdr.markForCheck();
      },
      error: (err) => {
        this.mostrarFallo(err?.error?.detail || 'Error al registrar la reserva.');
        this.cargandoAccion = false;
        this.cdr.markForCheck();
      }
    });
  }

  // ─────────────────────────────────────────────────────────────────────────────
  // HU145: CANCELAR RESERVA Y CONFIRMAR VENTA
  // ─────────────────────────────────────────────────────────────────────────────
  abrirModalCancelarReserva(u: UnidadComercial): void {
    this.unidadSeleccionada = u;
    this.motivoCancelacion = '';
    this.mostrarModalCancelarReserva = true;
  }

  ejecutarCancelacionReserva(): void {
    if (!this.unidadSeleccionada) return;
    this.cargandoAccion = true;

    this.comercializacionService.cancelarReserva(this.unidadSeleccionada.id_unidad, {
      motivo: this.motivoCancelacion.trim() || undefined
    }).subscribe({
      next: () => {
        this.mostrarModalCancelarReserva = false;
        this.mostrarExito(`Reserva cancelada. Unidad ${this.unidadSeleccionada?.codigo} liberada a DISPONIBLE.`);
        this.cargandoAccion = false;
        this.cargarResumen();
        this.cargarUnidades();
        this.cdr.markForCheck();
      },
      error: (err) => {
        this.mostrarFallo(err?.error?.detail || 'Error al cancelar la reserva.');
        this.cargandoAccion = false;
        this.cdr.markForCheck();
      }
    });
  }

  abrirModalConfirmarVenta(u: UnidadComercial): void {
    this.unidadSeleccionada = u;
    this.formVenta = {
      id_cliente: null,
      monto_pactado: u.precio_venta || null,
      observaciones: ''
    };
    this.clienteSeleccionado = null;
    this.busquedaCliente = '';
    this.mostrarModalConfirmarVenta = true;
    if (u.estado_comercial !== 'RESERVADA') {
      this.buscarClientesCrm();
    }
  }

  ejecutarConfirmacionVenta(): void {
    if (!this.unidadSeleccionada) return;
    this.cargandoAccion = true;

    const payload: any = {
      monto_pactado: this.formVenta.monto_pactado,
      observaciones: this.formVenta.observaciones.trim() || undefined
    };

    if (this.unidadSeleccionada.estado_comercial !== 'RESERVADA') {
      if (!this.formVenta.id_cliente) {
        this.mostrarFallo('Debe seleccionar el cliente comprador.');
        this.cargandoAccion = false;
        return;
      }
      payload.id_cliente = this.formVenta.id_cliente;
    }

    this.comercializacionService.confirmarVenta(this.unidadSeleccionada.id_unidad, payload).subscribe({
      next: () => {
        this.mostrarModalConfirmarVenta = false;
        this.mostrarExito(`Venta de unidad ${this.unidadSeleccionada?.codigo} confirmada exitosamente.`);
        this.cargandoAccion = false;
        this.cargarResumen();
        this.cargarUnidades();
        this.cdr.markForCheck();
      },
      error: (err) => {
        this.mostrarFallo(err?.error?.detail || 'Error al confirmar la venta.');
        this.cargandoAccion = false;
        this.cdr.markForCheck();
      }
    });
  }

  marcarNoDisponible(u: UnidadComercial): void {
    if (!confirm(`¿Marcar la unidad ${u.codigo} como NO_DISPONIBLE?`)) return;
    this.cargandoAccion = true;
    this.comercializacionService.cambiarEstado(u.id_unidad, {
      estado_comercial: 'NO_DISPONIBLE',
      observacion: 'Unidad retirada temporalmente de la venta.'
    }).subscribe({
      next: () => {
        this.mostrarExito(`Unidad ${u.codigo} marcada como NO_DISPONIBLE.`);
        this.cargandoAccion = false;
        this.cargarResumen();
        this.cargarUnidades();
        this.cdr.markForCheck();
      },
      error: (err) => {
        this.mostrarFallo(err?.error?.detail || 'Error al cambiar estado a NO_DISPONIBLE.');
        this.cargandoAccion = false;
        this.cdr.markForCheck();
      }
    });
  }

  reactivarDisponible(u: UnidadComercial): void {
    if (!confirm(`¿Habilitar nuevamente la unidad ${u.codigo} como DISPONIBLE?`)) return;
    this.cargandoAccion = true;
    this.comercializacionService.cambiarEstado(u.id_unidad, {
      estado_comercial: 'DISPONIBLE',
      observacion: 'Unidad habilitada nuevamente como disponible.'
    }).subscribe({
      next: () => {
        this.mostrarExito(`Unidad ${u.codigo} habilitada como DISPONIBLE.`);
        this.cargandoAccion = false;
        this.cargarResumen();
        this.cargarUnidades();
        this.cdr.markForCheck();
      },
      error: (err) => {
        this.mostrarFallo(err?.error?.detail || 'Error al habilitar unidad como DISPONIBLE.');
        this.cargandoAccion = false;
        this.cdr.markForCheck();
      }
    });
  }

  // ─────────────────────────────────────────────────────────────────────────────
  // HU146: HISTORIAL COMERCIAL
  // ─────────────────────────────────────────────────────────────────────────────
  abrirModalHistorial(u: UnidadComercial): void {
    this.unidadSeleccionada = u;
    this.historialEventos = [];
    this.filtroEventoHistorial = '';
    this.mostrarModalHistorial = true;
    this.cargarHistorial();
  }

  cargarHistorial(): void {
    if (!this.unidadSeleccionada) return;
    this.cargandoHistorial = true;
    const tipo = this.filtroEventoHistorial || undefined;

    this.comercializacionService.listarHistorial(this.unidadSeleccionada.id_unidad, tipo, 100).subscribe({
      next: (resp) => {
        this.historialEventos = resp.historial || [];
        this.cargandoHistorial = false;
        this.cdr.markForCheck();
      },
      error: (err) => {
        this.mostrarFallo(err?.error?.detail || 'Error al consultar historial comercial.');
        this.cargandoHistorial = false;
        this.cdr.markForCheck();
      }
    });
  }

  // Helpers de visualización y badges semánticos
  badgeEstadoComercial(estado: string): string {
    switch (estado) {
      case 'DISPONIBLE':
        return 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/50 dark:text-emerald-300 border-emerald-300 dark:border-emerald-800';
      case 'RESERVADA':
        return 'bg-amber-100 text-amber-800 dark:bg-amber-950/50 dark:text-amber-300 border-amber-300 dark:border-amber-800';
      case 'VENDIDA':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-950/50 dark:text-blue-300 border-blue-300 dark:border-blue-800';
      case 'NO_DISPONIBLE':
        return 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300 border-slate-300 dark:border-slate-700';
      default:
        return 'bg-slate-100 text-slate-800 border-slate-300';
    }
  }

  badgeEstadoConstructivo(estado: string): string {
    switch (estado) {
      case 'EN_CONSTRUCCION':
        return 'bg-sky-50 text-sky-700 dark:bg-sky-950/40 dark:text-sky-300 border-sky-200 dark:border-sky-800';
      case 'FINALIZADO':
        return 'bg-teal-50 text-teal-700 dark:bg-teal-950/40 dark:text-teal-300 border-teal-200 dark:border-teal-800';
      case 'PLANIFICADO':
        return 'bg-purple-50 text-purple-700 dark:bg-purple-950/40 dark:text-purple-300 border-purple-200 dark:border-purple-800';
      case 'SUSPENDIDO':
        return 'bg-rose-50 text-rose-700 dark:bg-rose-950/40 dark:text-rose-300 border-rose-200 dark:border-rose-800';
      default:
        return 'bg-slate-100 text-slate-700';
    }
  }

  badgeEventoHistorial(tipo: string): string {
    switch (tipo) {
      case 'RESERVA':
        return 'bg-amber-500 text-white';
      case 'VENTA':
        return 'bg-blue-600 text-white';
      case 'CANCELACION':
        return 'bg-rose-600 text-white';
      case 'PUBLICACION':
        return 'bg-emerald-600 text-white';
      case 'DESPUBLICACION':
        return 'bg-slate-600 text-white';
      case 'ACTUALIZACION_PRECIO':
        return 'bg-indigo-600 text-white';
      case 'FOTOGRAFIA_AGREGADA':
      case 'FOTOGRAFIA_ELIMINADA':
        return 'bg-teal-600 text-white';
      default:
        return 'bg-slate-700 text-white';
    }
  }
}
