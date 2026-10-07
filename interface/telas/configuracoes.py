from PySide6.QtCore import (
    QAbstractAnimation,
    QEasingCurve,
    QPropertyAnimation,
    QTimer,
    Qt,
)
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from config import settings
from interface.audio_devices import listar_dispositivos, nomes_com_padrao
from interface.prefs_manager import PrefsManager
from interface.theme_manager import aplicar_estilo
from interface.acessibilidade import atualizar_status


class ScrollConfiguracoes(QScrollArea):
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


class ConfiguracoesScreen(QWidget):
    TEXTO_SALVAMENTO_AUTOMATICO = (
        "As alterações são aplicadas e salvas automaticamente."
    )

    def __init__(self, parent=None, supabase_client=None, user_id=None):
        super().__init__(parent)
        self.prefs_manager = PrefsManager(supabase_client, user_id)
        self._colunas_atuais = 0
        self._inicializando = True
        self._ultimas_preferencias_salvas = None

        self._timer_salvamento = QTimer(self)
        self._timer_salvamento.setSingleShot(True)
        self._timer_salvamento.setInterval(650)
        self._timer_salvamento.timeout.connect(self._salvar_automaticamente)

        self.setObjectName("pagina_configuracoes")

        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)

        scroll = ScrollConfiguracoes()
        scroll.setObjectName("scroll_configuracoes")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        conteudo = QWidget()
        conteudo.setObjectName("conteudo_configuracoes")
        scroll.setWidget(conteudo)

        layout_conteudo = QVBoxLayout(conteudo)
        layout_conteudo.setContentsMargins(40, 32, 40, 32)
        layout_conteudo.setSpacing(20)

        rotulo = QLabel("PREFERÊNCIAS")
        rotulo.setObjectName("rotulo_pagina")

        titulo = QLabel("Configurações")
        titulo.setObjectName("titulo_pagina")

        subtitulo = QLabel(
            "Personalize a aparência, a voz e os dispositivos usados pelo V.INC."
        )
        subtitulo.setObjectName("subtitulo_pagina")
        subtitulo.setWordWrap(True)

        layout_conteudo.addWidget(rotulo)
        layout_conteudo.addWidget(titulo)
        layout_conteudo.addWidget(subtitulo)

        self.grid_cards = QGridLayout()
        self.grid_cards.setContentsMargins(0, 8, 0, 0)
        self.grid_cards.setHorizontalSpacing(16)
        self.grid_cards.setVerticalSpacing(16)

        self.card_visual = self._criar_card_visual()
        self.card_audio = self._criar_card_audio()
        self.cards = [self.card_visual, self.card_audio]
        layout_conteudo.addLayout(self.grid_cards)

        self.lbl_status = QLabel(self.TEXTO_SALVAMENTO_AUTOMATICO)
        self.lbl_status.setObjectName("status_configuracoes")
        self.lbl_status.setWordWrap(True)
        self.lbl_status.setAccessibleName("Estado do salvamento automático")
        self.lbl_status.setAccessibleDescription(
            "Informa se as preferências foram salvas localmente e sincronizadas."
        )
        layout_conteudo.addWidget(self.lbl_status)
        layout_conteudo.addStretch()

        layout_principal.addWidget(scroll)
        self._organizar_cards(2)
        self._conectar_salvamento_automatico()
        self._ultimas_preferencias_salvas = self._obter_preferencias()
        self._inicializando = False

    def _criar_card_visual(self):
        card, layout = self._criar_card(
            "Aparência e idioma",
            "Defina como o aplicativo e a voz devem ser apresentados.",
        )

        self.combo_tema = self._criar_combo(
            "Tema visual",
            "Escolha as cores usadas na interface.",
        )
        self.combo_tema.addItem("Escuro azul", "escuro")
        self.combo_tema.addItem("Claro", "claro")
        self.combo_tema.addItem("Alto contraste", "contraste")
        self._selecionar_dado(
            self.combo_tema,
            settings.get("visual", "tema") or "escuro",
        )
        layout.addWidget(self._criar_campo("Tema", self.combo_tema))

        self.combo_fonte = self._criar_combo(
            "Tamanho da fonte",
            "Altera o tamanho dos textos em toda a interface.",
        )
        self.combo_fonte.addItem("Pequena — 10 px", "10px")
        self.combo_fonte.addItem("Padrão — 12 px", "12px")
        self.combo_fonte.addItem("Grande — 14 px", "14px")
        self.combo_fonte.addItem("Muito grande — 16 px", "16px")
        self._selecionar_dado(
            self.combo_fonte,
            settings.get("visual", "fonte") or "12px",
        )
        layout.addWidget(self._criar_campo("Tamanho da fonte", self.combo_fonte))

        self.combo_idioma = self._criar_combo(
            "Idioma da voz",
            "Define o idioma do reconhecimento e das respostas faladas.",
        )
        self.combo_idioma.addItem("Português do Brasil", "pt_BR")
        self.combo_idioma.addItem("English — United States", "en_US")
        self.combo_idioma.addItem("Español — España", "es_ES")
        self._selecionar_dado(
            self.combo_idioma,
            settings.get("geral", "idioma") or "pt_BR",
        )
        layout.addWidget(self._criar_campo("Idioma da voz", self.combo_idioma))
        layout.addStretch()

        return card

    def _criar_card_audio(self):
        card, layout = self._criar_card(
            "Áudio e dispositivos",
            "Escolha como o V.INC escuta seus comandos e reproduz as respostas.",
        )

        self.combo_microfone = self._criar_combo(
            "Microfone de entrada",
            "Escolha o microfone usado para ouvir seus comandos.",
        )
        self.combo_saida = self._criar_combo(
            "Saída de áudio",
            "Escolha o dispositivo que reproduzirá a voz do assistente.",
        )
        self._carregar_dispositivos()

        layout.addWidget(
            self._criar_campo("Microfone de entrada", self.combo_microfone)
        )
        layout.addWidget(self._criar_campo("Saída de áudio", self.combo_saida))

        self.lbl_volume_valor = QLabel()
        self.lbl_volume_valor.setObjectName("valor_configuracao")
        self.slider_volume = self._criar_slider(
            int(settings.get("audio", "volume") or 80),
            self.lbl_volume_valor,
            "%",
        )
        layout.addWidget(
            self._criar_campo_slider(
                "Volume das respostas",
                self.slider_volume,
                self.lbl_volume_valor,
            )
        )

        self.lbl_velocidade_valor = QLabel()
        self.lbl_velocidade_valor.setObjectName("valor_configuracao")
        self.slider_velocidade = self._criar_slider(
            int(settings.get("audio", "velocidade") or 80),
            self.lbl_velocidade_valor,
            "%",
        )
        layout.addWidget(
            self._criar_campo_slider(
                "Velocidade da voz",
                self.slider_velocidade,
                self.lbl_velocidade_valor,
            )
        )

        self.btn_atualizar_dispositivos = QPushButton("Atualizar dispositivos")
        self.btn_atualizar_dispositivos.setObjectName(
            "botao_secundario_configuracoes"
        )
        self.btn_atualizar_dispositivos.setCursor(Qt.PointingHandCursor)
        self.btn_atualizar_dispositivos.clicked.connect(
            self._carregar_dispositivos
        )
        layout.addWidget(
            self.btn_atualizar_dispositivos,
            alignment=Qt.AlignRight,
        )

        return card

    @staticmethod
    def _criar_card(titulo, descricao):
        card = QFrame()
        card.setObjectName("card_configuracao")
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(22, 20, 22, 22)
        layout.setSpacing(14)

        lbl_titulo = QLabel(titulo)
        lbl_titulo.setObjectName("titulo_card_configuracao")

        lbl_descricao = QLabel(descricao)
        lbl_descricao.setObjectName("descricao_card_configuracao")
        lbl_descricao.setWordWrap(True)

        layout.addWidget(lbl_titulo)
        layout.addWidget(lbl_descricao)
        layout.addSpacing(4)
        return card, layout

    @staticmethod
    def _criar_combo(nome_acessivel, descricao_acessivel):
        combo = QComboBox()
        combo.setObjectName("campo_configuracao")
        combo.setMinimumHeight(42)
        combo.setAccessibleName(nome_acessivel)
        combo.setAccessibleDescription(descricao_acessivel)
        return combo

    @staticmethod
    def _criar_campo(titulo, controle):
        grupo = QFrame()
        grupo.setObjectName("grupo_configuracao")

        layout = QVBoxLayout(grupo)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        label = QLabel(titulo)
        label.setObjectName("label_configuracao")
        label.setBuddy(controle)

        layout.addWidget(label)
        layout.addWidget(controle)
        return grupo

    @staticmethod
    def _criar_slider(valor, label_valor, sufixo):
        slider = QSlider(Qt.Horizontal)
        slider.setObjectName("slider_configuracao")
        slider.setRange(0, 100)
        slider.setValue(valor)
        slider.valueChanged.connect(
            lambda atual: label_valor.setText(f"{atual}{sufixo}")
        )
        label_valor.setText(f"{valor}{sufixo}")
        return slider

    @staticmethod
    def _criar_campo_slider(titulo, slider, label_valor):
        grupo = QFrame()
        grupo.setObjectName("grupo_configuracao")

        layout = QVBoxLayout(grupo)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        cabecalho = QHBoxLayout()
        label = QLabel(titulo)
        label.setObjectName("label_configuracao")
        label.setBuddy(slider)
        cabecalho.addWidget(label)
        cabecalho.addStretch()
        cabecalho.addWidget(label_valor)

        layout.addLayout(cabecalho)
        layout.addWidget(slider)
        return grupo

    def _carregar_dispositivos(self):
        microfone_anterior = (
            self.combo_microfone.currentText()
            if self.combo_microfone.count()
            else settings.get("audio", "microfone")
        )
        saida_anterior = (
            self.combo_saida.currentText()
            if self.combo_saida.count()
            else settings.get("audio", "saida")
        )

        microfones, saidas = listar_dispositivos()
        self.combo_microfone.clear()
        self.combo_saida.clear()
        self.combo_microfone.addItems(nomes_com_padrao(microfones))
        self.combo_saida.addItems(nomes_com_padrao(saidas))

        self._selecionar_texto(self.combo_microfone, microfone_anterior)
        self._selecionar_texto(self.combo_saida, saida_anterior)

    def _obter_preferencias(self):
        return {
            "tema": self.combo_tema.currentData(),
            "fonte": self.combo_fonte.currentData(),
            "idioma": self.combo_idioma.currentData(),
            "volume": self.slider_volume.value(),
            "velocidade": self.slider_velocidade.value(),
            "microfone": self.combo_microfone.currentText(),
            "saida": self.combo_saida.currentText(),
        }

    def _conectar_salvamento_automatico(self):
        self.combo_tema.currentIndexChanged.connect(
            self._aplicar_aparencia_e_agendar
        )
        self.combo_fonte.currentIndexChanged.connect(
            self._aplicar_aparencia_e_agendar
        )

        for combo in (
            self.combo_idioma,
            self.combo_microfone,
            self.combo_saida,
        ):
            combo.currentIndexChanged.connect(self._agendar_salvamento)

        self.slider_volume.valueChanged.connect(self._agendar_salvamento)
        self.slider_velocidade.valueChanged.connect(self._agendar_salvamento)

    def _aplicar_aparencia_e_agendar(self, _indice=None):
        if self._inicializando:
            return

        controle_focado = QApplication.focusWidget()
        aplicar_estilo(
            self.combo_tema.currentData(),
            self.combo_fonte.currentData(),
        )

        if controle_focado is not None:
            QTimer.singleShot(
                0,
                lambda controle=controle_focado: self._restaurar_foco(controle),
            )

        self._agendar_salvamento()

    @staticmethod
    def _restaurar_foco(controle):
        try:
            controle.setFocus(Qt.OtherFocusReason)
        except RuntimeError:
            pass

    def _agendar_salvamento(self, _valor=None):
        if self._inicializando:
            return

        self._definir_status_silencioso(
            "Salvando alterações automaticamente..."
        )
        self._timer_salvamento.start()

    def _definir_status_silencioso(self, mensagem):
        """Atualiza progresso visual sem repetir anúncios durante ajustes."""
        self.lbl_status.setProperty("erro", False)
        self.lbl_status.style().unpolish(self.lbl_status)
        self.lbl_status.style().polish(self.lbl_status)
        self.lbl_status.setText(mensagem)

    def _salvar_automaticamente(self):
        preferencias = self._obter_preferencias()

        if preferencias == self._ultimas_preferencias_salvas:
            self._definir_status_silencioso(
                self.TEXTO_SALVAMENTO_AUTOMATICO
            )
            return

        try:
            sincronizado = self.prefs_manager.salvar(preferencias)
            self._ultimas_preferencias_salvas = preferencias.copy()

            if sincronizado is False:
                atualizar_status(
                    self.lbl_status,
                    "Alterações salvas neste computador. "
                    "A sincronização online não foi concluída.",
                )
            elif sincronizado is None:
                atualizar_status(
                    self.lbl_status,
                    "Alterações aplicadas e salvas neste computador.",
                )
            else:
                atualizar_status(
                    self.lbl_status,
                    "Alterações aplicadas e salvas.",
                )

        except Exception as erro:
            print(f"Erro ao salvar configurações: {erro}")
            atualizar_status(
                self.lbl_status,
                "Não foi possível salvar as alterações. Tente novamente.",
                erro=True,
            )

    def _organizar_cards(self, colunas):
        if colunas == self._colunas_atuais:
            return

        for coluna in range(max(2, self._colunas_atuais)):
            self.grid_cards.setColumnStretch(coluna, 0)

        while self.grid_cards.count():
            item = self.grid_cards.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        for indice, card in enumerate(self.cards):
            linha = indice // colunas
            coluna = indice % colunas
            self.grid_cards.addWidget(card, linha, coluna)

        for coluna in range(colunas):
            self.grid_cards.setColumnStretch(coluna, 1)

        self._colunas_atuais = colunas

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._organizar_cards(2 if event.size().width() >= 760 else 1)

    @staticmethod
    def _selecionar_dado(combo, dado):
        indice = combo.findData(dado)
        if indice >= 0:
            combo.setCurrentIndex(indice)

    @staticmethod
    def _selecionar_texto(combo, texto):
        if not texto:
            return
        indice = combo.findText(texto)
        if indice >= 0:
            combo.setCurrentIndex(indice)
