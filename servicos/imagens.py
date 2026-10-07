import base64
import hashlib
import json
import os
import re
import time
import unicodedata
import urllib.error
import urllib.request
import winreg
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

GRUPOS_ALIASES_PASTAS = (
    {"documentos", "documents", "meus documentos", "my documents"},
    {"imagens", "pictures", "fotos", "photos", "minhas imagens", "my pictures"},
    {"area de trabalho", "desktop"},
    {"downloads", "download"},
)

TIMEOUT_GEMINI_MS = 20_000
TIMEOUT_FALLBACK_HTTP = 25

PROMPT_DESCRICAO = """
Você é um recurso de acessibilidade visual.

Descreva esta imagem em português do Brasil, usando texto natural
e adequado para ser lido em voz alta.

Comece com um resumo de uma frase. Depois, normalmente em três a seis
frases, descreva os objetos, pessoas, ações, posições, cores e detalhes
visualmente importantes.

Leia todo texto visível que conseguir identificar.
Se houver gráfico, tabela ou diagrama, explique suas informações principais.

Se reconhecer um personagem, objeto ou referência cultural com boa confiança,
você pode citar o nome. Se não tiver certeza, descreva a aparência ou diga que
se parece com determinado elemento. Não afirme nomes específicos quando houver dúvida.

Não invente identidades, intenções ou detalhes incertos.
Quando algo não estiver claro, informe a incerteza.
Não seja excessivamente breve nem produza uma descrição longa sem necessidade.
Escreva exclusivamente em português do Brasil.
Não misture palavras ou expressões de outros idiomas na resposta.
Não use Markdown, tópicos ou símbolos de formatação.
""".strip()

MODELO_GEMINI_FALLBACK_PADRAO = "gemini-3.1-flash-lite"
MODELO_DOTS_PADRAO = "dots-studio/dots-3-note-preview:free"
MODELO_CLOUDFLARE_PADRAO = "@cf/google/gemma-4-26b-a4b-it"

VERSAO_INDICE_IMAGENS = 1
VERSAO_CACHE_DESCRICOES = 1

_cache_imagens = None


def obter_pasta_cache():
    base_local = os.getenv("LOCALAPPDATA")

    if base_local:
        pasta = Path(base_local) / "V-Inc" / "cache"
    else:
        pasta = Path.home() / ".v-inc" / "cache"

    pasta.mkdir(parents=True, exist_ok=True)
    return pasta


def caminho_cache(nome_arquivo):
    return obter_pasta_cache() / nome_arquivo


def carregar_json_cache(caminho, padrao):
    if not caminho.exists():
        return padrao

    try:
        with caminho.open("r", encoding="utf-8") as arquivo:
            return json.load(arquivo)
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as erro:
        print(f"Cache ignorado por estar inválido ({caminho.name}): {erro}")
        return padrao


def salvar_json_cache(caminho, dados):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho.with_name(caminho.name + ".tmp")

    try:
        with temporario.open("w", encoding="utf-8") as arquivo:
            json.dump(
                dados,
                arquivo,
                ensure_ascii=False,
                indent=2,
            )
        os.replace(temporario, caminho)
    except OSError as erro:
        print(f"Não foi possível salvar o cache {caminho.name}: {erro}")
        try:
            temporario.unlink(missing_ok=True)
        except OSError:
            pass


def carregar_indice_imagens():
    caminho = caminho_cache("indice_imagens.json")
    dados = carregar_json_cache(caminho, None)

    if not isinstance(dados, dict):
        return None

    if dados.get("versao") != VERSAO_INDICE_IMAGENS:
        return None

    itens = dados.get("imagens")
    if not isinstance(itens, list):
        return None

    imagens = []
    caminhos_adicionados = set()

    for item in itens:
        if not isinstance(item, dict):
            continue

        caminho_texto = item.get("caminho")
        if not caminho_texto:
            continue

        caminho_imagem = Path(caminho_texto)

        if (
            not caminho_imagem.exists()
            or caminho_imagem.suffix.lower() not in EXTENSOES_IMAGEM
        ):
            continue

        chave = str(caminho_imagem).casefold()
        if chave in caminhos_adicionados:
            continue

        imagens.append(caminho_imagem)
        caminhos_adicionados.add(chave)

    return imagens


