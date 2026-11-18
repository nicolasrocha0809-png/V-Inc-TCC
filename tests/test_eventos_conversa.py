"""Testes do protocolo de eventos (sem depender do Qt ou das APIs)."""

import unittest

from servicos.eventos import formatar_evento, interpretar_evento


class TestarEventosConversa(unittest.TestCase):
    def test_usuario_e_assistente(self):
        for tipo in ("usuario", "vinc", "erro"):
            linha = formatar_evento(tipo, "Olá, V.INC!")
            self.assertEqual(
                interpretar_evento(linha),
                {"tipo": tipo, "texto": "Olá, V.INC!"},
            )

    def test_conteudo_com_quebras_e_simbolos(self):
        texto = 'Linha 1\nLinha 2: <script> & "teste"'
        self.assertEqual(
            interpretar_evento(formatar_evento("usuario", texto))["texto"],
            texto,
        )

    def test_ignora_logs_tecnicos(self):
        self.assertIsNone(interpretar_evento("DEBUG: salvou no Supabase"))
        self.assertIsNone(interpretar_evento("Erro no edge-tts: 403"))
        self.assertIsNone(interpretar_evento("VINC_EVENT:{json inválido}"))
        self.assertIsNone(interpretar_evento('VINC_EVENT:{"tipo":"debug","texto":"x"}'))

    def test_rejeita_tipo_desconhecido(self):
        with self.assertRaises(ValueError):
            formatar_evento("debug", "não mostrar")


if __name__ == "__main__":
    unittest.main()
