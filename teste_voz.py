import pyttsx3
import speech_recognition as sr
import edge_tts as e_tts
import pygame as pg
import asyncio
import os
from groq import Groq
from dotenv import load_dotenv

# Carrega os segredos do arquivo .env
load_dotenv()

# Puxa a chave do cofre (se não achar, avisa que está faltando)
CHAVE_API = os.getenv("CHAVE_GROQ")
if not CHAVE_API:
    raise ValueError("Chave da Groq não encontrada! Verifique o arquivo .env")

cliente = Groq(api_key=CHAVE_API)
rec = sr.Recognizer()
voz_atual = "pt-BR-FranciscaNeural"

def falar(texto):
    try:
        async def gerar_audio():
            comunicacao = e_tts.Communicate(texto, voz_atual)
            await comunicacao.save("resposta.mp3")

        asyncio.run(gerar_audio())    

        pg.mixer.init()
        pg.mixer.music.load("resposta.mp3")
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
        with sr.Microphone() as mic:
            print("\n🎤 Assistente Ativo e Ouvindo...")
            rec.pause_threshold = 1.5
            rec.adjust_for_ambient_noise(mic)
            audio = rec.listen(mic)

            with open('meu_audio.wav', 'wb') as arquivo_wav:
                arquivo_wav.write(audio.get_wav_data())
                
            print("⏳ Processando...")

            with open('meu_audio.wav', 'rb') as arquivo_lido:
                transcricao = cliente.audio.transcriptions.create(
                    file=("meu_audio.wav", arquivo_lido.read()), 
                    model="whisper-large-v3",
                    language="pt"
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
            if "desligar sistema" in texto_ouvido.lower() or "encerrar" in texto_ouvido.lower():
                falar("Desligando o assistente. Até logo!")
                break
                
            falar(f"Você disse: {texto_ouvido}")

if __name__ == "__main__":
    iniciar_assistente()