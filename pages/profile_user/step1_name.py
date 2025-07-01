import flet as ft
from .base_step import BaseStep, logger
from services.openai import OpenAIService
import re


class Step1Name(BaseStep):
    """Etapa 1: Coleta do nome do usuário."""

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
        self.name_input = ft.TextField(
            label="Nome",
            width=320,
            border="underline",
            filled=True,
            text_size=16,
        )
        super().__init__(page, profile_data, current_step, on_next, on_previous)
        logger.info("Step1Name inicializado com sucesso.")

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
                        src="mascote_supafit/step_name.png",
                        width=150,
                        height=150,
                        fit=ft.ImageFit.CONTAIN,
                    ),
                    alignment=ft.alignment.center,
                    padding=20,
                ),
                self.name_input,
                ft.Row(
                    [
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

    async def validate(self) -> bool:
        name = self.name_input.value.strip()
        if not name:
            self.name_input.error_text = "Por favor, insira seu nome."
            self.name_input.update()
            self.show_snackbar("Por favor, insira seu nome.")
            logger.warning("Nome não preenchido.")
            return False

        # Verificação de comprimento do nome
        if len(name) < 2 or len(name) > 20:
            self.name_input.error_text = "Nome deve ter entre 2 e 20 caracteres."
            self.name_input.update()
            self.show_snackbar("Nome deve ter entre 2 e 20 caracteres")
            logger.warning(f"Comprimento do nome: {name}")
            return False

        # Verificação de caracteres permitidos
        if not re.match(r"^[a-zA-Z0-9\s]+$", name):
            self.name_input.error_text = "Use apenas letras, números e espaços."
            self.name_input.update()
            self.show_snackbar("Nome contém caracteres inválidos.")
            logger.warning(f"Caracteres inválidos no nome: {name}")
            return False

        # Verificação de conteúdo sensível
        openai_service = OpenAIService()
        if await openai_service.is_sensitive_name(name):
            self.name_input.error_text = "Nome contém conteúdo inadequado."
            self.name_input.update()
            self.show_snackbar("Escolha um nome apropriado.")
            logger.warning(f"Nome sensível detectado: {name}")
            return False

        self.name_input.error_text = None
        self.profile_data["name"] = name
        logger.info(f"Nome coletado: {name}")
        return True
