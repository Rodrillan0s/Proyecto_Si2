import { Component, OnInit, inject, NgZone, ChangeDetectorRef, PLATFORM_ID } from '@angular/core';
import { CommonModule, isPlatformBrowser } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { CambiarPasswordRequest, PerfilService, PerfilUsuario } from '../../services/perfil';
import { AuthService } from '../../services/auth';

@Component({
  selector: 'app-perfil',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './perfil.html'
})
export class PerfilComponent implements OnInit {
  private perfilService = inject(PerfilService);
  private authService = inject(AuthService);
  private router = inject(Router);
  private ngZone = inject(NgZone);
  private cdr = inject(ChangeDetectorRef);
  private platformId = inject(PLATFORM_ID);

  perfil: PerfilUsuario | null = null;
  perfilForm: any = {}; 
  
  cargando: boolean = true;
  modoEdicion: boolean = false;
  mensaje: { texto: string, tipo: 'exito' | 'error' } | null = null;
  modoOscuro: boolean = false;
  mensajeError: string = '';

  mostrarModalPassword: boolean = false;
  cambiandoPassword: boolean = false;
  errorCambioPassword: string = '';
  mostrarPasswordActual: boolean = false;
  mostrarPasswordNueva: boolean = false;
  mostrarConfirmarPassword: boolean = false;
  passwordForm: CambiarPasswordRequest = this.crearPasswordFormVacio();

  // En perfil.component.ts
  async ngOnInit() {
    this.cargando = true;
    
    // Damos un tiempo mínimo para que la app termine de cargar (fase de hidratación)
    await new Promise(r => setTimeout(r, 300)); 
    
    this.cargarDatosPerfil();
  }

  // --- MÉTODOS DE LA BARRA DE NAVEGACIÓN ---
  alternarModoOscuro() {
    this.modoOscuro = !this.modoOscuro;
    if (this.modoOscuro) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('tema_sistema', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('tema_sistema', 'light');
    }
  }

  navegarA(ruta: string) {
    this.router.navigate([ruta]);
  }

  cerrarSesion() {
    this.authService.cerrarSesion();
    this.router.navigate(['/login']);
  }
  // ----------------------------------------

  /**
   * CU09 - HU-23: Consultar perfil del usuario autenticado.
   * El backend identifica al usuario mediante el token JWT (Bearer).
   * No se pasa ningún ID desde el frontend → no es posible consultar el perfil de otro usuario.
   */
  async cargarDatosPerfil(reintentos = 3) {
    this.cargando = true;
    this.mensajeError = '';
    
    this.perfilService.obtenerPerfil().subscribe({
      next: (res) => {
        this.ngZone.run(() => {
          this.perfil = res.data;
          this.cargando = false;
          this.cdr.detectChanges();
        });
      },
      error: (err) => {
        if (reintentos > 0) {
          // Si falló, esperamos 500ms y reintentamos
          setTimeout(() => this.cargarDatosPerfil(reintentos - 1), 500);
        } else {
          this.ngZone.run(() => {
            // Determinar mensaje de error específico según el tipo de fallo
            if (err.status === 0) {
              this.mensajeError = 'No se pudo conectar con el servidor. Verifica tu conexión a internet.';
            } else if (err.status === 401) {
              this.mensajeError = 'Tu sesión ha expirado o no es válida. Por favor, inicia sesión nuevamente.';
              setTimeout(() => this.router.navigate(['/login']), 2000);
            } else if (err.status === 404) {
              this.mensajeError = 'No se encontró la información de tu perfil en el sistema.';
            } else if (err.status === 500) {
              this.mensajeError = 'Error interno del servidor. Intenta más tarde o contacta al administrador.';
            } else if (err.error?.detail) {
              this.mensajeError = err.error.detail;
            } else {
              this.mensajeError = 'Ocurrió un error inesperado al cargar tu perfil.';
            }
            this.perfil = null;
            this.cargando = false;
            this.cdr.detectChanges();
          });
        }
      }
    });
  }

  activarEdicion() {
    if (this.perfil) {
      this.perfilForm = { 
        ci: this.perfil.ci,
        telefono: this.perfil.telefono,
        correo: this.perfil.correo,
        direccion: this.perfil.direccion,
        id_empresa: this.perfil.id_empresa,
        descripcion_empresa: this.perfil.descripcion_empresa || ''
      };
      this.modoEdicion = true;
    }
  }

  cancelarEdicion() {
    this.modoEdicion = false;
    this.perfilForm = {};
  }

