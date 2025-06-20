import flet as ft
from services.supabase import SupabaseService
from utils.helpers import format_date


def HistoryPage(page: ft.Page, supabase):
    supabase_service = SupabaseService()
    user_id = page.client_storage.get("supafit.user_id")
    workouts = supabase_service.get_workouts(user_id).data or []

    history_cards = [
        ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text(workout["name"], weight=ft.FontWeight.BOLD),
                        ft.Text(format_date(workout["date"])),
                    ]
                ),
                padding=10,
            )
        )
        for workout in workouts
    ]

    return ft.Container(
        content=ft.Column(
            [
                ft.Text("Histórico de Treinos", size=24, weight=ft.FontWeight.BOLD),
                ft.ElevatedButton("Voltar", on_click=lambda e: page.go("/home")),
                ft.Column(history_cards, scroll=ft.ScrollMode.AUTO),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        alignment=ft.alignment.center,
        padding=20,
    )
