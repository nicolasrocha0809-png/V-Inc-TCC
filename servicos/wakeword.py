import io
import os
import re
import time
import unicodedata
import wave
from collections import deque
from difflib import SequenceMatcher
from pathlib import Path

import numpy as np
import pyaudio
from dotenv import load_dotenv
from groq import Groq
from livekit.wakeword import WakeWordModel

from config import settings


load_dotenv()

CHAVE_API = os.getenv("CHAVE_GROQ") or os.getenv("GROQ_API_KEY")
if not CHAVE_API:
    raise ValueError("Chave da Groq não encontrada! Verifique o arquivo .env")

cliente = Groq(api_key=CHAVE_API)

WAKE_THRESHOLD = 0.30
SAMPLE_RATE = 16000
FRAME_SAMPLES = 1280
MODEL_FRAMES = 25
VERIFY_FRAMES = 38
POST_TRIGGER_FRAMES = 8

MODELOS_CONFIRMACAO = (
    "whisper-large-v3-turbo",
    "whisper-large-v3",
)

RAIZ_PROJETO = Path(__file__).resolve().parent.parent

_modelo_wake = None
_nome_modelo = None


def _normalizar_nome_dispositivo(nome):
    texto = unicodedata.normalize("NFKD", str(nome or ""))
    texto = "".join(
        caractere
        for caractere in texto
        if not unicodedata.combining(caractere)
    )
    return re.sub(r"[^a-z0-9]+", "", texto.lower())


def _resolver_caminho_modelo():
    caminho_env = os.getenv("VINC_WAKEWORD_MODEL")

    candidatos = []

    if caminho_env:
        candidatos.append(Path(caminho_env).expanduser())

    candidatos.extend([
        RAIZ_PROJETO / "modelos" / "ola_vinc_v2.onnx",
        RAIZ_PROJETO / "ola_vinc_v2.onnx",
    ])

    for caminho in candidatos:
        caminho = caminho.resolve()

        if caminho.exists():
            return caminho

    caminhos_texto = "\n".join(f"- {caminho}" for caminho in candidatos)

    raise FileNotFoundError(
        "Modelo de wake word não encontrado. Coloque o arquivo "
        "'ola_vinc_v2.onnx' em uma destas posições:\n"
        f"{caminhos_texto}"
    )


def _obter_modelo():
    global _modelo_wake, _nome_modelo

    if _modelo_wake is None:
        caminho = _resolver_caminho_modelo()

        print(f"Carregando wake word: {caminho.name}")

        _modelo_wake = WakeWordModel(
            models=[caminho]
        )

        _nome_modelo = caminho.stem

    return _modelo_wake, _nome_modelo


def _obter_indice_microfone(audio):
    nome_salvo = settings.get("audio", "microfone")

    if not nome_salvo or nome_salvo == "Padrão do sistema":
        return None

    alvo = _normalizar_nome_dispositivo(nome_salvo)

    candidatos_parciais = []

    for indice in range(audio.get_device_count()):
        try:
            info = audio.get_device_info_by_index(indice)
        except Exception:
            continue

        if int(info.get("maxInputChannels", 0) or 0) <= 0:
            continue

        nome = str(info.get("name", "")).strip()
        normalizado = _normalizar_nome_dispositivo(nome)

        if normalizado == alvo:
            return indice

        if alvo and normalizado and (
            alvo in normalizado
            or normalizado in alvo
        ):
            candidatos_parciais.append(indice)

    if candidatos_parciais:
        return candidatos_parciais[0]

    print(
        f"Microfone configurado '{nome_salvo}' não foi encontrado no PyAudio. "
        "Usando o microfone padrão do sistema."
    )

    return None


def _abrir_stream(audio):
    indice = _obter_indice_microfone(audio)

    argumentos = {
        "format": pyaudio.paInt16,
        "channels": 1,
        "rate": SAMPLE_RATE,
        "input": True,
        "frames_per_buffer": FRAME_SAMPLES,
    }

    if indice is not None:
        argumentos["input_device_index"] = indice

    try:
        return audio.open(**argumentos)

    except Exception as erro:
        if indice is None:
            raise

        print(
            "Não foi possível abrir o microfone configurado para a wake word: "
            f"{erro}. Tentando o microfone padrão."
        )

        argumentos.pop("input_device_index", None)
        return audio.open(**argumentos)


