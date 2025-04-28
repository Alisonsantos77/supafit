import flet as ft
from services.supabase_service import SupabaseService


def RegisterPage(page: ft.Page):
    supabase_service = SupabaseService()
    email_field = ft.TextField(label="Email", width=300, keyboard_type="email")
    password_field = ft.TextField(
        label="Senha", width=300, password=True, can_reveal_password=True
    )
    level_dropdown = ft.Dropdown(
        label="Nível de Fitness",
        options=[
            ft.dropdown.Option("iniciante"),
            ft.dropdown.Option("intermediário"),
            ft.dropdown.Option("avançado"),
        ],
        value="iniciante",
        width=300,
    )
    status_text = ft.Text("", color=ft.Colors.RED)
    register_button = ft.ElevatedButton("Registrar", width=300, height=50)
    login_button = ft.TextButton(
        "Já tem uma conta? Faça login", on_click=lambda e: page.go("/login")
    )

    def register(e):
        email = email_field.value.strip()
        password = password_field.value.strip()
        level = level_dropdown.value
        if not email or not password or not level:
            status_text.value = "Preencha todos os campos!"
            page.update()
            return
        try:
            response = supabase_service.client.auth.sign_up(
                {"email": email, "password": password}
            )
            user_id = response.user.id
            supabase_service.client.table("user_profiles").insert(
                {"user_id": user_id, "level": level}
            ).execute()
            page.client_storage.set("user_id", user_id)
            status_text.value = "Registro concluído! Verifique seu email."
            page.update()
        except Exception as e:
            status_text.value = f"Erro ao registrar: {str(e)}"
            page.update()

    register_button.on_click = register

    return ft.Container(
        content=ft.Column(
            [email_field, password_field, level_dropdown, status_text, register_button, login_button],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20,
        ),
        padding=20,
    )
