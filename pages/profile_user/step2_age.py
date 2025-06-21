import flet as ft
from .base_step import BaseStep, logger


class Step2Age(BaseStep):
    """Etapa 2: Coleta da idade do usuário."""

    def __init__(
        self,
        page: ft.Page,
        profile_data: dict,
        current_step: list,
        on_next,
        on_previous,
    ):
        self.age_input = ft.TextField(
            label="Idade",
            width=320,
            border="underline",
            filled=True,
            text_size=16,
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        super().__init__(page, profile_data, current_step, on_next, on_previous)
        logger.info("Step2Age inicializado com sucesso.")

    def build_view(self) -> ft.Control:
        return ft.Column(
            [
                ft.Text("Etapa 2 de 5: Idade", size=20, weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=ft.Image(
                        src="mascote_supafit/step2.png",
                        width=150,
                        height=150,
                        fit=ft.ImageFit.CONTAIN,
                    ),
                    alignment=ft.alignment.center,
                    padding=20,
                ),
                self.age_input,
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
        age = self.age_input.value.strip()
        if not age or not age.isdigit() or int(age) < 10 or int(age) > 100:
            self.age_input.error_text = "Insira uma idade válida (10-100)."
            self.age_input.update()
            self.show_snackbar("Insira uma idade válida (10-100).")
            logger.warning("Idade inválida.")
            return False
        self.age_input.error_text = None
        self.profile_data["age"] = int(age)
        logger.info(f"Idade coletada: {age}")
        return True
