import ast
from datetime import datetime
import json
import os
import operator
import re
import unicodedata
from urllib.parse import quote_plus, urlencode
from urllib.request import urlopen

from dotenv import load_dotenv

from supabase import create_client
from config import settings  
from servicos.cerebro import pensar
from servicos.voz import ouvir, falar, tocar_sinal
from servicos.aplicativos import abrir_aplicativo
from servicos.imagens import localizar_imagem, descrever_imagem
import webbrowser

load_dotenv()


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = (
    create_client(SUPABASE_URL, SUPABASE_KEY)
    if SUPABASE_URL and SUPABASE_KEY
    else None
)


def salvar_comando_historico(comando_texto):
    """Salva o comando no Supabase usando dinamicamente o ID do usuário ativo"""
    if supabase:
        try:
            user_id_atual = settings.get("usuario", "id_usuario_atual")
            
            if not user_id_atual:
                print("DEBUG: Nenhum usuário logado encontrado no settings. O histórico não será salvo.")
                return

            supabase.table("historico").insert({
                "id_usuario": user_id_atual,
                "comando": comando_texto,
                "data_hora": datetime.now().isoformat(),
            }).execute()
            print(f"DEBUG: Comando salvo no Supabase para o usuário ID -> {user_id_atual}")
        except Exception as e:
            print(f"Erro ao salvar histórico no assistente: {e}")


OPERADORES_BINARIOS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

OPERADORES_UNARIOS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def calcular_expressao(expressao):
    """Avalia apenas expressões matemáticas sem nomes, chamadas ou atributos."""
    expressao = expressao.strip()
    expressao = unicodedata.normalize("NFKD", expressao)
    expressao = "".join(
        caractere for caractere in expressao
        if not unicodedata.combining(caractere)
    )
    expressao = re.sub(
        r"\bpotencia\s+de\s+(-?\d+(?:[.,]\d+)?)\s+por\s+(-?\d+(?:[.,]\d+)?)\b",
        r"\1 ** \2",
        expressao,
        flags=re.IGNORECASE,
    )
    expressao = re.sub(
        r"\b(-?\d+(?:[.,]\d+)?)\s+potencia(?:\s+de)?\s+(-?\d+(?:[.,]\d+)?)\b",
        r"\1 ** \2",
        expressao,
        flags=re.IGNORECASE,
    )
    expressao = re.sub(r"\^", "**", expressao)
    expressao = re.sub(r"\belevad[ao]s?\s+a\b", "**", expressao, flags=re.IGNORECASE)
    expressao = re.sub(r"\bvezes\b", "*", expressao, flags=re.IGNORECASE)
    expressao = re.sub(r"\bdividido\s+por\b", "/", expressao, flags=re.IGNORECASE)
    expressao = re.sub(r"\bsobre\b", "/", expressao, flags=re.IGNORECASE)
    expressao = re.sub(r"\bmais\b", "+", expressao, flags=re.IGNORECASE)
    expressao = re.sub(r"\bmenos\b", "-", expressao, flags=re.IGNORECASE)
    expressao = re.sub(r"(?<=\d),(?=\d)", ".", expressao)

    try:
        arvore = ast.parse(expressao, mode="eval")
    except (SyntaxError, TypeError) as erro:
        raise ValueError("expressão matemática inválida") from erro

    def avaliar(no):
        if isinstance(no, ast.Expression):
            return avaliar(no.body)
        if isinstance(no, ast.Constant) and isinstance(no.value, (int, float)):
            return no.value
        if isinstance(no, ast.BinOp) and type(no.op) in OPERADORES_BINARIOS:
            esquerda = avaliar(no.left)
            direita = avaliar(no.right)
            if isinstance(no.op, ast.Pow) and abs(direita) > 100:
                raise ValueError("potência muito grande")
            return OPERADORES_BINARIOS[type(no.op)](esquerda, direita)
        if isinstance(no, ast.UnaryOp) and type(no.op) in OPERADORES_UNARIOS:
            return OPERADORES_UNARIOS[type(no.op)](avaliar(no.operand))
        raise ValueError("a expressão contém elementos não permitidos")

    resultado = avaliar(arvore)
    if not isinstance(resultado, (int, float)):
        raise ValueError("resultado matemático inválido")
    return resultado


def normalizar_texto(texto):
    texto_sem_acentos = unicodedata.normalize("NFKD", texto)
    return "".join(
        caractere for caractere in texto_sem_acentos
        if not unicodedata.combining(caractere)
    ).lower().strip()


def eh_comando_encerramento(texto):
    texto_normalizado = normalizar_texto(texto)
    return any(frase in texto_normalizado for frase in (
        "encerrar",
        "encerar",
        "desligar sistema",
        "desligar o sistema",
        "sair do programa",
        "fechar o programa",
        "exit",
        "salir",
    ))


def consultar_youtube(endpoint, parametros):
    """Consulta endpoints públicos da YouTube Data API usando a chave do .env."""
    chave_api = os.getenv("YOUTUBE_API_KEY")
    if not chave_api:
        raise RuntimeError("YOUTUBE_API_KEY não encontrada no arquivo .env")

    parametros_completos = {**parametros, "key": chave_api}
    url = (
        f"https://www.googleapis.com/youtube/v3/{endpoint}?"
        f"{urlencode(parametros_completos)}"
    )

    try:
        with urlopen(url, timeout=10) as resposta:
            dados = json.load(resposta)
    except Exception as erro:
        raise RuntimeError("não foi possível consultar a YouTube Data API") from erro

    if "error" in dados:
        raise RuntimeError("a YouTube Data API retornou um erro")

    return dados


