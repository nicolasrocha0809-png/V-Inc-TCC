import ast
import json
import operator
import re
import unicodedata

from teste_cerebro import pensar
from teste_voz import ouvir, falar
import webbrowser


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

print("Iniciando o V-Inc...")
falar("Iniciando o V-Inc...")

while True:
    try:    
        texto_falado = ouvir()

        if eh_comando_encerramento(texto_falado):
            print("Encerrando o Sistema...")
            falar("Encerrando o Sistema...")

            break
           

        dicionario_resposta = pensar(texto_falado)
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