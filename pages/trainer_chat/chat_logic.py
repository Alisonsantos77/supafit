import flet as ft
import asyncio
import time
from datetime import datetime
import uuid
import json
from .message import Message, ChatMessage
from services.supabase import SupabaseService
from services.openai import OpenAIService
from utils.alerts import CustomAlertDialog
from postgrest.exceptions import APIError
from utils.logger import get_logger
from utils.quebra_mensagem import integrate_with_chat
from services.trainer_functions import FUNCTIONS

logger = get_logger("supafit.trainer_chat")

COOLDOWN_SECONDS = 2


async def load_chat_history(
    supabase_service: SupabaseService,
    user_id: str,
    chat_container: ft.ListView,
    page: ft.Page,
) -> list:
    """Carrega o histórico de conversa com animação de entrada."""
    try:
        chat_container.controls.clear()
        chat_container.controls.append(
            ChatMessage(
                Message(
                    user_name="Treinador",
                    text="Olá! Como posso ajudar com seu treino hoje? 😄",
                    user_type="trainer",
                    created_at=datetime.now().isoformat(),
                    show_avatar=True,
                ),
                page,
            )
        )

        resp = (
            supabase_service.client.table("trainer_qa")
            .select("message")
            .eq("user_id", user_id)
            .order("updated_at")
            .limit(50)
            .execute()
        )

        history = []

        for item in resp.data:
            raw_message = item.get("message", [])
            if raw_message is None:
                logger.warning(f"Mensagem nula encontrada para user_id: {user_id}")
                continue
            if isinstance(raw_message, str):
                try:
                    messages = json.loads(raw_message)
                except Exception as e:
                    logger.error(f"Erro ao decodificar mensagem JSON: {e}")
                    continue
            else:
                messages = raw_message

            history.extend(messages)
            for msg in messages:
                if msg["role"] == "tool":
                    continue
                chat_container.controls.append(
                    ChatMessage(
                        Message(
                            user_name="Você" if msg["role"] == "user" else "Treinador",
                            text=msg["content"] or "Mensagem vazia",
                            user_type=msg["role"],
                            created_at=msg["timestamp"],
                            show_avatar=False,
                        ),
                        page,
                    )
                )

        page.update()
        logger.info(f"Histórico carregado para user_id: {user_id}")
        return history

    except APIError as e:
        if e.code == "42501":
            if supabase_service.refresh_session():
                page.go(page.route)
                return []
            else:
                page.open(
                    ft.SnackBar(
                        ft.Text(
                            "Sessão expirada. Faça login novamente.",
                            color=ft.Colors.WHITE,
                        ),
                        bgcolor=ft.Colors.RED_700,
                    )
                )
                page.update()
                page.go("/login")
                return []
        logger.error(f"Erro ao carregar histórico: {str(e)}")
        page.open(
            ft.SnackBar(
                ft.Text(
                    f"Erro ao carregar histórico: {str(e)}",
                    color=ft.Colors.WHITE,
                ),
                bgcolor=ft.Colors.RED_700,
            )
        )
        page.update()
        return []


async def clear_chat(
    supabase_service: SupabaseService,
    user_id: str,
    chat_container: ft.ListView,
    page: ft.Page,
):
    """Limpa o histórico com confirmação visual."""

    async def confirm_clear(e):
        if e.control.text == "Sim":
            try:
                supabase_service.client.table("trainer_qa").delete().eq(
                    "user_id", user_id
                ).execute()
                chat_container.controls.clear()
                chat_container.controls.append(
                    ChatMessage(
                        Message(
                            user_name="Treinador",
                            text="Olá! Como posso ajudar com seu treino hoje? 😄",
                            user_type="trainer",
                            created_at=datetime.now().isoformat(),
                            show_avatar=True,
                        ),
                        page,
                    )
                )
                page.update()
                page.open(
                    ft.SnackBar(
                        ft.Text("Chat limpo com sucesso!", color=ft.Colors.WHITE),
                        bgcolor=ft.Colors.GREEN_700,
                    )
                )
                page.update()
                logger.info(f"Chat limpo para user_id: {user_id}")
            except APIError as ex:
                if ex.code == "42501":
                    if supabase_service.refresh_session():
                        page.go(page.route)
                    else:
                        page.open(
                            ft.SnackBar(
                                ft.Text(
                                    "Sessão expirada. Faça login novamente.",
                                    color=ft.Colors.WHITE,
                                ),
                                bgcolor=ft.Colors.RED_700,
                            )
                        )
                        page.update()
                        page.go("/login")
                else:
                    logger.error(f"Erro ao limpar chat: {str(ex)}")
                    page.open(
                        ft.SnackBar(
                            ft.Text(
                                f"Erro ao limpar chat: {str(ex)}", color=ft.Colors.WHITE
                            ),
                            bgcolor=ft.Colors.RED_700,
                        )
                    )
                    page.update()
            finally:
                page.close(confirm_dialog)
                page.update()
        else:
            page.close(confirm_dialog)
            page.update()

    confirm_dialog = CustomAlertDialog(
        content=ft.Text("Tem certeza que deseja limpar todo o histórico de mensagens?"),
        bgcolor=ft.Colors.GREY_900,
    )
    confirm_dialog.actions = [
        ft.TextButton("Sim", on_click=confirm_clear),
        ft.TextButton("Não", on_click=confirm_clear),
    ]
    confirm_dialog.show(page)