def salvar_indice_imagens(imagens):
    registros = []

    for caminho_imagem in imagens:
        try:
            estatisticas = caminho_imagem.stat()
        except OSError:
            continue

        registros.append({
            "caminho": str(caminho_imagem),
            "tamanho": estatisticas.st_size,
            "mtime_ns": estatisticas.st_mtime_ns,
        })

    salvar_json_cache(
        caminho_cache("indice_imagens.json"),
        {
            "versao": VERSAO_INDICE_IMAGENS,
            "imagens": registros,
        },
    )


def hash_imagem(imagem_bytes):
    return hashlib.sha256(imagem_bytes).hexdigest()


def buscar_descricao_cache(chave_imagem):
    dados = carregar_json_cache(
        caminho_cache("descricoes.json"),
        {
            "versao": VERSAO_CACHE_DESCRICOES,
            "descricoes": {},
        },
    )

    if not isinstance(dados, dict):
        return None

    if dados.get("versao") != VERSAO_CACHE_DESCRICOES:
        return None

    descricoes = dados.get("descricoes")
    if not isinstance(descricoes, dict):
        return None

    descricao = descricoes.get(chave_imagem)

    if isinstance(descricao, str) and descricao.strip():
        return descricao.strip()

    return None


def salvar_descricao_cache(chave_imagem, descricao):
    caminho = caminho_cache("descricoes.json")
    dados = carregar_json_cache(
        caminho,
        {
            "versao": VERSAO_CACHE_DESCRICOES,
            "descricoes": {},
        },
    )

    if (
        not isinstance(dados, dict)
        or dados.get("versao") != VERSAO_CACHE_DESCRICOES
        or not isinstance(dados.get("descricoes"), dict)
    ):
        dados = {
            "versao": VERSAO_CACHE_DESCRICOES,
            "descricoes": {},
        }

    dados["descricoes"][chave_imagem] = descricao.strip()
    salvar_json_cache(caminho, dados)


def finalizar_descricao(chave_imagem, descricao):
    salvar_descricao_cache(chave_imagem, descricao)
    return descricao


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

    if not forcar_atualizacao:
        indice_persistente = carregar_indice_imagens()

        if indice_persistente:
            _cache_imagens = indice_persistente
            print(
                f"Índice persistente carregado com "
                f"{len(_cache_imagens)} imagem(ns)."
            )
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
    salvar_indice_imagens(imagens)

    print(
        f"Índice de imagens atualizado com "
        f"{len(_cache_imagens)} imagem(ns)."
    )

    return imagens.copy()

def caminho_corresponde_pasta(caminho, pasta_solicitada):
    if not pasta_solicitada:
        return True

    pasta_normalizada = normalizar_nome(str(pasta_solicitada))
    pasta_normalizada = re.sub(
        r"^(?:pasta|diretorio)\s+",
        "",
        pasta_normalizada,
    ).strip()

    if not pasta_normalizada:
        return True

    aliases = {pasta_normalizada}

    for grupo in GRUPOS_ALIASES_PASTAS:
        grupo_normalizado = {normalizar_nome(nome) for nome in grupo}

        if pasta_normalizada in grupo_normalizado:
            aliases.update(grupo_normalizado)
            break

    partes_caminho = {
        normalizar_nome(parte)
        for parte in caminho.parent.parts
        if normalizar_nome(parte)
    }

    return bool(partes_caminho.intersection(aliases))


def buscar_imagens(nome_solicitado, forcar_atualizacao=False, pasta_solicitada=None):
    cache_ja_existia = _cache_imagens is not None
    imagens = encontrar_imagens(forcar_atualizacao)

    if pasta_solicitada:
        imagens = [
            caminho
            for caminho in imagens
            if caminho_corresponde_pasta(caminho, pasta_solicitada)
        ]

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
            pasta_solicitada=pasta_solicitada,
            forcar_atualizacao=True,
        )

    return []


