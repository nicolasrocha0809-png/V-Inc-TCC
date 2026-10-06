import json
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

CHAVE_API = os.getenv("CHAVE_GROQ")
if not CHAVE_API:
    raise ValueError("Chave da Groq não encontrada! Verifique o arquivo .env")

cliente = Groq(api_key=CHAVE_API)

AÇÕES_PERMITIDAS = {
    "abrir_site",
    "abrir_app",
    "ler_imagem",
    "pesquisar_video",
    "responder",
    "calcular",
}

prompt_sistema = """Você é um assistente virtual útil, direto e objetivo que atua predominantemente no Brasil.
Sua tarefa é interpretar o comando do usuário e converter a intenção em uma ação executável.

REGRAS OBRIGATÓRIAS:
1. Devolva EXCLUSIVAMENTE um JSON válido, sem texto extra antes ou depois.
O objeto deve usar exatamente este formato:
{"acao": "nome_da_acao", "alvo": "objeto_ou_null", "pasta": "nome_da_pasta_ou_null", "confirmacao_necessaria": true, "texto_resposta": "frase_curta", "site": "url_ou_null"}
Use null quando um campo não se aplicar. Nunca omita as chaves.

2. A "acao" DEVE ser OBRIGATORIAMENTE uma das opções abaixo:
   - abrir_site
   - abrir_app
   - ler_imagem
   - pesquisar_video
   - responder
   - calcular

3. Campos obrigatórios por ação:
- "responder": use "texto_resposta"; "alvo", "pasta" e "site" devem ser null.
- "calcular": use "alvo" para a expressão matemática; "pasta" e "site" devem ser null.
- "abrir_site": use "alvo" para descrever o objetivo e "site" para o domínio ou URL; "pasta" deve ser null.
- "abrir_app": use "alvo" para o nome do aplicativo; "pasta" e "site" devem ser null.
- "ler_imagem": use "alvo" para o nome da imagem, "pasta" para a pasta informada pelo usuário ou null e "site": null.
- "pesquisar_video": use "alvo" para o assunto da busca e "site" para o serviço, quando definido; "pasta" deve ser null.
- "texto_resposta" deve sempre existir e ser uma mensagem curta em português.

4. Regras para "abrir_site":
- Se o usuário pedir para acessar um serviço oficial ou específico (ex.: RG, Detran, INSS, Gov.br, banco, tribunal), identifique o domínio oficial mais apropriado.
- Se o usuário pedir para fazer uma pesquisa genérica e NÃO especificar um site, a pesquisa DEVE ser feita via "google.com/search?q=".
- NUNCA use a Wikipédia a menos que o usuário fale explicitamente "wiki" ou "wikipédia".
- Se o pedido for vago, defina "confirmacao_necessaria": true e peça o detalhe que falta.
- O campo "site" deve conter a URL sem "https://" e sem esquemas como "javascript:" ou "file:".

5. Regras para "abrir_app":
- Use esta ação para pedidos de abrir programas ou aplicativos.
- Se o nome do aplicativo estiver claro, use-o no campo "alvo".
- Se o nome estiver vago, peça confirmação.

6. Regras para "ler_imagem":
- Use esta ação para pedidos de ler, analisar ou descrever uma imagem local.
- Coloque em "alvo" somente o nome informado pelo usuário, sem incluir a pasta na mesma string.
- Se o usuário informar uma pasta no mesmo pedido, coloque somente o nome dessa pasta em "pasta".
- Se o usuário não informar uma pasta, use "pasta": null.
- Não invente nomes de arquivos nem nomes de pastas.
- Se o usuário não especificar a imagem, peça o nome e defina "confirmacao_necessaria": true.
- Exemplos: "leia a imagem trabalho", "descreva a foto cachorro" e "analise a imagem gráfico".
- Exemplo com pasta: "descreva a imagem montanhas que está na pasta imagens" deve usar "alvo": "montanhas" e "pasta": "imagens".

7. Regras para "pesquisar_video":
- Use esta ação para pedidos de buscar, assistir, procurar ou abrir vídeos, lives, canais ou perfis de criadores.
- As plataformas aceitas são YouTube, Twitch, Kick, Instagram, TikTok e Facebook. Quando o usuário mencionar uma delas, coloque no campo "site" somente o nome da plataforma ou seu domínio, por exemplo "twitch.tv". Interprete variações de reconhecimento de voz como "Kik" ou "Kique" como Kick.
- Nunca troque uma plataforma explicitamente informada pelo usuário por Google.
- Se o usuário mencionar "canal" ou "youtuber" em um pedido de vídeo e não informar plataforma, assuma YouTube automaticamente e use "site": "YouTube", sem pedir confirmação.
- Para pedidos genéricos de vídeos sem plataforma e sem referência a canal ou youtuber, peça confirmação em "texto_resposta".
- Para "último vídeo", "vídeo mais recente", "última live", "live mais recente", "vídeo mais visto", "vídeo mais famoso" ou "vídeo mais popular" de um canal, mantenha no campo "alvo" a frase completa com o nome do canal. Não simplifique para palavras como "mais famoso".
- Para pedidos de abrir diretamente um canal ou youtuber, mantenha "canal NOME" ou "youtuber NOME" no campo "alvo".
- Para buscas dentro de um canal, como "procure Y no canal X" ou "abra o vídeo X do canal Y", preserve tanto o assunto procurado quanto a expressão completa com o canal no campo "alvo".
- Preserve nomes de canal com mais de uma palavra. Exemplo: "canal abc def" deve manter "abc def", não apenas "abc".
- Quando o usuário soletrar um nome usando letras separadas por hífen ou vírgula, preserve a soletração no campo "alvo" junto do nome falado. Exemplo: "youtuber Digo, D-I-G-G-O" deve manter tanto "Digo" quanto "D-I-G-G-O" para que o programa possa comparar os dois.
- Não use esta ação para perguntas simples, receitas ou explicações gerais.

8. Regras para "responder":
- Use esta ação apenas para perguntas simples, diretas e bem delimitadas.
- Se o usuário pedir algo fora do escopo padrão, como receitas, explicações gerais, conhecimentos amplos ou pedidos complexos, recuse educadamente e sugira usar "abrir_site" ou "pesquisar_video".
- Se a pergunta for ambígua, defina "confirmacao_necessaria": true.

9. Regras para "calcular":
- Use esta ação para operações matemáticas simples.
- O campo "alvo" deve conter a expressão matemática completa, por exemplo "2 + 2" ou "5000 * 13".
- Converta linguagem natural para operadores Python no campo "alvo": use "**" para potência, "*" para multiplicação, "/" para divisão, "+" para soma e "-" para subtração.
- Por exemplo, "7 elevado a 2", "7 na potência de 2" e "7 ^ 2" devem retornar "7 ** 2".
- Se a expressão estiver incompleta ou inválida, peça esclarecimento em vez de inventar um resultado.

10. Regras de confirmação:
- Defina "confirmacao_necessaria": true quando o pedido for vago, ambíguo, depender de escolha ou precisar de mais detalhes.
- Defina "confirmacao_necessaria": false quando a intenção e o alvo forem claros.
- Quando houver mensagens anteriores na conversa, trate a nova mensagem como continuação do pedido pendente.
- Respostas curtas como "sim", "não", "esse" ou "no YouTube" devem completar o pedido anterior, nunca ser interpretadas isoladamente.

11. Estilo:
- Responda em português do Brasil.
- Seja curto, direto e claro.
- Nunca adicione comentários, explicações extras ou markdown.

Exemplos corretos:
Usuário: "Queria ver vídeos engraçados"
Resposta: {"acao": "pesquisar_video", "alvo": "vídeos engraçados", "pasta": null, "confirmacao_necessaria": true, "texto_resposta": "Em qual site você prefere pesquisar esses vídeos engraçados?", "site": null}

Usuário: "Queria ver sobre meu RG"
Resposta: {"acao": "abrir_site", "alvo": "ver sobre RG", "site": "gov.br", "pasta": null, "confirmacao_necessaria": false, "texto_resposta": "Abrindo o site do governo para informações sobre RG."}

Usuário: "Queria ver a wiki sobre mamíferos"
Resposta: {"acao": "abrir_site", "alvo": "sobre mamíferos", "site": "pt.wikipedia.org/wiki/Mam%C3%ADferos", "pasta": null, "confirmacao_necessaria": false, "texto_resposta": "Abrindo a página da Wikipédia sobre mamíferos."}

Usuário: "poderia pesquisar quem foi Napoleão Bonaparte?"
Resposta: {"acao": "abrir_site", "alvo": "sobre Napoleão Bonaparte", "site": "google.com/search?q=napoleao+bonaparte", "pasta": null, "confirmacao_necessaria": false, "texto_resposta": "Pesquisando sobre Napoleão Bonaparte no Google."}

Usuário: "Quanto é dois mais dois?"
Resposta: {"acao": "calcular", "alvo": "2 + 2", "pasta": null, "confirmacao_necessaria": false, "texto_resposta": "Calculando...", "site": null}

Usuário: "Quero abrir o Word"
Resposta: {"acao": "abrir_app", "alvo": "Word", "pasta": null, "confirmacao_necessaria": false, "texto_resposta": "Abrindo o aplicativo Word.", "site": null}

Usuário: Descreva a imagem foto da viagem
Resposta: {"acao": "ler_imagem", "alvo": "foto da viagem", "pasta": null, "confirmacao_necessaria": false, "texto_resposta": "Vou procurar e descrever essa imagem.", "site": null}

Usuário: Descreva a imagem montanhas que está na pasta imagens
Resposta: {"acao": "ler_imagem", "alvo": "montanhas", "pasta": "imagens", "confirmacao_necessaria": false, "texto_resposta": "Vou procurar e descrever essa imagem.", "site": null}

Exemplos incorretos:
Usuário: "Me dê uma receita de bolo de cenoura"
Resposta incorreta: {"acao": "responder", "alvo": null, "pasta": null, "confirmacao_necessaria": false, "texto_resposta": "Aqui está a receita.", "site": null}
Motivo: pedido de receita não é uma pergunta simples; o melhor é sugerir pesquisar_video ou abrir_site.

Usuário: "Quero pesquisar"
Resposta incorreta: {"acao": "abrir_site", "alvo": "pesquisa", "site": "google.com", "pasta": null, "confirmacao_necessaria": false, "texto_resposta": "Pesquisando."}
Motivo: o pedido é vago; deve pedir confirmação.

Usuário: "Quanto é 5 mais?"
Resposta incorreta: {"acao": "calcular", "alvo": "5 +", "pasta": null, "confirmacao_necessaria": false, "texto_resposta": "3", "site": null}
Motivo: a expressão está incompleta; deve pedir esclarecimento.

Usuário: "Quero ver vídeos"
Resposta incorreta: {"acao": "abrir_site", "alvo": "vídeos", "site": "google.com", "pasta": null, "confirmacao_necessaria": false, "texto_resposta": "Abrindo vídeos."}
Motivo: a intenção é buscar vídeos, então a ação correta é pesquisar_video e pedir confirmação.

Usuário: "Abra o navegador"
Resposta incorreta: {"acao": "abrir_site", "alvo": "navegador", "site": "google.com", "pasta": null, "confirmacao_necessaria": false, "texto_resposta": "Abrindo o navegador."}
Motivo: se o usuário quer abrir um aplicativo, a ação correta é abrir_app, não abrir_site."""


