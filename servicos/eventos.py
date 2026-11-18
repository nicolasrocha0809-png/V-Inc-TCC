"""Eventos estruturados do assistente para a interface gráfica.

Logs técnicos continuam no stdout; apenas eventos com prefixo VINC_EVENT
são exibidos como mensagens na conversa do V.INC.
"""

import json

PREFIXO_EVENTO = "VINC_EVENT:"
TIPOS_PERMITIDOS = {"usuario", "vinc", "erro"}


def formatar_evento(tipo, texto):
    if tipo not in TIPOS_PERMITIDOS:
        raise ValueError("Tipo de evento inválido")
    return PREFIXO_EVENTO + json.dumps(
        {"tipo": tipo, "texto": str(texto)},
        ensure_ascii=True,
    )


def interpretar_evento(linha):
    if not linha.startswith(PREFIXO_EVENTO):
        return None
    try:
        evento = json.loads(linha[len(PREFIXO_EVENTO):])
    except (ValueError, TypeError):
        return None
    if not isinstance(evento, dict):
        return None
    if evento.get("tipo") not in TIPOS_PERMITIDOS:
        return None
    if not isinstance(evento.get("texto"), str):
        return None
    return evento
