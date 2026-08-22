import { Component, inject, OnInit, PLATFORM_ID } from '@angular/core';
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

    // 2. Llamar al servicio
    this.authService.iniciarSesion(this.credenciales).subscribe({
      next: (respuesta) => {
        if (respuesta.success) {
          // 3. Guardar sesión y redirigir
          this.authService.guardarSesion(respuesta.token, respuesta.usuario);
          this.cargando = false;
          this.router.navigate(['/']); 
        }
      },
      error: (errorHttp) => {
        // 4. Capturar errores del backend (ej: 401 Unauthorized)
        this.cargando = false;
        this.mensajeError = errorHttp.error?.detail || 'Error de conexión con el servidor.';
      }
    });
  }
}