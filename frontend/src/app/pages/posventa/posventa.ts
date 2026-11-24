import { CommonModule } from '@angular/common';
import { Component, DestroyRef, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { forkJoin } from 'rxjs';
import { EmptyStateComponent } from '../../components/ui/empty-state';
import { StatusBadgeComponent } from '../../components/ui/status-badge';
import { AuthService } from '../../services/auth';
import {
  GarantiaInmobiliaria,
  HistorialUnidadPosventa,
  PosventaService,
  SolicitudPosventa,
} from '../../services/posventa.service';

@Component({
  standalone: true,
  selector: 'app-posventa',
  imports: [CommonModule, FormsModule, EmptyStateComponent, StatusBadgeComponent],
  templateUrl: './posventa.html',
  styleUrl: './posventa.css',
})
export class PosventaComponent implements OnInit {
  private api = inject(PosventaService);
  private auth = inject(AuthService);
  private destroyRef = inject(DestroyRef);

  readonly rol = this.auth.obtenerRolNormalizado();
  readonly esCliente = this.rol === 'CLIENTE';
  readonly esGestion = ['ADMINISTRADOR', 'ADMINISTRADOR_EMPRESA', 'JEFE_DE_OBRA', 'SUPERVISOR_OBRA'].includes(this.rol);

  tab = signal<'solicitudes' | 'garantias' | 'historial'>('solicitudes');
  cargando = signal(true);
  error = signal('');
  mensaje = signal('');

  categorias = signal<string[]>([]);
  estados = signal<string[]>([]);
  garantias = signal<GarantiaInmobiliaria[]>([]);
  solicitudes = signal<SolicitudPosventa[]>([]);
  seleccionada = signal<SolicitudPosventa | null>(null);
  historial = signal<HistorialUnidadPosventa | null>(null);

  filtroEstado = '';
  filtroCategoria = '';
  idUnidadHistorial: number | null = null;

  // Formulario garantía (HU161)
  nuevaGarantia = {
    id_unidad: null as number | null,
    codigo: '',
    tipo_garantia: '',
    descripcion: '',
    fecha_inicio: '',
    fecha_fin: '',
    observaciones: '',
  };

  // Formulario solicitud cliente (HU163)
  nuevaSolicitud = {
    id_unidad: null as number | null,
    id_garantia: null as number | null,
    titulo: '',
    descripcion: '',
  };

  // Acciones de gestión (HU164–HU166)
  categoriaSeleccionada = '';
  obsClasificacion = '';
  idResponsableAsignar: number | null = null;
  obsAsignacion = '';
  nuevoEstadoAtencion = '';
  obsAtencion = '';

  ngOnInit(): void {
    this.cargarTodo();
  }

  cargarTodo(): void {
    this.cargando.set(true);
    this.error.set('');
    forkJoin({
      catalogos: this.api.catalogos(),
      garantias: this.api.listarGarantias(),
      solicitudes: this.api.listarSolicitudes({
        estado: this.filtroEstado || undefined,
        categoria: this.filtroCategoria || undefined,
      }),
    })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: ({ catalogos, garantias, solicitudes }) => {
          this.categorias.set(catalogos.data?.categorias || []);
          this.estados.set(catalogos.data?.estados || []);
          this.garantias.set(garantias.data || []);
          this.solicitudes.set(solicitudes.data || []);
          this.cargando.set(false);
        },
        error: err => {
          this.error.set(err?.error?.detail || 'No se pudo cargar el módulo de garantías y posventa.');
          this.cargando.set(false);
        },
      });
  }

  verSeguimiento(sol: SolicitudPosventa): void {
    this.error.set('');
    this.api
      .obtenerSolicitud(sol.id_solicitud_posventa)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: res => {
          this.seleccionada.set(res.data);
          this.categoriaSeleccionada = res.data.categoria || '';
          this.idResponsableAsignar = res.data.id_responsable;
          this.nuevoEstadoAtencion = '';
          this.obsAtencion = '';
        },
        error: err => this.error.set(err?.error?.detail || 'No se pudo cargar el seguimiento.'),
      });
  }

  crearGarantia(): void {
    if (!this.esGestion || !this.nuevaGarantia.id_unidad) return;
    this.error.set('');
    this.mensaje.set('');
    this.api
      .registrarGarantia({
        id_unidad: Number(this.nuevaGarantia.id_unidad),
        codigo: this.nuevaGarantia.codigo.trim() || null,
        tipo_garantia: this.nuevaGarantia.tipo_garantia.trim(),
        descripcion: this.nuevaGarantia.descripcion.trim(),
        fecha_inicio: this.nuevaGarantia.fecha_inicio,
        fecha_fin: this.nuevaGarantia.fecha_fin || null,
        observaciones: this.nuevaGarantia.observaciones.trim() || null,
      })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => {
          this.mensaje.set('Garantía inmobiliaria registrada correctamente.');
          this.nuevaGarantia = {
            id_unidad: null,
            codigo: '',
            tipo_garantia: '',
            descripcion: '',
            fecha_inicio: '',
            fecha_fin: '',
            observaciones: '',
          };
          this.cargarTodo();
        },
        error: err => this.error.set(err?.error?.detail || 'No se pudo registrar la garantía.'),
      });
  }

  crearSolicitud(): void {
    if (!this.esCliente || !this.nuevaSolicitud.id_unidad) return;
    this.error.set('');
    this.mensaje.set('');
    this.api
      .registrarSolicitud({
        id_unidad: Number(this.nuevaSolicitud.id_unidad),
        id_garantia: this.nuevaSolicitud.id_garantia ? Number(this.nuevaSolicitud.id_garantia) : null,
        titulo: this.nuevaSolicitud.titulo.trim(),
        descripcion: this.nuevaSolicitud.descripcion.trim(),
      })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => {
          this.mensaje.set('Solicitud de posventa registrada correctamente.');
          this.nuevaSolicitud = { id_unidad: null, id_garantia: null, titulo: '', descripcion: '' };
          this.cargarTodo();
        },
        error: err => this.error.set(err?.error?.detail || 'No se pudo registrar la solicitud.'),
      });
  }

  clasificar(): void {
    const sol = this.seleccionada();
    if (!sol || !this.categoriaSeleccionada) return;
    this.api
      .clasificarSolicitud(sol.id_solicitud_posventa, {
        categoria: this.categoriaSeleccionada,
        observacion: this.obsClasificacion.trim() || undefined,
      })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => {
          this.mensaje.set('Solicitud clasificada correctamente.');
          this.obsClasificacion = '';
          this.verSeguimiento(sol);
          this.cargarTodo();
        },
        error: err => this.error.set(err?.error?.detail || 'No se pudo clasificar la solicitud.'),
      });
  }

  asignar(): void {
    const sol = this.seleccionada();
    if (!sol || !this.idResponsableAsignar) return;
    this.api
      .asignarResponsable(sol.id_solicitud_posventa, {
        id_responsable: Number(this.idResponsableAsignar),
        observacion: this.obsAsignacion.trim() || undefined,
      })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => {
          this.mensaje.set('Responsable asignado correctamente.');
          this.obsAsignacion = '';
          this.verSeguimiento(sol);
          this.cargarTodo();
        },
        error: err => this.error.set(err?.error?.detail || 'No se pudo asignar el responsable.'),
      });
  }

  registrarAtencion(): void {
    const sol = this.seleccionada();
    if (!sol || !this.obsAtencion.trim()) return;
    this.api
      .gestionarAtencion(sol.id_solicitud_posventa, {
        estado: this.nuevoEstadoAtencion || undefined,
        observacion: this.obsAtencion.trim(),
      })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: res => {
          this.mensaje.set('Atención registrada en el historial de seguimiento.');
          this.seleccionada.set(res.data);
          this.nuevoEstadoAtencion = '';
          this.obsAtencion = '';
          this.cargarTodo();
        },
        error: err => this.error.set(err?.error?.detail || 'No se pudo registrar la atención.'),
      });
  }

  consultarHistorialUnidad(): void {
    if (!this.idUnidadHistorial || this.idUnidadHistorial <= 0) return;
    this.error.set('');
    this.api
      .historialUnidad(Number(this.idUnidadHistorial))
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: res => this.historial.set(res.data),
        error: err => {
          this.historial.set(null);
          this.error.set(err?.error?.detail || 'No se pudo consultar el historial de la unidad.');
        },
      });
  }
}
