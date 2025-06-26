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
        on_favorite_click=None,
        on_load_save=None,
        page=None,
    ):
        """Inicializa o componente de exercício com nome, séries, repetições, carga e mídia."""
        self.exercise_name = exercise_name
        self.series = series
        self.repetitions = repetitions
        self.video_url = video_url
        self.image_url = image_url or "https://picsum.photos/200"
        self.page = page
        self.on_favorite_click = on_favorite_click
        self.on_load_save = on_load_save

        def get_video_source():
            """Obtém a fonte do vídeo (local, client storage ou Supabase)."""
            try:
                cache_key = f"video_path_{self.exercise_name}"
                local_path = self.page.client_storage.get(cache_key)
                if local_path and os.path.exists(local_path.replace("file://", "")):
                    logger.info(
                        f"Carregando vídeo LOCAL para {self.exercise_name}: {local_path}"
                    )
                    return local_path
                logger.info(
                    f"Carregando vídeo REMOTO do Supabase para {self.exercise_name}: {self.video_url}"
                )
                return self.video_url
            except Exception as e:
                logger.error(
                    f"Erro ao obter fonte do vídeo para {self.exercise_name}: {str(e)}"
                )
                logger.info(f"Fallback para vídeo REMOTO do Supabase: {self.video_url}")
                return self.video_url

        url = get_video_source()
        if url:
            media = Video(
                playlist=[VideoMedia(url)],
                expand=True,
                aspect_ratio=16 / 9,
                fit=ft.ImageFit.COVER,
                autoplay=False,
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
            exercise_id=None,
            on_save=on_load_save,
            supabase=None,
            enabled=False,
        )

        interval_button = ft.ElevatedButton(
            "Iniciar Intervalo (60s)",
            on_click=lambda e: TimerDialog(duration=60).start_timer(page),
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
        """Alterna o estado de favorito do exercício."""
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
        """Habilita controles de carga e intervalo."""
        self.load_editor.enable()
        self.interval_button.disabled = False
        logger.debug(f"Controles habilitados para {self.exercise_name}")
        self.update()

    def disable_controls(self):
        """Desabilita controles de carga e intervalo."""
        self.load_editor.disable()
        self.interval_button.disabled = True
        logger.debug(f"Controles desabilitados para {self.exercise_name}")
        self.update()
