"""Contratos tipados del Motor Semántico Compartido y Reportes Universales."""
from datetime import date
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid')


class SemanticFilter(StrictModel):
    campo: str = Field(min_length=1, max_length=80)
    operador: Literal['eq', 'ne', 'in', 'gt', 'gte', 'lt', 'lte', 'between', 'contains', 'is_null']
    valor: str | int | float | bool | list[str | int | float] | None = None


class SemanticMetric(StrictModel):
    operacion: Literal['count', 'count_distinct', 'sum', 'avg', 'min', 'max']
    campo: str | None = Field(default=None, max_length=80)
    alias: str = Field(pattern=r'^[a-z][a-z0-9_]{0,59}$')


class TimeConfig(StrictModel):
    campo_fecha: str | None = Field(default=None, max_length=80)
    desde: date | None = None
    hasta: date | None = None
    granularidad: Literal['day', 'week', 'month', 'quarter', 'year'] | None = None
    comparar_periodo_anterior: bool = False

    @model_validator(mode='after')
    def check_dates(self):
        if self.desde and self.hasta and self.desde > self.hasta:
            raise ValueError('La fecha inicial debe ser anterior o igual a la final.')
        return self


class SemanticQuerySpec(StrictModel):
    entidad: str = Field(min_length=1, max_length=60)
    relaciones: list[str] = Field(default_factory=list, max_length=3)
    filtros: list[SemanticFilter] = Field(default_factory=list, max_length=15)
    tiempo: TimeConfig | None = None
    dimensiones: list[str] = Field(default_factory=list, max_length=6)
    metricas: list[SemanticMetric] = Field(default_factory=list, max_length=8)
    campos: list[str] = Field(default_factory=list, max_length=30)
    ordenar_por: str | None = Field(default=None, max_length=80)
    orden: Literal['asc', 'desc'] = 'desc'
    limite: int = Field(default=50, ge=1, le=20000)
    id_obra: int | None = Field(default=None, gt=0)
    titulo: str | None = Field(default=None, max_length=120)
    tipo_grafico: Literal['auto', 'none', 'kpi', 'bar', 'stacked_bar', 'line', 'pie'] = 'auto'


class CrossModuleSpec(StrictModel):
    """Consulta multidimensional agregada por llave común (evita fan-out)."""
    llave: Literal['id_obra'] = 'id_obra'
    modulos: list[Literal['retrasos', 'incidencias_criticas', 'costos', 'ordenes_trabajo', 'posventa']] = Field(
        min_length=2, max_length=5
    )
    id_obra: int | None = Field(default=None, gt=0)
    ordenar_por: str | None = Field(default=None, max_length=80)
    orden: Literal['asc', 'desc'] = 'desc'
    limite: int = Field(default=30, ge=1, le=500)


class ReportSpecPatch(StrictModel):
    """Modificación incremental sobre el ReportSpec activo en conversación."""
    operacion: Literal[
        'add_dimension',
        'remove_dimension',
        'add_filter',
        'remove_filter',
        'set_time',
        'compare_periods',
        'set_sort',
        'set_chart',
        'set_limit',
        'set_title',
    ]
    campo: str | None = Field(default=None, max_length=80)
    filtro: SemanticFilter | None = None
    tiempo: TimeConfig | None = None
    orden: Literal['asc', 'desc'] | None = None
    tipo_grafico: Literal['auto', 'none', 'kpi', 'bar', 'stacked_bar', 'line', 'pie'] | None = None
    limite: int | None = Field(default=None, ge=1, le=20000)
    titulo: str | None = Field(default=None, max_length=120)


class ChartSpec(BaseModel):
    tipo: Literal['none', 'kpi', 'bar', 'stacked_bar', 'line', 'pie'] = 'none'
    eje_x: str | None = None
    series: list[dict[str, Any]] = Field(default_factory=list)
    titulo: str | None = None


class UnifiedResultSet(BaseModel):
    """Superconjunto estricto de ReportResult (compatible con Angular y Flutter)."""
    version: int = 2
    reporte: str
    titulo: str
    id_empresa: int
    corte: str
    solicitud: dict[str, Any]
    columnas: list[dict[str, Any]]
    columnas_disponibles: list[dict[str, Any]]
    filas: list[dict[str, Any]]
    resumen: dict[str, Any]
    advertencias: list[str]
    recomendaciones: list[dict[str, Any]] = Field(default_factory=list)
    permisos_fuente: list[str] = Field(default_factory=list)
    # Extensiones universales opcionales
    tipo_resultado: Literal[
        'tabular', 'agregacion', 'comparativa', 'serie_temporal', 'multidimensional', 'especializado'
    ] = 'tabular'
    chart_spec: ChartSpec = Field(default_factory=ChartSpec)
    comparativa_periodo: dict[str, Any] | None = None
    metadata_dominio: dict[str, Any] = Field(default_factory=dict)
    fuentes_consultadas: list[str] = Field(default_factory=list)
    fuentes_omitidas: list[dict[str, Any]] = Field(default_factory=list)
