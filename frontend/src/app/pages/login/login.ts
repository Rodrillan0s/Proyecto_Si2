import { Component, inject, OnInit, PLATFORM_ID, ChangeDetectorRef, NgZone } from '@angular/core';
import { CommonModule, isPlatformBrowser } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth';

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
            this.router.navigate(['/panel']); 
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