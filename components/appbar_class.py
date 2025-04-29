import flet as ft
from flet import Icons
from components.components import AvatarComponent


def create_appbar(title: str, user_id=None) -> ft.AppBar:
    def handle_menu_item(e):
        user_id = e.page.client_storage.get("user_id")
        print(
            f"Opção clicada: {e.control.content.controls[1].value}, user_id: {user_id}"
        )

        if not user_id:
            e.page.go("/login")
            return

        if e.control.content.controls[1].value == "Perfil":
            e.page.go("/profile_settings")
        elif e.control.content.controls[1].value == "Histórico":
            e.page.go("/history")
        elif e.control.content.controls[1].value == "Pergunte ao Treinador":
            e.page.go("/trainer")
        elif e.control.content.controls[1].value == "Galeria de Vitórias":
            e.page.go("/community")
        elif e.control.content.controls[1].value == "Sair":

            def confirm_logout(e):
                if e.control.text == "Sim":
                    e.page.client_storage.remove("user_id")
                    e.page.go("/login")
                e.page.close(confirm_dialog)

            confirm_dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("Confirmar Saída"),
                content=ft.Text("Tem certeza que deseja sair?"),
                actions=[
                    ft.TextButton("Sim", on_click=confirm_logout),
                    ft.TextButton("Não", on_click=confirm_logout),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            e.page.open(confirm_dialog)

    avatar = AvatarComponent(
        user_id=user_id if user_id else None,
        image_url=(
            user_id if user_id else "https://picsum.photos/200"
        ),
        radius=20,
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
