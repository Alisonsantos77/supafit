import flet as ft
import asyncio
import threading
import time
from datetime import datetime
import logging
logger = logging.getLogger(__name__)

class TrainingTimer(ft.Container):
    """Timer principal do treino com design moderno"""

    def __init__(
        self, on_start=None, on_pause=None, on_resume=None, on_finish=None, ref=None
    ):
        self.training_time = 0
        self.is_running = False
        self.timer_thread = None
        self.on_start = on_start
        self.on_pause = on_pause
        self.on_resume = on_resume
        self.on_finish = on_finish
        self.page = None

        self.time_display = ft.Text(
            "00:00:00",
            size=28,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.PRIMARY,
        )

        self.start_button = ft.FilledButton(
            "Iniciar Treino",
            icon=ft.Icons.PLAY_ARROW,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=25),
                padding=ft.padding.symmetric(horizontal=30, vertical=15),
            ),
            on_click=self._handle_start,
        )

        self.pause_button = ft.IconButton(
            icon=ft.Icons.PAUSE_ROUNDED,
            icon_size=24,
            style=ft.ButtonStyle(
                shape=ft.CircleBorder(),
                padding=ft.padding.all(12),
            ),
            tooltip="Pausar",
            visible=False,
            on_click=self._handle_pause,
        )

        self.resume_button = ft.IconButton(
            icon=ft.Icons.PLAY_ARROW_ROUNDED,
            icon_size=24,
            style=ft.ButtonStyle(
                shape=ft.CircleBorder(),
                padding=ft.padding.all(12),
            ),
            tooltip="Continuar",
            visible=False,
            on_click=self._handle_resume,
        )

        self.finish_button = ft.OutlinedButton(
            "Finalizar",
            icon=ft.Icons.STOP_ROUNDED,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=20),
                side=ft.BorderSide(color=ft.Colors.ERROR, width=2),
                color=ft.Colors.ERROR,
                padding=ft.padding.symmetric(horizontal=20, vertical=10),
            ),
            visible=False,
            on_click=self._handle_finish,
        )

        self.controls_row = ft.Row(
            [self.pause_button, self.resume_button, self.finish_button],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10,
        )

        super().__init__(
            content=ft.Column(
                [
                    ft.Row([self.time_display], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Row([self.start_button], alignment=ft.MainAxisAlignment.CENTER),
                    self.controls_row,
                ],
                spacing=15,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=20,
            border_radius=15,
            border=ft.border.all(1, ft.Colors.OUTLINE),
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=10,
                color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
            ),
            ref=ref,
        )

    def _run_timer(self):
        """Timer rodando em thread separada"""
        while self.is_running:
            if self.page:
                self.training_time += 1
                hours, remainder = divmod(self.training_time, 3600)
                minutes, seconds = divmod(remainder, 60)
                self.time_display.value = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                try:
                    self.time_display.update()
                except:
                    pass
            time.sleep(1)

    def _handle_start(self, e):
        self.is_running = True
        self.page = e.page
        self.start_button.visible = False
        self.pause_button.visible = True
        self.finish_button.visible = True
        if self.on_start:
            self.on_start()
        self.timer_thread = threading.Thread(target=self._run_timer, daemon=True)
        self.timer_thread.start()
        self.update()

    def _handle_pause(self, e):
        self.is_running = False
        self.pause_button.visible = False
        self.resume_button.visible = True
        if self.on_pause:
            self.on_pause()
        self.update()

    def _handle_resume(self, e):
        self.is_running = True
        self.pause_button.visible = True
        self.resume_button.visible = False
        if self.on_resume:
            self.on_resume()
        self.timer_thread = threading.Thread(target=self._run_timer, daemon=True)
        self.timer_thread.start()
        self.update()

    def _handle_finish(self, e):
        self.is_running = False
        if self.on_finish:
            self.on_finish()


class RestTimerDialog(ft.AlertDialog):
    """Timer de intervalo mais visível e intuitivo"""

    def __init__(self, duration=60, exercise_name="", on_complete=None, page=None):
        super().__init__(modal=True)
        self.duration = duration
        self.remaining_time = duration
        self.exercise_name = exercise_name
        self.on_complete = on_complete
        self.page = page
        self.is_running = False
        self.is_paused = False
        self.haptic = ft.HapticFeedback()
        self._task = None

        self.time_text_ref = ft.Ref[ft.Text]()
        self.progress_ring_ref = ft.Ref[ft.ProgressRing]()

        self.progress_ring = ft.ProgressRing(
            ref=self.progress_ring_ref,
            value=1.0,
            width=120,
            height=120,
            stroke_width=8,
            color=ft.Colors.PRIMARY,
        )

        self.time_text = ft.Text(
            ref=self.time_text_ref,
            value=self._format_time(duration),
            size=32,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.PRIMARY,
            text_align=ft.TextAlign.CENTER,
        )

        self.exercise_text = ft.Text(
            f"Intervalo - {exercise_name}",
            size=16,
            weight=ft.FontWeight.W_500,
            text_align=ft.TextAlign.CENTER,
        )

        self.play_pause_btn = ft.IconButton(
            icon=ft.Icons.PAUSE_ROUNDED,
            icon_size=32,
            style=ft.ButtonStyle(
                shape=ft.CircleBorder(),
                padding=ft.padding.all(16),
            ),
            on_click=self._toggle_pause,
        )

        self.reset_btn = ft.IconButton(
            icon=ft.Icons.REFRESH_ROUNDED,
            icon_size=24,
            style=ft.ButtonStyle(
                shape=ft.CircleBorder(),
                padding=ft.padding.all(12),
            ),
            tooltip="Reiniciar",
            on_click=self._reset_timer,
        )

        self.close_btn = ft.IconButton(
            icon=ft.Icons.CLOSE_ROUNDED,
            icon_size=24,
            style=ft.ButtonStyle(
                shape=ft.CircleBorder(),
                padding=ft.padding.all(12),
            ),
            tooltip="Fechar",
            on_click=self._close_dialog,
        )

        timer_stack = ft.Stack(
            [
                self.progress_ring,
                ft.Container(
                    content=self.time_text,
                    alignment=ft.alignment.center,
                ),
            ],
            width=120,
            height=120,
        )

        content = ft.Column(
            [
                self.exercise_text,
                ft.Container(height=20),
                timer_stack,
                ft.Container(height=20),
                ft.Row(
                    [
                        self.reset_btn,
                        self.play_pause_btn,
                        self.close_btn,
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=20,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
        )

        self.content = ft.Container(
            content=content,
            width=300,
            height=280,
            padding=20,
        )
        self.shape = ft.RoundedRectangleBorder(radius=20)
        self.on_dismiss = self._close_dialog

    def did_mount(self):
        if self.page and self.haptic not in self.page.overlay:
            self.page.overlay.append(self.haptic)

    def will_unmount(self):
        self.is_running = False
        if self.page and self.haptic in self.page.overlay:
            self.page.overlay.remove(self.haptic)

    def _format_time(self, seconds):
        """Formata o tempo em MM:SS"""
        minutes, secs = divmod(seconds, 60)
        return f"{minutes:02d}:{secs:02d}"

    async def _run_timer(self):
        while self.is_running and self.remaining_time > 0:
            if not self.is_paused:
                self.time_text_ref.current.value = self._format_time(
                    self.remaining_time
                )
                self.progress_ring_ref.current.value = (
                    self.remaining_time / self.duration
                )
                try:
                    self.time_text_ref.current.update()
                    self.progress_ring_ref.current.update()
                except Exception as e:
                    logger.error(f"Erro ao atualizar UI do timer: {e}")
                self.remaining_time -= 1
            await asyncio.sleep(1)
        if self.remaining_time <= 0 and self.is_running:
            self._timer_completed()

    def start_timer(self, page):
        self.page = page
        self.is_running = True
        if self.page and self.haptic not in self.page.overlay:
            self.page.overlay.append(self.haptic)
        self.page.open(self)
        self._task = page.run_task(self._run_timer)

    def _timer_completed(self):
        if self.page and self.haptic in self.page.overlay:
            try:
                self.haptic.light_impact()
            except Exception as e:
                logger.error(f"Erro ao executar haptic feedback: {e}")
        if self.page:
            try:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("⏰ Intervalo concluído!", size=16, color=ft.Colors.WHITE),
                    action="OK",
                    duration=2000,
                    bgcolor=ft.Colors.PRIMARY,
                )
                self.page.snack_bar.open = True
                self.page.update()
            except Exception as e:
                logger.error(f"Erro ao exibir SnackBar: {e}")
        if self.on_complete:
            self.on_complete()
        self._close_dialog(None)

    def _toggle_pause(self, e):
        self.is_paused = not self.is_paused
        self.play_pause_btn.icon = (
            ft.Icons.PLAY_ARROW_ROUNDED if self.is_paused else ft.Icons.PAUSE_ROUNDED
        )
        try:
            self.play_pause_btn.update()
        except Exception as e:
            logger.error(f"Erro ao atualizar botão de pausa: {e}")

    def _reset_timer(self, e):
        self.remaining_time = self.duration
        self.is_paused = False
        self.time_text_ref.current.value = self._format_time(self.duration)
        self.progress_ring_ref.current.value = 1.0
        self.play_pause_btn.icon = ft.Icons.PAUSE_ROUNDED
        try:
            self.time_text_ref.current.update()
            self.progress_ring_ref.current.update()
            self.play_pause_btn.update()
        except Exception as e:
            logger.error(f"Erro ao resetar timer: {e}")

    def _close_dialog(self, e):
        self.is_running = False
        if self._task:
            self._task.cancel()
            self._task = None
        if self.page:
            try:
                self.page.close(self)
            except Exception as e:
                logger.error(f"Erro ao fechar diálogo: {e}")


class EmptyTrainingState(ft.Container):
    """Estado vazio quando não há exercícios"""

    def __init__(self, day_name: str):
        empty_content = ft.Column(
            [
                ft.Icon(
                    ft.Icons.FITNESS_CENTER_OUTLINED,
                    size=80,
                ),
                ft.Text(
                    "Nenhum exercício encontrado",
                    size=20,
                    weight=ft.FontWeight.W_500,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    f"Não há exercícios programados para {day_name.capitalize()}.",
                    size=14,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(height=20),
                ft.OutlinedButton(
                    "Voltar ao Início",
                    icon=ft.Icons.HOME_ROUNDED,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=25),
                        padding=ft.padding.symmetric(horizontal=30, vertical=15),
                    ),
                    on_click=lambda e: e.page.go("/home") if e.page else None,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=15,
        )
        super().__init__(
            content=empty_content,
            padding=40,
            alignment=ft.alignment.center,
            expand=True,
        )


class TrainingProgress(ft.Container):
    """Indicador de progresso do treino"""

    def __init__(
        self, completed_exercises: int, total_exercises: int, ref=None, visible=True
    ):
        self.completed_exercises = completed_exercises
        self.total_exercises = total_exercises
        progress = completed_exercises / total_exercises if total_exercises > 0 else 0
        self.progress_bar = ft.ProgressBar(
            value=progress,
            height=8,
            border_radius=4,
            color=ft.Colors.PRIMARY,
        )
        self.progress_text = ft.Text(
            f"{completed_exercises}/{total_exercises} exercícios concluídos",
            size=14,
        )
        self.percentage_text = ft.Text(
            f"{int(progress * 100)}%",
            size=14,
            weight=ft.FontWeight.W_500,
            color=ft.Colors.PRIMARY,
        )
        super().__init__(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            self.progress_text,
                            self.percentage_text,
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    self.progress_bar,
                ],
                spacing=8,
            ),
            padding=ft.padding.symmetric(horizontal=20, vertical=15),
            border_radius=10,
            ref=ref,
            visible=visible,
        )

    def update_progress(self, completed: int):
        self.completed_exercises = completed
        progress = completed / self.total_exercises if self.total_exercises > 0 else 0
        self.progress_bar.value = progress
        self.progress_text.value = (
            f"{completed}/{self.total_exercises} exercícios concluídos"
        )
        self.percentage_text.value = f"{int(progress * 100)}%"
        self.update()


class FinishTrainingDialog(ft.AlertDialog):
    """Diálogo de confirmação para finalizar treino"""

    def __init__(
        self,
        training_time: int,
        completed_exercises: int,
        total_exercises: int,
        on_confirm=None,
    ):
        self.training_time = training_time
        self.completed_exercises = completed_exercises
        self.total_exercises = total_exercises
        self.on_confirm = on_confirm
        hours, remainder = divmod(training_time, 3600)
        minutes, seconds = divmod(remainder, 60)
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        content = ft.Column(
            [
                ft.Icon(
                    ft.Icons.TIMER_ROUNDED,
                    size=48,
                    color=ft.Colors.PRIMARY,
                ),
                ft.Text(
                    "Resumo do Treino",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(height=10),
                ft.Row(
                    [
                        ft.Icon(
                            ft.Icons.SCHEDULE_ROUNDED,
                            size=20,
                        ),
                        ft.Text(f"Tempo total: {time_str}", size=16),
                    ],
                    spacing=10,
                ),
                ft.Row(
                    [
                        ft.Icon(
                            ft.Icons.FITNESS_CENTER_ROUNDED,
                            size=20,
                        ),
                        ft.Text(
                            f"Exercícios: {completed_exercises}/{total_exercises}",
                            size=16,
                        ),
                    ],
                    spacing=10,
                ),
                ft.Container(height=10),
                ft.Text(
                    "Deseja finalizar o treino?",
                    size=16,
                    text_align=ft.TextAlign.CENTER,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=5,
        )
        super().__init__(
            modal=True,
            title=ft.Text("Finalizar Treino", weight=ft.FontWeight.BOLD),
            content=ft.Container(content=content, width=300, padding=20),
            actions=[
                ft.TextButton(
                    "Cancelar",
                    on_click=self._handle_cancel,
                ),
                ft.FilledButton(
                    "Finalizar",
                    icon=ft.Icons.CHECK_ROUNDED,
                    on_click=self._handle_confirm,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            shape=ft.RoundedRectangleBorder(radius=15),
        )

    def _handle_cancel(self, e):
        e.page.close(self)

    def _handle_confirm(self, e):
        if self.on_confirm:
            self.on_confirm()
        e.page.close(self)
