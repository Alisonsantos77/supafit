import flet as ft
from datetime import datetime
import logging
from components.components import AvatarComponent
from utils.notification import send_notification

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def CommunityTab(page: ft.Page, supabase_service):
    user_id = page.client_storage.get("user_id") or "default_user"

    victories_grid = ft.GridView(
        expand=True,
        runs_count=2,  # 2 colunas
        max_extent=400,  # Largura máxima dos cards
        child_aspect_ratio=1.0,  # Proporção quadrada
        spacing=10,
        run_spacing=10,
        padding=10,
    )

    # Categorias para filtro (usando Chips)
    categories = ["Força", "Resistência", "Disciplina", "Nutrição", "Todas"]
    selected_category = "Todas"
    filter_chips = ft.ResponsiveRow(spacing=10, alignment=ft.MainAxisAlignment.CENTER)

    def update_victories(category="Todas"):
        victories_grid.controls.clear()
        victories_data = load_victories(category)
        for victory in victories_data:
            victories_grid.controls.append(create_victory_card(victory))
        page.update()

    def load_victories(category="Todas"):
        # Dados fictícios
        mock_victories = [
            {
                "user_id": "user1",
                "content": "Consegui levantar 100kg no supino!",
                "created_at": "2025-04-28T10:00:00Z",
                "category": "Força",
            },
            {
                "user_id": "user2",
                "content": "Corri 10km sem parar pela primeira vez!",
                "created_at": "2025-04-27T15:30:00Z",
                "category": "Resistência",
            },
            {
                "user_id": "user3",
                "content": "Completei 30 dias de dieta balanceada!",
                "created_at": "2025-04-26T08:00:00Z",
                "category": "Nutrição",
            },
        ]

        # Busca vitórias reais do Supabase
        query = (
            supabase_service.table("victories")
            .select("*")
            .order("created_at", desc=True)
        )
        resp_victories = query.execute()
        logger.info(f"Retorno da tabela 'victories': {resp_victories.data}")

        # Combina dados fictícios com reais
        victories_data = mock_victories + (
            resp_victories.data if isinstance(resp_victories.data, list) else []
        )

        # Filtra por categoria apenas os dados fictícios
        if category != "Todas":
            victories_data = [
                v for v in victories_data if v.get("category") == category
            ]

        # Busca informações dos usuários
        user_ids = [item["user_id"] for item in victories_data if "user_id" in item]
        user_info = {}
        if user_ids:
            resp_users = (
                supabase_service.table("user_profiles")
                .select("user_id, name")
                .in_("user_id", user_ids)
                .execute()
            )
            for user in resp_users.data:
                user_id = user["user_id"]
                name = user.get("name")
                user_info[user_id] = name or "supafit_user"

        # Adiciona nomes e contagem de curtidas
        for victory in victories_data:
            victory["author_name"] = user_info.get(victory["user_id"], "supafit_user")
            # Conta curtidas
            if "id" in victory:
                likes = (
                    supabase_service.table("victory_likes")
                    .select("count", count=True)
                    .eq("victory_id", victory["id"])
                    .execute()
                )
                victory["likes"] = likes.data[0]["count"] if likes.data else 0
                # Verifica se o usuário curtiu
                if user_id != "default_user":
                    liked = (
                        supabase_service.table("victory_likes")
                        .select("id")
                        .eq("victory_id", victory["id"])
                        .eq("user_id", user_id)
                        .execute()
                    )
                    victory["liked"] = bool(liked.data)

        return victories_data

    def create_victory_card(victory):
        # Formata a data
        try:
            created_at = datetime.fromisoformat(
                victory.get("created_at", "").replace("Z", "+00:00")
            ).strftime("%d/%m/%Y %H:%M")
        except:
            created_at = "Data desconhecida"

        description = victory.get("content") or "Sem descrição"
        category = victory.get("category") or "Geral"
        likes = victory.get("likes", 0)
        liked = victory.get("liked", False)

        # (visível apenas para o autor)
        delete_button = (
            ft.IconButton(
                icon=ft.Icons.DELETE_OUTLINE,
                icon_color=ft.Colors.RED_400,
                tooltip="Excluir sua vitória",
                on_click=lambda e: delete_victory(victory["id"]),
            )
            if "id" in victory
            and victory["user_id"] == user_id
            and user_id != "supafit_user"
            else None
        )

        card_container = ft.Container(
            content=ft.Column(
                [
                    ft.ListTile(
                        leading=AvatarComponent(
                            victory["user_id"], radius=20, is_trainer=False
                        ),
                        title=ft.Text(
                            victory["author_name"],
                            weight=ft.FontWeight.BOLD,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                        subtitle=ft.Text(
                            created_at,
                            size=12,
                        ),
                        trailing=delete_button,
                    ),
                    ft.Container(
                        content=ft.Text(
                            description,
                            size=16,
                            overflow=ft.TextOverflow.ELLIPSIS,
                            max_lines=3,
                        ),
                        padding=ft.padding.symmetric(horizontal=15),
                    ),
                    ft.Row(
                        [
                            ft.Chip(
                                label=ft.Text(category),
                                shape=ft.StadiumBorder(),
                            ),
                            ft.Row(
                                [
                                    ft.IconButton(
                                        icon=(
                                            ft.Icons.FAVORITE
                                            if liked
                                            else ft.Icons.FAVORITE_BORDER
                                        ),
                                        icon_color=ft.Colors.RED_400,
                                        tooltip="Curtir",
                                        on_click=lambda e: (
                                            toggle_like(victory["id"], liked)
                                            if "id" in victory
                                            else None
                                        ),
                                    ),
                                    ft.Text(f"{likes}", color=ft.Colors.PRIMARY),
                                ],
                                spacing=5,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        spacing=10,
                    ),
                ],
                spacing=10,
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=15,
            border_radius=10,
            on_click=lambda e: show_victory_details(victory),
            alignment=ft.alignment.center,
            on_hover=lambda e: setattr(
                card_container, "elevation", 10 if e.data == "true" else 5
            ),
        )

        return ft.Card(
            elevation=5,
            content=card_container,
            margin=ft.margin.symmetric(vertical=5, horizontal=10),
        )

    def show_victory_details(victory):
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(
                f"Vitória de {victory['author_name']}",
                color=ft.Colors.PRIMARY,
                overflow=ft.TextOverflow.ELLIPSIS,
            ),
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text(
                            f"Categoria: {victory.get('category', 'Geral')}",
                            size=14,
                        ),
                        ft.Container(
                            content=ft.ListView(
                                controls=[
                                    ft.Text(
                                        victory["content"],
                                        size=16,
                                        color=ft.Colors.PRIMARY,
                                    )
                                ],
                                auto_scroll=True,
                            ),
                        ),
                        ft.Text(
                            f"Data: {datetime.fromisoformat(victory['created_at'].replace('Z', '+00:00')).strftime('%d/%m/%Y %H:%M')}",
                            size=12,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
            ),
            actions=[
                ft.TextButton(
                    "Fechar",
                    on_click=lambda e: page.close(dialog),
                ),
            ],
        )

        page.open(dialog)

    def toggle_like(victory_id, currently_liked):
        if user_id == "default_user":
            page.open(
                ft.SnackBar(
                    content=ft.Text(
                        "Você precisa estar logado para curtir!", color=ft.Colors.WHITE
                    ),
                    bgcolor=ft.Colors.RED_400,
                    action="OK",
                    action_color=ft.Colors.WHITE,
                )
            )
            return

        try:
            if currently_liked:
                # Remove curtida
                supabase_service.table("victory_likes").delete().eq(
                    "victory_id", victory_id
                ).eq("user_id", user_id).execute()
            else:
                # Adiciona curtida
                supabase_service.table("victory_likes").insert(
                    {
                        "victory_id": victory_id,
                        "user_id": user_id,
                        "created_at": datetime.utcnow().isoformat() + "Z",
                    }
                ).execute()
            update_victories(selected_category)
        except Exception as ex:
            logger.error(f"Erro ao curtir/descurtir: {str(ex)}")
            page.open(
                ft.SnackBar(
                    content=ft.Text(
                        f"Erro ao curtir/descurtir: {str(ex)}", color=ft.Colors.WHITE
                    ),
                    bgcolor=ft.Colors.RED,
                    action="OK",
                    action_color=ft.Colors.WHITE,
                )
            )

    def delete_victory(victory_id):
        if user_id == "default_user":
            page.open(
                ft.SnackBar(
                    content=ft.Text(
                        "Você precisa estar logado para excluir!", color=ft.Colors.WHITE
                    ),
                    bgcolor=ft.Colors.RED,
                    action="OK",
                    action_color=ft.Colors.WHITE,
                )
            )
            return

        try:
            # Verifica se o usuário é o autor
            victory = (
                supabase_service.table("victories")
                .select("user_id")
                .eq("id", victory_id)
                .execute()
            )
            if victory.data and victory.data[0]["user_id"] == user_id:
                supabase_service.table("victories").delete().eq(
                    "id", victory_id
                ).execute()
                supabase_service.table("victory_likes").delete().eq(
                    "victory_id", victory_id
                ).execute()
                update_victories(selected_category)
                page.open(
                    ft.SnackBar(
                        content=ft.Text(
                            "Vitória excluída com sucesso!", color=ft.Colors.WHITE
                        ),
                        bgcolor=ft.Colors.GREEN_400,
                        action="OK",
                        action_color=ft.Colors.WHITE,
                    )
                )
            else:
                page.open(
                    ft.SnackBar(
                        content=ft.Text(
                            "Você não pode excluir esta vitória!", color=ft.Colors.WHITE
                        ),
                        bgcolor=ft.Colors.RED,
                        action="OK",
                        action_color=ft.Colors.WHITE,
                    )
                )
        except Exception as ex:
            logger.error(f"Erro ao excluir vitória: {str(ex)}")
            page.open(
                ft.SnackBar(
                    content=ft.Text(
                        f"Erro ao excluir vitória: {str(ex)}", color=ft.Colors.WHITE
                    ),
                    bgcolor=ft.Colors.RED,
                    action="OK",
                    action_color=ft.Colors.WHITE,
                )
            )

    def post_victory(e):
        if user_id == "default_user":
            page.open(
                ft.SnackBar(
                    content=ft.Text(
                        "Você precisa estar logado para postar!", color=ft.Colors.WHITE
                    ),
                    bgcolor=ft.Colors.RED,
                    action="OK",
                    action_color=ft.Colors.WHITE,
                )
            )
            return

        victory_text = victory_input.value.strip()
        selected_cat = category_dropdown.value
        if not victory_text or not selected_cat:
            page.open(
                ft.SnackBar(
                    content=ft.Text("Preencha todos os campos!", color=ft.Colors.WHITE),
                    bgcolor=ft.Colors.RED,
                    action="OK",
                    action_color=ft.Colors.WHITE,
                )
            )
            return

        if len(victory_text) > 200:
            page.open(
                ft.SnackBar(
                    content=ft.Text(
                        "Limite de 200 caracteres excedido!", color=ft.Colors.WHITE
                    ),
                    bgcolor=ft.Colors.RED,
                    action="OK",
                    action_color=ft.Colors.WHITE,
                )
            )
            return

        try:
            supabase_service.table("victories").insert(
                {
                    "user_id": user_id,
                    "content": victory_text,
                    "created_at": datetime.utcnow().isoformat() + "Z",
                }
            ).execute()
            victory_input.value = ""
            category_dropdown.value = None
            update_victories(selected_category)
            send_notification(
                page,
                "Vitória Postada!",
                "Sua conquista foi compartilhada com a comunidade!",
            )
            page.open(
                ft.SnackBar(
                    content=ft.Text(
                        "Vitória postada com sucesso!", color=ft.Colors.WHITE
                    ),
                    bgcolor=ft.Colors.GREEN_400,
                    action="OK",
                    action_color=ft.Colors.WHITE,
                )
            )
        except Exception as ex:
            logger.error(f"Erro ao postar vitória: {str(ex)}")
            page.open(
                ft.SnackBar(
                    content=ft.Text(
                        f"Erro ao postar vitória: {str(ex)}", color=ft.Colors.WHITE
                    ),
                    bgcolor=ft.Colors.RED,
                    action="OK",
                    action_color=ft.Colors.WHITE,
                )
            )

    # Configura os Chips de filtro
    def category_selected(e):
        nonlocal selected_category
        selected_category = e.control.label.value
        filter_chips.controls = [
            ft.Chip(
                label=ft.Text(value=cat, overflow=ft.TextOverflow.ELLIPSIS),
                selected=cat == selected_category,
                on_select=category_selected,
                show_checkmark=True,
                shape=ft.StadiumBorder(),
                col={"xs": 4, "sm": 3, "md": 2},
            )
            for cat in categories
        ]
        update_victories(selected_category)

    for category in categories:
        filter_chips.controls.append(
            ft.Chip(
                label=ft.Text(category, overflow=ft.TextOverflow.ELLIPSIS),
                selected=category == "Todas",
                on_select=category_selected,
                show_checkmark=True,
                shape=ft.StadiumBorder(),
                col={"xs": 4, "sm": 3, "md": 2},
            )
        )

    # Formulário para postar vitórias
    victory_input = ft.TextField(
        label="Compartilhe sua vitória!",
        multiline=True,
        max_lines=3,
        max_length=200,
    )
    category_dropdown = ft.Dropdown(
        label="Categoria",
        options=[ft.dropdown.Option(cat) for cat in categories[:-1]],
    )
    post_button = ft.ElevatedButton(
        text="Postar",
        icon=ft.Icons.SEND,
        on_click=post_victory,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=5),
        ),
    )

    # Carrega vitórias iniciais
    update_victories()

    return ft.Column(
        controls=[
            ft.ResponsiveRow(
                controls=[
                    ft.Container(
                        content=ft.Text(
                            "Compartilhe sua vitória!",
                            size=24,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.PRIMARY,
                        ),
                        padding=5,
                        col=12,
                        alignment=ft.alignment.center,
                    ),
                    ft.Container(
                        content=victory_input,
                        padding=5,
                        col={"xs": 8, "sm": 8, "md": 6},
                        alignment=ft.alignment.center,
                    ),
                    ft.Container(
                        content=category_dropdown,
                        padding=5,
                        col={"xs": 4, "sm": 6, "md": 4},
                        alignment=ft.alignment.center,
                    ),
                    ft.Container(
                        content=post_button,
                        padding=5,
                        col=8,
                        alignment=ft.alignment.center,
                    ),
                    ft.Container(
                        content=filter_chips,
                        padding=5,
                        col=12,
                        alignment=ft.alignment.center,
                    ),
                    ft.Container(
                        content=ft.Text(
                            "Vitórias da Comunidade",
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.PRIMARY,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                        padding=5,
                        col=12,
                        alignment=ft.alignment.center,
                    ),
                    ft.Container(
                        content=victories_grid,
                        padding=10,
                        col={"xs": 12, "sm": 10, "md": 8},
                        alignment=ft.alignment.center,
                        expand=True,
                    ),
                ],
                spacing=10,
                run_spacing=10,
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        ],
        spacing=15,
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        alignment=ft.MainAxisAlignment.START,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )
