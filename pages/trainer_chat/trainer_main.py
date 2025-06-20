import flet as ft
from pages.trainer_chat.components import (
    create_chat_container,
    create_question_input,
    create_ask_button,
    create_clear_button,
)
from pages.trainer_chat.chat_logic import load_chat_history, clear_chat, ask_question
from pages.trainer_chat.data import get_user_profile
from services.services import AnthropicService
from utils.logger import get_logger

logger = get_logger("supabafit.trainer_chat.trainer_main")


def TrainerTab(
    page: ft.Page, supabase_service, anthropic: AnthropicService
) -> ft.Control:
    """Cria a interface da aba Treinador para interação com IA via Anthropic API."""
    page.padding = 10
    user_id = page.client_storage.get("supafit.user_id")

    if not user_id or user_id == "default_user":
        logger.error("Nenhum user_id válido encontrado. Usuário não autenticado.")
        return ft.Column(
            [
                ft.Text(
                    "Erro: Você precisa estar logado para acessar o chat com o treinador.",
                    size=20,
                    color=ft.Colors.RED,
                ),
                ft.ElevatedButton(
                    "Ir para Login", on_click=lambda e: page.go("/login")
                ),
            ]
        )

    user_data = get_user_profile(supabase_service, user_id)

    chat_container = create_chat_container(page)
    question_field = create_question_input()
    last_question_time = [0]

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
        )

    async def clear_button_callback(e):
        await clear_chat(supabase_service, user_id, chat_container, page)

    ask_button = create_ask_button(page, ask_button_callback)
    clear_button = create_clear_button(page, clear_button_callback)

    page.run_task(load_chat_history, supabase_service, user_id, chat_container, page)

    main_column = ft.Column(
        ref=ft.Ref[ft.Column](),
        controls=[
            ft.Row(
                [
                    ft.Text(
                        "Chat com o Treinador",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.WHITE,
                    ),
                    clear_button,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            ft.Container(
                content=chat_container,
                border_radius=5,
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
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
                run_spacing=10,
            ),
        ],
        spacing=15,
        alignment=ft.MainAxisAlignment.START,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        expand=True,
        scroll="auto",
    )

    return main_column
