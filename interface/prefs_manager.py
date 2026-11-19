from supabase import Client
from config import settings
from servicos.preferencias import valor_ou_padrao


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

    # Valores usados quando a preferência ainda não foi salva
    PADROES = {
        "tema": "escuro",
        "fonte": "12px",
        "idioma": "pt_BR",
        "volume": 80,
        "velocidade": 80,
    }

    def __init__(self, supabase: Client, user_id: str):
        self.supabase = supabase
        self.user_id = user_id

    def carregar(self):
        """Retorna as preferências em formato compatível com a tela antiga."""
        return {
            "tema": settings.get("visual", "tema") or self.PADROES["tema"],
            "fonte": settings.get("visual", "fonte") or self.PADROES["fonte"],
            "idioma": settings.get("geral", "idioma") or self.PADROES["idioma"],
            "volume": valor_ou_padrao(
                settings.get("audio", "volume"), self.PADROES["volume"]
            ),
            # DEMO AO VIVO: aqui a velocidade 0 ainda vira 80
            "velocidade": settings.get("audio", "velocidade") or self.PADROES["velocidade"],
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
        return self._sincronizar_supabase()

    def salvar(self, preferencias):
        """Salva várias preferências e sincroniza apenas uma vez."""
        atualizacoes = []

        for chave, valor in preferencias.items():
            if chave not in self.MAPA_PREFERENCIAS:
                raise ValueError(f"Preferência desconhecida: {chave}")

            categoria, nome = self.MAPA_PREFERENCIAS[chave]
            atualizacoes.append((categoria, nome, valor))

        settings.set_many(atualizacoes)

        return self._sincronizar_supabase()

    def _sincronizar_supabase(self):
        prefs = self.carregar()

        if not self.supabase or not self.user_id:
            return None

        try:
            dados_upsert = {
                "user_id": self.user_id,
                "tema": prefs["tema"],
                "fonte": prefs["fonte"],
                "idioma": prefs["idioma"],
                "volume": int(prefs["volume"]),
                "velocidade": int(prefs["velocidade"]),
            }
            self.supabase.table("configuracoes").upsert(dados_upsert).execute()
            return True
        except Exception as e:
            print(f"Erro ao sincronizar com Supabase: {e}")
            return False
