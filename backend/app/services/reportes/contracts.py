from datetime import date, time
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class Filters(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id_obra: int | None = Field(default=None, gt=0)
    desde: date | None = None
    hasta: date | None = None
    estado: str | None = Field(default=None, max_length=50)
    q: str | None = Field(default=None, max_length=120)
    id_categoria: int | None = Field(default=None, gt=0)
    prioridad: Literal['BAJA','MEDIA','ALTA','CRITICA'] | None = None

    @model_validator(mode="after")
    def ordered(self):
        if self.desde and self.hasta and self.desde > self.hasta:
            raise ValueError("La fecha inicial debe ser anterior a la final.")
        return self


class Presentation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    titulo: str | None = Field(default=None, max_length=120)
    columnas: list[str] = Field(default_factory=list, max_length=40)
    ordenar_por: str | None = Field(default=None, max_length=80)
    orden: Literal['asc', 'desc'] = 'asc'
    orientacion: Literal['vertical', 'horizontal'] = 'horizontal'


class ReportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reporte: str = Field(min_length=1, max_length=60)
    filtros: Filters = Field(default_factory=Filters)
    presentacion: Presentation = Field(default_factory=Presentation)


class Interpretation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    texto: str = Field(min_length=1, max_length=2000)
    conversacion: str | None = None
    usar_ia: bool = False


class Delivery(BaseModel):
    model_config = ConfigDict(extra="forbid")
    destinatarios: list[int] = Field(min_length=1, max_length=30)
    formatos: list[Literal["pdf", "xlsx"]] = Field(default_factory=lambda: ["pdf"], min_length=1, max_length=2)


class AssistantRequest(Interpretation):
    solicitud: ReportRequest | None = None
    id_obra_contexto: int | None = Field(default=None, gt=0)


class Schedule(Delivery):
    solicitud: ReportRequest
    frecuencia: Literal["diaria", "semanal", "mensual"]
    hora: time
    zona: str = "America/La_Paz"
    dia: int = Field(default=1, ge=1, le=31)
    periodo: Literal["fijo", "mes_anterior", "semana_anterior", "ayer"] = "fijo"
    habilitada: bool = True


class SchedulePatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    habilitada: bool
