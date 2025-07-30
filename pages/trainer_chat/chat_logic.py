import flet as ft
import asyncio
import time
from datetime import datetime
import uuid
import json
from .message import Message, ChatMessage
from services.supabase import SupabaseService
from services.openai import OpenAIService
from postgrest.exceptions import APIError
from utils.quebra_mensagem import integrate_with_chat
from services.trainer_functions import TOOLS


COOLDOWN_SECONDS = 2


def filtered(history):
    return [msg for msg in history if msg.get("role") != "tool"]


async def load_chat_history(
    supabase_service: SupabaseService,
    user_id: str,
    chat_container: ft.ListView,
    page: ft.Page,
    haptic_feedback: ft.HapticFeedback,
    user_data: dict,
):
    try:
        chat_container.controls.clear()
        chat_container.controls.append(
            ChatMessage(
                Message(
                    user_name="Treinador Coachito",
                    text="Olá! Como posso ajudar com seu treino hoje? 😄",
                    user_type="trainer",
                    created_at=datetime.now().isoformat(),
                    show_avatar=True,
                ),
                page,
                haptic_feedback,
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
                print(f"WARNING: Mensagem nula encontrada para user_id: {user_id}")
                raw_message = []
            if isinstance(raw_message, str):
                try:
                    messages = json.loads(raw_message)
                except Exception as e:
                    print(
                        f"ERROR: Falha ao decodificar mensagem JSON para user_id: {user_id} - {e}"
                    )
                    continue
            else:
                messages = raw_message
            history.extend(messages)

        for msg in history:
            if msg.get("role") == "tool":
                continue

            if (
                not isinstance(msg, dict)
                or not msg.get("role")
                or not msg.get("content")
            ):
                print(f"WARNING: Mensagem inválida ignorada: {msg}")
                continue

            created_at = (
                msg.get("timestamp")
                or msg.get("created_at")
                or datetime.now().isoformat()
            )

            chat_container.controls.append(
                ChatMessage(
                    Message(
                        user_name="Você" if msg.get("role") == "user" else "Treinador",
                        text=msg.get("content") or "Mensagem vazia",
                        user_type=msg.get("role", "user"),
                        created_at=created_at,
                        show_avatar=True,
                        gender=(
                            user_data.get("gender", "neutro")
                            if msg.get("role") == "user"
                            else "neutro"
                        ),
                        user_id=user_id if msg.get("role") == "user" else None,
                    ),
                    page,
                    haptic_feedback,
                )
            )
    except APIError as ex:
        print(
            f"ERROR: Falha ao carregar histórico de chat para user_id: {user_id} - {ex}"
        )
        page.update()
        return []
    except Exception as ex:
        print(
            f"ERROR: Erro inesperado ao carregar histórico para user_id: {user_id} - {ex}"
        )
        page.update()
        return []

    page.update()
    return []


async def clear_chat(
    supabase_service: SupabaseService,
    user_id: str,
    chat_container: ft.ListView,
    page: ft.Page,
    haptic_feedback: ft.HapticFeedback,
):
    print(f"INFO: Iniciando clear_chat para user_id: {user_id}")

    async def confirm_clear(e):
        print(f"INFO: Botão clicado no diálogo: {e.control.text}")
        if e.control.text == "Sim":
            try:
                print("INFO: Executando DELETE no Supabase")
                supabase_service.client.table("trainer_qa").delete().eq(
                    "user_id", user_id
                ).execute()
                chat_container.controls.clear()
                chat_container.controls.append(
                    ChatMessage(
                        Message(
                            user_name="Treinador Coachito",
                            text="Olá! Como posso ajudar com seu treino hoje? 😄",
                            user_type="trainer",
                            created_at=datetime.now().isoformat(),
                            show_avatar=True,
                        ),
                        page,
                        haptic_feedback,
                    )
                )
                page.update()
                haptic_feedback.light_impact()
                page.open(ft.SnackBar(ft.Text("Chat limpo com sucesso!")))
                page.update()
            except APIError as ex:
                print(f"ERROR: Erro ao limpar chat para user_id: {user_id} - {ex}")
                if ex.code == "42501":
                    if supabase_service.refresh_session():
                        page.go(page.route)
                    else:
                        haptic_feedback.heavy_impact()
                        page.open(
                            ft.SnackBar(
                                ft.Text("Sessão expirada. Faça login novamente.")
                            )
                        )
                        page.update()
                        page.go("/login")
                else:
                    haptic_feedback.heavy_impact()
                    page.open(ft.SnackBar(ft.Text(f"Erro ao limpar chat: {str(ex)}")))
                    page.update()
            finally:
                page.close(confirm_dialog)
                page.update()
        else:
            page.close(confirm_dialog)
            page.update()

    confirm_dialog = ft.AlertDialog(
        title=ft.Text("Confirmar Limpeza"),
        content=ft.Text("Tem certeza que deseja limpar todo o histórico de mensagens?", color=ft.Colors.ON_SURFACE),
        actions=[
            ft.TextButton("Sim", on_click=confirm_clear),
            ft.TextButton("Não", on_click=confirm_clear),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    page.open(confirm_dialog)
    page.update()


async def get_conversation_history(supabase_service: SupabaseService, user_id: str):
    try:
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
                raw_message = []
            if isinstance(raw_message, str):
                try:
                    messages = json.loads(raw_message)
                except:
                    continue
            else:
                messages = raw_message
            history.extend(messages)

        filtered_history = []
        for msg in history:
            if msg.get("role") in ["user", "assistant"] and msg.get("content"):
                clean_msg = {"role": msg["role"], "content": msg["content"]}
                filtered_history.append(clean_msg)

        return filtered_history

    except Exception as ex:
        print(f"ERROR: Erro ao buscar histórico: {ex}")
        return []


async def save_conversation_history(
    supabase_service: SupabaseService, user_id: str, new_messages: list
):
    try:
        current_history = await get_conversation_history(supabase_service, user_id)
        updated_history = current_history + new_messages

        supabase_service.client.table("trainer_qa").upsert(
            {"user_id": user_id, "message": updated_history}, on_conflict="user_id"
        ).execute()

        print(f"INFO: Histórico salvo para {user_id}")
        return True

    except Exception as err:
        print(f"ERROR: Falha ao salvar histórico: {err}")
        return False


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
    haptic_feedback: ft.HapticFeedback,
):
    current_time = time.time()
    if current_time - last_question_time[0] < COOLDOWN_SECONDS:
        haptic_feedback.medium_impact()
        page.open(
            ft.SnackBar(
                ft.Text(f"Espere {COOLDOWN_SECONDS} segundos antes de outra pergunta.")
            )
        )
        page.update()
        return

    question = question_field.value.strip()
    if not question:
        question_field.error_text = "Digite uma mensagem!"
        page.update()
        return
    if len(question) > 50:
        question_field.error_text = "Mensagem muito longa (máx. 50 chars)."
        page.update()
        return
    if await openai.is_sensitive_question(question):
        print("INFO: Pergunta sensível detectada")
        haptic_feedback.medium_impact()
        page.open(ft.SnackBar(ft.Text("Pergunta sensível detectada.")))
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
                    show_avatar=True,
                    gender=user_data.get("gender", "neutro"),
                ),
                page,
                haptic_feedback,
            )
        )
        if len(chat_container.controls) > 50:
            chat_container.controls.pop(0)

        typing = ft.AnimatedSwitcher(
            content=ft.Row(
                [
                    ft.Text("Coachito está digitando...", size=14, italic=True),
                    ft.ProgressRing(width=16, height=16, stroke_width=2),
                ],
                alignment=ft.MainAxisAlignment.START,
                spacing=8,
            ),
            transition=ft.AnimatedSwitcherTransition.FADE,
            duration=300,
        )

        system_msg = {
            "role": "system",
            "content": OpenAIService.get_system_prompt(user_data, user_id),
        }

        filtered_history = await get_conversation_history(supabase_service, user_id)

        user_msg = {
            "role": "user",
            "content": question,
        }

        messages = [system_msg] + filtered_history + [user_msg]

        max_iter = 5
        assistant_content = ""

        for it in range(1, max_iter + 1):
            response = await openai.chat_with_tools(
                messages=messages, tools=TOOLS, tool_choice="auto"
            )
            choice = response.choices[0].message
            assistant_content = choice.content or ""

            if not getattr(choice, "tool_calls", None):
                final_assistant_msg = {
                    "role": "assistant",
                    "content": assistant_content,
                }
                messages.append(final_assistant_msg)
                break

            assistant_msg = {
                "role": "assistant",
                "content": assistant_content,
                "tool_calls": [],
            }

            for tc in choice.tool_calls:
                assistant_msg["tool_calls"].append(
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                )

            messages.append(assistant_msg)

            for tc in choice.tool_calls:
                fname = tc.function.name
                try:
                    args = json.loads(tc.function.arguments)
                    args["supabase"] = supabase_service.client
                    if fname == "update_plan_exercise":
                        if not args.get("plan_exercise_id"):
                            raise ValueError(
                                "update_plan_exercise requer plan_exercise_id"
                            )
                        if not args.get("new_exercise_name"):
                            raise ValueError(
                                "update_plan_exercise requer new_exercise_name"
                            )
                    fres = await openai.execute_function_by_name(fname, args)
                    tool_msg = {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(fres, ensure_ascii=False, default=str),
                    }
                    messages.append(tool_msg)
                except json.JSONDecodeError as e:
                    error_msg = {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(
                            {"error": f"Erro de formato JSON: {str(e)}"},
                            ensure_ascii=False,
                        ),
                    }
                    messages.append(error_msg)
                except Exception as e:
                    error_msg = {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(
                            {"error": f"Erro na execução: {str(e)}"}, ensure_ascii=False
                        ),
                    }
                    messages.append(error_msg)

        for chunk, delay in integrate_with_chat(assistant_content):
            if not chunk.strip():
                continue
            chat_container.controls.append(typing)
            page.update()
            await asyncio.sleep(0.3)
            chat_container.controls.remove(typing)

            chat_container.controls.append(
                ChatMessage(
                    Message(
                        "Treinador Coachito",
                        chunk.strip(),
                        "assistant",
                        datetime.now().isoformat(),
                        True,
                    ),
                    page,
                    haptic_feedback,
                )
            )
            if len(chat_container.controls) > 50:
                chat_container.controls.pop(0)
            page.update()
            await asyncio.sleep(delay * 0.3)

        new_messages = [
            {
                "role": "user",
                "content": question,
                "message_id": question_id,
                "timestamp": datetime.now().isoformat(),
            },
            {
                "role": "assistant",
                "content": assistant_content,
                "timestamp": datetime.now().isoformat(),
            },
        ]

        await save_conversation_history(supabase_service, user_id, new_messages)

        haptic_feedback.light_impact()
        page.open(ft.SnackBar(ft.Text("Pergunta enviada com sucesso!")))
        page.update()
        last_question_time[0] = current_time

    except Exception as ex:
        print(f"ERROR: ask_question falhou: {ex}")
        haptic_feedback.heavy_impact()
        page.open(ft.SnackBar(ft.Text(f"Erro: {ex}")))
        page.update()

    finally:
        ask_button.disabled = False
        ask_button.icon_color = ft.Colors.BLUE_400
        page.update()
