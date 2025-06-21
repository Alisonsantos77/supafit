import flet as ft
from .base_step import BaseStep, logger


class Step3Weight(BaseStep):
    """Etapa 3: Coleta do peso do usuário."""

    def __init__(
        self,
        page: ft.Page,
        profile_data: dict,
        current_step: list,
        on_next,
        on_previous,
    ):
        self.weight_input = ft.TextField(
            label="Peso (kg)",
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
        logger.info("Step3Weight inicializado com sucesso.")

    def build_view(self) -> ft.Control:
        return ft.Column(
            [
                ft.Text("Etapa 3 de 5: Peso", size=20, weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=ft.Image(
                        src="mascote_supafit/step3.png",
                        width=150,
                        height=150,
                        fit=ft.ImageFit.CONTAIN,
                    ),
                    alignment=ft.alignment.center,
                    padding=20,
                ),
                self.weight_input,
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
        weight = self.weight_input.value.strip()
        try:
            weight = float(weight)
            if weight < 30 or weight > 300:
                self.weight_input.error_text = "Insira um peso válido (30-300 kg)."
                self.weight_input.update()
                self.show_snackbar("Insira um peso válido (30-300 kg).")
                logger.warning("Peso inválido.")
                return False
        except ValueError:
            self.weight_input.error_text = "Insira um número válido."
            self.weight_input.update()
            self.show_snackbar("Insira um número válido para o peso.")
            logger.warning("Peso não é um número.")
            return False
        self.weight_input.error_text = None
        self.profile_data["weight"] = weight
        logger.info(f"Peso coletado: {weight}")
        return True
