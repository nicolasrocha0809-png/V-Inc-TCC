from teste_cerebro import pensar
from teste_voz import ouvir, falar
import webbrowser

print("Iniciando o V-Inc...")
falar("Iniciando o V-Inc...")

while True:
    try:    
        texto_falado = ouvir()

        if "sair" in texto_falado.lower() or "encerrar" in texto_falado.lower():
            print("Encerrando o Sistema...")
            falar("Encerrando o Sistema...")

            break
           

        dicionario_resposta = pensar(texto_falado)

        print(f"A IA decidiu fazer a ação: {dicionario_resposta['acao']}")

        while dicionario_resposta['confirmacao_necessaria'] == True:

            resposta = dicionario_resposta['texto_resposta']
            
            print(resposta)
            falar(resposta)

            texto_falado = ouvir()
            dicionario_resposta = pensar(texto_falado)

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
                resultado = eval(equacao)

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