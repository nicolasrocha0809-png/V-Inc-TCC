import re

from PySide6.QtCore import QTime, Qt, Slot
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from interface.acessibilidade import anunciar


class TerminalScreen(QWidget):
    """Exibe a atividade pública do assistente sem depender do console."""

    PREFIXOS_OCULTOS = (
        "debug:",
        "pygame ",
        "hello from the pygame",
        "a ia decidiu fazer a ação:",
        "limite de energia:",
        "canal resolvido:",
        "direct use of automatic function calling",
    )

    PREFIXOS_SISTEMA = (
        "iniciando o v-inc",
        "calibrando o microfone",
        "assistente ativo e ouvindo",
        "processando áudio",
        "aguardando wake word",
        "candidato de wake word",
        "wake word confirmada",
        "wake word rejeitada",
        "nenhuma fala foi detectada",
        "não foi possível escutar",
        "encerrando",
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        self._ultima_linha = None
        self._montar_interface()

    def _montar_interface(self):
        self.setObjectName("pagina_terminal")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 32, 40, 32)
        layout.setSpacing(16)

        rotulo = QLabel("ACOMPANHAMENTO EM TEMPO REAL")
        rotulo.setObjectName("rotulo_pagina")

        titulo = QLabel("Atividade do assistente")
        titulo.setObjectName("titulo_pagina")

        subtitulo = QLabel(
            "Acompanhe os comandos reconhecidos, o processamento e as "
            "respostas do V.INC sem abrir um terminal externo."
        )
        subtitulo.setObjectName("subtitulo_pagina")
        subtitulo.setWordWrap(True)

        layout.addWidget(rotulo)
        layout.addWidget(titulo)
        layout.addWidget(subtitulo)

        card = QFrame()
        card.setObjectName("card_terminal")
        layout_card = QVBoxLayout(card)
        layout_card.setContentsMargins(20, 18, 20, 20)
        layout_card.setSpacing(12)

        cabecalho = QHBoxLayout()
        cabecalho.setSpacing(10)

        self.lbl_estado = QLabel("● Saída em tempo real")
        self.lbl_estado.setObjectName("estado_terminal")
        self.lbl_estado.setAccessibleName("Saída do assistente em tempo real")

        self.btn_copiar = QPushButton("Copiar conteúdo")
        self.btn_copiar.setObjectName("botao_copiar_terminal")
        self.btn_copiar.setCursor(Qt.PointingHandCursor)
        self.btn_copiar.setAccessibleDescription(
            "Copia toda a atividade exibida para a área de transferência."
        )
        self.btn_copiar.clicked.connect(self._copiar_conteudo)

        self.btn_limpar = QPushButton("Limpar tela")
        self.btn_limpar.setObjectName("botao_limpar_terminal")
        self.btn_limpar.setCursor(Qt.PointingHandCursor)
        self.btn_limpar.setAccessibleDescription(
            "Remove da tela as mensagens exibidas até agora."
        )
        self.btn_limpar.clicked.connect(self.limpar)

        cabecalho.addWidget(self.lbl_estado)
        cabecalho.addStretch()
        cabecalho.addWidget(self.btn_copiar)
        cabecalho.addWidget(self.btn_limpar)
        layout_card.addLayout(cabecalho)

        self.saida = QPlainTextEdit()
        self.saida.setObjectName("saida_terminal")
        self.saida.setReadOnly(True)
        self.saida.setLineWrapMode(QPlainTextEdit.WidgetWidth)
        self.saida.document().setMaximumBlockCount(1000)
        self.saida.setAccessibleName("Atividade do assistente")
        self.saida.setAccessibleDescription(
            "Registro em ordem cronológica dos comandos e respostas do V.INC."
        )
        self.saida.setPlaceholderText(
            "Inicie o assistente na tela Início. A atividade aparecerá aqui."
        )
        layout_card.addWidget(self.saida, 1)

        layout.addWidget(card, 1)

    @Slot(str)
    def adicionar_saida(self, texto):
        for linha in texto.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
            linha = self._limpar_linha(linha)

            if not linha or linha == self._ultima_linha:
                continue

            self._ultima_linha = linha
            horario = QTime.currentTime().toString("HH:mm:ss")
            autor, conteudo = self._classificar_linha(linha)
            self.saida.appendPlainText(f"[{horario}] {autor} — {conteudo}")

        cursor = self.saida.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.saida.setTextCursor(cursor)
        self.saida.ensureCursorVisible()

    @classmethod
    def _limpar_linha(cls, linha):
        linha = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", linha).strip()
        linha_normalizada = linha.casefold()

        if any(linha_normalizada.startswith(prefixo) for prefixo in cls.PREFIXOS_OCULTOS):
            return ""

        return linha

    @classmethod
    def _classificar_linha(cls, linha):
        texto_normalizado = linha.casefold()

        if texto_normalizado.startswith("você disse:"):
            return "VOCÊ", linha.split(":", 1)[1].strip()

        if any(texto_normalizado.startswith(prefixo) for prefixo in cls.PREFIXOS_SISTEMA):
            return "SISTEMA", linha

        return "V.INC", linha

    @Slot()
    def limpar(self):
        self.saida.clear()
        self._ultima_linha = None
        anunciar(self.btn_limpar, "Atividade do assistente limpa.")

    @Slot()
    def _copiar_conteudo(self):
        conteudo = self.saida.toPlainText()

        if not conteudo:
            anunciar(self.btn_copiar, "Não há atividade para copiar.")
            return

        QApplication.clipboard().setText(conteudo)
        anunciar(self.btn_copiar, "Atividade copiada.")