def localizar_imagem(nome_solicitado, pasta_solicitada=None):
    resultados = buscar_imagens(
        nome_solicitado,
        pasta_solicitada=pasta_solicitada,
    )

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


def abrir_imagem(caminho_imagem):
    """Abre uma imagem no visualizador padrão do Windows."""
    caminho = Path(caminho_imagem)

    if not caminho.exists() or not caminho.is_file():
        return {
            "status": "nao_encontrada",
            "caminho": caminho,
        }

    try:
        os.startfile(str(caminho))
        return {
            "status": "aberta",
            "caminho": caminho,
        }

    except OSError as erro:
        return {
            "status": "erro",
            "caminho": caminho,
            "erro": str(erro),
        }


def eh_erro_temporario(erro):
    texto = f"{type(erro).__name__}: {erro}".upper()

    indicadores = (
        "429",
        "500",
        "502",
        "503",
        "504",
        "UNAVAILABLE",
        "RESOURCE_EXHAUSTED",
        "TOO MANY REQUESTS",
        "TIMEOUT",
        "TIMED OUT",
        "TEMPORAR",
        "HIGH DEMAND",
    )

    return any(indicador in texto for indicador in indicadores)


def eh_timeout_rede(erro):
    texto = f"{type(erro).__name__}: {erro}".upper()

    return any(
        indicador in texto
        for indicador in (
            "TIMEOUT",
            "TIMED OUT",
            "READTIMEOUT",
            "CONNECTTIMEOUT",
        )
    )


def gerar_descricao_gemini(cliente, modelo, imagem_bytes, mime_type):
    resposta = cliente.models.generate_content(
        model=modelo,
        contents=[
            PROMPT_DESCRICAO,
            types.Part.from_bytes(
                data=imagem_bytes,
                mime_type=mime_type,
            ),
        ],
        config=types.GenerateContentConfig(
            temperature=0.2,
            max_output_tokens=700,
            thinking_config=types.ThinkingConfig(
                thinking_level="minimal",
            ),
            automatic_function_calling=types.AutomaticFunctionCallingConfig(
                disable=True,
            ),
        ),
    )

    candidatos = getattr(resposta, "candidates", None) or []

    if candidatos:
        motivo = getattr(candidatos[0], "finish_reason", None)
        motivo_texto = getattr(motivo, "name", str(motivo)).upper()

        if "MAX_TOKENS" in motivo_texto:
            raise RuntimeError(
                f"O modelo {modelo} atingiu o limite de tokens "
                "antes de concluir a descrição."
            )

    descricao = resposta.text.strip() if resposta.text else ""

    if not descricao:
        raise RuntimeError(f"O modelo {modelo} não retornou uma descrição.")

    return descricao

def criar_data_url(imagem_bytes, mime_type):
    imagem_base64 = base64.b64encode(imagem_bytes).decode("utf-8")
    return f"data:{mime_type};base64,{imagem_base64}"


def requisicao_json(url, corpo, headers, nome_servico, timeout=TIMEOUT_FALLBACK_HTTP):
    requisicao = urllib.request.Request(
        url,
        data=json.dumps(corpo).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(requisicao, timeout=timeout) as resposta:
            return json.loads(resposta.read().decode("utf-8"))

    except urllib.error.HTTPError as erro:
        corpo_erro = erro.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"{nome_servico} retornou HTTP {erro.code}: {corpo_erro}"
        ) from erro

    except urllib.error.URLError as erro:
        raise RuntimeError(
            f"Não foi possível conectar ao {nome_servico}: {erro.reason}"
        ) from erro


