import customtkinter as ctk
from comandos import ComandosScreen
from ajuda import AjudaScreen   

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("V-Inc - Assistente")
        self.geometry("960x640")        
        self.resizable(False, False)

        self.cor_primaria = "#60A5FA"
        self.cor_ajuda = "#F472B6"

        self.current_frame = None
        self.menu_buttons = {}

        self.criar_layout()

    def criar_layout(self):
        sidebar = ctk.CTkFrame(self, width=200, fg_color="#111827", corner_radius=0)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        logo = ctk.CTkLabel(sidebar, text="V-Inc", font=("Arial", 26, "bold"), text_color=self.cor_primaria)
        logo.pack(pady=(30, 40))

        self.criar_menu_button(sidebar, "🏠  Início", self.mostrar_inicio, selected=True)
        self.criar_menu_button(sidebar, "⚡  Comandos", self.mostrar_comandos)
        self.criar_menu_button(sidebar, "📺  Monitor", self.mostrar_monitor)
        self.criar_menu_button(sidebar, "📜  Histórico", self.mostrar_historico)
        self.criar_menu_button(sidebar, "⚙️  Configurações", self.mostrar_configuracoes)

        btn_ajuda = ctk.CTkButton(sidebar, text="❓  Ajuda", 
                                  fg_color=self.cor_ajuda,
                                  hover_color="#DB2777",
                                  text_color="white",
                                  font=("Arial", 14, "bold"),
                                  height=45,
                                  corner_radius=10,
                                  command=self.mostrar_ajuda)
        btn_ajuda.pack(side="bottom", pady=30, padx=20)

        self.main_area = ctk.CTkFrame(self, fg_color="#0F172A", corner_radius=0)
        self.main_area.pack(side="right", fill="both", expand=True)

        self.mostrar_inicio()

    def criar_menu_button(self, parent, text, command, selected=False):
        fg_color = "#1E2937" if selected else "transparent"
        text_color = self.cor_primaria if selected else "#94A3B8"

        btn = ctk.CTkButton(parent, 
                            text=text,
                            fg_color=fg_color,
                            text_color=text_color,
                            hover_color="#1E2937",
                            anchor="w",
                            height=50,
                            corner_radius=10,
                            font=("Arial", 15),
                            command=command)
        btn.pack(fill="x", padx=14, pady=4)
        
        self.menu_buttons[text] = btn
        return btn

    def destacar_menu(self, texto_selecionado):
        for texto, btn in self.menu_buttons.items():
            if texto == texto_selecionado:
                btn.configure(fg_color="#1E2937", text_color=self.cor_primaria)
            else:
                btn.configure(fg_color="transparent", text_color="#94A3B8")

    def limpar_content(self):
        if self.current_frame:
            self.current_frame.destroy()
        for widget in self.main_area.winfo_children():
            widget.destroy()

    def mostrar_inicio(self):
        self.limpar_content()
        self.destacar_menu("🏠  Início")
        
        content = ctk.CTkFrame(self.main_area, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=40, pady=25)

        mic_frame = ctk.CTkFrame(content, fg_color="#1E2937", width=140, height=140, corner_radius=999)
        mic_frame.pack(pady=10)
        mic_frame.pack_propagate(False)
        ctk.CTkLabel(mic_frame, text="🎤", font=("Arial", 60), text_color=self.cor_primaria).pack(expand=True)

        ctk.CTkLabel(content, text="OUVINDO", font=("Arial", 32, "bold"), text_color=self.cor_primaria).pack(pady=(8, 5))
        ctk.CTkLabel(content, text="Fale claramente para dar comandos...", font=("Arial", 13.5), text_color="#94A3B8").pack()

        audio_card = ctk.CTkFrame(content, fg_color="#1E2937", corner_radius=16, border_width=2, border_color="#334155")
        audio_card.pack(fill="x", pady=10, padx=20)

        ctk.CTkLabel(audio_card, text="Entrada de Áudio", font=("Arial", 14.5, "bold")).pack(anchor="w", padx=25, pady=(20, 6))
        self.mic_combo = ctk.CTkComboBox(audio_card, values=["Microfone Padrão", "Microfone Externo"], width=380, height=44, font=("Arial", 13))
        self.mic_combo.set("Microfone Padrão")
        self.mic_combo.pack(padx=25, pady=(0, 18))

        ctk.CTkLabel(audio_card, text="Saída de Áudio", font=("Arial", 14.5, "bold")).pack(anchor="w", padx=25, pady=(0, 6))
        self.speaker_combo = ctk.CTkComboBox(audio_card, values=["Headphone Padrão", "Alto-falantes"], width=380, height=44, font=("Arial", 13))
        self.speaker_combo.set("Headphone Padrão")
        self.speaker_combo.pack(padx=25, pady=(0, 25))

        btn_frame = ctk.CTkFrame(audio_card, fg_color="transparent")
        btn_frame.pack(pady=(0, 22), padx=25, fill="x")

        self.btn_parar = ctk.CTkButton(btn_frame, text="⏸️  Parar de Ouvir", font=("Arial", 14, "bold"), width=175, height=48,
                                       fg_color="#60A5FA", text_color="#0F172A", hover_color="#3B82F6", corner_radius=10,
                                       command=self.parar_ouvindo)
        self.btn_parar.pack(side="left", padx=(0, 10))

        self.btn_config = ctk.CTkButton(btn_frame, text="🎙️  Configurações de Voz", font=("Arial", 14, "bold"), width=175, height=48,
                                        fg_color="transparent", border_width=2, border_color="#475569", hover_color="#334155", corner_radius=10)
        self.btn_config.pack(side="left")

    def mostrar_comandos(self):
        self.limpar_content()
        self.destacar_menu("⚡  Comandos")
        self.current_frame = ComandosScreen(self.main_area)
        self.current_frame.pack(fill="both", expand=True)

    def mostrar_monitor(self):
        self.limpar_content()
        self.destacar_menu("📺  Monitor")
        ctk.CTkLabel(self.main_area, text="📺 Monitor", font=("Arial", 24, "bold"), text_color=self.cor_primaria).pack(expand=True)

    def mostrar_historico(self):
        self.limpar_content()
        self.destacar_menu("📜  Histórico")
        ctk.CTkLabel(self.main_area, text="📜 Histórico", font=("Arial", 24, "bold"), text_color=self.cor_primaria).pack(expand=True)

    def mostrar_configuracoes(self):
        self.limpar_content()
        self.destacar_menu("⚙️  Configurações")
        ctk.CTkLabel(self.main_area, text="⚙️ Configurações", font=("Arial", 24, "bold"), text_color=self.cor_primaria).pack(expand=True)

    def mostrar_ajuda(self):
        self.limpar_content()
        self.current_frame = AjudaScreen(self.main_area)

    def parar_ouvindo(self):
        if self.btn_parar.cget("text") == "⏸️  Parar de Ouvir":
            self.btn_parar.configure(text="▶️  Voltar a Ouvir", fg_color="#22C55E")
        else:
            self.btn_parar.configure(text="⏸️  Parar de Ouvir", fg_color="#60A5FA")


if __name__ == "__main__":
    app = MainApp()
    app.mainloop()