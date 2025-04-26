import flet as ft
from services.supabase_service import SupabaseService


def ProfilePage(page: ft.Page):
    supabase_service = SupabaseService()
    user_id = page.client_storage.get("user_id") or "default_user"
    profile = (
        supabase_service.get_profile(user_id).data[0]
        if supabase_service.get_profile(user_id).data
        else {}
    )

    name_field = ft.TextField(label="Nome", value=profile.get("name", ""))
    age_field = ft.TextField(label="Idade", value=str(profile.get("age", 0)))

    def save_profile(e):
        supabase_service.client.table("user_profiles").upsert(
            {
                "user_id": user_id,
                "name": name_field.value,
                "age": int(age_field.value) if age_field.value else 0,
            }
        ).execute()

    return ft.Container(
        content=ft.Column(
            [
                ft.Text("Perfil", size=24, weight=ft.FontWeight.BOLD),
                name_field,
                age_field,
                ft.ElevatedButton("Salvar", on_click=save_profile),
                ft.ElevatedButton("Voltar", on_click=lambda e: page.go("/")),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        alignment=ft.alignment.center,
        padding=20,
    )
