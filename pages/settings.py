import flet as ft
from services.supabase_service import SupabaseService


def SettingsPage(page: ft.Page):
    supabase_service = SupabaseService()
    user_id = page.client_storage.get("user_id") or "default_user"
    profile = (
        supabase_service.get_profile(user_id).data[0]
        if supabase_service.get_profile(user_id).data
        else {}
    )

    theme_switch = ft.Switch(
        label="Tema Escuro",
        value=profile.get("theme", "light") == "dark",
        on_change=lambda e: update_theme(e),
    )
    rest_duration = ft.TextField(
        label="Duração do Intervalo (segundos)",
        value=str(profile.get("rest_duration", 60)),
    )

    def update_theme(e):
        page.theme_mode = (
            ft.ThemeMode.DARK if theme_switch.value else ft.ThemeMode.LIGHT
        )
        supabase_service.client.table("user_profiles").upsert(
            {"user_id": user_id, "theme": "dark" if theme_switch.value else "light"}
        ).execute()
        page.update()

    def save_settings(e):
        supabase_service.client.table("user_profiles").upsert(
            {
                "user_id": user_id,
                "rest_duration": (
                    int(rest_duration.value) if rest_duration.value else 60
                ),
            }
        ).execute()

    return ft.Container(
        content=ft.Column(
            [
                ft.Text("Configurações", size=24, weight=ft.FontWeight.BOLD),
                theme_switch,
                rest_duration,
                ft.ElevatedButton("Salvar", on_click=save_settings),
                ft.ElevatedButton("Voltar", on_click=lambda e: page.go("/")),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        alignment=ft.alignment.center,
        padding=20,
    )
