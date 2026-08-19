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
        defaults = {
            "tema": "escuro", 
            "fonte": "12px", 
            "idioma": "pt_BR", 
            "volume": 80, 
            "velocidade": 80
        }
        if os.path.exists(self.caminho_local):
            try:
                with open(self.caminho_local, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                    defaults.update(dados)
                    return defaults
            except (json.JSONDecodeError, IOError):
                return defaults
        return defaults

    def carregar_do_supabase(self):
        """Busca as preferências no banco configuracoes e sincroniza com o arquivo local."""
        try:
            res = self.supabase.table("configuracoes").select("*").eq("user_id", self.user_id).execute()
            
            if res.data and len(res.data) > 0:
                prefs = res.data[0]
                with open(self.caminho_local, "w", encoding="utf-8") as f:
                    json.dump(prefs, f, ensure_ascii=False, indent=4)
                return prefs
        except Exception as e:
            print(f"Erro ao buscar preferências no Supabase: {e}")
        return None

    def salvar_preferencia(self, chave: str, valor: str):
        """Atualiza uma preferência localmente e envia o bloco completo para a tabela configuracoes."""
        prefs = self.carregar()
        prefs[chave] = valor
        
        # Salva localmente no JSON
        with open(self.caminho_local, "w", encoding="utf-8") as f:
            json.dump(prefs, f, ensure_ascii=False, indent=4)
        
        try:
            # Payload completo adaptado com volume e velocidade separados para a tabela 'configuracoes'
            dados_upsert = {
                "user_id": self.user_id,
                "tema": prefs.get("tema", "escuro"),
                "fonte": prefs.get("fonte", "12px"),
                "idioma": prefs.get("idioma", "pt_BR"),
                "volume": int(prefs.get("volume", 80)),
                "velocidade": int(prefs.get("velocidade", 80))
            }
            
            self.supabase.table("configuracoes").upsert(dados_upsert).execute()
        except Exception as e:
            print(f"Erro ao sincronizar com Supabase: {e}")