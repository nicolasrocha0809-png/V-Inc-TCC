import os
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


def normalizar_nome(nome):
    nome = unicodedata.normalize("NFKD", nome)

    nome = "".join(
        caractere
        for caractere in nome
        if not unicodedata.combining(caractere)
    )

    return nome.lower().strip()


def obter_pastas_de_imagens():
    pasta_usuario = Path(os.getenv("USERPROFILE", Path.home()))

    pastas = [
        pasta_usuario / "Downloads",
        pasta_usuario / "Documents",
        pasta_usuario / "Desktop",
        pasta_usuario / "Pictures",
    ]

    for variavel in ("OneDrive", "OneDriveConsumer", "OneDriveCommercial"):
        caminho_onedrive = os.getenv(variavel)

        if caminho_onedrive:
            onedrive = Path(caminho_onedrive)

            pastas.extend([
                onedrive / "Documents",
                onedrive / "Desktop",
                onedrive / "Pictures",
            ])

    pastas_existentes = []
    caminhos_adicionados = set()

    for pasta in pastas:
        caminho_normalizado = str(pasta).lower()

        if pasta.exists() and caminho_normalizado not in caminhos_adicionados:
            pastas_existentes.append(pasta)
            caminhos_adicionados.add(caminho_normalizado)

    return pastas_existentes


def encontrar_imagens():
    imagens = []

    for pasta in obter_pastas_de_imagens():
        try:
            for caminho in pasta.rglob("*"):
                if (
                    caminho.is_file()
                    and caminho.suffix.lower() in EXTENSOES_IMAGEM
                ):
                    imagens.append(caminho)

        except OSError as erro:
            print(f"Não foi possível acessar {pasta}: {erro}")

    return imagens


def buscar_imagens(nome_solicitado):
    imagens = encontrar_imagens()
    nome_normalizado = normalizar_nome(nome_solicitado)

    # Primeiro procura pelo nome exato, ignorando a extensão
    resultados_exatos = [
        caminho
        for caminho in imagens
        if normalizar_nome(caminho.stem) == nome_normalizado
    ]

    if resultados_exatos:
        return resultados_exatos

    # Depois procura nomes que contenham o texto solicitado
    resultados_parciais = [
        caminho
        for caminho in imagens
        if nome_normalizado in normalizar_nome(caminho.stem)
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

    return [
        caminho
        for caminho in imagens
        if normalizar_nome(caminho.stem) in nomes_parecidos
    ]


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

        modelo = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
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


if __name__ == "__main__":
    resultado = localizar_imagem("Triceps-pulley-corda-1")

    if resultado["status"] == "encontrada":
        print(f"Descrevendo: {resultado['caminho']}")
        print()
        print(descrever_imagem(resultado["caminho"]))

    else:
        print(resultado)