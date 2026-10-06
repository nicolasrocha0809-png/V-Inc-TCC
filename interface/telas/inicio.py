import os
import sys

from PySide6.QtCore import QProcess, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from config import settings
from interface.audio_devices import listar_dispositivos, nomes_com_padrao


class InicioScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.processo_assistente = None
        self.assistente_ativo = False

        self.setup_ui()

    def setup_ui(self):
        self.setObjectName("pagina_inicio")

        self.layout_principal = QVBoxLayout(self)
        self.layout_principal.setContentsMargins(40, 32, 40, 32)
        self.layout_principal.setSpacing(0)

        # ---------- Conteúdo central ----------
        self.content = QFrame()
        self.content.setObjectName("conteudo_inicio")
        self.layout_principal.addWidget(self.content, 1)

        self.layout_content = QVBoxLayout(self.content)
        self.layout_content.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.layout_content.setSpacing(18)
        self.layout_content.addSpacing(16)

        # Botão circular do microfone
        self.layout_content.addWidget(self._criar_botao_mic(), alignment=Qt.AlignHCenter)

        # Estado textual acessível do assistente
        self.lbl_ouvindo = QLabel("Assistente parado")
        self.lbl_ouvindo.setObjectName("estado_assistente")
        self.lbl_ouvindo.setAlignment(Qt.AlignCenter)
        fonte_titulo = QFont()
        fonte_titulo.setPointSize(24)
        fonte_titulo.setBold(True)
        fonte_titulo.setLetterSpacing(QFont.AbsoluteSpacing, 5)
        self.lbl_ouvindo.setFont(fonte_titulo)
        self.layout_content.addWidget(self.lbl_ouvindo)

        self.layout_content.addSpacing(12)

        # Card de Áudio
        self.layout_content.addWidget(self._criar_card_audio(), alignment=Qt.AlignHCenter)

    # ---------------------------------------------------------------
    def _criar_botao_mic(self):
        """Círculo grande do microfone, com controle acessível do assistente."""
        btn = QPushButton("🎤")
        self.btn_mic = btn
        btn.setObjectName("botao_microfone")
        btn.setAccessibleName("Ativar assistente de voz")
        btn.setAccessibleDescription(
            "Inicia ou interrompe o assistente de voz. Também pode ser acionado com Enter ou Espaço."
        )
        btn.setToolTip("Ativar ou parar o assistente de voz")
        btn.setFixedSize(180, 180)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(self.alternar_assistente)
        return btn

    def _criar_card_audio(self):
        card = QFrame()
        card.setObjectName("card_audio_inicio")
        card.setMinimumWidth(560)
        card.setMaximumWidth(640)

        layout_card = QVBoxLayout(card)
        layout_card.setContentsMargins(24, 24, 24, 24)
        layout_card.setSpacing(6)

        # Entrada de Áudio
        layout_card.addWidget(self._criar_titulo_campo("Entrada de Áudio"))
        self.mic_combo = QComboBox()
        self.mic_combo.setObjectName("campo_audio_inicio")
        microfones, _ = listar_dispositivos()
        self.mic_combo.addItems(nomes_com_padrao(microfones))
        self._selecionar_dispositivo(
            self.mic_combo,
            settings.get("audio", "microfone"),
        )
        self.mic_combo.setAccessibleName("Entrada de áudio")
        self.mic_combo.setAccessibleDescription("Selecione o microfone que será usado pelo assistente.")
        self.mic_combo.setMinimumHeight(44)
        self.mic_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout_card.addWidget(self.mic_combo)

        layout_card.addSpacing(10)

        # Saída de Áudio
        layout_card.addWidget(self._criar_titulo_campo("Saída de Áudio"))
        self.speaker_combo = QComboBox()
        self.speaker_combo.setObjectName("campo_audio_inicio")
        _, saidas = listar_dispositivos()
        self.speaker_combo.addItems(nomes_com_padrao(saidas))
        self._selecionar_dispositivo(
            self.speaker_combo,
            settings.get("audio", "saida"),
        )
        self.speaker_combo.setAccessibleName("Saída de áudio")
        self.speaker_combo.setAccessibleDescription("Selecione o dispositivo de saída das respostas do assistente.")
        self.speaker_combo.setMinimumHeight(44)
        self.speaker_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout_card.addWidget(self.speaker_combo)

        # Divisor
        divisor = QFrame()
        divisor.setObjectName("divisor_audio_inicio")
        divisor.setFixedHeight(2)
        layout_card.addSpacing(10)
        layout_card.addWidget(divisor)
        layout_card.addSpacing(10)

        # Botões de ação
        layout_botoes = QHBoxLayout()
        layout_botoes.setSpacing(16)

        self.btn_parar = QPushButton("Iniciar Assistente")
        self.btn_parar.setObjectName("botao_iniciar_assistente")
        self.btn_parar.setAccessibleName("Iniciar assistente de voz")
        self.btn_parar.setAccessibleDescription("Inicia o assistente de voz.")
        self.btn_parar.setMinimumHeight(44)
        self.btn_parar.clicked.connect(self.alternar_assistente)
        self.btn_parar.setCursor(Qt.PointingHandCursor)
        self.btn_config_voz = QPushButton("Configurações de Voz")
        self.btn_config_voz.setObjectName("botao_configuracoes_voz")
        self.btn_config_voz.setAccessibleName("Abrir configurações de voz")
        self.btn_config_voz.setAccessibleDescription("Abre a tela de configurações do assistente.")
        self.btn_config_voz.setMinimumHeight(44)
        self.btn_config_voz.clicked.connect(self.abrir_configuracoes)
        self.btn_config_voz.setCursor(Qt.PointingHandCursor)
        layout_botoes.addWidget(self.btn_parar)
        layout_botoes.addWidget(self.btn_config_voz)
        layout_card.addLayout(layout_botoes)

        self._atualizar_estado_controles()

        self.mic_combo.currentTextChanged.connect(
            lambda texto: settings.set("audio", "microfone", texto)
        )
        self.speaker_combo.currentTextChanged.connect(
            lambda texto: settings.set("audio", "saida", texto)
        )

        return card

    def alternar_assistente(self):
        if self.assistente_ativo:
            self.parar_assistente()
        else:
            self.iniciar_assistente()

    def iniciar_assistente(self):
        if self.processo_assistente and self.processo_assistente.state() != QProcess.NotRunning:
            return

        caminho_assistente = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "assistente.py",
        )
        self.processo_assistente = QProcess(self)
        self.processo_assistente.setProcessChannelMode(QProcess.MergedChannels)
        self.processo_assistente.readyReadStandardOutput.connect(self._ler_saida_assistente)
        self.processo_assistente.errorOccurred.connect(self._erro_assistente)
        self.processo_assistente.finished.connect(self._assistente_finalizado)
        self.processo_assistente.start(sys.executable, ["-u", caminho_assistente])

        self.assistente_ativo = True
        self.lbl_ouvindo.setText("Assistente ativado — ouvindo")
        self._atualizar_estado_controles()

    def parar_assistente(self):
        if not self.processo_assistente:
            self._assistente_finalizado()
            return

        if self.processo_assistente.state() != QProcess.NotRunning:
            self.processo_assistente.terminate()
            if not self.processo_assistente.waitForFinished(1500):
                self.processo_assistente.kill()
                self.processo_assistente.waitForFinished(500)
        else:
            self._assistente_finalizado()

    def _ler_saida_assistente(self):
        if not self.processo_assistente:
            return
        saida = bytes(self.processo_assistente.readAllStandardOutput()).decode(
            "utf-8", errors="replace"
        ).strip()
        if not saida:
            return
        print(saida)
        ultima_linha = saida.splitlines()[-1]
        if "Ouvindo" in ultima_linha or "ouvindo" in ultima_linha:
            self.lbl_ouvindo.setText("Assistente ativado — ouvindo")
        elif "Processando" in ultima_linha:
            self.lbl_ouvindo.setText("Assistente ativado — processando")
        elif "Encerrando" in ultima_linha:
            self.lbl_ouvindo.setText("Assistente parado")

    def _erro_assistente(self, erro):
        if erro == QProcess.FailedToStart:
            self.lbl_ouvindo.setText("Não foi possível iniciar o assistente")
            self.assistente_ativo = False

    def _atualizar_estado_controles(self):
        if not hasattr(self, "btn_parar"):
            return
        if self.assistente_ativo:
            self.btn_parar.setText("Parar de Ouvir")
            self.btn_parar.setAccessibleName("Parar de ouvir")
            self.btn_parar.setAccessibleDescription("Interrompe o assistente de voz ativo.")
            self.btn_parar.setEnabled(True)
            self.btn_mic.setAccessibleName("Parar assistente de voz")
            self.btn_mic.setToolTip("Parar o assistente de voz")
        else:
            self.btn_parar.setText("Iniciar Assistente")
            self.btn_parar.setAccessibleName("Iniciar assistente de voz")
            self.btn_parar.setAccessibleDescription("Inicia o assistente de voz.")
            self.btn_parar.setEnabled(True)
            self.btn_mic.setAccessibleName("Ativar assistente de voz")
            self.btn_mic.setToolTip("Ativar o assistente de voz")

    def _assistente_finalizado(self, *_args):
        self.assistente_ativo = False
        self.lbl_ouvindo.setText("Assistente parado")
        self._atualizar_estado_controles()        

    def abrir_configuracoes(self):
        janela = self.window()
        if hasattr(janela, "mudar_tela"):
            janela.mudar_tela(5)

    def closeEvent(self, event):
        self.parar_assistente()
        event.accept()

    def showEvent(self, event):
        super().showEvent(event)
        self._selecionar_dispositivo(
            self.mic_combo,
            settings.get("audio", "microfone"),
        )
        self._selecionar_dispositivo(
            self.speaker_combo,
            settings.get("audio", "saida"),
        )

    def _criar_titulo_campo(self, texto):
        lbl = QLabel(texto)
        lbl.setObjectName("titulo_campo_audio")
        return lbl

    @staticmethod
    def _selecionar_dispositivo(combo, nome):
        if not nome:
            return

        indice = combo.findText(nome)
        if indice >= 0:
            combo.setCurrentIndex(indice)
