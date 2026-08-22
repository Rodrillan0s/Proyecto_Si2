import { Component, OnInit, inject, PLATFORM_ID, ChangeDetectorRef, NgZone } from '@angular/core';
import { CommonModule, isPlatformBrowser } from '@angular/common';
import { Router, ActivatedRoute } from '@angular/router';
import { AuthService } from '../../services/auth';

@Component({
  selector: 'app-panel',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './panel.html',
  styleUrl: './panel.css'
})
export class PanelComponent implements OnInit {
  
  private authService = inject(AuthService);
  private router = inject(Router);
  private route = inject(ActivatedRoute);
  private platformId = inject(PLATFORM_ID);
  private cdr = inject(ChangeDetectorRef);
  private ngZone = inject(NgZone);

  usuarioActual: any = null;
  modoOscuro: boolean = false;
  
  // Variables del panel
  vistaActiva: string = 'resumen';
  dispositivosConocidos: any[] = [];

  ngOnInit() {
    if (isPlatformBrowser(this.platformId)) {
      this.usuarioActual = this.authService.obtenerUsuario();
      
      // Si el token expiró, lo enviamos al login
      if (!this.usuarioActual || this.authService.tokenExpirado()) {
        this.authService.cerrarSesion();
        this.router.navigate(['/login']);
        return;
      }

      // Escuchar query params para cambiar de pestaña reactivamente
      this.route.queryParams.subscribe(params => {
        this.ngZone.run(() => {
          if (params['tab']) {
            this.vistaActiva = params['tab'];
          } else {
            this.vistaActiva = 'resumen';
          }
          this.cdr.detectChanges();
        });
      });

      // Generar mockup de dispositivo en base al navegador actual
      const userAgent = navigator.userAgent;
      let browserName = 'Navegador Chrome (Windows)';
      if (userAgent.indexOf('Safari') > -1 && userAgent.indexOf('Chrome') === -1) {
        browserName = 'Navegador Safari (macOS)';
      } else if (userAgent.indexOf('Firefox') > -1) {
        browserName = 'Navegador Firefox (Linux)';
      } else if (userAgent.indexOf('Brave') > -1 || userAgent.indexOf('Chromium') > -1) {
        browserName = 'Navegador Brave/Chromium (Windows)';
      }
      
      this.dispositivosConocidos = [
        {
          hash: 'sha256:8bc57e5e7decf6d0d21051515f45851458e0a3592bc1ff4b98fae85295c52c502f6b',
          navegador: browserName,
          fecha: new Date()
        }
      ];

      // VERIFICAR PREFERENCIA DE MODO OSCURO
      if (localStorage.getItem('tema_sistema') === 'dark') {
        this.modoOscuro = true;
        document.documentElement.classList.add('dark');
      }
      this.cdr.detectChanges();
    }
  }

  // METODO PARA ALTERNAR EL MODO OSCURO
  alternarModoOscuro() {
    this.ngZone.run(() => {
      this.modoOscuro = !this.modoOscuro;
      if (this.modoOscuro) {
        document.documentElement.classList.add('dark');
        localStorage.setItem('tema_sistema', 'dark');
      } else {
        document.documentElement.classList.remove('dark');
        localStorage.setItem('tema_sistema', 'light');
      }
      this.cdr.detectChanges();
    });
  }
}