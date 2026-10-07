"""Utilitários para leitores de tela e operação integral pelo teclado."""

from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtGui import QAccessible, QAccessibleAnnouncementEvent
from PySide6.QtWidgets import QAbstractButton, QSlider


class FiltroAtivacaoTeclado(QObject):
    """Permite acionar qualquer botão usando Enter, além de Espaço."""

    def eventFilter(self, objeto, evento):
        if isinstance(objeto, QSlider) and evento.type() in (
            QEvent.FocusIn,
            QEvent.FocusOut,
        ):
            objeto.setProperty(
                "focoTeclado",
                evento.type() == QEvent.FocusIn,
            )
            objeto.style().unpolish(objeto)
            objeto.style().polish(objeto)
            objeto.update()

        if (
            isinstance(objeto, QAbstractButton)
            and evento.type() == QEvent.KeyPress
            and evento.key() in (Qt.Key_Return, Qt.Key_Enter)
            and not evento.isAutoRepeat()
        ):
            if objeto.isEnabled() and objeto.isVisible():
                objeto.click()
            evento.accept()
            return True

        return super().eventFilter(objeto, evento)


def anunciar(widget, mensagem, assertivo=False):
    """Anuncia uma mensagem sem mover o foco atual do teclado."""
    if not widget or not mensagem:
        return

    evento = QAccessibleAnnouncementEvent(widget, mensagem)

    try:
        nivel = (
            QAccessibleAnnouncementEvent.Politeness.Assertive
            if assertivo
            else QAccessibleAnnouncementEvent.Politeness.Polite
        )
        evento.setPoliteness(nivel)
    except AttributeError:
        # Compatibilidade com versões do PySide6 sem o enum Politeness.
        pass

    QAccessible.updateAccessibility(evento)


def atualizar_status(label, mensagem, erro=False):
    """Atualiza um rótulo de estado e anuncia o resultado ao leitor de tela."""
    if not label:
        return

    label.setProperty("erro", erro)
    label.style().unpolish(label)
    label.style().polish(label)
    label.setText(mensagem)
    label.updateGeometry()

    pai = label.parentWidget()
    if pai is not None and pai.layout() is not None:
        pai.layout().invalidate()
        pai.layout().activate()

    anunciar(label, mensagem, assertivo=erro)