  guardarPerfil() {
    this.cargando = true;
    const payload: any = {
      ci: this.perfilForm.ci,
      telefono: this.perfilForm.telefono,
      correo: this.perfilForm.correo,
      direccion: this.perfilForm.direccion,
      id_empresa: this.perfilForm.id_empresa,
      descripcion_empresa: this.perfilForm.descripcion_empresa
    };

    this.perfilService.actualizarPerfil(payload).subscribe({
      next: (res) => {
        this.ngZone.run(() => {
          if (res.success) {
            this.mostrarMensaje(res.message, 'exito');
            this.modoEdicion = false;
            this.cargarDatosPerfil(); 
          } else {
            this.mostrarMensaje(res.message, 'error');
            this.cargando = false;
          }
          this.cdr.detectChanges();
        });
      },
      error: (err) => {
        this.ngZone.run(() => {
          const detalle = err.error?.detail || 'Error al actualizar el perfil.';
          this.mostrarMensaje(detalle, 'error');
          this.cargando = false;
          this.cdr.detectChanges();
        });
      }
    });
  }

  mostrarMensaje(texto: string, tipo: 'exito' | 'error') {
    this.mensaje = { texto, tipo };
    setTimeout(() => {
      this.mensaje = null;
      this.cdr.detectChanges();
    }, 4000);
  }

  abrirModalPassword() {
    this.limpiarPasswordForm();
    this.mostrarModalPassword = true;
  }

  cerrarModalPassword() {
    if (this.cambiandoPassword) return;

    this.mostrarModalPassword = false;
    this.limpiarPasswordForm();
  }

  cambiarPassword() {
    if (!this.passwordFormValido || this.cambiandoPassword) return;

    this.cambiandoPassword = true;
    this.errorCambioPassword = '';

    const payload: CambiarPasswordRequest = {
      password_actual: this.passwordForm.password_actual,
      password_nueva: this.passwordForm.password_nueva,
      confirmar_password: this.passwordForm.confirmar_password
    };

    this.perfilService.cambiarPassword(payload).subscribe({
      next: (res) => {
        this.ngZone.run(() => {
          this.cambiandoPassword = false;

          if (res.success) {
            this.cerrarModalPassword();
            this.mostrarMensaje('Contraseña actualizada correctamente', 'exito');
          } else {
            this.errorCambioPassword = 'No se pudo actualizar la contraseña. Inténtalo más tarde.';
          }

          this.cdr.detectChanges();
        });
      },
      error: (err) => {
        this.ngZone.run(() => {
          this.errorCambioPassword = this.obtenerMensajeErrorPassword(err);
          this.cambiandoPassword = false;
          this.cdr.detectChanges();
        });
      }
    });
  }

  get requisitosPassword(): { texto: string; cumple: boolean }[] {
    const password = this.passwordForm.password_nueva;

    return [
      { texto: 'Al menos 8 caracteres', cumple: password.length >= 8 },
      { texto: 'Una letra mayúscula', cumple: /[A-Z]/.test(password) },
      { texto: 'Una letra minúscula', cumple: /[a-z]/.test(password) },
      { texto: 'Un número', cumple: /[0-9]/.test(password) },
      { texto: 'Un carácter especial', cumple: /[^A-Za-z0-9\s]/.test(password) }
    ];
  }

  get passwordNuevaSegura(): boolean {
    return this.requisitosPassword.every(requisito => requisito.cumple);
  }

  get passwordsCoinciden(): boolean {
    return this.passwordForm.confirmar_password.length > 0
      && this.passwordForm.password_nueva === this.passwordForm.confirmar_password;
  }

  get passwordFormValido(): boolean {
    return this.passwordForm.password_actual.length > 0
      && this.passwordForm.password_nueva.length > 0
      && this.passwordForm.confirmar_password.length > 0
      && this.passwordNuevaSegura
      && this.passwordsCoinciden;
  }

  private crearPasswordFormVacio(): CambiarPasswordRequest {
    return {
      password_actual: '',
      password_nueva: '',
      confirmar_password: ''
    };
  }

  private limpiarPasswordForm() {
    this.passwordForm = this.crearPasswordFormVacio();
    this.errorCambioPassword = '';
    this.mostrarPasswordActual = false;
    this.mostrarPasswordNueva = false;
    this.mostrarConfirmarPassword = false;
  }

  private obtenerMensajeErrorPassword(err: any): string {
    if (err?.status === 0) {
      return 'No se pudo conectar con el servidor.';
    }

    if (err?.status === 404) {
      return 'No se pudo identificar al usuario.';
    }

    if (err?.status >= 500) {
      return 'No se pudo actualizar la contraseña. Inténtalo más tarde.';
    }

    if (err?.status === 400) {
      const detalle = err?.error?.detail;
      const mensajesPermitidos = [
        'La contraseña actual es incorrecta',
        'Las contraseñas no coinciden',
        'La nueva contraseña no cumple los requisitos de seguridad',
        'Los tres campos de contraseña son obligatorios'
      ];

      return mensajesPermitidos.includes(detalle)
        ? detalle
        : 'Verifica los datos ingresados.';
    }

    return 'No se pudo actualizar la contraseña. Inténtalo más tarde.';
  }
}
