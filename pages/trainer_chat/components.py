import flet as ft


def create_chat_container(page: ft.Page) -> ft.ListView:
    """Cria o contêiner do chat com configurações padrão."""
    return ft.ListView(
        ref=ft.Ref[ft.ListView](),
        expand=True,
        spacing=10,
        padding=10,
        auto_scroll=True,
        width=page.window.width,
    )


def create_question_input() -> ft.TextField:
    """Cria o campo de entrada de texto para perguntas."""
    return ft.TextField(
        ref=ft.Ref[ft.TextField](),
        label="Faça sua pergunta",
        multiline=True,
        expand=True,
        border_radius=5,
        text_size=14,
        min_lines=1,
        max_lines=5,
        filled=True,
        shift_enter=True,
        bgcolor=ft.Colors.GREY_800,
        color=ft.Colors.WHITE,
        border_color=ft.Colors.GREY_600,
    )


def create_ask_button(page: ft.Page, on_click_callback) -> ft.ElevatedButton:
    """Cria o botão de envio de perguntas."""
    button = ft.ElevatedButton(
        ref=ft.Ref[ft.ElevatedButton](),
        text="Enviar",
        style=ft.ButtonStyle(
            padding=ft.padding.symmetric(horizontal=20, vertical=10),
            shape=ft.RoundedRectangleBorder(radius=5),
            bgcolor=ft.Colors.BLUE_600,
            color=ft.Colors.WHITE,
        ),
    )
    button.on_click = on_click_callback
    return button


def create_clear_button(page: ft.Page, clear_callback) -> ft.ElevatedButton:
    """Cria o botão para limpar o chat."""
    button = ft.ElevatedButton(
        "Limpar Chat",
        style=ft.ButtonStyle(
            bgcolor=ft.Colors.RED_700,
            color=ft.Colors.WHITE,
            padding=ft.padding.symmetric(horizontal=20, vertical=10),
            shape=ft.RoundedRectangleBorder(radius=5),
        ),
    )
    button.on_click = clear_callback
    return button
