from cmath import pi
import flet as ft
import logging

logger = logging.getLogger("supafit.support.components")


class AnimatedCard(ft.Container):
    def __init__(self, content, **kwargs):
        super().__init__()
        self.content = content
        self.padding = 20
        self.border_radius = 15
        self.border = ft.border.all(1, ft.Colors.OUTLINE_VARIANT)
        self.animate = ft.Animation(800, ft.AnimationCurve.EASE_OUT)
        self.animate_scale = ft.Animation(300, ft.AnimationCurve.ELASTIC_OUT)
        self.animate_opacity = ft.Animation(600, ft.AnimationCurve.EASE_IN_OUT)
        self.scale = 1
        self.opacity = 1
        self.bgcolor = None
        for key, value in kwargs.items():
            setattr(self, key, value)


class BuddyAvatar(ft.Container):
    def __init__(self):
        super().__init__()
        self.content = ft.Image(
            src="mascote_supafit/apoiador1.png",
            width=100,
            height=100,
            fit=ft.ImageFit.CONTAIN,
            border_radius=40,
        )
        self.width = 120
        self.height = 120
        self.border_radius = 60
        self.border = ft.border.all(3, ft.Colors.PRIMARY)
        self.alignment = ft.alignment.center
        self.animate_rotation = ft.Animation(1200, ft.AnimationCurve.ELASTIC_OUT)
        self.animate_scale = ft.Animation(400, ft.AnimationCurve.BOUNCE_OUT)
        self.rotate = 0
        self.scale = 1

    def animate_buddy(self):
        self.rotate += pi / 4
        self.scale = 1.1
        if hasattr(self, "page") and self.page:
            self.update()

        def reset_scale():
            self.scale = 1
            if hasattr(self, "page") and self.page:
                self.update()

        import threading

        timer = threading.Timer(0.3, reset_scale)
        timer.start()