def _normalizar_texto(texto):
    texto = str(texto or "").lower().strip()

    texto = unicodedata.normalize("NFD", texto)

    texto = "".join(
        caractere
        for caractere in texto
        if unicodedata.category(caractere) != "Mn"
    )

    texto = re.sub(r"[^a-z0-9]+", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()

    return texto


def _similaridade(a, b):
    return SequenceMatcher(
        None,
        a,
        b,
    ).ratio()


def _frase_wake_valida(texto):
    normalizado = _normalizar_texto(texto)
    compacto = normalizado.replace(" ", "")

    alvo = "olavinc"

    score_alvo = _similaridade(
        compacto,
        alvo,
    )

    falsos_alvos = (
        "vinc",
        "vincvinc",
        "ving",
        "vingue",
        "vinque",
        "pinc",
        "inc",
    )

    score_falso = max(
        _similaridade(
            compacto,
            falso,
        )
        for falso in falsos_alvos
    )

    print(
        f"Similaridade wake: {score_alvo:.2f} | "
        f"falso: {score_falso:.2f}"
    )

    return (
        score_alvo >= 0.72
        and score_alvo >= score_falso + 0.08
    )


def _audio_para_wav(audio_int16):
    buffer = io.BytesIO()

    with wave.open(buffer, "wb") as arquivo:
        arquivo.setnchannels(1)
        arquivo.setsampwidth(2)
        arquivo.setframerate(SAMPLE_RATE)
        arquivo.writeframes(audio_int16.tobytes())

    return buffer.getvalue()


def _transcrever_confirmacao(audio):
    dados_wav = _audio_para_wav(audio)
    ultimo_erro = None

    for indice, modelo in enumerate(MODELOS_CONFIRMACAO):
        try:
            resposta = cliente.audio.transcriptions.create(
                file=("wakeword.wav", dados_wav),
                model=modelo,
                language="pt",
                temperature=0,
            )

            return resposta.text.strip(), modelo

        except Exception as erro:
            ultimo_erro = erro

            if indice + 1 < len(MODELOS_CONFIRMACAO):
                proximo = MODELOS_CONFIRMACAO[indice + 1]

                print(
                    f"Falha no {modelo} durante a confirmação da wake word: "
                    f"{erro}. Tentando {proximo}."
                )

    raise RuntimeError(
        "Não foi possível confirmar a wake word pela Groq."
    ) from ultimo_erro


def aguardar_wakeword():
    modelo, nome_modelo = _obter_modelo()

    audio = pyaudio.PyAudio()
    stream = None

    try:
        stream = _abrir_stream(audio)
        buffer = deque(maxlen=VERIFY_FRAMES)

        print('Aguardando wake word "Olá V-Inc"...')

        while True:
            dados = stream.read(
                FRAME_SAMPLES,
                exception_on_overflow=False,
            )

            frame = np.frombuffer(
                dados,
                dtype=np.int16,
            )

            buffer.append(frame)

            if len(buffer) < MODEL_FRAMES:
                continue

            audio_modelo = np.concatenate(
                list(buffer)[-MODEL_FRAMES:]
            )

            scores = modelo.predict(
                audio_modelo
            )

            score = scores.get(
                nome_modelo,
                0.0,
            )

            if score < WAKE_THRESHOLD:
                continue

            print(
                "Candidato de wake word detectado "
                f"(score ONNX = {score:.3f}). Verificando..."
            )

            frames_extras = []

            for _ in range(POST_TRIGGER_FRAMES):
                dados_extra = stream.read(
                    FRAME_SAMPLES,
                    exception_on_overflow=False,
                )

                frames_extras.append(
                    np.frombuffer(
                        dados_extra,
                        dtype=np.int16,
                    )
                )

            audio_verificacao = np.concatenate(
                list(buffer)
                + frames_extras
            )

            try:
                texto, modelo_whisper = _transcrever_confirmacao(
                    audio_verificacao
                )

                print(
                    f'Confirmação ({modelo_whisper}) ouviu: "{texto}"'
                )

                if _frase_wake_valida(texto):
                    print("Wake word confirmada: Olá V-Inc.")
                    return True

                print(
                    "Wake word rejeitada. "
                    'Continuando a aguardar "Olá V-Inc"...'
                )

            except Exception as erro:
                print(
                    "Não foi possível verificar o candidato de wake word: "
                    f"{erro}. Continuando a escuta."
                )

            buffer.clear()
            time.sleep(0.3)

    finally:
        if stream is not None:
            try:
                stream.stop_stream()
            except Exception:
                pass

            try:
                stream.close()
            except Exception:
                pass

        audio.terminate()
