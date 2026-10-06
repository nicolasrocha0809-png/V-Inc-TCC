import asyncio
import io
import math
import os
import struct
import wave
import winsound
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

# Puxa a chave do cofre (se não achar, avisa que está faltando)
CHAVE_API = os.getenv("CHAVE_GROQ")
if not CHAVE_API:
    raise ValueError("Chave da Groq não encontrada! Verifique o arquivo .env")

cliente = Groq(api_key=CHAVE_API)
rec = sr.Recognizer()

SINAIS_SONOROS = {
    "iniciar": ((660, 90), (880, 130)),
    "pronto": ((1040, 150),),
    "processando": ((720, 90),),
    "erro": ((360, 130), (300, 170)),
    "encerrar": ((700, 100), (500, 150)),
}


def _gerar_tom_wav(frequencia, duracao_ms, volume=0.35, taxa=44100):
    quantidade = max(1, int(taxa * (duracao_ms / 1000)))
    fade = max(1, int(taxa * 0.008))
    frames = bytearray()

    for indice in range(quantidade):
        envelope = 1.0

        if indice < fade:
            envelope = indice / fade
        elif indice >= quantidade - fade:
            envelope = max(0.0, (quantidade - indice - 1) / fade)

        amostra = int(
            32767
            * volume
            * envelope
            * math.sin(2 * math.pi * frequencia * indice / taxa)
        )
        frames.extend(struct.pack("<h", amostra))

    buffer = io.BytesIO()

    with wave.open(buffer, "wb") as arquivo:
        arquivo.setnchannels(1)
        arquivo.setsampwidth(2)
        arquivo.setframerate(taxa)
        arquivo.writeframes(bytes(frames))

    buffer.seek(0)
    return buffer


def tocar_sinal(tipo="pronto"):
    padrao = SINAIS_SONOROS.get(tipo, SINAIS_SONOROS["pronto"])
    mixer_iniciado_aqui = False

    try:
        if not pg.mixer.get_init():
            iniciar_mixer_configurado()
            mixer_iniciado_aqui = True

        valor_volume = int(settings.get("audio", "volume") or 80)
        volume = max(0.0, min(1.0, valor_volume / 100.0))

        for frequencia, duracao in padrao:
            arquivo_tom = _gerar_tom_wav(
                frequencia,
                duracao,
                volume=0.42,
            )
            som = pg.mixer.Sound(file=arquivo_tom)
            som.set_volume(volume)
            canal = som.play()

            while canal and canal.get_busy():
                pg.time.Clock().tick(100)

            pg.time.wait(30)

        return True

    except Exception as erro:
        print(f"Não foi possível reproduzir o sinal pelo áudio configurado: {erro}")

        try:
            for frequencia, duracao in padrao:
                winsound.Beep(frequencia, duracao)
            return True
        except Exception as erro_fallback:
            print(f"Fallback do sinal sonoro também falhou: {erro_fallback}")
            return False

    finally:
        if mixer_iniciado_aqui:
            try:
                pg.mixer.quit()
            except Exception:
                pass


MAPA_IDIOMAS = {
    "pt_BR": {"whisper": "pt", "voz": "pt-BR-FranciscaNeural"},
    "en_US": {"whisper": "en", "voz": "en-US-AriaNeural"},
    "es_ES": {"whisper": "es", "voz": "es-ES-ElviraNeural"},
}

def obter_configuracao_idioma():
    """Busca o idioma atual nas ou usa pt_BR como padrão."""
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
    caminho_audio = "resposta.mp3"

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
            await comunicacao.save(caminho_audio)

        asyncio.run(gerar_audio())

        iniciar_mixer_configurado()
        pg.mixer.music.load(caminho_audio)
        pg.mixer.music.set_volume(volume_decimal)
        pg.mixer.music.play()

        while pg.mixer.music.get_busy():
            pg.time.Clock().tick(10)

    except Exception as erro:
        print(f"Erro no edge-tts: {erro}")

        try:
            motor = pyttsx3.init()
            motor.say(texto)
            motor.runAndWait()
        except Exception as erro_local:
            print(f"Não foi possível reproduzir a fala: {erro_local}")

    finally:
        try:
            if pg.mixer.get_init():
                pg.mixer.music.stop()
                try:
                    pg.mixer.music.unload()
                except Exception:
                    pass
                pg.mixer.quit()
        except Exception:
            pass

        try:
            if os.path.exists(caminho_audio):
                os.remove(caminho_audio)
        except OSError:
            pass


def ouvir():
    try:
        cfg_idioma = obter_configuracao_idioma()
        lang_whisper = cfg_idioma["whisper"]

        with obter_microfone_configurado() as mic:
            print("\nCalibrando o microfone. Aguarde em silêncio...")

            rec.pause_threshold = 1.5
            rec.adjust_for_ambient_noise(mic, duration=1)

            print(f"Limite de energia: {rec.energy_threshold:.0f}")
            print(
                f"Assistente ativo e ouvindo ({lang_whisper}). "
                "Pode falar agora..."
            )

            tocar_sinal("pronto")

            audio = rec.listen(
                mic,
                timeout=10,
                phrase_time_limit=10,
            )

        tocar_sinal("processando")

        with open("meu_audio.wav", "wb") as arquivo_wav:
            arquivo_wav.write(audio.get_wav_data())

        print("Processando áudio...")

        with open("meu_audio.wav", "rb") as arquivo_lido:
            transcricao = cliente.audio.transcriptions.create(
                file=("meu_audio.wav", arquivo_lido.read()),
                model="whisper-large-v3",
                language=lang_whisper,
            )

        texto = transcricao.text.strip()
        print(f"Você disse: {texto}")
        return texto

    except sr.WaitTimeoutError:
        print(
            "Nenhuma fala foi detectada. "
            "O assistente continuará ouvindo e emitirá outro sinal quando estiver pronto."
        )
        return ""

    except Exception as erro:
        print(f"Não foi possível escutar: {erro}")
        tocar_sinal("erro")

        try:
            falar(
                "Não consegui ouvir seu comando desta vez. "
                "Vou tentar novamente."
            )
        except Exception:
            pass

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
                break
                
            falar(f"Você disse: {texto_ouvido}")

if __name__ == "__main__":
    iniciar_assistente()