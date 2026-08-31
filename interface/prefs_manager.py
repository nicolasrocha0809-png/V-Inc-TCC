from supabase import Client
from config import settings


class PrefsManager:
    """Sincroniza preferências da instalação com o perfil do usuário."""

    MAPA_PREFERENCIAS = {
        "tema": ("visual", "tema"),
        "fonte": ("visual", "fonte"),
        "idioma": ("geral", "idioma"),
        "volume": ("audio", "volume"),
        "velocidade": ("audio", "velocidade"),
        "microfone": ("audio", "microfone"),
        "saida": ("audio", "saida"),
    }

    def __init__(self, supabase: Client, user_id: str):
        self.supabase = supabase
        self.user_id = user_id

    def carregar(self):
        """Retorna as preferências em formato compatível com a tela antiga."""
        return {
            "tema": settings.get("visual", "tema") or "dark",
            "fonte": settings.get("visual", "fonte") or "12px",
            "idioma": settings.get("geral", "idioma") or "pt_BR",
            "volume": settings.get("audio", "volume") or 80,
            "velocidade": settings.get("audio", "velocidade") or 80,
            "microfone": settings.get("audio", "microfone"),
            "saida": settings.get("audio", "saida"),
        }

    def carregar_do_supabase(self):
        """Busca preferências do usuário e atualiza o arquivo local."""
        if not self.supabase or not self.user_id:
            return None
        try:
            res = (
                self.supabase.table("configuracoes")
                .select("*")
                .eq("user_id", self.user_id)
                .execute()
            )
            if not res.data:
                return None

            prefs = res.data[0]
            for chave, valor in prefs.items():
                if chave in self.MAPA_PREFERENCIAS:
                    categoria, nome = self.MAPA_PREFERENCIAS[chave]
                    settings.set(categoria, nome, valor)
            return self.carregar()
        except Exception as e:
            print(f"Erro ao buscar preferências no Supabase: {e}")
            return None

    def salvar_preferencia(self, chave: str, valor):
        """Salva localmente e sincroniza uma preferência com o Supabase."""
        if chave not in self.MAPA_PREFERENCIAS:
            raise ValueError(f"Preferência desconhecida: {chave}")

        categoria, nome = self.MAPA_PREFERENCIAS[chave]
        settings.set(categoria, nome, valor)
        prefs = self.carregar()

        if not self.supabase or not self.user_id:
            return

        try:
            dados_upsert = {
                "user_id": self.user_id,
                "tema": prefs.get("tema", "dark"),
                "fonte": prefs.get("fonte", "12px"),
                "idioma": prefs.get("idioma", "pt_BR"),
                "volume": int(prefs.get("volume", 80)),
                "velocidade": int(prefs.get("velocidade", 80)),
            }
            self.supabase.table("configuracoes").upsert(dados_upsert).execute()
        except Exception as e:
            print(f"Erro ao sincronizar com Supabase: {e}")
