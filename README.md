# 👁️ V-Inc: Assistente de Voz versão incial de teste

Este repositório contém a versão de desenvolvimento do assistente virtual V-Inc. Ele combina uma interface gráfica de segurança login simples com reconhecimento e síntese de voz para teste inicial

## Funcionalidades
* **Tela de Acesso:** Interface construída em CustomTkinter para autenticação prévia.
* **Reconhecimento de Voz:** Transcrição de áudio usando a API Groq (modelo `whisper-large-v3`).
* **Síntese de Voz:** Respostas geradas usando `edge_tts` (voz realista) com um sistema de segurança (fallback) para `pyttsx3` caso o computador fique offline.
* **Fuções:** Algumas funções foram desativadas para o propósito dessa versão inicial para o teste e reconhecimento da voz

## Como rodar o projeto localmente

1. Faça o clone deste repositório.
2. Crie um ambiente virtual e ative-o:
   `python -m venv .venv`
   `.\.venv\Scripts\Activate.ps1`
3. Instale as dependências:
   `pip requirements.txt`
4. Crie um arquivo `.env` na raiz do projeto com a sua chave da Groq:
   `CHAVE_GROQ=sua_chave_aqui`
5. Execute o sistema:
   `python login.py`