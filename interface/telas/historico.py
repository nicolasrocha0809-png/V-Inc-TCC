from datetime import datetime
from functools import partial

from PySide6.QtCore import (
    QAbstractAnimation,
    QEasingCurve,
    QPropertyAnimation,
    QRect,
    QSize,
    Qt,
)
from PySide6.QtGui import QFontMetrics
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QComboBox,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from config import settings


class ListaHistorico(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.verticalScrollBar().setSingleStep(12)

        self._destino_scroll = 0
        self._animacao_scroll = QPropertyAnimation(
            self.verticalScrollBar(),
            b"value",
            self,
        )
        self._animacao_scroll.setDuration(170)
        self._animacao_scroll.setEasingCurve(QEasingCurve.OutCubic)

    def wheelEvent(self, event):
        delta = event.angleDelta().y()

        if not delta:
            super().wheelEvent(event)
            return

        barra = self.verticalScrollBar()
        deslocamento = int(-(delta / 120) * 92)

        if self._animacao_scroll.state() == QAbstractAnimation.State.Running:
            destino_base = self._destino_scroll
        else:
            destino_base = barra.value()

        self._destino_scroll = max(
            barra.minimum(),
            min(barra.maximum(), destino_base + deslocamento),
        )

        self._animacao_scroll.stop()
        self._animacao_scroll.setStartValue(barra.value())
        self._animacao_scroll.setEndValue(self._destino_scroll)
        self._animacao_scroll.start()
        event.accept()


class HistoricoScreen(QWidget):
    def __init__(self, supabase_client=None, user_id=None, parent=None):
        super().__init__(parent)
        self.supabase = supabase_client
        self.user_id = user_id
        self._primeira_exibicao = True

        self.setObjectName("pagina_historico")

        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(40, 32, 40, 32)
        layout_principal.setSpacing(20)

        textos_cabecalho = QVBoxLayout()
        textos_cabecalho.setSpacing(6)

        rotulo = QLabel("ATIVIDADE RECENTE")
        rotulo.setObjectName("rotulo_pagina")

        titulo = QLabel("Histórico de comandos")
        titulo.setObjectName("titulo_pagina")

        subtitulo = QLabel(
            "Consulte os comandos de voz reconhecidos pelo V.INC nesta conta."
        )
        subtitulo.setObjectName("subtitulo_pagina")
        subtitulo.setWordWrap(True)

        textos_cabecalho.addWidget(rotulo)
        textos_cabecalho.addWidget(titulo)
        textos_cabecalho.addWidget(subtitulo)

        layout_principal.addLayout(textos_cabecalho)

        barra_acoes = QHBoxLayout()
        barra_acoes.setSpacing(10)

        self.lbl_resumo = QLabel("Carregando histórico...")
        self.lbl_resumo.setObjectName("resumo_historico")

        self.combo_ordem = QComboBox()
        self.combo_ordem.setObjectName("ordem_historico")
        self.combo_ordem.addItems(
            [
                "Mais recentes primeiro",
                "Mais antigos primeiro",
            ]
        )
        self.combo_ordem.setAccessibleName("Ordenação do histórico")
        self.combo_ordem.currentIndexChanged.connect(self.carregar_historico)

        self.btn_atualizar = QPushButton("Atualizar")
        self.btn_atualizar.setObjectName("botao_atualizar_historico")
        self.btn_atualizar.setCursor(Qt.PointingHandCursor)
        self.btn_atualizar.setAccessibleName("Atualizar histórico de comandos")
        self.btn_atualizar.setAccessibleDescription(
            "Busca novamente os comandos registrados para esta conta."
        )
        self.btn_atualizar.clicked.connect(self.carregar_historico)

        self.btn_limpar = QPushButton("Limpar histórico")
        self.btn_limpar.setObjectName("botao_limpar_historico")
        self.btn_limpar.setCursor(Qt.PointingHandCursor)
        self.btn_limpar.setAccessibleDescription(
            "Exclui todos os comandos registrados para esta conta após confirmação."
        )
        self.btn_limpar.clicked.connect(self.excluir_todo_historico)

        barra_acoes.addWidget(self.lbl_resumo)
        barra_acoes.addStretch()
        barra_acoes.addWidget(self.combo_ordem)
        barra_acoes.addWidget(self.btn_atualizar)
        barra_acoes.addWidget(self.btn_limpar)
        layout_principal.addLayout(barra_acoes)

        self.conteudo = QStackedWidget()
        self.conteudo.setObjectName("conteudo_historico")

        self.lbl_estado = QLabel()
        self.lbl_estado.setObjectName("estado_historico")
        self.lbl_estado.setAlignment(Qt.AlignCenter)
        self.lbl_estado.setWordWrap(True)
        self.lbl_estado.setMinimumHeight(220)

        self.lista = ListaHistorico()
        self.lista.setObjectName("lista_historico")
        self.lista.setSpacing(10)
        self.lista.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.lista.setAccessibleName("Histórico de comandos")
        self.lista.setAccessibleDescription(
            "Lista dos comandos de voz reconhecidos, do mais recente para o mais antigo."
        )

        self.conteudo.addWidget(self.lbl_estado)
        self.conteudo.addWidget(self.lista)
        layout_principal.addWidget(self.conteudo, 1)

        if self.supabase:
            self.carregar_historico()
        else:
            self._mostrar_estado(
                "Não foi possível acessar o histórico porque a conexão está indisponível."
            )

    def showEvent(self, event):
        super().showEvent(event)

        if self._primeira_exibicao:
            self._primeira_exibicao = False
            return

        if self.supabase:
            self.carregar_historico()

    def carregar_historico(self):
        """Busca o histórico do usuário e atualiza os estados da tela."""
        self.btn_atualizar.setEnabled(False)
        self.btn_atualizar.setText("Atualizando...")
        self.lbl_resumo.setText("Buscando comandos registrados...")

        try:
            usuario_ativo = self.user_id or settings.get(
                "usuario",
                "id_usuario_atual",
            )

            if not usuario_ativo:
                self._mostrar_estado("Nenhum usuário autenticado foi encontrado.")
                return

            ordem_decrescente = self.combo_ordem.currentIndex() == 0

            resposta = (
                self.supabase.table("historico")
                .select("*")
                .eq("id_usuario", usuario_ativo)
                .order("data_hora", desc=ordem_decrescente)
                .execute()
            )

            dados = resposta.data or []

            if not dados:
                self._mostrar_estado(
                    "Nenhum comando registrado ainda.\n"
                    "Quando você usar o assistente, os comandos aparecerão aqui.",
                    "0 comandos registrados",
                )
                return

            self.lista.clear()

            for registro in dados:
                self._adicionar_registro(registro)

            quantidade = len(dados)
            sufixo = "comando registrado" if quantidade == 1 else "comandos registrados"
            self.lbl_resumo.setText(f"{quantidade} {sufixo}")
            self.conteudo.setCurrentWidget(self.lista)

        except Exception as erro:
            print(f"Erro ao carregar histórico: {erro}")
            self._mostrar_estado(
                "Não foi possível carregar o histórico neste momento.\n"
                "Verifique a conexão e tente atualizar novamente."
            )

        finally:
            self.btn_atualizar.setEnabled(True)
            self.btn_atualizar.setText("Atualizar")

    def _adicionar_registro(self, registro):
        comando = registro.get("comando") or "Comando não identificado"
        data_formatada = self._formatar_data(registro.get("data_hora", ""))

        item = QListWidgetItem()

        card = QFrame()
        card.setObjectName("item_historico")

        layout = QHBoxLayout(card)
        layout.setContentsMargins(18, 12, 18, 12)
        layout.setSpacing(18)

        textos = QVBoxLayout()
        textos.setSpacing(5)

        lbl_comando = QLabel(comando)
        lbl_comando.setObjectName("comando_historico")
        lbl_comando.setWordWrap(True)
        lbl_comando.setTextInteractionFlags(Qt.TextSelectableByMouse)

        lbl_data = QLabel(data_formatada)
        lbl_data.setObjectName("data_historico")

        btn_excluir = QPushButton("Excluir")
        btn_excluir.setObjectName("botao_excluir_historico")
        btn_excluir.setCursor(Qt.PointingHandCursor)
        btn_excluir.setAccessibleName(f"Excluir comando {comando}")
        btn_excluir.clicked.connect(partial(self.excluir_registro, dict(registro)))

        textos.addWidget(lbl_comando)
        textos.addWidget(lbl_data)
        layout.addLayout(textos, 1)
        layout.addWidget(btn_excluir, alignment=Qt.AlignVCenter)

        self.lista.addItem(item)
        self.lista.setItemWidget(item, card)
        self._ajustar_altura_item(item, lbl_comando)

    def excluir_registro(self, registro, _marcado=False):
        comando = registro.get("comando") or "Comando não identificado"
        confirmado = self._pedir_confirmacao(
            "Excluir comando",
            f'Deseja excluir o comando "{comando}" do histórico?',
            "Excluir",
        )

        if not confirmado:
            return

        try:
            usuario_ativo = self._obter_usuario_ativo()
            consulta = self.supabase.table("historico").delete()

            coluna_id = next(
                (
                    coluna
                    for coluna in ("id", "id_historico", "historico_id")
                    if registro.get(coluna) is not None
                ),
                None,
            )

            if coluna_id:
                consulta = consulta.eq(coluna_id, registro[coluna_id])
            else:
                data_hora = registro.get("data_hora")

                if not data_hora:
                    raise RuntimeError("O registro não possui um identificador seguro.")

                consulta = consulta.eq("data_hora", data_hora).eq("comando", comando)

            consulta.eq("id_usuario", usuario_ativo).execute()
            self.carregar_historico()

        except Exception as erro:
            print(f"Erro ao excluir registro do histórico: {erro}")
            QMessageBox.warning(
                self,
                "Não foi possível excluir",
                "O comando não pôde ser excluído neste momento.",
            )

    def excluir_todo_historico(self):
        if self.lista.count() == 0:
            return

        confirmado = self._pedir_confirmacao(
            "Limpar histórico",
            "Deseja excluir permanentemente todo o histórico desta conta?",
            "Limpar histórico",
        )

        if not confirmado:
            return

        try:
            usuario_ativo = self._obter_usuario_ativo()
            (
                self.supabase.table("historico")
                .delete()
                .eq("id_usuario", usuario_ativo)
                .execute()
            )
            self.carregar_historico()

        except Exception as erro:
            print(f"Erro ao limpar histórico: {erro}")
            QMessageBox.warning(
                self,
                "Não foi possível limpar",
                "O histórico não pôde ser excluído neste momento.",
            )

    def _obter_usuario_ativo(self):
        usuario_ativo = self.user_id or settings.get(
            "usuario",
            "id_usuario_atual",
        )

        if not usuario_ativo:
            raise RuntimeError("Nenhum usuário autenticado foi encontrado.")

        return usuario_ativo

    def _ajustar_altura_item(self, item, lbl_comando):
        largura_texto = max(260, self.lista.viewport().width() - 190)
        metricas = QFontMetrics(lbl_comando.font())
        area_texto = metricas.boundingRect(
            QRect(0, 0, largura_texto, 1000),
            Qt.TextWordWrap,
            lbl_comando.text(),
        )
        altura = max(76, area_texto.height() + 54)
        item.setSizeHint(QSize(0, altura))

    def _pedir_confirmacao(self, titulo, mensagem, texto_confirmar):
        caixa = QMessageBox(self)
        caixa.setWindowTitle(titulo)
        caixa.setText(mensagem)
        caixa.setIcon(QMessageBox.Question)

        btn_confirmar = caixa.addButton(
            texto_confirmar,
            QMessageBox.AcceptRole,
        )
        btn_cancelar = caixa.addButton("Cancelar", QMessageBox.RejectRole)
        caixa.setDefaultButton(btn_cancelar)
        caixa.exec()

        return caixa.clickedButton() is btn_confirmar

    def _mostrar_estado(self, mensagem, resumo="Histórico indisponível"):
        self.lista.clear()
        self.lbl_resumo.setText(resumo)
        self.lbl_estado.setText(mensagem)
        self.conteudo.setCurrentWidget(self.lbl_estado)

    @staticmethod
    def _formatar_data(data_str):
        if not data_str:
            return "Data não informada"

        try:
            data = datetime.fromisoformat(data_str.replace("Z", "+00:00"))

            if data.tzinfo is not None:
                data = data.astimezone()

            return data.strftime("%d/%m/%Y às %H:%M")

        except (TypeError, ValueError):
            return str(data_str)
