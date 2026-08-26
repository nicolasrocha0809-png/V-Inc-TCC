from datetime import datetime
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QListWidget, QVBoxLayout, QWidget
from config import settings  # Importado para garantir a leitura do ID atual se necessário


class HistoricoScreen(QWidget):

  def __init__(self, supabase_client=None, user_id=None, parent=None):
    super().__init__(parent)
    self.supabase = supabase_client
    self.user_id = user_id

    self.setStyleSheet("background-color: #0F172A;")

    layout = QVBoxLayout(self)
    layout.setAlignment(Qt.AlignCenter)
    layout.setContentsMargins(30, 30, 30, 30)

   
    lbl_titulo = QLabel("Histórico de Comandos")
    lbl_titulo.setStyleSheet(
        "font-size: 24px; font-weight: bold; color: #60A5FA;"
    )
    lbl_titulo.setAlignment(Qt.AlignCenter)
    layout.addWidget(lbl_titulo)

 
    self.list_widget = QListWidget()
    self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: #1E293B;
                color: #F8FAFC;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #334155;
            }
        """)
    layout.addWidget(self.list_widget)

    
    if self.supabase:
      self.carregar_historico()
    else:
      print(f"DEBUG: Supabase={self.supabase}")
      self.list_widget.addItem("Conexão com o Supabase indisponível.")

  def carregar_historico(self):
    """Busca o histórico filtrando estritamente pelo ID do usuário logado"""
    try:
      self.list_widget.clear()

      # Pega o ID passado por parâmetro ou busca direto nas configurações ativas
      usuario_ativo = self.user_id or settings.get("usuario", "id_usuario_atual")

      print(f"DEBUG: Tentando buscar histórico para o usuário ID -> {usuario_ativo}")

      if not usuario_ativo:
        self.list_widget.addItem("Nenhum usuário autenticado encontrado.")
        return

 
      response = (
          self.supabase.table("historico")
          .select("comando, data_hora")
          .eq("id_usuario", usuario_ativo)  # <-- O FILTRO QUE FALTAVA
          .order("data_hora", desc=True)
          .execute()
      )

      print(f"DEBUG: Resposta completa do Supabase: {response}")
      dados = response.data
      print(f"DEBUG: Dados encontrados: {dados}")

      if not dados:
        self.list_widget.addItem("Nenhum comando registrado ainda para este usuário.")
        return

      for item in dados:
        comando = item.get("comando", "Comando desconhecido")
        data_str = item.get("data_hora", "")

        try:
          dt = datetime.fromisoformat(data_str.replace("Z", "+00:00"))
          data_formatada = dt.strftime("%d/%m/%Y %H:%M:%S")
        except Exception:
          data_formatada = data_str

        texto_exibicao = f"[{data_formatada}] → {comando}"
        self.list_widget.addItem(texto_exibicao)

    except Exception as e:
      print(f"ERRO EXATO NO HISTORICO: {e}")
      self.list_widget.addItem(f"Erro ao carregar histórico: {e}")