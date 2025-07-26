import flet as ft
import flet_lottie as fl
import os
from time import sleep
from services.supabase import SupabaseService
import logging

logger = logging.getLogger("supafit.forgot_password")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


def ForgotPasswordPage(page: ft.Page):
    supabase_service = SupabaseService.get_instance(page)
    lottie_url = os.getenv("LOTTIE_LOGIN")

    forgot_password_lottie = fl.Lottie(
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
        keyboard_type=ft.KeyboardType.EMAIL,
        prefix_icon=ft.Icons.EMAIL,
    )
    status_text = ft.Text("", color=ft.Colors.RED, size=14, italic=True)

    reset_button = ft.ElevatedButton(
        "Enviar Link de Redefinição",
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

    login_row = ft.Row(
        [
            ft.Text("Lembrou sua senha?", size=14, color=ft.Colors.BLUE_GREY_600),
            ft.TextButton(
                "Faça login",
                style=ft.ButtonStyle(
                    color={
                        ft.ControlState.HOVERED: ft.Colors.BLUE_400,
                        ft.ControlState.DEFAULT: ft.Colors.BLUE_700,
                    },
                ),
                on_click=lambda _: page.go("/login"),
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
                            text_align=ft.TextAlign.CENTER,
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

    def reset_password(e):
        email = email_field.value.strip()

        if not email:
            status_text.value = "Preencha o campo de email!"
            page.update()
            logger.warning("Tentativa de redefinição de senha com campo vazio")
            return

        loading_dialog = show_loading()

        try:
            # URL de redirecionamento que vai capturar os tokens e fazer deep link para o app
            redirect_url = "https://alisondeveloper.com/reset-password"
            
            response = supabase_service.client.auth.reset_password_for_email(
                email, 
                {"redirect_to": redirect_url}
            )
            logger.info(
                f"Solicitação de redefinição de senha enviada para o email: {email}"
            )

            hide_loading(loading_dialog)
            show_success_and_redirect(
                "/login", 
                "Link de redefinição enviado! Verifique seu email e clique no link para continuar."
            )
        except Exception as ex:
            hide_loading(loading_dialog)
            error_message = str(ex)
            status_text.value = "Erro ao enviar o link de redefinição"
            page.update()
            logger.error(f"Erro na redefinição de senha: {error_message}")
        finally:
            page.update()

    reset_button.on_click = reset_password

    page.clean()

    layout_forgot_password = ft.ResponsiveRow(
        controls=[
            ft.Column(
                col={"sm": 6, "md": 5, "lg": 4},
                controls=[forgot_password_lottie],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            ft.Column(
                col={"sm": 6, "md": 5, "lg": 4},
                controls=[
                    ft.Container(height=20),
                    ft.Text(
                        "Recuperar Senha",
                        size=28,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        "Digite seu email para receber o link de redefinição de senha.",
                        size=14,
                        color=ft.Colors.BLUE_GREY_600,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(height=10),
                    email_field,
                    status_text,
                    reset_button,
                    ft.Container(height=10),
                    login_row,
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

    return layout_forgot_password