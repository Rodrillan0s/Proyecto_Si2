"""Contratos CU39: el plan completo se guarda con versión optimista."""
from datetime import date
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class Contrato(BaseModel):
    model_config = ConfigDict(extra='ignore', str_strip_whitespace=True)


class Actividad(Contrato):
    clave: str = Field(min_length=1, max_length=64, pattern=r'^[A-Za-z0-9_-]+$')
    nombre: str = Field(default='Nueva actividad', max_length=180)
    descripcion: str = Field(default='', max_length=2000)
    tipo: Literal['ACTIVIDAD', 'HITO'] = 'ACTIVIDAD'
    fecha_inicio: date
    fecha_fin: date
    inicio_real: date | None = None
    fin_real: date | None = None
    avance: int = Field(default=0, ge=0, le=100)
    dependencias: list[str] = Field(default_factory=list, max_length=200)

    @model_validator(mode='after')
    def coherencia(self):
        if not self.nombre or not self.nombre.strip():
            self.nombre = 'Nueva actividad'
        if self.fecha_fin < self.fecha_inicio:
            self.fecha_fin = self.fecha_inicio
        if self.tipo == 'HITO':
            self.fecha_fin = self.fecha_inicio
            if self.avance not in (0, 100):
                self.avance = 100 if self.avance >= 50 else 0
        if (self.avance > 0 or self.fin_real) and not self.inicio_real:
            self.inicio_real = self.fecha_inicio
        if self.avance == 100 and not self.fin_real:
            self.fin_real = self.fecha_fin if self.fecha_fin >= self.inicio_real else self.inicio_real
        if self.fin_real and (not self.inicio_real or self.fin_real < self.inicio_real):
            self.inicio_real = self.fin_real
        if len(set(self.dependencias)) != len(self.dependencias):
            self.dependencias = list(dict.fromkeys(self.dependencias))
        return self


class CronogramaCreate(Contrato):
    nombre: str = Field(default='Plan de obra', max_length=180)
    descripcion: str = Field(default='', max_length=2000)
    fecha_inicio: date
    fecha_fin: date
    actividades: list[Actividad] = Field(default_factory=list, max_length=500)

    @model_validator(mode='after')
    def fechas(self):
        if not self.nombre or not self.nombre.strip():
            self.nombre = 'Plan de obra'
        if self.fecha_fin < self.fecha_inicio:
            self.fecha_fin = self.fecha_inicio
        return self


class CronogramaUpdate(CronogramaCreate):
    version: int = Field(gt=0)


class PlanificacionUpdate(Contrato):
    version: int = Field(gt=0)
    actividades: list[Actividad] = Field(max_length=500)
