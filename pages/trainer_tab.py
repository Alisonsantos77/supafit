import flet as ft
from components.components import AvatarComponent
from services.services import AnthropicService
import httpx
import time
from datetime import datetime
from utils.notification import send_notification

# Classe para representar uma mensagem
class Message:
    def __init__(
        self, user_name: str, text: str, user_type: str = "user", created_at: str = None
    ):
        self.user_name = user_name
        self.text = text
        self.user_type = user_type
        self.created_at = created_at


# Classe para renderizar uma mensagem no chat
class ChatMessage(ft.Row):
    def __init__(self, message: Message, page: ft.Page):
        super().__init__()
        self.vertical_alignment = ft.CrossAxisAlignment.START

        # Define o avatar com base no tipo de usuário
        if message.user_type == "trainer":
            avatar = AvatarComponent(message.user_name, radius=20, is_trainer=True)
        else:
            avatar = AvatarComponent(message.user_name, radius=20, is_trainer=False)

        # Formata a data/hora da mensagem
        time_str = ""
        if message.created_at:
            try:
                time_str = datetime.fromisoformat(
                    message.created_at.replace("Z", "+00:00")
                ).strftime("%H:%M")
            except:
                time_str = "Horário desconhecido"

        # Define as cores e o alinhamento com base no tipo de usuário
        if message.user_type == "trainer":
            bgcolor = ft.Colors.GREEN
            text_color = ft.Colors.WHITE
            time_color = ft.Colors.WHITE54
            alignment = ft.MainAxisAlignment.START
            margin = ft.margin.only(right=20)
        else:
            bgcolor = ft.Colors.BLUE_700
            text_color = ft.Colors.WHITE
            time_color = ft.Colors.WHITE54
            alignment = ft.MainAxisAlignment.END
            margin = ft.margin.only(left=20)

        # Ajusta a largura do texto para ser responsiva (70% da largura da tela, com mínimo de 200 e máximo de 400)
        message_width = (
            min(max(page.window.width * 0.7, 200), 400) if page.window.width else 300
        )

        self.controls = [
            ft.Container(
                content=ft.Row(
                    [
                        avatar,
                        ft.Column(
                            [
                                ft.Text(
                                    message.user_name,
                                    weight=ft.FontWeight.BOLD,
                                    color=text_color,
                                ),
                                ft.Text(
                                    message.text,
                                    selectable=True,
                                    width=message_width, 
                                    no_wrap=False,  
                                    color=text_color,
                                ),
                                ft.Text(
                                    time_str,
                                    size=10,
                                    color=time_color,
                                    text_align=ft.TextAlign.RIGHT,
                                ),
                            ],
                            tight=True,
                            spacing=5,
                        ),
                    ],
                    alignment=alignment,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                ),
                bgcolor=bgcolor,
                padding=10,
                border_radius=10,
                margin=margin,
            ),
        ]


