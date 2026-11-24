"""Gestor de contexto conversacional persistente con 6 compartimentos separados.

REGLAS DE SEGURIDAD:
- policy_snapshot sirve EXCLUSIVAMENTE para detectar cambios de permisos/rol e invalidar
  el estado previo; NUNCA sustituye la reautorización en vivo en authorization.py.
- Los 6 compartimentos nunca se mezclan:
  1. Historial conversacional (en t_asistente_mensaje: pregunta + texto_respuesta truncado).
  2. preferencias_usuario (moneda, preferencias comerciales).
  3. entidades_resueltas (obra_actual, unidad_actual, cliente_actual).
  4. report_spec_activo (SemanticQuerySpec o ReportRequest editable incrementalmente).
  5. ultima_ejecucion (id_ejecucion, origen, corte).
  6. resumen_herramientas (últimas 6 invocaciones resumidas).
"""
from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, ConfigDict, Field
from app.repos import reportes_repos as repo


class ConversationState(BaseModel):
    model_config = ConfigDict(extra='forbid')
    version: int = 2
    policy_snapshot: dict[str, Any] = Field(default_factory=dict)
    id_empresa: int = 0
    entidades_resueltas: dict[str, Any] = Field(default_factory=dict)
    preferencias_usuario: dict[str, Any] = Field(default_factory=dict)
    report_spec_activo: dict[str, Any] | None = None
    ultima_ejecucion: dict[str, Any] | None = None
    resumen_herramientas: list[dict[str, Any]] = Field(default_factory=list)


def load_state(conversation_row: dict | None, ctx) -> tuple[ConversationState, bool]:
    """Carga el estado de conversación y devuelve (state, invalidated).
    Si la empresa o policy_snapshot cambiaron, invalida report_spec_activo,
    ultima_ejecucion y entidades_resueltas.
    """
    current_policy = ctx.policy()
    if not conversation_row or not isinstance(conversation_row.get('solicitud'), dict):
        return ConversationState(policy_snapshot=current_policy, id_empresa=ctx.empresa), False

    raw = conversation_row['solicitud']
    # Compatibilidad retroactiva con conversaciones v1 (donde solicitud era un ReportRequest plano)
    if raw.get('version') != 2:
        state = ConversationState(
            policy_snapshot=current_policy,
            id_empresa=ctx.empresa,
            report_spec_activo={'tipo': 'estandar', 'solicitud': raw} if raw.get('reporte') else None,
        )
        return state, False

    try:
        state = ConversationState.model_validate(raw)
    except Exception:
        return ConversationState(policy_snapshot=current_policy, id_empresa=ctx.empresa), True

    # Invalidación por cambio de empresa o política (nunca sustituye reautorización)
    if state.id_empresa != ctx.empresa or state.policy_snapshot != current_policy:
        fresh = ConversationState(
            policy_snapshot=current_policy,
            id_empresa=ctx.empresa,
            preferencias_usuario=dict(state.preferencias_usuario),
        )
        return fresh, True

    return state, False


def build_chat_history(recent_rows: list[dict], max_turns: int = 6) -> list[dict]:
    """Construye mensajes (user, assistant) limpios para DeepSeek desde t_asistente_mensaje."""
    messages: list[dict] = []
    for row in reversed((recent_rows or [])[:max_turns]):
        q = (row.get('texto') or '').strip()
        a = (row.get('texto_respuesta') or '').strip()
        if q:
            messages.append({'role': 'user', 'content': q[:1200]})
        if a:
            messages.append({'role': 'assistant', 'content': a[:1500]})
    return messages


def record_tool_summary(state: ConversationState, tool_name: str, summary: dict[str, Any]) -> None:
    entry = {
        'tool': tool_name,
        'ts': datetime.now(timezone.utc).isoformat(),
        **summary,
    }
    state.resumen_herramientas = (state.resumen_herramientas + [entry])[-6:]


def save_turn(
    db,
    conversation_id: str,
    ctx,
    question: str,
    answer_text: str,
    state: ConversationState,
    response_metadata: dict[str, Any],
    is_new_conversation: bool,
) -> None:
    """Persiste el turno completo incluyendo texto_respuesta truncado y estado v2."""
    state.policy_snapshot = ctx.policy()
    state.id_empresa = ctx.empresa

    if is_new_conversation:
        repo.create_conversation(db, (conversation_id, ctx.empresa, ctx.usuario))
    repo.set_conversation_request(db, (repo.j(state.model_dump(mode='json')), conversation_id))

    safe_meta = {
        k: v for k, v in response_metadata.items()
        if k not in {'ejecucion', 'ejecuciones', 'respuesta', 'resultados_consulta', 'resultado_analisis'}
    }
    safe_meta['texto_respuesta'] = (answer_text or '')[:2000]
    safe_meta['entidades'] = state.entidades_resueltas
    repo.add_message(db, (conversation_id, question, repo.j(safe_meta)))
