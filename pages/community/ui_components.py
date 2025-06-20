import flet as ft
from datetime import datetime
from .models import Victory
from components.components import AvatarComponent


class VictoryCard:
    """Componente para exibir um card de vitória"""

    def __init__(
        self,
        victory: Victory,
        user_id: str,
        on_like_click,
        on_delete_click,
        on_details_click,
    ):
        self.victory = victory
        self.user_id = user_id
        self.on_like_click = on_like_click
        self.on_delete_click = on_delete_click
        self.on_details_click = on_details_click

    def build(self) -> ft.Card:
        """Constrói o card da vitória"""
        delete_button = self._create_delete_button()
        like_button = self._create_like_button()
        card_container = self._create_card_container(delete_button, like_button)

        return ft.Card(
            elevation=5,
            content=card_container,
            margin=ft.margin.symmetric(vertical=5, horizontal=10),
        )

    def _create_delete_button(self):
        """Cria o botão de deletar se o usuário for o autor"""
        if (
            self.victory.id
            and self.victory.user_id == self.user_id
            and self.user_id != "supafit_user"
        ):
            return ft.IconButton(
                icon=ft.Icons.DELETE_OUTLINE,
                icon_color=ft.Colors.RED_400,
                tooltip="Excluir sua vitória",
                on_click=lambda e: self.on_delete_click(self.victory.id),
            )
        return None

    def _create_like_button(self):
        """Cria o botão de curtir"""
        return ft.Row(
            [
                ft.IconButton(
                    icon=(
                        ft.Icons.FAVORITE
                        if self.victory.liked
                        else ft.Icons.FAVORITE_BORDER
                    ),
                    icon_color=ft.Colors.RED_400,
                    tooltip="Curtir",
                    on_click=lambda e: (
                        self.on_like_click(self.victory.id, self.victory.liked)
                        if self.victory.id
                        else None
                    ),
                ),
                ft.Text(f"{self.victory.likes}", color=ft.Colors.PRIMARY),
            ],
            spacing=5,
        )

    def _create_card_container(self, delete_button, like_button):
        """Cria o container principal do card"""
        card_container = ft.Container(
            content=ft.Column(
                [
                    ft.ListTile(
                        leading=AvatarComponent(
                            self.victory.user_id, radius=20, is_trainer=False
                        ),
                        title=ft.Text(
                            self.victory.author_name,
                            weight=ft.FontWeight.BOLD,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                        subtitle=ft.Text(
                            self.victory.get_formatted_date(),
                            size=12,
                        ),
                        trailing=delete_button,
                    ),
                    ft.Container(
                        content=ft.Text(
                            self.victory.content,
                            size=16,
                            overflow=ft.TextOverflow.ELLIPSIS,
                            max_lines=3,
                        ),
                        padding=ft.padding.symmetric(horizontal=15),
                    ),
                    ft.Row(
                        [
                            ft.Chip(
                                label=ft.Text(self.victory.category),
                                shape=ft.StadiumBorder(),
                            ),
                            like_button,
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
            on_click=lambda e: self.on_details_click(self.victory),
            alignment=ft.alignment.center,
            on_hover=lambda e: setattr(
                card_container, "elevation", 10 if e.data == "true" else 5
            ),
        )
        return card_container


class VictoryDetailsDialog:
    """Dialog para exibir detalhes de uma vitória"""

    def __init__(self, victory: Victory, page: ft.Page):
        self.victory = victory
        self.page = page

    def show(self):
        """Exibe o dialog com os detalhes da vitória"""
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(
                f"Vitória de {self.victory.author_name}",
                color=ft.Colors.PRIMARY,
                overflow=ft.TextOverflow.ELLIPSIS,
            ),
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text(
                            f"Categoria: {self.victory.category}",
                            size=14,
                        ),
                        ft.Container(
                            content=ft.ListView(
                                controls=[
                                    ft.Text(
                                        self.victory.content,
                                        size=16,
                                        color=ft.Colors.PRIMARY,
                                    )
                                ],
                                auto_scroll=True,
                            ),
                        ),
                        ft.Text(
                            f"Data: {self.victory.get_formatted_date()}",
                            size=12,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
            ),
            actions=[
                ft.TextButton(
                    "Fechar",
                    on_click=lambda e: self.page.close(dialog),
                ),
            ],
        )
        self.page.open(dialog)


class CategoryFilter:
    """Componente para filtros de categoria"""

    def __init__(self, categories: list, selected_category: str, on_category_select):
        self.categories = categories
        self.selected_category = selected_category
        self.on_category_select = on_category_select

    def build(self) -> ft.ResponsiveRow:
        """Constrói o componente de filtro"""
        filter_chips = ft.ResponsiveRow(
            spacing=10, alignment=ft.MainAxisAlignment.CENTER
        )

        for category in self.categories:
            filter_chips.controls.append(
                ft.Chip(
                    label=ft.Text(category, overflow=ft.TextOverflow.ELLIPSIS),
                    selected=category == self.selected_category,
                    on_select=self.on_category_select,
                    show_checkmark=True,
                    shape=ft.StadiumBorder(),
                    col={"xs": 4, "sm": 3, "md": 2},
                )
            )

        return filter_chips


class VictoryForm:
    """Formulário para criar novas vitórias"""

    def __init__(self, categories: list, on_post_victory):
        self.categories = categories[:-1]  # Remove "Todas"
        self.on_post_victory = on_post_victory
        self.victory_input = self._create_victory_input()
        self.category_dropdown = self._create_category_dropdown()
        self.post_button = self._create_post_button()

    def _create_victory_input(self):
        """Cria o campo de texto para a vitória"""
        return ft.TextField(
            label="Compartilhe sua vitória!",
            multiline=True,
            max_lines=3,
            max_length=200,
        )

    def _create_category_dropdown(self):
        """Cria o dropdown de categorias"""
        return ft.Dropdown(
            label="Categoria",
            options=[ft.dropdown.Option(cat) for cat in self.categories],
        )

    def _create_post_button(self):
        """Cria o botão de postar"""
        return ft.ElevatedButton(
            text="Postar",
            icon=ft.Icons.SEND,
            on_click=self.on_post_victory,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=5),
            ),
        )

    def get_form_data(self) -> tuple[str, str]:
        """Retorna os dados do formulário"""
        return self.victory_input.value.strip(), self.category_dropdown.value

    def clear_form(self):
        """Limpa o formulário"""
        self.victory_input.value = ""
        self.category_dropdown.value = None

    def build_form_layout(self) -> list:
        """Constrói o layout do formulário"""
        return [
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
                content=self.victory_input,
                padding=5,
                col={"xs": 8, "sm": 8, "md": 6},
                alignment=ft.alignment.center,
            ),
            ft.Container(
                content=self.category_dropdown,
                padding=5,
                col={"xs": 4, "sm": 6, "md": 4},
                alignment=ft.alignment.center,
            ),
            ft.Container(
                content=self.post_button,
                padding=5,
                col=8,
                alignment=ft.alignment.center,
            ),
        ]


class SnackBarHelper:
    """Classe auxiliar para exibir mensagens"""

    @staticmethod
    def show_success(page: ft.Page, message: str):
        """Exibe uma mensagem de sucesso"""
        page.open(
            ft.SnackBar(
                content=ft.Text(message, color=ft.Colors.WHITE),
                bgcolor=ft.Colors.GREEN_400,
                action="OK",
                action_color=ft.Colors.WHITE,
            )
        )

    @staticmethod
    def show_error(page: ft.Page, message: str):
        """Exibe uma mensagem de erro"""
        page.open(
            ft.SnackBar(
                content=ft.Text(message, color=ft.Colors.WHITE),
                bgcolor=ft.Colors.RED_400,
                action="OK",
                action_color=ft.Colors.WHITE,
            )
        )

    @staticmethod
    def show_warning(page: ft.Page, message: str):
        """Exibe uma mensagem de aviso"""
        page.open(
            ft.SnackBar(
                content=ft.Text(message, color=ft.Colors.WHITE),
                bgcolor=ft.Colors.ORANGE_400,
                action="OK",
                action_color=ft.Colors.WHITE,
            )
        )
