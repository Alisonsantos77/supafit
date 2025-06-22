import flet as ft
from components.components import AvatarComponent
from services.supabase import SupabaseService
from utils.logger import get_logger

logger = get_logger("supafit.mobile_appbar")


class MobileAppBar:
    def __init__(self, page: ft.Page):
        self.page = page

    def show_snackbar(
        self, message: str, color: str = ft.Colors.RED_700, icon: str = None
    ):
        """Exibe SnackBar com ícone opcional e estilo moderno."""
        content = ft.Row(
            [
                (
                    ft.Icon(icon, color=ft.Colors.WHITE, size=20)
                    if icon
                    else ft.Container()
                ),
                ft.Text(
                    message,
                    color=ft.Colors.WHITE,
                    size=14,
                    weight=ft.FontWeight.BOLD,
                ),
            ],
            spacing=8,
            alignment=ft.MainAxisAlignment.CENTER,
        )
        self.page.snack_bar = ft.SnackBar(
            content=content,
            bgcolor=color,
            duration=3000,
            padding=12,
            shape=ft.RoundedRectangleBorder(radius=8),
            elevation=0,
        )
        self.page.snack_bar.open = True
        self.page.update()
        logger.info(f"SnackBar: {message}")

    def handle_menu_item(self, e):
        """Manipula ações do menu com navegação e logout."""
        user_id = self.page.client_storage.get("supafit.user_id")
        logger.info(
            f"Opção clicada: {e.control.content.controls[1].value}, user_id: {user_id}"
        )

        if not user_id:
            self.show_snackbar(
                "Faça login para continuar.", ft.Colors.BLUE_400, ft.Icons.LOGIN
            )
            self.page.go("/login")
            return

        menu_actions = {
            "Início": "/home",
            "Perfil": "/profile_settings",
            "Histórico": "/history",
            "Pergunte ao Treinador": "/trainer",
            "Galeria de Vitórias": "/community",
        }

        option = e.control.content.controls[1].value
        if option in menu_actions:
            self.page.go(menu_actions[option])
        elif option == "Sair":

            def confirm_logout(e):
                if e.control.text == "Sim":
                    try:
                        supabase_service = SupabaseService.get_instance(self.page)
                        supabase_service.logout()
                        self.show_snackbar(
                            "Logout realizado com sucesso.",
                            ft.Colors.GREEN_600,
                            ft.Icons.CHECK,
                        )
                        self.page.go("/login")
                    except Exception as ex:
                        logger.error(f"Erro ao realizar logout: {str(ex)}")
                        self.show_snackbar(
                            "Erro ao realizar logout.",
                            ft.Colors.RED_700,
                            ft.Icons.ERROR,
                        )
                self.page.close(confirm_dialog)
                self.page.update()

            confirm_dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("Confirmar Saída", size=18, weight=ft.FontWeight.BOLD),
                content=ft.Text("Deseja realmente sair?"),
                actions=[
                    ft.TextButton(
                        "Sim",
                        on_click=confirm_logout,
                        style=ft.ButtonStyle(color=ft.Colors.RED),
                    ),
                    ft.TextButton("Não", on_click=confirm_logout),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
                shape=ft.RoundedRectangleBorder(radius=12),
                elevation=2,
            )
            self.page.open(confirm_dialog)

    def create_appbar(self, title: str, show_back_button: bool = False) -> ft.AppBar:
        """Cria AppBar otimizado para mobile com design moderno."""
        user_id = self.page.client_storage.get("supafit.user_id")
        avatar = AvatarComponent(
            user_id=user_id,
            image_url=user_id if user_id else "https://picsum.photos/200",
            radius=16,
            is_trainer=False,
        )

        leading = (
            ft.IconButton(
                icon=ft.Icons.ARROW_BACK,
                on_click=lambda _: self.page.go(
                    self.page.views[-2].route if len(self.page.views) > 1 else "/home"
                ),
                tooltip="Voltar",
                icon_size=24,
                style=ft.ButtonStyle(color=ft.Colors.PRIMARY),
            )
            if show_back_button
            else None
        )

        return ft.AppBar(
            title=ft.Text(
                title,
                size=18,
                weight=ft.FontWeight.W_600,
                color=ft.Colors.PRIMARY,
            ),
            center_title=True,
            leading=leading,
            elevation=0,
            bgcolor=ft.Colors.SURFACE,
            actions=[
                ft.PopupMenuButton(
                    content=avatar,
                    tooltip="Menu",
                    items=[
                        ft.PopupMenuItem(
                            content=ft.Row(
                                [
                                    ft.Icon(
                                        ft.Icons.HOME, color=ft.Colors.BLUE_600, size=20
                                    ),
                                    ft.Text(
                                        "Início", size=14, weight=ft.FontWeight.W_500
                                    ),
                                ],
                                spacing=12,
                            ),
                            on_click=self.handle_menu_item,
                        ),
                        ft.PopupMenuItem(
                            content=ft.Row(
                                [
                                    ft.Icon(
                                        ft.Icons.PERSON,
                                        color=ft.Colors.GREEN_600,
                                        size=20,
                                    ),
                                    ft.Text(
                                        "Perfil", size=14, weight=ft.FontWeight.W_500
                                    ),
                                ],
                                spacing=12,
                            ),
                            on_click=self.handle_menu_item,
                        ),
                        ft.PopupMenuItem(
                            content=ft.Row(
                                [
                                    ft.Icon(
                                        ft.Icons.CALENDAR_MONTH,
                                        color=ft.Colors.PURPLE_600,
                                        size=20,
                                    ),
                                    ft.Text(
                                        "Histórico", size=14, weight=ft.FontWeight.W_500
                                    ),
                                ],
                                spacing=12,
                            ),
                            on_click=self.handle_menu_item,
                        ),
                        ft.PopupMenuItem(
                            content=ft.Row(
                                [
                                    ft.Icon(
                                        ft.Icons.TIMER,
                                        color=ft.Colors.ORANGE_600,
                                        size=20,
                                    ),
                                    ft.Text(
                                        "Pergunte ao Treinador",
                                        size=14,
                                        weight=ft.FontWeight.W_500,
                                    ),
                                ],
                                spacing=12,
                            ),
                            on_click=self.handle_menu_item,
                        ),
                        ft.PopupMenuItem(
                            content=ft.Row(
                                [
                                    ft.Icon(
                                        ft.Icons.GROUP,
                                        color=ft.Colors.TEAL_600,
                                        size=20,
                                    ),
                                    ft.Text(
                                        "Galeria de Vitórias",
                                        size=14,
                                        weight=ft.FontWeight.W_500,
                                    ),
                                ],
                                spacing=12,
                            ),
                            on_click=self.handle_menu_item,
                        ),
                        ft.PopupMenuItem(),
                        ft.PopupMenuItem(
                            content=ft.Row(
                                [
                                    ft.Icon(
                                        ft.Icons.LOGOUT,
                                        color=ft.Colors.RED_600,
                                        size=20,
                                    ),
                                    ft.Text(
                                        "Sair",
                                        size=14,
                                        weight=ft.FontWeight.W_500,
                                        color=ft.Colors.RED_600,
                                    ),
                                ],
                                spacing=12,
                            ),
                            on_click=self.handle_menu_item,
                        ),
                    ],
                    menu_position=ft.PopupMenuPosition.UNDER,
                    elevation=2,
                    shape=ft.RoundedRectangleBorder(radius=12),
                ),
            ],
        )
