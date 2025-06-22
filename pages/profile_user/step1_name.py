import flet as ft
from .base_step import BaseStep, logger
from services.anthropic import AnthropicService
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

    def build_view(self) -> ft.Control:
        return ft.Column(
            [
                ft.Text("Etapa 1 de 5: Nome", size=20, weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=ft.Image(
                        src="mascote_supafit/step1.png",
                        width=150,
                        height=150,
                        fit=ft.ImageFit.CONTAIN,
                    ),
                    alignment=ft.alignment.center,
                    padding=20,
                ),
                self.name_input,
                ft.Row(
                    [ft.ElevatedButton("Próximo", on_click=self.on_next)],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=10,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=15,
        )

    def validate(self) -> bool:
        name = self.name_input.value.strip()
        if not name:
            self.name_input.error_text = "Por favor, insira seu nome."
            self.name_input.update()
            self.show_snackbar("Por favor, insira seu nome.")
            logger.warning("Nome não preenchido.")
            return False

        # Verificar comprimento do nome
        if len(name) < 2 or len(name) > 20:
            self.name_input.error_text = "Nome deve ter entre 2 e 20 caracteres."
            self.name_input.update()
            self.show_snackbar("Nome deve ter entre 2 e 20 caracteres.")
            logger.warning(f"Comprimento inválido do nome: {name}")
            return False

        # Verificar caracteres permitidos
        if not re.match(r"^[a-zA-Z0-9\s]+$", name):
            self.name_input.error_text = "Use apenas letras, números e espaços."
            self.name_input.update()
            self.show_snackbar("Nome contém caracteres inválidos.")
            logger.warning(f"Caracteres inválidos no nome: {name}")
            return False

        # Verificar conteúdo sensível
        anthropic_service = AnthropicService()
        if anthropic_service.is_sensitive_name(name):
            self.name_input.error_text = "Nome contém conteúdo inadequado."
            self.name_input.update()
            self.show_snackbar("Escolha um nome apropriado.")
            logger.warning(f"Nome sensível detectado: {name}")
            return False

        self.name_input.error_text = None
        self.profile_data["name"] = name
        logger.info(f"Nome coletado: {name}")
        return True
