import tkinter as tk
import customtkinter as ctk
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import threading
import random
import bcrypt

# ==========================================
# CONFIGURAÇÃO DE CONFIGURAÇÃO DE E-MAIL REAL (SMTP GMAIL)
# ==========================================
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_REMETENTE = "."  # <- Coloque seu e-mail do Gmail aqui
SENHA_REMETENTE = "."         # <- Coloque sua Senha de App de 16 dígitos aqui

# Configurações globais do CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class VincLoginApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("V-Inc - Acesso Seguro")
        self.geometry("550x500")
        self.resizable(False, False)

        # Banco de dados simulado (básico para demonstração de TCC)
        self.usuario_db = "admin@vinc.com"
        # Senha padrão criptografada: 'admin123'
        self.senha_hash_db = bcrypt.hashpw(b"admin123", bcrypt.gensalt())
        self.codigo_recuperacao = None

        self.criar_tela_login()

    def limpar_tela(self):
        for widget in self.winfo_children():
            widget.destroy()

    def criar_tela_login(self):
        self.limpar_tela()

        # Título / Identidade do Sistema
        lbl_logo = ctk.CTkLabel(self, text="👁", font=("Arial", 50))
        lbl_logo.pack(pady=(40, 5))

        lbl_titulo = ctk.CTkLabel(self, text="V-Inc", font=("Arial", 28, "bold"), text_color="#B3E5FC")
        lbl_titulo.pack(pady=(0, 5))

        lbl_subtitulo = ctk.CTkLabel(self, text="Assistente Virtual & Acesso Seguro", font=("Arial", 12), text_color="#888888")
        lbl_subtitulo.pack(pady=(0, 30))

        # Campo de E-mail
        self.txt_email = ctk.CTkEntry(self, placeholder_text="Digite seu e-mail (ex: usuario@gmail.com)", width=400, height=45)
        self.txt_email.pack(pady=10)

        # Campo de Senha
        self.txt_senha = ctk.CTkEntry(self, placeholder_text="Digite sua senha", show="*", width=400, height=45)
        self.txt_senha.pack(pady=10)

        # Label de Mensagem de Erro/Sucesso
        self.lbl_status = ctk.CTkLabel(self, text="", font=("Arial", 12))
        self.lbl_status.pack(pady=5)

        # Botão Entrar
        btn_entrar = ctk.CTkButton(self, text="Entrar →", font=("Arial", 16, "bold"), width=400, height=45, fg_color="#B3E5FC", text_color="#000000", hover_color="#81D4FA", command=self.acao_login)
        btn_entrar.pack(pady=(10, 15))

        # Link Esqueci a Senha
        btn_esqueci = ctk.CTkButton(self, text="Esqueci a minha senha", font=("Arial", 12, "underline"), fg_color="transparent", hover_color="#263238", text_color="#B3E5FC", width=150, command=self.criar_tela_recuperacao)
        btn_esqueci.pack()

    def acao_login(self):
        email = self.txt_email.get().strip()
        senha = self.txt_senha.get().strip()

        if not email or not senha:
            self.lbl_status.configure(text="Preencha todos os campos obrigatórios.", text_color="#FF5252")
            return

        if email == self.usuario_db and bcrypt.checkpw(senha.encode('utf-8'), self.senha_hash_db):
            self.lbl_status.configure(text="Acesso concedido! Iniciando V-Inc...", text_color="#69F0AE")
            self.after(1500, self.iniciar_assistente_voz)
        else:
            self.lbl_status.configure(text="E-mail ou senha incorretos.", text_color="#FF5252")

    def iniciar_assistente_voz(self):
        self.limpar_tela()
        lbl_sucesso = ctk.CTkLabel(self, text=" V-Inc Ativo", font=("Arial", 24, "bold"), text_color="#B3E5FC")
        lbl_sucesso.pack(pady=100)
        lbl_info = ctk.CTkLabel(self, text="O assistente de voz está operando em segundo plano.\n[Dispositivo Infinix Hot 40i conectado]", font=("Arial", 14), text_color="#CCCCCC")
        lbl_info.pack(pady=10)
        
        # Aqui entra a chamada para o script teste_voz.py
        print("[SISTEMA] Assistente de voz carregado com sucesso.")

    def criar_tela_recuperacao(self):
        self.limpar_tela()

        lbl_logo = ctk.CTkLabel(self, text="🔐", font=("Arial", 40))
        lbl_logo.pack(pady=(50, 10))

        lbl_titulo = ctk.CTkLabel(self, text="Recuperação de Acesso", font=("Arial", 22, "bold"), text_color="#B3E5FC")
        lbl_titulo.pack(pady=5)

        lbl_desc = ctk.CTkLabel(self, text="Introduza o seu e-mail para receber o código de verificação:", font=("Arial", 12), text_color="#CCCCCC")
        lbl_desc.pack(pady=(0, 20))

        self.txt_email_recup = ctk.CTkEntry(self, placeholder_text="Seu e-mail cadastrado", width=400, height=45)
        self.txt_email_recup.pack(pady=10)

        self.lbl_status_recup = ctk.CTkLabel(self, text="", font=("Arial", 12))
        self.lbl_status_recup.pack(pady=5)

        self.btn_enviar_codigo = ctk.CTkButton(self, text="Enviar Código de Verificação", font=("Arial", 14, "bold"), width=400, height=45, fg_color="#B3E5FC", text_color="#000000", hover_color="#81D4FA", command=self.enviar_email_recuperacao)
        self.btn_enviar_codigo.pack(pady=15)

        btn_voltar = ctk.CTkButton(self, text="← Voltar para o Login", font=("Arial", 12), fg_color="transparent", text_color="#FFFFFF", hover_color="#263238", command=self.criar_tela_login)
        btn_voltar.pack()

    def enviar_email_recuperacao(self):
        email_destino = self.txt_email_recup.get().strip()

        if not email_destino:
            self.lbl_status_recup.configure(text="Por favor, introduza um e-mail válido.", text_color="#FF5252")
            return

        self.lbl_status_recup.configure(text="A processar envio... Por favor, aguarde.", text_color="#FFD700")
        self.btn_enviar_codigo.configure(state="disabled")

        # Gerar código de 6 dígitos
        self.codigo_recuperacao = str(random.randint(100000, 999999))

        # Executar o envio por e-mail em uma thread para a interface não travar
        threading.Thread(target=self.disparar_email_background, args=(email_destino, self.codigo_recuperacao), daemon=True).start()

    def disparar_email_background(self, email_destino, codigo):
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = " V-Inc - Código de Recuperação de Senha"
            msg['From'] = EMAIL_REMETENTE
            msg['To'] = email_destino

            # Template HTML Profissional Escuro para a Banca do TCC
            html_conteudo = f"""
            <html>
            <body style="font-family: 'Arial', sans-serif; background-color: #121212; margin: 0; padding: 40px; color: #FFFFFF;">
                <div style="max-width: 500px; margin: 0 auto; background-color: #1A1A1A; border: 1px solid #333333; border-radius: 12px; padding: 30px; text-align: center; box-shadow: 0px 4px 15px rgba(0,0,0,0.5);">
                    <div style="background-color: #B3E5FC; width: 60px; height: 60px; border-radius: 50%; margin: 0 auto 20px auto; line-height: 60px; font-size: 32px; color: #000000;"></div>
                    <h2 style="color: #B3E5FC; margin-bottom: 5px; font-size: 26px;">V-Inc</h2>
                    <p style="color: #CCCCCC; font-size: 14px; margin-top: 0; margin-bottom: 25px;">Assistente Virtual & Acesso Seguro</p>
                    <hr style="border: 0; border-top: 1px solid #333333; margin-bottom: 25px;">
                    <p style="font-size: 16px; color: #E0E0E0; line-height: 1.5; text-align: left;">
                        Olá,<br><br>
                        Recebemos uma solicitação para redefinir a senha da sua conta no sistema <strong>V-Inc</strong>. Use o código de verificação abaixo para prosseguir:
                    </p>
                    <div style="background-color: #2A2A2A; border: 1px solid #B3E5FC; border-radius: 8px; padding: 15px; font-size: 32px; font-weight: bold; letter-spacing: 6px; color: #B3E5FC; margin: 30px 0; display: inline-block; padding-left: 20px; padding-right: 10px;">
                        {codigo}
                    </div>
                    <p style="font-size: 12px; color: #888888; line-height: 1.5; text-align: left; margin-top: 25px;">
                        * Este código é válido apenas para esta sessão. Se você não solicitou a alteração da sua senha, ignore este e-mail por segurança.
                    </p>
                    <hr style="border: 0; border-top: 1px solid #333333; margin-top: 30px; margin-bottom: 20px;">
                    <p style="font-size: 11px; color: #555555; margin: 0;">
                        V-Inc TCC &copy; 2026 - Todos os direitos reservados.
                    </p>
                </div>
            </body>
            </html>
            """
            msg.attach(MIMEText(html_conteudo, 'html'))

            # Conexão SMTP Segura com o Google TLS
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(EMAIL_REMETENTE, SENHA_REMETENTE)
            server.sendmail(EMAIL_REMETENTE, [email_destino], msg.as_string())
            server.quit()

            # Sucesso: Executa na thread principal da interface gráfica
            self.after(0, self.sucesso_envio_email)

        except Exception as e:
            print(f"\n[ERRO SCRIPT GMAIL] Detalhes do erro: {e}\n")
            # Erro: Executa na thread principal da interface gráfica
            self.after(0, self.erro_envio_email)

    def sucesso_envio_email(self):
        self.btn_enviar_codigo.configure(state="normal")
        self.lbl_status_recup.configure(text="Código enviado com sucesso! Verifique a sua caixa de entrada.", text_color="#69F0AE")
        self.after(2000, self.criar_tela_validacao_codigo)

    def erro_envio_email(self):
        self.btn_enviar_codigo.configure(state="normal")
        self.lbl_status_recup.configure(text="Falha ao enviar. Verifique as credenciais e a sua Senha de App.", text_color="#FF5252")

    def criar_tela_validacao_codigo(self):
        self.limpar_tela()

        lbl_logo = ctk.CTkLabel(self, text="🔑", font=("Arial", 40))
        lbl_logo.pack(pady=(50, 10))

        lbl_titulo = ctk.CTkLabel(self, text="Validar Código", font=("Arial", 22, "bold"), text_color="#B3E5FC")
        lbl_titulo.pack(pady=5)

        lbl_desc = ctk.CTkLabel(self, text="Introduza o código de 6 dígitos enviado por e-mail:", font=("Arial", 12), text_color="#CCCCCC")
        lbl_desc.pack(pady=(0, 20))

        self.txt_codigo_inserido = ctk.CTkEntry(self, placeholder_text="Código de 6 dígitos", width=400, height=45, justify="center")
        self.txt_codigo_inserido.pack(pady=10)

        self.lbl_status_codigo = ctk.CTkLabel(self, text="", font=("Arial", 12))
        self.lbl_status_codigo.pack(pady=5)

        btn_verificar = ctk.CTkButton(self, text="Verificar Código", font=("Arial", 14, "bold"), width=400, height=45, fg_color="#B3E5FC", text_color="#000000", hover_color="#81D4FA", command=self.validar_codigo_recuperacao)
        btn_verificar.pack(pady=15)

    def validar_codigo_recuperacao(self):
        codigo_digitado = self.txt_codigo_inserido.get().strip()

        if codigo_digitado == self.codigo_recuperacao:
            self.lbl_status_codigo.configure(text="Código válido! Nova senha temporária gerada: 'admin123'", text_color="#69F0AE")
            self.senha_hash_db = bcrypt.hashpw(b"admin123", bcrypt.gensalt())
            self.after(3000, self.criar_tela_login)
        else:
            self.lbl_status_codigo.configure(text="Código incorreto ou expirado. Tente novamente.", text_color="#FF5252")

if __name__ == "__main__":
    app = VincLoginApp()
    app.mainloop()
