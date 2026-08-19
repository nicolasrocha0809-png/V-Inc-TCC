import json
import os

class ConfigManager:
    def __init__(self, file_path="settings.json"):
        self.file_path = file_path
        self.settings = self._load_defaults()
        self.load_settings()

    def _load_defaults(self):
        return {
            "visual": {"tema": "dark", "fonte": "12px"},
            "audio": {"velocidade": 80, "volume": 80},  # Atualizado para incluir o volume separado
            "geral": {"idioma": "pt_BR"}
        }

    def load_settings(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, "r", encoding="utf-8") as f:
                dados_salvos = json.load(f)
                # Atualiza as categorias de forma inteligente para não perder chaves novas
                for categoria, valores in dados_salvos.items():
                    if categoria in self.settings and isinstance(valores, dict):
                        self.settings[categoria].update(valores)
                    else:
                        self.settings[categoria] = valores

    def save_settings(self):
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.settings, f, indent=4, ensure_ascii=False)

    def get(self, category, key):
        return self.settings.get(category, {}).get(key)

    def set(self, category, key, value):
        # Garante que a categoria existe antes de definir a chave
        if category not in self.settings:
            self.settings[category] = {}
        self.settings[category][key] = value
        self.save_settings()

settings = ConfigManager()