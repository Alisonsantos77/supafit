import flet as ft
from services.supabase import SupabaseService
from utils.logger import get_logger

logger = get_logger("supafit.mobile_appbar")


class MobileAppBar:
    def __init__(self, page: ft.Page):
        self.page = page

    def handle_menu_item(self, e):
        """Manipula ações do menu com navegação e logout."""
        user_id = self.page.client_storage.get("supafit.user_id")
        logger.info(
            f"Opção clicada: {e.control.content.controls[1].value}, user_id: {user_id}"
        )

        if not user_id:
            print("[APPBAR]: Usuário não encontrado, voltando para login.")
            self.page.go("/login")
            return

        menu_actions = {
            "Início": "/home",
            "Perfil": "/profile_settings",
            "Histórico": "/history",
            "Pergunte ao Treinador": "/trainer",
            "Galeria de Vitórias": "/community",
            "💪 Apoie o SupaFit": "/support",
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
                        self.page.go("/login")
                    except Exception as ex:
                        logger.error(f"Erro ao realizar logout: {str(ex)}")
                self.page.close(confirm_dialog)
                self.page.update()

            confirm_dialog = ft.AlertDialog(
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

    def create_appbar(self, title: str, show_back_button: bool = True) -> ft.AppBar:
        """
        Cria AppBar otimizado para mobile com design moderno.

        Args:
            title: Título do AppBar
            show_back_button: Se deve mostrar botão de voltar (padrão: True)
                             False para telas principais como /home e /login
        """

        # Telas que nunca devem ter botão de voltar (pontos de entrada principais)
        NO_BACK_BUTTON_ROUTES = ["/", "/home", "/login", "/register"]

        # Se a rota atual está na lista de "sem botão de voltar", força show_back_button = False
        current_route = self.page.route
        if current_route in NO_BACK_BUTTON_ROUTES:
            show_back_button = False

        return ft.AppBar(
            title=ft.Container(
                content=ft.Text(
                    title,
                    size=18,
                    weight=ft.FontWeight.W_600,
                    color=ft.Colors.PRIMARY,
                ),
                padding=ft.padding.symmetric(horizontal=16),
            ),
            center_title=True,
            elevation=0,
            bgcolor=ft.Colors.SURFACE,
            automatically_imply_leading=show_back_button,
            color=ft.Colors.PRIMARY,
            actions=[
                ft.Container(
                    content=ft.PopupMenuButton(
                        content=ft.Icon(
                            ft.Icons.MENU_OUTLINED,
                            size=28,
                            color=ft.Colors.PRIMARY,
                        ),
                        tooltip="Menu",
                        items=[
                            ft.PopupMenuItem(
                                content=ft.Row(
                                    [
                                        ft.Icon(
                                            ft.Icons.HOME,
                                            color=ft.Colors.BLUE_600,
                                            size=20,
                                        ),
                                        ft.Text(
                                            "Início",
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
                                            ft.Icons.PERSON,
                                            color=ft.Colors.GREEN_600,
                                            size=20,
                                        ),
                                        ft.Text(
                                            "Perfil",
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
                                            ft.Icons.CALENDAR_MONTH,
                                            color=ft.Colors.PURPLE_600,
                                            size=20,
                                        ),
                                        ft.Text(
                                            "Histórico",
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
                            ft.PopupMenuItem(
                                content=ft.Row(
                                    [
                                        ft.Icon(
                                            ft.Icons.FAVORITE,
                                            color=ft.Colors.PINK_600,
                                            size=20,
                                        ),
                                        ft.Text(
                                            "💪 Apoie o SupaFit",
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
                    padding=ft.padding.only(right=16),
                ),
            ],
        )
