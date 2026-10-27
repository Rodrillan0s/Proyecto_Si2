"""Contratos CU39: el plan completo se guarda con versión optimista."""
from datetime import date
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class Contrato(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)


class Actividad(Contrato):
    clave: str = Field(min_length=1, max_length=64, pattern=r'^[A-Za-z0-9_-]+$')
    nombre: str = Field(min_length=1, max_length=180)
    descripcion: str = Field(default='', max_length=2000)
    tipo: Literal['ACTIVIDAD', 'HITO'] = 'ACTIVIDAD'
    fecha_inicio: date
    fecha_fin: date
    inicio_real: date | None = None
    fin_real: date | None = None
    avance: int = Field(default=0, ge=0, le=100, strict=True)
    dependencias: list[str] = Field(default_factory=list, max_length=200)

    @model_validator(mode='after')
    def coherencia(self):
        if self.fecha_fin < self.fecha_inicio:
            raise ValueError('La fecha fin prevista no puede preceder al inicio.')
        if self.tipo == 'HITO' and self.fecha_inicio != self.fecha_fin:
            raise ValueError('Un hito debe tener la misma fecha de inicio y fin.')
        if self.fin_real and (not self.inicio_real or self.fin_real < self.inicio_real):
            raise ValueError('El fin real requiere un inicio real anterior o igual.')
        if (self.avance > 0 or self.fin_real) and not self.inicio_real:
            raise ValueError('El avance requiere fecha de inicio real.')
        if (self.avance == 100) != (self.fin_real is not None):
            raise ValueError('El avance 100% y la fecha de fin real deben registrarse juntos.')
        if self.tipo == 'HITO' and self.avance not in (0, 100):
            raise ValueError('Un hito solo puede estar pendiente (0%) o cumplido (100%).')
        if len(set(self.dependencias)) != len(self.dependencias):
            raise ValueError('No repita dependencias.')
        return self


class CronogramaCreate(Contrato):
    nombre: str = Field(min_length=1, max_length=180)
    descripcion: str = Field(default='', max_length=2000)
    fecha_inicio: date
    fecha_fin: date
    actividades: list[Actividad] = Field(default_factory=list, max_length=500)

    @model_validator(mode='after')
    def fechas(self):
        if self.fecha_fin < self.fecha_inicio:
            raise ValueError('El fin del cronograma no puede preceder al inicio.')
        return self


class CronogramaUpdate(CronogramaCreate):
    version: int = Field(gt=0, strict=True)


class PlanificacionUpdate(Contrato):
    version: int = Field(gt=0, strict=True)
    actividades: list[Actividad] = Field(max_length=500)
