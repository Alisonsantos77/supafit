import flet as ft
from services.supabase_service import SupabaseService


def LoginPage(page: ft.Page):
    supabase_service = SupabaseService()
    email_field = ft.TextField(label="Email", width=300)
    password_field = ft.TextField(label="Senha", password=True, width=300)
    error_message = ft.Text("", color=ft.Colors.RED)

    def login(e):
        email = email_field.value
        password = password_field.value
        response = supabase_service.login(email, password)
        if response and response.user:
            page.client_storage.set("user_id", response.user.id)
            page.go("/")
        else:
            error_message.value = "Email ou senha inválidos"
            page.update()

    return ft.Container(
        content=ft.Column(
            [
                ft.Text("Login", size=24, weight=ft.FontWeight.BOLD),
                email_field,
                password_field,
                error_message,
                ft.ElevatedButton("Entrar", on_click=login),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        alignment=ft.alignment.center,
        padding=20,
    )
