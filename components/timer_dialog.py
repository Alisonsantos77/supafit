import flet as ft
import threading
import time


class TimerDialog(ft.AlertDialog):
    def __init__(self, duration=60, on_complete=None):
        self.timer_text_ref = ft.Ref[ft.Text]()
        self.timer_progress_ref = ft.Ref[ft.ProgressRing]()

        super().__init__(
            modal=True,
            title=ft.Text("Cronômetro de Intervalo"),
            content=ft.Row(
                [
                    ft.Text(
                        ref=self.timer_text_ref,
                        value=f"Intervalo: {duration}s",
                        size=20,
                    ),
                    ft.ProgressRing(
                        ref=self.timer_progress_ref, value=1.0, width=50, height=50
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=20,
            ),
            actions=[
                ft.TextButton("Pausar", on_click=self.pause_timer),
                ft.TextButton("Continuar", on_click=self.resume_timer),
                ft.TextButton("Resetar", on_click=self.reset_timer),
                ft.TextButton("Fechar", on_click=self.close_timer),
            ],
            actions_alignment=ft.MainAxisAlignment.CENTER,
            content_padding=ft.padding.all(20),
            shape=ft.RoundedRectangleBorder(radius=10),
            on_dismiss=self.close_timer,
        )
        self.duration = duration
        self.initial_seconds = duration
        self.timer_seconds = duration
        self.timer_running = threading.Event()
        self.timer_paused = threading.Event()
        self.timer_paused.set()  # Começa pausado
        self.on_complete = on_complete
        self.haptic = ft.HapticFeedback()
        self.page = None

    def did_mount(self):
        self.page.overlay.append(self.haptic)

    def will_unmount(self):
        self.timer_running.clear()
        self.page.overlay.remove(self.haptic)

    def run_timer(self):
        while self.timer_seconds > 0 and self.timer_running.is_set():
            if not self.timer_paused.is_set():
                self.timer_text_ref.current.value = f"Intervalo: {self.timer_seconds}s"
                self.timer_progress_ref.current.value = (
                    self.timer_seconds / self.initial_seconds
                )
                self.timer_text_ref.current.update()
                self.timer_progress_ref.current.update()
                self.timer_seconds -= 1
                time.sleep(1)
        if self.timer_seconds == 0 and self.timer_running.is_set():
            self.haptic.light_impact()
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("Intervalo concluído!"), action="OK"
            )
            self.page.snack_bar.open = True
            self.page.close(self)
            self.timer_running.clear()
            if self.on_complete:
                self.on_complete()
            self.page.update()

    def start_timer(self, page):
        self.page = page
        self.timer_running.set()
        self.timer_paused.clear()
        page.open(self)
        threading.Thread(target=self.run_timer, daemon=True).start()

    def pause_timer(self, e):
        self.timer_paused.set()
        self.timer_text_ref.current.update()
        self.timer_progress_ref.current.update()

    def resume_timer(self, e):
        self.timer_paused.clear()

    def reset_timer(self, e):
        self.timer_seconds = self.duration
        self.timer_text_ref.current.value = f"Intervalo: {self.timer_seconds}s"
        self.timer_progress_ref.current.value = 1.0
        self.timer_paused.set()
        self.timer_text_ref.current.update()
        self.timer_progress_ref.current.update()

    def close_timer(self, e):
        self.timer_running.clear()
        self.page.close(self)
