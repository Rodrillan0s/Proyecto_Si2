    # app/services/prediccion_services.py
import os
import json
from datetime import date
from groq import Groq

from app.repos import prediccion_repos
from app.classes.postgre import PostgreSQL

def predecir_rendimiento(id_campana: int, user_id: int) -> tuple[dict, int]:
    db = PostgreSQL()
    try:
        db.create_connection()

        contexto = prediccion_repos.get_contexto_campana(db, id_campana)

        if not contexto:
            return {'success': False, 'message': f'Campaña con id {id_campana} no encontrada.'}, 404

        prompt = _construir_prompt(contexto)
        respuesta_texto = _llamar_ia(prompt)
        resultado = _parsear_respuesta(respuesta_texto)

        # Registramos en bitácora el uso del módulo de IA
        db.insert_log(f"GENERÓ PREDICCIÓN IA PARA CAMPAÑA ID: {id_campana}", user_id)
        db.conn.commit()

        return {
            'success': True,
            'message': 'Predicción generada exitosamente.',
            'rendimiento_estimado': resultado['rendimiento_estimado'],
            'justificacion':        resultado['justificacion'],
        }, 200

    except EnvironmentError as e:
        if db.conn: db.conn.rollback()
        print(f'ERROR en predecir_rendimiento (env): {e}')
        return {'success': False, 'message': str(e)}, 500

    except ValueError as e:
        if db.conn: db.conn.rollback()
        print(f'ERROR en predecir_rendimiento (IA): {e}')
        return {'success': False, 'message': f'Error al procesar la respuesta de la IA: {str(e)}'}, 422

    except Exception as e:
        if db.conn: db.conn.rollback()
        print(f'ERROR en predecir_rendimiento: {e}')
        return {'success': False, 'message': f'ERROR: {str(e)}'}, 500

    finally:
        db.close_connection()


def _construir_prompt(ctx: dict) -> str:
    c   = ctx["campana"]
    h   = ctx["historial_lote"]
    ot  = ctx["ordenes_trabajo"]
    ins = ctx["insumos_usados"]
    cal = ctx["calidad_historica"]

    duracion_dias = None
    if c["fecha_siembra"] and c["fecha_cosecha"]:
        try:
            fs = date.fromisoformat(c["fecha_siembra"])
            fc = date.fromisoformat(c["fecha_cosecha"])
            duracion_dias = (fc - fs).days
        except Exception:
            pass

    hist_txt = "Sin historial previo en este lote."
    if h:
        lineas = []
        for prev in h:
            rend = prev["rendimiento_real"] or prev["rendimiento_estimado"]
            lineas.append(
                f"  - {prev['nombre_campana']} | {prev['variedad']} | "
                f"rendimiento: {rend} t/ha | estado: {prev['estado']}"
            )
        hist_txt = "\n".join(lineas)

    completadas   = [o for o in ot if o["estado"] == "COMPLETADA"]
    pendientes    = [o for o in ot if o["estado"] == "PENDIENTE"]
    tipos_trabajo = list({o["tipo_trabajo"] for o in ot})
    ordenes_txt = (
        f"{len(completadas)} completadas, {len(pendientes)} pendientes. "
        f"Tipos: {', '.join(tipos_trabajo) if tipos_trabajo else 'ninguno'}"
    )

    if ins:
        ins_txt = "\n".join(
            f"  - {i['producto']} ({i['categoria']}): {i['total_usado']} {i['unidad']}"
            for i in ins[:8]
        )
    else:
        ins_txt = "Sin insumos registrados."

    if cal["total_controles"] > 0:
        cal_txt = (
            f"Humedad promedio: {cal['avg_humedad']}% | "
            f"Impurezas promedio: {cal['avg_impurezas']}% "
            f"(basado en {cal['total_controles']} controles anteriores)"
        )
    else:
        cal_txt = "Sin datos de calidad histórica disponibles."

    return f"""Eres un agrónomo experto con amplio conocimiento en cultivos de la región oriental de Bolivia (Santa Cruz).
Tu tarea es estimar el rendimiento productivo de una campaña agrícola basándote en los datos reales del sistema de gestión.

═══════════════════════════════════════
DATOS DE LA CAMPAÑA ACTUAL
═══════════════════════════════════════
Nombre          : {c['nombre_campana']}
Variedad        : {c['variedad']}
Lote #          : {c['nro_lote']} — Sector: {c['nombre_sector']}
Tamaño lote     : {c['tamano_hectareas']} hectáreas
Estado terreno  : {c['estado_terreno']}
Estado campaña  : {c['estado']}
Fecha siembra   : {c['fecha_siembra']}
Fecha cosecha   : {c['fecha_cosecha']}
Duración ciclo  : {f"{duracion_dias} días" if duracion_dias else "No calculable"}

═══════════════════════════════════════
HISTORIAL DE CAMPAÑAS ANTERIORES (mismo lote)
═══════════════════════════════════════
{hist_txt}

═══════════════════════════════════════
ÓRDENES DE TRABAJO REGISTRADAS
═══════════════════════════════════════
{ordenes_txt}

═══════════════════════════════════════
INSUMOS APLICADOS
═══════════════════════════════════════
{ins_txt}

═══════════════════════════════════════
CALIDAD HISTÓRICA DEL LOTE
═══════════════════════════════════════
{cal_txt}

═══════════════════════════════════════
INSTRUCCIÓN
═══════════════════════════════════════
Analiza todos los factores anteriores y estima el rendimiento en toneladas por hectárea (t/ha).
Considera: historial productivo del lote, intensidad de manejo (insumos y órdenes de trabajo),
duración del ciclo, variedad sembrada y condición del terreno.

Responde ÚNICAMENTE con un objeto JSON válido, sin texto adicional, sin bloques de código:
{{"rendimiento_estimado": <número decimal>, "justificacion": "<máximo 3 oraciones concisas explicando los factores principales>"}}
"""

def _llamar_ia(prompt: str) -> str:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError("La variable GROQ_API_KEY no está configurada.")

    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=512,
        temperature=0.2,
    )
    return response.choices[0].message.content.strip()

def _parsear_respuesta(texto: str) -> dict:
    texto_limpio = texto.strip()
    if texto_limpio.startswith("```"):
        texto_limpio = texto_limpio.split("```")[1]
        if texto_limpio.lower().startswith("json"):
            texto_limpio = texto_limpio[4:]
        texto_limpio = texto_limpio.strip()

    try:
        resultado = json.loads(texto_limpio)
    except json.JSONDecodeError as e:
        raise ValueError(f"La IA devolvió una respuesta no parseable: {texto!r}") from e

    if "rendimiento_estimado" not in resultado:
        raise ValueError("La respuesta no contiene 'rendimiento_estimado'")
    if "justificacion" not in resultado:
        raise ValueError("La respuesta no contiene 'justificacion'")

    return {
        "rendimiento_estimado": round(float(resultado["rendimiento_estimado"]), 2),
        "justificacion":        str(resultado["justificacion"]),
    }