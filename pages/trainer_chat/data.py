import flet as ft
import asyncio
import time
from datetime import datetime
import uuid
from components.message import ChatMessage, Message
from services.services import AnthropicService, SupabaseService
from postgrest.exceptions import APIError
from utils.quebra_mensagem import integrate_with_chat
from utils.logger import get_logger

COOLDOWN_SECONDS = 2

logger = get_logger("supabafit.trainer_chat.data")


def get_user_profile(supabase_service: SupabaseService, user_id: str) -> dict:
    """Carrega os dados do perfil do usuário do Supabase."""
    try:
        user_profile = (
            supabase_service.client.table("user_profiles")
            .select("name, age, weight, height, goal, level")
            .eq("user_id", user_id)
            .execute()
            .data
        )
        return (
            user_profile[0]
            if user_profile
            else {
                "name": "Usuário",
                "age": "N/A",
                "weight": "N/A",
                "height": "N/A",
                "goal": "N/A",
                "level": "N/A",
                "user_id": user_id,
            }
        )
    except Exception as e:
        logger.error(f"Erro ao carregar perfil do usuário {user_id}: {str(e)}")
        return {
            "name": "Usuário",
            "age": "N/A",
            "weight": "N/A",
            "height": "N/A",
            "goal": "N/A",
            "level": "N/A",
            "user_id": user_id,
        }


async def load_chat_history(
    supabase_service, user_id: str, chat_container: ft.ListView, page: ft.Page
) -> list:
    """Carrega o histórico de conversa do Supabase e atualiza o contêiner do chat."""
    try:
        resp = (
            supabase_service.client.table("trainer_qa")
            .select("message")
            .eq("user_id", user_id)
            .order("updated_at")
            .limit(50)
            .execute()
        )
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

        for item in resp.data:
            messages = item.get("message", [])
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
        return resp.data
    except APIError as e:
        if e.code == "42501":
            if supabase_service.refresh_session():
                page.go(page.route)
                return []
            else:
                page.open(
                    ft.SnackBar(
                        ft.Text("Sessão expirada. Por favor, faça login novamente."),
                        bgcolor=ft.Colors.RED_700,
                    )
                )
                page.go("/login")
                return []
        logger.error(f"Erro ao carregar histórico de chat: {str(e)}")
        page.open(ft.SnackBar(ft.Text(f"Erro ao carregar chat: {str(e)}")))
        return []


async def clear_chat(
    supabase_service, user_id: str, chat_container: ft.ListView, page: ft.Page
):
    """Limpa o histórico de conversa após confirmação do usuário."""

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
                    page.open(ft.SnackBar(ft.Text(f"Erro ao limpar chat: {str(ex)}")))
        page.close(confirm_dialog)
        page.update()

    confirm_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Limpar Chat"),
        content=ft.Text("Tem certeza que deseja limpar todo o histórico de mensagens?"),
        actions=[
            ft.TextButton("Sim", on_click=confirm_clear),
            ft.TextButton("Não", on_click=lambda e: page.close(confirm_dialog)),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    page.open(confirm_dialog)


async def ask_question(
    e,
    page: ft.Page,
    supabase_service,
    anthropic: AnthropicService,
    question_field: ft.TextField,
    ask_button: ft.ElevatedButton,
    chat_container: ft.ListView,
    user_data: dict,
    last_question_time: list,
):
    """Processa a submissão de uma pergunta e obtém a resposta da IA."""
    current_time = time.time()
    if current_time - last_question_time[0] < COOLDOWN_SECONDS:
        page.open(
            ft.SnackBar(ft.Text("Aguarde um momento antes de enviar outra pergunta!"))
        )
        return

    question = question_field.value.strip()
    if not question:
        page.open(ft.SnackBar(ft.Text("Digite uma pergunta!")))
        return
    if len(question) > 500:
        page.open(ft.SnackBar(ft.Text("Pergunta muito longa (máximo 500 caracteres).")))
        return
    if anthropic.is_sensitive_question(question):
        page.open(
            ft.SnackBar(ft.Text("Conversa sensível detectada.", color=ft.Colors.WHITE), bgcolor=ft.Colors.RED)
        )
        return

    ask_button.disabled = True
    ask_button.content = ft.Row(
        [ft.ProgressRing(width=16, height=16), ft.Text(" Enviando...")],
        alignment=ft.MainAxisAlignment.CENTER,
    )
    page.update()

    try:
        history = []
        resp = (
            supabase_service.client.table("trainer_qa")
            .select("message")
            .eq("user_id", user_data["user_id"])
            .order("updated_at")
            .execute()
        )
        for item in resp.data:
            history.extend(item["message"])

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
            reverse_duration=500,
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
        answer = anthropic.answer_question(question, history, system_prompt)
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

        response = (
            await supabase_service.client.table("trainer_qa")
            .insert(
                {
                    "user_id": user_data["user_id"],
                    "message": message_json,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                }
            )
            .execute()
        )
        logger.info(f"Inserção bem-sucedida: {response.data}")

        question_field.value = ""
        page.open(ft.SnackBar(ft.Text("Pergunta enviada com sucesso!")))
        last_question_time[0] = current_time
        page.update()

    except Exception as ex:
        logger.error(f"Erro ao processar pergunta: {str(ex)}")
        page.open(
            ft.SnackBar(
                ft.Text(f"Erro ao obter resposta: {str(ex)}"), bgcolor=ft.Colors.RED_700
            )
        )
    finally:
        ask_button.disabled = False
        ask_button.content = ft.Text("Enviar")
        page.update()
