import flet as ft
from .base_step import BaseStep, logger
from services.openai import OpenAIService


class Step7Restrictions(BaseStep):
    """Etapa 8: Coleta de restrições do usuário (lesões, dificuldades, etc.)."""

    def __init__(
        self,
        page: ft.Page,
        profile_data: dict,
        current_step: list,
        on_next,
        on_previous,
        supabase_service=None,
        on_create=None,
    ):
        self.restrictions_input = ft.TextField(
            label="Restrições (lesões, dificuldades, etc.)",
            width=320,
            border="underline",
            filled=True,
            text_size=16,
            multiline=True,
            max_lines=4,
        )
        super().__init__(page, profile_data, current_step, on_next, on_previous)
        logger.info("Step7Restrictions inicializado com sucesso.")

    def build_step_progress(self) -> ft.Control:
        """Constrói o indicador de progresso das etapas."""
        steps = []
        for i in range(8):
            is_current = self.current_step[0] == i
            is_completed = self.current_step[0] > i
            steps.append(
                ft.Container(
                    width=30,
                    height=30,
                    border_radius=15,
                    bgcolor=ft.Colors.BLUE_400 if is_current else None,
                    border=ft.border.all(
                        2,
                        (
                            ft.Colors.BLUE_400
                            if is_current
                            else (
                                ft.Colors.GREEN_400
                                if is_completed
                                else ft.Colors.GREY_400
                            )
                        ),
                    ),
                    content=ft.Text(
                        str(i + 1),
                        color=ft.Colors.WHITE if is_current else ft.Colors.BLACK,
                        size=14,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    alignment=ft.alignment.center,
                    animate_opacity=300,
                    animate_scale=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
                    scale=1.2 if is_current else 1.0,
                )
            )
        return ft.Row(
            steps,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10,
        )

    def build_view(self) -> ft.Control:
        return ft.Column(
            [
                self.build_step_progress(),
                ft.Container(
                    content=ft.Image(
                        src="mascote_supafit/step7_restrictions.png",
                        width=150,
                        height=150,
                        fit=ft.ImageFit.CONTAIN,
                    ),
                    alignment=ft.alignment.center,
                    padding=20,
                ),
                self.restrictions_input,
                ft.Row(
                    [
                        ft.ElevatedButton("Voltar", on_click=self.on_previous),
                        ft.ElevatedButton("Próximo", on_click=self.on_next),
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
        restrictions = self.restrictions_input.value.strip()

        # Verificar comprimento
        if len(restrictions) > 500:
            self.restrictions_input.error_text = (
                "Descrição muito longa (máx. 500 caracteres)."
            )
            self.restrictions_input.update()
            self.show_snackbar("Descrição muito longa (máx. 500 caracteres).")
            logger.warning("Restrições excedem o limite de caracteres.")
            return False

        if restrictions:
            openai_service = OpenAIService()
            if openai_service.is_sensitive_restrictions(restrictions):
                self.restrictions_input.error_text = (
                    "Restrições contêm conteúdo inadequado."
                )
                self.restrictions_input.update()
                self.show_snackbar(
                    "Por favor, descreva apenas lesões ou dificuldades apropriadas."
                )
                logger.warning(
                    f"Conteúdo sensível detectado nas restrições: {restrictions}"
                )
                return False

        self.restrictions_input.error_text = None
        self.profile_data["restrictions"] = restrictions or None
        logger.info(
            f"Restrições coletadas: {self.profile_data['restrictions'] or 'nenhuma'}"
        )
        return True
