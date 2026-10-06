import os
import subprocess
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
    # Windows
    "calc": "calculadora",
    "calculator": "calculadora",

    "bloco": "bloco de notas",
    "bloco de nota": "bloco de notas",
    "notepad": "bloco de notas",

    "explorer": "file explorer",
    "explorador": "file explorer",
    "explorador de arquivos": "file explorer",
    "gerenciador de arquivos": "file explorer",
    "meus arquivos": "file explorer",

    "config": "configuracoes",
    "configuracao": "configuracoes",
    "configuracoes": "configuracoes",
    "settings": "configuracoes",
    "ajustes": "configuracoes",

    "painel de controle": "control panel",
    "gerenciador de tarefas": "task manager",
    "prompt": "command prompt",
    "prompt de comando": "command prompt",
    "cmd": "command prompt",

    # Navegadores
    "chrome": "google chrome",
    "google": "google chrome",
    "edge": "microsoft edge",
    "fire fox": "firefox",
    "mozilla": "firefox",

    # Desenvolvimento
    "vs code": "visual studio code",
    "vscode": "visual studio code",
    "visual code": "visual studio code",
    "code": "visual studio code",

    "git hub": "github desktop",
    "github": "github desktop",

    "docker": "docker desktop",
    "intellij": "intellij idea",
    "idea": "intellij idea",

    "mongo": "mongodb compass",
    "mongodb": "mongodb compass",

    "workbench": "mysql workbench",
    "mysql": "mysql workbench",

    "ssms": "sql server management studio",
    "sql management studio": "sql server management studio",

    "xampp": "xampp control panel",

    # Escritório
    "power point": "powerpoint",
    "ms word": "word",
    "ms excel": "excel",
    "ms powerpoint": "powerpoint",

    "libre office": "libreoffice",
    "libre office writer": "libreoffice writer",
    "libre office calc": "libreoffice calc",
    "libre office impress": "libreoffice impress",

    # Outros nomes comuns
    "power bi": "power bi desktop",
    "virtual box": "oracle virtualbox",
    "packet tracer": "cisco packet tracer",
}


APLICATIVOS_SISTEMA = {
    "calculadora": ["calc.exe"],
    "bloco de notas": ["notepad.exe"],
    "paint": ["mspaint.exe"],
    "file explorer": ["explorer.exe"],
    "command prompt": ["cmd.exe"],
    "task manager": ["taskmgr.exe"],
    "control panel": ["control.exe"],
}

APLICATIVOS_URI = {
    "configuracoes": {
        "uri": "ms-settings:",
        "nome": "configurações",
    },
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
    nome_normalizado = normalizar_nome(nome_solicitado)
    nome_normalizado = ALIASES.get(nome_normalizado, nome_normalizado)

    if nome_normalizado in APLICATIVOS_URI:
        aplicativo = APLICATIVOS_URI[nome_normalizado]

        try:
            os.startfile(aplicativo["uri"])

            return {
                "status": "aberto",
                "nome": aplicativo["nome"],
            }

        except OSError as erro:
            print(
                f"Não foi possível abrir "
                f"{aplicativo['nome']}: {erro}"
            )

            return {
                "status": "erro",
                "nome": aplicativo["nome"],
            }

    if nome_normalizado in APLICATIVOS_SISTEMA:
        comando = APLICATIVOS_SISTEMA[nome_normalizado]

        try:
            if nome_normalizado == "command prompt":
                subprocess.Popen(
                    comando,
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                )
            elif nome_normalizado == "task manager":
                os.startfile("taskmgr.exe")
            else:
                subprocess.Popen(comando)

            return {
                "status": "aberto",
                "nome": nome_normalizado,
            }

        except OSError as erro:
            print(f"Não foi possível abrir {nome_normalizado}: {erro}")

            return {
                "status": "erro",
                "nome": nome_normalizado,
            }

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