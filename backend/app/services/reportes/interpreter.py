"""Interpretación local tolerante; nunca produce SQL ni efectos externos."""
import calendar
import re
import unicodedata
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from zoneinfo import ZoneInfo
from .catalog import REGISTRY


def normalize(text):
    return ''.join(c for c in unicodedata.normalize('NFKD', text.lower()) if not unicodedata.combining(c))


def similarity(text, phrase):
    if phrase in text:
        return 1.0
    words, target = text.split(), phrase.split()
    scores = [SequenceMatcher(None, ' '.join(words[i:i+len(target)]), phrase).ratio() for i in range(len(words))]
    return max(scores, default=0)


def interpret(text, available, works, previous=None, now=None):
    normalized = normalize(text)
    scores = sorted([(max(similarity(normalized, normalize(a)) for a in REGISTRY[item].aliases), item) for item in available], reverse=True)
    # Las frases específicas prevalecen sobre alias genéricos contenidos en ellas.
    exact = [(max((len(a) for a in REGISTRY[item].aliases if normalize(a) in normalized), default=0), item) for item in available]
    exact.sort(reverse=True)
    if exact and exact[0][0] > 0:
        phrases = [(max((normalize(a) for a in REGISTRY[item].aliases if normalize(a) in normalized), key=len, default=''),item) for item in available]
        independent = [(phrase,item) for phrase,item in phrases if phrase and not any(phrase in other and item!=other_id for other,other_id in phrases)]
        if len(independent)>1:
            return {'estado':'needs_clarification','mensaje':'Tu solicitud incluye varios reportes. Elige cuál generar primero.', 'opciones':[REGISTRY[item].titulo for _,item in independent]}
        scores = [(1, exact[0][1])] + [(s,k) for s,k in scores if k != exact[0][1]]
        if len(exact)>1 and exact[0][0] == exact[1][0]:
            return {'estado':'needs_clarification','mensaje':'Elige cuál de estos reportes deseas.', 'opciones':[REGISTRY[k].titulo for _,k in exact[:3]]}
    if not scores or scores[0][0] < .77:
        named_followup = any(normalize(w['nombre']) == normalized.strip(' ?.¡!') or (w.get('codigo') and normalize(w['codigo']) == normalized.strip(' ?.¡!')) for w in works)
        if previous and (named_followup or any(p in normalized for p in ('mismo', 'ahora', 'pdf', 'excel', 'este mes', 'mes anterior'))):
            request = {'reporte': previous['reporte'], 'filtros': dict(previous.get('filtros',{}))}
            if previous.get('presentacion'):
                request['presentacion'] = dict(previous['presentacion'])
        else:
            return {'estado':'unsupported','mensaje':'Puedo ayudarte con estos reportes. Elige uno o añade el nombre del proyecto.', 'opciones':[REGISTRY[k].titulo for k in available]}
    else:
        if scores[0][0] < 1 and len(scores)>1 and scores[0][0]-scores[1][0]<.08:
            return {'estado':'needs_clarification','mensaje':'Hay dos interpretaciones cercanas. Elige el reporte.', 'opciones':[REGISTRY[k].titulo for _,k in scores[:2]]}
        request = {'reporte':scores[0][1],'filtros':{}}
    filters = request['filtros']
    if request['reporte']=='stock':
        category = re.search(r'\bcategoria\s+(\d+)\b',normalized)
        if category:
            filters['id_categoria']=int(category[1])
        if any(similarity(normalized, phrase)>=.86 for phrase in ('stock bajo','bajo minimo','poco stock','por agotarse','criticos','criticas','faltantes','escasez')):
            filters['estado']='STOCK_BAJO'
        elif any(phrase in normalized for phrase in ('sin stock','agotados','agotadas')):
            filters['estado']='SIN_STOCK'
    if request['reporte'] in {'incidencias','incidencias_criticas'}:
        priorities = {'alta':'ALTA','baja':'BAJA','media':'MEDIA'}
        for word, value in priorities.items():
            if re.search(r'\b(?:prioridad\s+)?'+word+r'\b',normalized):
                filters['prioridad']=value
        for word,value in {'resueltas':'RESUELTA','cerradas':'CERRADA','registradas':'REGISTRADA','asignadas':'ASIGNADA'}.items():
            if word in normalized:
                filters['estado']=value
    numbered = re.search(r'(?:obra|proyecto)\s*(?:#|numero|nro|id)?\s*(\d+)', normalized)
    if numbered:
        found = [w for w in works if w['id_obra']==int(numbered[1])]
        if not found:
            return {'estado':'needs_clarification','mensaje':'Selecciona una obra de tu lista autorizada.', 'obras':works}
        filters['id_obra'] = found[0]['id_obra']
    else:
        matched = [w for w in works if re.search(r'\b'+re.escape(normalize(w['nombre']))+r'\b',normalized) or (w.get('codigo') and re.search(r'\b'+re.escape(normalize(w['codigo']))+r'\b',normalized))]
        if len(matched)>1:
            return {'estado':'needs_clarification','mensaje':'Encontré varias obras. Selecciona una.', 'obras':matched}
        if matched:
            filters['id_obra'] = matched[0]['id_obra']
        elif 'mismo' in normalized and previous:
            filters['id_obra'] = previous.get('filtros',{}).get('id_obra')
        elif re.search(r'\b(?:obra|proyecto)\s+\S+',normalized) and not re.search(
            r'\b(?:obra|proyecto)\s+(?:que|cual|tiene|ha|han|genero|generaron|genera|con|sin|esta|mas|menos|alguna|ninguna)\b', normalized):
            named = re.split(r'\b(?:obra|proyecto)\s+',normalized,maxsplit=1)[-1]
            near = sorted([(similarity(named,normalize(w['nombre'])),w) for w in works],key=lambda pair:pair[0],reverse=True)
            if near and near[0][0]>=.82 and (len(near)==1 or near[0][0]-near[1][0]>=.1):
                filters['id_obra'] = near[0][1]['id_obra']
            else:
                return {'estado':'needs_clarification','mensaje':'Selecciona la obra que tienes en mente.', 'obras':works,'solicitud':request}
    today = (now or datetime.now(ZoneInfo('America/La_Paz'))).date()
    dates = re.findall(r'\b\d{4}-\d{2}-\d{2}\b', normalized)
    if dates:
        filters.update(desde=dates[0],hasta=dates[-1])
    elif 'mes anterior' in normalized or 'mes pasado' in normalized:
        last = today.replace(day=1)-timedelta(days=1)
        filters.update(desde=last.replace(day=1).isoformat(),hasta=last.isoformat())
    elif 'este mes' in normalized:
        filters.update(desde=today.replace(day=1).isoformat(),hasta=today.isoformat())
    elif 'ayer' in normalized:
        filters.update(desde=(today-timedelta(days=1)).isoformat(),hasta=(today-timedelta(days=1)).isoformat())
    elif 'hoy' in normalized:
        filters.update(desde=today.isoformat(),hasta=today.isoformat())
    elif 'ultimos 7 dias' in normalized or 'ultima semana' in normalized:
        filters.update(desde=(today-timedelta(days=6)).isoformat(),hasta=today.isoformat())
    elif 'ultimos 30 dias' in normalized:
        filters.update(desde=(today-timedelta(days=29)).isoformat(),hasta=today.isoformat())
    if request['reporte']=='comparativo_costos' and (filters.get('desde') or filters.get('hasta')) and 'costos_periodo' in available:
        request['reporte']='costos_periodo'
    if request['reporte']=='stock':
        filters.pop('id_obra', None)
    if REGISTRY[request['reporte']].obra and not filters.get('id_obra'):
        return {'estado':'needs_clarification','mensaje':'Selecciona la obra para comparar sus costos.', 'obras':works,'solicitud':request}
    if (filters.get('desde') or filters.get('hasta')) and not REGISTRY[request['reporte']].fecha:
        return {'estado':'needs_clarification','mensaje':'Este reporte refleja el estado actual y no dispone de cortes históricos. Puedes generarlo sin fechas.', 'solicitud':request}
    return {'estado':'ready','mensaje':'Solicitud preparada. Puedes generar el reporte.', 'solicitud':request,
            'formato':'xlsx' if 'excel' in normalized else 'pdf' if 'pdf' in normalized else None}
