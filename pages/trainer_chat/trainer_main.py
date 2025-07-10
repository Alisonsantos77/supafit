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
from services.openai import OpenAIService
import time


def TrainerTab(
    page: ft.Page, supabase_service: SupabaseService, openai: OpenAIService
) -> ft.Control:
    page.padding = 0
    user_id = page.client_storage.get("supafit.user_id")

    # Criar e configurar HapticFeedback
    haptic_feedback = ft.HapticFeedback()
    page.overlay.append(haptic_feedback)

    async def initialize():
        if not await validate_user_session(page, supabase_service, user_id):
            return False
        user_data = get_user_profile(supabase_service, user_id)
        history_cache = await load_chat_history(
            supabase_service, user_id, chat_container, page, haptic_feedback, user_data
        )
        return user_data, history_cache

    chat_container = create_chat_container(page)
    question_field = create_question_input()
    last_question_time = [time.time() - 10]
    user_data = {}
    history_cache = []

    async def ask_button_callback(e):
        if not user_data:
            haptic_feedback.medium_impact()
            page.open(ft.SnackBar(ft.Text("Carregando dados do perfil...")))
            page.update()
            return
        await ask_question(
            e,
            page,
            supabase_service,
            openai,
            question_field,
            ask_button,
            chat_container,
            user_data,
            user_id,
            last_question_time,
            history_cache,
            haptic_feedback,
        )

    async def clear_button_callback(e):
        await clear_chat(
            supabase_service, user_id, chat_container, page, haptic_feedback
        )

    ask_button = create_ask_button(page, ask_button_callback, haptic_feedback)
    clear_button = create_clear_button(page, clear_button_callback, haptic_feedback)

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
                        size=18,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.ElevatedButton(
                        "Ir para Login",
                        on_click=lambda e: page.go("/login"),
                        style=ft.ButtonStyle(
                            padding=ft.padding.symmetric(horizontal=24, vertical=12)
                        ),
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=16,
            )

    page.run_task(setup_page)

    input_row = ft.Container(
        content=ft.Row(
            [
                question_field,
                ask_button,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=12,
            tight=True,
        ),
        padding=ft.padding.symmetric(horizontal=16, vertical=16),
        border=ft.border.only(
            top=ft.BorderSide(1, ft.Colors.with_opacity(0.08, ft.Colors.ON_SURFACE))
        ),
    )

    header_row = ft.Row(
        [
            ft.Text(
                "Treinador Coachito",
                size=22,
                weight=ft.FontWeight.W_700,
                expand=True,
            ),
            clear_button,
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=12,
    )

    chat_section = ft.Container(
        content=ft.Column(
            [
                header_row,
                ft.Divider(
                    height=1, color=ft.Colors.with_opacity(0.08, ft.Colors.ON_SURFACE)
                ),
                chat_container,
            ],
            spacing=12,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            expand=True,
        ),
        padding=ft.padding.symmetric(horizontal=16, vertical=16),
        expand=True,
    )

    main_column = ft.Column(
        ref=ft.Ref[ft.Column](),
        controls=[
            chat_section,
            input_row,
        ],
        spacing=0,
        alignment=ft.MainAxisAlignment.START,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        expand=True,
    )

    return main_column
