import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QComboBox, 
                               QPushButton, QApplication)
from config import settings
from interface.prefs_manager import PrefsManager

class ConfiguracoesScreen(QWidget):
    def __init__(self, parent=None, supabase_client=None, user_id=None):
        super().__init__(parent)
        
        self.prefs_manager = PrefsManager(supabase_client, user_id)
        self.layout = QVBoxLayout(self)
        
        self.layout.addWidget(QLabel("Escolha o Tema:"))
        self.combo_tema = QComboBox()
        self.combo_tema.addItems(["escuro", "claro", "contraste"])
        
        tema_atual = settings.get("visual", "tema")
        index = self.combo_tema.findText(tema_atual)
        if index != -1:
            self.combo_tema.setCurrentIndex(index)
        self.layout.addWidget(self.combo_tema)
        
        self.btn_aplicar = QPushButton("Aplicar Alterações")
        self.btn_aplicar.clicked.connect(self.aplicar_configuracoes)
        self.layout.addWidget(self.btn_aplicar)
        
        self.lbl_status = QLabel("")
        self.layout.addWidget(self.lbl_status)

    def aplicar_configuracoes(self):
        novo_tema = self.combo_tema.currentText()
        settings.set("visual", "tema", novo_tema)
        self.prefs_manager.salvar_preferencia("tema", novo_tema)
        
    
        pasta_telas = os.path.dirname(os.path.abspath(__file__))
        raiz = os.path.dirname(os.path.dirname(pasta_telas))
        
        caminho_base = os.path.join(raiz, "interface", "estilos", "base.qss")
        caminho_tema = os.path.join(raiz, "interface", "temas", f"{novo_tema}.qss")
        
        if os.path.exists(caminho_base) and os.path.exists(caminho_tema):
            with open(caminho_base, "r", encoding="utf-8") as f1, \
                 open(caminho_tema, "r", encoding="utf-8") as f2:
                estilo_final = f1.read() + "\n" + f2.read()
                QApplication.instance().setStyleSheet(estilo_final)
                self.lbl_status.setText("Tema aplicado!")
        else:
            self.lbl_status.setText("Erro: Arquivos não encontrados!")
            print(f"DEBUG: Base em {caminho_base}")