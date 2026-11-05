from fastapi import APIRouter, Depends, Header, Request
from pydantic import BaseModel, ConfigDict, Field

from app.services import pago_services as service
from app.utils.security import exigir_rol, verificar_token


router = APIRouter(prefix='/api/pagos', tags=['Pagos SaaS'])


class InicioCheckout(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    codigo_plan: str = Field(min_length=1, max_length=20)


@router.get('/planes')
def planes(token: dict = Depends(verificar_token)):
    return {'success': True, 'data': service.listar_planes(token)}


@router.post('/checkout-sessions', status_code=201)
def checkout_session(
    datos: InicioCheckout,
    idempotency_key: str = Header(..., alias='Idempotency-Key', min_length=8, max_length=255),
    token: dict = Depends(exigir_rol('ADMINISTRADOR_EMPRESA')),
):
    return {'success': True, 'data': service.iniciar_checkout(token, datos.codigo_plan, idempotency_key)}


@router.post('/webhooks/stripe')
async def webhook_stripe(
    request: Request,
    stripe_signature: str = Header(..., alias='Stripe-Signature'),
):
    payload = await request.body()
    return {'success': True, 'data': service.procesar_webhook(payload, stripe_signature)}


@router.get('/mi-empresa')
def pagos_mi_empresa(
    token: dict = Depends(exigir_rol('ADMINISTRADOR_EMPRESA')),
):
    return {'success': True, 'data': service.listar_pagos_mi_empresa(token)}


@router.get('/{id_pago}/comprobante')
def comprobante_pago(
    id_pago: int,
    token: dict = Depends(exigir_rol('ADMINISTRADOR_EMPRESA', 'ADMINISTRADOR')),
):
    if id_pago <= 0:
        from fastapi import HTTPException
        raise HTTPException(422, 'Identificador de pago inválido.')
    return {'success': True, 'data': service.consultar_comprobante(token, id_pago)}


@router.post('/{id_pago}/verificar')
def verificar_pago(
    id_pago: int,
    token: dict = Depends(exigir_rol('ADMINISTRADOR', 'ADMINISTRADOR_EMPRESA')),
):
    if id_pago <= 0:
        from fastapi import HTTPException
        raise HTTPException(422, 'Identificador de pago inválido.')
    return {'success': True, 'data': service.verificar_pago(token, id_pago)}


@router.get('/{id_pago}')
def pago(id_pago: int, token: dict = Depends(verificar_token)):
    if id_pago <= 0:
        from fastapi import HTTPException
        raise HTTPException(422, 'Identificador de pago inválido.')
    return {'success': True, 'data': service.consultar_pago(token, id_pago)}

