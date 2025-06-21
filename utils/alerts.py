import flet as ft


class CustomSnackBar(ft.SnackBar):
    """A standardized SnackBar for consistent feedback."""

    def __init__(self, message: str, bgcolor=ft.Colors.RED_700, duration=3000):
        super().__init__(
            content=ft.Text(
                message,
                color=ft.Colors.WHITE,
                size=14,
                weight=ft.FontWeight.BOLD,
                text_align=ft.TextAlign.CENTER,
            ),
            bgcolor=bgcolor,
            duration=duration,
            padding=10,
            shape=ft.RoundedRectangleBorder(radius=5),
            behavior=ft.SnackBarBehavior.FLOATING,
            margin=20,
            show_close_icon=True,
            elevation=5,
        )

    def show(self, page: ft.Page):
        page.snack_bar = self
        self.open = True
        page.update()


class CustomAlertDialog(ft.AlertDialog):
    """A standardized AlertDialog for consistent feedback."""

    def __init__(self, content, bgcolor=ft.Colors.GREY_900, modal=True):
        super().__init__(
            content=content,
            bgcolor=ft.Colors.with_opacity(0.8, bgcolor),
            modal=modal,
            shape=ft.RoundedRectangleBorder(radius=10),
        )

    def show(self, page: ft.Page):
        page.dialog = self
        self.open = True
        page.update()

    def close(self, page: ft.Page):
        page.close(self)
        page.update()
