import customtkinter as ctk
import time
import threading
import sys
import subprocess
import os

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class LoadingScreen(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("V-Inc - Carregando")
        self.geometry("680x520")
        self.resizable(False, False)
        
        self.cor_primaria = "#60A5FA"
        self.cor_acento = "#93C5FD"
        self.running = True

        self.criar_tela_carregamento()
        self.iniciar_carregamento()

    def criar_tela_carregamento(self):
        frame = ctk.CTkFrame(self, fg_color="#0F172A", corner_radius=20)
        frame.pack(expand=True, fill="both", padx=40, pady=40)

        self.lbl_icon = ctk.CTkLabel(frame, text="🎤", font=("Arial", 92))
        self.lbl_icon.pack(pady=(50, 20))

        lbl_titulo = ctk.CTkLabel(frame, text="V-Inc", 
                                  font=("Arial", 38, "bold"), 
                                  text_color=self.cor_acento)
        lbl_titulo.pack(pady=(0, 4))

        lbl_sub = ctk.CTkLabel(frame, text="Assistente de Voz Inclusiva", 
                               font=("Arial", 16), text_color="#94A3B8")
        lbl_sub.pack(pady=(0, 40))

        self.lbl_status = ctk.CTkLabel(frame, text="Carregando sistema...", 
                                       font=("Arial", 15), text_color="#CBD5E1")
        self.lbl_status.pack(pady=(0, 12))

        self.progress_bar = ctk.CTkProgressBar(frame, width=420, height=12, 
                                               corner_radius=6, fg_color="#1E2937",
                                               progress_color=self.cor_primaria)
        self.progress_bar.pack(pady=10)
        self.progress_bar.set(0)

        self.lbl_porcentagem = ctk.CTkLabel(frame, text="0%", 
                                            font=("Arial", 17, "bold"), 
                                            text_color=self.cor_acento)
        self.lbl_porcentagem.pack(pady=(8, 4))

        self.lbl_modulos = ctk.CTkLabel(frame, text="Iniciando módulos...", 
                                        font=("Arial", 13), text_color="#64748B")
        self.lbl_modulos.pack()

    def atualizar_progresso(self):
        for i in range(101):
            if not self.running:
                return
            self.progress_bar.set(i / 100)
            self.lbl_porcentagem.configure(text=f"{i}%")
            
            if i == 35:
                self.lbl_modulos.configure(text="Carregando modelo de voz...")
            elif i == 60:
                self.lbl_modulos.configure(text="Inicializando reconhecimento...")
            elif i == 85:
                self.lbl_modulos.configure(text="Preparando interface...")
            
            time.sleep(0.045)
        
        if self.running:
            self.after(600, self.finalizar_e_fechar)

    def iniciar_carregamento(self):
        thread = threading.Thread(target=self.atualizar_progresso, daemon=True)
        thread.start()

    def finalizar_e_fechar(self):
        """Finaliza o carregamento, abre o assistente e fecha esta janela"""
        self.lbl_status.configure(text="Sistema pronto! Iniciando...", text_color="#4ADE80")
        self.lbl_modulos.configure(text="Abrindo V-Inc...")
        
      
        self.after(900, self.abrir_assistente_e_sair)

    def abrir_assistente_e_sair(self):
        try:
            self.running = False
            
            current_dir = os.path.dirname(os.path.abspath(__file__))
            assistente_path = os.path.join(current_dir, "main.py")
            
            print("[SISTEMA] Carregamento concluído. Iniciando assistente...")
            

            subprocess.Popen([sys.executable, assistente_path])
            
        except Exception as e:
            print(f"[ERRO] Falha ao abrir assistente: {e}")
        finally:
            self.after(300, self.forcar_fechamento)

    def forcar_fechamento(self):
        try:
            self.quit()
            self.destroy()
        except:
            pass
        try:
            os._exit(0)
        except:
            pass


# ====================== EXECUÇÃO ======================
if __name__ == "__main__":
    app = LoadingScreen()
    app.mainloop()