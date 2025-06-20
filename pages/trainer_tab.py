# Código completo atualizado de trainer_tab.py
import flet as ft
import asyncio
from components.message import ChatMessage, Message
from services.services import AnthropicService
import httpx
import time
from datetime import datetime
from postgrest.exceptions import APIError
from utils.quebra_mensagem import integrate_with_chat
import uuid
import logging

logger = logging.getLogger("supafit.trainer")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


def TrainerTab(page: ft.Page, supabase_service, anthropic: AnthropicService):
    """Cria a interface da aba Treinador para interação com IA via Anthropic API.

    Args:
        page (ft.Page): Instância da página Flet para renderização UI.
        supabase_service (SupabaseService): Serviço para operações no Supabase.
        anthropic (AnthropicService): Serviço para interações com a API Anthropic.

    Returns:
        ft.Control: Interface renderizada da aba Treinador.
    """
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

    # Carregar dados do perfil do usuário
    user_profile = (
        supabase_service.client.table("user_profiles")
        .select("name, age, weight, height, goal, level")
        .eq("user_id", user_id)
        .execute()
        .data
    )
    user_data = (
        user_profile[0]
        if user_profile
        else {
            "name": "Usuário",
            "age": "N/A",
            "weight": "N/A",
            "height": "N/A",
            "goal": "N/A",
            "level": "N/A",
        }
    )

    # Referências para controles
    chat_ref = ft.Ref[ft.ListView]()
    question_field_ref = ft.Ref[ft.TextField]()
    ask_button_ref = ft.Ref[ft.ElevatedButton]()
    main_column_ref = ft.Ref[ft.Column]()

    # Contêiner do chat
    chat_container = ft.ListView(
        ref=chat_ref,
        expand=True,
        spacing=10,
        padding=10,
        auto_scroll=True,
        width=page.window.width,
    )

    # Campo de pergunta
    question_field = ft.TextField(
        ref=question_field_ref,
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

    # Botão de enviar
    ask_button = ft.ElevatedButton(
        ref=ask_button_ref,
        text="Enviar",
        style=ft.ButtonStyle(
            padding=ft.padding.symmetric(horizontal=20, vertical=10),
            shape=ft.RoundedRectangleBorder(radius=5),
            bgcolor=ft.Colors.BLUE_600,
            color=ft.Colors.WHITE,
        ),
    )

    # Botão de limpar chat
    clear_button = ft.ElevatedButton(
        "Limpar Chat",
        style=ft.ButtonStyle(
            bgcolor=ft.Colors.RED_700,
            color=ft.Colors.WHITE,
            padding=ft.padding.symmetric(horizontal=20, vertical=10),
            shape=ft.RoundedRectangleBorder(radius=5),
        ),
        on_click=lambda e: page.run_task(clear_chat),
    )

    # Controle de cooldown e estado
    last_question_time = [0]  # Usar lista para permitir modificação em função aninhada
    COOLDOWN_SECONDS = 2

    async def load_chat():
        """Carrega o histórico de conversa do Supabase."""
        try:
            resp = (
                supabase_service.client.table("trainer_qa")
                .select("message")
                .eq("user_id", user_id)
                .order("updated_at")
                .limit(50)
                .execute()
            )
            chat_ref.current.controls.clear()

            # Mensagem inicial do treinador
            chat_ref.current.controls.append(
                ChatMessage(
                    Message(
                        user_name="Treinador",
                        text="Olá! Como posso ajudar com seu treino hoje? 😄",
                        user_type="trainer",
                        created_at=datetime.now().isoformat(),
                    ),
                    page,
                )
            )

            for item in resp.data:
                messages = item.get("message", [])
                for msg in messages:
                    chat_ref.current.controls.append(
                        ChatMessage(
                            Message(
                                user_name=(
                                    "Você" if msg["role"] == "user" else "Treinador"
                                ),
                                text=msg["content"],
                                user_type=msg["role"],
                                created_at=msg["timestamp"],
                            ),
                            page,
                        )
                    )

            logger.info("Rolar para o final da coluna principal")
            main_column_ref.current.scroll_to(
                offset=-1, duration=1000, curve=ft.AnimationCurve.EASE_OUT
            )
            page.update()
            return resp.data
        except APIError as e:
            if e.code == "42501":
                if supabase_service.refresh_session():
                    page.go(page.route)
                    return []
                else:
                    page.open(
                        ft.SnackBar(
                            ft.Text(
                                "Sessão expirada. Por favor, faça login novamente."
                            ),
                            bgcolor=ft.Colors.RED_700,
                        )
                    )
                    page.go("/login")
                    return []
            else:
                logger.error(f"Erro ao carregar chat: {str(e)}")
                page.open(ft.SnackBar(ft.Text(f"Erro ao carregar chat: {str(e)}")))
                return []

    async def clear_chat():
        """Limpa o histórico de conversa após confirmação."""

        async def confirm_clear(e):
            if e.control.text == "Sim":
                try:
                    await supabase_service.client.table("trainer_qa").delete().eq(
                        "user_id", user_id
                    ).execute()
                    chat_ref.current.controls = [
                        ChatMessage(
                            Message(
                                user_name="Treinador",
                                text="Olá! Como posso ajudar com seu treino hoje? 😄",
                                user_type="trainer",
                                created_at=datetime.now().isoformat(),
                            ),
                            page,
                        )
                    ]
                    page.open(ft.SnackBar(ft.Text("Chat limpo com sucesso!")))
                except APIError as ex:
                    if ex.code == "42501":
                        if supabase_service.refresh_session():
                            page.go(page.route)
                        else:
                            page.open(
                                ft.SnackBar(
                                    ft.Text(
                                        "Sessão expirada. Por favor, faça login novamente."
                                    ),
                                    bgcolor=ft.Colors.RED_700,
                                )
                            )
                            page.go("/login")
                    else:
                        logger.error(f"Erro ao limpar chat: {str(ex)}")
                        page.open(
                            ft.SnackBar(ft.Text(f"Erro ao limpar chat: {str(ex)}"))
                        )
            page.close(confirm_dialog)
            page.update()

        confirm_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Limpar Chat"),
            content=ft.Text(
                "Tem certeza que deseja limpar todo o histórico de mensagens?"
            ),
            actions=[
                ft.TextButton("Sim", on_click=confirm_clear),
                ft.TextButton("Não", on_click=lambda e: page.close(confirm_dialog)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.open(confirm_dialog)

    async def ask_question(e):
        """Processa a submissão de pergunta e obtém resposta da IA."""
        current_time = time.time()
        if current_time - last_question_time[0] < COOLDOWN_SECONDS:
            page.open(
                ft.SnackBar(
                    ft.Text("Aguarde um momento antes de enviar outra pergunta!")
                )
            )
            return

        question = question_field_ref.current.value.strip()
        if not question:
            page.open(ft.SnackBar(ft.Text("Digite uma pergunta!")))
            return
        if len(question) > 500:
            page.open(
                ft.SnackBar(ft.Text("Pergunta muito longa (máximo 500 caracteres)."))
            )
            return
        if anthropic.is_sensitive_question(question):
            page.open(
                ft.SnackBar(
                    ft.Text("Conversa sensível detectada.", color=ft.Colors.WHITE),
                    bgcolor=ft.Colors.RED,
                    
                )
            )
            return

        ask_button_ref.current.disabled = True
        ask_button_ref.current.content = ft.Row(
            [ft.ProgressRing(width=16, height=16), ft.Text(" Enviando...")],
            alignment=ft.MainAxisAlignment.CENTER,
        )
        page.update()

        try:
            # Carregar histórico
            history = []
            resp = (
                supabase_service.client.table("trainer_qa")
                .select("message")
                .eq("user_id", user_id)
                .order("updated_at")
                .execute()
            )
            for item in resp.data:
                history.extend(item["message"])

            # Adicionar pergunta ao chat
            question_id = str(uuid.uuid4())
            chat_ref.current.controls.append(
                ChatMessage(
                    Message(
                        user_name="Você",
                        text=question,
                        user_type="user",
                        created_at=datetime.now().isoformat(),
                    ),
                    page,
                )
            )
            if len(chat_ref.current.controls) > 50:
                chat_ref.current.controls.pop(0)

            typing_indicator = ft.AnimatedSwitcher(
                content=ft.Row(
                    [
                        ft.Text("Treinador está digitando"),
                        ft.ProgressRing(width=16, height=16),
                    ]
                ),
                transition=ft.AnimatedSwitcherTransition.FADE,
                duration=500,
                reverse_duration=500,
            )
            chat_ref.current.controls.append(typing_indicator)
            page.update()
            await asyncio.sleep(1)

            # Gerar resposta com contexto do usuário
            system_prompt = f"""
            Você é um treinador virtual do SupaFit, motivado e amigável. Use emojis 💪🏋️.
            Informações do usuário:
            - Nome: {user_data.get('name', 'Usuário')}
            - Idade: {user_data.get('age', 'N/A')} anos
            - Peso: {user_data.get('weight', 'N/A')} kg
            - Altura: {user_data.get('height', 'N/A')} cm
            - Objetivo: {user_data.get('goal', 'N/A')}
            - Nível: {user_data.get('level', 'N/A')}
            Responda considerando essas informações e o histórico da conversa.
            Data e hora atual: {datetime.now().strftime('%d/%m/%Y às %H:%M')}.
            """
            answer = anthropic.answer_question(question, history, system_prompt)
            if not answer or "desculpe" in answer.lower():
                raise ValueError("Resposta inválida do Anthropic")

            chat_ref.current.controls.remove(typing_indicator)
            messages_with_delays = integrate_with_chat(answer)

            # Salvar mensagens no JSON
            message_json = [
                {
                    "role": "user",
                    "content": question,
                    "message_id": question_id,
                    "timestamp": datetime.now().isoformat(),
                }
            ]
            for msg, delay in messages_with_delays:
                response_id = str(uuid.uuid4())
                message_json.append(
                    {
                        "role": "assistant",
                        "content": msg,
                        "message_id": response_id,
                        "timestamp": datetime.now().isoformat(),
                    }
                )
                chat_ref.current.controls.append(
                    ChatMessage(
                        Message(
                            user_name="Treinador",
                            text=msg,
                            user_type="assistant",
                            created_at=datetime.now().isoformat(),
                        ),
                        page,
                    )
                )
                if len(chat_ref.current.controls) > 50:
                    chat_ref.current.controls.pop(0)
                await asyncio.sleep(delay)
                page.update()

            # Inserir no Supabase
            response = (
                await supabase_service.client.table("trainer_qa")
                .insert(
                    {
                        "user_id": user_id,
                        "message": message_json,
                        "created_at": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat(),
                    }
                )
                .execute()
            )
            logger.info(f"Inserção bem-sucedida: {response.data}")

            question_field_ref.current.value = ""  # Limpa o input após envio
            page.open(ft.SnackBar(ft.Text("Pergunta enviada com sucesso!")))
            last_question_time[0] = current_time

            main_column_ref.current.scroll_to(
                offset=-1, duration=1000, curve=ft.AnimationCurve.EASE_OUT
            )
            page.update()

        except httpx.HTTPStatusError as ex:
            logger.error(f"Erro na API Anthropic: {ex.response.text or str(ex)}")
            page.open(
                ft.SnackBar(
                    ft.Text(f"Erro na API Anthropic: {ex.response.text or str(ex)}"),
                    bgcolor=ft.Colors.RED_700,
                )
            )
        except APIError as ex:
            if ex.code == "42501" or "permission denied" in str(ex).lower():
                if supabase_service.refresh_session():
                    page.go(page.route)
                else:
                    page.open(
                        ft.SnackBar(
                            ft.Text(
                                "Sessão expirada. Por favor, faça login novamente."
                            ),
                            bgcolor=ft.Colors.RED_700,
                        )
                    )
                    page.go("/login")
            else:
                logger.error(f"Erro ao obter resposta: {str(ex)}")
                page.open(
                    ft.SnackBar(
                        ft.Text(f"Erro ao obter resposta: {str(ex)}"),
                        bgcolor=ft.Colors.RED_700,
                    )
                )
        except Exception as ex:
            logger.error(f"Erro ao obter resposta: {str(ex)}")
            page.open(
                ft.SnackBar(
                    ft.Text(f"Erro ao obter resposta: {str(ex)}"),
                    bgcolor=ft.Colors.RED_700,
                )
            )
        finally:
            ask_button_ref.current.disabled = False
            ask_button_ref.current.content = ft.Text("Enviar")
            page.update()

    # Define o manipulador de clique assíncrono para o botão
    ask_button.on_click = lambda e: page.run_task(ask_question, e)

    # Executa a tarefa de carregamento ao iniciar
    page.run_task(load_chat)

    return ft.Column(
        ref=main_column_ref,
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
