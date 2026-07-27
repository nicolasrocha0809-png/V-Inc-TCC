from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt

class HistoricoScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setStyleSheet("background-color: #0F172A;")
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        # Label de Título
        lbl_titulo = QLabel("📜 Histórico")
        lbl_titulo.setStyleSheet("font-size: 28px; font-weight: bold; color: #60A5FA;")
        lbl_titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_titulo)
        
        lbl_dev = QLabel("Tela de Histórico em desenvolvimento...")
        lbl_dev.setStyleSheet("font-size: 16px; color: #94A3B8;")
        lbl_dev.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_dev)