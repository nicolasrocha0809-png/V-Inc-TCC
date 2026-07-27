from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QComboBox, QPushButton
from PySide6.QtCore import Qt
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import settings

class InicioScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cor_primaria = "#60A5FA"
        self.setup_ui()

    def setup_ui(self):
        self.layout_principal = QVBoxLayout(self)
        
        #  principal
        self.content = QFrame()
        self.content.setStyleSheet("background-color: transparent;")
        self.layout_principal.addWidget(self.content)
        
        self.layout_content = QVBoxLayout(self.content)
        
        # Ícone e Títulos
        self.lbl_mic = QLabel("🎤")
        self.lbl_mic.setAlignment(Qt.AlignCenter)
        self.lbl_mic.setStyleSheet(f"font-size: 60px; color: {self.cor_primaria};")
        self.layout_content.addWidget(self.lbl_mic)

        self.lbl_ouvindo = QLabel("OUVINDO")
        self.lbl_ouvindo.setAlignment(Qt.AlignCenter)
        self.lbl_ouvindo.setStyleSheet("font-size: 32px; font-weight: bold; color: #60A5FA;")
        self.layout_content.addWidget(self.lbl_ouvindo)

        # Card de Áudio
        self.audio_card = QFrame()
        self.audio_card.setStyleSheet("background-color: #1E2937; border-radius: 16px; border: 2px solid #334155;")
        self.layout_content.addWidget(self.audio_card)
        
        layout_card = QVBoxLayout(self.audio_card)
        
        layout_card.addWidget(QLabel("Entrada de Áudio"))
        self.mic_combo = QComboBox()
        self.mic_combo.addItems(["Microfone Padrão", "Microfone Externo"])
        layout_card.addWidget(self.mic_combo)

        layout_card.addWidget(QLabel("Saída de Áudio"))
        self.speaker_combo = QComboBox()
        self.speaker_combo.addItems(["Headphone Padrão", "Alto-falantes"])
        layout_card.addWidget(self.speaker_combo)

        