from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class LoadingScreen(QWidget):
    def __init__(self, callback_final=None, parent=None):
        super().__init__(parent)
        self.setObjectName("pagina_loading")
        self.callback_final = callback_final
        self.progresso = 0

        raiz_projeto = Path(__file__).resolve().parents[2]
        caminho_logo = raiz_projeto / "interface" / "assets" / "logo_vinc.svg"
        self.logo_original = QPixmap(str(caminho_logo))

        if self.logo_original.isNull():
            self.logo_original = QPixmap(str(raiz_projeto / "logo.png"))

        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(24, 24, 24, 24)
        layout_principal.setAlignment(Qt.AlignCenter)

        self.card = QFrame(self)
        self.card.setObjectName("card_loading")
        self.card.setMaximumWidth(540)
        self.card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        layout_card = QVBoxLayout(self.card)
        layout_card.setContentsMargins(42, 34, 42, 34)
        layout_card.setSpacing(12)
        layout_card.setAlignment(Qt.AlignCenter)

        self.lbl_logo = QLabel(self.card)
        self.lbl_logo.setObjectName("logo_loading")
        self.lbl_logo.setAlignment(Qt.AlignCenter)
        self.lbl_logo.setAccessibleName("Logo do V.INC — Voz Inclusiva")

        titulo = QLabel("V.INC", self.card)
        titulo.setObjectName("titulo_loading")
        titulo.setAlignment(Qt.AlignCenter)

        subtitulo = QLabel("VOZ INCLUSIVA", self.card)
        subtitulo.setObjectName("subtitulo_loading")
        subtitulo.setAlignment(Qt.AlignCenter)

        self.lbl_status = QLabel("Preparando o assistente…", self.card)
        self.lbl_status.setObjectName("status_loading")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        self.lbl_status.setWordWrap(True)

        self.progress_bar = QProgressBar(self.card)
        self.progress_bar.setObjectName("barra_loading")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setAccessibleName("Progresso de inicialização")

        info = QWidget(self.card)
        info.setObjectName("info_loading")
        layout_info = QHBoxLayout(info)
        layout_info.setContentsMargins(2, 0, 2, 0)
        layout_info.setSpacing(12)

        self.lbl_modulos = QLabel("Iniciando módulos…", info)
        self.lbl_modulos.setObjectName("modulos_loading")
        self.lbl_modulos.setWordWrap(True)
        self.lbl_modulos.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Preferred,
        )

        self.lbl_percentual = QLabel("0%", info)
        self.lbl_percentual.setObjectName("percentual_loading")
        self.lbl_percentual.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        layout_info.addWidget(self.lbl_modulos, 1)
        layout_info.addWidget(self.lbl_percentual)

        layout_card.addWidget(self.lbl_logo)
        layout_card.addWidget(titulo)
        layout_card.addWidget(subtitulo)
        layout_card.addSpacing(10)
        layout_card.addWidget(self.lbl_status)
        layout_card.addSpacing(8)
        layout_card.addWidget(self.progress_bar)
        layout_card.addWidget(info)
        layout_principal.addWidget(self.card)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.atualizar_progresso)
        self.timer.start(50)
        self.atualizar_tamanho_logo()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.atualizar_tamanho_logo()

    def atualizar_tamanho_logo(self):
        if self.logo_original.isNull():
            return

        referencia = min(max(self.width(), 320), max(self.height(), 320))
        tamanho = max(84, min(122, int(referencia * 0.16)))
        self.lbl_logo.setPixmap(
            self.logo_original.scaled(
                tamanho,
                tamanho,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
        )

    def atualizar_progresso(self):
        self.progresso = min(100, self.progresso + 1)
        self.progress_bar.setValue(self.progresso)
        self.lbl_percentual.setText(f"{self.progresso}%")

        if self.progresso == 35:
            self.lbl_modulos.setText("Carregando recursos de voz…")
        elif self.progresso == 60:
            self.lbl_modulos.setText("Inicializando reconhecimento…")
        elif self.progresso == 85:
            self.lbl_modulos.setText("Aplicando suas preferências…")
        elif self.progresso == 100:
            self.timer.stop()
            self.lbl_modulos.setText("Inicialização concluída")
            self.lbl_status.setText("Tudo pronto!")

            if self.callback_final:
                QTimer.singleShot(500, self.callback_final)
