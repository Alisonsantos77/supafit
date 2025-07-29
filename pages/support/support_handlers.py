import flet as ft
import logging
import random
from .support_components import AnimatedSnackBar

logger = logging.getLogger("supafit.support.handlers")


class SupportHandlers:
    def __init__(self, page: ft.Page, pix_key: str, buddy_avatar, pix_card=None):
        self.page = page
        self.pix_key = pix_key
        self.buddy_avatar = buddy_avatar
        self.pix_card = pix_card

    def copy_pix_key(self, e=None):
        try:
            self.page.set_clipboard(self.pix_key)

            if self.pix_card:
                self.pix_card.animate_copy_success()

            AnimatedSnackBar.show_success(
                self.page, "PIX copiado! 🎯 Abra seu banco!", ft.Icons.COPY_ALL
            )
            self.buddy_avatar.animate_buddy()

        except Exception as ex:
            logger.error(f"Erro ao copiar PIX: {ex}")
            AnimatedSnackBar.show_error(
                self.page, "Erro ao copiar 😞", ft.Icons.ERROR_OUTLINE
            )

    def animate_buddy_click(self, e):
        try:
            self.buddy_avatar.animate_buddy()
            encouragement_messages = [
                "Obrigado pelo apoio! 💙",
                "Você é incrível! ⭐",
                "Juntos vamos longe! 🚀",
                "Sua ajuda faz diferença! 💪",
                "Gratidão eterna! 🙏",
                "Você acredita no projeto! ✨",
            ]
            message = random.choice(encouragement_messages)
            AnimatedSnackBar.show_info(self.page, message, ft.Icons.FAVORITE)
        except Exception as e:
            logger.error(f"Erro ao animar buddy: {e}")

    def show_welcome_message(self):
        try:
            AnimatedSnackBar.show_info(
                self.page,
                "Ajude o SupaFit! 👨‍💻 Copie o PIX!",
                ft.Icons.WAVING_HAND,
            )
        except Exception as e:
            logger.error(f"Erro ao mostrar boas-vindas: {e}")