def TrainerTab(page: ft.Page, supabase_service, anthropic: AnthropicService):
    page.padding = 10

    user_id = page.client_storage.get("user_id") or "default_user"

    # Contêiner do chat
    chat_container = ft.ListView(
        expand=False,
        spacing=10,
        padding=10,
        auto_scroll=True,
        height=(
            page.window.height * 0.6 if page.window.height else 400
        ),
    )

    # Campo de pergunta
    question_field = ft.TextField(
        label="Faça sua pergunta",
        multiline=True,
        expand=True,
        border_radius=5,
        text_size=14,
        min_lines=1,
        max_lines=5,
        filled=True,
        shift_enter=True,
        on_submit=lambda e: ask_question(e),
        bgcolor=ft.Colors.GREY_800,
        color=ft.Colors.WHITE,
        border_color=ft.Colors.GREY_600,
    )

    # Botão de enviar
    ask_button = ft.ElevatedButton(
        "Enviar",
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
    )

    # Controle de cooldown
    last_question_time = 0
    COOLDOWN_SECONDS = 2  # Delay de 2 segundos entre perguntas

    def load_chat():
        resp = (
            supabase_service.table("trainer_qa")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at")
            .execute()
        )
        chat_container.controls.clear()

        # Mensagem inicial do treinador
        chat_container.controls.append(
            ChatMessage(
                Message(
                    user_name="Treinador",
                    text="Olá! Como posso ajudar com seu treino hoje? 😄",
                    user_type="trainer",
                ),
                page,
            )
        )

        # Histórico de perguntas e respostas
        for item in resp.data:
            # Pergunta do usuário
            chat_container.controls.append(
                ChatMessage(
                    Message(
                        user_name="Você",
                        text=item["question"],
                        user_type="user",
                        created_at=item["created_at"],
                    ),
                    page,
                )
            )
            # Resposta do treinador
            chat_container.controls.append(
                ChatMessage(
                    Message(
                        user_name="Treinador",
                        text=item["answer"],
                        user_type="trainer",
                        created_at=item["created_at"],
                    ),
                    page,
                )
            )

        page.update()
        return resp.data

    def clear_chat(e):
        def confirm_clear(e):
            if e.control.text == "Sim":
                try:
                    supabase_service.table("trainer_qa").delete().eq(
                        "user_id", user_id
                    ).execute()
                    load_chat()
                    page.open(ft.SnackBar(ft.Text("Chat limpo com sucesso!")))
                except Exception as ex:
                    page.open(
                        ft.SnackBar(
                            ft.Text(f"Erro ao limpar chat: {str(ex)}"),
                            bgcolor=ft.Colors.RED_700,
                        )
                    )
            page.close(confirm_dialog)

        confirm_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Limpar Chat"),
            content=ft.Text(
                "Tem certeza que deseja limpar todo o histórico de mensagens?"
            ),
            actions=[
                ft.TextButton("Sim", on_click=confirm_clear),
                ft.TextButton("Não", on_click=confirm_clear),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.open(confirm_dialog)

    def ask_question(e):
        nonlocal last_question_time

        # Verifica o cooldown
        current_time = time.time()
        if current_time - last_question_time < COOLDOWN_SECONDS:
            page.open(
                ft.SnackBar(
                    ft.Text(
                        "Calma aí! Espere um pouco antes de mandar outra pergunta. 😅"
                    ),
                    bgcolor=ft.Colors.ORANGE_700,
                )
            )
            return

        question = question_field.value.strip()
        if not question:
            page.open(ft.SnackBar(ft.Text("Digite uma pergunta!")))
            return

        # Desabilita o botão e mostra loader
        ask_button.disabled = True
        ask_button.content = ft.Row(
            [ft.ProgressRing(width=16, height=16), ft.Text(" Enviando...")],
            alignment=ft.MainAxisAlignment.CENTER,
        )
        page.update()

        try:
            history = load_chat()
            answer = anthropic.answer_question(question, history)

            if not answer or "desculpe" in answer.lower():
                raise ValueError("Resposta inválida do Anthropic")

            supabase_service.table("trainer_qa").insert(
                {
                    "user_id": user_id,
                    "question": question,
                    "answer": answer,
                    "created_at": datetime.now().isoformat(),
                }
            ).execute()

            question_field.value = ""
            load_chat()
            send_notification(
                page, "Resposta do Treinador", "O treinador respondeu sua pergunta!"
            )
            page.open(ft.SnackBar(ft.Text("Pergunta enviada com sucesso!")))

            last_question_time = time.time()

        except httpx.HTTPStatusError as ex:
            detail = ex.response.text or str(ex)
            page.open(
                ft.SnackBar(
                    ft.Text(f"Erro na API Anthropic: {detail}"),
                    bgcolor=ft.Colors.RED_700,
                )
            )
        except Exception as ex:
            page.open(
                ft.SnackBar(
                    ft.Text(f"Erro ao obter resposta: {str(ex)}"),
                    bgcolor=ft.Colors.RED_700,
                )
            )
        finally:
            ask_button.disabled = False
            ask_button.content = ft.Text("Enviar")
            page.update()

    ask_button.on_click = ask_question
    clear_button.on_click = clear_chat

    load_chat()

    return ft.Column(
        [
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
