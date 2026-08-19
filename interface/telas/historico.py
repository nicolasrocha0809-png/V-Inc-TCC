from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem
from PySide6.QtCore import Qt
from datetime import datetime

class HistoricoScreen(QWidget):
    def __init__(self, supabase_client=None, user_id=None, parent=None):
        super().__init__(parent)
        self.supabase = supabase_client
        self.user_id = user_id
        
        self.setStyleSheet("background-color: #0F172A;")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(30, 30, 30, 30)

        # Label de Título
        lbl_titulo = QLabel("Histórico de Comandos")
        lbl_titulo.setStyleSheet("font-size: 24px; font-weight: bold; color: #60A5FA;")
        lbl_titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_titulo)

        # Lista para exibir os históricos
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

        # Carrega os dados se o cliente Supabase e o user_id estiverem presentes
        if self.supabase and self.user_id:
            self.carregar_historico()
        else:
            self.list_widget.addItem("Usuário não autenticado ou conexão indisponível.")

    def carregar_historico(self):
        """Busca o histórico no Supabase correspondente ao usuário (listarHistorico)"""
        try:
            self.list_widget.clear()
            
            # Consulta na tabela historico filtrando pelo id_usuario correto da tabela
            response = self.supabase.table("historico") \
                .select("comando, data_hora") \
                .eq("id_usuario", self.user_id) \
                .order("data_hora", desc=True) \
                .execute()
            
            dados = response.data
            
            if not dados:
                self.list_widget.addItem("Nenhum comando registrado ainda.")
                return

            for item in dados:
                comando = item.get("comando", "Comando desconhecido")
                data_str = item.get("data_hora", "")
                
                # Formata a data/hora para o padrão brasileiro se possível
                try:
                    dt = datetime.fromisoformat(data_str.replace("Z", "+00:00"))
                    data_formatada = dt.strftime("%d/%m/%Y %H:%M:%S")
                except Exception:
                    data_formatada = data_str

                texto_exibicao = f"[{data_formatada}] ➔ {comando}"
                self.list_widget.addItem(texto_exibicao)

        except Exception as e:
            self.list_widget.addItem(f"Erro ao carregar histórico: {e}")