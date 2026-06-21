import customtkinter as ctk
import os

class LoginApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("V-Inc - Login")
        self.geometry("450x600")
        self.configure(fg_color="#121212")

        # Centralizar a janela
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

        # Layout Principal
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(expand=True, fill="both", padx=40, pady=20)

        # Logo / Ícone de Olho
        self.logo_frame = ctk.CTkFrame(self.main_frame, width=80, height=80, corner_radius=40, fg_color="#B3E5FC")
        self.logo_frame.pack(pady=(40, 10))
        self.logo_label = ctk.CTkLabel(self.logo_frame, text="👁", font=("Arial", 40), text_color="#000000")
        self.logo_label.place(relx=0.5, rely=0.5, anchor="center")

        # Título "V-Inc"
        self.title_label = ctk.CTkLabel(self.main_frame, text="V-Inc", font=("Arial Bold", 32), text_color="#B3E5FC")
        self.title_label.pack(pady=(0, 5))

        # Subtítulo "Acesso Seguro"
        self.subtitle_label = ctk.CTkLabel(self.main_frame, text="Acesso Seguro", font=("Arial", 18), text_color="#CCCCCC")
        self.subtitle_label.pack(pady=(0, 40))

        # Campo: Email
        self.email_label = ctk.CTkLabel(self.main_frame, text="Email de Acesso", font=("Arial", 12), text_color="#FFFFFF")
        self.email_label.pack(anchor="w", padx=5)
        self.email_entry = ctk.CTkEntry(self.main_frame, placeholder_text="nome@exemplo.com", height=50, fg_color="#2A2A2A", border_color="#333333", text_color="#FFFFFF", corner_radius=8)
        self.email_entry.pack(fill="x", pady=(5, 20))

        # Campo: Senha
        self.password_label = ctk.CTkLabel(self.main_frame, text="Senha", font=("Arial", 12), text_color="#FFFFFF")
        self.password_label.pack(anchor="w", padx=5)
        self.password_entry = ctk.CTkEntry(self.main_frame, placeholder_text="********", show="*", height=50, fg_color="#2A2A2A", border_color="#333333", text_color="#FFFFFF", corner_radius=8)
        self.password_entry.pack(fill="x", pady=(5, 40))

        # Botão Entrar
        self.login_button = ctk.CTkButton(self.main_frame, text="Entrar  →", command=self.login_event, height=55, fg_color="#B3E5FC", text_color="#000000", hover_color="#81D4FA", font=("Arial Bold", 18), corner_radius=10)
        self.login_button.pack(fill="x")

    def login_event(self):
        email = self.email_entry.get()
        senha = self.password_entry.get()

        if email and senha:
            print(f"Login bem-sucedido: {email}")
            
            # FECHA A TELA DE LOGIN
            self.destroy()
            
            # INICIA O ASSISTENTE DE VOZ DIRETAMENTE (SEM TELA)
            import teste_voz
            teste_voz.iniciar_assistente()
        else:
            print("Erro: Preencha todos os campos.")

if __name__ == "__main__":
    app = LoginApp()
    app.mainloop()