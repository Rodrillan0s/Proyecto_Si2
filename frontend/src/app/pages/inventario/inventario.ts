import { CommonModule } from '@angular/common';
import { ChangeDetectorRef, Component, DestroyRef, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { Subject, debounceTime, distinctUntilChanged } from 'rxjs';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';

import { AuthService } from '../../services/auth';
import { Empresa, EmpresaService } from '../../services/empresa';
import {
  AjusteStockPayload,
  InventarioService,
  ItemInventario,
  KpisInventario,
  MovimientoAlmacen
} from '../../services/inventario.service';
import { ComprasComponent } from '../compras/compras';

type TabInventario = 'stock' | 'movimientos' | 'compras';

@Component({
  selector: 'app-inventario',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, ComprasComponent],
  templateUrl: './inventario.html',
  styleUrl: './inventario.css'
})
export class InventarioComponent implements OnInit {
  private inventarioSvc = inject(InventarioService);
  private empresaSvc = inject(EmpresaService);
  private auth = inject(AuthService);
  private cdr = inject(ChangeDetectorRef);
  private destroyRef = inject(DestroyRef);
  private busqueda$ = new Subject<string>();

  tabActiva: TabInventario = 'stock';

  // Estados de carga
  cargandoStock = false;
  cargandoKpis = false;
  cargandoMovimientos = false;
  guardandoAjuste = false;

  // Datos
  stockItems: ItemInventario[] = [];
  totalStock = 0;
  paginaStock = 1;
  limiteStock = 20;

  movimientos: MovimientoAlmacen[] = [];
  totalMovimientos = 0;
  paginaMovimientos = 1;
  limiteMovimientos = 20;

  kpis: KpisInventario = {
    total_materiales: 0,
    total_con_stock: 0,
    total_sin_stock: 0,
    total_stock_bajo: 0,
    valor_total_inventario: 0,
    total_movimientos_mes: 0
  };

  // Filtros Stock
  filtroTexto = '';
  filtroEstadoStock = '';

  // Filtros Movimientos
  filtroTipoMovimiento = '';

  // Multi-tenant
  empresaActual: Empresa | null = null;
  esAdminGlobal = false;

  // Modal Ajuste
  modalAjusteAbierto = false;
  materialSeleccionado: ItemInventario | null = null;
  formAjuste: {
    tipo_movimiento: 'ENTRADA_AJUSTE' | 'SALIDA_AJUSTE' | 'AJUSTE_INVENTARIO';
    cantidad: number;
    stock_minimo: number | null;
    observaciones: string;
  } = {
    tipo_movimiento: 'ENTRADA_AJUSTE',
    cantidad: 1,
    stock_minimo: null,
    observaciones: ''
  };

  // Notificaciones / Mensajes
  mensajeAlerta: { tipo: 'success' | 'error'; texto: string } | null = null;

  ngOnInit(): void {
    this.esAdminGlobal = this.auth.esVistaGlobal();
    this.empresaActual = this.auth.obtenerEmpresaActiva();

    this.auth.empresaActiva$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((empresa: Empresa | null) => {
        this.empresaActual = empresa;
        this.paginaStock = 1;
        this.paginaMovimientos = 1;
        this.cargarTodo();
      });

    this.busqueda$
      .pipe(debounceTime(350), distinctUntilChanged(), takeUntilDestroyed(this.destroyRef))
      .subscribe((texto) => {
        this.filtroTexto = texto;
        this.paginaStock = 1;
        this.cargarStock();
      });

    this.cargarTodo();
  }

  get idEmpresaFiltro(): number | undefined {
    return this.auth.obtenerIdEmpresaActiva() || undefined;
  }

  cambiarTab(tab: TabInventario): void {
    this.tabActiva = tab;
    if (tab === 'movimientos' && this.movimientos.length === 0) {
      this.cargarMovimientos();
    }
  }

  onBuscarInput(e: Event): void {
    const val = (e.target as HTMLInputElement).value;
    this.busqueda$.next(val);
  }

  cambiarFiltroEstado(estado: string): void {
    this.filtroEstadoStock = estado;
    this.paginaStock = 1;
    this.cargarStock();
  }

  cambiarFiltroTipoMov(tipo: string): void {
    this.filtroTipoMovimiento = tipo;
    this.paginaMovimientos = 1;
    this.cargarMovimientos();
  }

  cargarTodo(): void {
    this.cargarKpis();
    this.cargarStock();
    if (this.tabActiva === 'movimientos') {
      this.cargarMovimientos();
    }
  }

  cargarKpis(): void {
    this.cargandoKpis = true;
    this.inventarioSvc.obtenerKpis(this.idEmpresaFiltro).subscribe({
      next: (res) => {
        if (res.success && res.data) {
          this.kpis = res.data;
        }
        this.cargandoKpis = false;
        this.cdr.markForCheck();
      },
      error: () => {
        this.cargandoKpis = false;
        this.cdr.markForCheck();
      }
    });
  }

