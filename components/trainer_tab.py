import flet as ft
from components.components import AvatarComponent
from services.services import AnthropicService
import httpx


def TrainerTab(page: ft.Page, supabase_service, anthropic: AnthropicService):
    user_id = page.client_storage.get("user_id") or "default_user"
    chat_container = ft.ListView(
        spacing=10,
        padding=10,
        auto_scroll=True,
        divider_thickness=1,
    )
    question_field = ft.TextField(
        label="Faça sua pergunta",
        multiline=True,
        expand=True,
        border_radius=5,
        text_size=14,
    )
    ask_button = ft.ElevatedButton(
        "Enviar",
        style=ft.ButtonStyle(
            padding=ft.padding.symmetric(horizontal=20, vertical=10),
            shape=ft.RoundedRectangleBorder(radius=5),
        ),
    )
    status_text = ft.Text("", color=ft.Colors.RED, size=14)

    def load_chat():
        response_qa = (
            supabase_service.table("trainer_qa")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at")
            .execute()
        )
        chat_container.controls.clear()
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
                    alignment=ft.alignment.center_left,
                ),
                elevation=2,
                margin=ft.margin.symmetric(vertical=5, horizontal=10),
            )
        )
        for item in response_qa.data:
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
                        alignment=ft.alignment.center_right,
                        margin=ft.margin.only(left=50),
                    ),
                    elevation=2,
                    margin=ft.margin.symmetric(vertical=5, horizontal=10),
                )
            )
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
                        alignment=ft.alignment.center_left,
                        margin=ft.margin.only(right=50),
                    ),
                    elevation=2,
                    margin=ft.margin.symmetric(vertical=5, horizontal=10),
                )
            )
        page.update()

    def ask_question(e):
        question = question_field.value.strip()
        if not question:
            status_text.value = "Digite uma pergunta!"
            page.update()
            return
        try:
            answer = anthropic.answer_question(question)
            if not answer or "desculpe" in answer.lower():
                raise ValueError("Resposta inválida do Anthropic")
            supabase_service.table("trainer_qa").insert(
                {"user_id": user_id, "question": question, "answer": answer}
            ).execute()
            question_field.value = ""
            load_chat()
            page.snack_bar = ft.SnackBar(content=ft.Text("Pergunta enviada!"))
            page.snack_bar.open = True
        except httpx.HTTPStatusError as ex:
            error_detail = ex.response.json() if ex.response else str(ex)
            status_text.value = f"Erro na API Anthropic: {error_detail}"
            page.update()
            return
        except Exception as ex:
            status_text.value = f"Erro ao obter resposta: {str(ex)}"
            page.update()
            return
        page.update()

    ask_button.on_click = ask_question
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
            status_text,
        ],
        spacing=15,
        alignment=ft.MainAxisAlignment.START,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )
