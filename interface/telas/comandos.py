from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


COMANDOS = (
    (
        "APP",
        "Abrir aplicativos",
        "Abra programas instalados no computador usando apenas a voz.",
        'Exemplo: "Abra o Visual Studio Code."',
    ),
    (
        "IMG",
        "Descrever imagens",
        "Localize uma imagem nas pastas do usuário e ouça sua descrição.",
        'Exemplo: "Descreva a imagem montanhas."',
    ),
    (
        "WEB",
        "Pesquisar na internet",
        "Abra sites ou faça pesquisas sobre o assunto solicitado.",
        'Exemplo: "Pesquise quem foi Ada Lovelace."',
    ),
    (
        "PLAY",
        "Encontrar vídeos e lives",
        "Pesquise conteúdo no YouTube, Twitch, Kick e outras plataformas.",
        'Exemplo: "Procure lives de programação na Twitch."',
    ),
    (
        "123",
        "Fazer cálculos",
        "Resolva operações matemáticas simples sem abrir outro aplicativo.",
        'Exemplo: "Quanto é vinte e cinco vezes oito?"',
    ),
    (
        "VOZ",
        "Respostas rápidas",
        "Converse com o assistente e receba respostas curtas em voz alta.",
        'Exemplo: "O que significa acessibilidade?"',
    ),
)


class ComandosScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cards = []
        self.quantidade_colunas = 0
        self._criar_tela()

    def _criar_tela(self):
        layout_externo = QVBoxLayout(self)
        layout_externo.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setObjectName("scroll_pagina")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        layout_externo.addWidget(scroll)

        conteudo = QWidget()
        conteudo.setObjectName("pagina_comandos")
        scroll.setWidget(conteudo)

        self.layout_principal = QVBoxLayout(conteudo)
        self.layout_principal.setContentsMargins(40, 32, 40, 40)
        self.layout_principal.setSpacing(10)

        lbl_secao = QLabel("RECURSOS DE VOZ")
        lbl_secao.setObjectName("rotulo_pagina")
        self.layout_principal.addWidget(lbl_secao)

        lbl_titulo = QLabel("O que você pode pedir")
        lbl_titulo.setObjectName("titulo_pagina")
        self.layout_principal.addWidget(lbl_titulo)

        lbl_subtitulo = QLabel(
            "Fale naturalmente. O V.INC identifica a ação e pede confirmação "
            "quando precisar de mais detalhes."
        )
        lbl_subtitulo.setObjectName("subtitulo_pagina")
        lbl_subtitulo.setWordWrap(True)
        self.layout_principal.addWidget(lbl_subtitulo)
        self.layout_principal.addSpacing(16)

        self.grid = QGridLayout()
        self.grid.setHorizontalSpacing(16)
        self.grid.setVerticalSpacing(16)
        self.layout_principal.addLayout(self.grid)
        self.layout_principal.addStretch()

        for sigla, titulo, descricao, exemplo in COMANDOS:
            self.cards.append(
                self._criar_card(sigla, titulo, descricao, exemplo)
            )

        self._organizar_cards(3)

    def _criar_card(self, sigla, titulo, descricao, exemplo):
        card = QFrame()
        card.setObjectName("card_comando")
        card.setAccessibleName(titulo)
        card.setAccessibleDescription(f"{descricao} {exemplo}")
        card.setMinimumHeight(176)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(8)

        lbl_sigla = QLabel(sigla)
        lbl_sigla.setObjectName("icone_comando")
        lbl_sigla.setAlignment(Qt.AlignCenter)
        lbl_sigla.setFixedSize(54, 34)
        layout.addWidget(lbl_sigla, alignment=Qt.AlignLeft)

        lbl_titulo = QLabel(titulo)
        lbl_titulo.setObjectName("titulo_card_comando")
        layout.addWidget(lbl_titulo)

        lbl_descricao = QLabel(descricao)
        lbl_descricao.setObjectName("descricao_card_comando")
        lbl_descricao.setWordWrap(True)
        layout.addWidget(lbl_descricao)

        layout.addStretch()

        lbl_exemplo = QLabel(exemplo)
        lbl_exemplo.setObjectName("exemplo_comando")
        lbl_exemplo.setWordWrap(True)
        layout.addWidget(lbl_exemplo)

        return card

    def _organizar_cards(self, colunas):
        if colunas == self.quantidade_colunas:
            return

        while self.grid.count():
            self.grid.takeAt(0)

        for indice, card in enumerate(self.cards):
            linha, coluna = divmod(indice, colunas)
            self.grid.addWidget(card, linha, coluna)

        for coluna in range(colunas):
            self.grid.setColumnStretch(coluna, 1)

        self.quantidade_colunas = colunas

    def resizeEvent(self, event):
        super().resizeEvent(event)
        largura = event.size().width()

        if largura >= 850:
            colunas = 3
        elif largura >= 560:
            colunas = 2
        else:
            colunas = 1

        self._organizar_cards(colunas)
