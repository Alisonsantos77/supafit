import flet as ft
from .base_step import BaseStep, logger

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
            bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.BLUE_GREY),
            border_color=ft.Colors.BLUE_600,
            focused_border_color=ft.Colors.BLUE_400,
            cursor_color=ft.Colors.BLUE_400,
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
        self.name_input.error_text = None
        self.profile_data["name"] = name
        logger.info(f"Nome coletado: {name}")
        return True
