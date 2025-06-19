import json
import flet as ft
import flet_lottie as fl
import re
import os
import logging
from time import sleep
from services.services import SupabaseService

logger = logging.getLogger("supafit.register")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

LOTTIE_REGISTER = os.getenv("LOTTIE_REGISTER")


def RegisterPage(page: ft.Page):
    supabase_service = SupabaseService()
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

    # Função para exibir diálogo de carregamento
    def show_loading():
        loading_dialog = ft.AlertDialog(
            content=ft.Container(
                content=ft.ProgressRing(color=ft.Colors.BLUE_400),
                alignment=ft.alignment.center,
            ),
            bgcolor=ft.Colors.TRANSPARENT,
            modal=True,
        )
        page.dialog = loading_dialog
        page.open(loading_dialog)
        page.update()
        logger.info("Diálogo de carregamento exibido")
        return loading_dialog

    # Função para fechar diálogo de carregamento
    def hide_loading(dialog):
        page.close(dialog)
        page.update()
        logger.info("Diálogo de carregamento fechado")

    # Função para exibir diálogo de sucesso
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
        )
        page.dialog = success_dialog
        page.open(success_dialog)
        page.update()
        logger.info(f"Diálogo de sucesso exibido: {message}")
        sleep(2)
        page.close(success_dialog)
        page.go(route)

    # Função para salvar dados localmente
    def save_user_data(user_id, email, level):
        try:
            page.client_storage.set("supafit.user_id", user_id)
            page.client_storage.set("supafit.email", email)
            page.client_storage.set("supafit.level", level)
            logger.info(
                f"Dados salvos no client_storage: user_id={user_id}, email={email}, level={level}"
            )

            # Salvar em arquivo user_data.txt
            app_data_path = os.getenv("FLET_APP_STORAGE_DATA")
            if app_data_path:
                file_path = os.path.join(app_data_path, "user_data.txt")
                with open(file_path, "w") as f:
                    f.write(f"user_id={user_id}\nemail={email}\nlevel={level}\n")
                logger.info(f"Dados salvos em arquivo: {file_path}")
            else:
                logger.warning("FLET_APP_STORAGE_DATA não definido, arquivo não salvo")
        except Exception as ex:
            logger.error(f"Erro ao salvar dados localmente: {str(ex)}")

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

            # Salvar dados de autenticação
            auth_data = {
                "user_id": response.user.id,
                "email": response.user.email,
                "access_token": (
                    response.session.access_token if response.session else None
                ),
                "refresh_token": (
                    response.session.refresh_token if response.session else None
                ),
                "created_at": response.user.created_at.isoformat(),
                "confirmed_at": (
                    response.user.confirmed_at.isoformat()
                    if response.user.confirmed_at
                    else None
                ),
            }
            supabase_service.save_auth_data(auth_data)
            logger.info(f"Dados de autenticação salvos:\n%s", json.dumps(auth_data, indent=2))

            # Configurar a sessão para requisições autenticadas
            if response.session:
                supabase_service.client.auth.set_session(
                    response.session.access_token, response.session.refresh_token
                )
                logger.info("Sessão configurada com sucesso.")
            else:
                logger.warning(
                    "Nenhuma sessão retornada no sign_up. Perfil será criado após o login."
                )

            # Validar user_id (ignorar validação para novo usuário)
            if not supabase_service.validate_user_id(
                response.user.id, is_new_user=True
            ):
                raise Exception(
                    "ID de usuário inválido ou não corresponde aos dados armazenados."
                )

            # Salvar dados localmente, mas não criar o perfil ainda
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
