import customtkinter as ctk

class ComandosScreen(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="#0F172A")
        self.criar_tela()

    def criar_tela(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(30, 20), padx=40)

        ctk.CTkLabel(header, text="Guia de Comandos", 
                     font=("Arial", 28, "bold"), text_color="#60A5FA").pack(anchor="w")

        ctk.CTkLabel(header, text="Diga o nome do assistente seguido por um destes comandos.",
                     font=("Arial", 14), text_color="#94A3B8", justify="left").pack(anchor="w", pady=8)

        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(fill="both", expand=True, padx=40, pady=10)

        self.criar_card(grid, "▶️", '"Abra o YouTube"', "Inicia o aplicativo de vídeo e prepara para pesquisa por voz.", 0, 0)
        self.criar_card(grid, "📖", '"Leia o texto"', "Ativa o leitor de tela para o documento ou site atualmente aberto.", 0, 1)
        self.criar_card(grid, "🔍", '"Pesquise sobre"', "Faz uma pesquisa no Google sobre o assunto dito.", 1, 0)
        self.criar_card(grid, "⏰", '"Defina alarme"', "Configura um alarme ou lembrete no horário desejado.", 1, 1)

    def criar_card(self, parent, emoji, titulo, descricao, row, column):
        card = ctk.CTkFrame(parent, fg_color="#1E2937", corner_radius=16, border_width=2, border_color="#334155")
        card.grid(row=row, column=column, padx=12, pady=12, sticky="nsew")

        ctk.CTkLabel(card, text=emoji, font=("Arial", 40)).pack(pady=(20, 8))
        ctk.CTkLabel(card, text=titulo, font=("Arial", 17, "bold"), text_color="#E0F2FE").pack(pady=5)
        ctk.CTkLabel(card, text=descricao, font=("Arial", 13), text_color="#94A3B8", 
                     wraplength=220, justify="center").pack(pady=10, padx=15)

        card.bind("<Enter>", lambda e: card.configure(fg_color="#334155"))
        card.bind("<Leave>", lambda e: card.configure(fg_color="#1E2937"))

        parent.grid_columnconfigure((0,1), weight=1)