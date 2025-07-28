import flet as ft
import logging

from utils.alerts import CustomSnackBar
from .controller import CommunityController
from .ui_components import (
    VictoryCard,
    VictoryDetailsDialog,
    CategoryFilter,
    VictoryForm,
)

logger = logging.getLogger("supafit.community")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


def CommunityTab(page: ft.Page, supabase_service):
    """Aba da comunidade com design profissional e minimalista."""
    controller = CommunityController(page, supabase_service)

    def handle_category_select(e):
        selected_category = e.control.label.value
        category_filter.selected_category = selected_category
        filter_container.content = category_filter.build()
        update_victories(selected_category)
        page.update()

    def handle_post_victory():
        content, category = victory_form.get_form_data()
        if controller.create_victory(content, category):
            victory_form.clear_form()
            update_victories(controller.get_selected_category())
            page.open(
                ft.SnackBar(
                    ft.Text("Vitória postada com sucesso!"),
                    bgcolor=ft.Colors.GREEN_600,
                )
            )
            page.update()

    def handle_like_click(victory_id: str, currently_liked: bool):
        logger.info(
            f"[LIKE_CLICK] Vitória: {victory_id}, Liked atualmente: {currently_liked}"
        )
        if controller.toggle_like(victory_id, currently_liked):
            logger.info(
                f"[LIKE_SUCCESS] Toggle executado com sucesso para {victory_id}"
            )
            update_victories(controller.get_selected_category())
        else:
            logger.error(f"[LIKE_FAIL] Falha ao alternar like para {victory_id}")

    def handle_delete_victory(victory_id: str):
        success, message = controller.delete_victory(
            victory_id, controller.get_current_user_id()
        )
        if success:
            page.open(
                ft.SnackBar(
                    ft.Text("Vitória deletada com sucesso!"),
                    bgcolor=ft.Colors.GREEN_600,
                )
            )
            page.update()
            update_victories(controller.get_selected_category())
        else:
            page.open(
                ft.SnackBar(
                    ft.Text(f"Erro ao deletar vitória: {message}"),
                    bgcolor=ft.Colors.RED_600,
                )
            )
            page.update()

    def handle_show_details(victory):
        dialog = VictoryDetailsDialog(victory, page)
        dialog.show()

    def update_victories(category: str = "Todas"):
        try:
            victories_list.controls.clear()
            victories = controller.load_victories(category)

            if not victories:
                # Estado vazio melhorado
                empty_state = ft.Container(
                    content=ft.Column(
                        [
                            ft.Icon(
                                ft.Icons.CELEBRATION_OUTLINED,
                                size=48,
                                color=ft.Colors.GREY_400,
                            ),
                            ft.Text(
                                "Nenhuma vitória encontrada",
                                size=16,
                                weight=ft.FontWeight.W_500,
                                color=ft.Colors.GREY_600,
                            ),
                            ft.Text(
                                "Seja o primeiro a compartilhar uma conquista!",
                                size=12,
                                color=ft.Colors.GREY_500,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=8,
                    ),
                    padding=ft.padding.all(40),
                    expand=True,
                    alignment=ft.alignment.center,
                )
                victories_list.controls.append(empty_state)
            else:
                for victory in victories:
                    card = VictoryCard(
                        victory=victory,
                        user_id=controller.get_current_user_id(),
                        on_like_click=handle_like_click,
                        on_delete_click=handle_delete_victory,
                        on_details_click=handle_show_details,
                        page=page,
                    )
                    victories_list.controls.append(card.build())

            page.update()
            logger.info(
                f"Interface atualizada com {len(victories)} vitórias para a categoria {category}"
            )
        except Exception as e:
            logger.error(f"Erro ao atualizar vitórias: {str(e)}")
            if page:
                page.open(
                    ft.SnackBar(
                        ft.Text(
                            "Erro ao carregar vitórias. Tente novamente mais tarde."
                        ),
                        bgcolor=ft.Colors.RED_600,
                    )
                )
                page.update()
            else:
                logger.error("Page não disponível para exibir SnackBar")

    # Componentes principais
    victories_list = ft.ListView(
        expand=True,
        spacing=12,
        padding=ft.padding.symmetric(horizontal=16, vertical=8),
        auto_scroll=True,
        animate_opacity=ft.Animation(300, ft.AnimationCurve.EASE_IN_OUT),
    )

    victory_form = VictoryForm(
        controller.get_categories(), lambda e: handle_post_victory(), page
    )

    category_filter = CategoryFilter(
        controller.get_categories(),
        controller.get_selected_category(),
        handle_category_select,
    )

    filter_container = ft.Container(
        content=category_filter.build(),
        padding=ft.padding.symmetric(horizontal=16, vertical=8),
    )

    # Carrega as vitórias iniciais
    update_victories()

    # Layout principal responsivo
    return ft.Container(
        content=ft.Column(
            controls=[
                # Formulário de postagem
                ft.Container(
                    content=ft.Column(
                        victory_form.build_form_layout(),
                        spacing=0,
                    ),
                    padding=ft.padding.symmetric(horizontal=16, vertical=16),
                ),
                # Filtros de categoria
                filter_container,
                # Linha divisória
                ft.Divider(height=1, color=ft.Colors.GREY_200),
                # Lista de vitórias
                ft.Container(
                    content=victories_list,
                    expand=True,
                    animate_opacity=ft.Animation(400, ft.AnimationCurve.EASE_IN_OUT),
                ),
            ],
            expand=True,
            spacing=0,
        ),
        expand=True,
    )
