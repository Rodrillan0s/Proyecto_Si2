import calendar
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from fastapi import HTTPException


def next_run(config, after=None):
    try:
        zone = ZoneInfo(config['zona'])
    except (ZoneInfoNotFoundError, ValueError):
        raise HTTPException(422,'Zona horaria IANA desconocida.')
    now = (after or datetime.now(timezone.utc)).astimezone(zone)
    hour, minute = map(int, str(config['hora']).split(':')[:2])
    if config['frecuencia']=='semanal' and config['dia']>7:
        raise HTTPException(422,'El día semanal debe estar entre 1 (lunes) y 7 (domingo).')
    for offset in range(370):
        day = now.date()+timedelta(days=offset)
        if config['frecuencia']=='semanal' and day.isoweekday()!=config['dia']:
            continue
        if config['frecuencia']=='mensual' and day.day!=min(config['dia'],calendar.monthrange(day.year,day.month)[1]):
            continue
        candidate = datetime(day.year,day.month,day.day,hour,minute,tzinfo=zone)
        # En saltos DST se usa la primera hora real posterior; fold=0 evita dos envíos.
        candidate = candidate.astimezone(timezone.utc).astimezone(zone)
        if candidate>now:
            return candidate.astimezone(timezone.utc)
    raise HTTPException(422,'No se pudo calcular la próxima ejecución.')


def period_request(config, occurrence):
    request = {'reporte':config['solicitud']['reporte'], 'filtros':dict(config['solicitud'].get('filtros',{}))}
    if 'presentacion' in config['solicitud']:
        request['presentacion'] = dict(config['solicitud']['presentacion'])
    day = occurrence.astimezone(ZoneInfo(config['zona'])).date()
    mode = config['periodo']
    if mode=='mes_anterior':
        end = day.replace(day=1)-timedelta(days=1)
        start = end.replace(day=1)
    elif mode=='semana_anterior':
        end = day-timedelta(days=day.weekday()+1)
        start = end-timedelta(days=6)
    elif mode=='ayer':
        start = end = day-timedelta(days=1)
    else:
        return request
    request['filtros'].update(desde=start.isoformat(),hasta=end.isoformat())
    return request
