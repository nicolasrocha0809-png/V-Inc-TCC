import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Forca a camada de acessibilidade do Qt para leitores de tela (NVDA/JAWS).
os.environ.setdefault("QT_ACCESSIBILITY", "1")

# 1. Carrega as variáveis do arquivo .env localizado na raiz
load_dotenv()


from PySide6.QtWidgets import QApplication, QProxyStyle, QStyle
from PySide6.QtGui import QAccessible, QIcon
from supabase import create_client
from interface.janela import JanelaPrincipal
from interface.theme_manager import carregar_estilo
from interface.acessibilidade import FiltroAtivacaoTeclado


class EstiloSemFocoPontilhado(QProxyStyle):
    """Remove apenas o pontilhado nativo; a borda de foco do QSS permanece."""

    def drawPrimitive(self, elemento, opcao, pintor, widget=None):
        if elemento == QStyle.PrimitiveElement.PE_FrameFocusRect:
            return

        super().drawPrimitive(elemento, opcao, pintor, widget)

# 2. Inicializa o cliente do Supabase com as variáveis de ambiente
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERRO: Variáveis SUPABASE_URL ou SUPABASE_KEY não encontradas no arquivo .env")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Faz o Windows agrupar e identificar corretamente o V.INC na barra de tarefas.
if sys.platform == "win32":
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "VINC.VozInclusiva"
        )
    except (AttributeError, OSError):
        pass

# Inicialização da Aplicação
app = QApplication(sys.argv)
app.setStyle(EstiloSemFocoPontilhado(app.style()))
QAccessible.setActive(True)

# Mantém o filtro vivo durante toda a execução do aplicativo.
filtro_ativacao_botoes = FiltroAtivacaoTeclado(app)
app.installEventFilter(filtro_ativacao_botoes)

icone_app = Path(__file__).resolve().parent / "interface" / "assets" / "vinc.ico"
if icone_app.exists():
    app.setWindowIcon(QIcon(str(icone_app)))

# Aplica o estilo concatenado
app.setStyleSheet(carregar_estilo())

# Cria a instância da Janela Principal passando o cliente Supabase
janela = JanelaPrincipal(supabase_client=supabase)

janela.show()
sys.exit(app.exec())
