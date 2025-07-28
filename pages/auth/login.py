import flet as ft
import flet_lottie as fl
import os
from time import sleep
import time
import threading
from services.supabase import SupabaseService
from utils.logger import get_logger
from pages.auth.utils.validators import Validators
from pages.auth.utils.animations import (
    AnimationPresets,
    AnimationHelpers,
    SnackbarAnimations,
    DialogAnimations,
)

logger = get_logger("supafit.login")


def LoginPage(page: ft.Page):
    supabase_service = SupabaseService.get_instance(page)
    lottie_url = os.getenv("LOTTIE_LOGIN")
    page.scroll = ft.ScrollMode.AUTO

    login_btn = ft.Ref[ft.ElevatedButton]()
    form_container = ft.Ref[ft.Container]()

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
        keyboard_type=ft.KeyboardType.EMAIL,
        prefix_icon=ft.Icons.EMAIL,
        animate_opacity=AnimationPresets.fade_in(),
        disabled=False,
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
        prefix_icon=ft.Icons.LOCK,
        animate_opacity=AnimationPresets.fade_in(),
        disabled=False,
    )

    info_container = ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Image(
                            src="mascote_supafit/perfil.png",
                            width=28,
                            height=28,
                            fit=ft.ImageFit.CONTAIN,
                            border_radius=50,
                            tooltip="Sou o Buddy! 😎",
                            error_content=ft.Icon(ft.Icons.PERSON),
                        ),
                        ft.Text(
                            "Antes de treinar, você precisa ativar sua conta!",
                            size=13,
                            weight=ft.FontWeight.W_600,
                            color=ft.Colors.BLUE_700,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=10,
                ),
                ft.Text(
                    spans=[
                        ft.TextSpan("1. ", ft.TextStyle(weight=ft.FontWeight.BOLD)),
                        ft.TextSpan("Acesse seu "),
                        ft.TextSpan("e-mail", ft.TextStyle(weight=ft.FontWeight.W_600)),
                        ft.TextSpan(" (inclusive a pasta "),
                        ft.TextSpan("spam", ft.TextStyle(italic=True)),
                        ft.TextSpan(")."),
                    ],
                    size=12,
                    text_align=ft.TextAlign.CENTER,
                    color=ft.Colors.BLUE_GREY_700,
                ),
                ft.Text(
                    spans=[
                        ft.TextSpan("2. ", ft.TextStyle(weight=ft.FontWeight.BOLD)),
                        ft.TextSpan(
                            "Clique no link de ativação, você será redirecionado para "
                        ),
                        ft.TextSpan(
                            "alisondeveloper.com",
                            ft.TextStyle(italic=True, color=ft.Colors.BLUE),
                        ),
                        ft.TextSpan("."),
                    ],
                    size=12,
                    text_align=ft.TextAlign.CENTER,
                    color=ft.Colors.BLUE_GREY_700,
                ),
                ft.Text(
                    spans=[
                        ft.TextSpan("3. ", ft.TextStyle(weight=ft.FontWeight.BOLD)),
                        ft.TextSpan("Volte ao SupaFit e faça login normalmente!"),
                    ],
                    size=12,
                    text_align=ft.TextAlign.CENTER,
                    color=ft.Colors.BLUE_GREY_700,
                ),
            ],
            spacing=6,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.Padding(15, 12, 15, 12),
        margin=ft.Margin(0, 10, 0, 10),
        bgcolor=ft.Colors.with_opacity(0.06, ft.Colors.BLUE_100),
        border_radius=10,
        animate_opacity=AnimationPresets.fade_in(),
        visible=False,
    )
    login_button = ft.ElevatedButton(
        "Entrar",
        style=ft.ButtonStyle(
            bgcolor={
                ft.ControlState.HOVERED: ft.Colors.BLUE_500,
                ft.ControlState.DEFAULT: ft.Colors.BLUE_700,
                ft.ControlState.DISABLED: ft.Colors.GREY_400,
            },
            color={
                ft.ControlState.DEFAULT: ft.Colors.WHITE,
                ft.ControlState.DISABLED: ft.Colors.GREY_600,
            },
            elevation={"pressed": 2, "": 5},
            animation_duration=AnimationPresets.NORMAL,
            shape=ft.RoundedRectangleBorder(radius=5),
        ),
        width=320,
        height=50,
        ref=login_btn,
        animate_opacity=AnimationPresets.fade_in(),
        disabled=False,
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
        animate_opacity=AnimationPresets.fade_in(),
    )

    def validate_form_client_side():
        email = email_field.value.strip() if email_field.value else ""
        password = password_field.value.strip() if password_field.value else ""

        if not email or not password:
            error_msg = "Preencha email e senha!"
            if not email:
                AnimationHelpers.animate_form_error(email_field, page)
            if not password:
                AnimationHelpers.animate_form_error(password_field, page)

            SnackbarAnimations.show_animated_snackbar(
                page, error_msg, "red", icon=ft.Icons.ERROR
            )
            return False

        email_validation = Validators.validate_email(email)
        if not email_validation.is_valid:
            AnimationHelpers.animate_form_error(email_field, page)
            SnackbarAnimations.show_animated_snackbar(
                page, email_validation.message, "red", icon=ft.Icons.ERROR
            )
            return False

        return True

    def save_user_data(user_id, email, level=None):
        try:
            page.client_storage.set("supafit.user_id", user_id)
            page.client_storage.set("supafit.email", email)
            if level:
                page.client_storage.set("supafit.level", level)
            logger.info(
                f"Dados salvos: user_id={user_id}, email={email}, level={level}"
            )
        except Exception as ex:
            logger.error(f"Erro ao salvar dados: {str(ex)}")

    def show_account_not_activated_info():
        info_container.visible = True
        info_container.animate_opacity = AnimationPresets.fade_in(AnimationPresets.SLOW)
        page.update()

    last_event_time = [0]

    def login(e):
        nonlocal last_event_time
        current_time = time.time()
        if current_time - last_event_time[0] < 0.5:
            logger.info("Clique ignorado por debounce")
            return
        last_event_time[0] = current_time

        AnimationHelpers.animate_button_click(login_button, page)

        if not validate_form_client_side():
            return

        email = email_field.value.strip()
        password = password_field.value.strip()

        loading_dialog = DialogAnimations.create_loading_dialog("Fazendo login...")
        DialogAnimations.show_dialog_with_animation(page, loading_dialog)

        try:
            logger.info(f"Tentativa de login para: {email}")
            response = supabase_service.login(email, password)

            if response and response.user:
                logger.info(f"Login bem-sucedido para: {email}")

                profile_response = supabase_service.get_profile(response.user.id)
                profile_exists = bool(
                    profile_response.data and len(profile_response.data) > 0
                )

                level = (
                    profile_response.data[0].get("level", "iniciante")
                    if profile_exists
                    else None
                )

                save_user_data(response.user.id, response.user.email, level)
                page.close(loading_dialog)

                if not profile_exists:
                    success_dialog = DialogAnimations.create_success_dialog(
                        "Login realizado!", "Vamos criar seu perfil completo."
                    )
                    DialogAnimations.show_dialog_with_animation(page, success_dialog)

                    def redirect_to_profile():
                        sleep(2)
                        page.close(success_dialog)
                        page.go("/create_profile")

                    threading.Thread(target=redirect_to_profile, daemon=True).start()
                else:
                    success_dialog = DialogAnimations.create_success_dialog(
                        "Login realizado!", "Bem-vindo de volta!"
                    )
                    DialogAnimations.show_dialog_with_animation(page, success_dialog)

                    def redirect_to_home():
                        sleep(2)
                        page.close(success_dialog)
                        page.go("/home")

                    threading.Thread(target=redirect_to_home, daemon=True).start()
            else:
                raise Exception("Resposta inválida do Supabase Auth")

        except Exception as ex:
            page.close(loading_dialog)
            error_message = str(ex)

            if "Email not confirmed" in error_message:
                SnackbarAnimations.show_animated_snackbar(
                    page,
                    "Conta não ativada! Verifique seu email.",
                    "orange",
                    icon=ft.Icons.WARNING,
                    duration=5000,
                )
                show_account_not_activated_info()
            elif "Invalid login credentials" in error_message:
                SnackbarAnimations.show_animated_snackbar(
                    page, "Email ou senha incorretos!", "red", icon=ft.Icons.ERROR
                )
                AnimationHelpers.animate_form_error(email_field, page)
                AnimationHelpers.animate_form_error(password_field, page)
            elif "network" in error_message.lower():
                error_dialog = ft.AlertDialog(
                    title=ft.Text(
                        "Erro de Conexão",
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.ON_ERROR_CONTAINER,
                    ),
                    content=ft.Container(
                        content=ft.Column(
                            [
                                ft.Icon(
                                    ft.Icons.WIFI_OFF,
                                    size=50,
                                    color=ft.Colors.ON_ERROR_CONTAINER,
                                ),
                                ft.Text(
                                    "Erro de conexão. Verifique sua internet e tente novamente.",
                                    size=16,
                                    text_align=ft.TextAlign.CENTER,
                                    color=ft.Colors.ON_ERROR_CONTAINER,
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=15,
                        ),
                        alignment=ft.alignment.center,
                        padding=20,
                    ),
                    actions=[
                        ft.TextButton(
                            "OK",
                            on_click=lambda e: page.close(error_dialog),
                            style=ft.ButtonStyle(color=ft.Colors.ON_SURFACE),
                        )
                    ],
                    bgcolor=ft.Colors.ERROR_CONTAINER,
                    shape=ft.RoundedRectangleBorder(radius=15),
                )
                DialogAnimations.show_dialog_with_animation(page, error_dialog)
            else:
                SnackbarAnimations.show_animated_snackbar(
                    page,
                    f"Erro ao fazer login: {error_message}",
                    "red",
                    icon=ft.Icons.ERROR_OUTLINE,
                    duration=5000,
                )

            logger.error(f"Erro no login: {error_message}")

    login_button.on_click = login

    lottie_container = ft.Container(
        content=login_lottie,
        animate_opacity=AnimationPresets.fade_in(AnimationPresets.SLOW),
        opacity=1.0,
    )

    form_column = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text(
                    "Acesse sua conta",
                    size=32,
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER,
                    color=ft.Colors.BLUE_800,
                ),
                ft.Text(
                    "Entre na comunidade SupaFit",
                    size=16,
                    text_align=ft.TextAlign.CENTER,
                    color=ft.Colors.BLUE_GREY_600,
                    italic=True,
                ),
                email_field,
                password_field,
                info_container,
                login_button,
                register_row,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20,
        ),
        ref=form_container,
        animate_opacity=AnimationPresets.fade_in(AnimationPresets.NORMAL),
        opacity=1.0,
    )

    layout_login = ft.ResponsiveRow(
        controls=[
            ft.Column(
                col={"sm": 6, "md": 5, "lg": 4},
                controls=[lottie_container],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            ft.Column(
                col={"sm": 6, "md": 5, "lg": 4},
                controls=[form_column],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        columns=12,
    )

    def animate_page_entry():
        AnimationHelpers.animate_container_entry(
            layout_login, page, delay=0.1, duration=AnimationPresets.SLOW
        )

    page.clean()
    animate_page_entry()
    page.update()

    return layout_login
