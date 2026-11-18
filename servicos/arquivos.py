"""Localiza e abre PDF/TXT no programa padrão do Windows.

O conteúdo permanece a cargo do leitor de tela (NVDA/Narrador do Windows).
"""

import os
import re
import sys
import unicodedata
from difflib import get_close_matches
from pathlib import Path


EXTENSOES = {".pdf", ".txt"}
PASTAS_IGNORADAS = {
    ".git", ".venv", "venv", "node_modules", "__pycache__", "appdata",
    ".cache", "$recycle.bin",
}


def normalizar_nome(valor):
    texto = unicodedata.normalize("NFKD", str(valor or ""))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return " ".join(re.sub(r"[^a-z0-9]+", " ", texto.lower()).split())


def normalizar_pasta(nome):
    texto = normalizar_nome(nome)
    return {
        "documentos": "documents",
        "area de trabalho": "desktop",
    }.get(texto, texto)


def obter_pastas_de_documentos():
    """Busca pastas pessoais e redirecionamentos típicos do Windows/OneDrive."""
    usuario = Path(os.getenv("USERPROFILE") or Path.home())
    bases = [usuario]
    for chave in ("OneDrive", "OneDriveConsumer"):
        if os.getenv(chave):
            bases.append(Path(os.getenv(chave)))

    pastas = [
        base / nome for base in bases
        for nome in (
            "Downloads", "Documents", "Documentos", "Desktop", "Área de Trabalho"
        )
    ]

    if sys.platform == "win32":
        try:
            import winreg

            registro = (
                r"Software\Microsoft\Windows\CurrentVersion"
                r"\Explorer\User Shell Folders"
            )
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, registro) as chave:
                for nome in (
                    "Desktop", "Personal", "{374DE290-123F-4565-9164-39C4925E467B}"
                ):
                    try:
                        valor, _ = winreg.QueryValueEx(chave, nome)
                        pastas.append(Path(os.path.expandvars(valor)))
                    except OSError:
                        pass
        except OSError:
            pass

    unicas = {}
    for pasta in pastas:
        if pasta.is_dir():
            unicas.setdefault(str(pasta.resolve()).casefold(), pasta)
    return list(unicas.values())


def localizar_arquivo(nome_solicitado, pasta_solicitada=None):
    """Retorna status nao_encontrado, ambiguo ou encontrado."""
    nome = str(nome_solicitado or "").strip().strip('"').strip("'")
    nome = re.sub(
        r"\s+ponto\s+(pdf|txt)$",
        lambda match: "." + match.group(1).lower(),
        nome,
        flags=re.IGNORECASE,
    )
    extensao = Path(nome).suffix.lower()
    if extensao in EXTENSOES:
        nome = Path(nome).stem
    consulta = normalizar_nome(nome)
    if not consulta:
        return {"status": "nao_encontrado"}

    pasta = None
    if pasta_solicitada:
        pasta = normalizar_nome(pasta_solicitada)
        pasta = re.sub(r"^(?:pasta|diretorio)\s+", "", pasta)
        pasta = normalizar_pasta(pasta)

    arquivos = {}
    for origem in obter_pastas_de_documentos():
        for raiz, diretorios, nomes in os.walk(
            origem, onerror=lambda erro: None
        ):
            diretorios[:] = [
                d for d in diretorios
                if d.casefold() not in PASTAS_IGNORADAS and not d.startswith(".")
            ]
            for item in nomes:
                caminho = Path(raiz) / item
                if caminho.suffix.lower() not in EXTENSOES:
                    continue
                if extensao in EXTENSOES and caminho.suffix.lower() != extensao:
                    continue
                if pasta and not any(
                    normalizar_pasta(parte) == pasta for parte in caminho.parent.parts
                ):
                    continue
                arquivos.setdefault(str(caminho).casefold(), caminho)

    opcoes = list(arquivos.values())
    exatos = [p for p in opcoes if normalizar_nome(p.stem) == consulta]
    parciais = [
        p for p in opcoes
        if f" {consulta} " in f" {normalizar_nome(p.stem)} "
    ]
    nomes_disponiveis = {normalizar_nome(p.stem) for p in opcoes}
    similares = set(get_close_matches(consulta, nomes_disponiveis, n=5, cutoff=0.7))
    aproximados = [p for p in opcoes if normalizar_nome(p.stem) in similares]
    resultados = sorted(
        exatos or parciais or aproximados,
        key=lambda p: str(p).casefold(),
    )
    if not resultados:
        return {"status": "nao_encontrado"}
    if len(resultados) > 1:
        return {"status": "ambiguo", "opcoes": resultados}
    return {
        "status": "encontrado",
        "nome": resultados[0].name,
        "caminho": resultados[0],
    }


def abrir_arquivo(caminho):
    """Abre um documento no leitor padrão sem ler seu conteúdo em voz alta."""
    caminho = Path(caminho)
    if caminho.suffix.lower() not in EXTENSOES:
        raise ValueError("Somente PDF e TXT podem ser abertos.")
    if not caminho.is_file():
        raise FileNotFoundError("Arquivo não encontrado.")
    if sys.platform != "win32":
        raise OSError("Esta funcionalidade requer Windows.")
    os.startfile(str(caminho))
