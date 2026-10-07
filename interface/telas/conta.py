import bcrypt

from PySide6.QtCore import (
    QAbstractAnimation,
    QEasingCurve,
    QPropertyAnimation,
    QTimer,
    Qt,
)
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from config import settings
from interface.acessibilidade import atualizar_status


class ScrollConta(QScrollArea):
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
        destino_base = (
            self._destino_scroll
            if self._animacao_scroll.state()
            == QAbstractAnimation.State.Running
            else barra.value()
        )
        self._destino_scroll = max(
            barra.minimum(),
            min(barra.maximum(), destino_base + deslocamento),
        )

        self._animacao_scroll.stop()
        self._animacao_scroll.setStartValue(barra.value())
        self._animacao_scroll.setEndValue(self._destino_scroll)
        self._animacao_scroll.start()
        event.accept()


class ContaScreen(QWidget):
    def __init__(
        self,
        supabase_client=None,
        user_id=None,
        email=None,
        callback_logout=None,
        parent=None,
    ):
        super().__init__(parent)
        self.supabase = supabase_client
        self.user_id = user_id
        self.email = email or settings.get("usuario", "email_usuario_atual")
        self.callback_logout = callback_logout
        self._alterando_senha = False

        self.setObjectName("pagina_conta")

        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)

        scroll = ScrollConta()
        scroll.setObjectName("scroll_conta")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        conteudo = QWidget()
        conteudo.setObjectName("conteudo_conta")
        scroll.setWidget(conteudo)

        layout = QVBoxLayout(conteudo)
        layout.setContentsMargins(40, 32, 48, 32)
        layout.setSpacing(20)

        rotulo = QLabel("CONTA")
        rotulo.setObjectName("rotulo_pagina")

        titulo = QLabel("Minha conta")
        titulo.setObjectName("titulo_pagina")

        subtitulo = QLabel(
            "Consulte seus dados, proteja o acesso ao V.INC ou encerre a sessão."
        )
        subtitulo.setObjectName("subtitulo_pagina")
        subtitulo.setWordWrap(True)

        layout.addWidget(rotulo)
        layout.addWidget(titulo)
        layout.addWidget(subtitulo)

        layout.addWidget(self._criar_card_identidade())
        layout.addWidget(self._criar_card_senha())
        layout.addWidget(self._criar_card_conta())
        layout.addStretch()

        layout_principal.addWidget(scroll)

    def _criar_card_identidade(self):
        card, layout = self._criar_card(
            "Perfil",
            "Esta é a conta conectada neste computador.",
        )

        rotulo_email = QLabel("E-mail")
        rotulo_email.setObjectName("label_conta")

        self.lbl_email = QLabel(self.email or "E-mail não disponível")
        self.lbl_email.setObjectName("email_conta")
        self.lbl_email.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.lbl_email.setAccessibleName("E-mail da conta conectada")

        layout.addWidget(rotulo_email)
        layout.addWidget(self.lbl_email)

        self.btn_sair = QPushButton("Sair da conta")
        self.btn_sair.setObjectName("botao_sair_conta")
        self.btn_sair.setCursor(Qt.PointingHandCursor)
        self.btn_sair.setAccessibleDescription(
            "Encerra a sessão salva neste computador e volta para o login."
        )
        self.btn_sair.clicked.connect(self.sair_da_conta)
        layout.addWidget(self.btn_sair, alignment=Qt.AlignLeft)

        return card

    def _criar_card_senha(self):
        card, layout = self._criar_card(
            "Alterar senha",
            "Confirme sua senha atual antes de definir uma nova.",
        )

        grupo_senha_atual, self.txt_senha_atual = self._criar_campo_senha(
            "Senha atual",
            "Digite sua senha atual",
        )
        grupo_nova_senha, self.txt_nova_senha = self._criar_campo_senha(
            "Nova senha",
            "Use pelo menos 8 caracteres",
        )
        grupo_confirmar_senha, self.txt_confirmar_senha = self._criar_campo_senha(
            "Confirmar nova senha",
            "Digite novamente a nova senha",
        )

        for grupo in (
            grupo_senha_atual,
            grupo_nova_senha,
            grupo_confirmar_senha,
        ):
            layout.addWidget(grupo)

        self.lbl_status_senha = QLabel("")
        self.lbl_status_senha.setObjectName("status_conta")
        self.lbl_status_senha.setWordWrap(True)
        self.lbl_status_senha.setAccessibleName("Resultado da alteração de senha")

        self.btn_alterar_senha = QPushButton("Salvar nova senha")
        self.btn_alterar_senha.setObjectName("botao_primario_conta")
        self.btn_alterar_senha.setCursor(Qt.PointingHandCursor)
        self.btn_alterar_senha.clicked.connect(self.alterar_senha)

        layout.addWidget(self.lbl_status_senha)
        layout.addWidget(self.btn_alterar_senha, alignment=Qt.AlignRight)
        return card

    def _criar_card_conta(self):
        card, layout = self._criar_card(
            "Excluir conta",
            "Esta ação remove permanentemente a conta, as preferências online "
            "e todo o histórico de comandos.",
        )
        card.setObjectName("card_perigo_conta")

        grupo_senha_exclusao, self.txt_senha_exclusao = self._criar_campo_senha(
            "Senha atual",
            "Confirme sua senha para excluir a conta",
        )
        layout.addWidget(grupo_senha_exclusao)

        self.lbl_status_exclusao = QLabel("")
        self.lbl_status_exclusao.setObjectName("status_perigo_conta")
        self.lbl_status_exclusao.setWordWrap(True)

        self.btn_excluir_conta = QPushButton("Excluir minha conta")
        self.btn_excluir_conta.setObjectName("botao_excluir_conta")
        self.btn_excluir_conta.setCursor(Qt.PointingHandCursor)
        self.btn_excluir_conta.setAccessibleDescription(
            "Exclui permanentemente esta conta após confirmar a senha e a ação."
        )
        self.btn_excluir_conta.clicked.connect(self.excluir_conta)

        layout.addWidget(self.lbl_status_exclusao)
        layout.addWidget(self.btn_excluir_conta, alignment=Qt.AlignRight)
        return card

    @staticmethod
    def _criar_card(titulo, descricao):
        card = QFrame()
        card.setObjectName("card_conta")
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 22, 24, 24)
        layout.setSpacing(14)

        lbl_titulo = QLabel(titulo)
        lbl_titulo.setObjectName("titulo_card_conta")

        lbl_descricao = QLabel(descricao)
        lbl_descricao.setObjectName("descricao_card_conta")
        lbl_descricao.setWordWrap(True)

        layout.addWidget(lbl_titulo)
        layout.addWidget(lbl_descricao)
        layout.addSpacing(2)
        return card, layout

    @staticmethod
    def _criar_campo_senha(titulo, placeholder):
        grupo = QFrame()
        grupo.setObjectName("grupo_conta")

        layout = QVBoxLayout(grupo)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        campo = QLineEdit(grupo)
        campo.setObjectName("campo_conta")
        campo.setPlaceholderText(placeholder)
        campo.setEchoMode(QLineEdit.Password)
        campo.setAccessibleName(titulo)

        label = QLabel(titulo, grupo)
        label.setObjectName("label_conta")
        label.setBuddy(campo)

        linha = QHBoxLayout()
        linha.setContentsMargins(0, 0, 0, 0)
        linha.setSpacing(8)
        linha.addWidget(campo, 1)

        botao = QPushButton("Mostrar")
        botao.setObjectName("botao_mostrar_senha_conta")
        botao.setCheckable(True)
        botao.setCursor(Qt.PointingHandCursor)
        botao.setAccessibleName(f"Mostrar {titulo.lower()}")

        def alternar_visibilidade(mostrar):
            campo.setEchoMode(QLineEdit.Normal if mostrar else QLineEdit.Password)
            botao.setText("Ocultar" if mostrar else "Mostrar")

        botao.toggled.connect(alternar_visibilidade)
        linha.addWidget(botao)

        layout.addWidget(label)
        layout.addLayout(linha)
        return grupo, campo

    def sair_da_conta(self):
        if not self._confirmar(
            "Sair da conta",
            "Deseja encerrar a sessão neste computador?",
            "Sair",
        ):
            return

        if self.callback_logout:
            self.callback_logout()

    def alterar_senha(self):
        if self._alterando_senha:
            return

        senha_atual = self.txt_senha_atual.text()
        nova_senha = self.txt_nova_senha.text()
        confirmacao = self.txt_confirmar_senha.text()

        if not senha_atual or not nova_senha or not confirmacao:
            self._mostrar_status_senha("Preencha os três campos de senha.", erro=True)
            return

        if len(nova_senha) < 8:
            self._mostrar_status_senha(
                "A nova senha deve ter pelo menos 8 caracteres.",
                erro=True,
            )
            return

        if nova_senha != confirmacao:
            self._mostrar_status_senha("As novas senhas não coincidem.", erro=True)
            return

        if senha_atual == nova_senha:
            self._mostrar_status_senha(
                "A nova senha deve ser diferente da senha atual.",
                erro=True,
            )
            return

        self._alterando_senha = True
        self.btn_alterar_senha.setEnabled(False)
        self.btn_alterar_senha.setText("Salvando...")

        try:
            usuario = self._obter_usuario()

            if not self._senha_confere(senha_atual, usuario):
                self._mostrar_status_senha("A senha atual está incorreta.", erro=True)
                return

            novo_hash = bcrypt.hashpw(
                nova_senha.encode("utf-8"),
                bcrypt.gensalt(),
            ).decode("utf-8")

            (
                self.supabase.table("usuarios")
                .update({"senha_hash": novo_hash})
                .eq("id", self.user_id)
                .execute()
            )

            self.txt_senha_atual.clear()
            self.txt_nova_senha.clear()
            self.txt_confirmar_senha.clear()
            self._mostrar_status_senha("Senha alterada com sucesso.")

        except Exception as erro:
            print(f"Erro ao alterar senha: {erro}")
            self._mostrar_status_senha(
                "Não foi possível alterar a senha neste momento.",
                erro=True,
            )

        finally:
            QTimer.singleShot(700, self._liberar_alteracao_senha)

    def _liberar_alteracao_senha(self):
        self._alterando_senha = False
        self.btn_alterar_senha.setEnabled(True)
        self.btn_alterar_senha.setText("Salvar nova senha")

    def excluir_conta(self):
        senha = self.txt_senha_exclusao.text()

        if not senha:
            self._mostrar_status_exclusao(
                "Informe sua senha atual para continuar.",
                erro=True,
            )
            return

        if not self._confirmar(
            "Excluir conta permanentemente",
            "A conta, o histórico e as preferências online serão apagados. "
            "Esta ação não pode ser desfeita.",
            "Excluir permanentemente",
            perigoso=True,
        ):
            return

        self.btn_excluir_conta.setEnabled(False)
        self.btn_excluir_conta.setText("Excluindo...")

        try:
            usuario = self._obter_usuario()

            if not self._senha_confere(senha, usuario):
                self._mostrar_status_exclusao(
                    "A senha informada está incorreta.",
                    erro=True,
                )
                return

            (
                self.supabase.table("historico")
                .delete()
                .eq("id_usuario", self.user_id)
                .execute()
            )
            (
                self.supabase.table("configuracoes")
                .delete()
                .eq("user_id", self.user_id)
                .execute()
            )
            (
                self.supabase.table("usuarios")
                .delete()
                .eq("id", self.user_id)
                .execute()
            )

            QMessageBox.information(
                self,
                "Conta excluída",
                "Sua conta e os dados associados foram excluídos.",
            )

            if self.callback_logout:
                self.callback_logout()

        except Exception as erro:
            print(f"Erro ao excluir conta: {erro}")
            self._mostrar_status_exclusao(
                "Não foi possível excluir a conta neste momento.",
                erro=True,
            )

        finally:
            self.btn_excluir_conta.setEnabled(True)
            self.btn_excluir_conta.setText("Excluir minha conta")

    def _obter_usuario(self):
        if not self.supabase or not self.user_id:
            raise RuntimeError("Não há uma conta ativa.")

        resposta = (
            self.supabase.table("usuarios")
            .select("id, email, senha_hash")
            .eq("id", self.user_id)
            .limit(1)
            .execute()
        )

        if not resposta.data:
            raise RuntimeError("A conta ativa não foi encontrada.")

        return resposta.data[0]

    @staticmethod
    def _senha_confere(senha, usuario):
        senha_hash = usuario.get("senha_hash") or ""
        return bool(senha_hash) and bcrypt.checkpw(
            senha.encode("utf-8"),
            senha_hash.encode("utf-8"),
        )

    def _mostrar_status_senha(self, mensagem, erro=False):
        self.lbl_status_senha.setProperty("erro", erro)
        self.lbl_status_senha.style().unpolish(self.lbl_status_senha)
        self.lbl_status_senha.style().polish(self.lbl_status_senha)
        atualizar_status(self.lbl_status_senha, mensagem, erro=erro)

    def _mostrar_status_exclusao(self, mensagem, erro=False):
        self.lbl_status_exclusao.setProperty("erro", erro)
        self.lbl_status_exclusao.style().unpolish(self.lbl_status_exclusao)
        self.lbl_status_exclusao.style().polish(self.lbl_status_exclusao)
        atualizar_status(self.lbl_status_exclusao, mensagem, erro=erro)

    def _confirmar(self, titulo, mensagem, texto_confirmar, perigoso=False):
        caixa = QMessageBox(self)
        caixa.setWindowTitle(titulo)
        caixa.setText(mensagem)
        caixa.setIcon(QMessageBox.Warning if perigoso else QMessageBox.Question)

        btn_confirmar = caixa.addButton(texto_confirmar, QMessageBox.AcceptRole)
        btn_cancelar = caixa.addButton("Cancelar", QMessageBox.RejectRole)
        caixa.setDefaultButton(btn_cancelar)
        caixa.exec()

        return caixa.clickedButton() is btn_confirmar
