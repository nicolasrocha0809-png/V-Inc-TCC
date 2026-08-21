import sys, random, bcrypt, os, threading
from pathlib import Path
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QBoxLayout, QLabel, QLineEdit, QPushButton, QFrame, QStyle, QStyleOptionButton, QToolButton, QSizePolicy
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QFont, QFontMetrics, QKeySequence, QShortcut, QPainter, QPen, QColor, QIcon
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from interface.prefs_manager import PrefsManager

EMAIL_REMETENTE, SENHA_REMETENTE = os.getenv("EMAIL_REMETENTE"), os.getenv("SENHA_REMETENTE")

class BotaoAcessivel(QPushButton):
    def paintEvent(self, event):
        option = QStyleOptionButton()
        self.initStyleOption(option)
        option.state &= ~QStyle.State_HasFocus

        painter = QPainter(self)
        self.style().drawControl(QStyle.CE_PushButton, option, painter, self)

        if self.hasFocus():
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setPen(QPen(QColor("#FACC15"), 4))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(self.rect().adjusted(2, 2, -2, -2), 7, 7)

class BotaoVisibilidadeSenha(QToolButton):
    def __init__(self, campo_senha, parent=None):
        super().__init__(parent)
        self.campo_senha = campo_senha
        self.senha_visivel = False
        self.setCheckable(True)
        self.setFixedSize(44, 44)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip("Mostrar senha")
        self.setAccessibleName("Mostrar senha")
        self.toggled.connect(self.alternar_visibilidade)
        self.atualizar_icone()

    def criar_icone(self, aberto):
        pixmap = QPixmap(24, 24)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor("#E2E8F0"), 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(3, 7, 18, 10)
        painter.setBrush(QColor("#E2E8F0"))
        painter.drawEllipse(9, 9, 6, 6)
        if not aberto:
            painter.setPen(QPen(QColor("#FACC15"), 2))
            painter.drawLine(3, 20, 21, 4)
        painter.end()
        return QIcon(pixmap)

    def atualizar_icone(self):
        self.setIcon(self.criar_icone(self.senha_visivel))

    def alternar_visibilidade(self, visivel):
        self.senha_visivel = visivel
        self.campo_senha.setEchoMode(
            QLineEdit.Normal if visivel else QLineEdit.Password
        )
        texto = "Ocultar senha" if visivel else "Mostrar senha"
        self.setToolTip(texto)
        self.setAccessibleName(texto)
        self.atualizar_icone()

