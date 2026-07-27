import json
import os

class ConfigManager:
    def __init__(self, file_path="settings.json"):
        self.file_path = file_path
        self.settings = self._load_defaults()
        self.load_settings()

    def _load_defaults(self):
        return {
            "visual": {"tema": "dark", "tamanho_fonte": 14},
            "audio": {"velocidade": 1.0, "tom": 1.0}
        }

    def load_settings(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, "r") as f:
                self.settings.update(json.load(f))

    def save_settings(self):
        with open(self.file_path, "w") as f:
            json.dump(self.settings, f, indent=4)

    def get(self, category, key):
        return self.settings.get(category, {}).get(key)

    def set(self, category, key, value):
        self.settings[category][key] = value
        self.save_settings()

settings = ConfigManager()