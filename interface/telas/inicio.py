from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QComboBox, QPushButton
from PySide6.QtCore import Qt
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import settings

# Imports extras necessários para o layout (não substituem os de cima)
from PySide6.QtWidgets import QHBoxLayout, QSizePolicy, QGraphicsDropShadowEffect
from PySide6.QtGui import QFont, QColor


class InicioScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # ---- Paleta oficial do design system (DESIGN.md) ----
        self.cor_fundo = "#121414"                # background / surface
        self.cor_card = "#1e2020"                  # surface-container
        self.cor_input_bg = "#282a2b"               # surface-container-high
        self.cor_outline = "#899297"                 # outline
        self.cor_primaria = "#bce8ff"                # primary (baby blue)
        self.cor_on_primary = "#003546"              # on-primary (texto escuro sobre azul)
        self.cor_primaria_container = "#89cff0"       # primary-container (hover)
        self.cor_texto = "#e2e2e2"                    # on-surface
        self.cor_texto_secundario = "#bfc8cd"          # on-surface-variant
        self.cor_erro = "#ffb4ab"                       # error
        self.cor_on_erro = "#690005"                     # on-error

        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet(f"background-color: {self.cor_fundo};")

        self.layout_principal = QVBoxLayout(self)
        self.layout_principal.setContentsMargins(40, 32, 40, 32)
        self.layout_principal.setSpacing(0)

        # ---------- Seletor de tema ----------
        self.layout_principal.addLayout(self._criar_toggle_tema())

        # ---------- Conteúdo central ----------
        self.content = QFrame()
        self.content.setStyleSheet("background-color: transparent;")
        self.layout_principal.addWidget(self.content, 1)

        self.layout_content = QVBoxLayout(self.content)
        self.layout_content.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.layout_content.setSpacing(18)
        self.layout_content.addSpacing(24)

        # Botão circular do microfone
        self.layout_content.addWidget(self._criar_botao_mic(), alignment=Qt.AlignHCenter)

        # Título "OUVINDO"
        self.lbl_ouvindo = QLabel("OUVINDO")
        self.lbl_ouvindo.setAlignment(Qt.AlignCenter)
        fonte_titulo = QFont()
        fonte_titulo.setPointSize(24)
        fonte_titulo.setBold(True)
        fonte_titulo.setLetterSpacing(QFont.AbsoluteSpacing, 5)
        self.lbl_ouvindo.setFont(fonte_titulo)
        self.lbl_ouvindo.setStyleSheet(
            f"color: {self.cor_primaria}; background-color: transparent; border: none; margin-top: 6px;"
        )
        self.layout_content.addWidget(self.lbl_ouvindo)

        self.layout_content.addSpacing(12)

        # Card de Áudio
        self.layout_content.addWidget(self._criar_card_audio(), alignment=Qt.AlignHCenter)

    # ---------------------------------------------------------------
    def _criar_toggle_tema(self):
        layout_topo = QHBoxLayout()
        layout_topo.setContentsMargins(0, 0, 0, 0)
        layout_topo.addStretch()

        container = QFrame()
        container.setStyleSheet(
            "background-color: #ffffff; border: 1px solid #ffffff; "
            "border-radius: 12px;"
        )
        container.setFixedSize(187, 43)
        layout_container = QHBoxLayout(container)
        layout_container.setContentsMargins(1, 1, 1, 1)
        layout_container.setSpacing(0)

        self.btn_escuro = QPushButton("Escuro")
        self.btn_claro = QPushButton("Claro")
        for btn in (self.btn_escuro, self.btn_claro):
            btn.setFixedSize(91, 39)
            btn.setCursor(Qt.PointingHandCursor)

        divisor = QFrame()
        divisor.setFixedSize(1, 39)
        divisor.setStyleSheet("background-color: #ffffff; border: none;")

        self.btn_escuro.clicked.connect(lambda: self._estilizar_toggle(True))
        self.btn_claro.clicked.connect(lambda: self._estilizar_toggle(False))
        self._estilizar_toggle(True)

        layout_container.addWidget(self.btn_escuro)
        layout_container.addWidget(divisor)
        layout_container.addWidget(self.btn_claro)
        layout_topo.addWidget(container)
        return layout_topo

    def _estilizar_toggle(self, modo_escuro: bool):
        estilo_ativo = (
            f"background-color: {self.cor_primaria}; color: {self.cor_on_primary}; "
            "font-weight: bold;"
        )
        estilo_inativo = (
            f"background-color: {self.cor_fundo}; color: #ffffff; "
            "font-weight: normal;"
        )
        self.btn_escuro.setStyleSheet(
            f"QPushButton {{ {estilo_ativo if modo_escuro else estilo_inativo} "
            "border: none; border-radius: 0; }"
        )
        self.btn_claro.setStyleSheet(
            f"QPushButton {{ {estilo_inativo if modo_escuro else estilo_ativo} "
            "border: none; border-radius: 0; }"
        )

    # ---------------------------------------------------------------
    def _criar_botao_mic(self):
        """Círculo grande do microfone, com brilho suave ao redor."""
        btn = QPushButton("🎤")
        btn.setFixedSize(180, 180)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.cor_primaria};
                color: {self.cor_on_primary};
                border: 4px solid {self.cor_on_primary};
                border-radius: 90px;
                font-size: 60px;
            }}
            QPushButton:hover {{
                background-color: {self.cor_primaria_container};
            }}
        """)

        brilho = QGraphicsDropShadowEffect()
        brilho.setBlurRadius(60)
        brilho.setOffset(0, 0)
        brilho.setColor(QColor(188, 232, 255, 160))
        btn.setGraphicsEffect(brilho)

        return btn

    def _criar_card_audio(self):
        card = QFrame()
        card.setStyleSheet(
            f"background-color: {self.cor_card}; border-radius: 20px; border: 1px solid {self.cor_outline};"
        )
        card.setMinimumWidth(560)
        card.setMaximumWidth(640)

        layout_card = QVBoxLayout(card)
        layout_card.setContentsMargins(24, 24, 24, 24)
        layout_card.setSpacing(6)

        # Entrada de Áudio
        layout_card.addWidget(self._criar_titulo_campo("Entrada de Áudio"))
        self.mic_combo = QComboBox()
        self.mic_combo.addItems(["🎙  Microfone Padrão", "🎙  Microfone Externo"])
        self.mic_combo.setMinimumHeight(44)
        self.mic_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.mic_combo.setStyleSheet(self._estilo_combo())
        layout_card.addWidget(self.mic_combo)

        layout_card.addSpacing(10)

        # Saída de Áudio
        layout_card.addWidget(self._criar_titulo_campo("Saída de Áudio"))
        self.speaker_combo = QComboBox()
        self.speaker_combo.addItems(["🎧  Headfone Padrão", "🎧  Alto-falantes"])
        self.speaker_combo.setMinimumHeight(44)
        self.speaker_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.speaker_combo.setStyleSheet(self._estilo_combo())
        layout_card.addWidget(self.speaker_combo)

        # Divisor
        divisor = QFrame()
        divisor.setFixedHeight(2)
        divisor.setStyleSheet(f"background-color: {self.cor_outline}; border: none;")
        layout_card.addSpacing(10)
        layout_card.addWidget(divisor)
        layout_card.addSpacing(10)

        # Botões de ação
        layout_botoes = QHBoxLayout()
        layout_botoes.setSpacing(16)

        self.btn_parar = QPushButton("⏸  Parar de Ouvir")
        self.btn_parar.setMinimumHeight(44)
        self.btn_parar.setCursor(Qt.PointingHandCursor)
        self.btn_parar.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.cor_primaria};
                color: {self.cor_on_primary};
                border: none;
                border-radius: 12px;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {self.cor_primaria_container};
            }}
        """)

        self.btn_config_voz = QPushButton("🎚  Configurações de Voz")
        self.btn_config_voz.setMinimumHeight(44)
        self.btn_config_voz.setCursor(Qt.PointingHandCursor)
        self.btn_config_voz.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {self.cor_primaria};
                border: 3px solid {self.cor_primaria};
                border-radius: 12px;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {self.cor_input_bg};
            }}
        """)

        layout_botoes.addWidget(self.btn_parar)
        layout_botoes.addWidget(self.btn_config_voz)
        layout_card.addLayout(layout_botoes)

        return card

    def _criar_titulo_campo(self, texto):
        lbl = QLabel(texto)
        lbl.setStyleSheet(
            f"color: {self.cor_texto}; font-size: 18px; font-weight: bold; "
            f"border: none; background-color: transparent;"
        )
        return lbl

    def _estilo_combo(self):
        return f"""
            QComboBox {{
                background-color: {self.cor_input_bg};
                color: {self.cor_texto};
                border: 3px solid {self.cor_outline};
                border-radius: 12px;
                padding: 8px 40px 8px 16px;
                font-size: 14px;
            }}
            QComboBox:focus {{
                border: 3px solid {self.cor_primaria};
            }}
            QComboBox:hover {{
                background-color: #333535;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 32px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {self.cor_card};
                color: {self.cor_texto};
                selection-background-color: {self.cor_primaria};
                selection-color: {self.cor_on_primary};
                border: 1px solid {self.cor_outline};
                outline: none;
            }}
        """