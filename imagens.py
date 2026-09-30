import os
import re
import winreg
import unicodedata
from difflib import get_close_matches
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types


load_dotenv()


MIME_POR_EXTENSAO = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".heic": "image/heic",
    ".heif": "image/heif",
}

EXTENSOES_IMAGEM = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".heic",
    ".heif",
}

PASTAS_TECNICAS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
}

_cache_imagens = None

def normalizar_nome(nome):
    nome = unicodedata.normalize("NFKD", nome)

    nome = "".join(
        caractere
        for caractere in nome
        if not unicodedata.combining(caractere)
    )

    nome = nome.lower()
    nome = re.sub(r"[^a-z0-9]+", " ", nome)

    return " ".join(nome.split())


def obter_pastas_de_imagens():
    pasta_usuario = Path(os.getenv("USERPROFILE", Path.home()))

    pastas = obter_pastas_conhecidas_windows()

    pastas.extend([
        pasta_usuario / "Downloads",
        pasta_usuario / "Documents",
        pasta_usuario / "Desktop",
        pasta_usuario / "Pictures",
    ])

    pastas_existentes = []
    caminhos_adicionados = set()

    for pasta in pastas:
        caminho_normalizado = str(pasta).lower()

        if pasta.exists() and caminho_normalizado not in caminhos_adicionados:
            pastas_existentes.append(pasta)
            caminhos_adicionados.add(caminho_normalizado)

    return pastas_existentes


def obter_pastas_conhecidas_windows():
    nomes_registro = (
        "Desktop",
        "Personal",
        "My Pictures",
        "{374DE290-123F-4565-9164-39C4925E467B}",
    )

    pastas = []

    try:
        chave_registro = (
            r"Software\Microsoft\Windows\CurrentVersion"
            r"\Explorer\User Shell Folders"
        )

        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            chave_registro,
        ) as chave:
            for nome in nomes_registro:
                try:
                    valor, _ = winreg.QueryValueEx(chave, nome)
                    caminho = Path(os.path.expandvars(valor))

                    if caminho.exists():
                        pastas.append(caminho)

                except OSError:
                    continue

    except OSError as erro:
        print(f"Não foi possível consultar as pastas do Windows: {erro}")

    return pastas


def encontrar_imagens(forcar_atualizacao=False):
    global _cache_imagens

    if _cache_imagens is not None and not forcar_atualizacao:
        return _cache_imagens.copy()

    imagens = []
    caminhos_adicionados = set()

    for pasta in obter_pastas_de_imagens():
        for raiz, diretorios, arquivos in os.walk(
            pasta,
            onerror=lambda erro: None,
        ):
            diretorios[:] = [
                diretorio
                for diretorio in diretorios
                if diretorio.casefold() not in PASTAS_TECNICAS
            ]
            for arquivo in arquivos:
                caminho = Path(raiz) / arquivo

                if caminho.suffix.lower() not in EXTENSOES_IMAGEM:
                    continue

                caminho_normalizado = str(caminho).casefold()

                if caminho_normalizado in caminhos_adicionados:
                    continue

                imagens.append(caminho)
                caminhos_adicionados.add(caminho_normalizado)

    _cache_imagens = imagens

    return imagens.copy()


