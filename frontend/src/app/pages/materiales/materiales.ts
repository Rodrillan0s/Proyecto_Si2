import { CommonModule } from '@angular/common';
import { ChangeDetectorRef, Component, DestroyRef, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Subject, debounceTime, distinctUntilChanged, finalize, forkJoin } from 'rxjs';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { AuthService } from '../../services/auth';
import {
  CategoriaMaterial, EstadoMaterial, Material, MaterialCaracteristica, MaterialCreatePayload,
  MaterialUpdatePayload, MaterialsService, UnidadMedida
} from '../../services/materials.service';

interface MaterialFormModel extends MaterialCreatePayload { id_material?: number; stock_actual?: number; }

@Component({
  selector: 'app-materiales',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './materiales.html',
  styleUrl: './materiales.css'
})
export class MaterialesComponent implements OnInit {
  private service = inject(MaterialsService);
  private auth = inject(AuthService);
  private cdr = inject(ChangeDetectorRef);
  private destroyRef = inject(DestroyRef);
  private busqueda$ = new Subject<string>();

  materiales: Material[] = [];
  categorias: CategoriaMaterial[] = [];
  unidades: UnidadMedida[] = [];
  q = '';
  categoria = '';
  estado = '';
  stock = '';
  pagina = 1;
  limite = 20;
  total = 0;
  totalPaginas = 0;
  loadingMaterials = false;
  loadingCatalogs = false;
  loadingDetail = false;
  savingMaterial = false;
  updatingMaterial = false;
  changingStatus = false;
  savingCategory = false;
  error = '';
  exito = '';
  modal: 'formulario' | 'detalle' | 'confirmacion' | null = null;
  categoriaModalAbierto = false;
  categoriaError = '';
  editando = false;
  detalle?: Material;
  objetivoEstado?: Material;
  form: MaterialFormModel = this.formularioVacio();
  categoriaForm = { nombre: '', descripcion: '' };

  ngOnInit(): void {
    this.busqueda$.pipe(debounceTime(400), distinctUntilChanged(), takeUntilDestroyed(this.destroyRef))
      .subscribe(() => { this.pagina = 1; this.cargarMateriales(); });
    this.loadingCatalogs = true;
    forkJoin({ categorias: this.service.categorias(), unidades: this.service.unidadesMedida() })
      .pipe(finalize(() => { this.loadingCatalogs = false; this.cdr.detectChanges(); })).subscribe({
      next: ({ categorias, unidades }) => { this.categorias = categorias.data || []; this.unidades = unidades.data || []; this.cdr.detectChanges(); },
      error: err => this.mostrarError(this.mensajeError(err, 'No se pudieron cargar los catálogos.'))
    });
    this.cargarMateriales();
  }

  formularioVacio(): MaterialFormModel {
    return { codigo: '', nombre_material: '', descripcion: null, id_categoria: 0, id_unidad_medida: 0,
      precio: null, caracteristicas: [], cantidad_inicial: 0, stock_minimo: 0,
      fecha_ingreso: new Date().toISOString().slice(0, 10) };
  }

  cargarMateriales(): void {
    this.loadingMaterials = true; this.error = '';
    this.service.listar({ q: this.q.trim() || undefined, id_categoria: this.categoria ? +this.categoria : undefined,
      estado: (this.estado || undefined) as EstadoMaterial | undefined,
      stock_bajo: this.stock === 'bajo' ? true : this.stock === 'normal' ? false : undefined,
      page: this.pagina, limit: this.limite })
      .pipe(finalize(() => { this.loadingMaterials = false; this.cdr.detectChanges(); })).subscribe({
        next: res => { this.materiales = res.data || []; this.total = res.pagination.total; this.totalPaginas = res.pagination.total_pages; this.cdr.detectChanges(); },
        error: err => this.mostrarError(this.mensajeError(err, 'No se pudo cargar el catálogo de materiales.'))
      });
  }

  buscar(): void { this.busqueda$.next(this.q.trim()); }
  filtrar(): void { this.pagina = 1; this.cargarMateriales(); }
  limpiarFiltros(): void { this.q = ''; this.categoria = ''; this.estado = ''; this.stock = ''; this.pagina = 1; this.cargarMateriales(); }
  cambiarPagina(pagina: number): void { if (!this.loadingMaterials && pagina >= 1 && pagina <= this.totalPaginas) { this.pagina = pagina; this.cargarMateriales(); } }

