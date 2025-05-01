import flet as ft
from services.services import SupabaseService


def ProfileSettingsPage(page: ft.Page):
    supabase_service = SupabaseService()
    user_id = page.client_storage.get("supafit.user_id") or "supafit_user"
    profile = (
        supabase_service.get_profile(user_id).data[0]
        if supabase_service.get_profile(user_id).data
        else {}
    )

    name_field = ft.TextField(label="Nome", value=profile.get("name", ""))
    age_field = ft.TextField(label="Idade", value=str(profile.get("age", 0)))
    theme_switch = ft.Switch(
        label="Tema Escuro",
        value=profile.get("theme", "light") == "dark",
    )
    rest_duration = ft.TextField(
        label="Duração do Intervalo (segundos)",
        value=str(profile.get("rest_duration", 60)),
    )

    def save_all(e):
        page.theme_mode = (
            ft.ThemeMode.DARK if theme_switch.value else ft.ThemeMode.LIGHT
        )
        supabase_service.client.table("user_profiles").upsert(
            {
                "user_id": user_id,
                "name": name_field.value,
                "age": int(age_field.value) if age_field.value else 0,
                "theme": "dark" if theme_switch.value else "light",
                "rest_duration": (
                    int(rest_duration.value) if rest_duration.value else 60
                ),
            }
        ).execute()
        page.go("/home")

    return ft.Container(
        content=ft.Column(
            [
                ft.Text("Perfil e Configurações", size=24, weight=ft.FontWeight.BOLD),
                name_field,
                age_field,
                theme_switch,
                rest_duration,
                ft.ElevatedButton("Salvar", on_click=save_all),
                ft.ElevatedButton("Voltar", on_click=lambda e: page.go("/home")),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        alignment=ft.alignment.center,
        padding=20,
    )