def buscar_imagens(nome_solicitado, forcar_atualizacao=False):
    cache_ja_existia = _cache_imagens is not None
    imagens = encontrar_imagens(forcar_atualizacao)
    nome_informado = str(nome_solicitado).strip()

    nome_informado = re.sub(
        r"\s+ponto\s+(png|jpe?g|webp|heic|heif)$",
        "",
        nome_informado,
        flags=re.IGNORECASE,
    )

    sufixo = Path(nome_informado).suffix.lower()

    if sufixo in EXTENSOES_IMAGEM:
        nome_informado = Path(nome_informado).stem

    nome_normalizado = normalizar_nome(nome_informado)

    if not nome_normalizado:
        return []

    # Primeiro procura pelo nome exato, ignorando a extensão
    resultados_exatos = [
        caminho
        for caminho in imagens
        if (
            normalizar_nome(caminho.stem) == nome_normalizado
            and caminho.exists()
        )
    ]

    if resultados_exatos:
        return resultados_exatos

    # Depois procura nomes que contenham o texto solicitado
    resultados_parciais = [
        caminho
        for caminho in imagens
        if (
            f" {nome_normalizado} "
            in f" {normalizar_nome(caminho.stem)} "
            and caminho.exists()
        )
    ]

    if resultados_parciais:
        return resultados_parciais

    # Por último, procura nomes parecidos
    nomes_disponiveis = {
        normalizar_nome(caminho.stem)
        for caminho in imagens
    }

    nomes_parecidos = get_close_matches(
        nome_normalizado,
        nomes_disponiveis,
        n=5,
        cutoff=0.6,
    )

    resultados_parecidos = [
        caminho
        for caminho in imagens
        if (
            normalizar_nome(caminho.stem) in nomes_parecidos
            and caminho.exists()
        )
    ]

    if resultados_parecidos:
        return resultados_parecidos

    # Se a busca utilizou um cache antigo e não encontrou nada,
    # atualiza a lista e tenta novamente uma única vez.
    if cache_ja_existia and not forcar_atualizacao:
        return buscar_imagens(
            nome_solicitado,
            forcar_atualizacao=True,
        )

    return []


def localizar_imagem(nome_solicitado):
    resultados = buscar_imagens(nome_solicitado)

    if not resultados:
        return {
            "status": "nao_encontrada",
            "nome": nome_solicitado,
        }

    if len(resultados) > 1:
        return {
            "status": "ambiguo",
            "opcoes": resultados,
        }

    imagem = resultados[0]

    return {
        "status": "encontrada",
        "nome": imagem.name,
        "caminho": imagem,
    }


def descrever_imagem(caminho_imagem):
    caminho = Path(caminho_imagem)

    if not caminho.exists():
        raise FileNotFoundError("A imagem selecionada não existe.")

    if caminho.stat().st_size > 20 * 1024 * 1024:
        raise ValueError("A imagem ultrapassa o limite de 20 MB.")

    mime_type = MIME_POR_EXTENSAO.get(caminho.suffix.lower())

    if not mime_type:
        raise ValueError("Formato de imagem não suportado.")

    chave_api = os.getenv("GEMINI_API_KEY")

    if not chave_api:
        raise RuntimeError("GEMINI_API_KEY não encontrada no arquivo .env.")

    modelo = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
    cliente = genai.Client(api_key=chave_api)

    prompt = """
    Você é um recurso de acessibilidade visual.

    Descreva esta imagem em português do Brasil, usando texto natural
    e adequado para ser lido em voz alta.

    Comece com um resumo de uma frase. Depois, normalmente em três a seis
    frases, descreva os objetos, pessoas, ações, posições, cores e detalhes
    visualmente importantes.

    Leia todo texto visível que conseguir identificar.
    Se houver gráfico, tabela ou diagrama, explique suas informações principais.

    Não invente identidades, intenções ou detalhes incertos.
    Quando algo não estiver claro, informe a incerteza.
    Não seja excessivamente breve nem produza uma descrição longa sem necessidade.
    Não use Markdown, tópicos ou símbolos de formatação.
    """.strip()

    imagem_bytes = caminho.read_bytes()

    resposta = cliente.models.generate_content(
        model=modelo,
        contents=[
            prompt,
            types.Part.from_bytes(
                data=imagem_bytes,
                mime_type=mime_type,
            ),
        ],
        config=types.GenerateContentConfig(
            temperature=0.2,
            max_output_tokens=2000,
            thinking_config=types.ThinkingConfig(
                thinking_level="low",
            ),
            automatic_function_calling=types.AutomaticFunctionCallingConfig(
                disable=True,
            ),
        ),
    )

    descricao = resposta.text.strip() if resposta.text else ""

    if not descricao:
        raise RuntimeError("O Gemini não retornou uma descrição.")

    return descricao