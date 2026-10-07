from PySide6.QtCore import QAbstractAnimation, QEasingCurve, QPropertyAnimation, Qt
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from interface.acessibilidade import anunciar


FAQS = (
    (
        "O que é o V.INC?",
        "O V.INC — Voz Inclusiva é um assistente para computador criado com "
        "foco em acessibilidade. Ele permite executar tarefas por voz, como "
        "abrir aplicativos, pesquisar conteúdos, fazer cálculos e descrever "
        "imagens armazenadas no computador.",
    ),
    (
        "Como iniciar e usar os comandos de voz?",
        "Na tela Início, confirme o microfone e a saída de áudio e selecione "
        "Iniciar Assistente. Aguarde a calibração em silêncio. Enquanto a "
        "ativação por palavra-chave ainda não estiver disponível, fale sempre "
        "depois do sinal sonoro que indica que o V.INC está pronto para ouvir. "
        "Você pode consultar exemplos completos na tela Comandos.",
    ),
    (
        "O que significam os sinais sonoros?",
        "Ao iniciar o assistente, dois tons confirmam que ele foi ativado. "
        "Um sinal curto e mais agudo indica que você já pode falar. Depois "
        "da sua fala, outro sinal curto indica que o comando foi recebido "
        "e está sendo processado. Tons mais graves indicam erro ou encerramento.",
    ),
    (
        "O que fazer se o microfone não for reconhecido?",
        "Abra Configurações, selecione o microfone correto e use Atualizar "
        "dispositivos caso ele tenha sido conectado depois que o programa "
        "abriu. Verifique também as permissões de microfone do Windows. "
        "Durante a calibração, permaneça em silêncio por alguns segundos.",
    ),
    (
        "Por que um aplicativo não foi encontrado?",
        "O V.INC procura aplicativos do sistema e atalhos disponíveis no "
        "Menu Iniciar e na Área de Trabalho. Programas sem atalho nesses "
        "locais podem não ser encontrados. Quando houver nomes parecidos, "
        "o assistente solicitará que você escolha uma das opções.",
    ),
    (
        "Onde o V.INC procura imagens?",
        "A busca considera Downloads, Documentos, Área de Trabalho e Imagens, "
        "incluindo os caminhos conhecidos pelo Windows e pelo OneDrive. Diga "
        "um nome de arquivo específico quando existirem imagens parecidas. "
        "A geração da descrição visual precisa de conexão com a internet.",
    ),
    (
        "Como alterar tema, fonte, idioma e áudio?",
        "Use a tela Configurações, escolha as preferências desejadas e "
        "selecione Salvar alterações. O tema e a fonte são aplicados "
        "imediatamente. Idioma, volume, velocidade e dispositivos serão "
        "usados nas próximas interações do assistente.",
    ),
    (
        "Como funciona o histórico de comandos?",
        "O histórico mostra os comandos reconhecidos para a conta atual. "
        "Você pode ordenar os registros, excluir apenas um comando ou limpar "
        "todo o histórico. As exclusões solicitam confirmação.",
    ),
    (
        "O V.INC funciona sem internet?",
        "O suporte offline ainda é parcial. Algumas ações no computador e a "
        "voz alternativa podem funcionar localmente, mas o reconhecimento "
        "de fala, a interpretação de comandos e a descrição de imagens ainda "
        "dependem de serviços online.",
    ),
)


class ScrollAjuda(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._destino_scroll = 0
        self._animacao_scroll = QPropertyAnimation(
            self.verticalScrollBar(),
            b"value",
            self,
        )
        self._animacao_scroll.setDuration(180)
        self._animacao_scroll.setEasingCurve(QEasingCurve.OutCubic)
        self.verticalScrollBar().setSingleStep(12)

    def wheelEvent(self, event):
        delta = event.angleDelta().y()

        if not delta:
            super().wheelEvent(event)
            return

        barra = self.verticalScrollBar()
        deslocamento = int(-(delta / 120) * 96)

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


class PerguntaCard(QFrame):
    def __init__(self, pergunta, resposta, parent=None):
        super().__init__(parent)
        self.pergunta = pergunta
        self.setObjectName("card_pergunta")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.botao = QPushButton()
        self.botao.setObjectName("botao_pergunta")
        self.botao.setCheckable(True)
        self.botao.setCursor(Qt.PointingHandCursor)
        self.botao.setAccessibleName(pergunta)
        self.botao.setAccessibleDescription("Expande ou recolhe a resposta.")
        self.botao.toggled.connect(self._alternar_resposta)

        self.resposta = QLabel(resposta)
        self.resposta.setObjectName("resposta_pergunta")
        self.resposta.setWordWrap(True)
        self.resposta.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.resposta.hide()

        layout.addWidget(self.botao)
        layout.addWidget(self.resposta)
        self._atualizar_texto_botao(False)

    def _alternar_resposta(self, expandida):
        self.resposta.setVisible(expandida)
        self._atualizar_texto_botao(expandida)

    def _atualizar_texto_botao(self, expandida):
        indicador = "−" if expandida else "+"
        self.botao.setText(f"{self.pergunta}    {indicador}")


class AjudaScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("pagina_ajuda")

        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)

        self.scroll = ScrollAjuda()
        self.scroll.setObjectName("scroll_ajuda")
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        conteudo = QWidget()
        conteudo.setObjectName("conteudo_ajuda")
        self.scroll.setWidget(conteudo)

        layout = QVBoxLayout(conteudo)
        layout.setContentsMargins(40, 32, 68, 32)
        layout.setSpacing(16)

        rotulo = QLabel("CENTRAL DE AJUDA")
        rotulo.setObjectName("rotulo_pagina")

        titulo = QLabel("Como podemos ajudar?")
        titulo.setObjectName("titulo_pagina")

        subtitulo = QLabel(
            "Encontre respostas rápidas e acesse as principais áreas do V.INC."
        )
        subtitulo.setObjectName("subtitulo_pagina")
        subtitulo.setWordWrap(True)

        layout.addWidget(rotulo)
        layout.addWidget(titulo)
        layout.addWidget(subtitulo)
        layout.addSpacing(6)

        atalhos = QHBoxLayout()
        atalhos.setSpacing(12)

        btn_comandos = QPushButton("Ver comandos disponíveis")
        btn_comandos.setObjectName("botao_atalho_ajuda")
        btn_comandos.setCursor(Qt.PointingHandCursor)
        btn_comandos.clicked.connect(lambda: self._mudar_tela(3))

        btn_configuracoes = QPushButton("Abrir configurações")
        btn_configuracoes.setObjectName("botao_atalho_ajuda")
        btn_configuracoes.setCursor(Qt.PointingHandCursor)
        btn_configuracoes.clicked.connect(lambda: self._mudar_tela(5))

        atalhos.addWidget(btn_comandos)
        atalhos.addWidget(btn_configuracoes)
        atalhos.addStretch()
        layout.addLayout(atalhos)
        layout.addSpacing(12)

        titulo_faq = QLabel("DÚVIDAS FREQUENTES")
        titulo_faq.setObjectName("rotulo_pagina")
        layout.addWidget(titulo_faq)

        for pergunta, resposta in FAQS:
            layout.addWidget(PerguntaCard(pergunta, resposta))

        layout.addSpacing(8)
        layout.addWidget(self._criar_card_suporte())
        layout.addStretch()

        layout_principal.addWidget(self.scroll)

    def _criar_card_suporte(self):
        card = QFrame()
        card.setObjectName("card_suporte")

        layout = QHBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(16)

        textos = QVBoxLayout()
        textos.setSpacing(5)

        titulo = QLabel("Ainda precisa de ajuda?")
        titulo.setObjectName("titulo_suporte")

        email = QLabel("Entre em contato: vinc.suporte@gmail.com")
        email.setObjectName("texto_suporte")
        email.setTextInteractionFlags(Qt.TextSelectableByMouse)

        textos.addWidget(titulo)
        textos.addWidget(email)

        btn_copiar = QPushButton("Copiar e-mail")
        btn_copiar.setObjectName("botao_copiar_suporte")
        btn_copiar.setCursor(Qt.PointingHandCursor)
        btn_copiar.clicked.connect(lambda: self._copiar_email(btn_copiar))

        layout.addLayout(textos, 1)
        layout.addWidget(btn_copiar, alignment=Qt.AlignVCenter)
        return card

    @staticmethod
    def _copiar_email(botao):
        QApplication.clipboard().setText("vinc.suporte@gmail.com")
        anunciar(botao, "E-mail de suporte copiado.")

    def _mudar_tela(self, indice):
        janela = self.window()
        if hasattr(janela, "mudar_tela"):
            janela.mudar_tela(indice)