class PixKeyCard(ft.Container):
    def __init__(self, pix_key, on_copy):
        super().__init__()
        self.padding = 24
        self.border = ft.border.all(2, ft.Colors.OUTLINE)
        self.border_radius = 16
        self.animate_scale = ft.Animation(200, ft.AnimationCurve.BOUNCE_OUT)
        self.animate_opacity = ft.Animation(300, ft.AnimationCurve.EASE_OUT)
        self.scale = 1

        self.copy_button = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.COPY_ALL, size=24, color=ft.Colors.WHITE),
                    ft.Text(
                        "COPIAR CHAVE PIX",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.WHITE,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
            ),
            bgcolor=ft.Colors.PRIMARY,
            border_radius=12,
            padding=ft.padding.symmetric(vertical=16, horizontal=24),
            animate_scale=ft.Animation(150, ft.AnimationCurve.EASE_OUT),
            ink=True,
            on_click=on_copy,
            scale=1,
        )

        self.content = ft.Column(
            [
                ft.Text(
                    "💰 Chave PIX do Desenvolvedor",
                    size=14,
                    weight=ft.FontWeight.W_600,
                    text_align=ft.TextAlign.CENTER,
                    color=ft.Colors.ON_SURFACE,
                ),
                ft.Container(
                    content=ft.Text(
                        pix_key,
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        selectable=True,
                        text_align=ft.TextAlign.CENTER,
                        color=ft.Colors.ON_SECONDARY_CONTAINER,
                    ),
                    border_radius=8,
                    padding=12,
                    border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
                ),
                self.copy_button,
                ft.Text(
                    "Cole no seu app e escolha qualquer valor! 🚀",
                    size=12,
                    text_align=ft.TextAlign.CENTER,
                    weight=ft.FontWeight.W_500,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=16,
        )

    def animate_copy_success(self):
        self.copy_button.scale = 0.95
        self.copy_button.update()

        def reset():
            self.copy_button.scale = 1
            self.copy_button.update()

        import threading

        timer = threading.Timer(0.2, reset)
        timer.start()


class StoryCard(ft.Container):
    def __init__(self, icon, title, description, delay=0):
        super().__init__()
        self.padding = 20
        self.border_radius = 12
        self.animate_opacity = ft.Animation(800, ft.AnimationCurve.EASE_OUT)
        self.animate_scale = ft.Animation(600, ft.AnimationCurve.EASE_OUT)
        self.opacity = 0
        self.scale = 0.8
        self.bgcolor = None

        self.content = ft.Row(
            [
                ft.Container(
                    content=ft.Text(icon, size=32),
                    width=60,
                    height=60,
                    border_radius=30,
                    bgcolor=ft.Colors.PRIMARY,
                    alignment=ft.alignment.center,
                ),
                ft.Column(
                    [
                        ft.Text(
                            title,
                            weight=ft.FontWeight.BOLD,
                            size=16,
                            color=ft.Colors.ON_SURFACE,
                        ),
                        ft.Text(
                            description, size=13, expand=True
                        ),
                    ],
                    spacing=4,
                    expand=True,
                ),
            ],
            spacing=16,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )

        import threading

        timer = threading.Timer(delay, self._animate_in)
        timer.start()

    def _animate_in(self):
        self.opacity = 1
        self.scale = 1
        if hasattr(self, "page") and self.page:
            self.update()


class AnimatedSnackBar:
    @staticmethod
    def show_success(page: ft.Page, message: str, icon=ft.Icons.CHECK_CIRCLE):
        snackbar = ft.SnackBar(
            content=ft.Row(
                [
                    ft.Icon(icon, color=ft.Colors.WHITE, size=20),
                    ft.Text(
                        message[:35] + "..." if len(message) > 35 else message,
                        color=ft.Colors.WHITE,
                        weight=ft.FontWeight.W_500,
                    ),
                ],
                spacing=8,
            ),
            bgcolor=ft.Colors.GREEN_600,
            duration=2500,
            behavior=ft.SnackBarBehavior.FLOATING,
            margin=ft.margin.all(10),
            elevation=8,
            shape=ft.RoundedRectangleBorder(radius=12),
        )
        page.overlay.append(snackbar)
        snackbar.open = True
        page.update()

    @staticmethod
    def show_error(page: ft.Page, message: str, icon=ft.Icons.ERROR):
        snackbar = ft.SnackBar(
            content=ft.Row(
                [
                    ft.Icon(icon, color=ft.Colors.WHITE, size=20),
                    ft.Text(
                        message[:35] + "..." if len(message) > 35 else message,
                        color=ft.Colors.WHITE,
                        weight=ft.FontWeight.W_500,
                    ),
                ],
                spacing=8,
            ),
            bgcolor=ft.Colors.RED_600,
            duration=3000,
            behavior=ft.SnackBarBehavior.FLOATING,
            margin=ft.margin.all(10),
            elevation=8,
            shape=ft.RoundedRectangleBorder(radius=12),
        )
        page.overlay.append(snackbar)
        snackbar.open = True
        page.update()

    @staticmethod
    def show_info(page: ft.Page, message: str, icon=ft.Icons.INFO):
        snackbar = ft.SnackBar(
            content=ft.Row(
                [
                    ft.Icon(icon, color=ft.Colors.WHITE, size=20),
                    ft.Text(
                        message[:35] + "..." if len(message) > 35 else message,
                        color=ft.Colors.WHITE,
                        weight=ft.FontWeight.W_500,
                    ),
                ],
                spacing=8,
            ),
            bgcolor=ft.Colors.BLUE_600,
            duration=2500,
            behavior=ft.SnackBarBehavior.FLOATING,
            margin=ft.margin.all(10),
            elevation=8,
            shape=ft.RoundedRectangleBorder(radius=12),
        )
        page.overlay.append(snackbar)
        snackbar.open = True
        page.update()
