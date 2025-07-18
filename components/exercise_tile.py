import flet as ft
from flet_video import Video, VideoMedia
import logging
import os

from components.components import LoadEditor, TimerDialog

logger = logging.getLogger("supafit.exercise_tile")


class ExerciseTile(ft.Container):
    def __init__(
        self,
        exercise_name: str,
        series: int,
        repetitions: int,
        load: float,
        video_url: str = None,
        image_url: str = None,
        exercise_id: str = None,
        plan_id: str = None,
        user_id: str = None,
        on_favorite_click=None,
        on_load_save=None,
        page=None,
        supabase=None,
        rest_duration: int = 60,
    ):
        """Inicializa o componente de exercício com nome, séries, repetições, carga e mídia."""
        self.exercise_name = exercise_name
        self.series = series
        self.repetitions = repetitions
        self.exercise_id = exercise_id
        self.plan_id = plan_id
        self.user_id = user_id
        self.video_url = video_url
        self.image_url = image_url or "https://picsum.photos/200"
        self.page = page
        self.supabase = supabase
        self.on_favorite_click = on_favorite_click
        self.on_load_save = on_load_save
        self.rest_duration = rest_duration

        def get_video_source():
            logger.info(
                f"Carregando vídeo diretamente do Supabase para {self.exercise_name}: {self.video_url}"
            )
            return self.video_url

        url = get_video_source()
        if url:
            media = Video(
                playlist=[VideoMedia(url)],
                expand=True,
                aspect_ratio=16 / 9,
                fit=ft.ImageFit.COVER,
                autoplay=True,
                show_controls=True,
                filter_quality=ft.FilterQuality.MEDIUM,
                on_loaded=lambda e: logger.info(
                    f"Vídeo carregado para {self.exercise_name}"
                ),
                on_error=lambda e: logger.error(
                    f"Erro ao carregar vídeo para {self.exercise_name}: {e}"
                ),
                on_enter_fullscreen=lambda e: logger.info(
                    f"Entrou em tela cheia para {self.exercise_name}"
                ),
                on_exit_fullscreen=lambda e: logger.info(
                    f"Saiu de tela cheia para {self.exercise_name}"
                ),
            )
        else:
            logger.warning(
                f"Sem URL de vídeo para {self.exercise_name}, usando imagem padrão"
            )
            media = ft.Image(
                src=self.image_url,
                expand=True,
                fit=ft.ImageFit.COVER,
                border_radius=ft.border_radius.all(10),
                error_content=ft.Icon(ft.Icons.ERROR),
            )

        media_container = ft.Container(
            content=media,
            expand=True,
        )

        details = ft.Column(
            [
                ft.Text(exercise_name, size=18, weight=ft.FontWeight.BOLD),
                ft.Text(f"Séries: {series} | Repetições: {repetitions}"),
            ],
            spacing=5,
        )

        load_editor = LoadEditor(
            initial_load=load,
            exercise_id=self.exercise_id,
            plan_id=self.plan_id,
            user_id=self.user_id,
            on_save=on_load_save,
            supabase=self.supabase,
            enabled=False,
        )

        interval_button = ft.ElevatedButton(
            f"Iniciar Intervalo ({self.rest_duration}s)",
            on_click=lambda e: TimerDialog(duration=self.rest_duration).start_timer(
                page
            ),
            disabled=True,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        )

        self.favorite_icon = ft.Icon(ft.Icons.STAR_BORDER, size=24)
        self.favorite_container = ft.AnimatedSwitcher(
            self.favorite_icon,
            transition=ft.AnimatedSwitcherTransition.SCALE,
            duration=300,
            reverse_duration=200,
        )
        action_buttons = ft.Row(
            [
                ft.IconButton(
                    content=self.favorite_container,
                    tooltip="Favoritar",
                    on_click=lambda e: self.toggle_favorite(),
                ),
            ],
            spacing=10,
        )

        super().__init__(
            content=ft.Column(
                [
                    media_container,
                    details,
                    load_editor,
                    interval_button,
                    action_buttons,
                ],
                expand=True,
                spacing=10,
            ),
            padding=10,
            border_radius=10,
            margin=ft.margin.symmetric(vertical=10),
        )

        self.load_editor = load_editor
        self.interval_button = interval_button
        self.is_favorited = False

    def toggle_favorite(self):
        self.is_favorited = not self.is_favorited
        self.favorite_icon.name = (
            ft.Icons.STAR if self.is_favorited else ft.Icons.STAR_BORDER
        )
        self.favorite_container.content = self.favorite_icon
        if self.on_favorite_click:
            self.on_favorite_click(self)
        logger.info(
            f"Exercício {self.exercise_name} {'favoritado' if self.is_favorited else 'desfavoritado'}"
        )
        self.update()

    def enable_controls(self):
        self.load_editor.enable()
        self.interval_button.disabled = False
        logger.debug(f"Controles habilitados para {self.exercise_name}")
        self.update()

    def disable_controls(self):
        self.load_editor.disable()
        self.interval_button.disabled = True
        logger.debug(f"Controles desabilitados para {self.exercise_name}")
        self.update()
