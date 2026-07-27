from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QTextEdit
from PySide6.QtCore import Qt

class MonitorScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.main_layout = QVBoxLayout(self)
        
       
        self.lbl_titulo = QLabel("👁 Resultado de Texto ao Vivo")
        self.lbl_titulo.setObjectName("titulo_tela")
        self.lbl_titulo.setAlignment(Qt.AlignLeft)
        
     
        self.text_area = QTextEdit()
        self.text_area.setObjectName("display_texto")
        self.text_area.setReadOnly(True) 
        self.text_area.setPlaceholderText("Aguardando entrada de dados...")
        
       
        self.main_layout.addWidget(self.lbl_titulo)
        self.main_layout.addWidget(self.text_area)