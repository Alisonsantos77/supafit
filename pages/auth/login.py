import flet as ft
import flet_lottie as fl
import os
from time import sleep
import time
from services.supabase import SupabaseService
from utils.alerts import CustomAlertDialog


def LoginPage(page: ft.Page):
    supabase_service = SupabaseService.get_instance(page)
    lottie_url = os.getenv("LOTTIE_LOGIN")

    login_lottie = fl.Lottie(
        src=lottie_url,
        repeat=True,
        animate=True,
        background_loading=True,
        filter_quality=ft.FilterQuality.HIGH,
        fit=ft.ImageFit.CONTAIN,
    )

    email_field = ft.TextField(
        label="Email",
        color=ft.Colors.BLUE_400,
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
        color=ft.Colors.BLUE_400,
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

    def show_loading(message="Carregando..."):
        if hasattr(page, "dialog") and page.dialog and page.dialog.open:
            print("INFO - Login: Diálogo de carregamento já exibido, ignorando")
            return page.dialog

        loading_dialog = ft.AlertDialog(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.ProgressRing(color=ft.Colors.BLUE_400),
                        ft.Text(message, size=16, text_align=ft.TextAlign.CENTER),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                alignment=ft.alignment.center,
                width=200,
                height=100,
            ),
            bgcolor=ft.Colors.TRANSPARENT,
            modal=True,
            disabled=True,
        )
        page.dialog = loading_dialog
        page.open(loading_dialog)
        page.update()
        print(f"INFO - Login: Diálogo de carregamento exibido: {message}")
        return loading_dialog

    def hide_loading(dialog):
        if dialog and dialog.open:
            page.close(dialog)
            page.dialog = None
            page.update()
            print("INFO - Login: Diálogo de carregamento fechado")

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
            bgcolor=ft.Colors.TRANSPARENT,
            modal=True,
        )
        page.dialog = success_dialog
        page.open(success_dialog)
        page.update()
        print("INFO - Login: Diálogo de sucesso exibido")
        sleep(2)
        page.close(success_dialog)
        page.go(route)

    def save_user_data(user_id, email, level=None):
        try:
            page.client_storage.set("supafit.user_id", user_id)
            page.client_storage.set("supafit.email", email)
            if level:
                page.client_storage.set("supafit.level", level)
            print(
                f"INFO - Login: Dados salvos no client_storage: user_id={user_id}, email={email}, level={level}"
            )
        except Exception as ex:
            print(f"ERROR - Login: Erro ao salvar dados no client_storage: {str(ex)}")

    last_event_time = [0]  # Variável para debounce

    def login(e):
        nonlocal last_event_time
        current_time = time.time()
        if current_time - last_event_time[0] < 0.5:
            print("INFO - Login: Clique ignorado por debounce (menos de 500ms)")
            return
        last_event_time[0] = current_time

        email = email_field.value.strip()
        password = password_field.value.strip()

        if not email or not password:
            status_text.value = "Preencha email e senha!"
            page.open(ft.SnackBar(ft.Text("Preencha email e senha!")))
            page.update()
            print("WARNING - Login: Tentativa de login com campos vazios")
            return

        loading_dialog = show_loading("Fazendo login...")

        try:
            response = supabase_service.login(email, password)

            if response and response.user:
                print(f"INFO - Login: Login bem-sucedido para o email: {email}")
                profile_response = supabase_service.get_profile(response.user.id)
                profile_exists = bool(
                    profile_response.data and len(profile_response.data) > 0
                )
                print(
                    f"INFO - Login: Verificando perfil para user_id: {response.user.id}, perfil {'encontrado' if profile_exists else 'não encontrado'}."
                )
                level = (
                    profile_response.data[0].get("level", "iniciante")
                    if profile_exists
                    else None
                )
                save_user_data(response.user.id, response.user.email, level)

                hide_loading(loading_dialog)

                if not profile_exists:
                    print(
                        f"INFO - Login: Perfil não encontrado, redirecionando para /create_profile."
                    )
                    show_success_and_redirect(
                        "/create_profile", "Login realizado! Vamos criar seu perfil."
                    )
                else:
                    print(
                        f"INFO - Login: Perfil encontrado, redirecionando para /home."
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
            page.open(ft.SnackBar(ft.Text(f"Erro ao fazer login: {error_message}")))
            page.update()
            print(f"ERROR - Login: Erro ao fazer login: {str(ex)}")

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
                    ft.Text(
                        "Acesse sua conta",
                        size=28,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    email_field,
                    password_field,
                    status_text,
                    login_button,
                    register_row,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        columns=12,
    )

    page.update()

    return layout_login
