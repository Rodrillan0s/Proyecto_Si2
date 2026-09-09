import { CommonModule } from '@angular/common';
import { ChangeDetectorRef, Component, DestroyRef, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Subject, debounceTime, distinctUntilChanged, finalize } from 'rxjs';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { AuthService } from '../../services/auth';
import {
  EstadoProveedor,
  Proveedor,
  ProveedorCreatePayload,
  ProveedorMaterial,
  ProveedorService,
} from '../../services/proveedor.service';
import { MaterialsService, Material } from '../../services/materials.service';

interface ProveedorFormModel extends ProveedorCreatePayload {
  id_proveedor?: number;
}

@Component({
  selector: 'app-proveedores',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './proveedores.html',
  styleUrl: './proveedores.css',
})
export class ProveedoresComponent implements OnInit {
  private service  = inject(ProveedorService);
  private matSvc   = inject(MaterialsService);
  private auth     = inject(AuthService);
  private cdr      = inject(ChangeDetectorRef);
  private destroyRef = inject(DestroyRef);
  private busqueda$ = new Subject<string>();

  // ── Lista principal ──────────────────────────────────────────────────────
  proveedores: Proveedor[] = [];
  q      = '';
  estado = '';
  pagina = 1;
  limite = 20;
  total  = 0;
  totalPaginas = 0;

  // ── Estados de carga ─────────────────────────────────────────────────────
  loadingProveedores = false;
  loadingDetalle     = false;
  savingProveedor    = false;
  updatingProveedor  = false;
  changingStatus     = false;
  loadingMateriales  = false;
  asociando          = false;

  // ── Mensajes ─────────────────────────────────────────────────────────────
  error  = '';
  exito  = '';

  // ── Modal activo ─────────────────────────────────────────────────────────
  modal: 'formulario' | 'detalle' | 'confirmacion' | 'materiales' | null = null;

  // ── Datos de formulario ───────────────────────────────────────────────────
  editando = false;
  form: ProveedorFormModel = this.formularioVacio();

  // ── Detalle / confirmación ────────────────────────────────────────────────
  detalle?: Proveedor;
  objetivoEstado?: Proveedor;

  // ── Gestión de materiales del proveedor ───────────────────────────────────
  proveedorMateriales: ProveedorMaterial[] = [];
  materialesDisponibles: Material[]  = [];
  seleccionMateriales: Set<number>   = new Set();
  proveedorActivo?: Proveedor;

  // ─────────────────────────────────────────────────────────────────────────
  // LIFECYCLE
  // ─────────────────────────────────────────────────────────────────────────
  ngOnInit(): void {
    this.busqueda$
      .pipe(debounceTime(400), distinctUntilChanged(), takeUntilDestroyed(this.destroyRef))
      .subscribe(() => { this.pagina = 1; this.cargarProveedores(); });
    this.cargarProveedores();
  }

  // ─────────────────────────────────────────────────────────────────────────
  // CARGA DE LISTA
  // ─────────────────────────────────────────────────────────────────────────
  cargarProveedores(): void {
    this.loadingProveedores = true;
    this.error = '';
    this.service
      .listar({
        q: this.q.trim() || undefined,
        estado: (this.estado || undefined) as EstadoProveedor | undefined,
        page: this.pagina,
        limit: this.limite,
      })
      .pipe(finalize(() => { this.loadingProveedores = false; this.cdr.detectChanges(); }))
      .subscribe({
        next: res => {
          this.proveedores   = res.data || [];
          this.total         = res.pagination.total;
          this.totalPaginas  = res.pagination.total_pages;
          this.cdr.detectChanges();
        },
        error: err => this.mostrarError(this.mensajeError(err, 'No se pudo cargar la lista de proveedores.')),
      });
  }

  buscar(): void { this.busqueda$.next(this.q.trim()); }
  filtrar(): void { this.pagina = 1; this.cargarProveedores(); }
  limpiarFiltros(): void { this.q = ''; this.estado = ''; this.pagina = 1; this.cargarProveedores(); }
  cambiarPagina(pagina: number): void {
    if (!this.loadingProveedores && pagina >= 1 && pagina <= this.totalPaginas) {
      this.pagina = pagina;
      this.cargarProveedores();
    }
  }

  // ─────────────────────────────────────────────────────────────────────────
  // FORMULARIO CREAR / EDITAR
  // ─────────────────────────────────────────────────────────────────────────
  formularioVacio(): ProveedorFormModel {
    return { nombre: '', nit: '', telefono: null, email: null, direccion: null, contacto: null };
  }

  abrirNuevo(): void {
    if (this.operacionFormularioActiva) return;
    this.error = '';
    this.editando = false;
    this.form = this.formularioVacio();
    this.modal = 'formulario';
  }

