import json
import flet as ft
import flet_lottie as fl
import re
import os
from time import sleep
from services.supabase import SupabaseService
from utils.logger import get_logger

logger = get_logger("supabafit.register")

LOTTIE_REGISTER = os.getenv("LOTTIE_REGISTER")


def RegisterPage(page: ft.Page):
    supabase_service = SupabaseService.get_instance(page)
    page.scroll = ft.ScrollMode.AUTO
    register_btn = ft.Ref[ft.ElevatedButton]()

    email_field = ft.TextField(
        label="Email",
        width=320,
        border="underline",
        filled=True,
        bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.BLUE_GREY),
        border_color=ft.Colors.BLUE_600,
        focused_border_color=ft.Colors.BLUE_400,
        cursor_color=ft.Colors.BLUE_400,
        text_size=16,
        keyboard_type=ft.KeyboardType.EMAIL,
        prefix_icon=ft.Icons.EMAIL,
        disabled=True,
    )
    password_field = ft.TextField(
        label="Senha",
        width=320,
        border="underline",
        filled=True,
        bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.BLUE_GREY),
        border_color=ft.Colors.BLUE_600,
        focused_border_color=ft.Colors.BLUE_400,
        cursor_color=ft.Colors.BLUE_400,
        text_size=16,
        password=True,
        can_reveal_password=True,
        disabled=True,
    )
    level_dropdown = ft.Dropdown(
        label="Nível de Fitness",
        width=320,
        options=[
            ft.dropdown.Option("iniciante"),
            ft.dropdown.Option("intermediário"),
            ft.dropdown.Option("avançado"),
        ],
        value="iniciante",
        border_color=ft.Colors.BLUE_600,
        focused_border_color=ft.Colors.BLUE_400,
        text_size=16,
        disabled=True,
    )
    terms_checkbox = ft.Checkbox(
        label="Li e aceito os Termos de Uso e a Política de Privacidade",
        value=False,
    )
    terms_link = ft.TextButton(
        "Leia aqui",
        style=ft.ButtonStyle(
            color={
                ft.ControlState.HOVERED: ft.Colors.BLUE_400,
                ft.ControlState.DEFAULT: ft.Colors.BLUE_700,
            }
        ),
        on_click=lambda _: page.go("/terms"),
    )
    status_text = ft.Text("", color=ft.Colors.RED, size=14, italic=True)

    register_button = ft.ElevatedButton(
        "Registrar",
        style=ft.ButtonStyle(
            bgcolor={
                ft.ControlState.HOVERED: ft.Colors.BLUE_500,
                ft.ControlState.DEFAULT: ft.Colors.BLUE_700,
            },
            color=ft.Colors.WHITE,
            elevation={"pressed": 2, "": 5},
            animation_duration=300,
            shape=ft.RoundedRectangleBorder(radius=5),
        ),
        width=320,
        height=50,
        disabled=True,
        ref=register_btn,
    )
    login_row = ft.Row(
        [
            ft.Text("Já tem uma conta?", size=14, color=ft.Colors.BLUE_GREY_600),
            ft.TextButton(
                "Faça login",
                style=ft.ButtonStyle(
                    color={
                        ft.ControlState.HOVERED: ft.Colors.BLUE_400,
                        ft.ControlState.DEFAULT: ft.Colors.BLUE_700,
                    }
                ),
                on_click=lambda e: page.go("/login"),
            ),
        ],
        spacing=5,
        alignment=ft.MainAxisAlignment.CENTER,
    )

    def update_form_state(e):
        are_terms_accepted = terms_checkbox.value
        email_field.disabled = not are_terms_accepted
        password_field.disabled = not are_terms_accepted
        level_dropdown.disabled = not are_terms_accepted
        register_btn.current.disabled = not are_terms_accepted
        register_btn.current.bgcolor = (
            ft.Colors.BLUE_700 if are_terms_accepted else ft.Colors.GREY_400
        )
        page.update()
        logger.info(
            f"Estado do formulário atualizado: Termos aceitos = {are_terms_accepted}"
        )

    terms_checkbox.on_change = update_form_state

    def show_loading():
        loading_dialog = ft.AlertDialog(
            content=ft.Container(
                content=ft.ProgressRing(color=ft.Colors.BLUE_400, width=50, height=50),
                alignment=ft.alignment.center,
                padding=20,
            ),
            bgcolor=ft.Colors.with_opacity(0.8, ft.Colors.GREY_900),
            modal=True,
            shape=ft.RoundedRectangleBorder(radius=10),
        )
        page.dialog = loading_dialog
        page.open(loading_dialog)
        page.update()
        logger.info("Diálogo de carregamento exibido")
        return loading_dialog

    def hide_loading(dialog):
        page.close(dialog)
        page.update()
        logger.info("Diálogo de carregamento fechado")

    def show_success_and_redirect(route, message="Sucesso!"):
        success_dialog = ft.AlertDialog(
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(
                            ft.Icons.CHECK_CIRCLE, size=50, color=ft.Colors.GREEN_400
                        ),
                        ft.Text(
                            message,
                            size=16,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.WHITE,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                ),
                alignment=ft.alignment.center,
                padding=20,
            ),
            bgcolor=ft.Colors.with_opacity(0.8, ft.Colors.GREY_900),
            modal=True,
            shape=ft.RoundedRectangleBorder(radius=10),
        )
        page.dialog = success_dialog
        page.open(success_dialog)
        page.update()
        logger.info(f"Diálogo de sucesso exibido: {message}")
        sleep(2)
        page.close(success_dialog)
        page.go(route)

    def save_user_data(user_id, email, level):
        try:
            page.client_storage.set("supafit.user_id", user_id)
            page.client_storage.set("supafit.email", email)
            page.client_storage.set("supafit.level", level)
            logger.info(
                f"Dados salvos no client_storage: user_id={user_id}, email={email}, level={level}"
            )
        except Exception as ex:
            logger.error(f"Erro ao salvar dados no client_storage: {str(ex)}")

    def register(e):
        if not terms_checkbox.value:
            status_text.value = (
                "Você precisa aceitar os Termos de Uso e a Política de Privacidade!"
            )
            page.update()
            logger.warning("Tentativa de registro sem aceitar os termos")
            return

        email = email_field.value.strip()
        password = password_field.value.strip()
        level = level_dropdown.value

        if not email or not password or not level:
            status_text.value = "Preencha todos os campos!"
            page.update()
            logger.warning("Tentativa de registro com campos vazios")
            return

        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, email):
            status_text.value = "Email inválido! Use o formato: nome@dominio.com"
            page.update()
            logger.warning(f"Tentativa de registro com email inválido: {email}")
            return

        if len(password) < 6:
            status_text.value = "A senha deve ter pelo menos 6 caracteres!"
            page.update()
            logger.warning("Tentativa de registro com senha curta")
            return

        loading_dialog = show_loading()
        try:
            logger.info(f"Iniciando registro para o email: {email}")
            response = supabase_service.client.auth.sign_up(
                {"email": email, "password": password}
            )

            if response.user is None:
                raise Exception("Nenhum usuário retornado pelo Supabase Auth")

            # Salvar dados localmente
            save_user_data(response.user.id, response.user.email, level)

            hide_loading(loading_dialog)
            show_success_and_redirect(
                "/login", "Registro concluído! Verifique seu email para ativar a conta."
            )

        except Exception as ex:
            hide_loading(loading_dialog)
            status_text.value = f"Erro ao registrar: {str(ex)}"
            page.update()
            logger.error(f"Erro no registro: {str(ex)}")

    register_button.on_click = register

    lottie_container = ft.Container(
        content=fl.Lottie(
            src=LOTTIE_REGISTER,
            background_loading=True,
            filter_quality=ft.FilterQuality.HIGH,
            repeat=True,
            fit=ft.ImageFit.CONTAIN,
        ),
        width=400,
        height=400,
    )

    layout_register = ft.ResponsiveRow(
        controls=[
            ft.Column(
                col={"sm": 6, "md": 5, "lg": 4},
                controls=[lottie_container],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            ft.Column(
                col={"sm": 6, "md": 5, "lg": 4},
                controls=[
                    ft.Container(height=20),
                    ft.Text(
                        "Crie sua Conta",
                        size=28,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    email_field,
                    password_field,
                    level_dropdown,
                    ft.Column(
                        [terms_checkbox, terms_link],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    register_button,
                    login_row,
                    status_text,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=15,
            ),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        columns=12,
    )

    return layout_register
