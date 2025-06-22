import flet as ft
from utils.alerts import CustomSnackBar


def create_chat_container(page: ft.Page) -> ft.ListView:
    """Cria o contêiner do chat com auto-scroll e animação de entrada."""
    return ft.ListView(
        ref=ft.Ref[ft.ListView](),
        expand=True,
        spacing=10,
        padding=20,
        auto_scroll=True,
        width=page.window.width,
        animate_opacity=ft.Animation(300, ft.AnimationCurve.EASE_IN),
    )


def create_question_input() -> ft.TextField:
    """Cria o campo de entrada de perguntas com validação visual."""
    return ft.TextField(
        ref=ft.Ref[ft.TextField](),
        label="Faça sua pergunta",
        multiline=True,
        expand=True,
        border_radius=12,
        text_size=14,
        min_lines=1,
        max_lines=5,
        shift_enter=True,
        filled=True,
        border_color=ft.Colors.with_opacity(0.12, ft.Colors.ON_SURFACE),
        focused_border_color=ft.Colors.BLUE_400,
        content_padding=ft.padding.all(16),
        text_style=ft.TextStyle(size=14),
        max_length=500,
        counter_style=ft.TextStyle(color=ft.Colors.ON_SURFACE_VARIANT),
        on_change=lambda e: e.control.error_text(None),  # Limpa erro ao digitar
    )


def create_ask_button(page: ft.Page, on_click_callback) -> ft.ElevatedButton:
    """Cria o botão de envio com feedback de loading e animação."""
    button = ft.ElevatedButton(
        ref=ft.Ref[ft.ElevatedButton](),
        content=ft.Text("Enviar", size=14, weight=ft.FontWeight.W_600),
        style=ft.ButtonStyle(
            padding=ft.padding.symmetric(horizontal=24, vertical=16),
            shape=ft.RoundedRectangleBorder(radius=12),
            elevation=0,
            overlay_color=ft.Colors.with_opacity(0.1, ft.Colors.ON_SURFACE),
        ),
        height=56,
        on_click=on_click_callback,
        animate_scale=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
    )
    return button


def create_clear_button(page: ft.Page, clear_callback) -> ft.ElevatedButton:
    """Cria o botão para limpar o chat com animação."""
    button = ft.ElevatedButton(
        content=ft.Text("Limpar Chat", size=14, weight=ft.FontWeight.W_600),
        style=ft.ButtonStyle(
            padding=ft.padding.symmetric(horizontal=24, vertical=16),
            shape=ft.RoundedRectangleBorder(radius=12),
            elevation=0,
            overlay_color=ft.Colors.with_opacity(0.1, ft.Colors.ON_SURFACE),
        ),
        height=56,
        on_click=clear_callback,
        animate_scale=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
    )
    return button
