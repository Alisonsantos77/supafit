import flet as ft
from .base_step import BaseStep, logger


class Step3Gender(BaseStep):
    """Etapa 3: Coleta do gênero do usuário."""

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
        self.gender_radio_group = ft.RadioGroup(
            content=ft.Column(
                [
                    ft.Radio(value="Masculino", label="Masculino"),
                    ft.Radio(value="Feminino", label="Feminino"),
                    ft.Radio(value="Outro", label="Outro"),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=10,
            ),
            value="Masculino",
        )
        super().__init__(page, profile_data, current_step, on_next, on_previous)
        logger.info("Step3Gender inicializado com sucesso.")

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
                        src="mascote_supafit/step_gender.png",
                        width=150,
                        height=150,
                        fit=ft.ImageFit.CONTAIN,
                    ),
                    alignment=ft.alignment.center,
                    padding=20,
                ),
                self.gender_radio_group,
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
        self.profile_data["gender"] = self.gender_radio_group.value
        logger.info(f"Gênero coletado: {self.profile_data['gender']}")
        return True
