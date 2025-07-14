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
    haptic_feedback: ft.HapticFeedback,
    user_data: dict
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
                haptic_feedback,
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
            if msg.get("role") == "tool":
                continue

            created_at = msg.get("timestamp") or msg.get("created_at")
            
            if created_at is None:
                print("⚠️ Mensagem sem campo de data:", msg)
                created_at = datetime.now().isoformat()
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

        page.update()
        return history

    except APIError as e:
        if e.code == "42501":
            if supabase_service.refresh_session():
                page.go(page.route)
                return []
            else:
                haptic_feedback.heavy_impact()
                page.open(
                    ft.SnackBar(ft.Text("Sessão expirada. Faça login novamente."))
                )
                page.update()
                page.go("/login")
                return []
        print(f"ERROR: Erro ao carregar histórico para user_id: {user_id} - {e}")
        haptic_feedback.heavy_impact()
        page.open(ft.SnackBar(ft.Text(f"Erro ao carregar histórico: {str(e)}")))
        page.update()
        return []

async def clear_chat(
    supabase_service: SupabaseService,
    user_id: str,
    chat_container: ft.ListView,
    page: ft.Page,
    haptic_feedback: ft.HapticFeedback,
):
    """Limpa o histórico com confirmação visual."""
    print(f"INFO: Iniciando clear_chat para user_id: {user_id}")

    async def confirm_clear(e):
        print(f"INFO: Botão clicado no diálogo: {e.control.text}")
        if e.control.text == "Sim":
            try:
                print("INFO: Executando DELETE no Supabase")
                supabase_service.client.table("trainer_qa").delete().eq(
                    "user_id", user_id
                ).execute()
                print(f"INFO: Controles antes da limpeza: {len(chat_container.controls)}")
                chat_container.controls.clear()
                print(f"INFO: Controles após limpeza: {len(chat_container.controls)}")
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
                        haptic_feedback,
                    )
                )
                page.update()
                haptic_feedback.light_impact()
                page.open(ft.SnackBar(ft.Text("Chat limpo com sucesso!")))
                page.update()
                print(f"INFO: Cache antes da limpeza: {user_id in cached_history}")
                cached_history.pop(user_id, None)
                print(f"INFO: Cache após a limpeza: {user_id in cached_history}")
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
            print("INFO: Diálogo fechado sem ação")
            page.close(confirm_dialog)
            page.update()

    confirm_dialog = ft.AlertDialog(
        title=ft.Text("Confirmar Limpeza"),
        content=ft.Text("Tem certeza que deseja limpar todo o histórico de mensagens?"),
        bgcolor=ft.Colors.GREY_900,
        actions=[
            ft.TextButton("Sim", on_click=confirm_clear),
            ft.TextButton("Não", on_click=confirm_clear),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
        modal=True,
    )
    print("INFO: Exibindo diálogo de confirmação")
    page.open(confirm_dialog)
    print("DEBUG: Após chamar page.open para confirm_dialog")
    page.update()

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
    """Processa pergunta do usuário, lida com function calling e atualiza o chat e o plano de treino."""
    current_time = time.time()
    if current_time - last_question_time[0] < COOLDOWN_SECONDS:
        print(f"WARNING: Tentativa antes do cooldown de {COOLDOWN_SECONDS}s")
        haptic_feedback.medium_impact()
        page.open(
            ft.SnackBar(
                ft.Text(f"Espere {COOLDOWN_SECONDS} segundos antes de outra pergunta.")
            )
        )
        page.update()
        return

    question = question_field.value.strip()
    # Validações iniciais
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

    # Desabilita botão e limpa campo
    ask_button.disabled = True
    ask_button.icon_color = ft.Colors.GREY_400
    question_field.value = ""
    page.update()

    try:
        # Exibe pergunta do usuário no chat
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

        filtered_history = []
        for msg in history_cache:
            if msg.get("role") in ["user", "assistant"] and msg.get("content"):
                clean_msg = {"role": msg["role"], "content": msg["content"]}
                filtered_history.append(clean_msg)

        user_msg = {
            "role": "user",
            "content": question,
        }

        messages = [system_msg] + filtered_history + [user_msg]

        convo_history = filtered_history + [
            {
                "role": "user",
                "content": question,
                "message_id": question_id,
                "timestamp": datetime.now().isoformat(),
            }
        ]

        max_iter = 5
        assistant_content = ""

        for it in range(1, max_iter + 1):
            print(f"INFO: Iteração {it}, mensagens: {len(messages)}")

            print(f"DEBUG: Estrutura das mensagens:")
            for i, msg in enumerate(messages):
                print(
                    f"  [{i}] role: {msg.get('role')}, content_length: {len(str(msg.get('content', '')))}"
                )
                if "tool_calls" in msg:
                    print(f"      tool_calls: {len(msg['tool_calls'])}")
                if "tool_call_id" in msg:
                    print(f"      tool_call_id: {msg['tool_call_id']}")

            response = await openai.chat_with_tools(
                messages=messages, tools=TOOLS, tool_choice="auto"
            )
            choice = response.choices[0].message
            assistant_content = choice.content or ""

            # Se não há tool_calls, finalizamos
            if not getattr(choice, "tool_calls", None):
                # Adiciona resposta final às mensagens
                final_assistant_msg = {
                    "role": "assistant",
                    "content": assistant_content,
                }
                messages.append(final_assistant_msg)

                convo_history.append(
                    {
                        "role": "assistant",
                        "content": assistant_content,
                        "timestamp": datetime.now().isoformat(),
                    }
                )
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
                    print(f"DEBUG: Chamada de {fname} com args: {args}")
                    args["supabase"] = supabase_service.client

                    # Validação específica para update_plan_exercise
                    if fname == "update_plan_exercise":
                        if not args.get("plan_exercise_id"):
                            raise ValueError(
                                "update_plan_exercise requer plan_exercise_id"
                            )
                        if not args.get("new_exercise_name"):
                            raise ValueError(
                                "update_plan_exercise requer new_exercise_name"
                            )

                    print(f"INFO: Executando {fname}")
                    fres = await openai.execute_function_by_name(fname, args)
                    print(f"INFO: {fname} retornou: {fres}")

                    tool_msg = {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(fres, ensure_ascii=False, default=str),
                    }
                    messages.append(tool_msg)

                except json.JSONDecodeError as e:
                    print(f"ERROR: Erro ao decodificar JSON para {fname}: {e}")
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
                    print(f"ERROR: Erro ao executar {fname}: {e}")
                    error_msg = {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(
                            {"error": f"Erro na execução: {str(e)}"}, ensure_ascii=False
                        ),
                    }
                    messages.append(error_msg)

            continue

        for chunk, delay in integrate_with_chat(assistant_content):
            if not chunk.strip():
                continue
            chat_container.controls.append(typing)
            page.update()
            await asyncio.sleep(0.3)
            chat_container.controls.remove(typing)

            resp_id = str(uuid.uuid4())
            history_cache.append(
                {
                    "role": "assistant",
                    "content": chunk.strip(),
                    "message_id": resp_id,
                    "timestamp": datetime.now().isoformat(),
                }
            )
            chat_container.controls.append(
                ChatMessage(
                    Message(
                        "Treinador",
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

        # Salva apenas mensagens de user/assistant no Supabase
        try:
            supabase_service.client.table("trainer_qa").upsert(
                {"user_id": user_id, "message": convo_history}, on_conflict="user_id"
            ).execute()
            history_cache[:] = convo_history
            print(f"INFO: Histórico salvo (somente conversas) para {user_id}")
        except Exception as err:
            print(f"ERROR: Falha ao salvar histórico: {err}")

        haptic_feedback.light_impact()
        page.open(ft.SnackBar(ft.Text("Pergunta enviada com sucesso!")))
        page.update()
        last_question_time[0] = current_time

    except Exception as ex:
        print(f"ERROR: ask_question falhou: {ex}")
        import traceback

        print(f"ERROR: Traceback completo: {traceback.format_exc()}")
        haptic_feedback.heavy_impact()
        page.open(ft.SnackBar(ft.Text(f"Erro: {ex}")))
        page.update()

    finally:
        ask_button.disabled = False
        ask_button.icon_color = ft.Colors.BLUE_400
        page.update()