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

# CONFIGURAÇÃO DO SUPABASE

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

# CONFIGURAÇÃO DE E-MAIL (GMAIL)

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

        self.geometry("550x620")  

        self.resizable(False, False)

        

        self.codigo_recuperacao = None

        self.email_recuperando = None



        self.criar_tela_login()



    def limpar_tela(self):

        for widget in self.winfo_children():

            widget.destroy()



    def criar_tela_login(self):

        self.limpar_tela()

        self.geometry("550x620")



        lbl_logo = ctk.CTkLabel(self, text="👁", font=("Arial", 50))

        lbl_logo.pack(pady=(30, 5))



        lbl_titulo = ctk.CTkLabel(self, text="V-Inc", font=("Arial", 28, "bold"), text_color="#B3E5FC")

        lbl_titulo.pack(pady=(0, 5))



        lbl_subtitulo = ctk.CTkLabel(self, text="Voz Inclusiva", font=("Arial", 14, "italic"), text_color="#888888")

        lbl_subtitulo.pack(pady=(0, 20))



        self.txt_email = ctk.CTkEntry(self, placeholder_text="Digite seu e-mail (ex: usuario@gmail.com)", width=400, height=45)

        self.txt_email.pack(pady=10)



        self.txt_senha = ctk.CTkEntry(self, placeholder_text="Digite sua senha", show="*", width=400, height=45)

        self.txt_senha.pack(pady=10)



        self.lbl_status = ctk.CTkLabel(self, text="", font=("Arial", 12))

        self.lbl_status.pack(pady=5)



        btn_entrar = ctk.CTkButton(self, text="Entrar →", font=("Arial", 16, "bold"), width=400, height=45, fg_color="#B3E5FC", text_color="#000000", hover_color="#81D4FA", command=self.acao_login)

        btn_entrar.pack(pady=10)



        btn_ir_cadastro = ctk.CTkButton(self, text="Não tem uma conta? Cadastre-se aqui", font=("Arial", 14, "bold"), width=400, height=45, fg_color="#1A237E", text_color="#FFFFFF", hover_color="#283593", command=self.criar_tela_cadastro)

        btn_ir_cadastro.pack(pady=10)



        btn_esqueci = ctk.CTkButton(self, text="Esqueci a minha senha", font=("Arial", 12, "underline"), fg_color="transparent", hover_color="#263238", text_color="#B3E5FC", width=150, command=self.criar_tela_recuperacao)

        btn_esqueci.pack(pady=5)



    # ... (mantive os outros métodos iguais até o envio de email)



    def acao_login(self):

        email = self.txt_email.get().strip()

        senha = self.txt_senha.get().strip()



        if not email or not senha:

            self.lbl_status.configure(text="Preencha todos os campos obrigatórios.", text_color="#FF5252")

            return



        try:

            resposta = supabase.table("usuarios").select("senha_hash").eq("email", email).execute()

            dados = resposta.data



            if dados:

                senha_hash_salva = dados[0]["senha_hash"].encode('utf-8')

                

                if bcrypt.checkpw(senha.encode('utf-8'), senha_hash_salva):

                    self.lbl_status.configure(text="Acesso concedido! Iniciando V-Inc...", text_color="#69F0AE")

                    self.after(1500, self.iniciar_assistente_voz)

                    return

            

            self.lbl_status.configure(text="E-mail ou senha incorretos.", text_color="#FF5252")



        except Exception as e:

            self.lbl_status.configure(text="Erro de conexão com o banco de dados.", text_color="#FF5252")

            print(f"[ERRO SUPABASE]: {e}")



    def criar_tela_cadastro(self):

        self.limpar_tela()

        self.geometry("550x620")



        lbl_logo = ctk.CTkLabel(self, text="📝", font=("Arial", 40))

        lbl_logo.pack(pady=(40, 5))



        lbl_titulo = ctk.CTkLabel(self, text="Criar Nova Conta", font=("Arial", 24, "bold"), text_color="#B3E5FC")

        lbl_titulo.pack(pady=5)



        lbl_desc = ctk.CTkLabel(self, text="Cadastre suas credenciais para acessar o V-Inc", font=("Arial", 12), text_color="#CCCCCC")

        lbl_desc.pack(pady=(0, 20))



        self.txt_novo_email = ctk.CTkEntry(self, placeholder_text="Digite o seu  e-mail", width=400, height=45)

        self.txt_novo_email.pack(pady=10)



        self.txt_nova_senha = ctk.CTkEntry(self, placeholder_text="Crie uma senha segura", show="*", width=400, height=45)

        self.txt_nova_senha.pack(pady=10)



        self.lbl_status_cadastro = ctk.CTkLabel(self, text="", font=("Arial", 12))

        self.lbl_status_cadastro.pack(pady=5)



        btn_salvar_cadastro = ctk.CTkButton(self, text="Concluir Cadastro ✓", font=("Arial", 15, "bold"), width=400, height=45, fg_color="#69F0AE", text_color="#000000", hover_color="#00E676", command=self.acao_cadastrar)

        btn_salvar_cadastro.pack(pady=15)



        btn_voltar = ctk.CTkButton(self, text="← Voltar para o Login", font=("Arial", 12), fg_color="transparent", text_color="#FFFFFF", hover_color="#263238", command=self.criar_tela_login)

        btn_voltar.pack()



    def acao_cadastrar(self):

        novo_email = self.txt_novo_email.get().strip()

        nova_senha = self.txt_nova_senha.get().strip()



        if not novo_email or not nova_senha:

            self.lbl_status_cadastro.configure(text="Por favor, preencha todos os campos.", text_color="#FF5252")

            return



        if "@" not in novo_email or "." not in novo_email:

            self.lbl_status_cadastro.configure(text="Formato de e-mail inválido.", text_color="#FF5252")

            return



        try:

            checagem = supabase.table("usuarios").select("email").eq("email", novo_email).execute()

            if checagem.data:

                self.lbl_status_cadastro.configure(text="Este e-mail já está cadastrado no sistema.", text_color="#FF5252")

                return



            senha_criptografada = bcrypt.hashpw(nova_senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

            

            supabase.table("usuarios").insert({"email": novo_email, "senha_hash": senha_criptografada}).execute()



            self.lbl_status_cadastro.configure(text="Conta criada com sucesso! Redirecionando...", text_color="#69F0AE")

            self.after(2000, self.criar_tela_login)



        except Exception as e:

            self.lbl_status_cadastro.configure(text="Erro ao salvar dados no servidor.", text_color="#FF5252")

            print(f"[ERRO SUPABASE]: {e}")



    def iniciar_assistente_voz(self):

        print("\n[SISTEMA] Login efetuado com sucesso!")

        self.withdraw() 

        self.quit()     

        

        try:

            subprocess.run([sys.executable, "teste_voz.py"])

        except Exception as e:

            print(f"\n[ERRO] Não foi possível iniciar o arquivo de voz: {e}")



    def criar_tela_recuperacao(self):

        self.limpar_tela()

        self.geometry("550x620")



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



        try:

            checagem = supabase.table("usuarios").select("email").eq("email", email_destino).execute()

            if not checagem.data:

                self.lbl_status_recup.configure(text="Este e-mail não está cadastrado no sistema.", text_color="#FF5252")

                return



            self.lbl_status_recup.configure(text="A processar envio... Por favor, aguarde.", text_color="#FFD700")

            self.btn_enviar_codigo.configure(state="disabled")



            self.email_recuperando = email_destino

            self.codigo_recuperacao = str(random.randint(100000, 999999))



            threading.Thread(target=self.disparar_email_background, args=(email_destino, self.codigo_recuperacao), daemon=True).start()



        except Exception as e:

            print(f"[ERRO SUPABASE]: {e}")



    # ====================== FUNÇÃO ATUALIZADA ======================

    def disparar_email_background(self, email_destino, codigo):

        if not EMAIL_REMETENTE or not SENHA_REMETENTE:

            print("[ERRO LOCAL] Credenciais de e-mail não configuradas no arquivo .env")

            self.after(0, self.erro_envio_email)

            return



        try:

            msg = MIMEMultipart('alternative')

            msg['Subject'] = "V-Inc - Código de Recuperação de Senha"

            msg['From'] = f"V-Inc - Voz Inclusiva <{EMAIL_REMETENTE}>"

            msg['To'] = email_destino

            msg['Reply-To'] = EMAIL_REMETENTE

            msg['X-Mailer'] = "V-Inc Application"

            msg['List-Unsubscribe'] = f"<mailto:{EMAIL_REMETENTE}?subject=Unsubscribe>"



            # Texto Plano (importante contra spam)

            texto_plano = f"""Olá,



Recebemos uma solicitação para redefinir a senha da sua conta no V-Inc.



Seu código de verificação é: {codigo}



Este código é válido por 15 minutos.



Atenciosamente,

Equipe V-Inc - Voz Inclusiva

"""



            # HTML Melhorado

            html_conteudo = f"""

            <html>

            <body style="background-color: #f4f4f4; margin: 0; padding: 30px 0; font-family: Arial, sans-serif;">

                <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 520px;">

                    <tr>

                        <td style="background-color: #121212; padding: 35px 20px; text-align: center; border-radius: 12px 12px 0 0;">

                            <h1 style="color: #B3E5FC; margin: 0; font-size: 28px;">V-Inc</h1>

                            <p style="color: #777777; margin: 8px 0 0 0;">Voz Inclusiva</p>

                        </td>

                    </tr>

                    <tr>

                        <td style="background-color: #ffffff; padding: 40px 35px; border-radius: 0 0 12px 12px;">

                            <p style="color: #333333; font-size: 16px;">Olá,</p>

                            <p style="color: #555555; line-height: 1.6; margin: 20px 0;">

                                Recebemos uma solicitação para redefinir a senha da sua conta.

                            </p>

                            <div style="text-align: center; margin: 35px 0;">

                                <div style="background-color: #1e252b; padding: 20px; border-radius: 10px; display: inline-block;">

                                    <span style="font-size: 32px; font-weight: bold; letter-spacing: 8px; color: #B3E5FC; font-family: monospace;">

                                        {codigo}

                                    </span>

                                </div>

                            </div>

                            <p style="color: #666666; font-size: 14px;">

                                Este código é válido por <strong>15 minutos</strong>.<br>

                                Se você não solicitou esta recuperação, pode ignorar este e-mail.

                            </p>

                        </td>

                    </tr>

                    <tr>

                        <td style="text-align: center; padding: 25px; color: #999999; font-size: 12px;">

                            Equipe V-Inc • Voz Inclusiva

                        </td>

                    </tr>

                </table>

            </body>

            </html>

            """



            msg.attach(MIMEText(texto_plano, 'plain'))

            msg.attach(MIMEText(html_conteudo, 'html'))



            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)

            server.ehlo()

            server.starttls()

            server.ehlo()

            server.login(EMAIL_REMETENTE, SENHA_REMETENTE)

            server.sendmail(EMAIL_REMETENTE, [email_destino], msg.as_string())

            server.quit()



            self.after(0, self.sucesso_envio_email)



        except Exception as e:

            print(f"\n[ERRO SCRIPT GMAIL] Detalhes do erro: {e}\n")

            self.after(0, self.erro_envio_email)



    def sucesso_envio_email(self):

        self.btn_enviar_codigo.configure(state="normal")

        self.lbl_status_recup.configure(text="Código enviado com sucesso! Verifique a sua caixa de entrada ou spam", text_color="#69F0AE")

        self.after(2000, self.criar_tela_validacao_codigo)



    def erro_envio_email(self):

        self.btn_enviar_codigo.configure(state="normal")

        self.lbl_status_recup.configure(text="Falha ao enviar. Verifique as credenciais e a sua Senha de App.", text_color="#FF5252")



    # (Os métodos restantes permanecem iguais)

    def criar_tela_validacao_codigo(self):

        self.limpar_tela()

        self.geometry("550x620")



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



        if codigo_digitado == self.codigo_recuperacao and self.email_recuperando:

            self.lbl_status_codigo.configure(text="Código validado com sucesso!", text_color="#69F0AE")

            self.after(1000, self.criar_tela_nova_senha)

        else:

            self.lbl_status_codigo.configure(text="Código incorreto ou expirado. Tente novamente.", text_color="#FF5252")



    def criar_tela_nova_senha(self):

        self.limpar_tela()

        self.geometry("550x620")



        lbl_logo = ctk.CTkLabel(self, text="🔄", font=("Arial", 40))

        lbl_logo.pack(pady=(50, 10))



        lbl_titulo = ctk.CTkLabel(self, text="Definir Nova Senha", font=("Arial", 22, "bold"), text_color="#B3E5FC")

        lbl_titulo.pack(pady=5)



        lbl_desc = ctk.CTkLabel(self, text="Digite a senha que você deseja usar a partir de agora:", font=("Arial", 12), text_color="#CCCCCC")

        lbl_desc.pack(pady=(0, 20))



        self.txt_nova_senha_recup = ctk.CTkEntry(self, placeholder_text="Digite sua nova senha", show="*", width=400, height=45)

        self.txt_nova_senha_recup.pack(pady=10)



        self.txt_confirma_senha_recup = ctk.CTkEntry(self, placeholder_text="Confirme sua nova senha", show="*", width=400, height=45)

        self.txt_confirma_senha_recup.pack(pady=10)



        self.lbl_status_nova_senha = ctk.CTkLabel(self, text="", font=("Arial", 12))

        self.lbl_status_nova_senha.pack(pady=5)



        btn_salvar = ctk.CTkButton(self, text="Salvar Nova Senha ✓", font=("Arial", 14, "bold"), width=400, height=45, fg_color="#69F0AE", text_color="#000000", hover_color="#00E676", command=self.acao_atualizar_senha)

        btn_salvar.pack(pady=15)



    def acao_atualizar_senha(self):

        nova_senha = self.txt_nova_senha_recup.get().strip()

        confirma_senha = self.txt_confirma_senha_recup.get().strip()



        if not nova_senha or not confirma_senha:

            self.lbl_status_nova_senha.configure(text="Por favor, preencha ambos os campos.", text_color="#FF5252")

            return



        if nova_senha != confirma_senha:

            self.lbl_status_nova_senha.configure(text="As senhas digitadas não são iguais.", text_color="#FF5252")

            return



        try:

            nova_senha_hash = bcrypt.hashpw(nova_senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

            supabase.table("usuarios").update({"senha_hash": nova_senha_hash}).eq("email", self.email_recuperando).execute()

            

            self.lbl_status_nova_senha.configure(text="Senha alterada com sucesso! Redirecionando...", text_color="#69F0AE")

            self.after(2500, self.criar_tela_login)

            

        except Exception as e:

            self.lbl_status_nova_senha.configure(text="Erro ao atualizar a senha no servidor.", text_color="#FF5252")

            print(f"[ERRO SUPABASE]: {e}")





# ==========================================

# INICIALIZAÇÃO

# ==========================================

if __name__ == "__main__":

    app = VincLoginApp()

    app.mainloop() 

