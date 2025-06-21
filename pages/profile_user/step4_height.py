import flet as ft
from .base_step import BaseStep, logger


class Step4Height(BaseStep):
    """Etapa 4: Coleta da altura do usuário."""

    def __init__(
        self,
        page: ft.Page,
        profile_data: dict,
        current_step: list,
        on_next,
        on_previous,
    ):
        self.height_input = ft.TextField(
            label="Altura (cm)",
            width=320,
            border="underline",
            filled=True,
            bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.BLUE_GREY),
            border_color=ft.Colors.BLUE_600,
            focused_border_color=ft.Colors.BLUE_400,
            cursor_color=ft.Colors.BLUE_400,
            text_size=16,
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        super().__init__(page, profile_data, current_step, on_next, on_previous)
        logger.info("Step4Height inicializado com sucesso.")

    def build_view(self) -> ft.Control:
        return ft.Column(
            [
                ft.Text("Etapa 4 de 5: Altura", size=20, weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=ft.Image(
                        src="mascote_supafit/step4.png",
                        width=150,
                        height=150,
                        fit=ft.ImageFit.CONTAIN,
                    ),
                    alignment=ft.alignment.center,
                    padding=20,
                ),
                self.height_input,
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
        height = self.height_input.value.strip()
        try:
            height = float(height)
            if height < 100 or height > 250:
                self.height_input.error_text = "Insira uma altura válida (100-250 cm)."
                self.height_input.update()
                self.show_snackbar("Insira uma altura válida (100-250 cm).")
                logger.warning("Altura inválida.")
                return False
        except ValueError:
            self.height_input.error_text = "Insira um número válido."
            self.height_input.update()
            self.show_snackbar("Insira um número válido para a altura.")
            logger.warning("Altura não é um número.")
            return False
        self.height_input.error_text = None
        self.profile_data["height"] = int(height)
        logger.info(f"Altura coletada: {height}")
        return True
