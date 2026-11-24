"""Contratos tipados Pydantic para el Asistente Comercial Inteligente (CU34: HUs 147, 148, 149, 150)."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


AmoblamientoEstado = Literal['AMOBLADA', 'PARCIALMENTE_AMOBLADA', 'SIN_AMOBLAR', 'DESCONOCIDO']


class CommercialSearchCriteria(BaseModel):
    model_config = ConfigDict(extra='ignore')
    intencion: str = Field(
        default='buscar_unidades',
        description=(
            'buscar_unidades | recomendar_presupuesto | comparar_unidades | '
            'estimar_costo | proponer_proyecto | solicitar_contacto | consulta_general'
        ),
    )
    tipo_unidad: str | None = Field(
        default=None,
        description='DEPARTAMENTO | VIVIENDA | LOCAL | LOTE | OFICINA | None',
    )
    min_dormitorios: int | None = Field(default=None, ge=0, le=20)
    min_banos: int | None = Field(default=None, ge=0, le=20)
    superficie_min_m2: float | None = Field(default=None, ge=0)
    superficie_max_m2: float | None = Field(default=None, ge=0)
    presupuesto_max: float | None = Field(default=None, ge=0)
    moneda: str = Field(default='BOB', description='BOB | USD')
    zona: str | None = None
    id_obra: int | None = None
    nombre_obra: str | None = None
    estilo_acabado: str | None = Field(
        default=None,
        description='ESTANDAR | MINIMALISTA | INDUSTRIAL | CONTEMPORANEO | LUJO',
    )
    estado_construccion: str | None = Field(
        default=None,
        description='PLANIFICADO | EN_CONSTRUCCION | FINALIZADO',
    )
    amoblamiento_preferido: Literal['AMOBLADA', 'PARCIALMENTE_AMOBLADA', 'SIN_AMOBLAR'] | None = None
    amoblamiento_indispensable: bool = False
    acepta_cotizar_mobiliario: bool = False
    tiene_terreno: bool | None = None
    superficie_terreno_m2: float | None = Field(default=None, ge=0)
    plazo_deseado_meses: int | None = Field(default=None, ge=1, le=120)
    restricciones_indispensables: list[str] = Field(default_factory=list)
    caracteristicas_deseadas: list[str] = Field(default_factory=list)
    codigos_comparar: list[str] = Field(default_factory=list)
    ids_unidades_comparar: list[int] = Field(default_factory=list)
    solo_disponibles: bool = True
    necesita_aclaracion: bool = False
    pregunta_aclaracion: str | None = None


class CostEstimationRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    superficie_m2: float = Field(gt=0, le=50000, description='Superficie total en metros cuadrados')
    tipo_inmueble: str = Field(default='DEPARTAMENTO', description='DEPARTAMENTO | VIVIENDA | LOCAL | OFICINA')
    estilo_acabado: str = Field(
        default='MODERNO',
        description='ESTANDAR | MINIMALISTA | INDUSTRIAL | CONTEMPORANEO | LUJO',
    )
    cantidad_plantas: int = Field(default=1, ge=1, le=40)
    dormitorios: int = Field(default=2, ge=0, le=20)
    banos: int = Field(default=2, ge=0, le=20)
    presupuesto_objetivo: float | None = Field(default=None, ge=0)
    moneda: str = Field(default='BOB', description='BOB | USD')
    incluir_parqueo: bool = False
    incluir_baulera: bool = False
    incluir_domotica: bool = False
    id_unidad_referencia: int | None = Field(default=None, gt=0)


class LeadContactRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    nombre_completo: str = Field(min_length=2, max_length=150)
    telefono: str | None = Field(default=None, max_length=30)
    email: str | None = Field(default=None, max_length=150)
    ci: str | None = Field(default=None, max_length=30)
    presupuesto_estimado: float | None = Field(default=None, ge=0)
    moneda: str = Field(default='BOB', description='BOB | USD')
    unidades_interes: list[int] = Field(default_factory=list)
    notas: str | None = Field(default=None, max_length=2000)
    horario_preferido: str | None = Field(default=None, max_length=100)
    conversacion_id: str | None = Field(default=None, max_length=80)


class CommercialChatRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    mensaje: str = Field(min_length=1, max_length=2000)
    conversacion_id: str | None = Field(default=None, max_length=80)
    presupuesto_max: float | None = Field(default=None, ge=0)
    moneda: str = Field(default='BOB', description='BOB | USD')
    tipo_unidad_preferido: str | None = Field(default=None, max_length=40)
    estilo_preferido: str | None = Field(default=None, max_length=40)
    min_dormitorios: int | None = Field(default=None, ge=0, le=20)
    ids_unidades_comparar: list[int] = Field(default_factory=list)
    contacto: LeadContactRequest | None = None