class LoginScreen(QWidget):
    def __init__(self, supabase_client, callback_sucesso, parent=None):
        super().__init__(parent)
        self.callback_sucesso = callback_sucesso
        self.supabase = supabase_client
        self.codigo_verificacao = None
        self.email_recuperando = None
        self.lbl_logo = None
        self.col_esquerda = None
        self.col_direita = None
        self.tela_atual = "login"
        self.botao_acao_atual = None
        self.botao_voltar_atual = None

        self.atalho_enter = QShortcut(QKeySequence(Qt.Key_Return), self)
        self.atalho_enter.setContext(Qt.WidgetWithChildrenShortcut)
        self.atalho_enter.activated.connect(self.ativar_acao_principal)
        self.atalho_enter_numerico = QShortcut(QKeySequence(Qt.Key_Enter), self)
        self.atalho_enter_numerico.setContext(Qt.WidgetWithChildrenShortcut)
        self.atalho_enter_numerico.activated.connect(self.ativar_acao_principal)
        self.atalho_escape = QShortcut(QKeySequence("Esc"), self)
        self.atalho_escape.setContext(Qt.WidgetWithChildrenShortcut)
        self.atalho_escape.activated.connect(self.voltar_para_login)

        # Estiliza O FUNDO DA TELA INTEIRA (troque #1e222d pela sua cor desejada em hex)
        self.setStyleSheet("""
            LoginScreen {
                background-color: #1e222d;
            }
        """)

        # Contêiner central único para evitar sobreposição entre telas
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(80, 48, 80, 48)
        self.main_layout.setSpacing(64)
        self.main_layout.setAlignment(Qt.AlignCenter)

        self.card_container = QWidget(self)
        self.card_container.setObjectName("card_container")
        self.card_layout = QVBoxLayout(self.card_container)
        self.card_layout.setContentsMargins(0, 0, 0, 0)
        self.card_layout.setSpacing(0)
        self.card_layout.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.card_container, alignment=Qt.AlignCenter)

        self.criar_tela_login()

    def limpar_card(self):
        while self.card_layout.count():
            item = self.card_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._limpar_sub_layout(item.layout())
                item.layout().deleteLater()

    def _limpar_sub_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._limpar_sub_layout(item.layout())
                item.layout().deleteLater()

    def criar_tela_login(self):
        self.limpar_card()

        painel = QWidget(self.card_container)
        painel.setObjectName("painel_login")
        painel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        painel_layout = QHBoxLayout(painel)
        painel_layout.setContentsMargins(0, 0, 0, 0)
        painel_layout.setSpacing(64)
        painel_layout.setAlignment(Qt.AlignCenter)

        # --- COLUNA 1: ESQUERDA (Marca e Boas-vindas) ---
        self.col_esquerda = QVBoxLayout()
        self.col_esquerda.setAlignment(Qt.AlignCenter)

        self.lbl_titulo = QLabel("V-Inc"); self.lbl_titulo.setObjectName("titulo_login")
        self.lbl_logo = QLabel(); self.lbl_logo.setObjectName("logo_login")
        logo_path = Path(__file__).resolve().parents[2] / "essa.png"
        self.logo_pixmap = QPixmap(str(logo_path))
        self.atualizar_logo()
        self.lbl_sub = QLabel("Voz Inclusiva"); self.lbl_sub.setObjectName("subtitulo_login")

        self.col_esquerda.addWidget(self.lbl_titulo, alignment=Qt.AlignCenter)
        self.col_esquerda.addWidget(self.lbl_logo, alignment=Qt.AlignCenter)
        self.col_esquerda.addWidget(self.lbl_sub, alignment=Qt.AlignCenter)

        # --- COLUNA 2: DIREITA (Formulário) ---
        self.col_direita = QVBoxLayout()
        self.col_direita.setAlignment(Qt.AlignCenter)
        self.col_direita.setSpacing(10)

        self.txt_email = QLineEdit(); self.txt_email.setPlaceholderText("nome@exemplo.com")
        self.txt_senha, self.btn_mostrar_senha = self.criar_campo_senha(
            "********", "Senha", "Informe sua senha de acesso."
        )
        self.lbl_e = QLabel("Email de Acesso"); self.lbl_e.setObjectName("label_input")
        self.lbl_e.setBuddy(self.txt_email)
        self.lbl_s = QLabel("Senha"); self.lbl_s.setObjectName("label_input")
        self.lbl_s.setBuddy(self.txt_senha)

        for input_field in [self.txt_email, self.txt_senha]:
            input_field.setMaximumWidth(380)

        self.btn_entrar = BotaoAcessivel("Entrar →"); self.btn_entrar.setObjectName("btn_entrar")
        self.btn_entrar.setMaximumWidth(380)
        self.btn_entrar.clicked.connect(self.acao_login)

        self.btn_cad = BotaoAcessivel("Criar nova conta"); self.btn_cad.setObjectName("btn_secundario")
        self.btn_cad.setMaximumWidth(380)
        self.btn_cad.clicked.connect(self.criar_tela_cadastro)

        self.btn_rec = BotaoAcessivel("Esqueci minha senha"); self.btn_rec.setObjectName("btn_link")
        self.btn_rec.clicked.connect(self.criar_tela_recuperacao)

        self.lbl_status = QLabel(""); self.lbl_status.setObjectName("status_msg")

        self.linha_senha = self.criar_linha_senha(self.txt_senha, self.btn_mostrar_senha)
        for w in [self.lbl_e, self.txt_email, self.lbl_s, self.btn_entrar, self.btn_cad]:
            self.col_direita.addWidget(w)
        self.col_direita.insertWidget(3, self.linha_senha)

        self.col_direita.addWidget(self.btn_rec, alignment=Qt.AlignCenter)
        self.col_direita.addWidget(self.lbl_status, alignment=Qt.AlignCenter)

        self.tela_atual = "login"
        self.botao_acao_atual = self.btn_entrar
        self.botao_voltar_atual = None
        self.configurar_navegacao(
            [self.txt_email, self.txt_senha, self.btn_mostrar_senha],
            [self.btn_entrar, self.btn_cad, self.btn_rec],
        )

        painel_layout.addLayout(self.col_esquerda, stretch=1)
        painel_layout.addLayout(self.col_direita, stretch=1)
        self.card_layout.addWidget(painel)
        self.atualizar_layout_responsivo()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.atualizar_layout_responsivo()

    def atualizar_logo(self):
        if self.lbl_logo is None or self.logo_pixmap.isNull():
            return
        tamanho = max(140, min(320, int(self.width() * 0.28)))
        self.lbl_logo.setPixmap(self.logo_pixmap.scaled(
            tamanho, tamanho, Qt.KeepAspectRatio, Qt.SmoothTransformation
        ))

    def atualizar_layout_responsivo(self):
        if not hasattr(self, "card_container") or self.card_container is None:
            return
        compacto = self.width() < 760
        self.main_layout.setDirection(
            QBoxLayout.TopToBottom if compacto else QBoxLayout.LeftToRight
        )
        self.main_layout.setContentsMargins(
            28 if compacto else 80,
            28 if compacto else 48,
            28 if compacto else 80,
            28 if compacto else 48,
        )
        self.main_layout.setSpacing(28 if compacto else 64)

        if hasattr(self, "col_esquerda") and hasattr(self, "col_direita"):
            painel = self.card_container.findChild(QWidget, "painel_login")
            if painel is not None:
                layout = painel.layout()
                if layout is not None:
                    layout.setDirection(
                        QBoxLayout.TopToBottom if compacto else QBoxLayout.LeftToRight
                    )
                    layout.setSpacing(28 if compacto else 64)

        self.atualizar_logo()
        self.atualizar_dimensoes_responsivas()

    def atualizar_dimensoes_responsivas(self):
        largura = max(320, self.width())
        fator_largura = max(0.0, min(1.0, (largura - 420) / 680))

        fonte_titulo = QFont(self.lbl_titulo.font())
        fonte_titulo.setPointSizeF(20.0 + (14.0 * fator_largura))
        self.lbl_titulo.setFont(fonte_titulo)

        fonte_subtitulo = QFont(self.lbl_sub.font())
        fonte_subtitulo.setPointSizeF(18.0 + (10.0 * fator_largura))
        self.lbl_sub.setFont(fonte_subtitulo)

        largura_controles = max(240, min(420, largura - (56 if largura < 760 else 120)))
        for botao in self.findChildren(QToolButton):
            tamanho_botao = max(40, min(48, int(40 + (8 * fator_largura))))
            botao.setFixedSize(tamanho_botao, tamanho_botao)

        for campo in self.findChildren(QLineEdit):
            largura_campo = largura_controles
            for botao in self.findChildren(BotaoVisibilidadeSenha):
                if botao.campo_senha is campo:
                    largura_campo = max(220, largura_controles - botao.width() - 12)
                    break
            campo.setMaximumWidth(max(180, largura_campo))
            fonte_campo = QFont(campo.font())
            fonte_campo.setPointSizeF(12.0 + (5.0 * fator_largura))
            campo.setFont(fonte_campo)

        for linha in self.findChildren(QWidget):
            if linha.objectName() == "linha_senha":
                linha.setFixedWidth(largura_controles)

        for botao in self.findChildren(QPushButton):
            if botao.objectName() != "btn_link":
                botao.setMaximumWidth(largura_controles)
                fonte_botao = QFont(botao.font())
                fonte_botao.setPointSizeF(13.0 + (3.0 * fator_largura))
                botao.setFont(fonte_botao)

        for label in self.findChildren(QLabel):
            fonte_label = QFont(label.font())
            if label.objectName() == "titulo_tela":
                tamanho = 20.0 + (8.0 * fator_largura)
            elif label.objectName() == "label_input":
                tamanho = 13.0 + (4.0 * fator_largura)
            elif label.objectName() == "descricao_tela":
                tamanho = 13.0 + (3.0 * fator_largura)
            else:
                tamanho = 12.0 + (2.0 * fator_largura)
            fonte_label.setPointSizeF(tamanho)
            label.setFont(fonte_label)
            if label.objectName() == "descricao_tela":
                metricas = QFontMetrics(fonte_label)
                altura = metricas.boundingRect(
                    0,
                    0,
                    max(180, label.maximumWidth()),
                    1000,
                    Qt.TextWordWrap,
                    label.text(),
                ).height()
                label.setMinimumHeight(altura + 8)

        self.card_layout.invalidate()
        self.card_layout.activate()
        painel = self.card_container.findChild(QWidget, "painel_login")
        if painel is not None and painel.layout() is not None:
            painel.layout().invalidate()
            painel.layout().activate()
        secundario = self.card_container.findChild(QWidget, "container_secundario")
        if secundario is not None and secundario.layout() is not None:
            secundario.layout().invalidate()
            secundario.layout().activate()

    def configurar_navegacao(self, campos, botoes):
        controles = campos + botoes
        for atual, proximo in zip(controles, controles[1:]):
            self.setTabOrder(atual, proximo)
        for campo in campos:
            if hasattr(campo, "returnPressed"):
                campo.returnPressed.connect(self.ativar_acao_principal)
        if controles:
            controles[0].setFocus()

    def criar_campo_senha(self, placeholder, nome_acessivel, descricao=None):
        campo = QLineEdit()
        campo.setPlaceholderText(placeholder)
        campo.setEchoMode(QLineEdit.Password)
        campo.setAccessibleName(nome_acessivel)
        campo.setAccessibleDescription(descricao or "A senha deve ter pelo menos 8 caracteres.")
        botao = BotaoVisibilidadeSenha(campo)
        return campo, botao

    def criar_linha_senha(self, campo, botao):
        linha = QWidget()
        linha.setObjectName("linha_senha")
        linha_layout = QHBoxLayout(linha)
        linha_layout.setContentsMargins(0, 0, 0, 0)
        linha_layout.setSpacing(8)
        campo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        linha_layout.addWidget(campo, stretch=1)
        linha_layout.addWidget(botao)
        return linha

    def ativar_acao_principal(self):
        controle_focado = self.focusWidget()
        if isinstance(controle_focado, (QPushButton, QToolButton)):
            if controle_focado.isVisible() and controle_focado.isEnabled():
                controle_focado.click()
            return
        if self.botao_acao_atual and self.botao_acao_atual.isVisible():
            self.botao_acao_atual.click()

    def voltar_para_login(self):
        if self.tela_atual == "login":
            return
        if self.tela_atual == "cadastro":
            self.criar_tela_login()
            return
        if self.tela_atual == "recuperacao":
            self.criar_tela_login()
            return
        if self.tela_atual == "validacao":
            self.criar_tela_recuperacao()
            return
        if self.tela_atual == "nova_senha":
            self.criar_tela_validar()
            return

    def acao_login(self):
        email, senha = self.txt_email.text().strip(), self.txt_senha.text().strip()
        try:
            res = self.supabase.table("usuarios").select("id, senha_hash").eq("email", email).execute()
            
            if res.data and bcrypt.checkpw(senha.encode('utf-8'), res.data[0]["senha_hash"].encode('utf-8')):
                user_id = res.data[0]["id"]
                if self.callback_sucesso: self.callback_sucesso(user_id)
            else: 
                self.lbl_status.setText("Credenciais inválidas.")
        except Exception as e:
            print(f"DEBUG LOGIN: {e}")
            self.lbl_status.setText("Erro de conexão.")

    def criar_tela_cadastro(self):
        self.limpar_card()
        layout = self.criar_layout_secundario()
        lbl_titulo = QLabel("Criar Conta"); lbl_titulo.setObjectName("titulo_tela")
        lbl_titulo.setAlignment(Qt.AlignCenter)
        lbl_descricao = QLabel("Cadastre seu e-mail e defina uma senha para acessar o V-Inc.")
        lbl_descricao.setObjectName("descricao_tela")
        lbl_descricao.setWordWrap(True)
        lbl_descricao.setMaximumWidth(420)
        lbl_descricao.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        lbl_descricao.setMinimumHeight(48)
        lbl_descricao.setAlignment(Qt.AlignCenter)

        lbl_email = QLabel("E-mail")
        lbl_email.setObjectName("label_input")
        lbl_email.setAlignment(Qt.AlignLeft)
        self.txt_n_email = QLineEdit(); self.txt_n_email.setPlaceholderText("nome@exemplo.com")
        self.txt_n_email.setAccessibleName("E-mail para cadastro")
        self.txt_n_email.setFixedWidth(420)
        self.txt_n_email.setMaximumWidth(420)
        lbl_email.setBuddy(self.txt_n_email)

        lbl_senha = QLabel("Senha")
        lbl_senha.setObjectName("label_input")
        lbl_senha.setAlignment(Qt.AlignLeft)
        self.txt_n_senha, self.btn_mostrar_nova_senha = self.criar_campo_senha(
            "Crie uma senha segura",
            "Senha para cadastro",
            "A senha deve ter pelo menos 8 caracteres."
        )
        self.txt_n_senha.setMaximumWidth(420)
        lbl_senha.setBuddy(self.txt_n_senha)

        lbl_requisito = QLabel("Use pelo menos 8 caracteres.")
        lbl_requisito.setObjectName("ajuda_input")
        lbl_requisito.setAlignment(Qt.AlignCenter)
        btn_salvar = BotaoAcessivel("Criar Conta"); btn_salvar.setObjectName("btn_entrar"); btn_salvar.clicked.connect(self.acao_cadastrar)
        btn_salvar.setAccessibleName("Criar conta")
        btn_salvar.setFixedWidth(420)
        btn_salvar.setMaximumWidth(420)
        btn_voltar = BotaoAcessivel("Voltar"); btn_voltar.setObjectName("btn_secundario"); btn_voltar.clicked.connect(self.criar_tela_login)
        btn_voltar.setAccessibleName("Voltar para o login")
        btn_voltar.setFixedWidth(420)
        btn_voltar.setMaximumWidth(420)

        self.lbl_status_cadastro = QLabel(""); self.lbl_status_cadastro.setObjectName("status_msg")
        self.lbl_status_cadastro.setAlignment(Qt.AlignCenter)

        self.linha_senha = self.criar_linha_senha(self.txt_n_senha, self.btn_mostrar_nova_senha)
        self.linha_senha.setFixedWidth(420)
        self.linha_senha.setMaximumWidth(420)
        for w in [
            lbl_titulo, lbl_descricao, lbl_email, self.txt_n_email,
            lbl_senha, self.linha_senha, lbl_requisito, btn_salvar, btn_voltar,
            self.lbl_status_cadastro
        ]:
            layout.addWidget(w)
        self.tela_atual = "cadastro"
        self.botao_acao_atual = btn_salvar
        self.botao_voltar_atual = btn_voltar
        self.atualizar_dimensoes_responsivas()
        self.configurar_navegacao([self.txt_n_email, self.txt_n_senha, self.btn_mostrar_nova_senha], [btn_salvar, btn_voltar])

    def acao_cadastrar(self):
        email, senha = self.txt_n_email.text().strip(), self.txt_n_senha.text().strip()
        if not email or not senha:
            self.lbl_status_cadastro.setText("Preencha todos os campos.")
            return

        if len(senha) < 8:
            self.lbl_status_cadastro.setText("A senha deve ter pelo menos 8 caracteres.")
            self.txt_n_senha.setFocus()
            return
            
        try:
            hash_s = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            self.supabase.table("usuarios").insert({"email": email, "senha_hash": hash_s}).execute()
            self.criar_tela_login()
        except Exception as e:
            print(f"DEBUG CADASTRO: {e}")
            self.lbl_status_cadastro.setText("Erro de conexão.")

    def criar_tela_recuperacao(self):
        self.limpar_card()
        layout = self.criar_layout_secundario()
        lbl_titulo = QLabel("Recuperação"); lbl_titulo.setObjectName("titulo_tela")
        self.txt_email_rec = QLineEdit(); self.txt_email_rec.setPlaceholderText("E-mail cadastrado")
        btn_env = BotaoAcessivel("Enviar Código"); btn_env.setObjectName("btn_entrar"); btn_env.clicked.connect(self.enviar_codigo_email)
        btn_voltar = BotaoAcessivel("Voltar"); btn_voltar.setObjectName("btn_secundario"); btn_voltar.clicked.connect(self.criar_tela_login)
        self.lbl_status_recuperacao = QLabel(""); self.lbl_status_recuperacao.setObjectName("status_msg")
        for w in [lbl_titulo, self.txt_email_rec, btn_env, btn_voltar, self.lbl_status_recuperacao]:
            layout.addWidget(w)
        self.tela_atual = "recuperacao"
        self.botao_acao_atual = btn_env
        self.botao_voltar_atual = btn_voltar
        self.configurar_navegacao([self.txt_email_rec], [btn_env, btn_voltar])

    def enviar_codigo_email(self):
        self.email_recuperando = self.txt_email_rec.text().strip()

        if not self.email_recuperando:
            self.lbl_status_recuperacao.setText("Informe seu e-mail.")
            self.txt_email_rec.setFocus()
            return

        try:
            resposta = (
                self.supabase.table("usuarios")
                .select("id")
                .eq("email", self.email_recuperando)
                .limit(1)
                .execute()
            )
        except Exception as e:
            print(f"DEBUG RECUPERACAO: {e}")
            self.lbl_status_recuperacao.setText("Erro de conexão. Tente novamente.")
            return

        if not resposta.data:
            self.lbl_status_recuperacao.setText("E-mail não encontrado.")
            self.txt_email_rec.setFocus()
            return

        self.codigo_verificacao = str(random.randint(100000, 999999))
        threading.Thread(target=self.disparar_email, args=(self.email_recuperando, self.codigo_verificacao), daemon=True).start()
        self.criar_tela_validar()

    def criar_tela_validar(self):
        self.limpar_card()
        layout = self.criar_layout_secundario()
        self.txt_cod = QLineEdit(); self.txt_cod.setPlaceholderText("Código recebido")
        btn_val = BotaoAcessivel("Validar"); btn_val.setObjectName("btn_entrar"); btn_val.clicked.connect(self.verificar_codigo)
        btn_voltar = BotaoAcessivel("Voltar"); btn_voltar.setObjectName("btn_secundario"); btn_voltar.clicked.connect(self.voltar_para_login)

        self.lbl_verificar_codigo = QLabel(""); self.lbl_verificar_codigo.setObjectName("status_msg")

        layout.addWidget(self.txt_cod)
        layout.addWidget(btn_val)
        layout.addWidget(btn_voltar)
        layout.addWidget(self.lbl_verificar_codigo, alignment=Qt.AlignCenter)
        self.tela_atual = "validacao"
        self.botao_acao_atual = btn_val
        self.botao_voltar_atual = btn_voltar
        self.configurar_navegacao([self.txt_cod], [btn_val, btn_voltar])

    def verificar_codigo(self):
        if self.txt_cod.text().strip() == self.codigo_verificacao: 
            self.criar_tela_nova_senha()
        else: 
            self.lbl_verificar_codigo.setText("Código incorreto!")

    def criar_tela_nova_senha(self):
        self.limpar_card()
        layout = self.criar_layout_secundario()
        self.txt_n_senha, self.btn_mostrar_nova_senha = self.criar_campo_senha(
            "Nova senha",
            "Nova senha",
            "A senha deve ter pelo menos 8 caracteres."
        )
        btn_upd = BotaoAcessivel("Atualizar Senha"); btn_upd.setObjectName("btn_entrar"); btn_upd.clicked.connect(self.atualizar_senha_supabase)
        btn_voltar = BotaoAcessivel("Voltar"); btn_voltar.setObjectName("btn_secundario"); btn_voltar.clicked.connect(self.voltar_para_login)

        self.lbl_atualizar_senha = QLabel(""); self.lbl_atualizar_senha.setObjectName("status_msg")

        self.linha_senha = self.criar_linha_senha(self.txt_n_senha, self.btn_mostrar_nova_senha)
        layout.addWidget(self.linha_senha)
        layout.addWidget(btn_upd)
        layout.addWidget(btn_voltar)
        layout.addWidget(self.lbl_atualizar_senha, alignment=Qt.AlignCenter)
        self.tela_atual = "nova_senha"
        self.botao_acao_atual = btn_upd
        self.botao_voltar_atual = btn_voltar
        self.atualizar_dimensoes_responsivas()
        self.configurar_navegacao([self.txt_n_senha, self.btn_mostrar_nova_senha], [btn_upd, btn_voltar])

    def criar_layout_secundario(self):
        container = QWidget(self.card_container)
        container.setObjectName("container_secundario")
        container.setMaximumWidth(460)
        container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 32, 0, 32)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignCenter)

        self.card_layout.addWidget(container, alignment=Qt.AlignCenter)
        return layout

    def atualizar_senha_supabase(self):
        try:
            hash_s = bcrypt.hashpw(self.txt_n_senha.text().strip().encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            self.supabase.table("usuarios").update({"senha_hash": hash_s}).eq("email", self.email_recuperando).execute()
            self.criar_tela_login()
        except Exception as e:
            print(f"DEBUG ATUALIZAR: {e}")
            self.lbl_atualizar_senha.setText("Erro ao atualizar.")

    def disparar_email(self, dest, cod):
        try:
            msg = MIMEMultipart()
            msg['Subject'] = "V-Inc - Código"
            msg['From'] = EMAIL_REMETENTE
            msg['To'] = dest
            msg.attach(MIMEText(f"Seu código: {cod}", 'plain'))
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(EMAIL_REMETENTE, SENHA_REMETENTE)
            server.sendmail(EMAIL_REMETENTE, dest, msg.as_string())
            server.quit()
        except Exception as e:
            print(f"DEBUG EMAIL: {e}")
