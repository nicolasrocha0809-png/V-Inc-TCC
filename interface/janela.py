from PySide6.QtWidgets import (QMainWindow, QStackedWidget, QWidget, QHBoxLayout, QVBoxLayout, QFrame, QPushButton)
from interface.prefs_manager import PrefsManager
from interface.telas.login import LoginScreen
from interface.telas.loading import LoadingScreen
from interface.telas.inicio import InicioScreen
from interface.telas.comandos import ComandosScreen
from interface.telas.monitor import MonitorScreen
from interface.telas.historico import HistoricoScreen
from interface.telas.configuracoes import ConfiguracoesScreen
from interface.telas.ajuda import AjudaScreen

class JanelaPrincipal(QMainWindow):
    def __init__(self, supabase_client=None):
        super().__init__()
        self.supabase = supabase_client
        self.current_user_id = None
        
        self.setWindowTitle("V-Inc - Assistente")
        self.resize(960, 640)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.layout_principal = QHBoxLayout(self.central_widget)
        self.layout_principal.setContentsMargins(0, 0, 0, 0)
        self.layout_principal.setSpacing(0)

      
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(200)
        self.layout_sidebar = QVBoxLayout(self.sidebar)
        self.layout_principal.addWidget(self.sidebar)

       
        self.btn_inicio = QPushButton("Início"); self.btn_inicio.setObjectName("menu_btn")
        self.btn_inicio.clicked.connect(lambda: self.mudar_tela(2))
        
        self.btn_comandos = QPushButton("Comandos"); self.btn_comandos.setObjectName("menu_btn")
        self.btn_comandos.clicked.connect(lambda: self.mudar_tela(3))
        
        self.btn_monitor = QPushButton("Monitor"); self.btn_monitor.setObjectName("menu_btn")
        self.btn_monitor.clicked.connect(lambda: self.mudar_tela(4))
        
        self.btn_historico = QPushButton("Histórico"); self.btn_historico.setObjectName("menu_btn")
        self.btn_historico.clicked.connect(lambda: self.mudar_tela(5))
        
        self.btn_config = QPushButton("Configurações"); self.btn_config.setObjectName("menu_btn")
        self.btn_config.clicked.connect(lambda: self.mudar_tela(6))
        
        for btn in [self.btn_inicio, self.btn_comandos, self.btn_monitor, self.btn_historico, self.btn_config]:
            self.layout_sidebar.addWidget(btn)
        
        self.layout_sidebar.addStretch()
        
       
        self.btn_ajuda = QPushButton(" Ajuda"); self.btn_ajuda.setObjectName("ajuda_btn")
        self.btn_ajuda.clicked.connect(lambda: self.mudar_tela(7))
        self.layout_sidebar.addWidget(self.btn_ajuda)

      
        self.stack = QStackedWidget()
        self.layout_principal.addWidget(self.stack)
        
    
        self.login_screen = LoginScreen(supabase_client=self.supabase, callback_sucesso=self.ir_para_loading)
        self.stack.addWidget(self.login_screen) 
        self.sidebar.hide()

    def mudar_tela(self, index):
        self.stack.setCurrentIndex(index)
        self.sidebar.hide() if index < 2 else self.sidebar.show()

    def ir_para_loading(self, user_id):
        self.current_user_id = user_id
        self.loading_screen = LoadingScreen(callback_final=self.ir_para_inicio)
        self.stack.addWidget(self.loading_screen) 
        self.mudar_tela(1)

    def ir_para_inicio(self):
       
        self.stack.addWidget(InicioScreen())          
        self.stack.addWidget(ComandosScreen())        
        self.stack.addWidget(MonitorScreen())         
        self.stack.addWidget(HistoricoScreen())      
        self.stack.addWidget(ConfiguracoesScreen(     
            supabase_client=self.supabase, 
            user_id=self.current_user_id
        ))
        self.stack.addWidget(AjudaScreen())
        self.mudar_tela(2)