def gerar_descricao_dots(imagem_bytes, mime_type):
    chave_api = os.getenv("OPENROUTER_API_KEY")

    if not chave_api:
        raise RuntimeError("OPENROUTER_API_KEY não encontrada no arquivo .env.")

    modelo = os.getenv("OPENROUTER_VISION_MODEL", MODELO_DOTS_PADRAO)
    imagem_data_url = criar_data_url(imagem_bytes, mime_type)

    dados = requisicao_json(
        "https://openrouter.ai/api/v1/chat/completions",
        {
            "model": modelo,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": PROMPT_DESCRICAO,
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": imagem_data_url,
                            },
                        },
                    ],
                }
            ],
            "temperature": 0.2,
            "max_tokens": 700,
            "reasoning": {
                "effort": "none",
            },
        },
        {
            "Authorization": f"Bearer {chave_api}",
            "Content-Type": "application/json",
        },
        "OpenRouter",
    )

    escolhas = dados.get("choices") or []

    if not escolhas:
        raise RuntimeError("O OpenRouter respondeu sem nenhuma opção de resposta.")

    descricao = (escolhas[0].get("message") or {}).get("content")

    if not descricao or not descricao.strip():
        raise RuntimeError("O Dots respondeu, mas não retornou uma descrição.")

    return descricao.strip()


def gerar_descricao_cloudflare(imagem_bytes, mime_type):
    account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")
    auth_token = os.getenv("CLOUDFLARE_AUTH_TOKEN")

    if not account_id or not auth_token:
        raise RuntimeError(
            "CLOUDFLARE_ACCOUNT_ID ou CLOUDFLARE_AUTH_TOKEN não encontrados no .env."
        )

    modelo = os.getenv("CLOUDFLARE_VISION_MODEL", MODELO_CLOUDFLARE_PADRAO)
    imagem_data_url = criar_data_url(imagem_bytes, mime_type)

    url = (
        "https://api.cloudflare.com/client/v4/accounts/"
        f"{account_id}/ai/v1/chat/completions"
    )

    dados = requisicao_json(
        url,
        {
            "model": modelo,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": imagem_data_url,
                            },
                        },
                        {
                            "type": "text",
                            "text": PROMPT_DESCRICAO,
                        },
                    ],
                }
            ],
            "temperature": 0.2,
            "max_completion_tokens": 700,
            "chat_template_kwargs": {
                "enable_thinking": False,
            },
        },
        {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        },
        "Cloudflare Workers AI",
    )

    escolhas = dados.get("choices") or []

    if not escolhas:
        raise RuntimeError("A Cloudflare respondeu sem nenhuma opção de resposta.")

    descricao = (escolhas[0].get("message") or {}).get("content")

    if not descricao or not descricao.strip():
        raise RuntimeError("O Gemma da Cloudflare não retornou uma descrição.")

    return descricao.strip()


