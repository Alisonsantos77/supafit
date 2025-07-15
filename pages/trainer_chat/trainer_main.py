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
import asyncio


class TrainerChatInitializer:
    """Classe responsável pela inicialização do chat do treinador com feedback visual."""

    def __init__(
        self, page: ft.Page, supabase_service: SupabaseService, openai: OpenAIService
    ):
        self.page = page
        self.supabase_service = supabase_service
        self.openai = openai
        self.user_id = page.client_storage.get("supafit.user_id")
        self.user_data = {}
        self.history_cache = []
        self.haptic_feedback = ft.HapticFeedback()
        self.initialization_complete = False

        # Adicionar haptic feedback ao overlay
        self.page.overlay.append(self.haptic_feedback)

    def show_loading_screen(self, message: str = "Carregando chat..."):
        """Exibe tela de carregamento com progress ring."""
        loading_content = ft.Column(
            [
                ft.ProgressRing(width=50, height=50, color=ft.Colors.BLUE_400),
                ft.Text(
                    message,
                    size=16,
                    text_align=ft.TextAlign.CENTER,
                    weight=ft.FontWeight.W_500,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20,
        )

        return ft.Container(
            content=loading_content,
            expand=True,
            alignment=ft.alignment.center,
            padding=ft.padding.all(20),
        )

    def show_error_screen(
        self,
        error_message: str,
        action_text: str = "Tentar Novamente",
        action_callback=None,
    ):
        """Exibe tela de erro com opção de ação."""

        def default_action(e):
            print("[TRAINER] Tentando reinicializar chat...")
            self.page.run_task(self.initialize_chat)

        error_content = ft.Column(
            [
                ft.Icon(ft.Icons.ERROR, color=ft.Colors.RED_400, size=50),
                ft.Text(
                    "Erro no Chat",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.RED_400,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    error_message,
                    size=14,
                    text_align=ft.TextAlign.CENTER,
                    color=ft.Colors.GREY_600,
                ),
                ft.ElevatedButton(
                    action_text,
                    on_click=action_callback or default_action,
                    icon=ft.Icons.REFRESH,
                    style=ft.ButtonStyle(
                        padding=ft.padding.symmetric(horizontal=24, vertical=12)
                    ),
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20,
        )

        return ft.Container(
            content=error_content,
            expand=True,
            alignment=ft.alignment.center,
            padding=ft.padding.all(20),
        )

    async def validate_session(self) -> bool:
        """Valida a sessão do usuário."""
        try:
            print("[TRAINER] Validando sessão do usuário...")

            if not self.user_id:
                print("[TRAINER] User ID não encontrado")
                return False

            is_valid = await validate_user_session(
                self.page, self.supabase_service, self.user_id
            )

            if not is_valid:
                print("[TRAINER] Sessão inválida")
                return False

            print("[TRAINER] Sessão validada com sucesso")
            return True

        except Exception as e:
            print(f"[TRAINER] Erro na validação da sessão: {e}")
            return False

    async def load_user_profile(self) -> bool:
        """Carrega o perfil do usuário."""
        try:
            print("[TRAINER] Carregando perfil do usuário...")

            self.user_data = get_user_profile(self.supabase_service, self.user_id)

            if not self.user_data:
                print("[TRAINER] Falha ao carregar perfil do usuário")
                return False

            print(
                f"[TRAINER] Perfil carregado: {self.user_data.get('name', 'Usuário')}"
            )
            return True

        except Exception as e:
            print(f"[TRAINER] Erro ao carregar perfil: {e}")
            return False

    async def load_chat_data(self, chat_container: ft.ListView) -> bool:
        """Carrega o histórico do chat."""
        try:
            print("[TRAINER] Carregando histórico do chat...")

            self.history_cache = await load_chat_history(
                self.supabase_service,
                self.user_id,
                chat_container,
                self.page,
                self.haptic_feedback,
                self.user_data,
            )

            print(f"[TRAINER] Histórico carregado: {len(self.history_cache)} mensagens")
            return True

        except Exception as e:
            print(f"[TRAINER] Erro ao carregar histórico: {e}")
            return False

    async def initialize_chat(self):
        """Método principal de inicialização do chat."""
        try:
            print("[TRAINER] Iniciando chat do treinador...")

            # Mostrar loading inicial
            loading_container = self.show_loading_screen("Validando sessão...")

            # Validar sessão
            if not await self.validate_session():
                return self.show_error_screen(
                    "Sessão expirada ou inválida. Faça login novamente.",
                    "Ir para Login",
                    lambda e: self.page.go("/login"),
                )

            # Atualizar loading
            loading_container = self.show_loading_screen("Carregando perfil...")

            # Carregar perfil
            if not await self.load_user_profile():
                return self.show_error_screen(
                    "Não foi possível carregar seu perfil. Tente novamente."
                )

            # Atualizar loading
            loading_container = self.show_loading_screen("Carregando histórico...")

            # Criar componentes do chat
            chat_container = create_chat_container(self.page)

            # Carregar histórico
            if not await self.load_chat_data(chat_container):
                return self.show_error_screen(
                    "Erro ao carregar histórico do chat. Tente novamente."
                )

            # Finalizar inicialização
            self.initialization_complete = True
            print("[TRAINER] Chat inicializado com sucesso")

            # Retornar interface do chat
            return self.create_chat_interface(chat_container)

        except Exception as e:
            print(f"[TRAINER] Erro crítico na inicialização: {e}")
            return self.show_error_screen(
                "Erro crítico na inicialização do chat. Tente novamente."
            )

    def create_chat_interface(self, chat_container: ft.ListView) -> ft.Control:
        """Cria a interface completa do chat."""

        # Criar componentes
        question_field = create_question_input()
        last_question_time = [time.time() - 10]

        async def ask_button_callback(e):
            if not self.user_data:
                self.haptic_feedback.medium_impact()
                self.page.open(ft.SnackBar(ft.Text("Carregando dados do perfil...")))
                self.page.update()
                return
            await ask_question(
                e,
                self.page,
                self.supabase_service,
                self.openai,
                question_field,
                ask_button,
                chat_container,
                self.user_data,
                self.user_id,
                last_question_time,
                self.history_cache,
                self.haptic_feedback,
            )

        async def clear_button_callback(e):
            await clear_chat(
                self.supabase_service,
                self.user_id,
                chat_container,
                self.page,
                self.haptic_feedback,
            )

        ask_button = create_ask_button(
            self.page, ask_button_callback, self.haptic_feedback
        )
        clear_button = create_clear_button(
            self.page, clear_button_callback, self.haptic_feedback
        )

        # Criar seção de input
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

        # Criar header
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

        # Criar seção do chat
        chat_section = ft.Container(
            content=ft.Column(
                [
                    header_row,
                    ft.Divider(
                        height=1,
                        color=ft.Colors.with_opacity(0.08, ft.Colors.ON_SURFACE),
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

        # Criar coluna principal
        main_column = ft.Column(
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


def TrainerTab(
    page: ft.Page, supabase_service: SupabaseService, openai: OpenAIService
) -> ft.Control:
    """Função principal do tab do treinador com inicialização visual."""

    page.padding = 0

    # Criar inicializador
    initializer = TrainerChatInitializer(page, supabase_service, openai)

    # Container principal que vai conter o estado atual
    main_container = ft.Container(
        content=initializer.show_loading_screen("Iniciando chat..."),
        expand=True,
    )

    async def initialize_and_update():
        """Inicializa o chat e atualiza o container."""
        try:
            # Executar inicialização
            result = await initializer.initialize_chat()

            # Atualizar container com resultado
            main_container.content = result
            main_container.update()

        except Exception as e:
            print(f"[TRAINER] Erro na inicialização: {e}")
            main_container.content = initializer.show_error_screen(
                "Erro inesperado na inicialização do chat."
            )
            main_container.update()

    # Executar inicialização
    page.run_task(initialize_and_update)

    return main_container
