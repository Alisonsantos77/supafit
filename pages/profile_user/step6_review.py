import flet as ft
from .base_step import BaseStep
from utils.logger import get_logger

logger = get_logger("supabafit.profile_user.step6_review")


class Step6Review(BaseStep):
    """Etapa 6: Revisão dos dados do perfil."""

    def __init__(
        self,
        page: ft.Page,
        profile_data: dict,
        current_step: list,
        on_next,
        on_previous,
        supabase_service,
        on_create,
    ):
        self.supabase_service = supabase_service
        self.on_create = on_create
        self.review_text = ft.Markdown("")
        super().__init__(page, profile_data, current_step, on_next, on_previous)
        logger.info("Step6Review inicializado com sucesso.")

    def build_view(self) -> ft.Control:
        return ft.Column(
            [
                ft.Text("Revisão", size=20, weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=ft.Image(
                        src="mascote_supafit/step6.png",
                        width=150,
                        height=150,
                        fit=ft.ImageFit.CONTAIN,
                    ),
                    alignment=ft.alignment.center,
                    padding=20,
                ),
                ft.Container(
                    content=self.review_text,
                    alignment=ft.alignment.center,
                    padding=10,
                ),
                ft.Row(
                    [
                        ft.ElevatedButton("Voltar", on_click=self.on_previous),
                        ft.ElevatedButton("Criar Perfil", on_click=self.on_create),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=10,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=15,
        )

    def validate(self) -> bool:
        return True

    def update_review(self):
        review_content = f"""
        **Revise seus dados:**  
        **Nome:** {self.profile_data.get("name", "Não informado")}  
        **Idade:** {self.profile_data.get("age", "Não informado")}  
        **Peso:** {self.profile_data.get("weight", "Não informado")} kg  
        **Altura:** {self.profile_data.get("height", "Não informado")} cm  
        **Objetivo:** {self.profile_data.get("goal", "Não informado")}
        """
        self.review_text.value = review_content
        if self.review_text.page:
            self.review_text.update()
            logger.info("Conteúdo de revisão atualizado.")
        else:
            logger.debug(
                "update_review chamado, mas review_text ainda não está na página."
            )