  abrirNuevo(): void { if (this.operacionFormularioActiva) return; this.error = ''; this.editando = false; this.form = this.formularioVacio(); this.modal = 'formulario'; }
  abrirEditar(material: Material): void {
    if (this.loadingDetail) return;
    this.loadingDetail = true;
    this.service.obtener(material.id_material).pipe(finalize(() => { this.loadingDetail = false; this.cdr.detectChanges(); })).subscribe({
      next: res => {
        const m = res.data; this.editando = true;
        this.form = { id_material: m.id_material, codigo: m.codigo, nombre_material: m.nombre_material,
          descripcion: m.descripcion || null, id_categoria: m.categoria.id_categoria,
          id_unidad_medida: m.unidad_medida.id_unidad_medida, precio: m.precio,
          caracteristicas: (m.caracteristicas || []).map(c => ({ nombre: c.nombre, valor: c.valor })),
          cantidad_inicial: 0, stock_minimo: m.stock_minimo, fecha_ingreso: '', stock_actual: m.stock_actual };
        this.modal = 'formulario';
        this.cdr.detectChanges();
      }, error: err => this.mostrarError(this.mensajeError(err, 'No se pudo cargar el material.'))
    });
  }

  abrirDetalle(material: Material): void {
    if (this.loadingDetail) return;
    this.loadingDetail = true;
    this.service.obtener(material.id_material).pipe(finalize(() => { this.loadingDetail = false; this.cdr.detectChanges(); })).subscribe({
      next: res => { this.detalle = res.data; this.modal = 'detalle'; this.cdr.detectChanges(); },
      error: err => this.mostrarError(this.mensajeError(err, 'No se pudo cargar el material.'))
    });
  }

  agregarCaracteristica(): void { this.form.caracteristicas.push({ nombre: '', valor: '' }); }
  quitarCaracteristica(index: number): void { this.form.caracteristicas.splice(index, 1); }
  trackCaracteristica(index: number, item: MaterialCaracteristica): number { return index; }

  abrirNuevaCategoria(): void {
    if (this.savingCategory) return;
    this.categoriaError = '';
    this.categoriaForm = { nombre: '', descripcion: '' };
    this.categoriaModalAbierto = true;
  }

  cerrarModalCategoria(): void {
    if (this.savingCategory) return;
    this.categoriaModalAbierto = false;
    this.categoriaError = '';
  }

  guardarCategoria(): void {
    if (this.savingCategory) return;
    const nombre = this.categoriaForm.nombre.trim();
    if (!nombre) { this.categoriaError = 'El nombre de la categoría es obligatorio.'; return; }
    this.savingCategory = true;
    this.categoriaError = '';
    this.cdr.detectChanges();
    this.service.crearCategoria({ nombre, descripcion: this.categoriaForm.descripcion.trim() || null })
      .pipe(finalize(() => { this.savingCategory = false; this.cdr.detectChanges(); })).subscribe({
        next: res => {
          const nueva = res.data;
          this.categorias = [...this.categorias, nueva].sort((a, b) => a.nombre.localeCompare(b.nombre));
          this.form.id_categoria = nueva.id_categoria;
          this.categoriaModalAbierto = false;
          this.mostrarExito('Categoría registrada correctamente.');
          this.cdr.detectChanges();
        },
        error: err => { this.categoriaError = this.mensajeErrorCategoria(err); this.cdr.detectChanges(); }
      });
  }

  private mensajeErrorCategoria(err: any): string {
    if (err?.status === 403) return 'No tienes permisos para crear categorías.';
    if (err?.status === 409) return 'Ya existe una categoría con ese nombre.';
    if (err?.status >= 500) return 'No se pudo completar la operación. Intenta nuevamente.';
    return err?.error?.detail || err?.error?.message || 'No se pudo registrar la categoría.';
  }

  guardar(): void {
    if (this.operacionFormularioActiva) return;
    const validacion = this.validar();
    if (validacion) { this.mostrarError(validacion); return; }
    if (this.editando) this.updatingMaterial = true;
    else this.savingMaterial = true;
    this.cdr.detectChanges();
    const base = { codigo: this.form.codigo.trim(), nombre_material: this.form.nombre_material.trim(),
      descripcion: this.form.descripcion?.trim() || null, id_categoria: +this.form.id_categoria,
      id_unidad_medida: +this.form.id_unidad_medida, precio: this.form.precio === null ? null : +this.form.precio,
      stock_minimo: +this.form.stock_minimo,
      caracteristicas: this.form.caracteristicas.map(c => ({ nombre: c.nombre.trim(), valor: c.valor.trim() })) };
    const request = this.editando && this.form.id_material
      ? this.service.modificar(this.form.id_material, base as MaterialUpdatePayload)
      : this.service.registrar({ ...base, cantidad_inicial: +this.form.cantidad_inicial, fecha_ingreso: this.form.fecha_ingreso } as MaterialCreatePayload);
    request.pipe(finalize(() => { this.liberarOperacionFormulario(); this.cdr.detectChanges(); })).subscribe({
      next: () => {
        this.liberarOperacionFormulario();
        this.modal = null;
        this.form = this.formularioVacio();
        this.mostrarExito(this.editando ? 'Material actualizado correctamente.' : 'Material registrado correctamente.');
        this.cdr.detectChanges();
        this.cargarMateriales();
      },
      error: err => this.mostrarError(this.mensajeError(err, 'No se pudo guardar el material.'))
    });
  }

