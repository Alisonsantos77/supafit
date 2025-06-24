import flet as ft
from flet_video import Video, VideoMedia
import logging
import json

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
        self.exercise_name = exercise_name
        self.series = series
        self.repetitions = repetitions
        self.video_url = self.validate_video_url(video_url, exercise_name)
        self.image_url = image_url or "https://picsum.photos/200"
        self.page = page

        # Load video_urls.json
        try:
            with open("video_urls.json", "r", encoding="utf-8") as f:
                self.video_urls = json.load(f)
            logger.info("video_urls.json loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load video_urls.json: {str(e)}")
            self.video_urls = {}

        # Select media component: video or image
        if self.video_url:
            try:
                media = Video(
                    playlist=[VideoMedia(self.video_url)],
                    autoplay=False,
                    show_controls=True,
                    expand=False,
                    width=150,
                    height=150,
                    fill_color=ft.Colors.BLACK,
                    filter_quality=ft.FilterQuality.HIGH,
                    on_loaded=lambda e: logger.info(
                        f"Video loaded for {self.exercise_name}: {self.video_url}"
                    ),
                    on_enter_fullscreen=lambda e: logger.info(
                        f"Entered fullscreen for {self.exercise_name}"
                    ),
                    on_exit_fullscreen=lambda e: logger.info(
                        f"Exited fullscreen for {self.exercise_name}"
                    ),
                )
            except Exception as e:
                logger.error(
                    f"Failed to initialize video for {self.exercise_name}: {str(e)}"
                )
                media = ft.Image(
                    src=self.image_url,
                    width=150,
                    height=150,
                    fit=ft.ImageFit.COVER,
                    border_radius=ft.border_radius.all(10),
                    error_content=ft.Icon(ft.Icons.ERROR),
                )
        else:
            logger.warning(
                f"No valid video URL for {self.exercise_name}, using fallback image"
            )
            media = ft.Image(
                src=self.image_url,
                width=150,
                height=150,
                fit=ft.ImageFit.COVER,
                border_radius=ft.border_radius.all(10),
                error_content=ft.Icon(ft.Icons.ERROR),
            )

        media_container = ft.GestureDetector(
            content=media,
            on_tap=lambda e: self.show_details(),
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
                    on_click=lambda e: self.toggle_favorite(on_favorite_click),
                ),
            ],
            spacing=10,
        )

        super().__init__(
            content=ft.Row(
                [
                    media_container,
                    ft.Column(
                        [details, load_editor, interval_button, action_buttons],
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

        self.load_editor = load_editor
        self.interval_button = interval_button
        self.is_favorited = False

    def validate_video_url(self, video_url: str, exercise_name: str) -> str:
        """Validates the video URL from video_urls.json or provided URL."""
        if video_url:
            logger.debug(f"Using provided video URL for {exercise_name}: {video_url}")
            return video_url

        try:
            video_url = self.video_urls.get(exercise_name)
            if video_url:
                logger.debug(f"Found video URL for {exercise_name}: {video_url}")
                return video_url
            else:
                logger.warning(
                    f"No video URL found in video_urls.json for {exercise_name}"
                )
                return None
        except AttributeError:
            logger.error(f"video_urls not loaded for {exercise_name}")
            return None

    def show_details(self):
        """Displays exercise details in a dialog with video or image."""
        content = []
        if self.video_url:
            try:
                content.append(
                    Video(
                        playlist=[VideoMedia(self.video_url)],
                        autoplay=False,
                        show_controls=True,
                        expand=False,
                        width=300,
                        height=300,
                        filter_quality=ft.FilterQuality.HIGH,
                        on_loaded=lambda e: logger.info(
                            f"Detail video loaded for {self.exercise_name}"
                        ),
                    )
                )
            except Exception as e:
                logger.error(
                    f"Failed to load detail video for {self.exercise_name}: {str(e)}"
                )
                content.append(
                    ft.Image(
                        src=self.image_url,
                        width=300,
                        height=300,
                        fit=ft.ImageFit.COVER,
                    )
                )
        else:
            logger.warning(
                f"No video URL for {self.exercise_name} in details, using image"
            )
            content.append(
                ft.Image(
                    src=self.image_url,
                    width=300,
                    height=300,
                    fit=ft.ImageFit.COVER,
                )
            )
        content.extend(
            [
                ft.Text(self.exercise_name, size=20, weight=ft.FontWeight.BOLD),
                ft.Text(f"Séries: {self.series} | Repetições: {self.repetitions}"),
            ]
        )

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Exercício: {self.exercise_name}"),
            content=ft.Column(content, spacing=10, scroll=ft.ScrollMode.AUTO),
            actions=[
                ft.TextButton("Fechar", on_click=lambda e: self.page.close(dialog))
            ],
        )
        self.page.open(dialog)

    def toggle_favorite(self, on_favorite_click):
        """Toggles favorite state and updates UI."""
        self.is_favorited = not self.is_favorited
        self.favorite_icon.name = (
            ft.Icons.STAR if self.is_favorited else ft.Icons.STAR_BORDER
        )
        self.favorite_container.content = self.favorite_icon
        if on_favorite_click:
            on_favorite_click(self)
        logger.info(
            f"Exercise {self.exercise_name} {'favorited' if self.is_favorited else 'unfavorited'}"
        )
        self.update()

    def enable_controls(self):
        """Enables load editor and interval button."""
        self.load_editor.enable()
        self.interval_button.disabled = False
        logger.debug(f"Controls enabled for {self.exercise_name}")
        self.update()

    def disable_controls(self):
        """Disables load editor and interval button."""
        self.load_editor.disable()
        self.interval_button.disabled = True
        logger.debug(f"Controls disabled for {self.exercise_name}")
        self.update()
