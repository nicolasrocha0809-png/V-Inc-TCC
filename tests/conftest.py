"""
Configuração compartilhada dos testes. O pytest carrega este arquivo antes dos testes.

O config.py cria e lê o arquivo ~/.v-inc/settings.json assim que é importado.
Para os testes nunca mexerem nas configurações reais de quem está rodando,
a pasta do usuário vira uma pasta temporária antes de qualquer import do app.
"""
import os
import tempfile

_pasta_do_usuario_nos_testes = tempfile.mkdtemp(prefix="vinc-testes-")
os.environ["HOME"] = _pasta_do_usuario_nos_testes  # Linux e macOS
os.environ["USERPROFILE"] = _pasta_do_usuario_nos_testes  # Windows
