from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QSizePolicy
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QPainter, QPen, QColor, QFont


class MicrofoneLoading(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        azul = QColor("#BCE8FF")
        borda = max(2, round(self.width() * 0.012))
        area = self.rect().adjusted(borda, borda, -borda, -borda)
        painter.setBrush(QColor("#1E2020"))
        painter.setPen(QPen(azul, borda))
        painter.drawEllipse(area)

        centro_x = self.width() // 2
        escala = self.width() / 256
        topo = round(82 * escala)
        microfone_largura = round(42 * escala)
        microfone_altura = round(74 * escala)
        espessura = max(3, round(6 * escala))
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(azul, espessura, Qt.SolidLine, Qt.RoundCap))
        painter.drawRoundedRect(centro_x - microfone_largura // 2, topo, microfone_largura, microfone_altura, microfone_largura // 2, microfone_largura // 2)
        arco_largura = round(96 * escala)
        painter.drawArc(centro_x - arco_largura // 2, round(116 * escala), arco_largura, round(76 * escala), 180 * 16, 180 * 16)
        painter.drawLine(centro_x, round(188 * escala), centro_x, round(216 * escala))
        painter.drawLine(centro_x - round(25 * escala), round(216 * escala), centro_x + round(25 * escala), round(216 * escala))
        painter.end()


class LoadingScreen(QWidget):
    def __init__(self, callback_final=None, parent=None):
        super().__init__(parent)
        self.callback_final = callback_final
        self.progresso = 0
        self.setStyleSheet("LoadingScreen { background-color: #121414; color: #E2E2E2; }")
        self.setFont(QFont("Lexend"))

        self.layout_principal = QVBoxLayout(self)
        self.layout_principal.setContentsMargins(40, 40, 40, 40)
        self.layout_principal.setSpacing(40)
        self.layout_principal.setAlignment(Qt.AlignCenter)

        self.conteudo = QWidget(self)
        self.conteudo.setStyleSheet("background: transparent;")
        self.conteudo.setMinimumWidth(0)
        self.layout_conteudo = QVBoxLayout(self.conteudo)
        self.layout_conteudo.setContentsMargins(0, 0, 0, 0)
        self.layout_conteudo.setSpacing(40)
        self.layout_conteudo.setAlignment(Qt.AlignCenter)
        self.layout_principal.addWidget(self.conteudo)

        self.lbl_icon = MicrofoneLoading(self.conteudo)
        self.layout_conteudo.addWidget(self.lbl_icon, alignment=Qt.AlignCenter)

        self.lbl_titulo = QLabel("V-Inc", self.conteudo)
        self.lbl_titulo.setAlignment(Qt.AlignCenter)
        self.lbl_titulo.setMinimumWidth(0)
        self.layout_conteudo.addWidget(self.lbl_titulo)

        self.lbl_status = QLabel("Carregando sistema...", self.conteudo)
        self.lbl_status.setAlignment(Qt.AlignCenter)
        self.lbl_status.setWordWrap(True)
        self.lbl_status.setMinimumWidth(0)
        self.layout_conteudo.addWidget(self.lbl_status)

        self.progress_area = QWidget(self.conteudo)
        self.progress_area.setStyleSheet("background: transparent;")
        self.progress_area.setMinimumWidth(0)
        self.layout_progress = QVBoxLayout(self.progress_area)
        self.layout_progress.setContentsMargins(0, 0, 0, 0)
        self.layout_progress.setSpacing(8)
        self.layout_conteudo.addWidget(self.progress_area)

        self.progress_bar = QProgressBar(self.progress_area)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("QProgressBar { background-color: #282A2B; border: 2px solid #333535; border-radius: 16px; } QProgressBar::chunk { background-color: #BCE8FF; border-radius: 12px; }")
        self.layout_progress.addWidget(self.progress_bar)

        self.progress_info = QWidget(self.progress_area)
        self.progress_info.setStyleSheet("background: transparent;")
        self.progress_info.setMinimumWidth(0)
        self.progress_row = QHBoxLayout(self.progress_info)
        self.progress_row.setContentsMargins(2, 0, 2, 0)
        self.progress_row.setSpacing(12)

        self.lbl_modulos = QLabel("Iniciando módulos...", self.progress_info)
        self.lbl_modulos.setStyleSheet("background: transparent;")
        self.lbl_modulos.setMinimumWidth(0)
        self.lbl_modulos.setWordWrap(True)
        self.lbl_modulos.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.progress_row.addWidget(self.lbl_modulos)

        self.lbl_percentual = QLabel("0%", self.progress_info)
        self.lbl_percentual.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.lbl_percentual.setStyleSheet("background: transparent; color: #BCE8FF;")
        self.lbl_percentual.setMinimumWidth(0)
        self.progress_row.addWidget(self.lbl_percentual)
        self.layout_progress.addWidget(self.progress_info)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.atualizar_progresso)
        self.timer.start(50)
        self.atualizar_tamanho()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.atualizar_tamanho()

    def atualizar_tamanho(self):
        largura = max(240, self.width())
        altura = max(240, self.height())
        escala = max(0.65, min(1.0, largura / 672))
        diametro = min(256, max(128, int(largura * 0.40)))
        if altura < 600:
            diametro = min(diametro, max(128, int(altura * 0.25)))
        largura_progresso = min(672, max(220, largura - 80))
        self.lbl_icon.setFixedSize(QSize(diametro, diametro))
        self.conteudo.setMaximumWidth(largura_progresso)
        self.progress_area.setMaximumWidth(largura_progresso)
        self.progress_area.setMinimumWidth(0)
        self.lbl_titulo.setStyleSheet(f"background: transparent; font-size: {max(30, int(48 * escala))}px; font-weight: 700; color: #E2E2E2;")
        self.lbl_status.setStyleSheet(f"background: transparent; font-size: {max(22, int(36 * escala))}px; font-weight: 600; color: #BFC8CD;")
        self.lbl_modulos.setStyleSheet(f"background: transparent; font-size: {max(14, int(20 * escala))}px; font-weight: 700; color: #BFC8CD;")
        self.lbl_percentual.setStyleSheet(f"background: transparent; font-size: {max(24, int(36 * escala))}px; font-weight: 600; color: #BCE8FF;")
        self.progress_bar.setFixedHeight(max(20, int(32 * escala)))

    def atualizar_progresso(self):
        self.progresso = min(100, self.progresso + 1)
        self.progress_bar.setValue(self.progresso)
        self.lbl_percentual.setText(f"{self.progresso}%")
        if self.progresso == 35:
            self.lbl_modulos.setText("Carregando modelo de voz...")
        elif self.progresso == 60:
            self.lbl_modulos.setText("Inicializando reconhecimento...")
        elif self.progresso == 100:
            self.timer.stop()
            self.lbl_status.setText("Sistema pronto!")
            if self.callback_final:
                QTimer.singleShot(500, self.callback_final)
