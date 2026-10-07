from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QApplication,
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
from interface.telas.conta import ContaScreen
from interface.telas.ajuda import AjudaScreen
from interface.acessibilidade import anunciar


class BotaoNavegacao(QPushButton):
    """Botão lateral acionável de forma equivalente por Enter ou Espaço."""

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.click()
            event.accept()
            return

        super().keyPressEvent(event)


class JanelaPrincipal(QMainWindow):
    def __init__(self, supabase_client=None):
        super().__init__()
        self.supabase = supabase_client
        self.current_user_id = None
        
        self.setWindowTitle("V.INC — Voz Inclusiva")
        self.setWindowIcon(QApplication.windowIcon())
        self.setMinimumSize(900, 560)
        self._definir_tamanho_inicial()
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

        self.botoes_navegacao = {
            2: self.btn_inicio,
            3: self.btn_comandos,
            4: self.btn_historico,
            5: self.btn_config,
        }

        for botao in self.botoes_navegacao.values():
            self.layout_sidebar.addWidget(botao)

        self.layout_sidebar.addStretch()

        self.btn_conta = self._criar_botao_menu("Minha conta", 6)
        self.btn_conta.setAccessibleDescription(
            "Abre os dados e as opções da conta conectada."
        )
        self.layout_sidebar.addWidget(self.btn_conta)

        self.botoes_menu = {
            **self.botoes_navegacao,
            6: self.btn_conta,
        }

        divisor = QFrame()
        divisor.setObjectName("divisor_sidebar")
        divisor.setFixedHeight(1)
        self.layout_sidebar.addWidget(divisor)
        self.layout_sidebar.addSpacing(8)

        self.btn_ajuda = BotaoNavegacao("Ajuda e suporte")
        self.btn_ajuda.setObjectName("ajuda_btn")
        self.btn_ajuda.setCheckable(True)
        self.btn_ajuda.setCursor(Qt.PointingHandCursor)
        self.btn_ajuda.setAccessibleDescription(
            "Abre as perguntas frequentes e os canais de suporte."
        )
        self.btn_ajuda.clicked.connect(lambda: self.mudar_tela(7))
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

        QTimer.singleShot(0, self._centralizar_janela)
        QTimer.singleShot(0, self._restaurar_sessao)

    def _definir_tamanho_inicial(self):
        tela = QApplication.primaryScreen()

        if tela is None:
            self.resize(1000, 640)
            return

        area_disponivel = tela.availableGeometry()
        largura = min(1120, max(900, int(area_disponivel.width() * 0.82)))
        altura = min(680, max(560, int(area_disponivel.height() * 0.88)))
        self.resize(largura, altura)

    def _centralizar_janela(self):
        tela = self.screen() or QApplication.primaryScreen()

        if tela is None:
            return

        area_disponivel = tela.availableGeometry()
        geometria = self.frameGeometry()
        geometria.moveCenter(area_disponivel.center())
        self.move(geometria.topLeft())

    def _criar_botao_menu(self, texto, indice):
        botao = BotaoNavegacao(texto)
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

        self.btn_ajuda.setChecked(index == 7)

        nomes_telas = {
            0: "Login",
            1: "Carregamento",
            2: "Início",
            3: "Comandos",
            4: "Histórico",
            5: "Configurações",
            6: "Minha conta",
            7: "Ajuda e suporte",
        }
        tela_atual = self.stack.currentWidget()
        anunciar(tela_atual, f"Tela {nomes_telas.get(index, 'atual')} aberta.")

    def _restaurar_sessao(self):
        sessao_ativa = settings.get("usuario", "sessao_ativa")
        user_id = settings.get("usuario", "id_usuario_atual")
        email = settings.get("usuario", "email_usuario_atual")

        if sessao_ativa and user_id:
            self.ir_para_loading(user_id, email)

    def ir_para_loading(self, user_id, email=None):
        self.current_user_id = user_id
        settings.set("usuario", "id_usuario_atual", user_id)
        settings.set("usuario", "email_usuario_atual", email)
        settings.set("usuario", "sessao_ativa", True)
        
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

        self.stack.addWidget(ContaScreen(
            supabase_client=self.supabase,
            user_id=user_id_ativo,
            email=settings.get("usuario", "email_usuario_atual"),
            callback_logout=self.encerrar_sessao,
        ))

        self.stack.addWidget(AjudaScreen())          
        self.mudar_tela(2)

    def encerrar_sessao(self):
        settings.set("usuario", "sessao_ativa", False)
        settings.set("usuario", "id_usuario_atual", None)
        settings.set("usuario", "email_usuario_atual", None)
        self.current_user_id = None

        while self.stack.count() > 1:
            tela = self.stack.widget(1)
            self.stack.removeWidget(tela)
            tela.deleteLater()

        self.login_screen.criar_tela_login()
        self.mudar_tela(0)
