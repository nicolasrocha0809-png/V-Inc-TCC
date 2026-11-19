"""
Testes unitários do PrefsManager (interface/prefs_manager.py).

O PrefsManager guarda as preferências de acessibilidade (tema, fonte, idioma,
volume e velocidade da voz) em dois lugares:
  - no arquivo local ~/.v-inc/settings.json, pelo objeto `settings` do config.py;
  - no banco Supabase, na tabela "configuracoes".

Num teste unitário queremos testar SÓ a regra do PrefsManager, então trocamos
essas duas dependências por DUBLÊS DE TESTE (test doubles):

  MOCK  o cliente do Supabase (MagicMock). Ele aceita qualquer chamada e guarda
        tudo o que recebeu; no fim, o teste VERIFICA essas chamadas
        ("o upsert foi chamado 1 vez, com estes dados?").
  STUB  um Supabase que só devolve uma resposta pronta para o select
        ("a conta u1 tem tema contraste"). O teste usa a resposta e pronto.
  FAKE  o SettingsFake: uma versão do settings que funciona de verdade,
        mas guarda tudo na memória em vez de gravar em arquivo.

Assim os testes rodam em milissegundos, sem internet, sem as chaves do Supabase
e sem mexer nas configurações de quem está rodando.

Cada teste segue o padrão Preparar -> Agir -> Verificar (Arrange-Act-Assert).
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from interface import prefs_manager
from interface.prefs_manager import PrefsManager


class SettingsFake:
    """FAKE do `settings` do config.py: mesmos métodos, tudo guardado na memória."""

    def __init__(self):
        self.dados = {}

    def get(self, categoria, chave):
        return self.dados.get(categoria, {}).get(chave)

    def set(self, categoria, chave, valor):
        self.dados.setdefault(categoria, {})[chave] = valor

    def set_many(self, atualizacoes):
        for categoria, chave, valor in atualizacoes:
            self.set(categoria, chave, valor)


@pytest.fixture
def settings_fake(monkeypatch):
    """Troca o `settings` usado pelo PrefsManager pelo fake, só durante o teste."""
    fake = SettingsFake()
    monkeypatch.setattr(prefs_manager, "settings", fake)
    return fake


@pytest.fixture
def supabase():
    """MOCK do cliente do Supabase.

    Aceita chamadas em cadeia, como supabase.table("configuracoes").upsert(dados).execute(),
    e registra cada uma para o teste conferir depois.
    """
    return MagicMock()


def criar_stub_supabase(linhas):
    """STUB do Supabase: o select sempre responde com as linhas informadas."""
    stub = MagicMock()
    consulta = stub.table.return_value.select.return_value.eq.return_value
    consulta.execute.return_value = SimpleNamespace(data=linhas)
    return stub


def dados_enviados(supabase):
    """O dicionário que o PrefsManager mandou no upsert do Supabase."""
    return supabase.table.return_value.upsert.call_args.args[0]


class TestComportamentoAtual:
    """Testes de caracterização: descrevem como o PrefsManager já funcionava.

    Passaram de primeira. Eles servem de rede de segurança: se uma mudança
    quebrar algo que já funcionava, um destes testes fica vermelho.
    """

    def test_salvar_varias_preferencias_sincroniza_uma_vez_so(self, supabase, settings_fake):
        # Preparar
        prefs = PrefsManager(supabase, user_id="u1")

        # Agir
        resultado = prefs.salvar({"tema": "claro", "volume": 50})

        # Verificar (MOCK): um único upsert, na tabela certa, com os dados certos
        supabase.table.assert_called_once_with("configuracoes")
        supabase.table.return_value.upsert.assert_called_once_with(
            {
                "user_id": "u1",
                "tema": "claro",
                "fonte": "12px",
                "idioma": "pt_BR",
                "volume": 50,
                "velocidade": 80,
            }
        )
        assert resultado is True
        # Verificar (FAKE): o valor também ficou salvo no computador
        assert settings_fake.get("visual", "tema") == "claro"

    def test_preferencia_desconhecida_da_erro_e_nada_e_salvo(self, supabase, settings_fake):
        prefs = PrefsManager(supabase, user_id="u1")

        with pytest.raises(ValueError, match="Preferência desconhecida"):
            prefs.salvar({"tema": "claro", "cor_do_cursor": "azul"})

        # MOCK: nada foi enviado ao banco. FAKE: nada foi salvo no computador.
        supabase.table.assert_not_called()
        assert settings_fake.dados == {}

    def test_salvar_preferencia_desconhecida_tambem_da_erro(self, supabase, settings_fake):
        prefs = PrefsManager(supabase, user_id="u1")

        with pytest.raises(ValueError, match="Preferência desconhecida"):
            prefs.salvar_preferencia("cor_do_cursor", "azul")

        supabase.table.assert_not_called()

    def test_sem_usuario_logado_nao_chama_o_supabase(self, supabase, settings_fake):
        prefs = PrefsManager(supabase, user_id=None)

        resultado = prefs.salvar_preferencia("tema", "contraste")

        assert resultado is None
        supabase.table.assert_not_called()
        # sem login, a preferência fica só no computador
        assert settings_fake.get("visual", "tema") == "contraste"

    def test_erro_no_supabase_devolve_false(self, supabase, settings_fake):
        # Preparar: o mock simula o banco fora do ar
        supabase.table.return_value.upsert.return_value.execute.side_effect = Exception(
            "sem internet"
        )
        prefs = PrefsManager(supabase, user_id="u1")

        resultado = prefs.salvar({"tema": "claro"})

        assert resultado is False
        assert settings_fake.get("visual", "tema") == "claro"  # o local continua salvo

    def test_carregar_do_supabase_aplica_as_preferencias_do_banco(self, settings_fake):
        # Preparar (STUB): o banco "responde" com as preferências da conta
        supabase = criar_stub_supabase(
            [
                {
                    "id": 7,
                    "user_id": "u1",
                    "tema": "contraste",
                    "fonte": "16px",
                    "idioma": "es_ES",
                    "volume": 40,
                    "velocidade": 60,
                }
            ]
        )
        prefs = PrefsManager(supabase, user_id="u1")

        # Agir
        resultado = prefs.carregar_do_supabase()

        # Verificar: as preferências chegaram e foram salvas no computador
        assert resultado["tema"] == "contraste"
        assert resultado["volume"] == 40
        # colunas que não são preferências (id, user_id) não vão para o arquivo local
        assert settings_fake.dados == {
            "visual": {"tema": "contraste", "fonte": "16px"},
            "geral": {"idioma": "es_ES"},
            "audio": {"volume": 40, "velocidade": 60},
        }

    def test_conta_sem_preferencias_no_banco_devolve_none(self, settings_fake):
        supabase = criar_stub_supabase([])  # STUB: nenhuma linha na tabela

        assert PrefsManager(supabase, user_id="u1").carregar_do_supabase() is None

    def test_carregar_do_supabase_sem_usuario_nao_consulta_o_banco(self, supabase, settings_fake):
        assert PrefsManager(supabase, user_id=None).carregar_do_supabase() is None
        supabase.table.assert_not_called()

    def test_carregar_do_supabase_com_banco_fora_do_ar_devolve_none(self, supabase, settings_fake):
        supabase.table.side_effect = Exception("sem internet")

        assert PrefsManager(supabase, user_id="u1").carregar_do_supabase() is None


class TestVolumeZero:
    """Bug encontrado por um teste de valor-limite: o volume 0 virava 80.

    O código usava `settings.get("audio", "volume") or 80`. No Python, o 0 conta
    como "falso", então `0 or 80` dá 80: o volume no mudo era trocado pelo padrão.
    """

    def test_volume_zero_chega_como_zero_ao_supabase(self, supabase, settings_fake):
        # Preparar
        prefs = PrefsManager(supabase, user_id="u1")

        # Agir: o usuário arrasta o slider de volume até o 0
        prefs.salvar({"volume": 0})

        # Verificar (MOCK): o que foi enviado ao banco
        assert dados_enviados(supabase)["volume"] == 0

    def test_volume_zero_vindo_do_banco_continua_zero(self, settings_fake):
        # Preparar (STUB): no banco, o volume desta conta é 0
        supabase = criar_stub_supabase([{"user_id": "u1", "volume": 0}])
        prefs = PrefsManager(supabase, user_id="u1")

        # Agir
        resultado = prefs.carregar_do_supabase()

        # Verificar
        assert resultado["volume"] == 0