def _chave_comparacao_canal(texto):
    texto = normalizar_texto(texto or "")
    return re.sub(r"[^a-z0-9]+", "", texto)


def _similaridade_canal(nome_procurado, nome_encontrado):
    # Compara nomes tolerando espaços e pequenos erros do reconhecimento de voz.
    procurado = _chave_comparacao_canal(nome_procurado)
    encontrado = _chave_comparacao_canal(nome_encontrado)

    if not procurado or not encontrado:
        return 0.0

    if procurado == encontrado:
        return 1.0

    anterior = list(range(len(encontrado) + 1))

    for indice_a, caractere_a in enumerate(procurado, start=1):
        atual = [indice_a]

        for indice_b, caractere_b in enumerate(encontrado, start=1):
            custo = 0 if caractere_a == caractere_b else 1
            atual.append(min(
                atual[-1] + 1,
                anterior[indice_b] + 1,
                anterior[indice_b - 1] + custo,
            ))

        anterior = atual

    distancia = anterior[-1]
    maior_tamanho = max(len(procurado), len(encontrado))
    return 1.0 - (distancia / maior_tamanho)


def resolver_canal_youtube(canal):
    # Resolve @handle exato ou escolhe, entre os resultados do YouTube,
    # o canal mais plausível considerando nome, relevância e popularidade.
    nome_canal = limpar_nome_canal(canal)

    if not nome_canal:
        raise RuntimeError("nome do canal não informado")

    item_canal = None

    # Handle só é tratado como handle quando o usuário realmente falou/escreveu @.
    if nome_canal.startswith("@"):
        handle = nome_canal[1:].strip()
        itens = consultar_youtube("channels", {
            "part": "snippet,contentDetails,statistics",
            "forHandle": handle,
            "maxResults": 1,
        }).get("items", [])

        if itens:
            item_canal = itens[0]

    if item_canal is None:
        encontrados = consultar_youtube("search", {
            "part": "snippet",
            "q": nome_canal,
            "type": "channel",
            "maxResults": 10,
        }).get("items", [])

        if not encontrados:
            raise RuntimeError(f"canal não encontrado: {nome_canal}")

        ids_por_ordem = []
        posicao_por_id = {}

        for posicao, encontrado in enumerate(encontrados):
            canal_id = (
                encontrado.get("id", {}).get("channelId")
                or encontrado.get("snippet", {}).get("channelId")
            )

            if canal_id and canal_id not in posicao_por_id:
                posicao_por_id[canal_id] = posicao
                ids_por_ordem.append(canal_id)

        if not ids_por_ordem:
            raise RuntimeError(f"canal não encontrado: {nome_canal}")

        detalhes = consultar_youtube("channels", {
            "part": "snippet,contentDetails,statistics",
            "id": ",".join(ids_por_ordem),
            "maxResults": len(ids_por_ordem),
        }).get("items", [])

        candidatos = []

        for item in detalhes:
            canal_id = item.get("id")
            titulo = item.get("snippet", {}).get("title", "")
            similaridade = _similaridade_canal(nome_canal, titulo)

            # mas nomes muito diferentes são descartados.
            if similaridade < 0.72:
                continue

            estatisticas = item.get("statistics", {})
            inscritos_texto = estatisticas.get("subscriberCount") or "0"
            visualizacoes_texto = estatisticas.get("viewCount") or "0"

            try:
                inscritos = int(inscritos_texto)
            except (TypeError, ValueError):
                inscritos = 0

            try:
                visualizacoes_canal = int(visualizacoes_texto)
            except (TypeError, ValueError):
                visualizacoes_canal = 0

            posicao = posicao_por_id.get(canal_id, 99)

            # Mantém a relevância da busca do próprio YouTube, mas impede
            # que um canal minúsculo com nome literalmente igual vença
            # automaticamente de um criador muito mais provável.
            bonus_relevancia = max(0.0, 0.25 - (posicao * 0.03))

            digitos_inscritos = max(0, len(str(inscritos)) - 1) if inscritos else 0
            bonus_popularidade = min(0.40, digitos_inscritos * 0.06)

            digitos_views = (
                max(0, len(str(visualizacoes_canal)) - 1)
                if visualizacoes_canal
                else 0
            )
            bonus_views = min(0.20, digitos_views * 0.025)

            pontuacao = (
                similaridade
                + bonus_relevancia
                + bonus_popularidade
                + bonus_views
            )

            candidatos.append((pontuacao, similaridade, -posicao, item))

        if not candidatos:
            raise RuntimeError(
                f"não encontrei um canal parecido o suficiente com {nome_canal}"
            )

        candidatos.sort(
            key=lambda candidato: (
                candidato[0],
                candidato[1],
                candidato[2],
            ),
            reverse=True,
        )

        item_canal = candidatos[0][3]

    uploads = (
        item_canal.get("contentDetails", {})
        .get("relatedPlaylists", {})
        .get("uploads")
    )

    titulo = item_canal.get("snippet", {}).get("title", nome_canal)

    if not uploads:
        raise RuntimeError(f"não foi possível obter os uploads de: {titulo}")

    if normalizar_texto(titulo) != normalizar_texto(nome_canal):
        print(f"Canal resolvido: '{nome_canal}' -> '{titulo}'.")

    return {
        "id": item_canal["id"],
        "titulo": titulo,
        "uploads": uploads,
    }

def listar_uploads_canal(canal, max_resultados=50):
    canal_info = resolver_canal_youtube(canal)
    itens = consultar_youtube("playlistItems", {
        "part": "snippet,contentDetails",
        "playlistId": canal_info["uploads"],
        "maxResults": max(1, min(int(max_resultados), 50)),
    }).get("items", [])
    return canal_info, itens


def obter_detalhes_videos(video_ids):
    ids = [video_id for video_id in video_ids if video_id]
    if not ids:
        return {}

    itens = consultar_youtube("videos", {
        "part": "snippet,statistics,liveStreamingDetails",
        "id": ",".join(ids[:50]),
        "maxResults": min(len(ids), 50),
    }).get("items", [])

    return {item["id"]: item for item in itens}


def item_playlist_video_id(item):
    return (
        item.get("contentDetails", {}).get("videoId")
        or item.get("snippet", {}).get("resourceId", {}).get("videoId")
    )


def video_foi_live(detalhes):
    return bool(detalhes.get("liveStreamingDetails"))


def buscar_ultimo_video(canal):
    """Abre o upload comum mais recente, ignorando lives atuais ou arquivadas."""
    canal_info, itens = listar_uploads_canal(canal, max_resultados=50)
    ids = [item_playlist_video_id(item) for item in itens]
    detalhes_por_id = obter_detalhes_videos(ids)

    for item in itens:
        video_id = item_playlist_video_id(item)
        detalhes = detalhes_por_id.get(video_id)
        if not video_id or not detalhes or video_foi_live(detalhes):
            continue

        titulo = detalhes.get("snippet", {}).get("title", "vídeo")
        return titulo, f"https://www.youtube.com/watch?v={video_id}"

    raise RuntimeError(
        f"não encontrei um vídeo comum recente no canal {canal_info['titulo']}"
    )


def buscar_ultima_live(canal):
    """Busca a transmissão mais recente entre os últimos uploads do canal."""
    canal_info, itens = listar_uploads_canal(canal, max_resultados=50)
    ids = [item_playlist_video_id(item) for item in itens]
    detalhes_por_id = obter_detalhes_videos(ids)

    for item in itens:
        video_id = item_playlist_video_id(item)
        detalhes = detalhes_por_id.get(video_id)
        if not video_id or not detalhes or not video_foi_live(detalhes):
            continue

        titulo = detalhes.get("snippet", {}).get("title", "live")
        return titulo, f"https://www.youtube.com/watch?v={video_id}"

    raise RuntimeError(
        f"não encontrei uma live recente no canal {canal_info['titulo']}"
    )


def buscar_video_mais_visto(canal):
    # Procura o maior viewCount em TODO o catálogo público do canal.
    # Aqui lives antigas também contam: o pedido é "mais visto/mais famoso",
    # diferente de "último vídeo", onde lives continuam sendo ignoradas.
    canal_info = resolver_canal_youtube(canal)
    melhor_video = None
    page_token = None
    paginas = 0

    print(
        f"Analisando os uploads públicos de {canal_info['titulo']} "
        "para encontrar o vídeo mais visto..."
    )

    while True:
        parametros = {
            "part": "snippet,contentDetails",
            "playlistId": canal_info["uploads"],
            "maxResults": 50,
        }

        if page_token:
            parametros["pageToken"] = page_token

        dados_playlist = consultar_youtube("playlistItems", parametros)
        itens = dados_playlist.get("items", [])
        paginas += 1

        ids = [
            item_playlist_video_id(item)
            for item in itens
            if item_playlist_video_id(item)
        ]

        detalhes_por_id = obter_detalhes_videos(ids)

        for video_id in ids:
            detalhes = detalhes_por_id.get(video_id)

            if not detalhes:
                continue

            visualizacoes_texto = (
                detalhes.get("statistics", {}).get("viewCount")
            )

            try:
                visualizacoes = int(visualizacoes_texto or 0)
            except (TypeError, ValueError):
                visualizacoes = 0

            if (
                melhor_video is None
                or visualizacoes > melhor_video["visualizacoes"]
            ):
                melhor_video = {
                    "id": video_id,
                    "titulo": detalhes.get("snippet", {}).get("title", "vídeo"),
                    "visualizacoes": visualizacoes,
                }

        page_token = dados_playlist.get("nextPageToken")

        if not page_token:
            break

    if melhor_video is None:
        raise RuntimeError(
            f"não encontrei vídeos públicos no canal {canal_info['titulo']}"
        )

    print(
        f"Catálogo analisado em {paginas} página(s) da playlist de uploads."
    )

    return (
        melhor_video["titulo"],
        f"https://www.youtube.com/watch?v={melhor_video['id']}",
        str(melhor_video["visualizacoes"]),
    )

def buscar_video_no_canal(canal, consulta):
    """Pesquisa um vídeo específico dentro de um canal."""
    canal_info = resolver_canal_youtube(canal)
    consulta = (consulta or "").strip()

    if not consulta:
        return None

    resultados = consultar_youtube("search", {
        "part": "snippet",
        "channelId": canal_info["id"],
        "q": consulta,
        "type": "video",
        "order": "relevance",
        "maxResults": 10,
    }).get("items", [])

    ids = [
        item.get("id", {}).get("videoId")
        for item in resultados
        if item.get("id", {}).get("videoId")
    ]
    detalhes_por_id = obter_detalhes_videos(ids)

    for video_id in ids:
        detalhes = detalhes_por_id.get(video_id)
        if not detalhes or video_foi_live(detalhes):
            continue

        titulo = detalhes.get("snippet", {}).get("title", "vídeo")
        return titulo, f"https://www.youtube.com/watch?v={video_id}"

    raise RuntimeError(
        f"não encontrei um vídeo sobre {consulta} no canal {canal_info['titulo']}"
    )


def obter_url_canal_youtube(canal):
    canal_info = resolver_canal_youtube(canal)
    return canal_info["titulo"], f"https://www.youtube.com/channel/{canal_info['id']}"


def extrair_canal_para_ultimo_video(alvo):
    canal = extrair_identificador_canal(alvo)
    if canal:
        return canal

    texto = normalizar_texto(limpar_soletracao(alvo))
    texto = re.sub(
        r"\b(?:o\s+)?ultimo\s+video(?:\s+mais\s+recente)?\b",
        " ",
        texto,
        flags=re.IGNORECASE,
    )
    texto = re.sub(r"\bvideo\s+mais\s+recente\b", " ", texto, flags=re.IGNORECASE)
    texto = re.sub(r"\b(?:canal|youtuber|perfil|streamer)\b", " ", texto)
    texto = re.sub(r"\b(?:do|da|de)\b", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip(" .?!")
    return texto or alvo

PLATAFORMAS_LIVE = {
    "youtube": {
        "nome": "YouTube",
        "aliases": ("youtube", "you tube"),
        "busca": "https://www.youtube.com/results?search_query={consulta}",
        "canal": "https://www.youtube.com/@{canal}",
    },
    "twitch": {
        "nome": "Twitch",
        "aliases": ("twitch",),
        "busca": "https://www.twitch.tv/search?term={consulta}",
        "canal": "https://www.twitch.tv/{canal}",
    },
    "kick": {
        "nome": "Kick",
        "aliases": ("kick", "kick.com", "kik"),
        "busca": "https://kick.com/search?query={consulta}",
        "canal": "https://kick.com/{canal}",
    },
    "instagram": {
        "nome": "Instagram",
        "aliases": ("instagram", "insta"),
        "busca": "https://www.instagram.com/explore/search/keyword/?q={consulta}",
        "canal": "https://www.instagram.com/{canal}/",
    },
    "tiktok": {
        "nome": "TikTok",
        "aliases": ("tiktok", "tik tok"),
        "busca": "https://www.tiktok.com/search?q={consulta}",
        "canal": "https://www.tiktok.com/@{canal}",
    },
    "facebook": {
        "nome": "Facebook",
        "aliases": ("facebook", "facebook live", "face"),
        "busca": "https://www.facebook.com/search/videos?q={consulta}",
        "canal": "https://www.facebook.com/{canal}",
    },
}


def identificar_plataforma(site):
    site_normalizado = normalizar_texto(site or "")
    for identificador, dados in PLATAFORMAS_LIVE.items():
        if any(alias in site_normalizado for alias in dados["aliases"]):
            return identificador, dados
    return "youtube", PLATAFORMAS_LIVE["youtube"]


def limpar_soletracao(texto):
    """Remove soletrações do tipo 'Pichone, P-I-X-O-N-E' geradas pelo Whisper."""
    return re.sub(
        r"\s*,?\s*[A-Za-zÀ-ÿ](?:\s*-\s*[A-Za-zÀ-ÿ]){2,}",
        "",
        texto or "",
    ).strip(" ,.-")


def limpar_nome_canal(nome):
    texto = limpar_soletracao(nome or "").strip(" ,.-?!")
    texto = re.sub(
        r"^(?:canal|perfil|streamer|youtuber)\s+(?:(?:do|da|de)\s+)?",
        "",
        texto,
        flags=re.IGNORECASE,
    )
    texto = re.sub(r"^(?:do|da|de)\s+", "", texto, flags=re.IGNORECASE)
    texto = re.sub(
        r"\s+(?:no|na|em)\s+(?:youtube|you\s*tube|twitch|kick|kik|instagram|tiktok|tik\s*tok|facebook)\b.*$",
        "",
        texto,
        flags=re.IGNORECASE,
    )
    texto = re.sub(r"\s+(?:pra|para)\s+mim\b.*$", "", texto, flags=re.IGNORECASE)
    texto = re.sub(r"\s+por\s+favor\b.*$", "", texto, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", texto).strip(" ,.-?!")


def extrair_identificador_canal(alvo):
    """Obtém nomes de canal com uma ou mais palavras, incluindo 'youtuber'."""
    texto = limpar_soletracao(alvo)

    padroes = (
        (
            r"\b(?:canal|perfil|streamer|youtuber)\s+"
            r"(?:(?:do|da|de)\s+)?@?(.+?)"
            r"(?=\s+(?:no|na|em)\s+(?:youtube|you\s*tube|twitch|kick|kik|instagram|tiktok|tik\s*tok|facebook)\b"
            r"|\s+(?:pra|para)\s+mim\b|\s+por\s+favor\b|[?!,;]|$)"
        ),
        (
            r"\b(?:do|da|de)\s+(?:canal\s+)?@?(.+?)\s+"
            r"(?:no|na|em)\s+(?:youtube|you\s*tube|twitch|kick|kik|instagram|tiktok|tik\s*tok|facebook)\b"
        ),
    )

    for padrao in padroes:
        correspondencia = re.search(padrao, texto, flags=re.IGNORECASE)
        if correspondencia:
            nome = limpar_nome_canal(correspondencia.group(1))
            if nome:
                return nome

    return None


def inferir_tipo_busca_video(assunto):
    texto = normalizar_texto(assunto or "")
    canal = extrair_identificador_canal(assunto)

    if any(frase in texto for frase in (
        "ultimo video",
        "video mais recente",
        "video recente",
    )):
        return "ultimo_video"

    if any(frase in texto for frase in (
        "ultima live",
        "live mais recente",
        "ultima transmissao",
        "transmissao mais recente",
    )):
        return "ultima_live"

    if any(frase in texto for frase in (
        "mais visto",
        "mais vista",
        "mais famoso",
        "mais famosa",
        "mais popular",
    )):
        return "mais_visto"

    if (
        canal
        and re.search(r"\b(?:abra|abrir|acesse|acessar|entre|ir)\b", texto)
        and "video" not in texto
        and "live" not in texto
    ):
        return "abrir_canal"

    if canal:
        return "buscar_no_canal"

    return "busca_normal"


def extrair_consulta_video_no_canal(assunto, canal):
    texto = limpar_soletracao(assunto or "")
    nome_falado = extrair_identificador_canal(texto)

    if nome_falado:
        texto = re.sub(re.escape(nome_falado), " ", texto, flags=re.IGNORECASE)
    if canal and normalizar_texto(canal) != normalizar_texto(nome_falado or ""):
        texto = re.sub(re.escape(canal), " ", texto, flags=re.IGNORECASE)

    texto = re.sub(
        r"\b(?:no|do|da|de)\s+(?:canal|perfil|streamer|youtuber)\b",
        " ",
        texto,
        flags=re.IGNORECASE,
    )
    texto = re.sub(r"\b(?:canal|perfil|streamer|youtuber)\b", " ", texto, flags=re.IGNORECASE)
    texto = re.sub(r"\b(?:poderia|pode|por\s+favor)\b", " ", texto, flags=re.IGNORECASE)
    texto = re.sub(r"\b(?:pra|para)\s+mim\b", " ", texto, flags=re.IGNORECASE)
    texto = re.sub(
        r"\b(?:pesquisar|pesquise|procurar|procure|buscar|busque|abrir|abra|assistir)\b",
        " ",
        texto,
        flags=re.IGNORECASE,
    )
    texto = re.sub(r"\b(?:(?:um|uma|o|a)\s+)?(?:vídeo|vídeos|video|videos)\b", " ", texto, flags=re.IGNORECASE)
    texto = re.sub(r"\b(?:no|na|em)\s+(?:youtube|you\s*tube)\b", " ", texto, flags=re.IGNORECASE)
    texto = re.sub(r"\s+", " ", texto).strip(" ,.-?!")

    return texto or None

def extrair_soletracao(texto):
    """Reconstrói letras faladas em formatos como P-I-X-O-N-E."""
    correspondencia = re.search(
        r"\b[A-Za-zÀ-ÿ](?:\s*[-,]\s*[A-Za-zÀ-ÿ]){2,}\b",
        texto or "",
        flags=re.IGNORECASE,
    )
    if not correspondencia:
        return None
    return "".join(re.findall(r"[A-Za-zÀ-ÿ]", correspondencia.group(0))).upper()


def substituir_nome_no_alvo(alvo, nome_antigo, nome_novo):
    if not alvo or not nome_antigo:
        return alvo
    return re.sub(
        re.escape(nome_antigo),
        nome_novo,
        alvo,
        count=1,
        flags=re.IGNORECASE,
    )


def resolver_soletracao(texto_falado, dicionario):
    """Confirma divergências entre o nome reconhecido e o nome soletrado."""
    if dicionario.get("acao") != "pesquisar_video":
        return dicionario, None

    soletrado = extrair_soletracao(texto_falado)
    nome_falado = extrair_identificador_canal(dicionario.get("alvo"))

    if not nome_falado:
        nome_falado = extrair_identificador_canal(texto_falado)

    if not soletrado or not nome_falado:
        return dicionario, None

    if normalizar_texto(nome_falado) == normalizar_texto(soletrado):
        return dicionario, nome_falado

    soletrado_formatado = "-".join(soletrado)
    pergunta = (
        f"Você falou '{nome_falado}', mas informou as letras "
        f"{soletrado_formatado}. "
        "Devo pesquisar usando o nome falado ou o nome soletrado?"
    )
    print(pergunta)
    falar(pergunta)
    resposta = ouvir()
    resposta_normalizada = normalizar_texto(resposta)

    if any(palavra in resposta_normalizada for palavra in (
        "soletrado", "soletracao", "letras", "segundo", "segunda"
    )):
        nome_escolhido = soletrado
    elif any(palavra in resposta_normalizada for palavra in (
        "falado", "primeiro", "primeira"
    )):
        nome_escolhido = nome_falado
    else:
        falar("Vou usar o nome soletrado para evitar confusão.")
        nome_escolhido = soletrado

    dicionario["alvo"] = substituir_nome_no_alvo(
        dicionario.get("alvo"),
        nome_falado,
        nome_escolhido,
    )

    return dicionario, nome_escolhido

print("Iniciando o V-Inc...")
tocar_sinal("iniciar")
falar(
    "V.INC iniciado. Enquanto a palavra de ativação ainda não está disponível, "
    "fale sempre depois do sinal sonoro. Eu aviso quando estiver pronto para ouvir."
)

while True:
    try:    
        texto_falado = ouvir()

        if not texto_falado:
            continue

        if eh_comando_encerramento(texto_falado):
            print("Encerrando o Sistema...")
            falar("Encerrando o Sistema...")
            tocar_sinal("encerrar")
            break
           
        
        salvar_comando_historico(texto_falado)

        dicionario_resposta = pensar(texto_falado)
        dicionario_resposta, nome_escolhido = resolver_soletracao(
            texto_falado, dicionario_resposta
        )
        historico_confirmacao = [
            {"role": "user", "content": texto_falado},
            {"role": "assistant", "content": json.dumps(dicionario_resposta, ensure_ascii=False)},
        ]

        print(f"A IA decidiu fazer a ação: {dicionario_resposta['acao']}")

        while dicionario_resposta['confirmacao_necessaria'] == True:

            resposta = dicionario_resposta['texto_resposta']
            
            print(resposta)
            falar(resposta)

            texto_falado = ouvir()

            if not texto_falado:
                continue

            if eh_comando_encerramento(texto_falado):
                print("Encerrando o Sistema...")
                falar("Encerrando o Sistema...")
                raise SystemExit
            
            dicionario_resposta = pensar(
                texto_falado,
                historico=historico_confirmacao,
            )
            if nome_escolhido and dicionario_resposta.get("acao") == "pesquisar_video":
                alvo_atual = dicionario_resposta.get("alvo") or ""
                nome_atual = extrair_identificador_canal(alvo_atual)
                if nome_atual:
                    dicionario_resposta["alvo"] = substituir_nome_no_alvo(
                        alvo_atual, nome_atual, nome_escolhido
                    )
            historico_confirmacao.extend([
                {"role": "user", "content": texto_falado},
                {"role": "assistant", "content": json.dumps(dicionario_resposta, ensure_ascii=False)},
            ])

        if dicionario_resposta['confirmacao_necessaria'] == False:
            if dicionario_resposta['acao'] == "responder":
                texto_resposta = dicionario_resposta['texto_resposta']

                print(texto_resposta)
                falar(texto_resposta)

            elif dicionario_resposta['acao'] == "abrir_app":
                alvo = dicionario_resposta['alvo']
                aviso_app = f"Vou procurar o aplicativo {alvo}. Só um momento."
                print(aviso_app)
                falar(aviso_app)
                resultado = abrir_aplicativo(alvo)
                status = resultado["status"]

                if status == "aberto":
                    fala = f"Abrindo {resultado['nome']}."

                elif status == "nao_encontrado":
                    fala = (
                        f"Não encontrei o aplicativo {alvo} "
                        "no Menu Iniciar ou na Área de Trabalho."
                    )

                elif status == "ambiguo":
                    opcoes = resultado["opcoes"]

                    opcoes_numeradas = ", ".join(
                        f"{indice + 1}: {nome}"
                        for indice, nome in enumerate(opcoes)
                    )

                    pergunta = (
                        f"Encontrei mais de uma opção para {alvo}: "
                        f"{opcoes_numeradas}. Qual você deseja abrir?"
                    )

                    print(pergunta)
                    falar(pergunta)

                    escolha = ouvir()

                    if not escolha:
                        fala = "Não consegui ouvir sua escolha."

                    else:
                        palavras = set(normalizar_texto(escolha).split())

                        ordinais = {
                            "1": 0,
                            "primeiro": 0,
                            "primeira": 0,
                            "2": 1,
                            "segundo": 1,
                            "segunda": 1,
                            "3": 2,
                            "terceiro": 2,
                            "terceira": 2,
                            "4": 3,
                            "quarto": 3,
                            "quarta": 3,
                            "5": 4,
                            "quinto": 4,
                            "quinta": 4,
                        }

                        indice_escolhido = next(
                            (
                                indice
                                for palavra, indice in ordinais.items()
                                if palavra in palavras and indice < len(opcoes)
                            ),
                            None,
                        )

                        if indice_escolhido is not None:
                            nome_escolhido = opcoes[indice_escolhido]
                        else:
                            nome_escolhido = escolha

                        resultado_escolha = abrir_aplicativo(nome_escolhido)

                        if resultado_escolha["status"] == "aberto":
                            fala = f"Abrindo {resultado_escolha['nome']}."

                        elif resultado_escolha["status"] == "ambiguo":
                            fala = "Sua escolha ainda corresponde a mais de um aplicativo."

                        else:
                            fala = f"Não encontrei o aplicativo {nome_escolhido}."

                else:
                    fala = f"Não consegui abrir o aplicativo {alvo}."

                print(fala)
                falar(fala)

            elif dicionario_resposta['acao'] == "ler_imagem":
                alvo = dicionario_resposta["alvo"]
                pasta = dicionario_resposta.get("pasta")

                if pasta:
                    aviso_busca = (
                        f"Procurando a imagem {alvo} na pasta {pasta}. "
                        "Aguarde um momento."
                    )
                else:
                    aviso_busca = f"Procurando a imagem {alvo}. Aguarde um momento."

                print(aviso_busca)
                falar(aviso_busca)

                resultado = localizar_imagem(
                    alvo,
                    pasta_solicitada=pasta,
                )
                status = resultado["status"]

                if status == "nao_encontrada":
                    if pasta:
                        fala = (
                            f"Não encontrei uma imagem chamada {alvo} "
                            f"na pasta {pasta}."
                        )
                    else:
                        fala = (
                            f"Não encontrei uma imagem chamada {alvo} "
                            "em Downloads, Documentos, Área de Trabalho ou Imagens."
                        )

                elif status == "ambiguo":
                    todas_opcoes = resultado["opcoes"]
                    opcoes = todas_opcoes[:5]

                    opcoes_numeradas = "; ".join(
                        (
                            f"{indice + 1}: {caminho.name}, "
                            f"na pasta {caminho.parent.name}"
                        )
                        for indice, caminho in enumerate(opcoes)
                    )

                    pergunta = (
                        f"Encontrei {len(todas_opcoes)} imagens parecidas. "
                        f"{opcoes_numeradas}. "
                        "Qual delas você deseja descrever?"
                    )

                    print(pergunta)
                    falar(pergunta)

                    escolha = ouvir()

                    if not escolha:
                        fala = "Não consegui ouvir sua escolha."

                    else:
                        escolha_normalizada = normalizar_texto(escolha)
                        palavras = set(escolha_normalizada.split())

                        ordinais = {
                            "1": 0,
                            "primeiro": 0,
                            "primeira": 0,
                            "2": 1,
                            "segundo": 1,
                            "segunda": 1,
                            "3": 2,
                            "terceiro": 2,
                            "terceira": 2,
                            "4": 3,
                            "quarto": 3,
                            "quarta": 3,
                            "5": 4,
                            "quinto": 4,
                            "quinta": 4,
                        }

                        indice_escolhido = next(
                            (
                                indice
                                for palavra, indice in ordinais.items()
                                if palavra in palavras
                                and indice < len(opcoes)
                            ),
                            None,
                        )

                        # Caso o usuário diga o nome da pasta
                        if indice_escolhido is None:
                            correspondencias_pasta = [
                                indice
                                for indice, caminho in enumerate(opcoes)
                                if normalizar_texto(caminho.parent.name)
                                in escolha_normalizada
                            ]

                            if len(correspondencias_pasta) == 1:
                                indice_escolhido = correspondencias_pasta[0]

                        if indice_escolhido is None:
                            fala = (
                                "Não consegui identificar a imagem escolhida. "
                                "Tente informar o número da opção."
                            )

                        else:
                            caminho_escolhido = opcoes[indice_escolhido]

                            aviso_analise = (
                                f"Encontrei {caminho_escolhido.name}, "
                                f"na pasta {caminho_escolhido.parent.name}. "
                                "Vou analisar a imagem agora. Isso pode levar alguns segundos."
                            )

                            print(aviso_analise)
                            falar(aviso_analise)

                            try:
                                fala = descrever_imagem(caminho_escolhido, notificar=falar)

                            except Exception as erro:
                                print(f"Erro ao descrever imagem: {erro}")
                                fala = (
                                    "Encontrei a imagem escolhida, mas não "
                                    "consegui gerar a descrição neste momento."
                                )

                elif status == "encontrada":
                    caminho = resultado["caminho"]

                    aviso_analise = (
                        f"Encontrei {resultado['nome']}. "
                        "Vou analisar a imagem agora. Isso pode levar alguns segundos."
                    )

                    print(aviso_analise)
                    falar(aviso_analise)

                    try:
                        fala = descrever_imagem(caminho, notificar=falar)

                    except Exception as erro:
                        print(f"Erro ao descrever imagem: {erro}")
                        fala = (
                            "Encontrei a imagem, mas não consegui gerar "
                            "a descrição neste momento."
                        )

                else:
                    fala = "Não consegui processar a imagem solicitada."

                print(fala)
                falar(fala)

            elif dicionario_resposta['acao'] == "abrir_site":
                site = dicionario_resposta['site']
                alvo = dicionario_resposta['alvo']
                texto_resposta = dicionario_resposta['texto_resposta']
                fala = f"Abrindo site: {texto_resposta}"

                print(fala)
                falar(fala)
                webbrowser.open(f"https://{site}")

            elif dicionario_resposta['acao'] == "pesquisar_video":
                assunto = limpar_soletracao(dicionario_resposta['alvo'] or "videos")
                identificador, plataforma = identificar_plataforma(
                    dicionario_resposta.get('site')
                )
                assunto_normalizado = normalizar_texto(assunto)
                tipo_busca = inferir_tipo_busca_video(assunto)
                canal = extrair_identificador_canal(assunto)

                if identificador == "youtube" and tipo_busca == "mais_visto":
                    aviso_youtube = (
                        "Vou verificar os vídeos públicos do canal para encontrar "
                        "o mais visto. Em canais grandes, isso pode levar alguns segundos."
                    )
                    print(aviso_youtube)
                    falar(aviso_youtube)
                elif identificador == "youtube" and tipo_busca in {
                    "ultimo_video", "ultima_live", "abrir_canal", "buscar_no_canal"
                }:
                    aviso_youtube = "Vou consultar o YouTube. Só um momento."
                    print(aviso_youtube)
                    falar(aviso_youtube)

                if identificador == "youtube":
                    if tipo_busca == "ultimo_video":
                        canal = canal or extrair_canal_para_ultimo_video(assunto)
                        titulo_video, url = buscar_ultimo_video(canal)
                        fala = (
                            f"Abrindo o vídeo mais recente de {canal}: "
                            f"{titulo_video}."
                        )

                    elif tipo_busca == "ultima_live":
                        if not canal:
                            raise RuntimeError("não consegui identificar o canal da live")
                        titulo_video, url = buscar_ultima_live(canal)
                        fala = f"Abrindo a live mais recente de {canal}: {titulo_video}."

                    elif tipo_busca == "mais_visto":
                        if not canal:
                            raise RuntimeError("não consegui identificar o canal do vídeo")
                        titulo_video, url, visualizacoes = buscar_video_mais_visto(canal)
                        if visualizacoes and visualizacoes.isdigit():
                            visualizacoes_texto = f"{int(visualizacoes):,}".replace(",", ".")
                            fala = (
                                f"Abrindo o vídeo mais visto de {canal}, com aproximadamente "
                                f"{visualizacoes_texto} visualizações: {titulo_video}."
                            )
                        else:
                            fala = f"Abrindo o vídeo mais visto de {canal}: {titulo_video}."

                    elif tipo_busca == "abrir_canal":
                        if not canal:
                            raise RuntimeError("não consegui identificar o canal")
                        titulo_canal, url = obter_url_canal_youtube(canal)
                        fala = f"Abrindo o canal {titulo_canal} no YouTube."

                    elif tipo_busca == "buscar_no_canal":
                        if not canal:
                            raise RuntimeError("não consegui identificar o canal")

                        consulta = extrair_consulta_video_no_canal(assunto, canal)

                        if consulta:
                            resultado_video = buscar_video_no_canal(canal, consulta)
                            if resultado_video:
                                titulo_video, url = resultado_video
                                fala = (
                                    f"Abrindo um vídeo de {canal} sobre {consulta}: "
                                    f"{titulo_video}."
                                )
                        else:
                            titulo_canal, url = obter_url_canal_youtube(canal)
                            fala = f"Abrindo o canal {titulo_canal} no YouTube."

                    else:
                        consulta = quote_plus(assunto)
                        url = plataforma["busca"].format(consulta=consulta)
                        fala = f"Pesquisando por {assunto} no YouTube."

                else:
                    consulta = quote_plus(assunto)
                    canal = canal or extrair_identificador_canal(assunto)

                    if canal and identificador in {
                        "twitch", "kick", "instagram", "tiktok", "facebook"
                    }:
                        url = plataforma["canal"].format(canal=quote_plus(canal))
                        fala = (
                            f"Abrindo o canal ou perfil {canal} "
                            f"na {plataforma['nome']}."
                        )
                    else:
                        url = plataforma["busca"].format(consulta=consulta)
                        tipo_conteudo = (
                            "lives" if "live" in assunto_normalizado else "vídeos"
                        )
                        fala = (
                            f"Pesquisando {tipo_conteudo} sobre {assunto} "
                            f"na {plataforma['nome']}."
                        )

                print(fala)
                falar(fala)
                webbrowser.open(url)

            elif dicionario_resposta['acao'] == "calcular":

                texto_resposta = dicionario_resposta['texto_resposta']
                print(texto_resposta)
                falar(texto_resposta)

                equacao = dicionario_resposta['alvo']
                resultado = calcular_expressao(equacao)

                # 1. Formata no padrão americano com 2 casas decimais: "40,410.50"
                resultado_texto = f"{resultado:,.2f}"

                # 2. Truque para inverter a vírgula e o ponto para o padrão BR:
                resultado_br = resultado_texto.replace(',', 'X').replace('.', ',').replace('X', '.')

                # Agora você tem "40.410,50" prontinho para o print!
                print(f'O resultado de {equacao} é: {resultado_br}')
                falar(f'O resultado é {resultado_br}')

    except SystemExit:
        break

    except KeyboardInterrupt:
        print("\nEncerrando o V.INC com segurança...")
        tocar_sinal("encerrar")
        break

    except Exception as e:
        print(f"Ops, tive um probleminha: {e}")
        tocar_sinal("erro")
        falar(
            "Não consegui concluir esse pedido. Você pode tentar novamente "
            "ou falar de outra forma. Continuo ouvindo."
        )