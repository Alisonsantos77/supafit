import flet as ft
import flet_lottie as fl
import re
from time import sleep
from services.services import SupabaseService
from flet.security import encrypt
import os

LOTTIE_REGISTER = os.getenv("LOTTIE_REGISTER")


def RegisterPage(page: ft.Page):
    supabase_service = SupabaseService()
    page.scroll = ft.ScrollMode.HIDDEN
    register_btn = ft.Ref[ft.ElevatedButton]()

    email_field = ft.TextField(
        label="Email",
        width=300,
        border_color=ft.Colors.BLUE,
        focused_border_color=ft.Colors.BLUE,
        border_radius=5,
        keyboard_type="email",
        prefix_icon=ft.Icons.EMAIL,
        disabled=True,
    )
    password_field = ft.TextField(
        label="Senha",
        width=300,
        password=True,
        can_reveal_password=True,
        border_color=ft.Colors.BLUE,
        focused_border_color=ft.Colors.BLUE,
        border_radius=5,
        disabled=True,
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
        border_color=ft.Colors.BLUE,
        focused_border_color=ft.Colors.BLUE_400,
        disabled=True,
    )
    terms_checkbox = ft.Checkbox(
        label="Li e aceito os Termos de Uso e a Política de Privacidade",
        value=False,
    )
    terms_link = ft.TextButton(
        "Leia aqui",
        style=ft.ButtonStyle(color=ft.Colors.BLUE_700),
        on_click=lambda _: page.go("/terms"),
    )
    terms_row = ft.Column(
        [terms_checkbox, terms_link],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=5,
    )
    status_text = ft.Text("", color=ft.Colors.ERROR)

    register_button = ft.ElevatedButton(
        "Registrar",
        bgcolor=ft.Colors.GREY_400,
        color=ft.Colors.WHITE,
        width=300,
        height=50,
        style=ft.ButtonStyle(
            elevation=2,
            shape=ft.RoundedRectangleBorder(radius=5),
        ),
        disabled=True,
        ref=register_btn,
    )
    login_button = ft.TextButton(
        "Já tem uma conta? Faça login",
        style=ft.ButtonStyle(color=ft.Colors.BLUE),
        on_click=lambda e: page.go("/login"),
    )

    def update_form_state(e):
        are_terms_accepted = terms_checkbox.value
        email_field.disabled = not are_terms_accepted
        password_field.disabled = not are_terms_accepted
        level_dropdown.disabled = not are_terms_accepted
        register_btn.current.disabled = not are_terms_accepted
        register_btn.current.bgcolor = (
            ft.Colors.BLUE if are_terms_accepted else ft.Colors.GREY_400
        )
        register_btn.current.color = ft.Colors.WHITE
        page.update()

    terms_checkbox.on_change = update_form_state

    def show_loading():
        loading_dialog = ft.AlertDialog(
            content=ft.Container(
                content=ft.ProgressRing(), alignment=ft.alignment.center
            ),
            bgcolor=ft.Colors.TRANSPARENT,
            modal=True,
            disabled=True,
        )
        page.dialog = loading_dialog
        page.open(loading_dialog)
        page.update()
        return loading_dialog

    def hide_loading(dialog):
        page.close(dialog)
        page.update()

    def show_success_and_redirect(route, message="Sucesso!"):
        success_dialog = ft.AlertDialog(
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(ft.Icons.CHECK_CIRCLE, size=50, color=ft.Colors.GREEN),
                        ft.Text(
                            message,
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.GREEN,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                alignment=ft.alignment.center,
            ),
            bgcolor=ft.Colors.TRANSPARENT,
            modal=True,
            disabled=True,
        )
        page.dialog = success_dialog
        page.open(success_dialog)
        page.update()
        sleep(2)
        page.close(success_dialog)
        page.go(route)

    def register(e):
        if not terms_checkbox.value:
            status_text.value = (
                "Você precisa aceitar os Termos de Uso e a Política de Privacidade!"
            )
            page.update()
            return

        email = email_field.value.strip()
        password = password_field.value.strip()
        level = level_dropdown.value

        if not email or not password or not level:
            status_text.value = "Preencha todos os campos!"
            page.update()
            return

        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, email):
            status_text.value = "Email inválido! Use o formato: nome@dominio.com"
            page.update()
            return

        loading_dialog = show_loading()
        try:
            response = supabase_service.client.auth.sign_up(
                {"email": email, "password": password}
            )
            user_id = response.user.id
            supabase_service.client.table("user_profiles").insert(
                {"user_id": user_id, "level": level}
            ).execute()
            page.client_storage.set("user_id", user_id)
            hide_loading(loading_dialog)
            show_success_and_redirect(
                "/login", "Registro concluído! Verifique seu email para ativar a conta."
            )
        except Exception as ex:
            hide_loading(loading_dialog)
            status_text.value = f"Erro ao registrar: {str(ex)}"
            page.update()

    register_button.on_click = register

    lottie_container = ft.Container(
        content=fl.Lottie(
            src=LOTTIE_REGISTER,
            background_loading=True,
            filter_quality=ft.FilterQuality.HIGH,
            repeat=True,
        ),
        width=400,
        height=350,
        alignment=ft.alignment.center,
    )

    form_container = ft.Column(
        [
            ft.Text("Crie sua Conta", size=24, weight=ft.FontWeight.BOLD),
            email_field,
            password_field,
            level_dropdown,
            terms_row,
            register_button,
            login_button,
            status_text,
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=20,
        width=400,
    )

    top_row = ft.Row(
        [lottie_container, form_container],
        alignment=ft.MainAxisAlignment.CENTER,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=30,
    )

    return ft.Container(
        content=ft.Column(
            [top_row], alignment=ft.MainAxisAlignment.CENTER, scroll=ft.ScrollMode.AUTO
        ),
        padding=20,
    )
