import asyncio
import flet as ft


def create_chat_container(page: ft.Page) -> ft.ListView:
    return ft.ListView(
        ref=ft.Ref[ft.ListView](),
        expand=True,
        spacing=12,
        padding=ft.padding.symmetric(horizontal=16, vertical=8),
        auto_scroll=True,
        width=page.window.width,
    )


def create_question_input() -> ft.TextField:
    return ft.TextField(
        ref=ft.Ref[ft.TextField](),
        label="Digite sua mensagem",
        multiline=True,
        expand=True,
        border_radius=20,
        text_size=16,
        min_lines=1,
        max_lines=3,
        shift_enter=True,
        filled=True,
        border_color=ft.Colors.with_opacity(0.1, ft.Colors.PRIMARY),
        focused_border_color=ft.Colors.PRIMARY,
        content_padding=ft.padding.symmetric(horizontal=16, vertical=14),
        text_style=ft.TextStyle(size=16, height=1.4),
        max_length=50,
        counter_style=ft.TextStyle(color=ft.Colors.PRIMARY, size=12),
        on_change=lambda e: setattr(e.control, "error_text", None),
    )


def create_ask_button(
    page: ft.Page, on_click_callback, haptic_feedback: ft.HapticFeedback
) -> ft.IconButton:
    def enhanced_click(e):
        haptic_feedback.light_impact()
        page.run_task(
            on_click_callback, e
        )
    return ft.IconButton(
        ref=ft.Ref[ft.IconButton](),
        icon=ft.Icons.SEND_ROUNDED,
        icon_size=22,
        icon_color=ft.Colors.PRIMARY,
        style=ft.ButtonStyle(
            padding=16,
            shape=ft.CircleBorder(),
            overlay_color=ft.Colors.with_opacity(0.1, ft.Colors.ON_SURFACE),
        ),
        on_click=enhanced_click,
        animate_scale=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
    )


def create_clear_button(
    page: ft.Page, clear_callback, haptic_feedback: ft.HapticFeedback
) -> ft.TextButton:
    def enhanced_clear(e):
        haptic_feedback.medium_impact()
        page.run_task(clear_callback, e)

    return ft.TextButton(
        content=ft.Text(
            "Limpar", size=14, color=ft.Colors.PRIMARY, weight=ft.FontWeight.W_500
        ),
        style=ft.ButtonStyle(
            padding=ft.padding.symmetric(horizontal=16, vertical=10),
            shape=ft.RoundedRectangleBorder(radius=10),
        ),
        on_click=enhanced_clear,
        animate_opacity=ft.Animation(200, ft.AnimationCurve.EASE_IN),
    )


def create_haptic_feedback(page: ft.Page) -> ft.HapticFeedback:
    haptic = ft.HapticFeedback()
    page.overlay.append(haptic)
    return haptic


def show_success_snackbar(
    page: ft.Page, message: str, haptic_feedback: ft.HapticFeedback
):
    haptic_feedback.light_impact()
    page.open(
        ft.SnackBar(
            ft.Text(message, color=ft.Colors.WHITE),
            bgcolor=ft.Colors.GREEN_700,
        )
    )
    page.update()


def show_error_snackbar(
    page: ft.Page, message: str, haptic_feedback: ft.HapticFeedback
):
    haptic_feedback.heavy_impact()
    page.open(
        ft.SnackBar(
            ft.Text(message, color=ft.Colors.WHITE),
            bgcolor=ft.Colors.RED_700,
        )
    )
    page.update()


def show_warning_snackbar(
    page: ft.Page, message: str, haptic_feedback: ft.HapticFeedback
):
    haptic_feedback.medium_impact()
    page.open(
        ft.SnackBar(
            ft.Text(message, color=ft.Colors.WHITE),
            bgcolor=ft.Colors.ORANGE_700,
        )
    )
    page.update()


def show_info_snackbar(page: ft.Page, message: str, haptic_feedback: ft.HapticFeedback):
    haptic_feedback.vibrate()
    page.open(
        ft.SnackBar(
            ft.Text(message, color=ft.Colors.WHITE),
            bgcolor=ft.Colors.BLUE_700,
        )
    )
    page.update()
