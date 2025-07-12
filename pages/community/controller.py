import asyncio
import logging
from datetime import datetime, timezone
from typing import List
from .models import Victory, VictoryPost
from .service import CommunityService
from .ui_components import SnackBarHelper

logger = logging.getLogger("supafit.community.controller")


class CommunityController:
    """Controller responsável pela lógica de negócio da comunidade"""

    def __init__(self, page, supabase_service):
        self.page = page
        self.supabase_service = supabase_service
        self.service = CommunityService(supabase_service)
        self.user_id = page.client_storage.get("supafit.user_id") or "supafit_user"
        self.selected_category = "Todas"

    def load_victories(self, category: str = "Todas") -> List[Victory]:
        """Carrega as vitórias filtradas por categoria"""
        self.selected_category = category
        return self.service.load_victories(category)

    def create_victory(self, content: str, category: str) -> bool:
        """Cria uma nova vitória com validações"""
        # Validação de login
        if self.user_id == "supafit_user":
            SnackBarHelper.show_error(
                self.page, "Você precisa estar logado para postar!"
            )
            return False

        # Validação de campos obrigatórios
        if not content or not category:
            SnackBarHelper.show_error(self.page, "Preencha todos os campos!")
            return False

        # Validação de tamanho
        if len(content) > 200:
            SnackBarHelper.show_error(self.page, "Limite de 200 caracteres excedido!")
            return False

        # Criar vitória
        victory_post = VictoryPost(
            user_id=self.user_id,
            content=content,
            category=category,
            created_at=datetime.now(timezone.utc),
        )

        success = self.service.create_victory(victory_post)

        if success:
            SnackBarHelper.show_success(self.page, "Vitória postada com sucesso!")
        else:
            SnackBarHelper.show_error(self.page, "Erro ao postar vitória!")

        return success

    def toggle_like(self, victory_id: str, currently_liked: bool) -> bool:
        """Alterna o like de uma vitória"""
        if self.user_id == "supafit_user":
            SnackBarHelper.show_error(
                self.page, "Você precisa estar logado para curtir!"
            )
            return False

        success = self.service.toggle_like(victory_id, self.user_id, currently_liked)

        if not success:
            SnackBarHelper.show_error(self.page, "Erro ao curtir/descurtir!")

        return success

    def delete_victory(self, victory_id: str, user_id: str) -> tuple[bool, str]:
        """Deleta uma vitória se o usuário for o autor"""
        try:
            # Verifica se o usuário é o autor da vitória
            victory = (
                self.supabase_service.client.table("victories")
                .select("user_id")
                .eq("id", victory_id)
                .execute()
            )

            if not victory.data or victory.data[0]["user_id"] != user_id:
                return False, "Você não pode excluir esta vitória!"

            # Deleta a vitória
            delete_resp = (
                self.supabase_service.client.table("victories")
                .delete()
                .eq("id", victory_id)
                .execute()
            )

            if not delete_resp.data:
                logger.warning(f"Nenhuma linha deletada para vitória {victory_id}")
                return False, "Falha ao excluir vitória. Verifique suas permissões."

            # Deleta os likes associados
            self.supabase_service.client.table("victory_likes").delete().eq(
                "victory_id", victory_id
            ).execute()

            # Pequeno atraso para consistência eventual
            import time

            asyncio.sleep(0.2)

            # Verifica se ainda existe
            check_victory = (
                self.supabase_service.client.table("victories")
                .select("id")
                .eq("id", victory_id)
                .execute()
            )

            if check_victory.data:
                logger.error(
                    f"Vitória {victory_id} ainda existe após tentativa de exclusão!"
                )
                return False, "Erro ao excluir vitória: ela ainda existe no banco."

            return True, "Vitória excluída com sucesso!"

        except Exception as e:
            logger.error(f"Erro ao excluir vitória: {str(e)}")
            return False, f"Erro ao excluir vitória: {str(e)}"

    def get_categories(self) -> List[str]:
        """Retorna as categorias disponíveis"""
        return ["Força", "Resistência", "Disciplina", "Nutrição", "Todas"]

    def is_user_logged_in(self) -> bool:
        """Verifica se o usuário está logado"""
        return self.user_id != "supafit_user"

    def get_current_user_id(self) -> str:
        """Retorna o ID do usuário atual"""
        return self.user_id

    def get_selected_category(self) -> str:
        """Retorna a categoria atualmente selecionada"""
        return self.selected_category