def descrever_imagem(caminho_imagem, notificar=None):
    caminho = Path(caminho_imagem)

    def avisar(mensagem):
        print(f"Status da descrição: {mensagem}")

        if notificar is None:
            return

        try:
            notificar(mensagem)
        except Exception as erro_aviso:
            print(f"Não foi possível reproduzir o aviso de status: {erro_aviso}")

    if not caminho.exists():
        raise FileNotFoundError("A imagem selecionada não existe.")

    if caminho.stat().st_size > 20 * 1024 * 1024:
        raise ValueError("A imagem ultrapassa o limite de 20 MB.")

    mime_type = MIME_POR_EXTENSAO.get(caminho.suffix.lower())

    if not mime_type:
        raise ValueError("Formato de imagem não suportado.")

    imagem_bytes = caminho.read_bytes()
    chave_imagem = hash_imagem(imagem_bytes)

    descricao_cache = buscar_descricao_cache(chave_imagem)

    if descricao_cache:
        print("Descrição encontrada no cache persistente.")
        return descricao_cache

    erros = []

    chave_gemini = os.getenv("GEMINI_API_KEY")
    modelo_principal = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
    modelo_fallback = os.getenv(
        "GEMINI_FALLBACK_MODEL",
        MODELO_GEMINI_FALLBACK_PADRAO,
    )

    if chave_gemini:
        cliente = genai.Client(
            api_key=chave_gemini,
            http_options=types.HttpOptions(
                timeout=TIMEOUT_GEMINI_MS,
            ),
        )

        print(f"Tentando descrição com Gemini ({modelo_principal})...")

        try:
            descricao = gerar_descricao_gemini(
                cliente,
                modelo_principal,
                imagem_bytes,
                mime_type,
            )
            print(f"Descrição gerada com Gemini ({modelo_principal}).")
            return finalizar_descricao(chave_imagem, descricao)

        except Exception as erro:
            erros.append(f"Gemini {modelo_principal}: {erro}")
            print(f"Falha no Gemini ({modelo_principal}): {erro}")

            if eh_erro_temporario(erro) and not eh_timeout_rede(erro):
                avisar(
                    "O serviço principal de descrição está ocupado. "
                    "Vou tentar novamente."
                )
                print(
                    "Erro temporário no Gemini. "
                    "Tentando novamente em 2 segundos..."
                )
                time.sleep(2)

                try:
                    descricao = gerar_descricao_gemini(
                        cliente,
                        modelo_principal,
                        imagem_bytes,
                        mime_type,
                    )
                    print(
                        f"Descrição gerada com Gemini ({modelo_principal}) "
                        "na segunda tentativa."
                    )
                    return finalizar_descricao(chave_imagem, descricao)

                except Exception as erro_retry:
                    erros.append(
                        f"Gemini {modelo_principal} (retry): {erro_retry}"
                    )
                    print(
                        f"Segunda tentativa do Gemini ({modelo_principal}) "
                        f"falhou: {erro_retry}"
                    )

        if modelo_fallback != modelo_principal:
            avisar(
                "O serviço principal ainda não respondeu. "
                "Vou tentar uma opção alternativa."
            )
            print(f"Tentando fallback Gemini ({modelo_fallback})...")

            try:
                descricao = gerar_descricao_gemini(
                    cliente,
                    modelo_fallback,
                    imagem_bytes,
                    mime_type,
                )
                print(f"Descrição gerada com Gemini ({modelo_fallback}).")
                return finalizar_descricao(chave_imagem, descricao)

            except Exception as erro:
                erros.append(f"Gemini {modelo_fallback}: {erro}")
                print(f"Falha no Gemini ({modelo_fallback}): {erro}")

    else:
        erros.append("GEMINI_API_KEY ausente")
        print("GEMINI_API_KEY não encontrada. Pulando os modelos Gemini.")
        avisar(
            "O serviço principal de descrição não está disponível. "
            "Vou usar uma alternativa."
        )

    avisar(
        "A primeira opção não conseguiu concluir a descrição. "
        "Vou tentar outro serviço."
    )
    print("Tentando fallback gratuito pelo OpenRouter (Dots)...")

    try:
        descricao = gerar_descricao_dots(imagem_bytes, mime_type)
        print("Descrição gerada com Dots pelo OpenRouter.")
        return finalizar_descricao(chave_imagem, descricao)

    except Exception as erro:
        erros.append(f"Dots/OpenRouter: {erro}")
        print(f"Falha no Dots/OpenRouter: {erro}")

    avisar(
        "Ainda não consegui gerar a descrição. "
        "Vou fazer uma última tentativa."
    )
    print("Tentando fallback pela Cloudflare Workers AI (Gemma)...")

    try:
        descricao = gerar_descricao_cloudflare(imagem_bytes, mime_type)
        print("Descrição gerada com Gemma pela Cloudflare Workers AI.")
        return finalizar_descricao(chave_imagem, descricao)

    except Exception as erro:
        erros.append(f"Gemma/Cloudflare: {erro}")
        print(f"Falha no Gemma/Cloudflare: {erro}")

    resumo_erros = " | ".join(erros)
    raise RuntimeError(
        "Nenhum serviço conseguiu gerar a descrição da imagem. "
        f"Detalhes: {resumo_erros}"
    )
