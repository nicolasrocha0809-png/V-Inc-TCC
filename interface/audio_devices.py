import os

PADRAO = "Padrão do sistema"


def _listar_windows_ativos():
    """Consulta o Core Audio do Windows e retorna somente endpoints ACTIVE."""
    from pycaw.constants import DEVICE_STATE, EDataFlow
    from pycaw.pycaw import AudioUtilities

    entradas = []
    saidas = []
    dispositivos = AudioUtilities.GetAllDevices(
        EDataFlow.eAll.value,
        DEVICE_STATE.ACTIVE.value,
    )

    for dispositivo in dispositivos:
        nome = str(dispositivo.FriendlyName or "").strip()
        if not nome:
            continue

        fluxo = AudioUtilities.GetEndpointDataFlow(dispositivo.id, outputType=1)
        if fluxo == EDataFlow.eCapture.value and nome not in entradas:
            entradas.append(nome)
        elif fluxo == EDataFlow.eRender.value and nome not in saidas:
            saidas.append(nome)

    return entradas, saidas


def _listar_fallback_pyaudio():
    """Fallback para ambientes sem Core Audio do Windows."""
    try:
        import pyaudio
    except ImportError:
        return [], []

    entradas = []
    saidas = []
    audio = pyaudio.PyAudio()
    try:
        for indice in range(audio.get_device_count()):
            info = audio.get_device_info_by_index(indice)
            nome = str(info.get("name", "")).strip()
            if not nome:
                continue
            if info.get("maxInputChannels", 0) > 0 and nome not in entradas:
                entradas.append(nome)
            if info.get("maxOutputChannels", 0) > 0 and nome not in saidas:
                saidas.append(nome)
    finally:
        audio.terminate()
    return entradas, saidas

def definir_saida_padrao(nome):
    """Define no Windows a saída ativa escolhida pelo usuário."""
    if not nome or nome == PADRAO or os.name != "nt":
        return False

    try:
        from pycaw.constants import DEVICE_STATE, EDataFlow, ERole
        from pycaw.pycaw import AudioUtilities

        dispositivos = AudioUtilities.GetAllDevices(
            EDataFlow.eRender.value,
            DEVICE_STATE.ACTIVE.value,
        )
        dispositivo = next(
            (
                item for item in dispositivos
                if str(item.FriendlyName or "").strip() == nome
            ),
            None,
        )
        if dispositivo is None:
            return False

        AudioUtilities.SetDefaultDevice(
            dispositivo.id,
            roles=[ERole.eConsole, ERole.eMultimedia, ERole.eCommunications],
        )
        return True
    except Exception as erro:
        print(f"Não foi possível definir a saída do Windows: {erro}")
        return False

def listar_dispositivos():
    """Retorna (entradas, saídas) presentes e ativas neste momento."""
    if os.name == "nt":
        try:
            return _listar_windows_ativos()
        except Exception as erro:
            print(f"Não foi possível consultar o Core Audio do Windows: {erro}")
    return _listar_fallback_pyaudio()


def nomes_com_padrao(dispositivos):
    return [PADRAO, *dispositivos]