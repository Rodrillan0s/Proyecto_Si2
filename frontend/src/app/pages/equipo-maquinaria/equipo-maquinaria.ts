import { CommonModule } from '@angular/common';
import { ChangeDetectorRef, Component, DestroyRef, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Subject, debounceTime, distinctUntilChanged } from 'rxjs';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';

import { AuthService } from '../../services/auth';
import { Empresa, EmpresaService } from '../../services/empresa';
import {
  AsignacionEquipoMaquinaria,
  EquipoMaquinaria,
  EquipoMaquinariaPayload,
  EquipoMaquinariaService
} from '../../services/equipo-maquinaria';

type TabEquipos = 'equipos' | 'asignaciones';

@Component({
  selector: 'app-equipo-maquinaria',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './equipo-maquinaria.html',
  styleUrl: './equipo-maquinaria.css'
})
export class EquipoMaquinariaComponent implements OnInit {
  private equipoSvc = inject(EquipoMaquinariaService);
  private empresaSvc = inject(EmpresaService);
  private auth = inject(AuthService);
  private cdr = inject(ChangeDetectorRef);
  private destroyRef = inject(DestroyRef);
  private busqueda$ = new Subject<string>();

  tabActiva: TabEquipos = 'equipos';

  cargandoEquipos = false;
  cargandoAsignaciones = false;
  guardandoEquipo = false;
  guardandoAsignacion = false;

  equipos: EquipoMaquinaria[] = [];
  asignaciones: AsignacionEquipoMaquinaria[] = [];

  filtroTexto = '';
  filtroTipo = '';
  filtroEstado = '';

  filtroEstadoAsignacion = '';

  empresaActual: Empresa | null = null;
  esAdminGlobal = false;

  modalEquipoAbierto = false;
  modalAsignacionAbierto = false;
  modalRetiroAbierto = false;

  equipoSeleccionado: EquipoMaquinaria | null = null;
  asignacionSeleccionada: AsignacionEquipoMaquinaria | null = null;

  editandoEquipo = false;

  formEquipo: EquipoMaquinariaPayload = {
    codigo: '',
    nombre: '',
    tipo: '',
    marca: '',
    modelo: '',
    numero_serie: '',
    descripcion: '',
    estado: 'DISPONIBLE'
  };

  formAsignacion = {
    id_equipo_maquinaria: 0,
    id_obra: 0,
    observacion: ''
  };

  formRetiro = {
    observacion: ''
  };

  mensajeAlerta: {
    tipo: 'success' | 'error';
    texto: string;
  } | null = null;

  ngOnInit(): void {
    this.esAdminGlobal = this.auth.esVistaGlobal();
    this.empresaActual = this.auth.obtenerEmpresaActiva();

    this.auth.empresaActiva$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((empresa: Empresa | null) => {
        this.empresaActual = empresa;
        this.cargarTodo();
      });

    this.busqueda$
      .pipe(
        debounceTime(350),
        distinctUntilChanged(),
        takeUntilDestroyed(this.destroyRef)
      )
      .subscribe((texto) => {
        this.filtroTexto = texto;
        this.cargarEquipos();
      });

    this.cargarTodo();
  }

  cambiarTab(tab: TabEquipos): void {
    this.tabActiva = tab;

    if (tab === 'equipos') {
      this.cargarEquipos();
    } else {
      this.cargarAsignaciones();
    }
  }

  onBuscarInput(e: Event): void {
    const valor = (e.target as HTMLInputElement).value;
    this.busqueda$.next(valor);
  }

  cambiarFiltroTipo(tipo: string): void {
    this.filtroTipo = tipo;
    this.cargarEquipos();
  }

  cambiarFiltroEstado(estado: string): void {
    this.filtroEstado = estado;
    this.cargarEquipos();
  }

  cambiarFiltroEstadoAsignacion(estado: string): void {
    this.filtroEstadoAsignacion = estado;
    this.cargarAsignaciones();
  }

  cargarTodo(): void {
    this.cargarEquipos();

    if (this.tabActiva === 'asignaciones') {
      this.cargarAsignaciones();
    }
  }

  cargarEquipos(): void {
    this.cargandoEquipos = true;

    this.equipoSvc
      .listarEquipos({
        tipo: this.filtroTipo,
        estado: this.filtroEstado
      })
      .subscribe({
        next: (res) => {
          const equipos = res.data || [];

          this.equipos = equipos.filter((equipo) => {
            const texto = this.filtroTexto.trim().toLowerCase();

            if (!texto) {
              return true;
            }

            return (
              equipo.codigo?.toLowerCase().includes(texto) ||
              equipo.nombre?.toLowerCase().includes(texto) ||
              equipo.tipo?.toLowerCase().includes(texto) ||
              equipo.marca?.toLowerCase().includes(texto) ||
              equipo.modelo?.toLowerCase().includes(texto) ||
              equipo.numero_serie?.toLowerCase().includes(texto)
            );
          });

          this.cargandoEquipos = false;
          this.cdr.markForCheck();
        },
        error: (err) => {
          this.cargandoEquipos = false;
          this.mostrarNotificacion(
            'error',
            err.error?.detail || 'Error al cargar los equipos y maquinaria'
          );
          this.cdr.markForCheck();
        }
      });
  }

