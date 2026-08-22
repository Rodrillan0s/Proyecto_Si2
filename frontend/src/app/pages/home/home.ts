import { Component, OnInit, inject,PLATFORM_ID } from '@angular/core';
import { CommonModule,isPlatformBrowser } from '@angular/common';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './home.html',
  styleUrl: './home.css'
})
export class HomeComponent implements OnInit {
  
  private authService = inject(AuthService);
  private router = inject(Router);
  private platformId = inject(PLATFORM_ID);

  usuarioActual: any = null;
  modoOscuro: boolean = false;

  //METODO AL INICIAR LA PAGINA
  ngOnInit() {
    //VALIDAR QUE SE ESTE EJECUTANDO EN NAVEGADOR
    if (isPlatformBrowser(this.platformId)) {
      this.usuarioActual = this.authService.obtenerUsuario();
      
      // Si el token expiró, limpiamos la sesión local
      if (this.usuarioActual && this.authService.tokenExpirado()) {
        this.authService.cerrarSesion();
        this.usuarioActual = null;
      }

      // VERIFICAR PREFERENCIA DE MODO OSCURO
      if (localStorage.getItem('tema_sistema') === 'dark') {
        this.modoOscuro = true;
        document.documentElement.classList.add('dark');
      }
    }
  }

  //METODO PARA ALTERNAR EL MODO OSCURO
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

  //METODO PARA NAVEGAR A ALGUN MODULO
  navegarA(ruta: string) {
    this.router.navigate([ruta]);
  }

  //METODO PARA CERRAR SESION
  cerrarSesion() {
    this.authService.cerrarSesion();
    this.router.navigate(['/login']);
  }
}