"""Testes de localização de PDF/TXT, independentes das APIs externas."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from servicos.arquivos import abrir_arquivo, localizar_arquivo


class TesteDocumentos(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.pasta = self.base / "Documents"
        self.pasta.mkdir()
        patcher = patch(
            "servicos.arquivos.obter_pastas_de_documentos",
            return_value=[self.base],
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_busca_txt_sem_acentos(self):
        arquivo = self.pasta / "Anotações.txt"
        arquivo.write_text("Teste", encoding="utf-8")
        resultado = localizar_arquivo("anotacoes")
        self.assertEqual(resultado["status"], "encontrado")
        self.assertEqual(resultado["caminho"], arquivo)

    def test_busca_pdf_com_extensao(self):
        (self.pasta / "Trabalho.txt").write_text("Teste")
        pdf = self.pasta / "Trabalho.pdf"
        pdf.write_bytes(b"%PDF-1.4")
        self.assertEqual(localizar_arquivo("trabalho.pdf")["caminho"], pdf)

    def test_pede_escolha_com_nomes_iguais(self):
        (self.pasta / "Trabalho.txt").write_text("Teste")
        (self.pasta / "Trabalho.pdf").write_bytes(b"%PDF-1.4")
        self.assertEqual(localizar_arquivo("trabalho")["status"], "ambiguo")

    def test_pasta_portugues(self):
        arquivo = self.pasta / "Resumo.txt"
        arquivo.write_text("Teste")
        resultado = localizar_arquivo("resumo", pasta_solicitada="Documentos")
        self.assertEqual(resultado["caminho"], arquivo)

    def test_extensao_nao_permitida(self):
        (self.pasta / "Programa.exe").write_bytes(b"")
        self.assertEqual(localizar_arquivo("programa")["status"], "nao_encontrado")
        with self.assertRaises(ValueError):
            abrir_arquivo(self.pasta / "Programa.exe")


if __name__ == "__main__":
    unittest.main()