  cargarAsignaciones(): void {
    this.cargandoAsignaciones = true;

    this.equipoSvc
      .listarAsignaciones({
        estado: this.filtroEstadoAsignacion
      })
      .subscribe({
        next: (res) => {
          this.asignaciones = res.data || [];
          this.cargandoAsignaciones = false;
          this.cdr.markForCheck();
        },
        error: (err) => {
          this.cargandoAsignaciones = false;
          this.mostrarNotificacion(
            'error',
            err.error?.detail || 'Error al cargar las asignaciones'
          );
          this.cdr.markForCheck();
        }
      });
  }

  get totalEquipos(): number {
    return this.equipos.length;
  }

  get equiposDisponibles(): number {
    return this.equipos.filter(
      (equipo) => equipo.estado === 'DISPONIBLE'
    ).length;
  }

  get equiposAsignados(): number {
    return this.equipos.filter(
      (equipo) => equipo.estado === 'ASIGNADO'
    ).length;
  }

  get equiposMantenimiento(): number {
    return this.equipos.filter(
      (equipo) =>
        equipo.estado === 'MANTENIMIENTO' ||
        equipo.estado === 'FUERA_SERVICIO'
    ).length;
  }

  get asignacionesActivas(): number {
    return this.asignaciones.filter(
      (asignacion) => asignacion.estado === 'ASIGNADO'
    ).length;
  }

  abrirModalRegistrar(): void {
    this.editandoEquipo = false;
    this.equipoSeleccionado = null;

    this.formEquipo = {
      codigo: '',
      nombre: '',
      tipo: '',
      marca: '',
      modelo: '',
      numero_serie: '',
      descripcion: '',
      estado: 'DISPONIBLE'
    };

    this.modalEquipoAbierto = true;
  }

  abrirModalEditar(equipo: EquipoMaquinaria): void {
    this.editandoEquipo = true;
    this.equipoSeleccionado = equipo;

    this.formEquipo = {
      codigo: equipo.codigo || '',
      nombre: equipo.nombre || '',
      tipo: equipo.tipo || '',
      marca: equipo.marca || '',
      modelo: equipo.modelo || '',
      numero_serie: equipo.numero_serie || '',
      descripcion: equipo.descripcion || '',
      estado: equipo.estado || 'DISPONIBLE'
    };

    this.modalEquipoAbierto = true;
  }

  cerrarModalEquipo(): void {
    this.modalEquipoAbierto = false;
    this.equipoSeleccionado = null;
  }

  guardarEquipo(): void {
    if (!this.formEquipo.codigo.trim()) {
      this.mostrarNotificacion('error', 'El código del equipo es obligatorio');
      return;
    }

    if (!this.formEquipo.nombre.trim()) {
      this.mostrarNotificacion('error', 'El nombre del equipo es obligatorio');
      return;
    }

    this.guardandoEquipo = true;

    const payload: EquipoMaquinariaPayload = {
      codigo: this.formEquipo.codigo.trim(),
      nombre: this.formEquipo.nombre.trim(),
      tipo: this.formEquipo.tipo?.trim() || null,
      marca: this.formEquipo.marca?.trim() || null,
      modelo: this.formEquipo.modelo?.trim() || null,
      numero_serie: this.formEquipo.numero_serie?.trim() || null,
      descripcion: this.formEquipo.descripcion?.trim() || null,
      estado: this.formEquipo.estado || 'DISPONIBLE'
    };

    const solicitud = this.editandoEquipo && this.equipoSeleccionado
      ? this.equipoSvc.actualizarEquipo(
          this.equipoSeleccionado.id_equipo_maquinaria,
          payload
        )
      : this.equipoSvc.registrarEquipo(payload);

    solicitud.subscribe({
      next: (res) => {
        this.guardandoEquipo = false;

        this.mostrarNotificacion(
          'success',
          res.message ||
            (this.editandoEquipo
              ? 'Equipo actualizado correctamente'
              : 'Equipo registrado correctamente')
        );

        this.cerrarModalEquipo();
        this.cargarEquipos();
      },
      error: (err) => {
        this.guardandoEquipo = false;

        this.mostrarNotificacion(
          'error',
          err.error?.detail || 'Error al guardar el equipo'
        );

        this.cdr.markForCheck();
      }
    });
  }

