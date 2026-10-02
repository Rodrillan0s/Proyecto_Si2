import { Component, inject, OnInit, PLATFORM_ID, ChangeDetectorRef, HostListener, NgZone } from '@angular/core';
import { CommonModule, isPlatformBrowser } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth';
import { PasswordRecoveryService } from '../../services/password-recovery';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule], // Necesario para ngIf y ngModel
  templateUrl: './login.html',
  styleUrl: './login.css'
})
export class LoginComponent implements OnInit {
  
  // Inyección de dependencias
  private authService = inject(AuthService);
  private passwordRecoveryService = inject(PasswordRecoveryService);
  private router = inject(Router);
  private platformId = inject(PLATFORM_ID);
  private cdr = inject(ChangeDetectorRef);
  private ngZone = inject(NgZone);

  // Variables de estado
  credenciales = {
    ci: '',
    password: ''
  };
  mensajeError = '';
  cargando = false;
  modoOscuro = false;

  mostrarModalRecuperacion = false;
  pasoRecuperacion: 1 | 2 | 3 = 1;
  correoRecuperacion = '';
  codigoRecuperacion = '';
  solicitudId: string | null = null;
  resetToken: string | null = null;
  passwordNueva = '';
  confirmarPassword = '';
  mostrandoPasswordNueva = false;
  mostrandoConfirmacion = false;
  procesandoRecuperacion = false;
  errorRecuperacion = '';
  mensajeRecuperacion = '';
  mensajeExitoRecuperacion = '';

  ngOnInit() {
    if (isPlatformBrowser(this.platformId)) {
      if (localStorage.getItem('tema_sistema') === 'dark') {
        this.modoOscuro = true;
        document.documentElement.classList.add('dark');
      }
    }
  }

