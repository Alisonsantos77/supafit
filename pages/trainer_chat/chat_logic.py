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
from utils.quebra_mensagem import integrate_with_chat
from services.trainer_functions import TOOLS  # Importar TOOLS

# Cache global para armazenar planos e histórico
cached_plans = {}
cached_history = {}

COOLDOWN_SECONDS = 2


def filtered(history):
    """Filtra mensagens de ferramenta do histórico."""
    return [msg for msg in history if msg.get("role") != "tool"]


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

        # Verificar cache antes de consultar o Supabase
        if user_id in cached_history:
            history = cached_history[user_id]
            print(f"INFO: Histórico carregado do cache para user_id: {user_id}")
        else:
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
                    continue
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
            cached_history[user_id] = history
            print(f"INFO: Histórico carregado do Supabase para user_id: {user_id}")

        for msg in history:
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
        print(f"ERROR: Erro ao carregar histórico para user_id: {user_id} - {e}")
        page.open(
            ft.SnackBar(
                ft.Text(f"Erro ao carregar histórico: {str(e)}", color=ft.Colors.WHITE),
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
                # Limpar cache do histórico
                cached_history.pop(user_id, None)
                print(f"INFO: Chat limpo para user_id: {user_id}")
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
                    print(f"ERROR: Erro ao limpar chat para user_id: {user_id} - {ex}")
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
    """Processa pergunta do usuário e atualiza o plano de treino."""
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
    if await openai.is_sensitive_question(question):
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

        system_msg = {
            "role": "system",
            "content": OpenAIService.get_system_prompt(user_data, user_id),
        }

        filtered_history = filtered(history_cache)  # Usar função definida
        user_message = {
            "role": "user",
            "content": question,
            "message_id": question_id,
            "timestamp": datetime.now().isoformat(),
        }

        messages = [system_msg] + filtered_history + [user_message]
        messages_to_save = [msg for msg in messages if msg.get("role") != "system"]

        max_iterations = 5
        iteration = 0
        last_tool = None

        while iteration < max_iterations:
            iteration += 1
            print(
                f"INFO: Iteração {iteration} - Enviando {len(messages)} mensagens para OpenAI"
            )

            response = await openai.chat_with_tools(
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
            )
            print(f"INFO: Iteração {iteration} - Resposta recebida do OpenAI")

            assistant_message = response.choices[0].message
            assistant_message_dict = {
                "role": "assistant",
                "content": assistant_message.content or "",
                "timestamp": datetime.now().isoformat(),
            }
            if assistant_message.tool_calls:
                assistant_message_dict["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in assistant_message.tool_calls
                ]
            messages.append(assistant_message_dict)
            messages_to_save.append(assistant_message_dict)

            if not assistant_message.tool_calls:
                final_message = (
                    assistant_message.content or f"Plano atualizado com sucesso!"
                    if last_tool == "update_plan_exercise"
                    else "Desculpe, não consegui processar sua solicitação. Tente novamente."
                )
                break

            for tc in assistant_message.tool_calls:
                try:
                    fname = tc.function.name
                    fargs = json.loads(tc.function.arguments)

                    if fname in ["add_exercise_to_plan", "update_plan_exercise"]:
                        plan_id = fargs.get("plan_id")
                        exercise_id = fargs.get(
                            "exercise_id",
                            fargs.get("exercises", [{}])[0].get("exercise_id"),
                        )
                        if plan_id and exercise_id:
                            plan = (
                                supabase_service.client.table("user_plans")
                                .select("title")
                                .eq("plan_id", plan_id)
                                .execute()
                                .data
                            )
                            exercise = (
                                supabase_service.client.table("exercicios")
                                .select("grupo_muscular")
                                .eq("id", exercise_id)
                                .execute()
                                .data
                            )
                            if plan and exercise:
                                title = plan[0]["title"].lower()
                                grupo_muscular = exercise[0]["grupo_muscular"].lower()
                                if "costas" in title and not (
                                    "dorsal" in grupo_muscular
                                    or "bíceps" in grupo_muscular
                                ):
                                    raise ValueError(
                                        f"Exercício {exercise_id} não corresponde ao grupo muscular esperado para o plano {plan_id}."
                                    )

                    # Validação de UUID para update_plan_exercise
                    if fname == "update_plan_exercise":
                        plan_exercise_id = fargs.get("plan_exercise_id")
                        plan_exercise = (
                            supabase_service.client.table("plan_exercises")
                            .select("plan_exercise_id")
                            .eq("plan_id", plan_id)
                            .eq("exercise_id", exercise_id)
                            .execute()
                            .data
                        )
                        if plan_exercise:
                            fargs["plan_exercise_id"] = plan_exercise[0][
                                "plan_exercise_id"
                            ]
                        else:
                            raise ValueError(
                                f"ID de plan_exercise inválido: {plan_exercise_id}"
                            )

                    fargs["supabase"] = supabase_service.client
                    print(
                        f"INFO: Iteração {iteration} - Chamando função '{fname}' com args: {fargs}"
                    )
                    fres = await openai.execute_function_by_name(fname, fargs)
                    print(
                        f"INFO: Iteração {iteration} - Função '{fname}' executada com sucesso"
                    )

                    tool_message = {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "name": fname,
                        "content": json.dumps(fres, ensure_ascii=False, default=str),
                        "timestamp": datetime.now().isoformat(),
                    }
                    messages.append(tool_message)
                    messages_to_save.append(tool_message)
                    last_tool = fname

                except Exception as tool_error:
                    print(
                        f"ERROR: Iteração {iteration} - Erro ao executar função '{fname}': {tool_error}"
                    )
                    error_message = {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "name": fname,
                        "content": json.dumps(
                            {"error": f"Erro ao executar função: {str(tool_error)}"},
                            ensure_ascii=False,
                        ),
                        "timestamp": datetime.now().isoformat(),
                    }
                    messages.append(error_message)
                    messages_to_save.append(error_message)

        for msg, delay in integrate_with_chat(final_message):
            if not msg.strip():
                continue

            chat_container.controls.append(typing_indicator)
            page.update()
            await asyncio.sleep(0.3)
            chat_container.controls.remove(typing_indicator)

            response_id = str(uuid.uuid4())
            assistant_response = {
                "role": "assistant",
                "content": msg.strip(),
                "message_id": response_id,
                "timestamp": datetime.now().isoformat(),
            }
            messages_to_save.append(assistant_response)
            if assistant_response.get("role") != "tool":
                history_cache.append(assistant_response)

            chat_container.controls.append(
                ChatMessage(
                    Message(
                        user_name="Treinador",
                        text=msg.strip(),
                        user_type="assistant",
                        created_at=datetime.now().isoformat(),
                        show_avatar=False,
                    ),
                    page,
                )
            )
            if len(chat_container.controls) > 50:
                chat_container.controls.pop(0)
            page.update()
            await asyncio.sleep(delay * 0.3)

        try:
            supabase_service.client.table("trainer_qa").upsert(
                {"user_id": user_id, "message": messages_to_save},
                on_conflict="user_id",
            ).execute()
            cached_history[user_id] = messages_to_save  # Atualizar cache
            print(f"INFO: Histórico salvo com sucesso para user_id: {user_id}")
        except Exception as save_error:
            print(
                f"ERROR: Falha ao salvar histórico para user_id: {user_id} - {save_error}"
            )
        page.open(
            ft.SnackBar(
                ft.Text("Pergunta enviada com sucesso!", color=ft.Colors.WHITE),
                bgcolor=ft.Colors.GREEN_700,
            )
        )
        page.update()
        last_question_time[0] = current_time
        print(f"INFO: Pergunta processada com sucesso para user_id: {user_id}")

    except Exception as ex:
        print(f"ERROR: Erro ao processar pergunta para user_id: {user_id} - {ex}")
        page.open(
            ft.SnackBar(
                ft.Text(f"Erro ao processar pergunta: {ex}", color=ft.Colors.WHITE),
                bgcolor=ft.Colors.RED_700,
            )
        )
        page.update()

    finally:
        ask_button.disabled = False
        ask_button.icon_color = ft.Colors.BLUE_400
        page.update()
