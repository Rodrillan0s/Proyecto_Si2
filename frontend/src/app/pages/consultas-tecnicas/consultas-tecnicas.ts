import { Component, OnInit, ChangeDetectorRef, DestroyRef, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { Subject, debounceTime, distinctUntilChanged } from 'rxjs';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';

import { AuthService } from '../../services/auth';
import { ProyectosService, Proyecto, ApiResponseList, ApiResponseDetail } from '../../services/proyectos';
import {
  ConsultaTecnica,
  ConsultaTecnicaDetalle,
  ConsultaTecnicaFiltros,
  ConsultaTecnicaRespuesta,
  ConsultaTecnicaService,
  EstadoConsultaTecnica,
  UsuarioAsignable
} from '../../services/consulta-tecnica.service';

import { PageHeaderComponent } from '../../components/ui/page-header';
import { DashboardCardComponent } from '../../components/ui/dashboard-card';
import { StatusBadgeComponent } from '../../components/ui/status-badge';
import { EmptyStateComponent } from '../../components/ui/empty-state';

@Component({
  selector: 'app-consultas-tecnicas',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    PageHeaderComponent,
    DashboardCardComponent,
    StatusBadgeComponent,
    EmptyStateComponent
  ],
  templateUrl: './consultas-tecnicas.html',
  styleUrl: './consultas-tecnicas.css'
})
export class ConsultasTecnicasComponent implements OnInit {
  private consultaService = inject(ConsultaTecnicaService);
  private proyectosService = inject(ProyectosService);
  private authService = inject(AuthService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private cdr = inject(ChangeDetectorRef);
  private destroyRef = inject(DestroyRef);

  // Contexto y filtrado
  idObraFiltro?: number;
  esVistaObraEspecifica = false;
  obraActual?: Proyecto | null;
  obrasDisponibles: Proyecto[] = [];

  busqueda = '';
  estadoSeleccionado = '';
  idResponsableSeleccionado?: number;

  private searchSubject = new Subject<string>();

  // Datos
  consultas: ConsultaTecnica[] = [];
  cargando = false;
  guardando = false;
  error = '';
  exito = '';

  // Paginación y KPI
  total = 0;
  page = 1;
  limit = 15;
  pages = 1;

  resumen = {
    total: 0,
    abiertas: 0,
    asignadas: 0,
    respondidas: 0,
    cerradas: 0
  };

  // Modal Nueva Consulta
  mostrarModalCrear = false;
  formCrear = {
    id_obra: 0,
    asunto: '',
    descripcion: '',
    referencia_tecnica: '',
    asignado_a: undefined as number | undefined
  };
  usuariosAsignablesParaCrear: UsuarioAsignable[] = [];
  cargandoUsuariosCrear = false;

  // Drawer / Modal Detalle
  mostrarModalDetalle = false;
  consultaSeleccionada?: ConsultaTecnicaDetalle | null;
  cargandoDetalle = false;

  // Acciones en detalle
  nuevaRespuestaTexto = '';
  enviandoRespuesta = false;

  mostrarModalAsignar = false;
  nuevoResponsableId?: number;
  motivoAsignacion = '';
  usuariosAsignablesDetalle: UsuarioAsignable[] = [];
  cargandoUsuariosDetalle = false;

  mostrarModalCerrar = false;
  motivoCierre = '';

  ngOnInit(): void {
    // Escuchar debounced search
    this.searchSubject
      .pipe(debounceTime(350), distinctUntilChanged(), takeUntilDestroyed(this.destroyRef))
      .subscribe(() => {
        this.page = 1;
        this.cargarConsultas();
      });

    // Detectar si la ruta es /proyectos/:id/consultas-tecnicas o /consultas-tecnicas
    this.route.paramMap.pipe(takeUntilDestroyed(this.destroyRef)).subscribe(params => {
      const idParam = params.get('id');
      if (idParam) {
        this.idObraFiltro = Number(idParam);
        this.esVistaObraEspecifica = true;
        this.formCrear.id_obra = this.idObraFiltro;
        this.cargarInfoObra(this.idObraFiltro);
      } else {
        this.esVistaObraEspecifica = false;
      }
      this.cargarObrasEmpresa();
      this.cargarConsultas();
    });

    this.route.queryParamMap.pipe(takeUntilDestroyed(this.destroyRef)).subscribe(qp => {
      const qpObra = qp.get('id_obra');
      if (qpObra && !this.esVistaObraEspecifica) {
        this.idObraFiltro = Number(qpObra);
        this.formCrear.id_obra = this.idObraFiltro;
      }
      const qpEstado = qp.get('estado');
      if (qpEstado) {
        this.estadoSeleccionado = qpEstado.toUpperCase();
      }
      const qpId = qp.get('ver');
      if (qpId) {
        this.abrirDetalle(Number(qpId));
      }
    });
  }

  onSearchChange(): void {
    this.searchSubject.next(this.busqueda);
  }

  cargarObrasEmpresa(): void {
    this.proyectosService.listarProyectos().subscribe({
      next: (res: ApiResponseList) => {
        if (res.success && Array.isArray(res.data)) {
          this.obrasDisponibles = res.data;
          if (this.idObraFiltro && !this.obraActual) {
            this.obraActual = this.obrasDisponibles.find(o => o.id_obra === this.idObraFiltro) || null;
          }
        }
        this.cdr.detectChanges();
      },
      error: () => {}
    });
  }

  cargarInfoObra(idObra: number): void {
    this.proyectosService.obtenerProyectoDetalle(idObra).subscribe({
      next: (res: ApiResponseDetail) => {
        if (res.success) {
          this.obraActual = res.data;
        }
        this.cdr.detectChanges();
      },
      error: () => {}
    });
  }

  cargarConsultas(): void {
    this.cargando = true;
    this.error = '';

    const filtros: ConsultaTecnicaFiltros = {
      id_obra: this.idObraFiltro || undefined,
      estado: this.estadoSeleccionado || undefined,
      id_responsable: this.idResponsableSeleccionado || undefined,
      busqueda: this.busqueda.trim() || undefined,
      page: this.page,
      limit: this.limit
    };

    const call$ = this.idObraFiltro
      ? this.consultaService.listarPorObra(this.idObraFiltro, filtros)
      : this.consultaService.listar(filtros);

    call$.subscribe({
      next: (res) => {
        this.consultas = res.items || [];
        this.total = res.total;
        this.pages = res.pages;
        this.calcularResumen();
        this.cargando = false;
        this.cdr.detectChanges();
      },
      error: (err) => {
        this.error = err.error?.detail || 'Error al cargar el listado de consultas técnicas.';
        this.cargando = false;
        this.cdr.detectChanges();
      }
    });
  }

  calcularResumen(): void {
    // Calculado sobre el conjunto de consultas actual o filtros
    this.resumen.total = this.total;
    this.resumen.abiertas = this.consultas.filter(c => c.estado === 'ABIERTA').length;
    this.resumen.asignadas = this.consultas.filter(c => c.estado === 'ASIGNADA').length;
    this.resumen.respondidas = this.consultas.filter(c => c.estado === 'RESPONDIDA').length;
    this.resumen.cerradas = this.consultas.filter(c => c.estado === 'CERRADA').length;
  }

  filtrarPorEstado(estado: string): void {
    this.estadoSeleccionado = estado;
    this.page = 1;
    this.cargarConsultas();
  }

  onObraFiltroChange(): void {
    this.page = 1;
    this.cargarConsultas();
  }

  cambiarPagina(nuevaPagina: number): void {
    if (nuevaPagina >= 1 && nuevaPagina <= this.pages) {
      this.page = nuevaPagina;
      this.cargarConsultas();
    }
  }

  // --- NUEVA CONSULTA (HU138) ---
  abrirModalCrear(): void {
    this.formCrear = {
      id_obra: this.idObraFiltro || (this.obrasDisponibles[0]?.id_obra || 0),
      asunto: '',
      descripcion: '',
      referencia_tecnica: '',
      asignado_a: undefined
    };
    this.error = '';
    this.exito = '';
    this.mostrarModalCrear = true;
    if (this.formCrear.id_obra) {
      this.cargarUsuariosAsignablesCrear(this.formCrear.id_obra);
    }
  }

  onObraCrearChange(): void {
    if (this.formCrear.id_obra) {
      this.cargarUsuariosAsignablesCrear(this.formCrear.id_obra);
    } else {
      this.usuariosAsignablesParaCrear = [];
    }
  }

  cargarUsuariosAsignablesCrear(idObra: number): void {
    this.cargandoUsuariosCrear = true;
    this.consultaService.obtenerUsuariosAsignables(idObra).subscribe({
      next: (usuarios) => {
        this.usuariosAsignablesParaCrear = usuarios;
        this.cargandoUsuariosCrear = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.usuariosAsignablesParaCrear = [];
        this.cargandoUsuariosCrear = false;
        this.cdr.detectChanges();
      }
    });
  }

  guardarNuevaConsulta(): void {
    if (!this.formCrear.id_obra) {
      this.error = 'Debe seleccionar una obra para registrar la consulta técnica.';
      return;
    }
    if (!this.formCrear.asunto.trim() || this.formCrear.asunto.trim().length < 3) {
      this.error = 'El asunto debe tener al menos 3 caracteres.';
      return;
    }
    if (!this.formCrear.descripcion.trim() || this.formCrear.descripcion.trim().length < 5) {
      this.error = 'La descripción técnica debe tener al menos 5 caracteres.';
      return;
    }

    this.guardando = true;
    this.error = '';

    const payload = {
      asunto: this.formCrear.asunto.trim(),
      descripcion: this.formCrear.descripcion.trim(),
      referencia_tecnica: this.formCrear.referencia_tecnica.trim() || null,
      asignado_a: this.formCrear.asignado_a ? Number(this.formCrear.asignado_a) : undefined
    };

    this.consultaService.registrar(this.formCrear.id_obra, payload).subscribe({
      next: (res) => {
        this.guardando = false;
        this.mostrarModalCrear = false;
        this.mostrarExito(`Consulta técnica ${res.codigo} registrada correctamente.`);
        this.cargarConsultas();
        this.abrirDetalle(res.id_consulta_tecnica);
      },
      error: (err) => {
        this.guardando = false;
        this.error = err.error?.detail || 'Error al registrar la consulta técnica.';
        this.cdr.detectChanges();
      }
    });
  }

  // --- DETALLE, RESPUESTA Y ASIGNACIÓN (HU139, HU140) ---
  abrirDetalle(idConsulta: number): void {
    this.cargandoDetalle = true;
    this.mostrarModalDetalle = true;
    this.nuevaRespuestaTexto = '';

    this.consultaService.obtenerDetalle(idConsulta).subscribe({
      next: (detalle) => {
        this.consultaSeleccionada = detalle;
        this.cargandoDetalle = false;
        this.cdr.detectChanges();
      },
      error: (err) => {
        this.cargandoDetalle = false;
        this.error = err.error?.detail || 'No se pudo cargar el detalle de la consulta técnica.';
        this.cdr.detectChanges();
      }
    });
  }

  cerrarDetalle(): void {
    this.mostrarModalDetalle = false;
    this.consultaSeleccionada = null;
    this.mostrarModalAsignar = false;
    this.mostrarModalCerrar = false;
  }

  // Enviar respuesta técnica (HU139)
  enviarRespuesta(): void {
    if (!this.consultaSeleccionada || !this.nuevaRespuestaTexto.trim() || this.enviandoRespuesta) return;
    if (this.nuevaRespuestaTexto.trim().length < 3) {
      this.error = 'La respuesta técnica debe contener al menos 3 caracteres.';
      return;
    }

    this.enviandoRespuesta = true;
    this.error = '';

    this.consultaService.responder(this.consultaSeleccionada.id_consulta_tecnica, {
      respuesta: this.nuevaRespuestaTexto.trim()
    }).subscribe({
      next: () => {
        this.enviandoRespuesta = false;
        this.nuevaRespuestaTexto = '';
        this.mostrarExito('Aclaración técnica registrada correctamente.');
        // Recargar detalle y refrescar lista
        this.abrirDetalle(this.consultaSeleccionada!.id_consulta_tecnica);
        this.cargarConsultas();
      },
      error: (err) => {
        this.enviandoRespuesta = false;
        this.error = err.error?.detail || 'Error al guardar la respuesta.';
        this.cdr.detectChanges();
      }
    });
  }

  // Abrir modal de asignación
  abrirModalAsignacion(): void {
    if (!this.consultaSeleccionada) return;
    this.nuevoResponsableId = this.consultaSeleccionada.asignado_a || undefined;
    this.motivoAsignacion = '';
    this.mostrarModalAsignar = true;
    this.cargandoUsuariosDetalle = true;

    this.consultaService.obtenerUsuariosAsignables(this.consultaSeleccionada.id_obra).subscribe({
      next: (usuarios) => {
        this.usuariosAsignablesDetalle = usuarios;
        this.cargandoUsuariosDetalle = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.usuariosAsignablesDetalle = [];
        this.cargandoUsuariosDetalle = false;
        this.cdr.detectChanges();
      }
    });
  }

  guardarAsignacion(): void {
    if (!this.consultaSeleccionada || !this.nuevoResponsableId) {
      this.error = 'Debe seleccionar un responsable válido.';
      return;
    }

    this.guardando = true;
    this.consultaService.asignarResponsable(this.consultaSeleccionada.id_consulta_tecnica, {
      id_responsable: Number(this.nuevoResponsableId),
      motivo: this.motivoAsignacion.trim() || undefined
    }).subscribe({
      next: (res) => {
        this.guardando = false;
        this.mostrarModalAsignar = false;
        this.mostrarExito(`Responsable asignado a: ${res.responsable_nombre || 'Usuario'}`);
        this.abrirDetalle(this.consultaSeleccionada!.id_consulta_tecnica);
        this.cargarConsultas();
      },
      error: (err) => {
        this.guardando = false;
        this.error = err.error?.detail || 'Error al reasignar responsable.';
        this.cdr.detectChanges();
      }
    });
  }

  // Cerrar / Reabrir consulta (HU139 / HU140)
  abrirModalCierre(): void {
    this.motivoCierre = '';
    this.mostrarModalCerrar = true;
  }

  confirmarCierre(): void {
    if (!this.consultaSeleccionada) return;

    this.guardando = true;
    this.consultaService.cambiarEstado(this.consultaSeleccionada.id_consulta_tecnica, {
      estado: 'CERRADA',
      motivo: this.motivoCierre.trim() || undefined
    }).subscribe({
      next: () => {
        this.guardando = false;
        this.mostrarModalCerrar = false;
        this.mostrarExito('Consulta técnica cerrada exitosamente.');
        this.abrirDetalle(this.consultaSeleccionada!.id_consulta_tecnica);
        this.cargarConsultas();
      },
      error: (err) => {
        this.guardando = false;
        this.error = err.error?.detail || 'Error al cerrar la consulta técnica.';
        this.cdr.detectChanges();
      }
    });
  }

  reabrirConsulta(): void {
    if (!this.consultaSeleccionada) return;
    if (!confirm('¿Desea reabrir esta consulta técnica para solicitar aclaraciones adicionales?')) return;

    this.guardando = true;
    const nuevoEstado: EstadoConsultaTecnica = this.consultaSeleccionada.asignado_a ? 'ASIGNADA' : 'ABIERTA';

    this.consultaService.cambiarEstado(this.consultaSeleccionada.id_consulta_tecnica, {
      estado: nuevoEstado,
      motivo: 'Reapertura de consulta técnica para aclaración'
    }).subscribe({
      next: () => {
        this.guardando = false;
        this.mostrarExito('Consulta técnica reabierta.');
        this.abrirDetalle(this.consultaSeleccionada!.id_consulta_tecnica);
        this.cargarConsultas();
      },
      error: (err) => {
        this.guardando = false;
        this.error = err.error?.detail || 'Error al reabrir la consulta técnica.';
        this.cdr.detectChanges();
      }
    });
  }

  // Navegación
  volverAProyecto(): void {
    if (this.idObraFiltro) {
      this.router.navigate(['/proyectos', this.idObraFiltro]);
    } else {
      this.router.navigate(['/proyectos']);
    }
  }

  // Permisos
  puedeRegistrar(): boolean {
    return this.authService.hasPermission('Registrar_consultas_tecnicas');
  }

  puedeAsignar(): boolean {
    return this.authService.hasPermission('Asignar_consultas_tecnicas');
  }

  puedeResponder(): boolean {
    return this.authService.hasPermission('Responder_consultas_tecnicas');
  }

  puedeCerrar(): boolean {
    return this.authService.hasPermission('Cerrar_consultas_tecnicas');
  }

  mostrarExito(msg: string): void {
    this.exito = msg;
    setTimeout(() => {
      this.exito = '';
      this.cdr.detectChanges();
    }, 4500);
  }
}