  abrirEditar(proveedor: Proveedor): void {
    if (this.loadingDetalle) return;
    this.loadingDetalle = true;
    this.service.obtener(proveedor.id_proveedor)
      .pipe(finalize(() => { this.loadingDetalle = false; this.cdr.detectChanges(); }))
      .subscribe({
        next: res => {
          const p = res.data;
          this.editando = true;
          this.form = {
            id_proveedor: p.id_proveedor,
            nombre:    p.nombre,
            nit:       p.nit,
            telefono:  p.telefono   || null,
            email:     p.email      || null,
            direccion: p.direccion  || null,
            contacto:  p.contacto   || null,
          };
          this.modal = 'formulario';
          this.cdr.detectChanges();
        },
        error: err => this.mostrarError(this.mensajeError(err, 'No se pudo cargar el proveedor.')),
      });
  }

  abrirDetalle(proveedor: Proveedor): void {
    if (this.loadingDetalle) return;
    this.loadingDetalle = true;
    this.service.obtener(proveedor.id_proveedor)
      .pipe(finalize(() => { this.loadingDetalle = false; this.cdr.detectChanges(); }))
      .subscribe({
        next: res => { this.detalle = res.data; this.modal = 'detalle'; this.cdr.detectChanges(); },
        error: err => this.mostrarError(this.mensajeError(err, 'No se pudo cargar el proveedor.')),
      });
  }

  guardar(): void {
    if (this.operacionFormularioActiva) return;
    const err = this.validar();
    if (err) { this.mostrarError(err); return; }

    if (this.editando) this.updatingProveedor = true;
    else               this.savingProveedor   = true;
    this.cdr.detectChanges();

    const payload: ProveedorCreatePayload = {
      nombre:    this.form.nombre.trim(),
      nit:       this.form.nit.trim(),
      telefono:  this.form.telefono?.trim()  || null,
      email:     this.form.email?.trim()     || null,
      direccion: this.form.direccion?.trim() || null,
      contacto:  this.form.contacto?.trim()  || null,
    };

    const request = this.editando && this.form.id_proveedor
      ? this.service.modificar(this.form.id_proveedor, payload)
      : this.service.registrar(payload);

    request
      .pipe(finalize(() => { this.liberarOperacionFormulario(); this.cdr.detectChanges(); }))
      .subscribe({
        next: () => {
          this.liberarOperacionFormulario();
          this.modal = null;
          this.form  = this.formularioVacio();
          this.mostrarExito(this.editando ? 'Proveedor actualizado correctamente.' : 'Proveedor registrado correctamente.');
          this.cargarProveedores();
        },
        error: err => this.mostrarError(this.mensajeError(err, 'No se pudo guardar el proveedor.')),
      });
  }

  get operacionFormularioActiva(): boolean { return this.savingProveedor || this.updatingProveedor; }
  private liberarOperacionFormulario(): void { this.savingProveedor = false; this.updatingProveedor = false; }

  private validar(): string | null {
    if (!this.form.nombre?.trim()) return 'El nombre o razón social es obligatorio.';
    if (!this.form.nit?.trim())    return 'El NIT es obligatorio.';
    const email = this.form.email?.trim();
    if (email && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) return 'El formato del correo electrónico no es válido.';
    return null;
  }

  // ─────────────────────────────────────────────────────────────────────────
  // CAMBIO DE ESTADO
  // ─────────────────────────────────────────────────────────────────────────
  confirmarEstado(proveedor: Proveedor): void {
    this.objetivoEstado = proveedor;
    this.modal = 'confirmacion';
  }

  cambiarEstado(): void {
    if (!this.objetivoEstado || this.changingStatus) return;
    const nuevo: EstadoProveedor = this.objetivoEstado.estado === 'ACTIVO' ? 'INACTIVO' : 'ACTIVO';
    this.changingStatus = true;
    this.service.cambiarEstado(this.objetivoEstado.id_proveedor, nuevo)
      .pipe(finalize(() => { this.changingStatus = false; this.cdr.detectChanges(); }))
      .subscribe({
        next: () => {
          this.modal = null;
          this.mostrarExito(nuevo === 'ACTIVO' ? 'Proveedor reactivado correctamente.' : 'Proveedor desactivado correctamente.');
          this.cargarProveedores();
        },
        error: err => this.mostrarError(this.mensajeError(err, 'No se pudo cambiar el estado.')),
      });
  }

