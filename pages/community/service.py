import logging
import hashlib
from datetime import datetime, timezone
from typing import List, Dict, Set
from .models import Victory, VictoryPost

logger = logging.getLogger("supafit.community.service")


class CommunityService:
    """Serviço responsável pelas operações de dados da comunidade"""

    def __init__(self, supabase_service):
        self.supabase = supabase_service

    def load_victories(self, category: str = "Todas") -> List[Victory]:
        """Carrega as vitórias filtradas por categoria"""
        try:
            query = self.supabase.client.table("victories").select("*")
            if category != "Todas":
                query = query.eq("category", category)

            resp_victories = query.order("created_at", desc=True).execute()
            victories_data = resp_victories.data or []
            logger.info(f"Vitórias carregadas do Supabase: {len(victories_data)} itens para categoria {category}")
            if not victories_data:
                logger.info("Nenhuma vitória encontrada.")
                return []

            # Enriquecer os dados das vitórias
            victories = self._enrich_victories_data(victories_data)
            return [Victory.from_dict(v) for v in victories]

        except Exception as e:
            logger.error(f"Erro ao carregar vitórias: {str(e)}")
            return []

    def _enrich_victories_data(self, victories_data: List[Dict]) -> List[Dict]:
        """Enriquece os dados das vitórias com nomes e likes"""
        user_ids = [v["user_id"] for v in victories_data]
        victory_ids = [v["id"] for v in victories_data]

        # Buscar nomes dos usuários
        name_map = self._get_user_names(user_ids)

        # Buscar dados de likes
        likes_map = self._get_likes_count(victory_ids)
        user_liked_ids = self._get_user_liked_victories(victory_ids)

        # Aplicar os dados enriquecidos
        for victory in victories_data:
            uid = victory["user_id"]
            vid = victory["id"]

            victory["author_name"] = name_map.get(
                uid, self._generate_fallback_name(uid)
            )
            victory["likes"] = likes_map.get(vid, 0)
            victory["liked"] = vid in user_liked_ids

        return victories_data

    def _get_user_names(self, user_ids: List[str]) -> Dict[str, str]:
        """Busca os nomes dos usuários com fallback"""
        name_map = {}

        if not user_ids:
            return name_map

        # 1. Buscar em public_profile_info
        try:
            resp_pub = (
                self.supabase.client.table("public_profile_info")
                .select("user_id, name")
                .in_("user_id", user_ids)
                .execute()
            )
            for profile in resp_pub.data or []:
                if profile.get("name"):
                    name_map[profile["user_id"]] = profile["name"]
        except Exception as e:
            logger.error(f"Erro ao buscar public_profile_info: {str(e)}")

        # 2. Fallback para user_profiles
        missing_ids = [uid for uid in user_ids if uid not in name_map]
        if missing_ids:
            try:
                resp_profiles = (
                    self.supabase.client.table("user_profiles")
                    .select("user_id, name")
                    .in_("user_id", missing_ids)
                    .execute()
                )
                for profile in resp_profiles.data or []:
                    if profile.get("name"):
                        name_map[profile["user_id"]] = profile["name"]
            except Exception as e:
                logger.error(f"Erro ao buscar user_profiles: {str(e)}")

        return name_map

    def _generate_fallback_name(self, user_id: str) -> str:
        """Gera um nome de fallback baseado no hash do user_id"""
        return f"Usuário_{hashlib.sha1(user_id.encode()).hexdigest()[:6]}"

    def _get_likes_count(self, victory_ids: List[str]) -> Dict[str, int]:
        """Busca a contagem de likes para cada vitória"""
        likes_map = {}

        if not victory_ids:
            return likes_map

        try:
            resp_likes = (
                self.supabase.client.table("victory_likes")
                .select("victory_id", count="exact")
                .in_("victory_id", victory_ids)
                .execute()
            )
            for item in resp_likes.data or []:
                vid = item["victory_id"]
                likes_map[vid] = likes_map.get(vid, 0) + 1
        except Exception as e:
            logger.error(f"Erro ao buscar likes: {str(e)}")

        return likes_map

    def _get_user_liked_victories(
        self, victory_ids: List[str], user_id: str = None
    ) -> Set[str]:
        """Busca quais vitórias o usuário curtiu"""
        if not user_id or not victory_ids:
            return set()

        try:
            resp_user_likes = (
                self.supabase.client.table("victory_likes")
                .select("victory_id")
                .eq("user_id", user_id)
                .in_("victory_id", victory_ids)
                .execute()
            )
            return {item["victory_id"] for item in resp_user_likes.data or []}
        except Exception as e:
            logger.error(f"Erro ao buscar likes do usuário: {str(e)}")
            return set()

    def create_victory(self, victory_post: VictoryPost) -> bool:
        """Cria uma nova vitória"""
        try:
            self.supabase.client.table("victories").insert(
                victory_post.to_dict()
            ).execute()
            return True
        except Exception as e:
            logger.error(f"Erro ao criar vitória: {str(e)}")
            return False

    def toggle_like(self, victory_id: str, user_id: str, currently_liked: bool) -> bool:
        """Alterna o like de uma vitória"""
        try:
            if currently_liked:
                # Remove curtida
                self.supabase.client.table("victory_likes").delete().eq(
                    "victory_id", victory_id
                ).eq("user_id", user_id).execute()
            else:
                # Adiciona curtida
                self.supabase.client.table("victory_likes").insert(
                    {
                        "victory_id": victory_id,
                        "user_id": user_id,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    }
                ).execute()
            return True
        except Exception as e:
            logger.error(f"Erro ao curtir/descurtir: {str(e)}")
            return False

    def delete_victory(self, victory_id: str, user_id: str) -> tuple[bool, str]:
        """Deleta uma vitória se o usuário for o autor"""
        try:
            # Verifica se o usuário é o autor
            victory = (
                self.supabase.client.table("victories")
                .select("user_id")
                .eq("id", victory_id)
                .execute()
            )

            if not victory.data or victory.data[0]["user_id"] != user_id:
                return False, "Você não pode excluir esta vitória!"

            # Deleta a vitória e seus likes
            self.supabase.client.table("victories").delete().eq(
                "id", victory_id
            ).execute()

            self.supabase.client.table("victory_likes").delete().eq(
                "victory_id", victory_id
            ).execute()

            return True, "Vitória excluída com sucesso!"

        except Exception as e:
            logger.error(f"Erro ao excluir vitória: {str(e)}")
            return False, f"Erro ao excluir vitória: {str(e)}"
