import asyncio
import flet as ft
import threading
import time
from flet import Icons


class CustomListTile(ft.ListTile):
    def __init__(self, leading=None, title=None, subtitle=None, content_padding=None):
        super().__init__()
        self.leading = leading
        self.title = title
        self.subtitle = subtitle
        self.content_padding = content_padding


class CustomAppBar(ft.AppBar):
    def __init__(self, page: ft.Page, user_id: str = None, on_menu_click=None):
        super().__init__()
        self.leading = ft.Icon(ft.Icons.FITNESS_CENTER, size=30)
        self.leading_width = 40
        self.title = ft.Text("SupaFit", size=20, weight=ft.FontWeight.BOLD)
        self.center_title = False
        self.elevation = 4
        self.actions = [
            ft.PopupMenuButton(
                items=[
                    ft.PopupMenuItem(
                        text="Perfil", on_click=lambda e: page.go("/profile_settings")
                    ),
                    ft.PopupMenuItem(
                        text="Histórico", on_click=lambda e: page.go("/history")
                    ),
                    ft.PopupMenuItem(
                        text="Pergunte ao Treinador",
                        on_click=lambda e: page.go("/trainer"),
                    ),
                    ft.PopupMenuItem(
                        text="Galeria de Vitórias",
                        on_click=lambda e: page.go("/community"),
                    ),
                    ft.PopupMenuItem(
                        text="Sair",
                        on_click=lambda e: self._handle_logout(page, user_id),
                    ),
                ]
            )
        ]
        self.on_menu_click = on_menu_click

    def _handle_logout(self, page: ft.Page, user_id: str):
        if user_id:
            supabase_service = page.get_control("supabase_service")
            supabase_service.logout(page)
        page.go("/login")


# Componentes de Avatares
class AvatarComponent(ft.CircleAvatar):
    def __init__(
        self, user_id=None, radius=20, is_trainer=False, image_url=None, **kwargs
    ):
        if image_url:
            self.image_url = image_url
        else:
            if not user_id:
                raise ValueError(
                    "user_id é obrigatório se image_url não for fornecido."
                )
            self.image_url = "mascote_supafit/coachito.png"
        super().__init__(foreground_image_src=self.image_url, radius=radius, **kwargs)
        self.on_click = self.handle_click

    def handle_click(self, e):
        print("Avatar clicked!")

    def build(self):
        return self


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

        self.leading = ft.Image(
            src=image_url,
            width=64,
            height=64,
            fit=ft.ImageFit.COVER,
            border_radius=ft.border_radius.all(10),
            error_content=ft.Icon(ft.Icons.ERROR_ROUNDED),
        )
        self.trailing = ft.Checkbox(value=is_current_day, disabled=True)
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


# Componentes de Cartões
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

        self.favorite_icon = ft.IconButton(
            icon=ft.Icons.STAR if self.is_favorited else ft.Icons.STAR_BORDER,
            icon_color=ft.Colors.YELLOW_500 if self.is_favorited else ft.Colors.WHITE,
            icon_size=30,
            tooltip="Favoritar",
            on_click=self.on_favorite_click,
        )

        self.controls = [
            ft.Container(
                height=self.height,
                width=self.width,
                border_radius=20,
                bgcolor=ft.Colors.GREY_900,
            ),
            ft.Container(
                image=ft.DecorationImage(
                    src=self.image_url,
                    fit=ft.ImageFit.COVER,
                ),
                height=self.height / 2,
                width=self.width,
                border_radius=ft.border_radius.only(top_left=20, top_right=20),
            ),
            ft.IconButton(
                icon=ft.Icons.PLAY_ARROW,
                icon_color=ft.Colors.WHITE,
                tooltip="Assistir",
                bottom=self.height / 4,
                top=self.height / 4,
                right=10,
                icon_size=40,
                on_click=self.on_play_click,
                enable_feedback=True,
            ),
            ft.Container(
                content=self.favorite_icon,
                top=5,
                right=10,
            ),
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
            ft.Icons.STAR if self.is_favorited else ft.Icons.STAR_BORDER
        )
        self.favorite_icon.icon_color = (
            ft.Colors.YELLOW_500 if self.is_favorited else ft.Colors.WHITE
        )
        self.favorite_icon.update()


# Componentes de Edição
class LoadEditor(ft.Row):
    def __init__(self, initial_load, exercise_id, on_save, supabase, enabled=False):
        super().__init__()
        self.initial_load = initial_load
        self.exercise_id = exercise_id
        self.on_save = on_save
        self.supabase = supabase
        self.enabled = enabled

        self.load_text = ft.Text(f"{initial_load}kg")
        self.load_field = ft.TextField(
            value=str(initial_load),
            width=100,
            keyboard_type=ft.KeyboardType.NUMBER,
            visible=False,
            label="Carga (kg)",
        )
        self.edit_button = ft.IconButton(
            icon=ft.Icons.EDIT,
            on_click=self.start_edit,
            tooltip="Editar carga",
            disabled=not self.enabled,
        )
        self.save_button = ft.IconButton(
            icon=ft.Icons.SAVE,
            visible=False,
            on_click=self.confirm_save,
            tooltip="Salvar carga",
            disabled=not self.enabled,
        )

        self.controls = [
            self.load_text,
            self.load_field,
            self.edit_button,
            self.save_button,
        ]
        self.spacing = 5
        self.alignment = ft.MainAxisAlignment.END

    def start_edit(self, e):
        if not self.enabled:
            return
        self.load_text.visible = False
        self.load_field.visible = True
        self.edit_button.visible = False
        self.save_button.visible = True
        self.update()

    def confirm_save(self, e):
        if not self.enabled:
            return

        def save_confirmed(e):
            if e.control.text == "Sim":
                try:
                    load = float(self.load_field.value) if self.load_field.value else 0
                    self.supabase.client.table("progress").insert(
                        {
                            "exercise_id": self.exercise_id,
                            "load": load,
                            "date": time.strftime("%Y-%m-%d %H:%M:%S"),
                        }
                    ).execute()
                    self.load_text.value = f"{load}kg"
                    self.on_save(load)
                    e.page.snack_bar = ft.SnackBar(
                        content=ft.Text(f"Carga {load}kg salva!"), action="OK"
                    )
                    e.page.snack_bar.open = True
                    e.page.update()
                except Exception as error:
                    e.page.snack_bar = ft.SnackBar(
                        content=ft.Text(f"Erro ao salvar carga: {str(error)}"),
                        action="OK",
                    )
                    e.page.snack_bar.open = True
                    e.page.update()
            e.page.close(confirm_dialog)
            self.load_text.visible = True
            self.load_field.visible = False
            self.edit_button.visible = True
            self.save_button.visible = False
            self.update()

        confirm_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirmar Carga"),
            content=ft.Text(f"Deseja salvar a carga de {self.load_field.value}kg?"),
            actions=[
                ft.TextButton("Sim", on_click=save_confirmed),
                ft.TextButton("Não", on_click=save_confirmed),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        e.page.open(confirm_dialog)

    def enable(self):
        self.enabled = True
        self.edit_button.disabled = False
        self.save_button.disabled = False
        self.update()

    def disable(self):
        self.enabled = False
        self.edit_button.disabled = True
        self.save_button.disabled = True
        self.update()


# Componentes de Diálogos
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
        self.timer_paused.set()
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
                asyncio.sleep(1)
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
