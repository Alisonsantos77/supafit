import flet as ft
from .base_step import BaseStep
from utils.logger import get_logger

logger = get_logger("supabafit.profile_user.step9_review")


class Step8Review(BaseStep):
    """Etapa 9: Revisão dos dados do perfil."""

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
        super().__init__(page, profile_data, current_step, on_next, on_previous)
        logger.info("Step8Review inicializado com sucesso.")

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
                ft.Text("Revisão", size=20, weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=ft.Image(
                        src="mascote_supafit/step9.png",
                        width=150,
                        height=150,
                        fit=ft.ImageFit.CONTAIN,
                    ),
                    alignment=ft.alignment.center,
                    padding=20,
                ),
                ft.Card(
                    content=ft.Container(
                        content=ft.ListView(
                            controls=self.build_review_items(),
                            spacing=10,
                            padding=10,
                            auto_scroll=False,
                        ),
                        padding=20,
                    ),
                    elevation=4,
                    width=340,
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

    def build_review_items(self) -> list:
        """Constrói os itens de revisão com ícones e formatação."""
        items = [
            ("Nome", self.profile_data.get("name", "Não informado"), ft.Icons.PERSON),
            (
                "Idade",
                f"{self.profile_data.get('age', 'Não informado')} anos",
                ft.Icons.CALENDAR_TODAY,
            ),
            (
                "Gênero",
                self.profile_data.get("gender", "Não informado"),
                ft.Icons.PEOPLE,
            ),
            (
                "Peso",
                f"{self.profile_data.get('weight', 'Não informado')} kg",
                ft.Icons.FITNESS_CENTER,
            ),
            (
                "Altura",
                f"{self.profile_data.get('height', 'Não informado')} cm",
                ft.Icons.HEIGHT,
            ),
            ("Objetivo", self.profile_data.get("goal", "Não informado"), ft.Icons.STAR),
            (
                "Nível",
                self.profile_data.get("level", "Não informado"),
                ft.Icons.FITNESS_CENTER,
            ),
            (
                "Restrições",
                self.profile_data.get("restrictions", "Nenhuma"),
                ft.Icons.WARNING,
            ),
        ]
        return [
            ft.Row(
                [
                    ft.Icon(icon, color=ft.Colors.BLUE_400, size=20),
                    ft.Text(f"{label}: ", weight=ft.FontWeight.BOLD, size=16),
                    ft.Text(value, size=16, color=ft.Colors.GREY_800),
                ],
                alignment=ft.MainAxisAlignment.START,
                spacing=10,
            )
            for label, value, icon in items
        ]

    def validate(self) -> bool:
        return True

    def update_review(self):
        """Atualiza a lista de revisão."""
        self.view.controls[3].content.controls = self.build_review_items()
        if self.view.page:
            self.view.update()
            logger.info("Conteúdo de revisão atualizado.")
        else:
            logger.debug("update_review chamado, mas view ainda não está na página.")
