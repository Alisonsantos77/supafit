import flet as ft
from components.custom_list_tile import CustomListTile
from components.avatar_component import AvatarComponent
from services.supabase_service import SupabaseService


def CommunityPage(page: ft.Page, supabase_service):
    user_id = page.client_storage.get("user_id")
    victories_list = ft.ListView(expand=True, spacing=10, padding=10)
    victory_field = ft.TextField(
        label="Compartilhe sua conquista", width=600, multiline=True
    )
    share_button = ft.ElevatedButton("Compartilhar", width=150, height=50)
    status_text = ft.Text("", color=ft.Colors.RED)

    def load_victories():
        response = supabase_service.client.table("victories").select("*").execute()
        victories_list.controls.clear()
        for victory in response.data:
            victories_list.controls.append(
                CustomListTile(
                    leading=AvatarComponent(victory["user_id"], radius=20),
                    title=ft.Text(f"Usuário: {victory['user_id']}"),
                    subtitle=ft.Text(victory["content"]),
                )
            )
        page.update()

    def share_victory(e):
        content = victory_field.value.strip()
        if not content:
            status_text.value = "Digite uma conquista!"
            page.update()
            return
        supabase_service.client.table("victories").insert(
            {"user_id": user_id, "content": content}
        ).execute()
        victory_field.value = ""
        load_victories()
        page.snack_bar = ft.SnackBar(
            ft.Text("Conquista Compartilhada - Sua conquista está na galeria!")
        )
        page.snack_bar.open = True
        page.update()

    share_button.on_click = share_victory
    load_victories()

    return ft.Container(
        content=ft.Column(
            [victories_list, ft.Row([victory_field, share_button]), status_text],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20,
        ),
        padding=20,
    )
