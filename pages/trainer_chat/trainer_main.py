import flet as ft
from pages.trainer_chat.components import (
    create_chat_container,
    create_question_input,
    create_ask_button,
    create_clear_button,
)
from pages.trainer_chat.chat_logic import load_chat_history, clear_chat, ask_question
from pages.trainer_chat.data import get_user_profile, validate_user_session
from services.supabase import SupabaseService
from services.anthropic import AnthropicService
from utils.logger import get_logger
from utils.alerts import CustomSnackBar

logger = get_logger("supafit.trainer_chat.trainer_main")


def TrainerTab(
    page: ft.Page, supabase_service: SupabaseService, anthropic: AnthropicService
) -> ft.Control:
    """Cria a interface da aba Treinador com design moderno."""
    page.padding = 10
    user_id = page.client_storage.get("supafit.user_id")

    async def initialize():
        if not await validate_user_session(page, supabase_service, user_id):
            return False
        user_data = get_user_profile(supabase_service, user_id)
        history_cache = await load_chat_history(
            supabase_service, user_id, chat_container, page
        )
        return user_data, history_cache

    chat_container = create_chat_container(page)
    question_field = create_question_input()
    last_question_time = [0]
    user_data = {}
    history_cache = []

    async def ask_button_callback(e):
        await ask_question(
            e,
            page,
            supabase_service,
            anthropic,
            question_field,
            ask_button,
            chat_container,
            user_data,
            user_id,
            last_question_time,
            history_cache,
        )

    async def clear_button_callback(e):
        await clear_chat(supabase_service, user_id, chat_container, page)

    ask_button = create_ask_button(page, ask_button_callback)
    clear_button = create_clear_button(page, clear_button_callback)

    async def setup_page():
        result = await initialize()
        if result:
            nonlocal user_data, history_cache
            user_data, history_cache = result
        else:
            return ft.Column(
                [
                    ft.Text(
                        "Erro: Você precisa estar logado para acessar o chat com o treinador.",
                        size=20,
                    ),
                    ft.ElevatedButton(
                        "Ir para Login", on_click=lambda e: page.go("/login")
                    ),
                ]
            )

    page.run_task(setup_page)

    header = ft.Container(
        content=ft.Column(
            [
                ft.Text(
                    "Chat com o Treinador",
                    size=28,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Text(
                    "Converse com seu treinador virtual",
                    size=14,
                    opacity=0.8,
                ),
            ],
            spacing=4,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.padding.all(32),
        border_radius=ft.border_radius.only(bottom_left=24, bottom_right=24),
    )

    main_column = ft.Column(
        ref=ft.Ref[ft.Column](),
        controls=[
            header,
            ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Text(
                                    "Conversa",
                                    size=18,
                                    weight=ft.FontWeight.BOLD,
                                ),
                                clear_button,
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Container(
                            content=chat_container,
                            border=ft.border.all(
                                1, ft.Colors.with_opacity(0.12, ft.Colors.ON_SURFACE)
                            ),
                            border_radius=16,
                            padding=10,
                            expand=True,
                        ),
                        ft.ResponsiveRow(
                            [
                                ft.Container(
                                    content=question_field,
                                    col={"xs": 12, "sm": 9, "md": 10},
                                    padding=5,
                                ),
                                ft.Container(
                                    content=ask_button,
                                    col={"xs": 12, "sm": 3, "md": 2},
                                    alignment=ft.alignment.center,
                                    padding=5,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            vertical_alignment=ft.CrossAxisAlignment.END,
                        ),
                    ],
                    spacing=15,
                    horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                ),
                padding=ft.padding.all(24),
            ),
        ],
        spacing=0,
        alignment=ft.MainAxisAlignment.START,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        expand=True,
        scroll="auto",
    )

    return main_column