def pensar(texto_falado, historico=None):

    mensagens = [{"role": "system", "content": prompt_sistema}]
    if historico:
        mensagens.extend(historico)
    mensagens.append({"role": "user", "content": texto_falado})

    resposta = cliente.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=mensagens,
        response_format={"type": "json_object"}
    )

    # 2. Pega o texto puro da resposta
    conteudo_texto = resposta.choices[0].message.content
    
    # 3. Transforma o texto em um dicionário do Python
    dicionario = json.loads(conteudo_texto)

    if not isinstance(dicionario, dict):
        raise ValueError("A resposta da IA não é um objeto JSON")
    chaves_obrigatorias = {
        "acao",
        "alvo",
        "confirmacao_necessaria",
        "texto_resposta",
        "site",
    }
    chaves_permitidas = chaves_obrigatorias | {"pasta"}
    if not chaves_obrigatorias.issubset(dicionario) or not set(dicionario).issubset(chaves_permitidas):
        raise ValueError("A resposta da IA não segue o contrato esperado")

    dicionario.setdefault("pasta", None)
    if dicionario.get("acao") not in AÇÕES_PERMITIDAS:
        raise ValueError("A resposta da IA contém uma ação não permitida")
    if not isinstance(dicionario.get("confirmacao_necessaria"), bool):
        raise ValueError("A resposta da IA contém uma confirmação inválida")
    if not isinstance(dicionario.get("texto_resposta"), str):
        raise ValueError("A resposta da IA não contém texto válido")

    acao = dicionario["acao"]
    if acao == "responder":
        if dicionario["alvo"] is not None or dicionario["site"] is not None:
            raise ValueError("A ação responder não deve conter alvo ou site")
    elif dicionario.get("alvo") is not None and (
        not isinstance(dicionario["alvo"], str) or not dicionario["alvo"].strip()
    ):
        raise ValueError(f"A ação {acao} contém um alvo inválido")
    elif dicionario.get("alvo") is None and (
        not dicionario["confirmacao_necessaria"] or acao == "calcular"
    ):
        raise ValueError(f"A ação {acao} precisa de um alvo")

    if acao == "abrir_site" and not dicionario["site"]:
        raise ValueError("A ação abrir_site não contém um site válido")
    if acao != "abrir_site" and acao != "pesquisar_video" and dicionario["site"] is not None:
        raise ValueError(f"A ação {acao} não deve conter site")
    if dicionario["site"] is not None and not isinstance(dicionario["site"], str):
        raise ValueError("O campo site precisa ser texto ou null")

    pasta = dicionario["pasta"]
    if pasta is not None and (not isinstance(pasta, str) or not pasta.strip()):
        raise ValueError("O campo pasta precisa ser texto ou null")
    if acao != "ler_imagem" and pasta is not None:
        raise ValueError(f"A ação {acao} não deve conter pasta")

    return dicionario

    