import flet as ft
from services.supabase_service import SupabaseService


def AskTrainerPage(page: ft.Page, supabase_service, anthropic):
    user_id = page.client_storage.get("user_id")
    chat_container = ft.ListView(expand=True, spacing=10, padding=10)
    question_field = ft.TextField(label="Faça sua pergunta", width=600, multiline=True)
    ask_button = ft.ElevatedButton("Enviar", width=150, height=50)
    status_text = ft.Text("", color=ft.Colors.RED)

    def load_history():
        response = (
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
        for item in response.data:
            chat_container.controls.append(
                ft.Text(f"Você: {item['question']}", weight=ft.FontWeight.BOLD)
            )
            chat_container.controls.append(ft.Text(f"Treinador: {item['answer']}"))
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
        load_history()

    ask_button.on_click = ask_question
    load_history()

    return ft.Container(
        content=ft.Column(
            [chat_container, ft.Row([question_field, ask_button]), status_text],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20,
        ),
        padding=20,
    )
