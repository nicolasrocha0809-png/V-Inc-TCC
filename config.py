import customtkinter as ctk

class ConfigScreen(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="#0F172A")
        ctk.CTkLabel(self, text="⚙️ Configurações", font=("Arial", 28, "bold"), text_color="#60A5FA").pack(pady=100)
        ctk.CTkLabel(self, text="Tela de Configurações em desenvolvimento...", font=("Arial", 16), text_color="#94A3B8").pack()