import flet as ft
from services.supabase import SupabaseService
from time import sleep


def UpdatePasswordPage(page: ft.Page):
    supabase = SupabaseService.get_instance(page)
    page.scroll = ft.ScrollMode.AUTO

    token = None
    user_id = None
    status_text = ft.Text("", color=ft.Colors.RED, size=14, italic=True)

    # --- Tentativa de autenticar com o access_token da URL ---
    if "#access_token=" in page.route:
        token = page.route.split("#access_token=")[-1].split("&")[0]
        try:
            response = supabase.client.auth.set_session(token, None)
            if not response.session:
                raise Exception("Sessão inválida")
            user_id = response.user.id
        except Exception as e:
            print(f"ERROR - UpdatePasswordPage: Erro ao autenticar com token: {str(e)}")
            page.go("/login")
            return
    else:
        print("ERROR - UpdatePasswordPage: Token não encontrado na URL.")
        page.go("/login")
        return

    # --- Campo de nova senha ---
    password_field = ft.TextField(
        label="Nova Senha",
        width=320,
        password=True,
        can_reveal_password=True,
        filled=True,
        border="underline",
        bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.BLUE_GREY),
        border_color=ft.Colors.BLUE_600,
        focused_border_color=ft.Colors.BLUE_400,
        cursor_color=ft.Colors.BLUE_400,
        text_size=16,
    )

    # --- Botão de salvar ---
    save_button = ft.ElevatedButton(
        "Salvar nova senha",
        width=320,
        height=50,
        style=ft.ButtonStyle(
            bgcolor={
                ft.ControlState.DEFAULT: ft.Colors.BLUE_700,
                ft.ControlState.HOVERED: ft.Colors.BLUE_500,
            },
            color=ft.Colors.WHITE,
            elevation={"": 4, "pressed": 2},
            shape=ft.RoundedRectangleBorder(radius=5),
        ),
    )

    def show_loading():
        dialog = ft.AlertDialog(
            modal=True,
            bgcolor=ft.Colors.TRANSPARENT,
            content=ft.Container(
                alignment=ft.alignment.center,
                content=ft.ProgressRing(color=ft.Colors.BLUE_400),
            ),
        )
        page.dialog = dialog
        page.open(dialog)
        page.update()
        return dialog

    def hide_loading(dialog):
        page.close(dialog)
        page.update()

    def show_success_and_redirect(message, route):
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
            modal=True,
            bgcolor=ft.Colors.with_opacity(0.9, ft.Colors.GREY_900),
        )
        page.dialog = success_dialog
        page.open(success_dialog)
        page.update()
        sleep(2)
        page.close(success_dialog)
        page.go(route)

    def on_save_click(e):
        nova_senha = password_field.value.strip()

        if len(nova_senha) < 6:
            status_text.value = "A senha deve ter pelo menos 6 caracteres."
            page.update()
            return

        dialog = show_loading()

        try:
            # Atualizar senha
            supabase.client.auth.update_user({"password": nova_senha})

            # Verificar perfil
            profile_response = supabase.get_profile(user_id)
            profile_exists = bool(
                profile_response.data and len(profile_response.data) > 0
            )
            level = (
                profile_response.data[0].get("level", "iniciante")
                if profile_exists
                else None
            )

            # Salvar no client_storage
            page.client_storage.set("supafit.access_token", token)
            page.client_storage.set("supafit.refresh_token", None)
            page.client_storage.set("supafit.user_id", user_id)
            page.client_storage.set("supafit.email", supabase.get_current_user().email)
            page.client_storage.set("supafit.profile_created", profile_exists)
            if level:
                page.client_storage.set("supafit.level", level)

            hide_loading(dialog)

            if profile_exists:
                show_success_and_redirect("Senha redefinida com sucesso!", "/home")
            else:
                show_success_and_redirect(
                    "Senha redefinida! Vamos criar seu perfil.", "/create_profile"
                )

        except Exception as ex:
            hide_loading(dialog)
            status_text.value = f"Erro: {str(ex)}"
            page.update()
            print(f"ERROR - UpdatePasswordPage: {str(ex)}")

    save_button.on_click = on_save_click

    # --- Layout da página ---
    layout = ft.ResponsiveRow(
        controls=[
            ft.Column(
                controls=[
                    ft.Text(
                        "Defina sua nova senha",
                        size=26,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(height=20),
                    password_field,
                    status_text,
                    ft.Container(height=10),
                    save_button,
                ],
                col={"sm": 12, "md": 6, "lg": 4},
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20,
            )
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        columns=12,
    )

    return layout