  cargarStock(): void {
    this.cargandoStock = true;
    this.inventarioSvc
      .listarStock({
        q: this.filtroTexto,
        estado_stock: this.filtroEstadoStock,
        page: this.paginaStock,
        limit: this.limiteStock,
        id_empresa: this.idEmpresaFiltro
      })
      .subscribe({
        next: (res) => {
          this.stockItems = res.data || [];
          this.totalStock = res.total || 0;
          this.cargandoStock = false;
          this.cdr.markForCheck();
        },
        error: (err) => {
          this.cargandoStock = false;
          this.mostrarNotificacion('error', err.error?.detail || 'Error al cargar existencias de inventario');
          this.cdr.markForCheck();
        }
      });
  }

  cargarMovimientos(): void {
    this.cargandoMovimientos = true;
    this.inventarioSvc
      .listarMovimientos({
        tipo_movimiento: this.filtroTipoMovimiento,
        page: this.paginaMovimientos,
        limit: this.limiteMovimientos,
        id_empresa: this.idEmpresaFiltro
      })
      .subscribe({
        next: (res) => {
          this.movimientos = res.data || [];
          this.totalMovimientos = res.total || 0;
          this.cargandoMovimientos = false;
          this.cdr.markForCheck();
        },
        error: (err) => {
          this.cargandoMovimientos = false;
          this.mostrarNotificacion('error', err.error?.detail || 'Error al consultar movimientos de almacén');
          this.cdr.markForCheck();
        }
      });
  }

  // Paginación Stock
  get totalPaginasStock(): number {
    return Math.ceil(this.totalStock / this.limiteStock) || 1;
  }

  cambiarPaginaStock(p: number): void {
    if (p < 1 || p > this.totalPaginasStock) return;
    this.paginaStock = p;
    this.cargarStock();
  }

  // Paginación Movimientos
  get totalPaginasMov(): number {
    return Math.ceil(this.totalMovimientos / this.limiteMovimientos) || 1;
  }

  cambiarPaginaMov(p: number): void {
    if (p < 1 || p > this.totalPaginasMov) return;
    this.paginaMovimientos = p;
    this.cargarMovimientos();
  }

  // Modal Ajuste
  abrirModalAjuste(item: ItemInventario): void {
    this.materialSeleccionado = item;
    this.formAjuste = {
      tipo_movimiento: 'ENTRADA_AJUSTE',
      cantidad: 1,
      stock_minimo: item.stock_minimo || null,
      observaciones: ''
    };
    this.modalAjusteAbierto = true;
  }

  cerrarModalAjuste(): void {
    this.modalAjusteAbierto = false;
    this.materialSeleccionado = null;
  }

  guardarAjuste(): void {
    if (!this.materialSeleccionado) return;
    if (!this.formAjuste.observaciones.trim()) {
      this.mostrarNotificacion('error', 'Por favor ingresa un motivo u observación para el ajuste');
      return;
    }
    if (this.formAjuste.cantidad <= 0) {
      this.mostrarNotificacion('error', 'La cantidad del ajuste debe ser mayor a cero');
      return;
    }

    this.guardandoAjuste = true;
    const payload: AjusteStockPayload = {
      id_empresa: this.idEmpresaFiltro,
      id_material: this.materialSeleccionado.id_material,
      tipo_movimiento: this.formAjuste.tipo_movimiento,
      cantidad: this.formAjuste.cantidad,
      observaciones: this.formAjuste.observaciones.trim(),
      stock_minimo: this.formAjuste.stock_minimo
    };

    this.inventarioSvc.registrarAjuste(payload).subscribe({
      next: (res) => {
        this.guardandoAjuste = false;
        this.mostrarNotificacion('success', res.message || 'Ajuste de inventario guardado correctamente');
        this.cerrarModalAjuste();
        this.cargarTodo();
      },
      error: (err) => {
        this.guardandoAjuste = false;
        this.mostrarNotificacion('error', err.error?.detail || 'Error al registrar el ajuste de inventario');
        this.cdr.markForCheck();
      }
    });
  }

  mostrarNotificacion(tipo: 'success' | 'error', texto: string): void {
    this.mensajeAlerta = { tipo, texto };
    this.cdr.markForCheck();
    setTimeout(() => {
      if (this.mensajeAlerta?.texto === texto) {
        this.mensajeAlerta = null;
        this.cdr.markForCheck();
      }
    }, 4500);
  }

  badgeClase(estado: string): string {
    switch (estado) {
      case 'EN_STOCK':
        return 'badge-en-stock';
      case 'STOCK_BAJO':
        return 'badge-stock-bajo';
      case 'SIN_STOCK':
        return 'badge-sin-stock';
      default:
        return 'badge-default';
    }
  }

  formatoBadge(estado: string): string {
    switch (estado) {
      case 'EN_STOCK':
        return 'En Stock';
      case 'STOCK_BAJO':
        return 'Stock Bajo';
      case 'SIN_STOCK':
        return 'Sin Stock';
      default:
        return estado;
    }
  }

  tipoMovBadge(tipo: string): { label: string; clase: string } {
    if (tipo.startsWith('ENTRADA')) {
      return { label: tipo.replace('_', ' '), clase: 'mov-entrada' };
    }
    if (tipo.startsWith('SALIDA')) {
      return { label: tipo.replace('_', ' '), clase: 'mov-salida' };
    }
    return { label: tipo, clase: 'mov-ajuste' };
  }
}
