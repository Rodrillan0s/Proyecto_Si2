import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../environments/environment';


export interface SolicitarRecuperacionRequest {
  correo: string;
}

export interface SolicitarRecuperacionResponse {
  success: boolean;
  message: string;
  solicitud_id: string;
}

export interface VerificarCodigoRequest {
  solicitud_id: string;
  codigo: string;
}

export interface VerificarCodigoResponse {
  success: boolean;
  reset_token: string;
}

export interface RestablecerPasswordRequest {
  solicitud_id: string;
  reset_token: string;
  password_nueva: string;
  confirmar_password: string;
}

export interface RestablecerPasswordResponse {
  success: boolean;
  message: string;
}


@Injectable({
  providedIn: 'root'
})
export class PasswordRecoveryService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = `${environment.apiUrl}/api/auth/recuperar-password`;

  solicitarRecuperacion(correo: string): Observable<SolicitarRecuperacionResponse> {
    const payload: SolicitarRecuperacionRequest = { correo };
    return this.http.post<SolicitarRecuperacionResponse>(
      `${this.apiUrl}/solicitar`,
      payload
    );
  }

  verificarCodigo(
    solicitudId: string,
    codigo: string
  ): Observable<VerificarCodigoResponse> {
    const payload: VerificarCodigoRequest = {
      solicitud_id: solicitudId,
      codigo
    };

    return this.http.post<VerificarCodigoResponse>(
      `${this.apiUrl}/verificar`,
      payload
    );
  }

  restablecerPassword(
    solicitudId: string,
    resetToken: string,
    passwordNueva: string,
    confirmarPassword: string
  ): Observable<RestablecerPasswordResponse> {
    const payload: RestablecerPasswordRequest = {
      solicitud_id: solicitudId,
      reset_token: resetToken,
      password_nueva: passwordNueva,
      confirmar_password: confirmarPassword
    };

    return this.http.post<RestablecerPasswordResponse>(
      `${this.apiUrl}/restablecer`,
      payload
    );
  }
}