  alternarTema() {
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

  crearUsuario() {
    this.router.navigate(['/registro']);
  }

  abrirModalRecuperacion() {
    this.limpiarEstadoRecuperacion();
    this.mensajeExitoRecuperacion = '';
    this.mostrarModalRecuperacion = true;
  }

  cerrarModalRecuperacion() {
    if (this.procesandoRecuperacion) return;

    this.mostrarModalRecuperacion = false;
    this.limpiarEstadoRecuperacion();
  }

  @HostListener('document:keydown.escape')
  cerrarModalRecuperacionConEscape() {
    if (this.mostrarModalRecuperacion && !this.procesandoRecuperacion) {
      this.cerrarModalRecuperacion();
    }
  }

  get tituloPasoRecuperacion(): string {
    if (this.pasoRecuperacion === 2) return 'Código de verificación';
    if (this.pasoRecuperacion === 3) return 'Nueva contraseña';
    return 'Recuperar contraseña';
  }

  get correoRecuperacionValido(): boolean {
    const correo = this.correoRecuperacion.trim();
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(correo);
  }

  get codigoRecuperacionValido(): boolean {
    return /^\d{6}$/.test(this.codigoRecuperacion);
  }

  get requisitosPasswordRecuperacion(): { texto: string; cumple: boolean }[] {
    return [
      { texto: 'Al menos 8 caracteres', cumple: this.passwordNueva.length >= 8 },
      { texto: 'Una letra mayúscula', cumple: /[A-Z]/.test(this.passwordNueva) },
      { texto: 'Una letra minúscula', cumple: /[a-z]/.test(this.passwordNueva) },
      { texto: 'Un número', cumple: /[0-9]/.test(this.passwordNueva) },
      { texto: 'Un carácter especial', cumple: /[^A-Za-z0-9\s]/.test(this.passwordNueva) }
    ];
  }

  get passwordRecuperacionSegura(): boolean {
    return this.requisitosPasswordRecuperacion.every(requisito => requisito.cumple);
  }

  get passwordsRecuperacionCoinciden(): boolean {
    return this.confirmarPassword.length > 0
      && this.passwordNueva === this.confirmarPassword;
  }

  get formularioPasswordRecuperacionValido(): boolean {
    return this.passwordNueva.length > 0
      && this.confirmarPassword.length > 0
      && this.passwordRecuperacionSegura
      && this.passwordsRecuperacionCoinciden;
  }

  actualizarCodigoRecuperacion(valor: string) {
    this.codigoRecuperacion = String(valor ?? '')
      .replace(/\D/g, '')
      .slice(0, 6);
  }

  solicitarRecuperacion() {
    if (this.procesandoRecuperacion) return;

    const correo = this.correoRecuperacion.trim();
    if (!this.correoRecuperacionValido) {
      this.errorRecuperacion = 'Ingresa un correo electrónico válido.';
      return;
    }

    this.procesandoRecuperacion = true;
    this.errorRecuperacion = '';
    this.mensajeRecuperacion = '';

    this.passwordRecoveryService.solicitarRecuperacion(correo).subscribe({
      next: (respuesta) => {
        this.ngZone.run(() => {
          this.procesandoRecuperacion = false;

          if (respuesta.success && respuesta.solicitud_id) {
            this.solicitudId = respuesta.solicitud_id;
            this.mensajeRecuperacion = respuesta.message;
            this.pasoRecuperacion = 2;
          } else {
            this.errorRecuperacion = 'No se pudo procesar la solicitud. Inténtalo más tarde.';
          }

          this.cdr.detectChanges();
        });
      },
      error: (errorHttp) => {
        this.ngZone.run(() => {
          this.procesandoRecuperacion = false;
          this.errorRecuperacion = this.obtenerMensajeErrorRecuperacion(errorHttp, 1);
          this.cdr.detectChanges();
        });
      }
    });
  }

  verificarCodigoRecuperacion() {
    if (this.procesandoRecuperacion || !this.codigoRecuperacionValido) return;

    if (!this.solicitudId) {
      this.errorRecuperacion = 'El código es inválido o ha expirado.';
      return;
    }

    this.procesandoRecuperacion = true;
    this.errorRecuperacion = '';

    this.passwordRecoveryService.verificarCodigo(
      this.solicitudId,
      this.codigoRecuperacion
    ).subscribe({
      next: (respuesta) => {
        this.ngZone.run(() => {
          this.procesandoRecuperacion = false;

          if (respuesta.success && respuesta.reset_token) {
            this.resetToken = respuesta.reset_token;
            this.codigoRecuperacion = '';
            this.mensajeRecuperacion = '';
            this.pasoRecuperacion = 3;
          } else {
            this.errorRecuperacion = 'El código es inválido o ha expirado.';
          }

          this.cdr.detectChanges();
        });
      },
      error: (errorHttp) => {
        this.ngZone.run(() => {
          this.procesandoRecuperacion = false;
          this.errorRecuperacion = this.obtenerMensajeErrorRecuperacion(errorHttp, 2);
          this.cdr.detectChanges();
        });
      }
    });
  }

  restablecerPassword() {
    if (this.procesandoRecuperacion || !this.formularioPasswordRecuperacionValido) return;

    if (!this.solicitudId || !this.resetToken) {
      this.errorRecuperacion = 'La solicitud de restablecimiento es inválida o ha expirado.';
      return;
    }

    this.procesandoRecuperacion = true;
    this.errorRecuperacion = '';

    this.passwordRecoveryService.restablecerPassword(
      this.solicitudId,
      this.resetToken,
      this.passwordNueva,
      this.confirmarPassword
    ).subscribe({
      next: (respuesta) => {
        this.ngZone.run(() => {
          this.procesandoRecuperacion = false;

          if (respuesta.success) {
            this.mostrarModalRecuperacion = false;
            this.limpiarEstadoRecuperacion();
            this.mensajeExitoRecuperacion = 'Contraseña restablecida correctamente. Ya puedes iniciar sesión.';
          } else {
            this.errorRecuperacion = 'No se pudo restablecer la contraseña. Inténtalo más tarde.';
          }

          this.cdr.detectChanges();
        });
      },
      error: (errorHttp) => {
        this.ngZone.run(() => {
          this.procesandoRecuperacion = false;
          this.errorRecuperacion = this.obtenerMensajeErrorRecuperacion(errorHttp, 3);
          this.cdr.detectChanges();
        });
      }
    });
  }

  private limpiarEstadoRecuperacion() {
    this.pasoRecuperacion = 1;
    this.correoRecuperacion = '';
    this.codigoRecuperacion = '';
    this.solicitudId = null;
    this.resetToken = null;
    this.passwordNueva = '';
    this.confirmarPassword = '';
    this.mostrandoPasswordNueva = false;
    this.mostrandoConfirmacion = false;
    this.procesandoRecuperacion = false;
    this.errorRecuperacion = '';
    this.mensajeRecuperacion = '';
  }

  private obtenerMensajeErrorRecuperacion(errorHttp: any, paso: 1 | 2 | 3): string {
    if (errorHttp?.status === 0) {
      return 'No se pudo conectar con el servidor.';
    }

    if (paso === 1) {
      if (errorHttp?.status === 422) {
        return 'Ingresa un correo electrónico válido.';
      }
      return 'No se pudo procesar la solicitud. Inténtalo más tarde.';
    }

    if (paso === 2) {
      if (errorHttp?.status === 400) {
        return 'El código es inválido o ha expirado.';
      }
      return 'No se pudo verificar el código. Inténtalo más tarde.';
    }

    if (errorHttp?.status === 400) {
      return 'La solicitud de restablecimiento es inválida o ha expirado.';
    }
    return 'No se pudo restablecer la contraseña. Inténtalo más tarde.';
  }

  // Función principal
  hacerLogin() {
    // 1. Validar que no haya campos vacíos
    if (!this.credenciales.ci || !this.credenciales.password) {
      this.mensajeError = 'Por favor complete todos los campos.';
      return;
    }

    this.cargando = true;
    this.mensajeError = '';
    this.cdr.detectChanges();

    // 2. Llamar al servicio
    this.authService.iniciarSesion(this.credenciales).subscribe({
      next: (respuesta) => {
        this.ngZone.run(() => {
          console.log('Login exitoso next:', respuesta);
          if (respuesta.success) {
            // 3. Guardar sesión y redirigir a /panel
            this.authService.guardarSesion(respuesta.token, respuesta.usuario);
            this.cargando = false;
            const esCliente = respuesta.usuario?.nombre_rol === 'CLIENTE';
            this.router.navigate([esCliente ? '/main_cliente' : '/panel']);
          }
          this.cdr.detectChanges();
        });
      },
      error: (errorHttp) => {
        this.ngZone.run(() => {
          console.error('ERROR EN LOGIN SUB:', errorHttp);
          this.cargando = false;
          
          // Manejar estructura de error en Angular
          let errorMsg = 'Error de conexión con el servidor.';
          if (errorHttp.error) {
            if (typeof errorHttp.error === 'string') {
              try {
                const parsed = JSON.parse(errorHttp.error);
                errorMsg = parsed.detail || errorMsg;
              } catch (e) {
                errorMsg = errorHttp.error;
              }
            } else if (errorHttp.error.detail) {
              errorMsg = errorHttp.error.detail;
            } else if (errorHttp.message) {
              errorMsg = errorHttp.message;
            }
          }
          
          this.mensajeError = errorMsg;
          console.log('mensajeError establecido en:', this.mensajeError);
          this.cdr.detectChanges();
        });
      }
    });
  }
}
