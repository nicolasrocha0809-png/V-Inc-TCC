"""Painel de conversa da sessão em estilo de mensagens, acessível por teclado."""

from collections import deque

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class ConversaWidget(QFrame):
    """Mostra somente pedidos, respostas e erros destinados ao usuário."""

    LIMITE_MENSAGENS = 80

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("painel_conversa")
        self.setMinimumWidth(560)
        self.setMaximumWidth(640)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._linhas = deque()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        cabecalho = QHBoxLayout()
        cabecalho.setSpacing(12)

        titulos = QVBoxLayout()
        titulos.setSpacing(3)
        titulo = QLabel("Conversa com o V.INC")
        titulo.setObjectName("titulo_conversa")
        titulo.setAccessibleName("Conversa com o V.INC")
        legenda = QLabel("Comandos e respostas desta sessão")
        legenda.setObjectName("descricao_conversa")
        titulos.addWidget(titulo)
        titulos.addWidget(legenda)
        cabecalho.addLayout(titulos, 1)

        limpar = QPushButton("Limpar")
        limpar.setObjectName("limpar_conversa")
        limpar.setCursor(Qt.PointingHandCursor)
        limpar.setAccessibleName("Limpar conversa visual")
        limpar.setAccessibleDescription(
            "Remove as mensagens desta tela. Não apaga o histórico da conta."
        )
        limpar.clicked.connect(self.limpar)
        cabecalho.addWidget(limpar)
        layout.addLayout(cabecalho)

        self.scroll = QScrollArea()
        self.scroll.setObjectName("scroll_conversa")
        self.scroll.setWidgetResizable(True)
        self.scroll.setFixedHeight(330)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setAccessibleName("Mensagens da sessão")
        self.scroll.setAccessibleDescription(
            "Pedidos do usuário à direita e respostas do V.INC à esquerda."
        )

        corpo = QWidget()
        corpo.setObjectName("conteudo_conversa")
        self.layout_mensagens = QVBoxLayout(corpo)
        self.layout_mensagens.setContentsMargins(4, 8, 4, 8)
        self.layout_mensagens.setSpacing(10)

        self.aviso_vazio = QLabel(
            "Quando você falar com o V.INC, a conversa aparecerá aqui."
        )
        self.aviso_vazio.setObjectName("conversa_vazia")
        self.aviso_vazio.setWordWrap(True)
        self.aviso_vazio.setAlignment(Qt.AlignCenter)
        self.layout_mensagens.addWidget(self.aviso_vazio)
        self.layout_mensagens.addStretch(1)
        self.scroll.setWidget(corpo)
        layout.addWidget(self.scroll)

    def adicionar_mensagem(self, tipo, texto):
        if tipo not in {"usuario", "vinc", "erro"}:
            return
        texto = str(texto or "").strip()
        if not texto:
            return

        self.aviso_vazio.hide()
        linha = QWidget()
        linha_layout = QHBoxLayout(linha)
        linha_layout.setContentsMargins(0, 0, 0, 0)
        linha_layout.setSpacing(0)

        bolha = QFrame()
        bolha.setObjectName({
            "usuario": "bolha_usuario",
            "vinc": "bolha_vinc",
            "erro": "bolha_erro",
        }[tipo])
        bolha.setMaximumWidth(430)
        bolha.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        conteudo = QVBoxLayout(bolha)
        conteudo.setContentsMargins(14, 10, 14, 10)
        conteudo.setSpacing(4)

        nome = {"usuario": "Você", "vinc": "V.INC", "erro": "Aviso do V.INC"}[tipo]
        remetente = QLabel(nome)
        remetente.setObjectName("remetente_conversa")
        conteudo.addWidget(remetente)

        mensagem = QLabel(texto)
        mensagem.setObjectName("texto_conversa")
        mensagem.setTextFormat(Qt.PlainText)
        mensagem.setWordWrap(True)
        mensagem.setTextInteractionFlags(
            Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard
        )
        mensagem.setAccessibleName(f"{nome}: {texto}")
        conteudo.addWidget(mensagem)

        if tipo == "usuario":
            linha_layout.addStretch(1)
            linha_layout.addWidget(bolha)
        else:
            linha_layout.addWidget(bolha)
            linha_layout.addStretch(1)

        self.layout_mensagens.insertWidget(self.layout_mensagens.count() - 1, linha)
        self._linhas.append(linha)
        if len(self._linhas) > self.LIMITE_MENSAGENS:
            antiga = self._linhas.popleft()
            self.layout_mensagens.removeWidget(antiga)
            antiga.deleteLater()

        QTimer.singleShot(0, self._ir_para_ultima_mensagem)

    def _ir_para_ultima_mensagem(self):
        barra = self.scroll.verticalScrollBar()
        barra.setValue(barra.maximum())

    def limpar(self):
        while self._linhas:
            linha = self._linhas.popleft()
            self.layout_mensagens.removeWidget(linha)
            linha.deleteLater()
        self.aviso_vazio.show()
