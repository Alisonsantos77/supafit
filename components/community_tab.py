import flet as ft
from components.components import CustomListTile, AvatarComponent


def CommunityTab(page: ft.Page, supabase_service):
    user_id = page.client_storage.get("user_id")
    victories_list = ft.ListView(
        spacing=10,
        padding=10,
        auto_scroll=True,
        divider_thickness=1,
    )
    status_text = ft.Text("", color=ft.Colors.RED, size=14)

    predefined_victories = [
        {"label": "Aumentei o peso!", "content": "Aumentei 5kg no supino"},
        {
            "label": "Treino concluído!",
            "content": "Completei meu primeiro treino da semana",
        },
        {"label": "Novo recorde!", "content": "Corri 10km pela primeira vez"},
        {"label": "Semana perfeita!", "content": "Treinei todos os dias desta semana"},
        {"label": "Foco total!", "content": "Mantive minha dieta por 7 dias seguidos"},
    ]

    def load_victories():
        # 1) Busca todas as vitórias
        resp_vic = supabase_service.table("victories").select("*").execute()
        victories = resp_vic.data or []

        # 2) Extrai IDs únicos de usuário
        user_ids = list({v["user_id"] for v in victories})
        user_ids.append(
            user_id
        )  # garante incluir o próprio usuário, se quiser mostrar também

        # 3) Busca perfis em lote
        resp_profiles = (
            supabase_service.table("user_profiles")
            .select("user_id, name")
            .in_("user_id", user_ids)
            .execute()
        )
        profiles = resp_profiles.data or []

        # 4) Mapeia user_id → name
        name_map = {p["user_id"]: p["name"] for p in profiles}

        victories_list.controls.clear()
        for v in victories:
            nome = name_map.get(v["user_id"], "Usuário desconhecido")
            victories_list.controls.append(
                ft.Card(
                    content=ft.Container(
                        content=CustomListTile(
                            leading=AvatarComponent(v["user_id"], radius=20),
                            title=ft.Text(nome, weight=ft.FontWeight.BOLD, size=16),
                            subtitle=ft.Text(v["content"], size=14),
                            content_padding=ft.padding.symmetric(
                                horizontal=10, vertical=5
                            ),
                        ),
                        padding=10,
                        border_radius=10,
                    ),
                    elevation=2,
                    margin=ft.margin.symmetric(vertical=5),
                )
            )
        page.update()

    def share_victory(e, content):
        try:
            supabase_service.table("victories").insert(
                {"user_id": user_id, "content": content}
            ).execute()
            load_victories()
            page.snack_bar = ft.SnackBar(
                content=ft.Text(
                    "Conquista Compartilhada – sua conquista está na galeria!"
                )
            )
            page.snack_bar.open = True
        except Exception as ex:
            status_text.value = f"Erro ao compartilhar: {ex}"
            page.update()

    # Gera os chips de conquistas
    victory_chips = ft.Row(
        wrap=True, spacing=10, run_spacing=10, alignment=ft.MainAxisAlignment.CENTER
    )
    for vic in predefined_victories:
        victory_chips.controls.append(
            ft.Chip(
                label=ft.Text(vic["label"]),
                leading=ft.Icon(ft.Icons.STAR, color=ft.Colors.YELLOW_700),
                on_click=lambda e, c=vic["content"]: share_victory(e, c),
            )
        )

    load_victories()

    return ft.Column(
        [
            ft.Text("Galeria de Conquistas", size=20, weight=ft.FontWeight.BOLD),
            ft.Container(
                content=victories_list, height=page.window.height * 0.5, expand=True
            ),
            ft.Text(
                "Escolha uma conquista para compartilhar:",
                size=16,
                weight=ft.FontWeight.BOLD,
            ),
            victory_chips,
            status_text,
        ],
        spacing=15,
        alignment=ft.MainAxisAlignment.START,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )
