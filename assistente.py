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
from teste_cerebro import pensar
from teste_voz import ouvir, falar
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


def buscar_ultimo_video(canal):
    """Busca o vídeo mais recente de um canal público usando a YouTube Data API."""
    chave_api = os.getenv("YOUTUBE_API_KEY")
    if not chave_api:
        raise RuntimeError("YOUTUBE_API_KEY não encontrada no arquivo .env")

    def consultar(endpoint, parametros):
        parametros_completos = {**parametros, "key": chave_api}
        url = f"https://www.googleapis.com/youtube/v3/{endpoint}?{urlencode(parametros_completos)}"
        try:
            with urlopen(url, timeout=10) as resposta:
                dados = json.load(resposta)
        except Exception as erro:
            raise RuntimeError("não foi possível consultar a YouTube Data API") from erro
        if "error" in dados:
            raise RuntimeError("a YouTube Data API retornou um erro")
        return dados

    canais = consultar("search", {
        "part": "snippet",
        "q": canal,
        "type": "channel",
        "maxResults": 1,
    }).get("items", [])
    if not canais:
        raise RuntimeError(f"canal não encontrado: {canal}")

    canal_id = canais[0]["snippet"]["channelId"]
    detalhes_canal = consultar("channels", {
        "part": "contentDetails",
        "id": canal_id,
    }).get("items", [])
    if not detalhes_canal:
        raise RuntimeError(f"não foi possível obter os vídeos de: {canal}")

    playlist_uploads = detalhes_canal[0]["contentDetails"]["relatedPlaylists"]["uploads"]
    videos = consultar("playlistItems", {
        "part": "snippet",
        "playlistId": playlist_uploads,
        "maxResults": 1,
    }).get("items", [])
    if not videos:
        raise RuntimeError(f"nenhum vídeo encontrado no canal: {canal}")

    video = videos[0]["snippet"]
    video_id = video["resourceId"]["videoId"]
    return video["title"], f"https://www.youtube.com/watch?v={video_id}"


def extrair_canal_para_ultimo_video(alvo):
    alvo = normalizar_texto(alvo)
    canal = re.sub(
        r"\b(?:o\s+)?ultimo\s+video(?:\s+mais\s+recente)?\b",
        "",
        alvo,
        flags=re.IGNORECASE,
    )
    canal = re.sub(r"\bvideo\s+mais\s+recente\b", "", canal, flags=re.IGNORECASE)
    canal = re.sub(r"\b(?:do|da|de)\b", " ", canal, flags=re.IGNORECASE)
    canal = re.sub(r"\s+", " ", canal).strip(" .?!")
    return canal or alvo


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


def extrair_identificador_canal(alvo):
    """Obtém o nome do canal ou perfil mencionado no comando."""
    texto = limpar_soletracao(alvo)
    padroes = (
        r"\b(?:canal|perfil|streamer)\s+@?([a-zA-Z0-9_\.]+)",
        r"\b(?:do|da|de)\s+@?([a-zA-Z0-9_\.]+)\s+(?:no|na|em)\b",
    )
    for padrao in padroes:
        correspondencia = re.search(padrao, texto, flags=re.IGNORECASE)
        if correspondencia:
            return correspondencia.group(1).strip(".")
    return None


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
    """Confirma divergências e devolve também o nome escolhido pelo usuário."""
    if dicionario.get("acao") != "pesquisar_video":
        return dicionario, None

    soletrado = extrair_soletracao(texto_falado)
    nome_falado = extrair_identificador_canal(dicionario.get("alvo"))
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
        "soletrado", "soletracao", "letras", "segundo", "pixone"
    )):
        nome_escolhido = soletrado
        dicionario["alvo"] = substituir_nome_no_alvo(
            dicionario.get("alvo"), nome_falado, nome_escolhido
        )
    elif any(palavra in resposta_normalizada for palavra in (
        "falado", "primeiro", "pichone"
    )):
        nome_escolhido = nome_falado
    else:
        falar("Vou usar o nome soletrado para evitar confusão.")
        nome_escolhido = soletrado
        dicionario["alvo"] = substituir_nome_no_alvo(
            dicionario.get("alvo"), nome_falado, nome_escolhido
        )
    return dicionario, nome_escolhido


print("Iniciando o V-Inc...")
falar("Iniciando o V-Inc...")

while True:
    try:    
        texto_falado = ouvir()

        if eh_comando_encerramento(texto_falado):
            print("Encerrando o Sistema...")
            falar("Encerrando o Sistema...")
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

            elif dicionario_resposta['acao'] == "abrir_site":
                site = dicionario_resposta['site']
                alvo = dicionario_resposta['alvo']
                texto_resposta = dicionario_resposta['texto_resposta']
                fala = f"Abrindo site: {texto_resposta}"

                print(fala)
                falar(fala)
                webbrowser.open(f"https://{site}")

            elif dicionario_resposta['acao'] == "pesquisar_video":
                assunto = limpar_soletracao(dicionario_resposta['alvo'] or "lives")
                identificador, plataforma = identificar_plataforma(
                    dicionario_resposta.get('site')
                )
                assunto_normalizado = normalizar_texto(assunto)

                if identificador == "youtube" and (
                    "ultimo video" in assunto_normalizado
                    or "video mais recente" in assunto_normalizado
                ):
                    canal = extrair_canal_para_ultimo_video(assunto)
                    titulo_video, url = buscar_ultimo_video(canal)
                    fala = f"Abrindo o vídeo mais recente de {canal}: {titulo_video}."
                else:
                    consulta = quote_plus(assunto)
                    canal = extrair_identificador_canal(assunto)
                    if canal and identificador in {"twitch", "kick", "instagram", "tiktok", "facebook"}:
                        url = plataforma["canal"].format(canal=quote_plus(canal))
                        fala = f"Abrindo o canal ou perfil {canal} na {plataforma['nome']}."
                    else:
                        url = plataforma["busca"].format(consulta=consulta)
                        fala = f"Pesquisando lives sobre {assunto} na {plataforma['nome']}."

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

    except Exception as e:
        # Se algo der errado cai aqui no except
        print(f"Ops, tive um probleminha: {e}")
        falar("Houve um erro no processamento, mas ainda estou aqui.")