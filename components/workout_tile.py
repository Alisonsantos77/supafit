import flet as ft


class WorkoutTile(ft.ExpansionTile):
    def __init__(
        self,
        workout_name: str,
        day: str,
        image_url: str,
        is_current_day: bool = False,
        on_view_click=None,
    ):
        super().__init__(
            title=ft.Text(workout_name, weight=ft.FontWeight.BOLD, no_wrap=False),
            subtitle=ft.Text(day.capitalize(), no_wrap=False),
            tile_padding=ft.padding.symmetric(horizontal=16, vertical=8),
            controls_padding=ft.padding.all(10),
            maintain_state=True,
            affinity=ft.TileAffinity.TRAILING,
            show_trailing_icon=True,
        )
        self.workout_name = workout_name
        self.day = day
        self.image_url = image_url
        self.is_current_day = is_current_day
        self.on_view_click = on_view_click

        # Configuração do leading (imagem)
        self.leading = ft.Image(
            src=image_url,
            width=64,
            height=64,
            fit=ft.ImageFit.COVER,
            border_radius=ft.border_radius.all(10),
            error_content=ft.Icon(ft.Icons.ERROR),
        )

        # Configuração do trailing (checkbox para indicar o dia atual)
        self.trailing = ft.Checkbox(value=is_current_day, disabled=True)

        # Controles exibidos ao expandir
        self.controls = [
            ft.ListTile(
                title=ft.Text(
                    f"Detalhes do treino de {day.capitalize()}",
                    weight=ft.FontWeight.BOLD,
                ),
                subtitle=ft.Text(
                    "Aqui você pode ver os exercícios planejados para este dia."
                ),
            ),
            ft.ElevatedButton(
                text="Ver Treino",
                on_click=self.on_view_click,
                style=ft.ButtonStyle(
                    bgcolor=ft.Colors.BLUE,
                    color=ft.Colors.WHITE,
                    shape=ft.RoundedRectangleBorder(radius=5),
                ),
            ),
        ]

    def build(self):
        return self
