"""Regras compartilhadas das preferências de acessibilidade."""


def valor_ou_padrao(valor, padrao):
    """Devolve o padrão só quando não existe valor salvo (None).

    Diferente de `valor or padrao`, que também troca o 0 pelo padrão:
    volume 0 (mudo) e velocidade 0 (a mais lenta) são escolhas válidas.
    """
    if valor is None:
        return padrao
    return valor
