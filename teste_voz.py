import asyncio
import os
from dotenv import load_dotenv
import edge_tts as e_tts
from groq import Groq
import pygame as pg
import pyttsx3
import speech_recognition as sr
from config import settings
from interface.audio_devices import definir_saida_padrao

# Carrega os segredos do arquivo .env
load_dotenv()

CHAVE_API = os.getenv("CHAVE_GROQ")
if not CHAVE_API:
    raise ValueError("Chave da Groq não encontrada! Verifique o arquivo .env")

cliente = Groq(api_key=CHAVE_API)
rec = sr.Recognizer()

MAPA_IDIOMAS = {
    "pt_BR": {"whisper": "pt", "voz": "pt-BR-FranciscaNeural"},
    "en_US": {"whisper": "en", "voz": "en-US-AriaNeural"},
    "es_ES": {"whisper": "es", "voz": "es-ES-ElviraNeural"},
}


def obter_configuracao_idioma():
    """Busca o idioma atual ou usa pt_BR como padrão."""
    sigla = settings.get("geral", "idioma") or "pt_BR"
    return MAPA_IDIOMAS.get(sigla, MAPA_IDIOMAS["pt_BR"])


def obter_microfone_configurado():
    """Abre o microfone salvo nas preferências ou usa o padrão do sistema."""
    nome_salvo = settings.get("audio", "microfone")

    if not nome_salvo or nome_salvo == "Padrão do sistema":
        return sr.Microphone()

    try:
        nomes = sr.Microphone.list_microphone_names()
        indice = next(
            (i for i, nome in enumerate(nomes) if nome == nome_salvo),
            None,
        )
        if indice is not None:
            return sr.Microphone(device_index=indice)
    except Exception as erro:
        print(f"Não foi possível selecionar o microfone: {erro}")

    return sr.Microphone()

def iniciar_mixer_configurado():
    """Inicializa o mixer na saída salva ou usa a saída padrão."""
    nome_salvo = settings.get("audio", "saida")

    if not nome_salvo or nome_salvo == "Padrão do sistema":
        pg.mixer.init()
        return

    try:
        definir_saida_padrao(nome_salvo)
        pg.mixer.init()
    except Exception as erro:
        print(f"Não foi possível selecionar a saída: {erro}")
        pg.mixer.init()


def falar(texto):
    try:
        cfg_idioma = obter_configuracao_idioma()
        voz_atual = cfg_idioma["voz"]

        valor_velocidade = int(settings.get("audio", "velocidade") or 80)
        taxa_calculada = int((valor_velocidade - 50) * 1.5)
        rate_str = (
            f"+{taxa_calculada}%"
            if taxa_calculada >= 0
            else f"{taxa_calculada}%"
        )

        valor_volume_slider = int(settings.get("audio", "volume") or 80)
        volume_decimal = max(0.0, min(1.0, valor_volume_slider / 100.0))

        async def gerar_audio():
            comunicacao = e_tts.Communicate(texto, voz_atual, rate=rate_str)
            await comunicacao.save("resposta.mp3")

        asyncio.run(gerar_audio())

        iniciar_mixer_configurado()
        pg.mixer.music.load("resposta.mp3")
        pg.mixer.music.set_volume(volume_decimal)
        pg.mixer.music.play()

        while pg.mixer.music.get_busy():
            pg.time.Clock().tick(10)

        pg.mixer.music.unload()
        pg.mixer.quit()
        if os.path.exists("resposta.mp3"):
            os.remove("resposta.mp3")

    except Exception as erro:
        print(f"Erro no edge-tts: {erro}")
        motor = pyttsx3.init()
        motor.say(texto)
        motor.runAndWait()


def ouvir():
    try:
        cfg_idioma = obter_configuracao_idioma()
        lang_whisper = cfg_idioma["whisper"]

        with obter_microfone_configurado() as mic:
            print(f"\nAssistente ativo e ouvindo ({lang_whisper})...")
            rec.pause_threshold = 1.5
            rec.adjust_for_ambient_noise(mic)
            audio = rec.listen(mic)

            with open("meu_audio.wav", "wb") as arquivo_wav:
                arquivo_wav.write(audio.get_wav_data())

            print("Processando audio...")

            with open("meu_audio.wav", "rb") as arquivo_lido:
                transcricao = cliente.audio.transcriptions.create(
                    file=("meu_audio.wav", arquivo_lido.read()),
                    model="whisper-large-v3",
                    language=lang_whisper,
                )

            texto = transcricao.text
            print(f"Você disse: {texto}")
            return texto

    except Exception as erro:
        print(f"Não foi possível escutar: {erro}")
        return ""


def iniciar_assistente():
    falar("Acesso liberado. Assistente de voz ativado.")

    while True:
        texto_ouvido = ouvir()

        if texto_ouvido:
            texto_normalizado = texto_ouvido.lower()
            if (
                "desligar sistema" in texto_normalizado
                or "encerrar" in texto_normalizado
                or "exit" in texto_normalizado
                or "salir" in texto_normalizado
            ):
                falar("Desligando o assistente. Até logo!")
                break

            falar(f"Você disse: {texto_ouvido}")


if __name__ == "__main__":
    iniciar_assistente()
