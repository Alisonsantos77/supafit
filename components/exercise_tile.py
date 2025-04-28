import flet as ft
import logging
from components.components import LoadEditor
from components.components import TimerDialog

logger = logging.getLogger("supafit.exercise_tile")


class ExerciseTile(ft.Container):
    def __init__(
        self,
        exercise_name: str,
        series: int,
        repetitions: int,
        load: float,
        animation_url: str,
        image_url: str = None,
        body_part: str = None,
        target: str = None,
        secondary_muscles: list = None,
        instructions: list = None,
        on_favorite_click=None,
        on_load_save=None,
        supabase=None,
        exercise_id=None,
        page=None,
    ):
        logger.debug(
            f"Carregando ExerciseTile para {exercise_name} com animation_url: {animation_url}, image_url: {image_url}"
        )

        # Imagem clicável com animação
        self.animation_url = animation_url or image_url or "https://picsum.photos/200"
        self.body_part = body_part
        self.target = target
        self.secondary_muscles = secondary_muscles or []
        self.instructions = instructions or []

        image = ft.Image(
            src=self.animation_url,
            width=150,
            height=150,
            fit=ft.ImageFit.COVER,
            border_radius=ft.border_radius.all(10),
            error_content=ft.Icon(ft.Icons.ERROR),
        )
        image_container = ft.GestureDetector(
            content=image,
            on_tap=lambda e: self.show_animation(exercise_name),
        )

        # Detalhes do exercício
        details = ft.Column(
            [
                ft.Text(exercise_name, size=18, weight=ft.FontWeight.BOLD),
                ft.Text(f"Séries: {series} | Repetições: {repetitions}"),
            ],
            spacing=5,
        )

        # Editor de carga
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

        # Botões de ação (apenas favoritar)
        action_buttons = ft.Row(
            [
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
                    image_container,
                    ft.Column(
                        [
                            details,
                            load_editor,
                            interval_button,
                            action_buttons,
                        ],
                        expand=True,
                        spacing=10,
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
        self.exercise_name = exercise_name
        self.supabase = supabase
        self.page = page

    def show_animation(self, exercise_name):
        logger.debug(f"Exibindo animação para {exercise_name}: {self.animation_url}")
        # Criar conteúdo do diálogo com mais informações
        muscles_info = ft.Column(
            [
                ft.Text(f"Músculo Principal: {self.body_part}", size=14),
                ft.Text(f"Alvo: {self.target}", size=14),
                ft.Text(
                    f"Músculos Secundários: {', '.join(self.secondary_muscles)}",
                    size=14,
                ),
            ],
            spacing=5,
        )
        instructions_info = ft.Column(
            [
                ft.Text(f"{i+1}. {step}", size=12)
                for i, step in enumerate(self.instructions)
            ],
            spacing=3,
            scroll=ft.ScrollMode.AUTO,
            height=150,
        )
        dialog_content = ft.Column(
            [
                ft.Image(
                    src=self.animation_url,
                    width=300,
                    height=300,
                    fit=ft.ImageFit.CONTAIN,
                ),
                muscles_info,
                ft.Text("Instruções:", size=16, weight=ft.FontWeight.BOLD),
                instructions_info,
            ],
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
        )
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Animação: {exercise_name}"),
            content=dialog_content,
            actions=[
                ft.TextButton("Fechar", on_click=lambda e: self.page.close(dialog))
            ],
        )
        self.page.open(dialog)

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
