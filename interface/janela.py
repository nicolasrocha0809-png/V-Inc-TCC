from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from config import settings
from interface.telas.login import LoginScreen
from interface.telas.loading import LoadingScreen
from interface.telas.inicio import InicioScreen
from interface.telas.comandos import ComandosScreen
from interface.telas.historico import HistoricoScreen
from interface.telas.configuracoes import ConfiguracoesScreen
from interface.telas.ajuda import AjudaScreen


class JanelaPrincipal(QMainWindow):
    def __init__(self, supabase_client=None):
        super().__init__()
        self.supabase = supabase_client
        self.current_user_id = None
        
        self.setWindowTitle("V.INC — Voz Inclusiva")
        self.setMinimumSize(960, 640)
        self.resize(1120, 720)
        self.central_widget = QWidget()
        self.central_widget.setObjectName("janela_principal")
        self.setCentralWidget(self.central_widget)
        
        self.layout_principal = QHBoxLayout(self.central_widget)
        self.layout_principal.setContentsMargins(0, 0, 0, 0)
        self.layout_principal.setSpacing(0)

        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(232)
        self.layout_sidebar = QVBoxLayout(self.sidebar)
        self.layout_sidebar.setContentsMargins(16, 24, 16, 20)
        self.layout_sidebar.setSpacing(8)
        self.layout_principal.addWidget(self.sidebar)

        marca = QLabel("V.INC")
        marca.setObjectName("marca_sidebar")
        marca.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        marca.setAccessibleName("V.INC — Voz Inclusiva")
        self.layout_sidebar.addWidget(marca)

        subtitulo = QLabel("VOZ INCLUSIVA")
        subtitulo.setObjectName("subtitulo_sidebar")
        self.layout_sidebar.addWidget(subtitulo)
        self.layout_sidebar.addSpacing(24)

        titulo_menu = QLabel("NAVEGAÇÃO")
        titulo_menu.setObjectName("titulo_menu")
        self.layout_sidebar.addWidget(titulo_menu)
        self.layout_sidebar.addSpacing(4)

        self.btn_inicio = self._criar_botao_menu("Início", 2)
        self.btn_comandos = self._criar_botao_menu("Comandos", 3)
        self.btn_historico = self._criar_botao_menu("Histórico", 4)
        self.btn_config = self._criar_botao_menu("Configurações", 5)

        self.botoes_menu = {
            2: self.btn_inicio,
            3: self.btn_comandos,
            4: self.btn_historico,
            5: self.btn_config,
        }

        for botao in self.botoes_menu.values():
            self.layout_sidebar.addWidget(botao)

        self.layout_sidebar.addStretch()

        divisor = QFrame()
        divisor.setObjectName("divisor_sidebar")
        divisor.setFixedHeight(1)
        self.layout_sidebar.addWidget(divisor)
        self.layout_sidebar.addSpacing(8)

        self.btn_ajuda = QPushButton("Ajuda e suporte")
        self.btn_ajuda.setObjectName("ajuda_btn")
        self.btn_ajuda.setCheckable(True)
        self.btn_ajuda.setCursor(Qt.PointingHandCursor)
        self.btn_ajuda.setAccessibleDescription(
            "Abre as perguntas frequentes e os canais de suporte."
        )
        self.btn_ajuda.clicked.connect(lambda: self.mudar_tela(6))
        self.layout_sidebar.addWidget(self.btn_ajuda)

        self.stack = QStackedWidget()
        self.stack.setObjectName("conteudo_principal")
        self.layout_principal.addWidget(self.stack)

        self.login_screen = LoginScreen(
            supabase_client=self.supabase,
            callback_sucesso=self.ir_para_loading,
        )
        self.stack.addWidget(self.login_screen)
        self.sidebar.hide()

    def _criar_botao_menu(self, texto, indice):
        botao = QPushButton(texto)
        botao.setObjectName("menu_btn")
        botao.setCheckable(True)
        botao.setCursor(Qt.PointingHandCursor)
        botao.setAccessibleDescription(f"Abre a tela {texto}.")
        botao.clicked.connect(lambda: self.mudar_tela(indice))
        return botao

    def mudar_tela(self, index):
        self.stack.setCurrentIndex(index)
        self.sidebar.hide() if index < 2 else self.sidebar.show()

        for indice, botao in self.botoes_menu.items():
            botao.setChecked(indice == index)

        self.btn_ajuda.setChecked(index == 6)

    def ir_para_loading(self, user_id):
        self.current_user_id = user_id
        settings.set("usuario", "id_usuario_atual", user_id)
        
        self.loading_screen = LoadingScreen(callback_final=self.ir_para_inicio)
        self.stack.addWidget(self.loading_screen) 
        self.mudar_tela(1)

    def ir_para_inicio(self):
       
        user_id_ativo = settings.get("usuario", "id_usuario_atual") or self.current_user_id

        
        self.stack.addWidget(InicioScreen())         
        self.stack.addWidget(ComandosScreen())        
        
       
        self.stack.addWidget(HistoricoScreen(        
            supabase_client=self.supabase, 
            user_id=user_id_ativo
        ))       
        
        self.stack.addWidget(ConfiguracoesScreen(    
            supabase_client=self.supabase, 
            user_id=user_id_ativo
        ))
        
        self.stack.addWidget(AjudaScreen())          
        self.mudar_tela(2)
