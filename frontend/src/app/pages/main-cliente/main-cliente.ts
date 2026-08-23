import { Component, inject } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth';

@Component({
  selector: 'app-main-cliente',
  standalone: true,
  templateUrl: './main-cliente.html',
  styleUrl: './main-cliente.css'
})
export class MainClienteComponent {
  private authService = inject(AuthService);
  private router = inject(Router);

  cerrarSesion(): void {
    this.authService.cerrarSesion();
    this.router.navigate(['/login']);
  }
}
