import flet as ft
from .base_step import BaseStep, logger


class Step5Goal(BaseStep):
    """Etapa 5: Coleta do objetivo do usuário."""

    def __init__(
        self,
        page: ft.Page,
        profile_data: dict,
        current_step: list,
        on_next,
        on_previous,
    ):
        self.goal_radio_group = ft.RadioGroup(
            content=ft.Column(
                [
                    ft.Radio(value="Perder peso", label="Perder peso"),
                    ft.Radio(value="Ganhar massa", label="Ganhar massa"),
                    ft.Radio(value="Manter forma", label="Manter forma"),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=10,
            ),
            value="Manter forma",
        )
        super().__init__(page, profile_data, current_step, on_next, on_previous)
        logger.info("Step5Goal inicializado com sucesso.")

    def build_view(self) -> ft.Control:
        return ft.Column(
            [
                ft.Text("Etapa 5 de 5: Objetivo", size=20, weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=ft.Image(
                        src="mascote_supafit/step5.png",
                        width=150,
                        height=150,
                        fit=ft.ImageFit.CONTAIN,
                    ),
                    alignment=ft.alignment.center,
                    padding=20,
                ),
                self.goal_radio_group,
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
        self.profile_data["goal"] = self.goal_radio_group.value
        logger.info(f"Objetivo coletado: {self.profile_data['goal']}")
        return True
