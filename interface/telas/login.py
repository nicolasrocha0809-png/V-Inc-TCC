import sys, random, bcrypt, os, threading
from pathlib import Path
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFrame
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from interface.prefs_manager import PrefsManager

EMAIL_REMETENTE, SENHA_REMETENTE = os.getenv("EMAIL_REMETENTE"), os.getenv("SENHA_REMETENTE")

class LoginScreen(QWidget):
    def __init__(self, supabase_client, callback_sucesso, parent=None):
        super().__init__(parent)
        self.callback_sucesso = callback_sucesso
        self.supabase = supabase_client
        self.codigo_verificacao = None
        self.email_recuperando = None

        # Estiliza O FUNDO DA TELA INTEIRA (troque #1e222d pela sua cor desejada em hex)
        self.setStyleSheet("""
            LoginScreen {
                background-color: #1e222d;
            }
        """)

        # O layout principal agora é HORIZONTAL e ocupa 100% da tela
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(60, 40, 60, 40) # Margens nas bordas da tela
        self.main_layout.setSpacing(40)

        self.criar_tela_login()

    def limpar_card(self):
        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._limpar_sub_layout(item.layout())

    def _limpar_sub_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._limpar_sub_layout(item.layout())

    def criar_tela_login(self):
        self.limpar_card()

        # --- COLUNA 1: ESQUERDA (Marca e Boas-vindas) ---
        col_esquerda = QVBoxLayout()
        col_esquerda.setAlignment(Qt.AlignCenter)

        self.lbl_titulo = QLabel("V-Inc"); self.lbl_titulo.setObjectName("titulo_login")
        self.lbl_logo = QLabel(); self.lbl_logo.setObjectName("logo_login")
        logo_path = Path(__file__).resolve().parents[2] / "essa.png"
        self.lbl_logo.setPixmap(QPixmap(str(logo_path)).scaled(
            400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation
        ))
        self.lbl_sub = QLabel("Voz Inclusiva"); self.lbl_sub.setObjectName("subtitulo_login")

        col_esquerda.addWidget(self.lbl_titulo, alignment=Qt.AlignCenter)
        col_esquerda.addWidget(self.lbl_logo, alignment=Qt.AlignCenter)
        col_esquerda.addWidget(self.lbl_sub, alignment=Qt.AlignCenter)

        # --- COLUNA 2: DIREITA (Formulário) ---
        col_direita = QVBoxLayout()
        col_direita.setAlignment(Qt.AlignCenter)
        col_direita.setSpacing(10)

        self.lbl_e = QLabel("Email de Acesso"); self.lbl_e.setObjectName("label_input")
        self.txt_email = QLineEdit(); self.txt_email.setPlaceholderText("nome@exemplo.com")
        self.lbl_s = QLabel("Senha"); self.lbl_s.setObjectName("label_input")
        self.txt_senha = QLineEdit(); self.txt_senha.setPlaceholderText("********"); self.txt_senha.setEchoMode(QLineEdit.Password)

        # Limita a largura dos inputs para não ficarem gigantes em telas muito largas
        for input_field in [self.txt_email, self.txt_senha]:
            input_field.setMaximumWidth(380)

        self.btn_entrar = QPushButton("Entrar →"); self.btn_entrar.setObjectName("btn_entrar")
        self.btn_entrar.setMaximumWidth(380)
        self.btn_entrar.clicked.connect(self.acao_login)

        self.btn_cad = QPushButton("Criar nova conta"); self.btn_cad.setObjectName("btn_secundario")
        self.btn_cad.setMaximumWidth(380)
        self.btn_cad.clicked.connect(self.criar_tela_cadastro)

        self.btn_rec = QPushButton("Esqueci minha senha"); self.btn_rec.setObjectName("btn_link")
        self.btn_rec.clicked.connect(self.criar_tela_recuperacao)

        self.lbl_status = QLabel(""); self.lbl_status.setObjectName("status_msg")

        # Adiciona os elementos no layout da direita
        for w in [self.lbl_e, self.txt_email, self.lbl_s, self.txt_senha, self.btn_entrar, self.btn_cad]:
            col_direita.addWidget(w)

        col_direita.addWidget(self.btn_rec, alignment=Qt.AlignCenter)
        col_direita.addWidget(self.lbl_status, alignment=Qt.AlignCenter)

        # Adiciona as duas colunas diretamente no layout principal da janela
        self.main_layout.addLayout(col_esquerda, stretch=1)
        self.main_layout.addLayout(col_direita, stretch=1)

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
        lbl_titulo = QLabel("Criar Conta"); lbl_titulo.setObjectName("titulo_tela")
        self.txt_n_email = QLineEdit(); self.txt_n_email.setPlaceholderText("E-mail")
        self.txt_n_senha = QLineEdit(); self.txt_n_senha.setPlaceholderText("Senha"); self.txt_n_senha.setEchoMode(QLineEdit.Password)
        btn_salvar = QPushButton("Criar Conta"); btn_salvar.setObjectName("btn_entrar"); btn_salvar.clicked.connect(self.acao_cadastrar)
        btn_voltar = QPushButton("Voltar"); btn_voltar.setObjectName("btn_secundario"); btn_voltar.clicked.connect(self.criar_tela_login)

        self.lbl_status_cadastro = QLabel(""); self.lbl_status_cadastro.setObjectName("status_msg")

        for w in [lbl_titulo, self.txt_n_email, self.txt_n_senha, btn_salvar, btn_voltar, self.lbl_status_cadastro]: 
            self.card_layout.addWidget(w)

    def acao_cadastrar(self):
        email, senha = self.txt_n_email.text().strip(), self.txt_n_senha.text().strip()
        if not email or not senha:
            self.lbl_status_cadastro.setText("Preencha todos os campos.")
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
        lbl_titulo = QLabel("Recuperação"); lbl_titulo.setObjectName("titulo_tela")
        self.txt_email_rec = QLineEdit(); self.txt_email_rec.setPlaceholderText("E-mail cadastrado")
        btn_env = QPushButton("Enviar Código"); btn_env.setObjectName("btn_entrar"); btn_env.clicked.connect(self.enviar_codigo_email)
        btn_voltar = QPushButton("Voltar"); btn_voltar.setObjectName("btn_secundario"); btn_voltar.clicked.connect(self.criar_tela_login)
        for w in [lbl_titulo, self.txt_email_rec, btn_env, btn_voltar]: self.card_layout.addWidget(w)

    def enviar_codigo_email(self):
        self.email_recuperando = self.txt_email_rec.text().strip()
        self.codigo_verificacao = str(random.randint(100000, 999999))
        threading.Thread(target=self.disparar_email, args=(self.email_recuperando, self.codigo_verificacao), daemon=True).start()
        self.criar_tela_validar()

    def criar_tela_validar(self):
        self.limpar_card()
        self.txt_cod = QLineEdit(); self.txt_cod.setPlaceholderText("Código recebido")
        btn_val = QPushButton("Validar"); btn_val.setObjectName("btn_entrar"); btn_val.clicked.connect(self.verificar_codigo)
        
        self.lbl_verificar_codigo = QLabel(""); self.lbl_verificar_codigo.setObjectName("status_msg")
        
        self.card_layout.addWidget(self.txt_cod)
        self.card_layout.addWidget(btn_val)
        self.card_layout.addWidget(self.lbl_verificar_codigo, alignment=Qt.AlignCenter)

    def verificar_codigo(self):
        if self.txt_cod.text().strip() == self.codigo_verificacao: 
            self.criar_tela_nova_senha()
        else: 
            self.lbl_verificar_codigo.setText("Código incorreto!")

    def criar_tela_nova_senha(self):
        self.limpar_card()
        self.txt_n_senha = QLineEdit(); self.txt_n_senha.setPlaceholderText("Nova senha"); self.txt_n_senha.setEchoMode(QLineEdit.Password)
        btn_upd = QPushButton("Atualizar Senha"); btn_upd.setObjectName("btn_entrar"); btn_upd.clicked.connect(self.atualizar_senha_supabase)
        
        self.lbl_atualizar_senha = QLabel(""); self.lbl_atualizar_senha.setObjectName("status_msg")
        
        self.card_layout.addWidget(self.txt_n_senha)
        self.card_layout.addWidget(btn_upd)
        self.card_layout.addWidget(self.lbl_atualizar_senha, alignment=Qt.AlignCenter)

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
