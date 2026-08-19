import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QComboBox, 
                                QSlider, QPushButton, QApplication)
from PySide6.QtCore import Qt
from config import settings
from interface.prefs_manager import PrefsManager

class ConfiguracoesScreen(QWidget):
    def __init__(self, parent=None, supabase_client=None, user_id=None):
        super().__init__(parent)
        
        self.prefs_manager = PrefsManager(supabase_client, user_id)
        self.layout = QVBoxLayout(self)
        
        # --- 1. Tema ---
        self.layout.addWidget(QLabel("Escolha o Tema:"))
        self.combo_tema = QComboBox()
        self.combo_tema.addItems(["escuro", "claro", "contraste"])
        
        tema_atual = settings.get("visual", "tema") or "escuro"
        index = self.combo_tema.findText(tema_atual)
        if index != -1:
            self.combo_tema.setCurrentIndex(index)
        self.layout.addWidget(self.combo_tema)
        
        # --- 2. Tamanho da Fonte ---
        self.layout.addWidget(QLabel("Tamanho da Fonte:"))
        self.combo_fonte = QComboBox()
        self.combo_fonte.addItems(["10px", "12px", "14px", "16px"])
        
        fonte_atual = settings.get("visual", "fonte") or "12px"
        index_fonte = self.combo_fonte.findText(fonte_atual)
        if index_fonte != -1:
            self.combo_fonte.setCurrentIndex(index_fonte)
        self.layout.addWidget(self.combo_fonte)

        # --- 3. Idioma ---
        self.layout.addWidget(QLabel("Idioma:"))
        self.combo_idioma = QComboBox()
        self.combo_idioma.addItems(["pt_BR", "en_US", "es_ES"])
        
        idioma_atual = settings.get("geral", "idioma") or "pt_BR"
        index_idioma = self.combo_idioma.findText(idioma_atual)
        if index_idioma != -1:
            self.combo_idioma.setCurrentIndex(index_idioma)
        self.layout.addWidget(self.combo_idioma)

        # --- 4. Volume do Áudio (Separado) ---
        self.layout.addWidget(QLabel("Volume do Áudio:"))
        self.slider_volume = QSlider(Qt.Horizontal)
        self.slider_volume.setRange(0, 100)
        
        volume_atual = int(settings.get("audio", "volume") or 80)
        self.slider_volume.setValue(volume_atual)
        self.layout.addWidget(self.slider_volume)

        # --- 5. Velocidade do Áudio (Separado) ---
        self.layout.addWidget(QLabel("Velocidade do Áudio:"))
        self.slider_velocidade = QSlider(Qt.Horizontal)
        self.slider_velocidade.setRange(0, 100)
        
        velocidade_atual = int(settings.get("audio", "velocidade") or 80)
        self.slider_velocidade.setValue(velocidade_atual)
        self.layout.addWidget(self.slider_velocidade)

        # --- Botão Salvar ---
        self.btn_aplicar = QPushButton("Aplicar e Salvar Alterações")
        self.btn_aplicar.clicked.connect(self.aplicar_configuracoes)
        self.layout.addWidget(self.btn_aplicar)
        
        self.lbl_status = QLabel("")
        self.layout.addWidget(self.lbl_status)
        
    def aplicar_configuracoes(self):
        # Coleta os valores da interface de forma independente
        novo_tema = self.combo_tema.currentText()
        nova_fonte = self.combo_fonte.currentText()
        novo_idioma = self.combo_idioma.currentText()
        novo_volume = self.slider_volume.value()
        nova_velocidade = self.slider_velocidade.value()

        # Atualiza o arquivo de configurações local (settings)
        settings.set("visual", "tema", novo_tema)
        settings.set("visual", "fonte", nova_fonte)
        settings.set("geral", "idioma", novo_idioma)
        settings.set("audio", "volume", novo_volume)
        settings.set("audio", "velocidade", nova_velocidade)

        # Salva via PrefsManager no Supabase
        self.prefs_manager.salvar_preferencia("tema", novo_tema)
        self.prefs_manager.salvar_preferencia("fonte", nova_fonte)
        self.prefs_manager.salvar_preferencia("idioma", novo_idioma)
        self.prefs_manager.salvar_preferencia("volume", str(novo_volume))
        self.prefs_manager.salvar_preferencia("velocidade", str(nova_velocidade))

        # Aplica o QSS do Tema e a nova fonte globalmente
        pasta_telas = os.path.dirname(os.path.abspath(__file__))
        raiz = os.path.dirname(os.path.dirname(pasta_telas))
        
        caminho_base = os.path.join(raiz, "interface", "estilos", "base.qss")
        caminho_tema = os.path.join(raiz, "interface", "temas", f"{novo_tema}.qss")
        
        if os.path.exists(caminho_base) and os.path.exists(caminho_tema):
            with open(caminho_base, "r", encoding="utf-8") as f1, \
                 open(caminho_tema, "r", encoding="utf-8") as f2:
                
                estilo_final = f1.read() + "\n" + f2.read() + f"\nQWidget {{ font-size: {nova_fonte}; }}"
                QApplication.instance().setStyleSheet(estilo_final)
                
                self.lbl_status.setText("Configurações aplicadas e salvas com sucesso!")
        else:
            self.lbl_status.setText("Erro: Arquivos de estilo não encontrados!")
            print(f"DEBUG: Base em {caminho_base}")