from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QGridLayout
from PySide6.QtCore import Qt

class ComandosScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #0F172A;")
        self.criar_tela()

    def criar_tela(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(40, 30, 40, 40)

    
        lbl_titulo = QLabel("Guia de Comandos")
        lbl_titulo.setStyleSheet("font-size: 28px; font-weight: bold; color: #60A5FA;")
        layout_principal.addWidget(lbl_titulo)

        lbl_sub = QLabel("Diga o nome do assistente seguido por um destes comandos.")
        lbl_sub.setStyleSheet("font-size: 14px; color: #94A3B8; margin-bottom: 20px;")
        layout_principal.addWidget(lbl_sub)

        grid = QGridLayout()
        layout_principal.addLayout(grid)

        self.criar_card(grid, "▶️", "Abra o YouTube", "Inicia o aplicativo de vídeo e prepara para pesquisa por voz.", 0, 0)
        self.criar_card(grid, "📖", "Leia o texto", "Ativa o leitor de tela para o documento ou site atualmente aberto.", 0, 1)
        self.criar_card(grid, "🔍", "Pesquise sobre", "Faz uma pesquisa no Google sobre o assunto dito.", 1, 0)
        self.criar_card(grid, "⏰", "Defina alarme", "Configura um alarme ou lembrete no horário desejado.", 1, 1)

    def criar_card(self, grid, emoji, titulo, descricao, row, column):
        card = QFrame()
        card.setStyleSheet("""
            QFrame { 
                background-color: #1E2937; 
                border-radius: 16px; 
                border: 2px solid #334155; 
            }
        """)
        
        layout_card = QVBoxLayout(card)
        
        lbl_emoji = QLabel(emoji)
        lbl_emoji.setStyleSheet("font-size: 40px;")
        lbl_emoji.setAlignment(Qt.AlignCenter)
        layout_card.addWidget(lbl_emoji)

        lbl_titulo = QLabel(titulo)
        lbl_titulo.setStyleSheet("font-size: 17px; font-weight: bold; color: #E0F2FE;")
        lbl_titulo.setAlignment(Qt.AlignCenter)
        layout_card.addWidget(lbl_titulo)

        lbl_desc = QLabel(descricao)
        lbl_desc.setStyleSheet("font-size: 13px; color: #94A3B8;")
        lbl_desc.setWordWrap(True)
        lbl_desc.setAlignment(Qt.AlignCenter)
        layout_card.addWidget(lbl_desc)

        grid.addWidget(card, row, column)