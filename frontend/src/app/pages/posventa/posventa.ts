import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PosventaService, SolicitudPosventa, GarantiaInmobiliaria, MetricasPosventa, OpcionGarantiaPosventa } from '../../services/posventa.service';
import { AuthService } from '../../services/auth';

@Component({
  selector: 'app-posventa',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './posventa.html',
  styleUrls: ['./posventa.css']
})
export class PosventaComponent implements OnInit {
  private posventaService = inject(PosventaService);
  private auth = inject(AuthService);

  tabActiva: 'solicitudes' | 'garantias' | 'historial' = 'solicitudes';

  solicitudes: SolicitudPosventa[] = [];
  garantias: GarantiaInmobiliaria[] = [];
  supervisores: { id_usuario: number; nombre_completo: string; nombre_rol: string; username: string }[] = [];
  metricas?: MetricasPosventa;
  opcionesGarantia: OpcionGarantiaPosventa[] = [];
  mensajeError = '';

  // Filtros
  filtroEstado = '';
  filtroPrioridad = '';

  // Permisos según rol
  get esCliente(): boolean {
    return this.auth.obtenerRolNormalizado() === 'CLIENTE';
  }

  get puedeRegistrarGarantia(): boolean {
    const rol = this.auth.obtenerRolNormalizado();
    return ['ADMINISTRADOR', 'ADMINISTRADOR_EMPRESA'].includes(rol);
  }

  get puedeClasificar(): boolean {
    const rol = this.auth.obtenerRolNormalizado();
    return ['ADMINISTRADOR', 'ADMINISTRADOR_EMPRESA'].includes(rol);
  }

  get puedeAsignar(): boolean {
    const rol = this.auth.obtenerRolNormalizado();
    return ['ADMINISTRADOR', 'ADMINISTRADOR_EMPRESA', 'JEFE_DE_OBRA'].includes(rol);
  }

  get puedeAtender(): boolean {
    const rol = this.auth.obtenerRolNormalizado();
    return ['SUPERVISOR_OBRA', 'SUPERVISOR', 'JEFE_DE_OBRA', 'ADMINISTRADOR_EMPRESA'].includes(rol);
  }

  // Modales
  modalGarantiaAbierto = false;
  modalReclamoAbierto = false;
  modalClasificarAbierto = false;
  modalAsignarAbierto = false;
  modalAtenderAbierto = false;
  modalDetalleAbierto = false;

  solicitudSeleccionada?: SolicitudPosventa;

  // Formularios
  formGarantia = {
    id_unidad: 0,
    id_cliente: 0,
    tipo_garantia: 'ESTRUCTURAL',
    descripcion_cobertura: '',
    fecha_inicio: new Date().toISOString().slice(0, 10),
    fecha_fin: new Date(new Date().setFullYear(new Date().getFullYear() + 5)).toISOString().slice(0, 10),
    condiciones: ''
  };

  formReclamo = {
    id_unidad: 0,
    id_cliente: 0,
    titulo: '',
    descripcion_defecto: ''
  };

  formClasificar = {
    categoria: 'PLOMERIA',
    prioridad: 'MEDIA',
    aplica_garantia: false,
    id_garantia: undefined as number | undefined,
    observaciones: ''
  };

  formAsignar = {
    id_supervisor: 0,
    fecha_estimada_visita: new Date(Date.now() + 86400000 * 2).toISOString().slice(0, 10),
    instrucciones_tecnicas: ''
  };

  formAtender = {
    nuevo_estado: 'EN_ATENCION',
    acciones_realizadas: '',
    materiales_utilizados: '',
    motivo_cierre: ''
  };

  ngOnInit(): void {
    this.cargarSolicitudes();
    this.cargarGarantias();
    this.cargarMetricas();
    this.cargarSupervisores();
    this.cargarOpcionesGarantia();
  }

  cambiarTab(tab: 'solicitudes' | 'garantias' | 'historial'): void {
    this.tabActiva = tab;
    if (tab === 'solicitudes') this.cargarSolicitudes();
    if (tab === 'garantias') this.cargarGarantias();
    if (tab === 'historial') this.cargarMetricas();
  }

  cargarSolicitudes(): void {
    this.posventaService.listarSolicitudes({
      estado: this.filtroEstado || undefined,
      prioridad: this.filtroPrioridad || undefined
    }).subscribe({
      next: (data) => this.solicitudes = data,
      error: (err) => console.error('Error cargando solicitudes', err)
    });
  }

  cargarGarantias(): void {
    this.posventaService.listarGarantias().subscribe({
      next: (data) => this.garantias = data,
      error: (err) => console.error('Error cargando garantías', err)
    });
  }

  cargarMetricas(): void {
    this.posventaService.consultarMetricas().subscribe({
      next: (res) => this.metricas = res.metricas,
      error: (err) => console.error('Error cargando métricas', err)
    });
  }

  cargarSupervisores(): void {
    this.posventaService.listarSupervisores().subscribe({
      next: (data) => {
        this.supervisores = data;
        if (data.length > 0) this.formAsignar.id_supervisor = data[0].id_usuario;
      },
      error: (err) => console.error('Error cargando supervisores', err)
    });
  }

  cargarOpcionesGarantia(): void {
    if (!this.puedeRegistrarGarantia) return;
    this.posventaService.listarOpcionesGarantia().subscribe({
      next: (data) => this.opcionesGarantia = data,
      error: (err) => console.error('Error cargando unidades y clientes', err)
    });
  }

  unidadSeleccionadaGarantia(): OpcionGarantiaPosventa | undefined {
    return this.opcionesGarantia.find(opcion => opcion.id_unidad === this.formGarantia.id_unidad);
  }

