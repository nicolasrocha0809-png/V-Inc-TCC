import os

from PySide6.QtWidgets import QApplication

from config import settings


TEMAS_DISPONIVEIS = {"escuro", "claro", "contraste"}
FONTES_DISPONIVEIS = {"10px", "12px", "14px", "16px"}


def carregar_estilo(tema=None, fonte=None):
    tema = tema or settings.get("visual", "tema") or "escuro"
    fonte = fonte or settings.get("visual", "fonte") or "12px"

    if tema not in TEMAS_DISPONIVEIS:
        tema = "escuro"

    if fonte not in FONTES_DISPONIVEIS:
        fonte = "12px"

    raiz_projeto = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    caminho_base = os.path.join(
        raiz_projeto,
        "interface",
        "estilos",
        "base.qss",
    )
    caminho_tema = os.path.join(
        raiz_projeto,
        "interface",
        "temas",
        f"{tema}.qss",
    )

    with open(caminho_base, "r", encoding="utf-8") as arquivo_base:
        estilo_base = arquivo_base.read()

    with open(caminho_tema, "r", encoding="utf-8") as arquivo_tema:
        estilo_tema = arquivo_tema.read()

    return (
        f"{estilo_base}\n{estilo_tema}\n"
        f"QWidget {{ font-size: {fonte}; }}"
    )


def aplicar_estilo(tema=None, fonte=None):
    aplicacao = QApplication.instance()

    if aplicacao is None:
        return False

    aplicacao.setStyleSheet(carregar_estilo(tema, fonte))
    return True
