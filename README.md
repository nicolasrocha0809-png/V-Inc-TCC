# V.INC — Voz Inclusiva

O V.INC é um assistente de voz para Windows desenvolvido com foco em acessibilidade.
O projeto combina interface gráfica, reconhecimento e síntese de voz, execução de
comandos, pesquisa de vídeos, abertura de aplicativos e descrição de imagens.

## Principais recursos

- Interface em PySide6 com temas claro, escuro e alto contraste.
- Reconhecimento de voz usando Whisper pela API da Groq.
- Síntese de voz com Edge TTS e fallback local com pyttsx3.
- Abertura de aplicativos instalados e atalhos do Windows.
- Abertura de PDF/TXT pelo aplicativo padrão, sem leitura pelo assistente.
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
│   ├── arquivos.py
│   ├── imagens.py
│   └── preferencias.py
├── interface/
│   ├── telas/
│   ├── estilos/
│   ├── temas/
│   └── assets/
├── tests/
├── requirements.txt
└── requirements-dev.txt
```

## Abertura de documentos

- "Abra o PDF trabalho" — abre no programa padrão do Windows.
- "Abra o TXT anotações na pasta Documentos" — restringe a busca à pasta indicada.
- A busca considera as pastas Downloads, Documentos e Área de Trabalho.
- Quando mais de um arquivo for encontrado, o assistente pede uma escolha por número.
- O V.INC **não lê o conteúdo** do arquivo. O usuário pode utilizar NVDA ou Narrador.

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

## Testes

Os testes unitários usam **pytest**. Eles não precisam do arquivo `.env`, de internet
nem de microfone: o Supabase e as configurações locais são trocados por dublês de teste.

1. Com o ambiente virtual ativado, instale também as ferramentas de teste:

```powershell
pip install -r requirements.txt -r requirements-dev.txt
```

2. Rode os testes:

```powershell
pytest
```

3. Gere o relatório de cobertura, no terminal e em `htmlcov\index.html`:

```powershell
pytest --cov --cov-report=term --cov-report=html
start htmlcov\index.html
```

| Arquivo | O que testa |
| --- | --- |
| `tests/test_prefs_manager.py` | o `PrefsManager`: salvar e carregar preferências e sincronizar com o Supabase |
| `tests/test_preferencias.py` | a regra `valor_ou_padrao`, que só usa o valor padrão quando não há valor salvo |
| `tests/test_arquivos.py` | a busca de documentos |
| `tests/test_eventos_conversa.py` | os eventos da conversa exibidos na interface |

A cobertura (`.coveragerc`) é medida no `PrefsManager` e em `servicos/preferencias.py`.
As telas e o `voz.py` dependem de interface gráfica, microfone e alto-falante, então
seriam cobertos por testes de integração ou de ponta a ponta.

### Dublês de teste

| Dublê | O que é | Onde aparece |
| --- | --- | --- |
| Mock | registra as chamadas, e o teste confere no final | cliente do Supabase: `upsert.assert_called_once_with(...)` e `assert_not_called()` |
| Stub | só devolve uma resposta pronta | `criar_stub_supabase()`: o select responde com as preferências da conta |
| Fake | versão simplificada que funciona de verdade | `SettingsFake`: o `settings` guardado na memória, sem arquivo |

O `tests/conftest.py` também troca a pasta do usuário por uma pasta temporária, para
os testes nunca mexerem no `~/.v-inc/settings.json` real.

### TDD: o bug do volume 0

Um teste de valor-limite mostrou que o volume 0 virava 80. O código usava
`settings.get("audio", "volume") or 80`, e no Python o 0 conta como "falso", então
`0 or 80` dá 80. Com o slider no zero, o V.INC continuava falando a 80% e mandava 80
para o Supabase. A velocidade 0, que é a voz mais lenta, virava uma voz 45% mais rápida.

A correção seguiu o ciclo Red → Green → Refactor, com um commit por etapa:

```text
test: volume 0 precisa chegar como 0 ao Supabase                 (red: o teste falha)
fix: mantém o volume 0 em vez de trocar por 80                   (green: o teste passa)
refactor: extrai valor_ou_padrao e centraliza os valores padrão  (refactor)
fix: respeita volume e velocidade 0 na fala e nos bipes
```

### Demonstração ao vivo: velocidade 0

A velocidade ainda tem o mesmo bug no `PrefsManager` e fica para ser corrigida na
apresentação. Os dois pontos do código estão marcados com o comentário `DEMO AO VIVO`.

1. **Red.** Em `tests/test_prefs_manager.py`, troque o comentário `DEMO AO VIVO` por
   este teste e rode `pytest`:

    ```python
    def test_velocidade_zero_chega_como_zero_ao_supabase(supabase, settings_fake):
        # Preparar
        prefs = PrefsManager(supabase, user_id="u1")

        # Agir: o usuário arrasta o slider de velocidade até o 0 (a voz mais lenta)
        prefs.salvar({"velocidade": 0})

        # Verificar (MOCK): o que foi enviado ao banco
        assert dados_enviados(supabase)["velocidade"] == 0
    ```

    O teste falha com `assert 80 == 0`.

2. **Green.** Em `interface/prefs_manager.py`, troque o comentário `DEMO AO VIVO` e a
   linha da velocidade logo abaixo dele por:

    ```python
                "velocidade": valor_ou_padrao(
                    settings.get("audio", "velocidade"), self.PADROES["velocidade"]
                ),
    ```

    Rode `pytest` de novo: todos os testes passam.

3. Para voltar ao estado de antes da demo, use `git restore .` ou "Discard all changes"
   no GitHub Desktop.
