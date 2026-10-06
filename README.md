# V.INC — Voz Inclusiva

O V.INC é um assistente de voz para Windows desenvolvido com foco em acessibilidade.
O projeto combina interface gráfica, reconhecimento e síntese de voz, execução de
comandos, pesquisa de vídeos, abertura de aplicativos e descrição de imagens.

## Principais recursos

- Interface em PySide6 com temas claro, escuro e alto contraste.
- Reconhecimento de voz usando Whisper pela API da Groq.
- Síntese de voz com Edge TTS e fallback local com pyttsx3.
- Abertura de aplicativos instalados e atalhos do Windows.
- Pesquisa de vídeos, canais e lives, com integração à YouTube Data API.
- Descrição de imagens com cadeia de fallback entre serviços de visão.
- Cache persistente para índice e descrições de imagens.
- Histórico de comandos integrado ao Supabase.
- Preferências de áudio, tema, fonte e idioma.

## Estrutura do projeto

```text
V-Inc-TCC/
├── main.py
├── assistente.py
├── config.py
├── servicos/
│   ├── cerebro.py
│   ├── voz.py
│   ├── aplicativos.py
│   └── imagens.py
├── interface/
│   ├── telas/
│   ├── estilos/
│   ├── temas/
│   └── assets/
└── requirements.txt
```

## Como executar

1. Clone o repositório.
2. Crie e ative um ambiente virtual:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. Instale as dependências:

```powershell
pip install -r requirements.txt
```

4. Crie um arquivo `.env` na raiz e configure as credenciais usadas pelo projeto.

```env
CHAVE_GROQ=
YOUTUBE_API_KEY=
SUPABASE_URL=
SUPABASE_KEY=
GEMINI_API_KEY=
GEMINI_MODEL=gemini-3.6-flash
GEMINI_FALLBACK_MODEL=gemini-3.1-flash-lite
OPENROUTER_API_KEY=
CLOUDFLARE_ACCOUNT_ID=
CLOUDFLARE_AUTH_TOKEN=
```

5. Inicie a interface:

```powershell
python .\main.py
```

Para executar diretamente o assistente de voz:

```powershell
python .\assistente.py
```
