import tkinter as tk
import customtkinter as ctk
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import threading
import random
import bcrypt
import subprocess
import sys
import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# ==========================================
# CONFIGURAÇÃO DO SUPABASE (BANCO NA NUVEM)
# ==========================================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

try:
    if SUPABASE_URL and SUPABASE_KEY:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    else:
        print("[ERRO] Variáveis do Supabase não encontradas no arquivo .env")
except Exception as e:
    print(f"[ERRO] Falha ao conectar ao Supabase: {e}")

# ==========================================
# CONFIGURAÇÃO DE E-MAIL REAL (SMTP GMAIL)
# ==========================================
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_REMETENTE = os.getenv("EMAIL_REMETENTE")  
SENHA_REMETENTE = os.getenv("SENHA_REMETENTE")         

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class VincLoginApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("V-Inc - Acesso Seguro")
        self.geometry("620x700")  
        self.resizable(False, False)
        
        # Cores predominantes em azul
        self.cor_primaria = "#60A5FA"
        self.cor_secundaria = "#3B82F6"
        self.cor_acento = "#93C5FD"
        
        self.codigo_recuperacao = None
        self.email_recuperando = None

        self.criar_tela_login()

    def limpar_tela(self):
        for widget in self.winfo_children():
            widget.destroy()

    def criar_frame_central(self, parent):
        frame = ctk.CTkFrame(parent, fg_color="#1E2937", corner_radius=20, border_width=2, border_color="#334155")
        frame.pack(expand=True, fill="both", padx=40, pady=30)
        return frame

    def criar_tela_login(self):
        self.limpar_tela()
        self.geometry("620x700")

        main_frame = self.criar_frame_central(self)

        # Logo + Título
        lbl_logo = ctk.CTkLabel(main_frame, text="👁", font=("Arial", 78))
        lbl_logo.pack(pady=(45, 8))

        lbl_titulo = ctk.CTkLabel(main_frame, text="V-Inc", 
                                  font=("Arial", 36, "bold"), 
                                  text_color=self.cor_acento)
        lbl_titulo.pack(pady=(0, 4))

        lbl_subtitulo = ctk.CTkLabel(main_frame, text="Voz Inclusiva", 
                                     font=("Arial", 16, "italic"), 
                                     text_color="#94A3B8")
        lbl_subtitulo.pack(pady=(0, 45))

        entry_width = 380

        self.txt_email = ctk.CTkEntry(main_frame, 
                                      placeholder_text="Digite seu e-mail",
                                      width=entry_width, 
                                      height=54,
                                      font=("Arial", 14),
                                      border_color="#475569",
                                      fg_color="#0F172A")
        self.txt_email.pack(pady=12)

        self.txt_senha = ctk.CTkEntry(main_frame, 
                                      placeholder_text="Digite sua senha",
                                      show="*", 
                                      width=entry_width, 
                                      height=54,
                                      font=("Arial", 14),
                                      border_color="#475569",
                                      fg_color="#0F172A")
        self.txt_senha.pack(pady=12)

        self.lbl_status = ctk.CTkLabel(main_frame, text="", font=("Arial", 13))
        self.lbl_status.pack(pady=(8, 16))

        # Botão Entrar
        btn_entrar = ctk.CTkButton(main_frame, 
                                   text="Entrar", 
                                   font=("Arial", 16, "bold"), 
                                   width=entry_width, 
                                   height=54,
                                   fg_color=self.cor_primaria, 
                                   text_color="#0F172A",
                                   hover_color=self.cor_secundaria,
                                   corner_radius=12,
                                   command=self.acao_login)
        btn_entrar.pack(pady=(0, 20))

        # Botão Criar conta
        btn_ir_cadastro = ctk.CTkButton(main_frame, 
                                        text="Criar nova conta", 
                                        font=("Arial", 14), 
                                        width=entry_width, 
                                        height=48,
                                        fg_color="transparent", 
                                        border_width=2,
                                        border_color="#475569",
                                        text_color="#E2E8F0",
                                        hover_color="#334155",
                                        command=self.criar_tela_cadastro)
        btn_ir_cadastro.pack(pady=(0, 24))

        # Link Esqueci senha
        btn_esqueci = ctk.CTkButton(main_frame, 
                                    text="Esqueci minha senha",
                                    font=("Arial", 14, "underline"), 
                                    fg_color="transparent", 
                                    text_color=self.cor_acento,
                                    hover_color="#1E2937",
                                    width=entry_width,
                                    height=40,
                                    command=self.criar_tela_recuperacao)
        btn_esqueci.pack(pady=4)

        lbl_ajuda = ctk.CTkLabel(main_frame, text="Será enviado um código para seu e-mail", 
                                 font=("Arial", 12), text_color="#64748B")
        lbl_ajuda.pack(pady=(2, 20))

    def acao_login(self):
        email = self.txt_email.get().strip()
        senha = self.txt_senha.get().strip()

        if not email or not senha:
            self.lbl_status.configure(text="Preencha todos os campos.", text_color="#F87171")
            return

        try:
            resposta = supabase.table("usuarios").select("senha_hash").eq("email", email).execute()
            dados = resposta.data

            if dados:
                senha_hash_salva = dados[0]["senha_hash"].encode('utf-8')
                if bcrypt.checkpw(senha.encode('utf-8'), senha_hash_salva):
                    self.lbl_status.configure(text="Acesso concedido! Carregando...", text_color="#4ADE80")
                    self.after(800, self.iniciar_assistente_voz)
                    return
            
            self.lbl_status.configure(text="E-mail ou senha incorretos.", text_color="#F87171")

        except Exception as e:
            self.lbl_status.configure(text="Erro de conexão com o banco de dados.", text_color="#F87171")
            print(f"[ERRO SUPABASE]: {e}")

    def criar_tela_cadastro(self):
        self.limpar_tela()
        self.geometry("620x700")
        main_frame = self.criar_frame_central(self)

        lbl_logo = ctk.CTkLabel(main_frame, text="📝", font=("Arial", 58))
        lbl_logo.pack(pady=(35, 15))

        lbl_titulo = ctk.CTkLabel(main_frame, text="Criar Conta", 
                                  font=("Arial", 28, "bold"), text_color=self.cor_acento)
        lbl_titulo.pack(pady=(0, 6))

        lbl_desc = ctk.CTkLabel(main_frame, text="Cadastre-se para acessar o V-Inc", 
                                font=("Arial", 14), text_color="#94A3B8")
        lbl_desc.pack(pady=(0, 30))

        entry_width = 380

        self.txt_novo_email = ctk.CTkEntry(main_frame, placeholder_text="Seu melhor e-mail", width=entry_width, height=54, font=("Arial", 14))
        self.txt_novo_email.pack(pady=12)

        self.txt_nova_senha = ctk.CTkEntry(main_frame, placeholder_text="Senha segura", show="*", width=entry_width, height=54, font=("Arial", 14))
        self.txt_nova_senha.pack(pady=12)

        self.lbl_status_cadastro = ctk.CTkLabel(main_frame, text="", font=("Arial", 13))
        self.lbl_status_cadastro.pack(pady=10)

        btn_salvar = ctk.CTkButton(main_frame, text="Criar Conta", font=("Arial", 16, "bold"), width=entry_width, height=54,
                                   fg_color="#4ADE80", text_color="#0F172A", hover_color="#22C55E", corner_radius=12,
                                   command=self.acao_cadastrar)
        btn_salvar.pack(pady=(20, 12))

        btn_voltar = ctk.CTkButton(main_frame, text="Voltar ao Login", font=("Arial", 14), fg_color="transparent", 
                                   text_color="#CBD5E1", hover_color="#334155", width=entry_width, height=40,
                                   command=self.criar_tela_login)
        btn_voltar.pack()

    def acao_cadastrar(self):
        novo_email = self.txt_novo_email.get().strip()
        nova_senha = self.txt_nova_senha.get().strip()

        if not novo_email or not nova_senha:
            self.lbl_status_cadastro.configure(text="Por favor, preencha todos os campos.", text_color="#F87171")
            return

        if "@" not in novo_email or "." not in novo_email:
            self.lbl_status_cadastro.configure(text="Formato de e-mail inválido.", text_color="#F87171")
            return

        try:
            checagem = supabase.table("usuarios").select("email").eq("email", novo_email).execute()
            if checagem.data:
                self.lbl_status_cadastro.configure(text="Este e-mail já está cadastrado.", text_color="#F87171")
                return

            senha_criptografada = bcrypt.hashpw(nova_senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            supabase.table("usuarios").insert({"email": novo_email, "senha_hash": senha_criptografada}).execute()

            self.lbl_status_cadastro.configure(text="Conta criada com sucesso!", text_color="#4ADE80")
            self.after(1800, self.criar_tela_login)

        except Exception as e:
            self.lbl_status_cadastro.configure(text="Erro ao salvar no servidor.", text_color="#F87171")
            print(f"[ERRO SUPABASE]: {e}")

    def iniciar_assistente_voz(self):
        """Inicia a tela de carregamento após login bem-sucedido"""
        print("\n[SISTEMA] Login efetuado com sucesso! Abrindo tela de carregamento...")
        
        self.withdraw()  # Esconde a janela de login
        
        try:
            # Importa dinamicamente a tela de loading
            from loading import LoadingScreen
            
            # Cria e executa a tela de carregamento
            loading_screen = LoadingScreen()
            loading_screen.mainloop()
            
        except ImportError:
            print("[ERRO] Arquivo 'loading.py' não encontrado. Tentando abrir assistente diretamente...")
            try:
                subprocess.run([sys.executable, "assistente.py"])
            except Exception as e:
                print(f"[ERRO] Não foi possível iniciar o assistente: {e}")
        except Exception as e:
            print(f"[ERRO] Falha ao iniciar tela de carregamento: {e}")
            # Fallback
            try:
                subprocess.run([sys.executable, "assistente.py"])
            except:
                pass

    # ====================== TELAS DE RECUPERAÇÃO ======================

    def criar_tela_recuperacao(self):
        self.limpar_tela()
        self.geometry("620x700")
        main_frame = self.criar_frame_central(self)

        lbl_logo = ctk.CTkLabel(main_frame, text="🔐", font=("Arial", 58))
        lbl_logo.pack(pady=(40, 15))

        lbl_titulo = ctk.CTkLabel(main_frame, text="Recuperar Senha", font=("Arial", 26, "bold"), text_color=self.cor_acento)
        lbl_titulo.pack(pady=8)

        lbl_desc = ctk.CTkLabel(main_frame, text="Digite seu e-mail para receber o código de verificação", 
                                font=("Arial", 14), text_color="#94A3B8", wraplength=420)
        lbl_desc.pack(pady=(0, 30))

        self.txt_email_recup = ctk.CTkEntry(main_frame, placeholder_text="E-mail cadastrado", width=380, height=54, font=("Arial", 14))
        self.txt_email_recup.pack(pady=12)

        self.lbl_status_recup = ctk.CTkLabel(main_frame, text="", font=("Arial", 13))
        self.lbl_status_recup.pack(pady=12)

        self.btn_enviar_codigo = ctk.CTkButton(main_frame, text="Enviar Código", font=("Arial", 15, "bold"), 
                                               width=380, height=54, fg_color=self.cor_primaria, text_color="#0F172A",
                                               hover_color=self.cor_secundaria, corner_radius=12,
                                               command=self.enviar_email_recuperacao)
        self.btn_enviar_codigo.pack(pady=20)

        btn_voltar = ctk.CTkButton(main_frame, text="Voltar ao Login", font=("Arial", 14), fg_color="transparent", 
                                   text_color="#CBD5E1", hover_color="#334155", width=200, command=self.criar_tela_login)
        btn_voltar.pack()

    def enviar_email_recuperacao(self):
        email_destino = self.txt_email_recup.get().strip()
        if not email_destino:
            self.lbl_status_recup.configure(text="Por favor, introduza um e-mail válido.", text_color="#F87171")
            return

        try:
            checagem = supabase.table("usuarios").select("email").eq("email", email_destino).execute()
            if not checagem.data:
                self.lbl_status_recup.configure(text="Este e-mail não está cadastrado.", text_color="#F87171")
                return

            self.lbl_status_recup.configure(text="Enviando código...", text_color="#FACC15")
            self.btn_enviar_codigo.configure(state="disabled")

            self.email_recuperando = email_destino
            self.codigo_recuperacao = str(random.randint(100000, 999999))

            threading.Thread(target=self.disparar_email_background, 
                           args=(email_destino, self.codigo_recuperacao), daemon=True).start()

        except Exception as e:
            print(f"[ERRO SUPABASE]: {e}")

    def disparar_email_background(self, email_destino, codigo):
        if not EMAIL_REMETENTE or not SENHA_REMETENTE:
            self.after(0, self.erro_envio_email)
            return

        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = "V-Inc - Código de Recuperação de Senha"
            msg['From'] = EMAIL_REMETENTE
            msg['To'] = email_destino

            html_conteudo = f"""
            <html><body style="background:#0F172A;margin:0;padding:40px 0;font-family:Arial,sans-serif;">
                <table align="center" width="100%" style="max-width:500px;background:#1E2937;border-radius:16px;padding:40px;">
                    <tr><td align="center" style="padding-bottom:20px;">
                        <div style="width:70px;height:70px;background:linear-gradient(135deg,#60A5FA,#3B82F6);border-radius:50%;font-size:36px;display:flex;align-items:center;justify-content:center;">👁</div>
                    </td></tr>
                    <tr><td align="center"><h1 style="color:#E0F2FE;font-size:32px;margin:0;">V-Inc</h1></td></tr>
                    <tr><td align="center" style="padding:30px 0 20px;">
                        <div style="background:#0F172A;padding:20px 40px;border-radius:12px;font-size:42px;letter-spacing:8px;font-weight:bold;color:#60A5FA;font-family:monospace;">{codigo}</div>
                    </td></tr>
                </table>
            </body></html>
            """
            msg.attach(MIMEText(html_conteudo, 'html'))

            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.ehlo(); server.starttls(); server.ehlo()
            server.login(EMAIL_REMETENTE, SENHA_REMETENTE)
            server.sendmail(EMAIL_REMETENTE, email_destino, msg.as_string())
            server.quit()

            self.after(0, self.sucesso_envio_email)
        except Exception as e:
            print(f"[ERRO EMAIL]: {e}")
            self.after(0, self.erro_envio_email)

    def sucesso_envio_email(self):
        self.btn_enviar_codigo.configure(state="normal")
        self.lbl_status_recup.configure(text="Código enviado com sucesso!", text_color="#4ADE80")
        self.after(2000, self.criar_tela_validacao_codigo)

    def erro_envio_email(self):
        self.btn_enviar_codigo.configure(state="normal")
        self.lbl_status_recup.configure(text="Falha ao enviar. Verifique sua conexão.", text_color="#F87171")

    def criar_tela_validacao_codigo(self):
        self.limpar_tela()
        self.geometry("620x700")
        main_frame = self.criar_frame_central(self)

        lbl_logo = ctk.CTkLabel(main_frame, text="🔑", font=("Arial", 58))
        lbl_logo.pack(pady=(40, 15))

        lbl_titulo = ctk.CTkLabel(main_frame, text="Verificar Código", font=("Arial", 26, "bold"), text_color=self.cor_acento)
        lbl_titulo.pack(pady=8)

        lbl_desc = ctk.CTkLabel(main_frame, text="Digite o código de 6 dígitos", font=("Arial", 14), text_color="#94A3B8")
        lbl_desc.pack(pady=(0, 25))

        self.txt_codigo_inserido = ctk.CTkEntry(main_frame, placeholder_text="000000", width=300, height=60,
                                                font=("Arial", 22, "bold"), justify="center")
        self.txt_codigo_inserido.pack(pady=15)

        self.lbl_status_codigo = ctk.CTkLabel(main_frame, text="", font=("Arial", 13))
        self.lbl_status_codigo.pack(pady=10)

        btn_verificar = ctk.CTkButton(main_frame, text="Verificar Código", font=("Arial", 15, "bold"), 
                                      width=380, height=54, fg_color=self.cor_primaria, text_color="#0F172A",
                                      hover_color=self.cor_secundaria, corner_radius=12,
                                      command=self.validar_codigo_recuperacao)
        btn_verificar.pack(pady=20)

    def validar_codigo_recuperacao(self):
        if self.txt_codigo_inserido.get().strip() == self.codigo_recuperacao and self.email_recuperando:
            self.lbl_status_codigo.configure(text="Código validado!", text_color="#4ADE80")
            self.after(1000, self.criar_tela_nova_senha)
        else:
            self.lbl_status_codigo.configure(text="Código incorreto.", text_color="#F87171")

    def criar_tela_nova_senha(self):
        self.limpar_tela()
        self.geometry("620x700")
        main_frame = self.criar_frame_central(self)

        lbl_logo = ctk.CTkLabel(main_frame, text="🔄", font=("Arial", 58))
        lbl_logo.pack(pady=(40, 15))

        lbl_titulo = ctk.CTkLabel(main_frame, text="Nova Senha", font=("Arial", 26, "bold"), text_color=self.cor_acento)
        lbl_titulo.pack(pady=8)

        self.txt_nova_senha_recup = ctk.CTkEntry(main_frame, placeholder_text="Nova senha", show="*", width=380, height=54, font=("Arial", 14))
        self.txt_nova_senha_recup.pack(pady=12)

        self.txt_confirma_senha_recup = ctk.CTkEntry(main_frame, placeholder_text="Confirme a senha", show="*", width=380, height=54, font=("Arial", 14))
        self.txt_confirma_senha_recup.pack(pady=12)

        self.lbl_status_nova_senha = ctk.CTkLabel(main_frame, text="", font=("Arial", 13))
        self.lbl_status_nova_senha.pack(pady=12)

        btn_salvar = ctk.CTkButton(main_frame, text="Salvar Nova Senha", font=("Arial", 15, "bold"), width=380, height=54,
                                   fg_color="#4ADE80", text_color="#0F172A", hover_color="#22C55E", corner_radius=12,
                                   command=self.acao_atualizar_senha)
        btn_salvar.pack(pady=25)

    def acao_atualizar_senha(self):
        nova_senha = self.txt_nova_senha_recup.get().strip()
        confirma = self.txt_confirma_senha_recup.get().strip()

        if not nova_senha or not confirma:
            self.lbl_status_nova_senha.configure(text="Preencha ambos os campos.", text_color="#F87171")
            return
        if nova_senha != confirma:
            self.lbl_status_nova_senha.configure(text="As senhas não coincidem.", text_color="#F87171")
            return

        try:
            nova_hash = bcrypt.hashpw(nova_senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            supabase.table("usuarios").update({"senha_hash": nova_hash}).eq("email", self.email_recuperando).execute()
            self.lbl_status_nova_senha.configure(text="Senha atualizada com sucesso!", text_color="#4ADE80")
            self.after(2200, self.criar_tela_login)
        except Exception as e:
            self.lbl_status_nova_senha.configure(text="Erro ao atualizar senha.", text_color="#F87171")
            print(f"[ERRO]: {e}")


# ==========================================
if __name__ == "__main__":
    app = VincLoginApp()
    app.mainloop()