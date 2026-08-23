import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth';

interface RegistroForm {
  ci: string;
  nombre_completo: string;
  nombre_usuario: string;
  password: string;
  confirmar_password: string;
  telefono: string;
  correo: string;
  direccion: string;
  nombre_empresa: string;
}

@Component({
  selector: 'app-registro',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './registro.html',
  styleUrl: './registro.css'
})
export class RegistroComponent {
  private authService = inject(AuthService);
  private router = inject(Router);

  formulario: RegistroForm = {
    ci: '',
    nombre_completo: '',
    nombre_usuario: '',
    password: '',
    confirmar_password: '',
    telefono: '',
    correo: '',
    direccion: '',
    nombre_empresa: ''
  };
  mensajeError = '';
  cargando = false;

  registrar() {
    this.mensajeError = '';
    if (!this.formulario.ci || !this.formulario.nombre_completo || !this.formulario.nombre_usuario || !this.formulario.password || !this.formulario.correo) {
      this.mensajeError = 'Complete los campos obligatorios.';
      return;
    }
    if (this.formulario.password.length < 6) {
      this.mensajeError = 'La contraseña debe tener al menos 6 caracteres.';
      return;
    }
    if (this.formulario.password !== this.formulario.confirmar_password) {
      this.mensajeError = 'Las contraseñas no coinciden.';
      return;
    }

    this.cargando = true;
    this.authService.registrarUsuario({
      ci: this.formulario.ci,
      nombre_completo: this.formulario.nombre_completo,
      nombre_usuario: this.formulario.nombre_usuario,
      password: this.formulario.password,
      telefono: this.formulario.telefono,
      correo: this.formulario.correo,
      direccion: this.formulario.direccion,
      nombre_empresa: this.formulario.nombre_empresa
    }).subscribe({
      next: () => this.router.navigate(['/login'], { queryParams: { registrado: '1' } }),
      error: (error) => {
        this.mensajeError = error.error?.detail || 'No se pudo crear la cuenta.';
        this.cargando = false;
      }
    });
  }

  volverAlLogin() {
    this.router.navigate(['/login']);
  }
}
