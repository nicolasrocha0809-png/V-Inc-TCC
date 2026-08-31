import asyncio
import os
from dotenv import load_dotenv
import edge_tts as e_tts
from groq import Groq
import pygame as pg
import pyttsx3
import speech_recognition as sr
from config import settings 

# Carrega os segredos do arquivo .env
load_dotenv()

# Puxa a chave do cofre (se não achar, avisa que está faltando)
CHAVE_API = os.getenv("CHAVE_GROQ")
if not CHAVE_API:
    raise ValueError("Chave da Groq não encontrada! Verifique o arquivo .env")

cliente = Groq(api_key=CHAVE_API)
rec = sr.Recognizer()

# Mapeamento de vozes e códigos de idioma para o Whisper e Edge-TTS
MAPA_IDIOMAS = {
    "pt_BR": {"whisper": "pt", "voz": "pt-BR-FranciscaNeural"},
    "en_US": {"whisper": "en", "voz": "en-US-AriaNeural"},
    "es_ES": {"whisper": "es", "voz": "es-ES-ElviraNeural"}
}

def obter_configuracao_idioma():
    """Busca o idioma atual nas configurações ou usa pt_BR como padrão."""
    sigla = settings.get("geral", "idioma") or "pt_BR"
    return MAPA_IDIOMAS.get(sigla, MAPA_IDIOMAS["pt_BR"])

def falar(texto):
    try:
        # Pega a voz dinâmica com base no idioma salvo nas configurações
        cfg_idioma = obter_configuracao_idioma()
        voz_atual = cfg_idioma["voz"]

        # 1. Lê a velocidade configurada no slider (0 a 100)
        valor_velocidade = int(settings.get("audio", "velocidade") or 80)
        taxa_calculada = int((valor_velocidade - 50) * 1.5) 
        rate_str = f"+{taxa_calculada}%" if taxa_calculada >= 0 else f"{taxa_calculada}%"

        # 2. Lê o volume configurado no slider (0 a 100) e converte para a escala do Pygame (0.0 a 1.0)
        valor_volume_slider = int(settings.get("audio", "volume") or 80)
        volume_decimal = valor_volume_slider / 100.0

        async def gerar_audio():
            comunicacao = e_tts.Communicate(texto, voz_atual, rate=rate_str)
            await comunicacao.save("resposta.mp3")

        asyncio.run(gerar_audio())
        
        # 3. Reproduz o áudio aplicando o volume de forma independente
        pg.mixer.init()
        pg.mixer.music.load("resposta.mp3")
        pg.mixer.music.set_volume(volume_decimal)
        pg.mixer.music.play()
        
        while pg.mixer.music.get_busy():
            pg.time.Clock().tick(10)
            
        pg.mixer.music.unload()
        pg.mixer.quit()
        if os.path.exists("resposta.mp3"):
            os.remove("resposta.mp3")

    except Exception as e:
        print(f"Erro no edge-tts: {e}")
        motor = pyttsx3.init()
        motor.say(texto)
        motor.runAndWait()

def ouvir():
    try:
        # Pega o código de idioma correto para o Whisper (ex: 'pt', 'en', 'es')
        cfg_idioma = obter_configuracao_idioma()
        lang_whisper = cfg_idioma["whisper"]

        with sr.Microphone() as mic:
            print(f"\nAssistente ativo e ouvindo ({lang_whisper})...")
            rec.pause_threshold = 1.5
            rec.adjust_for_ambient_noise(mic)
            audio = rec.listen(mic)

            with open('meu_audio.wav', 'wb') as arquivo_wav:
                arquivo_wav.write(audio.get_wav_data())
                
            print("Processando audio...")

            with open('meu_audio.wav', 'rb') as arquivo_lido:
                transcricao = cliente.audio.transcriptions.create(
                    file=("meu_audio.wav", arquivo_lido.read()), 
                    model="whisper-large-v3",
                    language=lang_whisper  # Idioma dinâmico aplicado aqui!
                )
            
            texto = transcricao.text
            print(f'Você disse: {texto}')
            return texto
    except Exception as e:
        print(f"Não foi possível escutar: {e}")
        return ""

def iniciar_assistente():
    falar("Acesso liberado. Assistente de voz ativado.")
    
    while True:
        texto_ouvido = ouvir()
        
        if texto_ouvido:
            if "desligar sistema" in texto_ouvido.lower() or "encerrar" in texto_ouvido.lower() or "exit" in texto_ouvido.lower() or "salir" in texto_ouvido.lower():
                falar("Desligando o assistente. Até logo!")
                break
                
            falar(f"Você disse: {texto_ouvido}")

if __name__ == "__main__":
    iniciar_assistente()