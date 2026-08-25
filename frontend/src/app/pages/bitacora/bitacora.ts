import { ChangeDetectorRef, Component, OnInit, inject, PLATFORM_ID } from '@angular/core';
import { CommonModule, isPlatformBrowser } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { AuthService } from '../../services/auth';
import {
  BitacoraService,
  PaginacionBitacora,
  RegistroBitacora
} from '../../services/bitacora.service';

@Component({
  selector: 'app-bitacora',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './bitacora.html'
})
export class BitacoraComponent implements OnInit {

  private authService = inject(AuthService);
  private bitacoraService = inject(BitacoraService);
  private router = inject(Router);
  private platformId = inject(PLATFORM_ID);
  private cdr = inject(ChangeDetectorRef);

  usuarioActual: any = null;
  modoOscuro: boolean = false;

  fecha: string = '';
  usuario: string = '';
  accion: string = '';
  registros: RegistroBitacora[] = [];
  pagination: PaginacionBitacora = { page: 1, limit: 20, total: 0, total_pages: 0 };
  loading: boolean = false;
  error: string = '';

  ngOnInit(): void {
    if (isPlatformBrowser(this.platformId)) {
      this.usuarioActual = this.authService.obtenerUsuario();

      if (!this.usuarioActual || this.authService.tokenExpirado()) {
        this.cerrarSesion();
        return;
      }

      if (localStorage.getItem('tema_sistema') === 'dark') {
        this.modoOscuro = true;
        document.documentElement.classList.add('dark');
      }

      void this.cargarBitacora();
    }
  }

  async cargarBitacora(): Promise<void> {
    const fecha = this.fecha.trim();

    if (!this.fechaValida(fecha)) {
      this.loading = false;
      this.error = 'Seleccione una fecha válida.';
      return;
    }

    this.loading = true;
    this.error = '';

    try {
      const respuesta = await firstValueFrom(
        this.bitacoraService.obtenerBitacora({
          fecha,
          usuario: this.usuario.trim(),
          accion: this.accion.trim(),
          page: this.pagination.page,
          limit: this.pagination.limit
        })
      );

      this.registros = respuesta.data ?? [];
      this.pagination = {
        page: respuesta.pagination?.page ?? 1,
        limit: respuesta.pagination?.limit ?? 20,
        total: respuesta.pagination?.total ?? 0,
        total_pages: respuesta.pagination?.total_pages ?? 0
      };
    } catch (err: unknown) {
      console.error('Error consultando bitácora:', err);

      this.registros = [];
      this.pagination = {
        page: this.pagination.page,
        limit: this.pagination.limit,
        total: 0,
        total_pages: 0
      };
      this.error = this.obtenerMensajeError(err);
    } finally {
      this.loading = false;
      this.cdr.detectChanges();
    }
  }

  buscar(): void {
    if (this.loading) return;

    this.pagination.page = 1;
    void this.cargarBitacora();
  }

  limpiarFiltros(): void {
    if (this.loading) return;

    this.fecha = '';
    this.usuario = '';
    this.accion = '';
    this.pagination.page = 1;
    void this.cargarBitacora();
  }

  cambiarPagina(page: number): void {
    if (this.loading || page < 1 || page > this.pagination.total_pages || page === this.pagination.page) {
      return;
    }

    this.pagination.page = page;
    void this.cargarBitacora();
  }

  alternarModoOscuro(): void {
    this.modoOscuro = !this.modoOscuro;

    if (this.modoOscuro) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('tema_sistema', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('tema_sistema', 'light');
    }
  }

  navegarA(ruta: string): void {
    this.router.navigate([ruta]);
  }

  cerrarSesion(): void {
    this.authService.cerrarSesion();
    this.router.navigate(['/login']);
  }

  trackByRegistro(index: number, item: RegistroBitacora): string {
    return `${item.id_bitacora}-${index}`;
  }

  private fechaValida(fecha: string): boolean {
    if (!fecha) return true;

    const coincidencia = /^(\d{4})-(\d{2})-(\d{2})$/.exec(fecha);
    if (!coincidencia) return false;

    const anio = Number(coincidencia[1]);
    const mes = Number(coincidencia[2]);
    const dia = Number(coincidencia[3]);

    if (anio < 2000 || anio > 2100) return false;

    const fechaUtc = new Date(Date.UTC(anio, mes - 1, dia));
    return fechaUtc.getUTCFullYear() === anio
      && fechaUtc.getUTCMonth() === mes - 1
      && fechaUtc.getUTCDate() === dia;
  }

  private obtenerMensajeError(err: unknown): string {
    const errorHttp = err as { status?: number; error?: { detail?: unknown } };
    const detalle = errorHttp?.error?.detail;

    return errorHttp?.status === 400 && typeof detalle === 'string' && detalle.trim()
      ? detalle
      : 'No fue posible cargar la bitácora.';
  }
}
