import flet as ft
import flet_lottie as fl
import os
from time import sleep
from services.services import SupabaseService
from utils.notification import send_notification
import logging

# Configurar logger
logger = logging.getLogger("supafit.login")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


def LoginPage(page: ft.Page):
    supabase_service = SupabaseService()
    lottie_url = os.getenv("LOTTIE_LOGIN")

    login_lottie = fl.Lottie(
        src=lottie_url,
        width=400,
        height=400,
        repeat=True,
        animate=True,
        background_loading=True,
        filter_quality=ft.FilterQuality.HIGH,
        fit=ft.ImageFit.CONTAIN,
    )

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
    )
    status_text = ft.Text(
        "",
        color=ft.Colors.RED,
        size=14,
        italic=True,
    )

    login_button = ft.ElevatedButton(
        "Entrar",
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
    )

    register_row = ft.Row(
        [
            ft.Text(
                "Ainda não possui uma conta?", size=14, color=ft.Colors.BLUE_GREY_600
            ),
            ft.TextButton(
                "Registre aqui",
                style=ft.ButtonStyle(
                    color={
                        ft.ControlState.HOVERED: ft.Colors.BLUE_400,
                        ft.ControlState.DEFAULT: ft.Colors.BLUE_700,
                    },
                ),
                on_click=lambda _: page.go("/register"),
            ),
        ],
        spacing=5,
        alignment=ft.MainAxisAlignment.CENTER,
    )

    activate_row = ft.Row(
        [
            ft.Text(
                "Já tem conta, mas não ativou?", size=14, color=ft.Colors.BLUE_GREY_600
            ),
            ft.TextButton(
                "Ative aqui",
                style=ft.ButtonStyle(
                    color={
                        ft.ControlState.HOVERED: ft.Colors.BLUE_400,
                        ft.ControlState.DEFAULT: ft.Colors.BLUE_700,
                    },
                ),
                on_click=lambda _: page.go("/activation"),
            ),
        ],
        spacing=5,
        alignment=ft.MainAxisAlignment.CENTER,
    )

    def show_loading():
        loading_dialog = ft.AlertDialog(
            content=ft.Container(
                content=ft.ProgressRing(color=ft.Colors.BLUE_400),
                alignment=ft.alignment.center,
            ),
            bgcolor=ft.Colors.TRANSPARENT,
            modal=True,
            disabled=True,
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
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.GREEN_400,
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
        logger.info(f"Diálogo de sucesso exibido: {message}")
        sleep(2)
        page.close(success_dialog)
        page.go(route)
        page.update()

    # Função para salvar dados localmente
    def save_user_data(user_id, email):
        try:
            # Salvar no client_storage
            page.client_storage.set("supafit.user_id", user_id)
            page.client_storage.set("supafit.email", email)
            logger.info(
                f"Dados salvos no client_storage: user_id={user_id}, email={email}"
            )

            # Salvar em arquivo
            app_data_path = os.getenv("FLET_APP_STORAGE_DATA")
            if app_data_path:
                file_path = os.path.join(app_data_path, "user_data.txt")
                with open(file_path, "w") as f:
                    f.write(f"user_id={user_id}\nemail={email}\n")
                logger.info(f"Dados salvos em arquivo: {file_path}")
            else:
                logger.warning("FLET_APP_STORAGE_DATA não definido, arquivo não salvo")
        except Exception as ex:
            logger.error(f"Erro ao salvar dados localmente: {str(ex)}")
            send_notification(page, "Erro", "Falha ao salvar dados localmente.")

    def login(e):
        email = email_field.value.strip()
        password = password_field.value.strip()

        if not email or not password:
            status_text.value = "Preencha email e senha!"
            page.update()
            logger.warning("Tentativa de login com campos vazios")
            send_notification(page, "Erro", "Preencha email e senha!")
            return

        loading_dialog = show_loading()

        try:
            response = supabase_service.login(email, password)

            if response and response.user:
                logger.info(f"Login bem-sucedido para o email: {email}")
                save_user_data(response.user.id, response.user.email)
                hide_loading(loading_dialog)
                send_notification(page, "Sucesso", "Login realizado com sucesso!")
                show_success_and_redirect("/home", "Login realizado!")
            else:
                raise Exception("Resposta inválida do Supabase Auth")
        except Exception as ex:
            hide_loading(loading_dialog)
            status_text.value = "Email ou senha inválidos"
            page.update()
            logger.error(f"Erro no login: {str(ex)}")
            send_notification(page, "Erro", "Email ou senha inválidos")

    login_button.on_click = login

    page.clean()

    layout_login = ft.ResponsiveRow(
        controls=[
            ft.Column(
                col={"sm": 6, "md": 5, "lg": 4},
                controls=[
                    login_lottie,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            ft.Column(
                col={"sm": 6, "md": 5, "lg": 4},
                controls=[
                    ft.Container(height=20),
                    ft.Text(
                        "Login",
                        size=28,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    email_field,
                    password_field,
                    status_text,
                    login_button,
                    ft.Container(height=10),
                    register_row,
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

    page.update()

    return layout_login
