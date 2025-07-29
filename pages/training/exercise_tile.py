import flet as ft
from flet_video import Video, VideoMedia
import logging
import os

from components.components import LoadEditor, TimerDialog
from .training_components import RestTimerDialog

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
        on_complete=None,
        page=None,
        supabase=None,
        rest_duration: int = 60,
        ref=None,
    ):
        """Inicializa o componente de exercício com nome, séries, repetições, carga e mídia."""
        super().__init__(ref=ref)
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
        self.on_complete = on_complete
        self.rest_duration = rest_duration

        # Estados do exercício
        self.is_favorited = False
        self.is_completed = False
        self.completed_sets = 0
        self.series_completed = [
            False
        ] * self.series
        self._was_completed = False  # Rastreia se já foi concluído anteriormente

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

        self.completion_overlay = ft.Container(
            content=ft.Icon(
                ft.Icons.CHECK_CIRCLE_ROUNDED,
                size=60,
                color=ft.Colors.WHITE,
            ),
            alignment=ft.alignment.center,
            bgcolor=ft.Colors.with_opacity(0.8, ft.Colors.PRIMARY),
            visible=False,
            expand=True,
        )

        media_stack = ft.Stack(
            [
                media,
                self.completion_overlay,
            ],
            expand=True,
        )

        exercise_header = ft.Row(
            [
                ft.Column(
                    [
                        ft.Text(
                            exercise_name,
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                        ft.Row(
                            [
                                ft.Icon(
                                    ft.Icons.FITNESS_CENTER,
                                    size=16,
                                ),
                                ft.Text(
                                    f"{series} séries",
                                    size=14,
                                ),
                                ft.Icon(
                                    ft.Icons.REPEAT,
                                    size=16,
                                ),
                                ft.Text(
                                    f"{repetitions} reps",
                                    size=14,
                                ),
                            ],
                            spacing=5,
                        ),
                    ],
                    spacing=5,
                    expand=True,
                ),
                self._create_sets_progress_indicator(),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        # Editor de carga
        load_editor = LoadEditor(
            initial_load=load,
            exercise_id=self.exercise_id,
            plan_id=self.plan_id,
            user_id=self.user_id,
            on_save=on_load_save,
            supabase=self.supabase,
            enabled=False,
        )

        self.rest_button = ft.FilledButton(
            text=f"Intervalo ({rest_duration}s)",
            icon=ft.Icons.TIMER_ROUNDED,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
                padding=ft.padding.symmetric(horizontal=12, vertical=8),
                bgcolor=ft.Colors.PRIMARY,
                color=ft.Colors.ON_PRIMARY,
                text_style=ft.TextStyle(size=14),
            ),
            on_click=self._start_rest_timer,
            disabled=True,
            col={"xs": 12, "sm": 12},
        )

        self.series_buttons = []
        self._create_series_buttons()

        self.favorite_icon = ft.Icon(
            ft.Icons.STAR_BORDER,
            size=28,
            color=ft.Colors.AMBER if self.is_favorited else None,
        )
        self.favorite_container = ft.AnimatedSwitcher(
            self.favorite_icon,
            transition=ft.AnimatedSwitcherTransition.SCALE,
            duration=300,
            reverse_duration=200,
        )

        favorite_button = ft.IconButton(
            content=self.favorite_container,
            tooltip="Favoritar",
            on_click=self.toggle_favorite,
            style=ft.ButtonStyle(
                shape=ft.CircleBorder(),
                padding=ft.padding.all(10),
                icon_color=ft.Colors.AMBER,
            ),
        )

        series_buttons_row = ft.ResponsiveRow(
            self.series_buttons,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=8,
            run_spacing=8,
        )

        controls_row = ft.Row(
            [
                self.rest_button,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        )

        super().__init__(
            content=ft.Column(
                [
                    media_stack,
                    exercise_header,
                    load_editor,
                    series_buttons_row,
                    controls_row,
                ],
                spacing=10,
                expand=True,
            ),
            padding=10,
            border_radius=10,
            border=ft.border.all(1, ft.Colors.OUTLINE),
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=8,
                color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
            ),
            margin=ft.margin.symmetric(vertical=8),
            animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
        )

        self.load_editor = load_editor

    def _create_series_buttons(self):
        """Creates numbered buttons for each series"""
        self.series_buttons = []
        for i in range(self.series):
            button = ft.ElevatedButton(
                text=str(i + 1),
                width=45,
                height=45,
                style=self._get_series_button_style(i),
                on_click=lambda e, series_index=i: self._toggle_series(series_index),
                disabled=True,
                col={"xs": 2, "sm": 2},
            )
            self.series_buttons.append(button)

    def _get_series_button_style(self, series_index):
        """Returns appropriate style for series button based on its state"""
        if self.series_completed[series_index]:
            return ft.ButtonStyle(
                shape=ft.CircleBorder(),
                bgcolor=ft.Colors.GREEN_600,
                color=ft.Colors.WHITE,
                text_style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD),
            )
        elif series_index == self.completed_sets:
            return ft.ButtonStyle(
                shape=ft.CircleBorder(),
                bgcolor=ft.Colors.PRIMARY,
                color=ft.Colors.WHITE,
                text_style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD),
            )
        elif series_index < self.completed_sets:
            return ft.ButtonStyle(
                shape=ft.CircleBorder(),
                text_style=ft.TextStyle(size=16),
            )
        else:
            return ft.ButtonStyle(
                shape=ft.CircleBorder(),
                bgcolor=ft.Colors.OUTLINE_VARIANT,
                color=ft.Colors.OUTLINE,
                text_style=ft.TextStyle(size=16),
            )

    def _update_series_buttons(self):
        """Updates all series buttons styles and states"""
        for i, button in enumerate(self.series_buttons):
            button.style = self._get_series_button_style(i)
            if i <= self.completed_sets:
                button.disabled = False
            else:
                button.disabled = True

            if self.series_completed[i]:
                button.text = "✓"
            else:
                button.text = str(i + 1)

    def _toggle_series(self, series_index):
        """Toggles completion state of a specific series"""
        if series_index > self.completed_sets:
            return

        if self.series_completed[series_index]:
            for i in range(series_index, self.series):
                self.series_completed[i] = False
            self.completed_sets = series_index
        else:
            self.series_completed[series_index] = True
            self.completed_sets = series_index + 1

        previous_completion_state = self.is_completed
        all_series_completed = all(self.series_completed)

        if all_series_completed and not self.is_completed:
            self.is_completed = True
            self.completion_overlay.visible = True
            self.border = ft.border.all(2, ft.Colors.PRIMARY)
            self.bgcolor = ft.Colors.with_opacity(0.05, ft.Colors.PRIMARY)
            if self.on_complete:
                self.on_complete(increment=True)
            if self.page:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(
                        f"🎉 {self.exercise_name} - Todas as séries concluídas!",
                        color=ft.Colors.WHITE,
                    ),
                    bgcolor=ft.Colors.GREEN_700,
                    duration=3000,
                )
                self.page.snack_bar.open = True
                self.page.update()
        elif not all_series_completed and self.is_completed:
            self.is_completed = False
            self.completion_overlay.visible = False
            self.border = ft.border.all(1, ft.Colors.OUTLINE)
            self.bgcolor = None
            if self.on_complete:
                self.on_complete(increment=False)
            if self.page:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(
                        f"↩️ {self.exercise_name} - Série desmarcada!",
                        color=ft.Colors.WHITE,
                    ),
                    bgcolor=ft.Colors.BLUE_700,
                    duration=2000,
                )
                self.page.snack_bar.open = True
                self.page.update()

        self._update_series_buttons()
        self._update_progress_indicator()
        self.update()

        logger.info(
            f"Série {series_index + 1} {'marcada' if self.series_completed[series_index] else 'desmarcada'} "
            f"para {self.exercise_name}. Exercício {'completo' if self.is_completed else 'incompleto'}"
        )

    def _create_sets_progress_indicator(self):
        """Cria indicador visual do progresso das séries"""
        self.progress_indicators = []
        for i in range(self.series):
            indicator = ft.Container(
                width=12,
                height=12,
                border_radius=6,
                bgcolor=(
                    ft.Colors.PRIMARY if self.series_completed[i] else ft.Colors.OUTLINE
                ),
                border=ft.border.all(1, ft.Colors.OUTLINE),
            )
            self.progress_indicators.append(indicator)

        completed_count = sum(self.series_completed)
        self.progress_text = ft.Text(
            f"{completed_count}/{self.series}",
            size=12,
            text_align=ft.TextAlign.CENTER,
        )

        return ft.Column(
            [
                self.progress_text,
                ft.Row(self.progress_indicators, spacing=2),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=5,
        )

    def _update_progress_indicator(self):
        """Updates the progress indicator to reflect current series completion"""
        completed_count = sum(self.series_completed)
        self.progress_text.value = f"{completed_count}/{self.series}"

        for i, indicator in enumerate(self.progress_indicators):
            indicator.bgcolor = (
                ft.Colors.PRIMARY if self.series_completed[i] else ft.Colors.OUTLINE
            )

    def _start_rest_timer(self, e):
        """Inicia o timer de descanso moderno - apenas cronômetro, não afeta séries"""
        if self.page:

            def on_timer_complete():
                if self.page:
                    self.page.snack_bar = ft.SnackBar(
                        content=ft.Text(
                            f"⏰ Tempo de descanso finalizado para {self.exercise_name}!",
                            color=ft.Colors.WHITE,
                        ),
                        bgcolor=ft.Colors.PRIMARY,
                        duration=2000,
                    )
                    self.page.snack_bar.open = True
                    self.page.update()
                    logger.info(
                        f"Timer de descanso finalizado para {self.exercise_name}"
                    )

            rest_timer = RestTimerDialog(
                duration=self.rest_duration,
                exercise_name=self.exercise_name,
                on_complete=on_timer_complete,
                page=self.page,
            )
            rest_timer.start_timer(self.page)

    def toggle_favorite(self, e=None):
        """Alterna o estado de favorito"""
        self.is_favorited = not self.is_favorited
        self.favorite_icon.name = (
            ft.Icons.STAR if self.is_favorited else ft.Icons.STAR_BORDER
        )
        self.favorite_icon.color = ft.Colors.AMBER if self.is_favorited else None
        self.favorite_container.content = self.favorite_icon
        if self.on_favorite_click:
            self.on_favorite_click(self)
        logger.info(
            f"Exercício {self.exercise_name} {'favoritado' if self.is_favorited else 'desfavoritado'}"
        )
        self.update()

    def enable_controls(self):
        """Habilita os controles do exercício quando o treino inicia"""
        if not self.is_completed:
            self.load_editor.enable()
            self.rest_button.disabled = False
            for i, button in enumerate(self.series_buttons):
                button.disabled = i > self.completed_sets
        logger.debug(f"Controles habilitados para {self.exercise_name}")
        self.update()

    def disable_controls(self):
        """Desabilita os controles do exercício"""
        self.load_editor.disable()
        self.rest_button.disabled = True
        for button in self.series_buttons:
            button.disabled = True
        logger.debug(f"Controles desabilitados para {self.exercise_name}")
        self.update()

    def reset_exercise(self):
        """Reseta o estado do exercício"""
        self.is_completed = False
        self._was_completed = False
        self.completed_sets = 0
        self.series_completed = [False] * self.series
        self.completion_overlay.visible = False
        self.border = ft.border.all(1, ft.Colors.OUTLINE)
        self.bgcolor = None
        self._update_series_buttons()
        for button in self.series_buttons:
            button.disabled = True
        logger.debug(f"Exercício {self.exercise_name} resetado")
        self.update()