  cambiarUnidadGarantia(): void {
    const opcion = this.unidadSeleccionadaGarantia();
    this.formGarantia.id_cliente = opcion?.id_cliente || 0;
  }

  unidadSeleccionadaReclamo(): OpcionGarantiaPosventa | undefined {
    return this.opcionesGarantia.find(opcion => opcion.id_unidad === this.formReclamo.id_unidad);
  }

  cambiarUnidadReclamo(): void {
    const opcion = this.unidadSeleccionadaReclamo();
    this.formReclamo.id_cliente = opcion?.id_cliente || 0;
  }

  // Modales
  abrirModalNuevaGarantia(): void {
    this.cargarOpcionesGarantia();
    this.formGarantia.id_unidad = 0;
    this.formGarantia.id_cliente = 0;
    this.formGarantia.descripcion_cobertura = '';
    this.modalGarantiaAbierto = true;
  }

  guardarGarantia(): void {
    if (!this.formGarantia.id_unidad || !this.formGarantia.id_cliente) {
      alert('Seleccione una unidad y un cliente propietario.');
      return;
    }
    if (!this.formGarantia.descripcion_cobertura.trim()) {
      alert('Ingrese la descripción de cobertura.');
      return;
    }
    if (this.formGarantia.fecha_fin < this.formGarantia.fecha_inicio) {
      alert('La fecha de vencimiento no puede ser anterior a la fecha de inicio.');
      return;
    }
    this.posventaService.registrarGarantia(this.formGarantia).subscribe({
      next: () => {
        this.modalGarantiaAbierto = false;
        this.cargarGarantias();
        this.cargarMetricas();
      },
      error: (err) => alert(err.error?.detail || 'Error registrando garantía')
    });
  }

  abrirModalNuevoReclamo(): void {
    this.cargarOpcionesGarantia();
    this.formReclamo.id_unidad = 0;
    this.formReclamo.id_cliente = 0;
    this.formReclamo.titulo = '';
    this.formReclamo.descripcion_defecto = '';
    this.modalReclamoAbierto = true;
  }

  solicitarPosventaDesdeGarantia(garantia: GarantiaInmobiliaria): void {
    this.formReclamo.id_unidad = garantia.id_unidad;
    this.formReclamo.id_cliente = garantia.id_cliente;
    this.modalReclamoAbierto = true;
  }

  guardarReclamo(): void {
    if (!this.formReclamo.id_unidad) {
      alert('Seleccione la unidad inmobiliaria asociada al reclamo.');
      return;
    }
    if (!this.formReclamo.titulo.trim() || !this.formReclamo.descripcion_defecto.trim()) {
      alert('Ingrese el título y la descripción del defecto.');
      return;
    }
    this.posventaService.registrarSolicitud(this.formReclamo).subscribe({
      next: (res) => {
        alert(res.message);
        this.modalReclamoAbierto = false;
        this.cargarSolicitudes();
        this.cargarMetricas();
      },
      error: (err) => alert(err.error?.detail || 'Error registrando solicitud')
    });
  }

  verDetalle(solicitud: SolicitudPosventa): void {
    this.posventaService.obtenerDetalleSolicitud(solicitud.id_solicitud).subscribe({
      next: (data) => {
        this.solicitudSeleccionada = data;
        this.modalDetalleAbierto = true;
      },
      error: (err) => alert(err.error?.detail || 'Error cargando detalle')
    });
  }

  abrirModalClasificar(s: SolicitudPosventa): void {
    this.solicitudSeleccionada = s;
    this.formClasificar.categoria = s.categoria || 'PLOMERIA';
    this.formClasificar.prioridad = s.prioridad || 'MEDIA';
    this.formClasificar.aplica_garantia = s.aplica_garantia || false;
    this.formClasificar.id_garantia = s.id_garantia;
    this.modalClasificarAbierto = true;
  }

  guardarClasificacion(): void {
    if (!this.solicitudSeleccionada) return;
    this.posventaService.clasificarSolicitud(this.solicitudSeleccionada.id_solicitud, this.formClasificar).subscribe({
      next: () => {
        this.modalClasificarAbierto = false;
        this.cargarSolicitudes();
        this.cargarMetricas();
      },
      error: (err) => alert(err.error?.detail || 'Error clasificando solicitud')
    });
  }

  abrirModalAsignar(s: SolicitudPosventa): void {
    this.solicitudSeleccionada = s;
    this.modalAsignarAbierto = true;
  }

  guardarAsignacion(): void {
    if (!this.solicitudSeleccionada) return;
    this.posventaService.asignarResponsable(this.solicitudSeleccionada.id_solicitud, this.formAsignar).subscribe({
      next: () => {
        this.modalAsignarAbierto = false;
        this.cargarSolicitudes();
        this.cargarMetricas();
      },
      error: (err) => alert(err.error?.detail || 'Error asignando responsable')
    });
  }

  abrirModalAtender(s: SolicitudPosventa): void {
    this.solicitudSeleccionada = s;
    this.formAtender.nuevo_estado = s.estado === 'ASIGNADA' ? 'EN_ATENCION' : s.estado;
    this.modalAtenderAbierto = true;
  }

  guardarAtencion(): void {
    if (!this.solicitudSeleccionada) return;
    this.posventaService.atenderSolicitud(this.solicitudSeleccionada.id_solicitud, this.formAtender).subscribe({
      next: () => {
        this.modalAtenderAbierto = false;
        this.cargarSolicitudes();
        this.cargarMetricas();
      },
      error: (err) => alert(err.error?.detail || 'Error guardando atención')
    });
  }
}
