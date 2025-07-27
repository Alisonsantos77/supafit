import json
import flet as ft
import flet_lottie as fl
import os
from time import sleep
from services.supabase import SupabaseService
from utils.logger import get_logger
from pages.auth.utils.validators import Validators
from pages.auth.utils.animations import (
    AnimationPresets,
    AnimationHelpers,
    SnackbarAnimations,
    DialogAnimations,
)

logger = get_logger("supabafit.register")

LOTTIE_REGISTER = os.getenv("LOTTIE_REGISTER")


def RegisterPage(page: ft.Page):
    supabase_service = SupabaseService.get_instance(page)
    page.scroll = ft.ScrollMode.AUTO

    register_btn = ft.Ref[ft.ElevatedButton]()
    form_container = ft.Ref[ft.Container]()

    # Campos do formulário - HABILITADOS por padrão
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
        disabled=False,
        animate_opacity=AnimationPresets.fade_in(),
        color=ft.Colors.BLUE_400,
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
        disabled=False,
        animate_opacity=AnimationPresets.fade_in(),
        color=ft.Colors.BLUE_400,
    )

    password_confirmation_field = ft.TextField(
        label="Confirmar Senha",
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
        disabled=False,
        animate_opacity=AnimationPresets.fade_in(),
        color=ft.Colors.BLUE_400,
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
        disabled=False,
        animate_opacity=AnimationPresets.fade_in(),
    )

    terms_checkbox = ft.Checkbox(
        label="Li e aceito os Termos de Uso e a Política de Privacidade",
        value=False,
        animate_opacity=AnimationPresets.fade_in(),
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

    register_button = ft.ElevatedButton(
        "Registrar",
        style=ft.ButtonStyle(
            bgcolor={
                ft.ControlState.HOVERED: ft.Colors.BLUE_500,
                ft.ControlState.DEFAULT: ft.Colors.GREY_400,
                ft.ControlState.DISABLED: ft.Colors.GREY_300,
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
        disabled=True,
        ref=register_btn,
        animate_opacity=AnimationPresets.fade_in(),
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
        animate_opacity=AnimationPresets.fade_in(),
    )

    def update_form_state(e):
        """Atualiza estado do botão baseado na aceitação dos termos"""
        are_terms_accepted = terms_checkbox.value
        register_btn.current.disabled = not are_terms_accepted

        # Animação suave do botão usando AnimationPresets
        register_btn.current.opacity = 1.0 if are_terms_accepted else 0.8

        register_btn.current.bgcolor = (
            ft.Colors.BLUE_700 if are_terms_accepted else ft.Colors.GREY_400
        )
        register_btn.current.animate_opacity = AnimationPresets.fade_in(AnimationPresets.FAST)
        page.update()
        logger.info(
            f"Estado do formulário atualizado: Termos aceitos = {are_terms_accepted}"
        )

    terms_checkbox.on_change = update_form_state

    def save_user_data(user_id, email, level):
        """Salva dados do usuário no client storage"""
        try:
            page.client_storage.set("supafit.user_id", user_id)
            page.client_storage.set("supafit.email", email)
            page.client_storage.set("supafit.level", level)
            logger.info(
                f"Dados salvos: user_id={user_id}, email={email}, level={level}"
            )
        except Exception as ex:
            logger.error(f"Erro ao salvar dados: {str(ex)}")

    def clear_form():
        """Limpa todos os campos do formulário com animação"""
        email_field.value = ""
        password_field.value = ""
        password_confirmation_field.value = ""
        level_dropdown.value = "iniciante"
        terms_checkbox.value = False
        update_form_state(None)

        # Usar AnimationHelpers para animação de limpeza
        form_container.current.opacity = 0.7
        form_container.current.animate_opacity = AnimationPresets.fade_in(
            AnimationPresets.FAST
        )
        page.update()
        sleep(0.1)
        form_container.current.opacity = 1.0
        page.update()

        logger.info("Formulário limpo")

    def validate_form_client_side():
        """Validação client-side com feedback via SnackBar animado"""
        email = email_field.value.strip() if email_field.value else ""
        password = password_field.value.strip() if password_field.value else ""
        password_confirmation = (
            password_confirmation_field.value.strip()
            if password_confirmation_field.value
            else ""
        )
        level = level_dropdown.value
        terms_accepted = terms_checkbox.value

        # Usar o módulo de validações
        is_valid, error_message = Validators.validate_registration_form(
            email, password, password_confirmation, level, terms_accepted
        )

        if not is_valid:
            # Animar campo com erro se aplicável
            if "Email" in error_message:
                AnimationHelpers.animate_form_error(email_field, page)
            elif "senha" in error_message.lower():
                if "coincidem" in error_message:
                    AnimationHelpers.animate_form_error(
                        password_confirmation_field, page
                    )
                else:
                    AnimationHelpers.animate_form_error(password_field, page)

            SnackbarAnimations.show_animated_snackbar(
                page, error_message, "red", icon=ft.Icons.ERROR
            )
            return False

        return True

    def register(e):
        """Função principal de registro"""
        AnimationHelpers.animate_button_click(register_button, page)

        # Validação client-side
        if not validate_form_client_side():
            return

        email = email_field.value.strip()
        password = password_field.value.strip()
        level = level_dropdown.value

        loading_dialog = DialogAnimations.create_loading_dialog("Criando sua conta...")
        DialogAnimations.show_dialog_with_animation(page, loading_dialog)

        try:
            logger.info(f"Iniciando registro para: {email}")
            response = supabase_service.client.auth.sign_up(
                {"email": email, "password": password}
            )

            if response.user is None:
                raise Exception("Falha na criação da conta. Tente novamente.")

            # Salvar dados localmente
            save_user_data(response.user.id, response.user.email, level)

            page.close(loading_dialog)

            clear_form()

            success_dialog = DialogAnimations.create_success_dialog(
                "Conta criada com sucesso!", "Verifique seu email para ativar a conta."
            )
            DialogAnimations.show_dialog_with_animation(page, success_dialog)

            # Redirecionar após 3 segundos
            def redirect_after_success():
                sleep(3)
                page.close(success_dialog)
                SnackbarAnimations.show_animated_snackbar(
                    page, "Redirecionando para login...", "green", icon=ft.Icons.LOGIN
                )
                sleep(1)
                page.go("/login")

            # Executar redirecionamento em thread separada
            import threading

            threading.Thread(target=redirect_after_success, daemon=True).start()

        except Exception as ex:
            page.close(loading_dialog)
            error_msg = str(ex)

            # Errors conhecidos com mensagens amigáveis e snackbars animados
            if "already registered" in error_msg.lower():
                SnackbarAnimations.show_animated_snackbar(
                    page,
                    "Este email já está cadastrado. Tente fazer login.",
                    "orange",
                    icon=ft.Icons.WARNING,
                )
                AnimationHelpers.animate_form_error(email_field, page)
            elif "network" in error_msg.lower():
                # Criar diálogo de erro customizado para problemas de rede
                error_dialog = ft.AlertDialog(
                    title=ft.Text(
                        "Erro de Conexão",
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.RED_400,
                    ),
                    content=ft.Container(
                        content=ft.Column(
                            [
                                ft.Icon(
                                    ft.Icons.WIFI_OFF, size=50, color=ft.Colors.RED_400
                                ),
                                ft.Text(
                                    "Erro de conexão. Verifique sua internet e tente novamente.",
                                    size=16,
                                    color=ft.Colors.WHITE,
                                    text_align=ft.TextAlign.CENTER,
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
                            style=ft.ButtonStyle(color=ft.Colors.BLUE_400),
                        )
                    ],
                    bgcolor=ft.Colors.with_opacity(0.95, ft.Colors.GREY_900),
                    shape=ft.RoundedRectangleBorder(radius=15),
                )
                DialogAnimations.show_dialog_with_animation(page, error_dialog)
            else:
                # Erro genérico com snackbar
                SnackbarAnimations.show_animated_snackbar(
                    page,
                    f"Erro inesperado: {error_msg}",
                    "red",
                    duration=5000,
                    icon=ft.Icons.ERROR_OUTLINE,
                )

            logger.error(f"Erro no registro: {error_msg}")

    register_button.on_click = register

    lottie_container = ft.Container(
        content=fl.Lottie(
            src=LOTTIE_REGISTER,
            background_loading=True,
            filter_quality=ft.FilterQuality.HIGH,
            repeat=True,
            fit=ft.ImageFit.CONTAIN,
        ),
        animate_opacity=AnimationPresets.fade_in(AnimationPresets.SLOW),
        opacity=1.0,
    )

    form_column = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text(
                    "Crie sua conta",
                    size=32,
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER,
                    color=ft.Colors.BLUE_800,
                ),
                ft.Text(
                    "Junte-se à comunidade SupaFit",
                    size=16,
                    text_align=ft.TextAlign.CENTER,
                    color=ft.Colors.BLUE_GREY_600,
                    italic=True,
                ),
                email_field,
                password_field,
                password_confirmation_field,
                level_dropdown,
                ft.Column(
                    [terms_checkbox, terms_link],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=8,
                ),
                register_button,
                login_row,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20,
        ),
        ref=form_container,
        animate_opacity=AnimationPresets.fade_in(AnimationPresets.NORMAL),
        opacity=1.0,
    )

    layout_register = ft.ResponsiveRow(
        controls=[
            # ft.Column(
            #     col={"sm": 6, "md": 5, "lg": 4},
            #     controls=[lottie_container],
            #     alignment=ft.MainAxisAlignment.CENTER,
            #     horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            # ),
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
        """Animação de entrada suave da página usando AnimationHelpers"""
        AnimationHelpers.animate_container_entry(
            layout_register, page, delay=0.1, duration=AnimationPresets.SLOW
        )

    animate_page_entry()

    return layout_register
