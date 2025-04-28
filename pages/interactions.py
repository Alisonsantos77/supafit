import flet as ft
from components.community_tab import CommunityTab
from components.trainer_tab import TrainerTab


def InteractionsPage(page: ft.Page, supabase_service, anthropic):
    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        tabs=[
            ft.Tab(
                text="Comunidade",
                icon=ft.Icons.GROUP,
                content=ft.Container(
                    content=CommunityTab(page, supabase_service),
                    padding=10,
                ),
            ),
            ft.Tab(
                text="Treinador",
                icon=ft.Icons.CHAT,
                content=ft.Container(
                    content=TrainerTab(page, supabase_service, anthropic),
                    padding=10,
                ),
            ),
        ],
        divider_color=ft.Colors.BLUE_200,
        indicator_color=ft.Colors.BLUE_700,
    )

    return ft.Container(
        content=ft.Column(
            [tabs],
            expand=True,
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=10,
        height=page.window.height - 100,
        expand=True,
    )
