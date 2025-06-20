import flet as ft
import flet_lottie as fl
import os
from time import sleep
from services.supabase import SupabaseService
from utils.logger import get_logger

logger = get_logger("supabafit.login")


def LoginPage(page: ft.Page):
    supabase_service = SupabaseService(page)
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

    forgot_password_row = ft.Row(
        [
            ft.Text("Esqueceu sua senha?", size=14, color=ft.Colors.BLUE_GREY_600),
            ft.TextButton(
                "Recuperar",
                style=ft.ButtonStyle(
                    color={
                        ft.ControlState.HOVERED: ft.Colors.BLUE_400,
                        ft.ControlState.DEFAULT: ft.Colors.BLUE_700,
                    },
                ),
                on_click=lambda _: page.go("/forgot_password"),
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
        logger.info(f"Redirecionando para a rota: {route}")

    def save_user_data(user_id, email, level=None):
        try:
            # Salvar no client_storage
            page.client_storage.set("supafit.user_id", user_id)
            page.client_storage.set("supafit.email", email)
            if level:
                page.client_storage.set("supafit.level", level)
            logger.info(
                f"Dados salvos no client_storage: user_id={user_id}, email={email}, level={level}"
            )

            # Salvar em arquivo user_data.txt
            app_data_path = os.getenv("FLET_APP_STORAGE_DATA")
            if app_data_path:
                file_path = os.path.join(app_data_path, "user_data.txt")
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, "w") as f:
                    content = f"user_id={user_id}\nemail={email}\n"
                    if level:
                        content += f"level={level}\n"
                    f.write(content)
                logger.info(f"Dados salvos em arquivo: {file_path}")
            else:
                logger.warning("FLET_APP_STORAGE_DATA não definido, arquivo não salvo")
        except Exception as ex:
            logger.error(f"Erro ao salvar dados localmente: {str(ex)}")

    def login(e):
        email = email_field.value.strip()
        password = password_field.value.strip()

        if not email or not password:
            status_text.value = "Preencha email e senha!"
            page.update()
            logger.warning("Tentativa de login com campos vazios")
            return

        loading_dialog = show_loading()

        try:
            # Limpa dados residuais antes do login
            page.client_storage.clear()
            app_data_path = os.getenv("FLET_APP_STORAGE_DATA")
            if app_data_path:
                for file in ["auth_data.txt", "user_data.txt"]:
                    file_path = os.path.join(app_data_path, file)
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        logger.info(f"Arquivo {file} removido antes do login.")

            response = supabase_service.login(email, password)

            if response and response.user:
                logger.info(f"Login bem-sucedido para o email: {email}")
                # Validar user_id contra Supabase Auth
                supabase_service.validate_user_id(response.user.id)

                # Verificar se o perfil já existe
                profile_response = supabase_service.get_profile(response.user.id)
                profile_exists = bool(
                    profile_response.data and len(profile_response.data) > 0
                )
                logger.info(
                    f"Verificando perfil para user_id: {response.user.id}, perfil {'encontrado' if profile_exists else 'não encontrado'}."
                )

                # Define nível padrão ou do perfil
                level = (
                    profile_response.data[0].get("level", "iniciante")
                    if profile_exists
                    else None
                )
                # Salvar dados localmente
                save_user_data(response.user.id, response.user.email, level)

                hide_loading(loading_dialog)

                if not profile_exists:
                    logger.info(
                        f"Perfil não encontrado para user_id: {response.user.id}. Redirecionando para /create_profile."
                    )
                    show_success_and_redirect(
                        "/create_profile", "Login realizado! Vamos criar seu perfil."
                    )
                else:
                    logger.info(
                        f"Perfil encontrado para user_id: {response.user.id}. Redirecionando para /home."
                    )
                    show_success_and_redirect("/home", "Login realizado!")
            else:
                raise Exception("Resposta inválida do Supabase Auth")
        except Exception as ex:
            hide_loading(loading_dialog)
            error_message = (
                "Por favor, confirme seu email antes de fazer login."
                if "Email not confirmed" in str(ex)
                else str(ex)
            )
            status_text.value = error_message
            page.update()
            logger.error(f"Erro no login: {str(ex)}")

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
                    forgot_password_row,
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