  // ─────────────────────────────────────────────────────────────────────────
  // ASOCIAR MATERIALES
  // ─────────────────────────────────────────────────────────────────────────
  abrirAsociarMateriales(proveedor: Proveedor): void {
    this.proveedorActivo  = proveedor;
    this.proveedorMateriales = [];
    this.materialesDisponibles = [];
    this.seleccionMateriales = new Set();
    this.modal = 'materiales';
    this.loadingMateriales = true;

    // Cargar materiales del proveedor y catálogo en paralelo
    let done = 0;
    const check = () => { if (++done === 2) { this.loadingMateriales = false; this.cdr.detectChanges(); } };

    this.service.listarMateriales(proveedor.id_proveedor).subscribe({
      next: res => { this.proveedorMateriales = res.data || []; check(); },
      error: () => { this.mostrarError('No se pudieron cargar los materiales del proveedor.'); check(); },
    });

    this.matSvc.listar({ estado: 'ACTIVO', limit: 100 }).subscribe({
      next: res => { this.materialesDisponibles = res.data || []; check(); },
      error: () => { this.mostrarError('No se pudo cargar el catálogo de materiales.'); check(); },
    });
  }

  materialYaAsociado(id_material: number): boolean {
    return this.proveedorMateriales.some(m => m.id_material === id_material);
  }

  toggleSeleccion(id_material: number): void {
    if (this.materialYaAsociado(id_material)) return;
    if (this.seleccionMateriales.has(id_material)) {
      this.seleccionMateriales.delete(id_material);
    } else {
      this.seleccionMateriales.add(id_material);
    }
  }

  asociarSeleccionados(): void {
    if (!this.proveedorActivo || this.asociando || this.seleccionMateriales.size === 0) return;
    this.asociando = true;
    const ids = Array.from(this.seleccionMateriales);
    this.service.asociarMateriales(this.proveedorActivo.id_proveedor, ids)
      .pipe(finalize(() => { this.asociando = false; this.cdr.detectChanges(); }))
      .subscribe({
        next: res => {
          this.mostrarExito(res.message);
          this.seleccionMateriales = new Set();
          // Recargar materiales del proveedor
          this.service.listarMateriales(this.proveedorActivo!.id_proveedor).subscribe({
            next: r => { this.proveedorMateriales = r.data || []; this.cdr.detectChanges(); },
          });
        },
        error: err => this.mostrarError(this.mensajeError(err, 'No se pudo asociar los materiales.')),
      });
  }

  desasociarMaterial(id_material: number): void {
    if (!this.proveedorActivo || this.asociando) return;
    this.asociando = true;
    this.service.desasociarMaterial(this.proveedorActivo.id_proveedor, id_material)
      .pipe(finalize(() => { this.asociando = false; this.cdr.detectChanges(); }))
      .subscribe({
        next: () => {
          this.mostrarExito('Material desasociado correctamente.');
          this.proveedorMateriales = this.proveedorMateriales.filter(m => m.id_material !== id_material);
          this.cdr.detectChanges();
        },
        error: err => this.mostrarError(this.mensajeError(err, 'No se pudo desasociar el material.')),
      });
  }

  // ─────────────────────────────────────────────────────────────────────────
  // CONTROL DE MODAL
  // ─────────────────────────────────────────────────────────────────────────
  cerrarModal(): void {
    if (this.operacionFormularioActiva || this.changingStatus || this.asociando) return;
    this.modal = null;
    this.detalle = undefined;
    this.objetivoEstado = undefined;
    this.proveedorActivo = undefined;
    this.error = '';
    if (!this.editando) this.form = this.formularioVacio();
    this.cdr.detectChanges();
  }

  // ─────────────────────────────────────────────────────────────────────────
  // PERMISOS
  // ─────────────────────────────────────────────────────────────────────────
  puedeRegistrar(): boolean { return this.rolGestion(); }
  puedeModificar(): boolean { return this.rolGestion(); }
  puedeCambiarEstado(): boolean { return this.rolGestion(); }
  private rolGestion(): boolean {
    return ['ADMINISTRADOR', 'ADMINISTRADOR_EMPRESA'].includes(this.auth.obtenerUsuario()?.nombre_rol);
  }

  // ─────────────────────────────────────────────────────────────────────────
  // MENSAJES
  // ─────────────────────────────────────────────────────────────────────────
  private mensajeError(err: any, fallback: string): string {
    if (err?.status === 401) return 'Tu sesión ha expirado. Vuelve a iniciar sesión.';
    if (err?.status === 403) return 'No tienes permisos para realizar esta acción.';
    if (err?.status === 404) return err?.error?.detail || 'Proveedor o material no encontrado.';
    if (err?.status === 409) return err?.error?.detail || 'Ya existe un registro con esos datos.';
    if (err?.status >= 500)  return 'Error interno del servidor. Intenta nuevamente.';
    return err?.error?.detail || err?.error?.message || fallback;
  }

  private mostrarError(mensaje: string): void {
    this.error = mensaje;
    setTimeout(() => { this.error = ''; this.cdr.detectChanges(); }, 6000);
  }

  private mostrarExito(mensaje: string): void {
    this.exito = mensaje;
    setTimeout(() => { this.exito = ''; this.cdr.detectChanges(); }, 4500);
  }
}
