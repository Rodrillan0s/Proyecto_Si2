from datetime import datetime, time, timedelta, timezone
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from pydantic import BaseModel, ConfigDict, Field, field_validator


class Contract(BaseModel):
    model_config = ConfigDict(extra='forbid')


class BackupRequest(Contract):
    alcance: Literal['base_datos'] = 'base_datos'


class Schedule(BackupRequest):
    habilitada: bool = False
    frecuencia: Literal['diario', 'semanal', 'mensual'] = 'diario'
    hora: str = '02:00'
    zona_horaria: str = 'America/La_Paz'
    dia_semana: int = Field(0, ge=0, le=6)
    dia_mes: int = Field(1, ge=1, le=28)
    retencion_dias: Literal[7, 15, 30, 90] = 30

    @field_validator('hora')
    @classmethod
    def hour(cls, value):
        if len(value) != 5 or value[2] != ':':
            raise ValueError('Use HH:MM.')
        try:
            time.fromisoformat(value)
        except ValueError:
            raise ValueError('Hora inválida.')
        return value

    @field_validator('zona_horaria')
    @classmethod
    def zone(cls, value):
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError):
            raise ValueError('Zona horaria IANA inválida.')
        return value


class ValidateRequest(Contract):
    archivo: str = Field(pattern=r'^[1-9][0-9]{0,18}$')


class ApplyRequest(Contract):
    confirmacion: str = Field(min_length=1, max_length=200)
    desafio: str = Field(min_length=32, max_length=128)
    token_reautenticacion: str = Field(min_length=20, max_length=4000)


def next_run(config, after):
    config = config if isinstance(config, Schedule) else Schedule.model_validate(config)
    zone = ZoneInfo(config.zona_horaria)
    local = after.astimezone(zone)
    hour, minute = map(int, config.hora.split(':'))
    for offset in range(370):
        day = local.date() + timedelta(days=offset)
        if config.frecuencia == 'semanal' and day.weekday() != config.dia_semana:
            continue
        if config.frecuencia == 'mensual' and day.day != config.dia_mes:
            continue
        candidate = datetime.combine(day, time(hour, minute), zone)
        # No ejecutar dos veces una hora repetida; normalizar horas inexistentes.
        candidate = candidate.astimezone(timezone.utc)
        if candidate > after:
            return candidate
    raise ValueError('No se encontró la siguiente ejecución.')
