from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar, QFrame
from PySide6.QtCore import Qt, QTimer
from interface.prefs_manager import PrefsManager

class LoadingScreen(QWidget):
    def __init__(self, callback_final=None, parent=None):
        super().__init__(parent)
        self.callback_final = callback_final
    
        self.layout_principal = QVBoxLayout(self)
        self.layout_principal.setContentsMargins(40, 40, 40, 40)
        
        self.frame = QFrame()
        self.frame.setStyleSheet("background-color: #0F172A; border-radius: 20px; border: 2px solid #334155;")
        self.layout_principal.addWidget(self.frame)
        
        layout_f = QVBoxLayout(self.frame)
        
        self.lbl_icon = QLabel("🎤")
        self.lbl_icon.setAlignment(Qt.AlignCenter)
        self.lbl_icon.setStyleSheet("font-size: 80px;")
        layout_f.addWidget(self.lbl_icon)

        self.lbl_titulo = QLabel("V-Inc")
        self.lbl_titulo.setAlignment(Qt.AlignCenter)
        self.lbl_titulo.setStyleSheet("font-size: 38px; font-weight: bold; color: #93C5FD;")
        layout_f.addWidget(self.lbl_titulo)

        self.lbl_status = QLabel("Carregando sistema...")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        self.lbl_status.setStyleSheet("font-size: 15px; color: #CBD5E1;")
        layout_f.addWidget(self.lbl_status)

        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar { border: 2px solid #1E2937; border-radius: 6px; text-align: center; color: white; }
            QProgressBar::chunk { background-color: #60A5FA; }
        """)
        layout_f.addWidget(self.progress_bar)

        self.lbl_modulos = QLabel("Iniciando módulos...")
        self.lbl_modulos.setAlignment(Qt.AlignCenter)
        self.lbl_modulos.setStyleSheet("color: #64748B;")
        layout_f.addWidget(self.lbl_modulos)

        self.progresso = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.atualizar_progresso)
        self.timer.start(50) # Atualiza a cada 50ms

    def atualizar_progresso(self):
        self.progresso += 1
        self.progress_bar.setValue(self.progresso)
        
        if self.progresso == 35: self.lbl_modulos.setText("Carregando modelo de voz...")
        if self.progresso == 60: self.lbl_modulos.setText("Inicializando reconhecimento...")
        if self.progresso == 100:
            self.timer.stop()
            self.lbl_status.setText("Sistema pronto!")
            if self.callback_final:
                QTimer.singleShot(500, self.callback_final)