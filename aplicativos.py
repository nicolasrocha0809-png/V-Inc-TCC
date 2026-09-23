import os
from pathlib import Path
import unicodedata
from difflib import get_close_matches


def obter_pastas_de_aplicativos():
    pastas = [
        Path(os.getenv("APPDATA", ""))
        / "Microsoft/Windows/Start Menu/Programs",

        Path(os.getenv("PROGRAMDATA", ""))
        / "Microsoft/Windows/Start Menu/Programs",

        Path(os.getenv("USERPROFILE", ""))
        / "Desktop",

        Path(os.getenv("PUBLIC", ""))
        / "Desktop",
    ]

    return [pasta for pasta in pastas if pasta.exists()]


ALIASES = {
    "vs code": "visual studio code",
    "vscode": "visual studio code",
    "chrome": "google chrome",
    "opera": "navegador opera gx",
    "explorador": "file explorer",
    "explorador de arquivos": "file explorer",
}


def normalizar_nome(nome):
    nome = unicodedata.normalize("NFKD", nome)

    nome = "".join(
        caractere
        for caractere in nome
        if not unicodedata.combining(caractere)
    )

    return nome.lower().strip()


def buscar_aplicativos(nome_solicitado, aplicativos):
    nome_normalizado = normalizar_nome(nome_solicitado)
    nome_normalizado = ALIASES.get(nome_normalizado, nome_normalizado)

    # Primeiro procura pelo nome exato
    if nome_normalizado in aplicativos:
        return [nome_normalizado]

    # Depois procura aplicativos que contenham o nome solicitado
    resultados_parciais = [
        nome
        for nome in aplicativos
        if nome_normalizado in nome
    ]

    if resultados_parciais:
        return resultados_parciais

    # Por último, procura nomes parecidos
    return get_close_matches(
        nome_normalizado,
        aplicativos.keys(),
        n=5,
        cutoff=0.6,
    )


def encontrar_atalhos():
    atalhos = {}

    for pasta in obter_pastas_de_aplicativos():
        for caminho in pasta.rglob("*.lnk"):
            nome = normalizar_nome(caminho.stem)
            atalhos[nome] = caminho

    return atalhos


def abrir_aplicativo(nome_solicitado):
    aplicativos = encontrar_atalhos()
    resultados = buscar_aplicativos(nome_solicitado, aplicativos)

    if not resultados:
        return {
            "status": "nao_encontrado",
            "nome": nome_solicitado,
        }

    if len(resultados) > 1:
        return {
            "status": "ambiguo",
            "opcoes": resultados,
        }

    nome_encontrado = resultados[0]
    caminho = aplicativos[nome_encontrado]

    try:
        os.startfile(caminho)

        return {
            "status": "aberto",
            "nome": nome_encontrado,
        }

    except OSError as erro:
        print(f"Não foi possível abrir {nome_encontrado}: {erro}")

        return {
            "status": "erro",
            "nome": nome_encontrado,
        }


if __name__ == "__main__":
    print(abrir_aplicativo("VS Code"))
    print(abrir_aplicativo("Visual Studio"))
    print(abrir_aplicativo("programa completamente inexistente"))