  get operacionFormularioActiva(): boolean { return this.savingMaterial || this.updatingMaterial; }
  private liberarOperacionFormulario(): void { this.savingMaterial = false; this.updatingMaterial = false; }

  private validar(): string | null {
    if (!this.form.codigo.trim()) return 'El código es obligatorio.';
    if (!this.form.nombre_material.trim()) return 'El nombre es obligatorio.';
    if (!(+this.form.id_categoria > 0)) return 'La categoría es obligatoria.';
    if (!(+this.form.id_unidad_medida > 0)) return 'La unidad de medida es obligatoria.';
    if (!this.editando && (!this.form.fecha_ingreso || Number.isNaN(Date.parse(this.form.fecha_ingreso)))) return 'La fecha de ingreso es obligatoria y debe ser válida.';
    if (!this.editando && +this.form.cantidad_inicial < 0) return 'La cantidad inicial no puede ser negativa.';
    if (+this.form.stock_minimo < 0) return 'El stock mínimo no puede ser negativo.';
    if (this.form.precio !== null && +this.form.precio < 0) return 'El precio no puede ser negativo.';
    if (this.form.caracteristicas.some(c => !c.nombre.trim() || !c.valor.trim())) return 'Cada característica debe tener nombre y valor.';
    const nombres = this.form.caracteristicas.map(c => c.nombre.trim().toLocaleLowerCase());
    if (new Set(nombres).size !== nombres.length) return 'No se permiten características duplicadas.';
    return null;
  }

  confirmarEstado(material: Material): void { this.objetivoEstado = material; this.modal = 'confirmacion'; }
  cambiarEstado(): void {
    if (!this.objetivoEstado || this.changingStatus) return;
    const nuevo: EstadoMaterial = this.objetivoEstado.estado === 'ACTIVO' ? 'INACTIVO' : 'ACTIVO';
    this.changingStatus = true;
    this.service.cambiarEstado(this.objetivoEstado.id_material, nuevo).pipe(finalize(() => { this.changingStatus = false; this.cdr.detectChanges(); })).subscribe({
      next: () => { this.modal = null; this.mostrarExito(nuevo === 'ACTIVO' ? 'Material reactivado correctamente.' : 'Material desactivado correctamente.'); this.cdr.detectChanges(); this.cargarMateriales(); },
      error: err => this.mostrarError(this.mensajeError(err, 'No se pudo cambiar el estado del material.'))
    });
  }

  cerrarModal(): void {
    if (this.operacionFormularioActiva || this.changingStatus || this.categoriaModalAbierto) return;
    this.modal = null; this.detalle = undefined; this.objetivoEstado = undefined; this.error = '';
    if (!this.editando) this.form = this.formularioVacio();
    this.cdr.detectChanges();
  }
  stockEstado(m: Material): 'sin' | 'bajo' | 'normal' { return +m.stock_actual === 0 ? 'sin' : +m.stock_actual <= +m.stock_minimo ? 'bajo' : 'normal'; }

  puedeRegistrar(): boolean { return this.rolGestion(); }
  puedeModificar(): boolean { return this.rolGestion(); }
  puedeCambiarEstado(): boolean { return this.rolGestion(); }
  private rolGestion(): boolean { return ['ADMINISTRADOR', 'ADMINISTRADOR_EMPRESA'].includes(this.auth.obtenerUsuario()?.nombre_rol); }

  private mensajeError(err: any, fallback: string): string {
    if (err?.status === 403) return 'No tienes permisos para realizar esta acción.';
    if (err?.status === 404) return err?.error?.detail || 'Material no encontrado.';
    if (err?.status === 409) return 'Ya existe un material con ese código.';
    if (err?.status >= 500) return 'No se pudo completar la operación. Intenta nuevamente.';
    return err?.error?.detail || err?.error?.message || fallback;
  }
  private mostrarError(mensaje: string): void { this.error = mensaje; setTimeout(() => this.error = '', 6000); }
  private mostrarExito(mensaje: string): void { this.exito = mensaje; setTimeout(() => this.exito = '', 4500); }
}
