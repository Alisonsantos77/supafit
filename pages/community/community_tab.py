import flet as ft
import logging
from .controller import CommunityController, SnackBarHelper
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
    """Aba da comunidade - interface principal"""

    # Inicializa o controller
    controller = CommunityController(page, supabase_service)

    # Componentes da UI
    victories_grid = ft.GridView(
        expand=True,
        runs_count=2,
        max_extent=400,
        child_aspect_ratio=1.0,
        spacing=10,
        run_spacing=10,
        padding=10,
    )

    def handle_category_select(e):
        """Handler para seleção de categoria"""
        selected_category = e.control.label.value

        # Atualiza o filtro visual
        category_filter.selected_category = selected_category
        filter_chips = category_filter.build()

        # Encontra o container do filtro e atualiza
        for control in page.controls:
            if hasattr(control, "controls"):
                for responsive_row in control.controls:
                    if hasattr(responsive_row, "controls"):
                        for container in responsive_row.controls:
                            if (
                                hasattr(container, "content")
                                and hasattr(container.content, "controls")
                                and len(container.content.controls) > 0
                                and hasattr(container.content.controls[0], "label")
                            ):
                                container.content = filter_chips
                                break

        update_victories(selected_category)

    def handle_post_victory():
        """Handler para postar vitória"""
        content, category = victory_form.get_form_data()

        if controller.create_victory(content, category):
            victory_form.clear_form()
            update_victories(controller.get_selected_category())

    def handle_like_click(victory_id: str, currently_liked: bool):
        """Handler para curtir/descurtir"""
        if controller.toggle_like(victory_id, currently_liked):
            update_victories(controller.get_selected_category())

    def handle_delete_victory(victory_id: str):
        """Handler para deletar vitória"""
        success, message = controller.delete_victory(victory_id, controller.get_current_user_id())
        if success:
            SnackBarHelper.show_success(page, "Vitória deletada com sucesso!")
            update_victories(controller.get_selected_category())
        else:
            SnackBarHelper.show_error(page, message)

    def handle_show_details(victory):
        """Handler para exibir detalhes da vitória"""
        dialog = VictoryDetailsDialog(victory, page)
        dialog.show()


    def update_victories(category: str = "Todas"):
        """Atualiza a lista de vitórias"""
        try:
            victories_grid.controls.clear()  # Limpa a grade antes de recarregar
            victories = controller.load_victories(category)

            if not victories:
                logger.info(f"Nenhuma vitória encontrada para a categoria: {category}")
                victories_grid.controls.append(
                    ft.Text("Nenhuma vitória encontrada.", size=16, color=ft.Colors.GREY)
                )
            else:
                for victory in victories:
                    card = VictoryCard(
                        victory=victory,
                        user_id=controller.get_current_user_id(),
                        on_like_click=handle_like_click,
                        on_delete_click=handle_delete_victory,
                        on_details_click=handle_show_details,
                    )
                    victories_grid.controls.append(card.build())

            page.update()
            logger.info(
                f"Interface atualizada com {len(victories)} vitórias para a categoria {category}"
            )
        except Exception as e:
            logger.error(f"Erro ao atualizar vitórias: {str(e)}")
            
        
    # Inicializa os componentes após definir os handlers
    categories = controller.get_categories()
    victory_form = VictoryForm(categories, lambda e: handle_post_victory())
    category_filter = CategoryFilter(
        categories, controller.get_selected_category(), handle_category_select
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
                    *victory_form.build_form_layout(),
                    ft.Container(
                        content=category_filter.build(),
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