async def ask_question(
    e,
    page: ft.Page,
    supabase_service: SupabaseService,
    openai: OpenAIService,
    question_field: ft.TextField,
    ask_button: ft.IconButton,
    chat_container: ft.ListView,
    user_data: dict,
    user_id: str,
    last_question_time: list,
    history_cache: list,
):
    """Processa a pergunta do usuário com validações, animações e feedback visual, incluindo suporte a function calling."""
    current_time = time.time()
    if current_time - last_question_time[0] < COOLDOWN_SECONDS:
        page.open(
            ft.SnackBar(
                ft.Text(
                    "Aguarde alguns segundos antes de enviar outra pergunta.",
                    color=ft.Colors.WHITE,
                ),
                bgcolor=ft.Colors.RED_700,
            )
        )
        page.update()
        return

    question = question_field.value.strip()
    if not question:
        question_field.error_text = "Digite uma mensagem!"
        page.update()
        return
    if len(question) > 500:
        question_field.error_text = "Mensagem muito longa (máximo 500 caracteres)."
        page.update()
        return
    if openai.is_sensitive_question(question):
        page.open(
            ft.SnackBar(
                ft.Text("Pergunta sensível detectada.", color=ft.Colors.WHITE),
                bgcolor=ft.Colors.RED_700,
            )
        )
        page.update()
        return

    ask_button.disabled = True
    ask_button.icon_color = ft.Colors.GREY_400
    question_field.value = ""
    page.update()

    try:
        question_id = str(uuid.uuid4())
        chat_container.controls.append(
            ChatMessage(
                Message(
                    user_name="Você",
                    text=question,
                    user_type="user",
                    created_at=datetime.now().isoformat(),
                    show_avatar=False,
                ),
                page,
            )
        )
        if len(chat_container.controls) > 50:
            chat_container.controls.pop(0)

        typing_indicator = ft.AnimatedSwitcher(
            content=ft.Row(
                [
                    ft.Text("Treinador está digitando...", size=14, italic=True),
                    ft.ProgressRing(width=16, height=16, stroke_width=2),
                ],
                alignment=ft.MainAxisAlignment.START,
                spacing=8,
            ),
            transition=ft.AnimatedSwitcherTransition.FADE,
            duration=300,
        )

        # Preparar mensagens para a chamada da API, incluindo o histórico
        messages = history_cache + [
            {
                "role": "user",
                "content": question,
                "message_id": question_id,
                "timestamp": datetime.now().isoformat(),
            }
        ]

        # Primeira chamada à API com suporte a ferramentas
        response = await openai.chat_with_functions(
            messages=messages,
            functions=FUNCTIONS,
            function_call="auto",
        )

        message_json = messages.copy()

        # Verificar se a resposta requer uma chamada de função
        if response.choices[0].finish_reason == "tool_calls":
            tool_calls = response.choices[0].message.tool_calls
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)

                logger.info(
                    f"[FunctionCalling] user_id={user_id} chamou '{function_name}' com {arguments}"
                )

                function_result = await openai.execute_function_by_name(
                    function_name, arguments
                )

                message_json.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        # "content": str(function_result),
                        "content": (
                            json.dumps(function_result, indent=2)
                            if isinstance(function_result, (dict, list))
                            else str(function_result)
                        ),
                        "timestamp": datetime.now().isoformat(),
                    }
                )

            # Nova chamada à API com o resultado da função
            response = await openai.chat_with_functions(
                messages=message_json,
                functions=FUNCTIONS,
                function_call="auto",
            )

        # Obter a mensagem final
        final_message = response.choices[0].message.content
        if not final_message:
            logger.warning("Resposta do modelo vazia após function calling.")
            final_message = "Desculpe, não consegui gerar uma resposta agora. Tente novamente em instantes. 💬"

        messages_with_delays = integrate_with_chat(final_message)

        for msg, delay in messages_with_delays:
            if not msg.strip():
                continue
            chat_container.controls.append(typing_indicator)
            page.update()
            await asyncio.sleep(0.3)
            chat_container.controls.remove(typing_indicator)

            response_id = str(uuid.uuid4())
            message_json.append(
                {
                    "role": "assistant",
                    "content": msg,
                    "message_id": response_id,
                    "timestamp": datetime.now().isoformat(),
                }
            )
            history_cache.append(message_json[-1])
            chat_container.controls.append(
                ChatMessage(
                    Message(
                        user_name="Treinador",
                        text=msg.strip() or "Mensagem vazia",
                        user_type="assistant",
                        created_at=datetime.now().isoformat(),
                        show_avatar=False,
                    ),
                    page,
                )
            )
            if len(chat_container.controls) > 50:
                chat_container.controls.pop(0)
            await asyncio.sleep(delay * 0.3)
            page.update()

        if len(message_json) > 1:
            supabase_service.client.table("trainer_qa").upsert(
                {
                    "user_id": user_id,
                    "message": message_json,
                },
                on_conflict="user_id",
            ).execute()
        question_field.error_text = None
        page.open(
            ft.SnackBar(
                ft.Text("Pergunta enviada com sucesso!", color=ft.Colors.WHITE),
                bgcolor=ft.Colors.GREEN_700,
            )
        )
        page.update()
        last_question_time[0] = current_time
        logger.info(f"Pergunta processada com sucesso para user_id: {user_id}")

    except Exception as ex:
        logger.error(f"Erro ao processar pergunta: {str(ex)}")
        page.open(
            ft.SnackBar(
                ft.Text(
                    f"Erro ao processar pergunta: {str(ex)}", color=ft.Colors.WHITE
                ),
                bgcolor=ft.Colors.RED_700,
            )
        )
    finally:
        ask_button.disabled = False
        ask_button.icon_color = ft.Colors.BLUE_400
        page.update()
