"""Testes unitários de servicos/preferencias.py."""
import pytest

from servicos.preferencias import valor_ou_padrao


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [
        (None, 80),  # nada salvo ainda: usa o padrão
        (0, 0),  # valor-limite: 0 é uma escolha válida (volume mudo)
        (1, 1),
        (100, 100),  # valor-limite: o máximo do slider
    ],
)
def test_valor_ou_padrao_so_usa_o_padrao_quando_nao_ha_valor(valor, esperado):
    assert valor_ou_padrao(valor, 80) == esperado
