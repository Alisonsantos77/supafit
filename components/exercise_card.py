import flet as ft


class ExerciseCard(ft.Stack):
    def __init__(
        self,
        image_url: str,
        exercise_name: str,
        duration: str,
        sets: int,
        on_play_click=None,
        on_favorite_click=None,
        width=400,
        height=400,
        initially_favorited=False,
    ):
        super().__init__()
        self.image_url = image_url
        self.exercise_name = exercise_name
        self.duration = duration
        self.sets = sets
        self.on_play_click = on_play_click
        self.on_favorite_click = (
            on_favorite_click if on_favorite_click else self.default_favorite_click
        )
        self.width = width
        self.height = height
        self.is_favorited = initially_favorited

        # Configuração inicial do ícone de favorito
        self.favorite_icon = ft.IconButton(
            icon=ft.icons.STAR if self.is_favorited else ft.icons.STAR_BORDER,
            icon_color=ft.Colors.YELLOW_500 if self.is_favorited else ft.Colors.WHITE,
            icon_size=30,
            tooltip="Favoritar",
            on_click=self.on_favorite_click,
        )

        # Construção do card
        self.controls = [
            ft.Container(
                height=self.height,
                width=self.width,
                border_radius=20,
                bgcolor=ft.Colors.GREY_900,
            ),
            # Imagem superior
            ft.Container(
                image=ft.DecorationImage(
                    src=self.image_url,
                    fit=ft.ImageFit.COVER,
                ),
                height=self.height / 2,
                width=self.width,
                border_radius=ft.border_radius.only(top_left=20, top_right=20),
            ),
            # Botão de play
            ft.IconButton(
                icon=ft.icons.PLAY_ARROW,
                icon_color=ft.Colors.WHITE,
                tooltip="Assistir",
                bottom=self.height / 4,
                top=self.height / 4,
                right=10,
                icon_size=40,
                on_click=self.on_play_click,
                enable_feedback=True,
            ),
            # Ícone de favorito (estrela)
            ft.Container(
                content=self.favorite_icon,
                top=5,
                right=10,
            ),
            # Nome do exercício
            ft.Container(
                content=ft.Text(
                    self.exercise_name,
                    text_align=ft.TextAlign.CENTER,
                    color=ft.Colors.WHITE,
                    size=24,
                    weight=ft.FontWeight.BOLD,
                ),
                bottom=100,
                left=10,
            ),
            # Duração e séries
            ft.Container(
                bottom=50,
                left=20,
                right=20,
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Container(
                            content=ft.Text(
                                self.duration,
                                text_align=ft.TextAlign.CENTER,
                                color=ft.Colors.WHITE,
                                size=16,
                                weight=ft.FontWeight.BOLD,
                            ),
                            padding=ft.padding.only(left=10),
                        ),
                        ft.Container(
                            content=ft.Text(
                                f"{self.sets} sets",
                                text_align=ft.TextAlign.CENTER,
                                color=ft.Colors.WHITE,
                                size=16,
                                weight=ft.FontWeight.BOLD,
                            ),
                            padding=ft.padding.only(right=10),
                        ),
                    ],
                ),
            ),
        ]

    def default_favorite_click(self, e):
        self.is_favorited = not self.is_favorited
        self.favorite_icon.icon = (
            ft.icons.STAR if self.is_favorited else ft.icons.STAR_BORDER
        )
        self.favorite_icon.icon_color = (
            ft.Colors.YELLOW_500 if self.is_favorited else ft.Colors.WHITE
        )
        self.favorite_icon.update()
