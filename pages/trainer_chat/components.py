import flet as ft


def create_chat_container(page: ft.Page) -> ft.ListView:
    """Cria o contêiner do chat com auto-scroll e design minimalista."""
    return ft.ListView(
        ref=ft.Ref[ft.ListView](),
        expand=True,
        spacing=8,
        padding=ft.padding.symmetric(horizontal=8, vertical=12),
        auto_scroll=True,
        width=page.window.width,
    )


def create_question_input() -> ft.TextField:
    """Cria o campo de entrada com validação visual e design limpo."""
    return ft.TextField(
        ref=ft.Ref[ft.TextField](),
        label="Digite sua mensagem",
        multiline=True,
        expand=True,
        border_radius=24,
        text_size=16,
        min_lines=1,
        max_lines=4,
        shift_enter=True,
        filled=True,
        border_color=ft.Colors.with_opacity(0.1, ft.Colors.ON_SURFACE),
        focused_border_color=ft.Colors.BLUE_400,
        content_padding=ft.padding.symmetric(horizontal=16, vertical=12),
        text_style=ft.TextStyle(size=16),
        max_length=500,
        counter_style=ft.TextStyle(color=ft.Colors.ON_SURFACE_VARIANT),
        on_change=lambda e: setattr(e.control, "error_text", None),
    )


def create_ask_button(page: ft.Page, on_click_callback) -> ft.IconButton:
    """Cria o botão de envio como ícone com animação suave."""
    return ft.IconButton(
        ref=ft.Ref[ft.IconButton](),
        icon=ft.Icons.SEND_ROUNDED,
        icon_size=24,
        icon_color=ft.Colors.BLUE_400,
        style=ft.ButtonStyle(
            padding=12,
            shape=ft.CircleBorder(),
            overlay_color=ft.Colors.with_opacity(0.1, ft.Colors.ON_SURFACE),
        ),
        on_click=on_click_callback,
        animate_scale=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
    )


def create_clear_button(page: ft.Page, clear_callback) -> ft.TextButton:
    """Cria o botão de limpar chat como texto com animação."""
    return ft.TextButton(
        content=ft.Text("Limpar", size=14, color=ft.Colors.BLUE_400),
        style=ft.ButtonStyle(
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            shape=ft.RoundedRectangleBorder(radius=8),
        ),
        on_click=clear_callback,
        animate_opacity=ft.Animation(200, ft.AnimationCurve.EASE_IN),
    )
