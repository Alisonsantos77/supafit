import flet as ft


def create_appbar(title: str) -> ft.AppBar:
    return ft.AppBar(
        title=ft.AnimatedSwitcher(
            content=ft.Text(
                f"{title}",
                size=20,
                weight=ft.FontWeight.BOLD,
            ),
            transition=ft.AnimatedSwitcherTransition.SCALE,
            duration=300,
        ),
        center_title=True,
        actions=[
            ft.PopupMenuButton(
                icon=ft.Icons.PERSON,
                tooltip="Perfil",
                content=ft.Stack(
                    [
                        ft.AnimatedSwitcher(
                            content=ft.Container(
                                content=ft.CircleAvatar(
                                    bgcolor=ft.Colors.GREEN,
                                    radius=50,
                                    foreground_image_src="https://avatars.githubusercontent.com/u/5041459?s=88&v=4",
                                ),
                                alignment=ft.alignment.bottom_left,
                            ),
                            transition=ft.AnimatedSwitcherTransition.SCALE,
                            duration=300,
                        ),
                    ],
                    width=35,
                    height=35,
                ),
                items=[
                    ft.PopupMenuItem(
                        content=ft.Row(
                            controls=[
                                ft.Icon(name=ft.Icons.SETTINGS, size=20),
                                ft.Text(value="Perfil", size=14),
                            ]
                        ),
                    ),
                    ft.PopupMenuItem(
                        content=ft.Row(
                            controls=[
                                ft.Icon(name=ft.Icons.CALENDAR_MONTH_ROUNDED, size=20),
                            ]
                        ),
                        disabled=True,
                    ),
                    ft.PopupMenuItem(
                        content=ft.Row(
                            controls=[
                                ft.Icon(name=ft.Icons.TIMER, size=20),
                            ]
                        ),
                        disabled=True,
                    ),
                    ft.PopupMenuItem(
                        content=ft.Row(
                            controls=[
                                ft.Icon(name=ft.Icons.WB_SUNNY_OUTLINED, size=20),
                                ft.Text(value="Alterar Tema", size=14),
                            ]
                        ),
                    ),
                    ft.PopupMenuItem(),
                    ft.PopupMenuItem(
                        content=ft.Row(
                            controls=[
                                ft.Icon(
                                    name=ft.Icons.LOGOUT_SHARP,
                                    size=20,
                                    color=ft.Colors.RED,
                                ),
                                ft.Text(value="Sair", size=14, color=ft.Colors.RED),
                            ]
                        ),
                    ),
                ],
            ),
        ],
    )
