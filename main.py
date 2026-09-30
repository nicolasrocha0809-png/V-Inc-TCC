import sys
import os
from dotenv import load_dotenv

# Forca a camada de acessibilidade do Qt para leitores de tela (NVDA/JAWS).
os.environ.setdefault("QT_ACCESSIBILITY", "1")

# 1. Carrega as variáveis do arquivo .env localizado na raiz
load_dotenv()


from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QAccessible
from supabase import create_client
from interface.janela import JanelaPrincipal
from interface.theme_manager import carregar_estilo

# 2. Inicializa o cliente do Supabase com as variáveis de ambiente
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERRO: Variáveis SUPABASE_URL ou SUPABASE_KEY não encontradas no arquivo .env")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Inicialização da Aplicação
app = QApplication(sys.argv)
QAccessible.setActive(True)

# Aplica o estilo concatenado
app.setStyleSheet(carregar_estilo())

# Cria a instância da Janela Principal passando o cliente Supabase
janela = JanelaPrincipal(supabase_client=supabase)

janela.show()
sys.exit(app.exec())
