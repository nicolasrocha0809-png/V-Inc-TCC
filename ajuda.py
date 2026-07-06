import customtkinter as ctk

class AjudaScreen(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.pack(fill="both", expand=True, padx=40, pady=25)


        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True)

        self.criar_faq()

    def criar_faq(self):
        # Título
        title = ctk.CTkLabel(self.scroll_frame, text="Perguntas Frequentes (FAQ)", 
                            font=("Arial", 28, "bold"), text_color="#60A5FA")
        title.pack(anchor="w", pady=(0, 8))

        subtitle = ctk.CTkLabel(self.scroll_frame, text="Encontre respostas rápidas para as dúvidas mais comuns.",
                               font=("Arial", 15), text_color="#94A3B8")
        subtitle.pack(anchor="w", pady=(0, 30))

        # Perguntas
        self.criar_pergunta(
            "O que é o V-Inc?",
            "escrevam uma breve explicação sobre o que é."
        )

        self.criar_pergunta(
            "Como usar comandos de voz?",
            "breve explicação",
            exemplos=["Abrir Monitor", "Ler Histórico", "Configurar Tema"]
        )

        self.criar_pergunta(
            "Como alterar o tema?",
            " breve explicação"
        )

        self.criar_pergunta(
            "O monitoramento é em tempo real?",
            "responda a pergunta"
        )

       
        support_frame = ctk.CTkFrame(self.scroll_frame, fg_color="#1E40AF", corner_radius=12)
        support_frame.pack(fill="x", pady=(40, 0))

        support_text = ctk.CTkLabel(support_frame, 
                                   text="Ainda tem dúvidas?\nEntre em contato com a nossa equipe: vinc.suporte@gmail.com ou @v.inc_tcc",
                                   font=("Arial", 14),
                                   text_color="white",
                                   justify="left",
                                   wraplength=820)
        support_text.pack(side="left", padx=25, pady=22)

       
    def criar_pergunta(self, titulo, resposta, exemplos=None):
        frame = ctk.CTkFrame(self.scroll_frame, fg_color="#1E2937", corner_radius=10)
        frame.pack(fill="x", pady=8, padx=5)

      
        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=16)

        label = ctk.CTkLabel(header, text=titulo, font=("Arial", 16, "bold"), text_color="#E0F2FE")
        label.pack(side="left", fill="x", expand=True)

        arrow = ctk.CTkLabel(header, text="▼", font=("Arial", 20), text_color="#60A5FA")
        arrow.pack(side="right")

        # Resposta
        answer_frame = ctk.CTkFrame(frame, fg_color="transparent")
        
        answer = ctk.CTkLabel(answer_frame, text=resposta, 
                             font=("Arial", 14.5), 
                             text_color="#CBD5E1", 
                             wraplength=820,      # Aumentado bastante
                             justify="left")
        answer.pack(anchor="w", padx=20, pady=(0, 18))

        if exemplos:
            for ex in exemplos:
                ex_label = ctk.CTkLabel(answer_frame, text=f"• {ex}", 
                                       font=("Arial", 14), text_color="#94A3B8")
                ex_label.pack(anchor="w", padx=25, pady=2)

        # Toggle
        def toggle():
            if answer_frame.winfo_ismapped():
                answer_frame.pack_forget()
                arrow.configure(text="▼")
            else:
                answer_frame.pack(fill="x", padx=5, pady=(0, 12))
                arrow.configure(text="▲")

        header.bind("<Button-1>", lambda e: toggle())
        label.bind("<Button-1>", lambda e: toggle())
        arrow.bind("<Button-1>", lambda e: toggle())

        answer_frame.pack_forget()  