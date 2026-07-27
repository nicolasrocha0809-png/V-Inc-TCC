import json
import os
from supabase import Client

class PrefsManager:
    def __init__(self, supabase: Client, user_id: str):
        self.supabase = supabase
        self.user_id = user_id
        self.caminho_local = os.path.join(os.path.dirname(__file__), "..", "config.json")

    def carregar(self):
        """Carrega as preferências do arquivo local se existir."""
        if os.path.exists(self.caminho_local):
            try:
                with open(self.caminho_local, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {"tema": "escuro"}
        return {"tema": "escuro"}

    def carregar_do_supabase(self):
        """Busca as preferências no banco e sincroniza com o arquivo local."""
        try:
            res = self.supabase.table("preferencias").select("*").eq("user_id", self.user_id).execute()
            
            if res.data and len(res.data) > 0:
                prefs = res.data[0]
                with open(self.caminho_local, "w") as f:
                    json.dump(prefs, f)
                return prefs
        except Exception as e:
            print(f"Erro ao buscar preferências no Supabase: {e}")
        return None

    def salvar_preferencia(self, chave: str, valor: str):
        """Atualiza uma preferência localmente e no Supabase."""
        prefs = self.carregar()
        prefs[chave] = valor
        
        with open(self.caminho_local, "w") as f:
            json.dump(prefs, f)
        
        try:
            self.supabase.table("preferencias").upsert({
                "user_id": self.user_id,
                chave: valor
            }).execute()
        except Exception as e:
            print(f"Erro ao sincronizar com Supabase: {e}")