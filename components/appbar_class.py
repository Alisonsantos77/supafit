import flet as ft
from components.components import AvatarComponent
from services.supabase import SupabaseService
from utils.logger import get_logger

logger = get_logger("supafit.appbar_class")


def create_appbar(title: str, user_id=None) -> ft.AppBar:
    def show_snackbar(page, message: str, color: str = ft.Colors.RED_700):
        """Exibe feedback para o usuário com estilo consistente."""
        page.snack_bar = ft.SnackBar(
            content=ft.Text(
                message,
                color=ft.Colors.WHITE,
                size=14,
                weight=ft.FontWeight.BOLD,
                text_align=ft.TextAlign.CENTER,
            ),
            bgcolor=color,
            duration=3000,
            padding=10,
            shape=ft.RoundedRectangleBorder(radius=5),
        )
        page.snack_bar.open = True
        page.update()
        logger.info(f"SnackBar: {message}")

    def handle_menu_item(e):
        page = e.page
        user_id = page.client_storage.get("supafit.user_id")
        logger.info(
            f"Opção clicada: {e.control.content.controls[1].value}, user_id: {user_id}"
        )

        if not user_id:
            show_snackbar(
                page, "Usuário não autenticado. Faça login.", ft.Colors.BLUE_400
            )
            page.go("/login")
            return

        menu_actions = {
            "Início": "/home",
            "Perfil": "/profile_settings",
            "Histórico": "/history",
            "Pergunte ao Treinador": "/trainer",
            "Galeria de Vitórias": "/community",
        }

        if e.control.content.controls[1].value in menu_actions:
            page.go(menu_actions[e.control.content.controls[1].value])
        elif e.control.content.controls[1].value == "Sair":

            def confirm_logout(e):
                if e.control.text == "Sim":
                    try:
                        supabase_service = SupabaseService.get_instance(page)
                        supabase_service.logout()
                    except Exception as ex:
                        logger.error(f"Erro ao realizar logout: {str(ex)}")
                        show_snackbar(
                            page,
                            "Erro ao realizar logout. Tente novamente.",
                            ft.Colors.RED_700,
                        )
                page.close(confirm_dialog)
                page.update()

            confirm_dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("Confirmar Saída"),
                content=ft.Text("Tem certeza que deseja sair?"),
                actions=[
                    ft.TextButton("Sim", on_click=confirm_logout),
                    ft.TextButton("Não", on_click=confirm_logout),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
                shape=ft.RoundedRectangleBorder(radius=10),
            )
            page.open(confirm_dialog)

    avatar = AvatarComponent(
        user_id=user_id if user_id else None,
        image_url=(user_id if user_id else "https://picsum.photos/200"),
        radius=10,
        is_trainer=False,
    )

    return ft.AppBar(
        title=ft.Text(f"{title}", size=20, weight=ft.FontWeight.BOLD),
        center_title=True,
        actions=[
            ft.PopupMenuButton(
                content=avatar,
                icon=ft.Icons.PERSON,
                tooltip="Perfil",
                items=[
                    ft.PopupMenuItem(
                        content=ft.Row(
                            [
                                ft.Icon(ft.Icons.HOME, size=20),
                                ft.Text("Início", size=14),
                            ]
                        ),
                        on_click=handle_menu_item,
                    ),
                    ft.PopupMenuItem(
                        content=ft.Row(
                            [
                                ft.Icon(ft.Icons.PERSON, size=20),
                                ft.Text("Perfil", size=14),
                            ]
                        ),
                        on_click=handle_menu_item,
                    ),
                    ft.PopupMenuItem(
                        content=ft.Row(
                            [
                                ft.Icon(ft.Icons.CALENDAR_MONTH_ROUNDED, size=20),
                                ft.Text("Histórico", size=14),
                            ]
                        ),
                        on_click=handle_menu_item,
                    ),
                    ft.PopupMenuItem(
                        content=ft.Row(
                            [
                                ft.Icon(ft.Icons.TIMER, size=20),
                                ft.Text("Pergunte ao Treinador", size=14),
                            ]
                        ),
                        on_click=handle_menu_item,
                    ),
                    ft.PopupMenuItem(
                        content=ft.Row(
                            [
                                ft.Icon(ft.Icons.GROUP, size=20),
                                ft.Text("Galeria de Vitórias", size=14),
                            ]
                        ),
                        on_click=handle_menu_item,
                    ),
                    ft.PopupMenuItem(),
                    ft.PopupMenuItem(
                        content=ft.Row(
                            [
                                ft.Icon(
                                    ft.Icons.LOGOUT_SHARP, size=20, color=ft.Colors.RED
                                ),
                                ft.Text("Sair", size=14, color=ft.Colors.RED),
                            ]
                        ),
                        on_click=handle_menu_item,
                    ),
                ],
            ),
        ],
    )
