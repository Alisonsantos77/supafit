import flet as ft
from components.components import CustomListTile, AvatarComponent
from services.services import SupabaseService, AnthropicService


def InteractionsPage(page: ft.Page, supabase_service, anthropic):
    user_id = page.client_storage.get("user_id") or "default_user"
    victories_list = ft.ListView(expand=True, spacing=10, padding=10)
    chat_container = ft.ListView(expand=True, spacing=10, padding=10)
    victory_field = ft.TextField(
        label="Compartilhe sua conquista", width=600, multiline=True
    )
    question_field = ft.TextField(label="Faça sua pergunta", width=600, multiline=True)
    share_button = ft.ElevatedButton("Compartilhar", width=150, height=50)
    ask_button = ft.ElevatedButton("Enviar", width=150, height=50)
    status_text = ft.Text("", color=ft.Colors.RED)

    def load_data():
        # Carregar conquistas
        response_victories = (
            supabase_service.client.table("victories").select("*").execute()
        )
        victories_list.controls.clear()
        for victory in response_victories.data:
            victories_list.controls.append(
                CustomListTile(
                    leading=AvatarComponent(victory["user_id"], radius=20),
                    title=ft.Text(f"Usuário: {victory['user_id']}"),
                    subtitle=ft.Text(victory["content"]),
                )
            )

        # Carregar histórico de perguntas
        response_qa = (
            supabase_service.client.table("trainer_qa")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at")
            .execute()
        )
        chat_container.controls.clear()
        chat_container.controls.append(
            ft.Text(
                "Treinador: Olá! Como posso ajudar com seu treino hoje?", italic=True
            )
        )
        for item in response_qa.data:
            chat_container.controls.append(
                ft.Text(f"Você: {item['question']}", weight=ft.FontWeight.BOLD)
            )
            chat_container.controls.append(ft.Text(f"Treinador: {item['answer']}"))

    def share_victory(e):
        content = victory_field.value.strip()
        if not content:
            status_text.value = "Digite uma conquista!"
            page.update()
            return
        supabase_service.client.table("victories").insert(
            {"user_id": user_id, "content": content}
        ).execute()
        victory_field.value = ""
        load_data()
        page.snack_bar = ft.SnackBar(
            ft.Text("Conquista Compartilhada - Sua conquista está na galeria!")
        )
        page.snack_bar.open = True
        page.update()

    def ask_question(e):
        question = question_field.value.strip()
        if not question:
            status_text.value = "Digite uma pergunta!"
            page.update()
            return
        history = (
            supabase_service.client.table("trainer_qa")
            .select("question, answer")
            .eq("user_id", user_id)
            .order("created_at")
            .execute()
            .data
        )
        answer = anthropic.answer_question(question, history)
        supabase_service.client.table("trainer_qa").insert(
            {"user_id": user_id, "question": question, "answer": answer}
        ).execute()
        question_field.value = ""
        load_data()
        page.update()

    share_button.on_click = share_victory
    ask_button.on_click = ask_question
    load_data()

    tabs = ft.Tabs(
        selected_index=0,
        tabs=[
            ft.Tab(
                text="Comunidade",
                content=ft.Column(
                    [
                        victories_list,
                        ft.Row([victory_field, share_button]),
                        status_text,
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=20,
                ),
            ),
            ft.Tab(
                text="Treinador",
                content=ft.Column(
                    [chat_container, ft.Row([question_field, ask_button]), status_text],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=20,
                ),
            ),
        ],
    )

    return ft.Container(
        content=ft.Column([tabs], alignment=ft.MainAxisAlignment.CENTER),
        padding=20,
    )
