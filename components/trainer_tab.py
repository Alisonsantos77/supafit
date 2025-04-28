import flet as ft
from components.components import AvatarComponent
from services.services import AnthropicService
import httpx


def TrainerTab(page: ft.Page, supabase_service, anthropic: AnthropicService):
    user_id = page.client_storage.get("user_id") or "default_user"

    # Contêiner do chat
    chat_container = ft.ListView(
        spacing=10,
        padding=10,
        auto_scroll=True,
        divider_thickness=1,
    )

    # Campo de pergunta
    question_field = ft.TextField(
        label="Faça sua pergunta",
        multiline=True,
        expand=True,
        border_radius=5,
        text_size=14,
    )

    # Botão de enviar (vai trocar o texto para 'Enviando...' ao clicar)
    ask_button = ft.ElevatedButton(
        "Enviar",
        on_click=None,
        style=ft.ButtonStyle(
            padding=ft.padding.symmetric(horizontal=20, vertical=10),
            shape=ft.RoundedRectangleBorder(radius=5),
        ),
    )

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
            ft.Card(
                content=ft.Container(
                    content=ft.Row(
                        [
                            AvatarComponent(user_id, radius=20, is_trainer=True),
                            ft.Text(
                                "Treinador: Olá! Como posso ajudar com seu treino hoje?",
                                italic=True,
                                size=14,
                                color=ft.Colors.BLACK,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.START,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=ft.padding.all(10),
                    bgcolor=ft.Colors.GREY_200,
                    border_radius=10,
                ),
                elevation=2,
                margin=ft.margin.symmetric(vertical=5, horizontal=10),
            )
        )

        # Histórico de perguntas e respostas
        for item in resp.data:
            # Pergunta do usuário
            chat_container.controls.append(
                ft.Card(
                    content=ft.Container(
                        content=ft.Row(
                            [
                                AvatarComponent(user_id, radius=20, is_trainer=False),
                                ft.Text(
                                    item["question"],
                                    weight=ft.FontWeight.BOLD,
                                    size=14,
                                    color=ft.Colors.WHITE,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.END,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        padding=ft.padding.all(10),
                        bgcolor=ft.Colors.BLUE_700,
                        border_radius=10,
                        margin=ft.margin.only(left=50),
                    ),
                    elevation=2,
                    margin=ft.margin.symmetric(vertical=5, horizontal=10),
                )
            )
            # Resposta do treinador
            chat_container.controls.append(
                ft.Card(
                    content=ft.Container(
                        content=ft.Row(
                            [
                                AvatarComponent(user_id, radius=20, is_trainer=True),
                                ft.Text(
                                    item["answer"],
                                    size=14,
                                    color=ft.Colors.BLACK,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.START,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        padding=ft.padding.all(10),
                        bgcolor=ft.Colors.GREY_200,
                        border_radius=10,
                        margin=ft.margin.only(right=50),
                    ),
                    elevation=2,
                    margin=ft.margin.symmetric(vertical=5, horizontal=10),
                )
            )

        page.update()
        return resp.data

    def ask_question(e):
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

            # Se a resposta vier inválida, tratamos como erro
            if not answer or "desculpe" in answer.lower():
                raise ValueError("Resposta inválida do Anthropic")

            # Salva no Supabase
            supabase_service.table("trainer_qa").insert(
                {"user_id": user_id, "question": question, "answer": answer}
            ).execute()

            # Limpa campo e recarrega chat
            question_field.value = ""
            load_chat()

            # SnackBar de sucesso
            page.open(ft.SnackBar(ft.Text("Pergunta enviada com sucesso!")))

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
            # Restaura o botão
            ask_button.disabled = False
            ask_button.content = ft.Text("Enviar")
            page.update()

    # Atribui o handler ao botão
    ask_button.on_click = ask_question

    # Carrega o chat inicial
    load_chat()

    return ft.Column(
        [
            ft.Text("Chat com o Treinador", size=20, weight=ft.FontWeight.BOLD),
            ft.Container(
                content=chat_container,
                height=page.window.height * 0.5,
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
    )
