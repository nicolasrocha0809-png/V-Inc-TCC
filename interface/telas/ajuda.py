from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QFrame, 
                               QScrollArea, QPushButton)
from PySide6.QtCore import Qt

class AjudaScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout_principal = QVBoxLayout(self)
        self.layout_principal.setContentsMargins(40, 25, 40, 25)

    
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        self.layout_principal.addWidget(self.scroll)

        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll.setWidget(self.scroll_content)

        self.criar_faq()

    def criar_faq(self):
        title = QLabel("Perguntas Frequentes (FAQ)")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #60A5FA;")
        self.scroll_layout.addWidget(title)

        subtitle = QLabel("Encontre respostas rápidas para as dúvidas mais comuns.")
        subtitle.setStyleSheet("font-size: 15px; color: #94A3B8; margin-bottom: 30px;")
        self.scroll_layout.addWidget(subtitle)

        self.criar_pergunta("O que é o V-Inc?", "Breve explicação sobre o V-Inc.")
        self.criar_pergunta("Como usar comandos de voz?", "Breve explicação sobre comandos.")
        self.criar_pergunta("Como alterar o tema?", "Breve explicação sobre temas.")
        self.criar_pergunta("O monitoramento é em tempo real?", "breve explicação")

    
        support_frame = QFrame()
        layout_sup = QVBoxLayout(support_frame)
        
        support_text = QLabel("Ainda tem dúvidas?\nEntre em contato: vinc.suporte@gmail.com")
        support_text.setStyleSheet("color: white; font-size: 14px; padding: 22px;")
        layout_sup.addWidget(support_text)
        self.scroll_layout.addWidget(support_frame)
        self.scroll_layout.addStretch()

    def criar_pergunta(self, titulo, resposta):
        frame = QFrame()
        layout_f = QVBoxLayout(frame)

        header = QPushButton(f"{titulo} ▼")

        
        answer = QLabel(resposta)
        answer.hide()

     
        def toggle():
            if answer.isVisible():
                answer.hide()
                header.setText(f"{titulo} ▼")
            else:
                answer.show()
                header.setText(f"{titulo} ▲")

        header.clicked.connect(toggle)
        
        layout_f.addWidget(header)
        layout_f.addWidget(answer)
        self.scroll_layout.addWidget(frame)