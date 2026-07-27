import sys
import os
from dotenv import load_dotenv
from PySide6.QtWidgets import QApplication
from supabase import create_client
from interface.janela import JanelaPrincipal
from config import settings
from interface.prefs_manager import PrefsManager
# 1. Carrega as variáveis do arquivo .env localizado na raiz
load_dotenv()

# 2. Inicializa o cliente do Supabase com as variáveis de ambiente
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERRO: Variáveis SUPABASE_URL ou SUPABASE_KEY não encontradas no arquivo .env")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def carregar_estilo_global():
    tema = settings.get("visual", "tema")
    # Define caminhos baseados na estrutura de pastas correta
    raiz = os.path.dirname(os.path.abspath(__file__))
    caminho_base = os.path.join(raiz, "interface", "estilos", "base.qss")
    caminho_tema = os.path.join(raiz, "interface", "temas", f"{tema}.qss")
    
    estilo_total = ""
    
    # Carrega o base.qss
    if os.path.exists(caminho_base):
        with open(caminho_base, "r", encoding="utf-8") as f:
            estilo_total += f.read()
            
    # Carrega o tema selecionado
    if os.path.exists(caminho_tema):
        with open(caminho_tema, "r", encoding="utf-8") as f:
            estilo_total += f.read()
            
    return estilo_total

# Inicialização da Aplicação
app = QApplication(sys.argv)

# Aplica o estilo concatenado
app.setStyleSheet(carregar_estilo_global())

# Cria a instância da Janela Principal passando o cliente Supabase
janela = JanelaPrincipal(supabase_client=supabase)

janela.show()
sys.exit(app.exec())