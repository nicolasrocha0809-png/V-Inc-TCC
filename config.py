import json
import os


DIRETORIO_DADOS = os.path.join(os.path.expanduser("~"), ".v-inc")
ARQUIVO_CONFIGURACAO = os.path.join(DIRETORIO_DADOS, "settings.json")


class ConfigManager:
    def __init__(self, file_path=None):
        self.file_path = file_path or ARQUIVO_CONFIGURACAO
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        self.settings = self._load_defaults()
        self.load_settings()
        if not os.path.exists(self.file_path):
            self.save_settings()

    def _load_defaults(self):
        return {
            "visual": {"tema": "escuro", "fonte": "12px"},
            "audio": {
                "velocidade": 80,
                "volume": 80,
                "microfone": None,
                "saida": None,
            },
            "geral": {"idioma": "pt_BR"},
            "usuario": {"id_usuario_atual": None}
        }

    def load_settings(self):
        if not os.path.exists(self.file_path):
            return
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                dados_salvos = json.load(f)
            for categoria, valores in dados_salvos.items():
                if categoria in self.settings and isinstance(valores, dict):
                    self.settings[categoria].update(valores)
                else:
                    self.settings[categoria] = valores
        except (json.JSONDecodeError, OSError):
            # Mantém os padrões se o arquivo local estiver vazio ou corrompido.
            self.settings = self._load_defaults()

    def save_settings(self):
        arquivo_temporario = f"{self.file_path}.tmp"
        with open(arquivo_temporario, "w", encoding="utf-8") as f:
            json.dump(self.settings, f, indent=4, ensure_ascii=False)
        os.replace(arquivo_temporario, self.file_path)

    def get(self, category, key):
        return self.settings.get(category, {}).get(key)

    def set(self, category, key, value):
        # Garante que a categoria existe antes de definir a chave
        if category not in self.settings:
            self.settings[category] = {}
        self.settings[category][key] = value
        self.save_settings()

settings = ConfigManager()