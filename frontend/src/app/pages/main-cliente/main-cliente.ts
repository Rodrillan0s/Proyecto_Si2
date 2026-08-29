import { Component, OnInit, inject, ChangeDetectorRef, NgZone } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth';
import { ProyectosService, Proyecto } from '../../services/proyectos';

@Component({
  selector: 'app-main-cliente',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './main-cliente.html',
  styleUrl: './main-cliente.css'
})
export class MainClienteComponent implements OnInit {
  private authService = inject(AuthService);
  private proyectosService = inject(ProyectosService);
  private router = inject(Router);
  private cdr = inject(ChangeDetectorRef);
  private ngZone = inject(NgZone);

  usuarioActual: any = null;
  modoOscuro: boolean = false;
  proyectos: Proyecto[] = [];
  cargando: boolean = false;

  totalProyectos = 0;
  proyectosEnEjecucion = 0;
  proyectosFinalizados = 0;

  ngOnInit() {
    this.usuarioActual = this.authService.obtenerUsuario();
    if (!this.usuarioActual) {
      this.cerrarSesion();
      return;
    }

    if (localStorage.getItem('tema_sistema') === 'dark') {
      this.modoOscuro = true;
      document.documentElement.classList.add('dark');
    }

    this.cargarProyectosCliente();
  }

  cargarProyectosCliente() {
    this.cargando = true;
    this.proyectosService.listarProyectos().subscribe({
      next: (res) => {
        this.ngZone.run(() => {
          if (res && res.success) {
            // Filtrar proyectos correspondientes a este cliente
            const idUsuario = this.usuarioActual?.nro_usuario;
            this.proyectos = (res.data || []).filter(p => p.id_cliente === idUsuario || !p.id_cliente);
            this.totalProyectos = this.proyectos.length;
            this.proyectosEnEjecucion = this.proyectos.filter(p => p.estado_obra === 'ACTIVO').length;
            this.proyectosFinalizados = this.proyectos.filter(p => p.estado_obra === 'FINALIZADO').length;
          }
          this.cargando = false;
          this.cdr.detectChanges();
        });
      },
      error: () => {
        this.ngZone.run(() => {
          this.cargando = false;
          this.cdr.detectChanges();
        });
      }
    });
  }

  alternarModoOscuro() {
    this.modoOscuro = !this.modoOscuro;
    if (this.modoOscuro) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('tema_sistema', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('tema_sistema', 'light');
    }
    this.cdr.detectChanges();
  }

  cerrarSesion(): void {
    this.authService.cerrarSesion();
    this.router.navigate(['/login']);
  }
}