  cambiarEstadoEquipo(equipo: EquipoMaquinaria, estado: string): void {
    this.equipoSvc
      .actualizarEstado(equipo.id_equipo_maquinaria, estado)
      .subscribe({
        next: (res) => {
          this.mostrarNotificacion(
            'success',
            res.message || 'Estado actualizado correctamente'
          );
          this.cargarEquipos();
        },
        error: (err) => {
          this.mostrarNotificacion(
            'error',
            err.error?.detail || 'Error al actualizar el estado'
          );
        }
      });
  }

  abrirModalAsignacion(equipo?: EquipoMaquinaria): void {
    this.equipoSeleccionado = equipo || null;

    this.formAsignacion = {
      id_equipo_maquinaria: equipo?.id_equipo_maquinaria || 0,
      id_obra: 0,
      observacion: ''
    };

    this.modalAsignacionAbierto = true;
  }

  cerrarModalAsignacion(): void {
    this.modalAsignacionAbierto = false;
    this.equipoSeleccionado = null;
  }

  guardarAsignacion(): void {
    if (!this.formAsignacion.id_equipo_maquinaria) {
      this.mostrarNotificacion(
        'error',
        'Selecciona un equipo o maquinaria'
      );
      return;
    }

    if (!this.formAsignacion.id_obra || this.formAsignacion.id_obra <= 0) {
      this.mostrarNotificacion(
        'error',
        'Ingresa el ID de la obra'
      );
      return;
    }

    this.guardandoAsignacion = true;

    this.equipoSvc
      .asignarEquipo({
        id_equipo_maquinaria: this.formAsignacion.id_equipo_maquinaria,
        id_obra: this.formAsignacion.id_obra,
        observacion: this.formAsignacion.observacion.trim() || null
      })
      .subscribe({
        next: (res) => {
          this.guardandoAsignacion = false;

          this.mostrarNotificacion(
            'success',
            res.message || 'Equipo asignado correctamente'
          );

          this.cerrarModalAsignacion();
          this.cargarTodo();
        },
        error: (err) => {
          this.guardandoAsignacion = false;

          this.mostrarNotificacion(
            'error',
            err.error?.detail || 'Error al asignar el equipo'
          );

          this.cdr.markForCheck();
        }
      });
  }

  abrirModalRetiro(asignacion: AsignacionEquipoMaquinaria): void {
    this.asignacionSeleccionada = asignacion;
    this.formRetiro = {
      observacion: ''
    };

    this.modalRetiroAbierto = true;
  }

  cerrarModalRetiro(): void {
    this.modalRetiroAbierto = false;
    this.asignacionSeleccionada = null;
  }

  retirarEquipo(): void {
    if (!this.asignacionSeleccionada) {
      return;
    }

    this.guardandoAsignacion = true;

    this.equipoSvc
      .retirarEquipo(
        this.asignacionSeleccionada.id_asignacion,
        {
          observacion: this.formRetiro.observacion.trim() || null
        }
      )
      .subscribe({
        next: (res) => {
          this.guardandoAsignacion = false;

          this.mostrarNotificacion(
            'success',
            res.message || 'Equipo retirado correctamente'
          );

          this.cerrarModalRetiro();
          this.cargarTodo();
        },
        error: (err) => {
          this.guardandoAsignacion = false;

          this.mostrarNotificacion(
            'error',
            err.error?.detail || 'Error al retirar el equipo'
          );

          this.cdr.markForCheck();
        }
      });
  }

  badgeClase(estado: string): string {
    switch (estado) {
      case 'DISPONIBLE':
        return 'badge-disponible';
      case 'ASIGNADO':
        return 'badge-asignado';
      case 'MANTENIMIENTO':
        return 'badge-mantenimiento';
      case 'FUERA_SERVICIO':
        return 'badge-fuera-servicio';
      case 'RETIRADO':
        return 'badge-retirado';
      default:
        return 'badge-default';
    }
  }

  formatoEstado(estado: string): string {
    switch (estado) {
      case 'DISPONIBLE':
        return 'Disponible';
      case 'ASIGNADO':
        return 'Asignado';
      case 'MANTENIMIENTO':
        return 'Mantenimiento';
      case 'FUERA_SERVICIO':
        return 'Fuera de servicio';
      case 'RETIRADO':
        return 'Retirado';
      default:
        return estado;
    }
  }

  mostrarNotificacion(
    tipo: 'success' | 'error',
    texto: string
  ): void {
    this.mensajeAlerta = {
      tipo,
      texto
    };

    this.cdr.markForCheck();

    setTimeout(() => {
      if (this.mensajeAlerta?.texto === texto) {
        this.mensajeAlerta = null;
        this.cdr.markForCheck();
      }
    }, 4500);
  }
}