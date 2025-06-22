import flet as ft
import asyncio
import time
from datetime import datetime
import uuid
from components.message import ChatMessage, Message
from services.supabase import SupabaseService
from services.anthropic import AnthropicService
from postgrest.exceptions import APIError
from utils.logger import get_logger
from utils.quebra_mensagem import integrate_with_chat
from utils.alerts import CustomSnackBar, CustomAlertDialog

logger = get_logger("supafit.trainer_chat.chat_logic")
COOLDOWN_SECONDS = 2


async def load_chat_history(
    supabase_service: SupabaseService,
    user_id: str,
    chat_container: ft.ListView,
    page: ft.Page,
) -> list:
    """Carrega o histórico de conversa do Supabase com animação de entrada."""
    try:
        chat_container.controls.clear()
        chat_container.controls.append(
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
            messages = item.get("message", [])
            history.extend(messages)
            for msg in messages:
                chat_container.controls.append(
                    ChatMessage(
                        Message(
                            user_name="Você" if msg["role"] == "user" else "Treinador",
                            text=msg["content"],
                            user_type=msg["role"],
                            created_at=msg["timestamp"],
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
                CustomSnackBar(
                    message="Sessão expirada. Faça login novamente.",
                    bgcolor=ft.Colors.RED_700,
                ).show(page)
                page.go("/login")
                return []
        logger.error(f"Erro ao carregar histórico: {str(e)}")
        CustomSnackBar(
            message="Erro ao carregar chat.", bgcolor=ft.Colors.RED_700
        ).show(page)
        return []


async def clear_chat(
    supabase_service: SupabaseService,
    user_id: str,
    chat_container: ft.ListView,
    page: ft.Page,
):
    """Limpa o histórico de conversa com confirmação visual."""

    async def confirm_clear(e):
        if e.control.text == "Sim":
            try:
                supabase_service.client.table("trainer_qa").delete().eq(
                    "user_id", user_id
                ).execute()
                chat_container.controls = [
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
                CustomSnackBar(message="Chat limpo com sucesso!").show(page)
                logger.info(f"Chat limpo para user_id: {user_id}")
            except APIError as ex:
                if ex.code == "42501":
                    if supabase_service.refresh_session():
                        page.go(page.route)
                    else:
                        CustomSnackBar(
                            message="Sessão expirada. Faça login novamente.",
                            bgcolor=ft.Colors.RED_700,
                        ).show(page)
                        page.go("/login")
                else:
                    logger.error(f"Erro ao limpar chat: {str(ex)}")
                    CustomSnackBar(
                        message=f"Erro ao limpar chat: {str(ex)}",
                        bgcolor=ft.Colors.RED_700,
                    ).show(page)
        page.close(confirm_dialog)
        page.update()

    confirm_dialog = CustomAlertDialog(
        content=ft.Text("Tem certeza que deseja limpar todo o histórico de mensagens?"),
        bgcolor=ft.Colors.GREY_900,
    )
    confirm_dialog.actions = [
        ft.TextButton("Sim", on_click=confirm_clear),
        ft.TextButton("Não", on_click=lambda e: page.close(confirm_dialog)),
    ]
    confirm_dialog.show(page)


async def ask_question(
    e,
    page: ft.Page,
    supabase_service: SupabaseService,
    anthropic: AnthropicService,
    question_field: ft.TextField,
    ask_button: ft.ElevatedButton,
    chat_container: ft.ListView,
    user_data: dict,
    user_id: str,
    last_question_time: list,
    history_cache: list,
):
    """Processa a pergunta do usuário com validações e animações."""
    current_time = time.time()
    if current_time - last_question_time[0] < COOLDOWN_SECONDS:
        CustomSnackBar(message="Aguarde antes de enviar outra pergunta!").show(page)
        return

    question = question_field.value.strip()
    if not question:
        question_field.error_text = "Digite uma pergunta!"
        page.update()
        return
    if len(question) > 500:
        question_field.error_text = "Pergunta muito longa (máximo 500 caracteres)."
        page.update()
        return
    if anthropic.is_sensitive_question(question):
        CustomSnackBar(
            message="Conversa sensível detectada.", bgcolor=ft.Colors.RED_700
        ).show(page)
        return

    ask_button.disabled = True
    ask_button.content = ft.Row(
        [ft.ProgressRing(width=16, height=16), ft.Text(" Enviando...")],
        alignment=ft.MainAxisAlignment.CENTER,
    )
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
                ),
                page,
            )
        )
        if len(chat_container.controls) > 50:
            chat_container.controls.pop(0)

        typing_indicator = ft.AnimatedSwitcher(
            content=ft.Row(
                [
                    ft.Text("Treinador está digitando"),
                    ft.ProgressRing(width=16, height=16),
                ]
            ),
            transition=ft.AnimatedSwitcherTransition.FADE,
            duration=500,
        )
        chat_container.controls.append(typing_indicator)
        page.update()
        await asyncio.sleep(1)

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
        answer = anthropic.answer_question(question, history_cache, system_prompt)
        if not answer or "desculpe" in answer.lower():
            raise ValueError("Resposta inválida do Anthropic")

        chat_container.controls.remove(typing_indicator)
        messages_with_delays = integrate_with_chat(answer)

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
            history_cache.append(message_json[-1])
            chat_container.controls.append(
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
            if len(chat_container.controls) > 50:
                chat_container.controls.pop(0)
            await asyncio.sleep(delay)
            page.update()

        supabase_service.client.table("trainer_qa").insert(
            {
                "user_id": user_id,
                "message": message_json,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }
        ).execute()
        question_field.value = ""
        question_field.error_text = None
        CustomSnackBar(message="Pergunta enviada com sucesso!").show(page)
        last_question_time[0] = current_time
        logger.info(f"Pergunta processada com sucesso para user_id: {user_id}")

    except Exception as ex:
        logger.error(f"Erro ao processar pergunta: {str(ex)}")
        CustomSnackBar(
            message=f"Erro ao obter resposta: {str(ex)}", bgcolor=ft.Colors.RED_700
        ).show(page)
    finally:
        ask_button.disabled = False
        ask_button.content = ft.Text("Enviar", size=14, weight=ft.FontWeight.W_600)
        page.update()
