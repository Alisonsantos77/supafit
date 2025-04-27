import flet as ft
from components.load_editor import LoadEditor
from components.timer_dialog import TimerDialog


class ExerciseTile(ft.Container):
    def __init__(
        self,
        exercise_name: str,
        series: int,
        repetitions: int,
        load: float,
        image_url: str,
        on_play_click=None,
        on_favorite_click=None,
        on_load_save=None,
        supabase=None,
        exercise_id=None,
        page=None,
    ):
        # Imagem maior
        image = ft.Image(
            src=image_url,
            width=150,
            height=150,
            fit=ft.ImageFit.COVER,
            border_radius=ft.border_radius.all(10),
            error_content=ft.Icon(ft.Icons.ERROR),
        )

        # Detalhes do exercício
        details = ft.Column(
            [
                ft.Text(exercise_name, size=18, weight=ft.FontWeight.BOLD),
                ft.Text(f"Séries: {series} | Repetições: {repetitions}"),
            ],
            spacing=5,
        )

        # Editor de carga (desabilitado por padrão)
        load_editor = LoadEditor(
            initial_load=load,
            exercise_id=exercise_id,
            on_save=on_load_save,
            supabase=supabase,
            enabled=False,
        )

        # Botão de intervalo
        interval_button = ft.ElevatedButton(
            "Iniciar Intervalo (60s)",
            on_click=lambda e: TimerDialog(duration=60).start_timer(page),
            disabled=True,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        )

        # Botão de favoritar com animação
        self.favorite_icon = ft.Icon(ft.Icons.STAR_BORDER, size=24)
        self.favorite_container = ft.AnimatedSwitcher(
            self.favorite_icon,
            transition=ft.AnimatedSwitcherTransition.SCALE,
            duration=300,
            reverse_duration=200,
        )

        # Botões de ação
        action_buttons = ft.Row(
            [
                ft.IconButton(
                    ft.Icons.PLAY_ARROW, tooltip="Assistir", on_click=on_play_click
                ),
                ft.IconButton(
                    content=self.favorite_container,
                    tooltip="Favoritar",
                    on_click=lambda e: self.toggle_favorite(on_favorite_click),
                ),
            ],
            spacing=10,
        )

        # Configuração do Container
        super().__init__(
            content=ft.Row(
                [
                    image,
                    ft.Column(
                        [
                            details,
                            load_editor,
                            interval_button,
                            action_buttons,
                        ],
                        expand=True,
                        spacing=10,
                        run_spacing=10,
                    ),
                ],
                alignment=ft.MainAxisAlignment.START,
                spacing=20,
            ),
            padding=10,
            border_radius=10,
            margin=ft.margin.symmetric(vertical=10),
        )

        # Atributos para controle
        self.load_editor = load_editor
        self.interval_button = interval_button
        self.is_favorited = False
        self.exercise_id = exercise_id
        self.supabase = supabase

    def toggle_favorite(self, on_favorite_click):
        self.is_favorited = not self.is_favorited
        self.favorite_icon.name = (
            ft.Icons.STAR if self.is_favorited else ft.Icons.STAR_BORDER
        )
        self.favorite_container.content = self.favorite_icon
        if on_favorite_click:
            on_favorite_click(self)
        self.update()

    def enable_controls(self):
        self.load_editor.enable()
        self.interval_button.disabled = False
        self.update()

    def disable_controls(self):
        self.load_editor.disable()
        self.interval_button.disabled = True
        self.update()
