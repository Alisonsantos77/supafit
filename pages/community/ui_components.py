import flet as ft
from datetime import datetime
from .models import Victory
from components.components import AvatarComponent
from utils.alerts import CustomSnackBar

category_Colors = {
    "Força": ft.Colors.RED_100,
    "Resistência": ft.Colors.BLUE_100,
    "Disciplina": ft.Colors.PURPLE_100,
    "Nutrição": ft.Colors.GREEN_100,
}

category_text_Colors = {
    "Força": ft.Colors.RED_800,
    "Resistência": ft.Colors.BLUE_800,
    "Disciplina": ft.Colors.PURPLE_800,
    "Nutrição": ft.Colors.GREEN_800,
}


class VictoryCard:
    """Card de vitória com visual profissional tipo Twitter/X."""

    def __init__(
        self,
        victory: Victory,
        user_id: str,
        on_like_click,
        on_delete_click,
        on_details_click,
        page: ft.Page,
    ):
        self.victory = victory
        self.user_id = user_id
        self.on_like_click = on_like_click
        self.on_delete_click = on_delete_click
        self.on_details_click = on_details_click
        self.page = page
        self.ref = ft.Ref[ft.Dismissible]()
        self.opacity = 1
        self.scale = 1

    def build(self) -> ft.Dismissible:
        content = ft.Container(
            content=ft.Column(
                [
                    ft.ListTile(
                        leading=AvatarComponent(
                            user_id=self.victory.user_id,
                            radius=20,
                            is_trainer=False,
                            user_name=self.victory.author_name,
                        ),
                        title=ft.Text(
                            self.victory.author_name,
                            size=14,
                            weight=ft.FontWeight.W_500,
                        ),
                        subtitle=ft.Text(
                            self.victory.get_formatted_date(),
                            size=12,
                        ),
                        trailing=ft.Chip(
                            label=ft.Text(
                                self.victory.category,
                                size=12,
                                color=category_text_Colors.get(
                                    self.victory.category, ft.Colors.PRIMARY
                                ),
                            ),
                            padding=ft.padding.symmetric(horizontal=8),
                            bgcolor=category_Colors.get(
                                self.victory.category, ft.Colors.GREY_200
                            ),
                        ),
                    ),
                    ft.Container(
                        content=ft.Text(
                            self.victory.content,
                            size=14,
                            max_lines=3,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                        padding=ft.padding.only(left=16, right=16, bottom=8),
                    ),
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.IconButton(
                                    icon=ft.Icons.FAVORITE_BORDER,
                                    selected_icon=ft.Icons.FAVORITE,
                                    selected=self.victory.liked,
                                    style=ft.ButtonStyle(
                                        color={
                                            "selected": ft.Colors.RED_500,
                                            "": ft.Colors.GREY_500,
                                        },
                                        animation_duration=200,
                                    ),
                                    icon_size=20,
                                    on_click=lambda e: self.on_like_click(
                                        self.victory.id, e.control.selected
                                    ),
                                ),
                                ft.Text(
                                    str(self.victory.likes),
                                    size=12,
                                ),
                                ft.Container(width=16),
                                ft.IconButton(
                                    icon=ft.Icons.COMMENT,
                                    icon_size=20,
                                    on_click=lambda e: self.on_details_click(
                                        self.victory
                                    ),
                                ),
                                ft.Text("Ver mais", size=12),
                            ],
                            alignment=ft.MainAxisAlignment.START,
                        ),
                        padding=ft.padding.only(left=16, right=16, bottom=8),
                    ),
                ],
                spacing=0,
            ),
            animate_opacity=ft.Animation(300, ft.AnimationCurve.EASE_IN_OUT),
            animate_scale=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
            on_click=lambda e: self.on_details_click(self.victory),
            on_hover=lambda e: setattr(
                content,
                "shadow",
                (
                    ft.BoxShadow(4, color=ft.Colors.GREY_300)
                    if e.data == "true"
                    else ft.BoxShadow(0)
                ),
            ),
        )

        def handle_close_modal(e):
            self.on_delete_click(self.victory.id)
            self.page.close(dialog)

        def show_unauthorized_dialog():
            unauthorized_dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("Ação Não Permitida"),
                content=ft.Text("Você só pode excluir suas próprias vitórias."),
                icon=ft.Icon(name=ft.Icons.WARNING, color=ft.Colors.RED, size=40),
                icon_padding=ft.padding.all(10),
                content_padding=ft.padding.symmetric(horizontal=30, vertical=20),
                actions=[
                    ft.TextButton(
                        "OK", on_click=lambda e: self.page.close(unauthorized_dialog)
                    ),
                ],
                actions_alignment=ft.MainAxisAlignment.CENTER,
            )
            self.page.open(unauthorized_dialog)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirmar Exclusão"),
            content=ft.Text("Deseja realmente excluir esta vitória?"),
            icon=ft.Icon(name=ft.Icons.WARNING, color=ft.Colors.RED, size=40),
            icon_padding=ft.padding.all(10),
            content_padding=ft.padding.symmetric(horizontal=30, vertical=20),
            actions=[
                ft.TextButton("Sim", on_click=handle_close_modal),
                ft.TextButton("Não", on_click=lambda e: self.page.close(dialog)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        def handle_confirm_dismiss(e: ft.DismissibleDismissEvent):
            if (
                e.direction == ft.DismissDirection.END_TO_START
                and self.victory.user_id == self.user_id
            ):
                self.page.open(dialog)
                return False
            else:
                show_unauthorized_dialog()
                return False

        return ft.Dismissible(
            ref=self.ref,
            content=content,
            dismiss_direction=(
                ft.DismissDirection.END_TO_START
                if self.victory.user_id == self.user_id
                else None
            ),
            background=ft.Container(
                bgcolor=ft.Colors.RED_100,
                content=ft.Row(
                    [
                        ft.Icon(ft.Icons.DELETE, color=ft.Colors.RED_800),
                        ft.Text("Excluir", color=ft.Colors.RED_800),
                    ],
                    alignment=ft.MainAxisAlignment.END,
                    spacing=8,
                ),
                padding=ft.padding.all(16),
            ),
            on_confirm_dismiss=handle_confirm_dismiss,
            dismiss_thresholds={ft.DismissDirection.END_TO_START: 0.2},
        )


class VictoryDetailsDialog:
    """Diálogo com estilo baseado no exemplo com ícone, usando avatar do autor."""

    def __init__(self, victory: Victory, page: ft.Page):
        self.victory = victory
        self.page = page

    def show(self):
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(self.victory.author_name),
            icon=AvatarComponent(self.victory.user_id, radius=20, is_trainer=False),
            icon_padding=ft.padding.all(10),
            content=ft.Text(
                self.victory.content,
                size=14,
                selectable=True,
            ),
            content_padding=ft.padding.symmetric(horizontal=30, vertical=20),
            actions=[
                ft.TextButton("Fechar", on_click=lambda e: self.page.close(dialog)),
            ],
            actions_alignment=ft.MainAxisAlignment.CENTER,
        )

        self.page.open(dialog)


class CategoryFilter:
    """Filtros de categoria com chips profissionais."""

    def __init__(self, categories: list, selected_category: str, on_category_select):
        self.categories = categories
        self.selected_category = selected_category
        self.on_category_select = on_category_select

    def build(self) -> ft.Container:
        chips = [
            ft.Chip(
                label=ft.Text(
                    category,
                    size=12,
                    color=(
                        ft.Colors.WHITE
                        if category == self.selected_category
                        else category_text_Colors.get(category, ft.Colors.GREY_800)
                    ),
                ),
                selected=category == self.selected_category,
                on_select=self.on_category_select,
                bgcolor=(
                    ft.Colors.GREY_900
                    if category == self.selected_category
                    else category_Colors.get(category, ft.Colors.GREY_200)
                ),
                padding=ft.padding.symmetric(horizontal=12),
                animate_scale=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
            )
            for category in self.categories
        ]
        return ft.Container(
            content=ft.Row(
                controls=chips,
                wrap=True,
                spacing=8,
                run_spacing=8,
                alignment=ft.MainAxisAlignment.CENTER,
            )
        )


class VictoryForm:
    """Formulário profissional para postar vitórias."""

    def __init__(self, categories: list, on_post_victory, page: ft.Page):
        self.categories = categories[:-1]
        self.on_post_victory = on_post_victory
        self.page = page
        self.victory_input = ft.Ref[ft.TextField]()
        self.category_dropdown = ft.Ref[ft.Dropdown]()
        self.post_button = ft.Ref[ft.ElevatedButton]()

    def build_form_layout(self) -> list:
        def update_button_state(e=None):
            """Atualiza o estado do botão com base no conteúdo e autenticação."""
            if not self.post_button.current:  # Verifica se o botão foi adicionado
                return
            is_authenticated = self.page.client_storage.get("supafit.user_id")
            has_content = (
                self.victory_input.current.value.strip()
                if self.victory_input.current
                else False
            )
            self.post_button.current.disabled = not (is_authenticated and has_content)
            self.victory_input.current.disabled = not is_authenticated
            self.category_dropdown.current.disabled = not is_authenticated
            self.post_button.current.update()
            self.victory_input.current.update()
            self.category_dropdown.current.update()

        form = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "Compartilhe sua vitória",
                        size=16,
                        weight=ft.FontWeight.W_500,
                    ),
                    ft.ResponsiveRow(
                        [
                            ft.TextField(
                                ref=self.victory_input,
                                label="Conte sobre sua conquista... (máx. 50 caracteres)",
                                multiline=True,
                                max_lines=3,
                                max_length=50,
                                border_radius=8,
                                filled=True,
                                on_change=update_button_state,
                                animate_opacity=ft.Animation(
                                    300, ft.AnimationCurve.EASE_IN_OUT
                                ),
                                disabled=not self.page.client_storage.get(
                                    "supafit.user_id"
                                ),
                                col={"sm": 12, "md": 8, "lg": 6},
                            ),
                            ft.Container(
                                content=ft.Row(
                                    [
                                        ft.Dropdown(
                                            ref=self.category_dropdown,
                                            label="Categoria",
                                            options=[
                                                ft.dropdown.Option(cat)
                                                for cat in self.categories
                                            ],
                                            border_radius=8,
                                            filled=True,
                                            width=150,
                                            disabled=not self.page.client_storage.get(
                                                "supafit.user_id"
                                            ),
                                        ),
                                        ft.ElevatedButton(
                                            ref=self.post_button,
                                            text="Publicar",
                                            icon=ft.Icons.SEND,
                                            style=ft.ButtonStyle(
                                                elevation=2,
                                                shape=ft.RoundedRectangleBorder(
                                                    radius=5
                                                ),
                                            ),
                                            on_click=self.on_post_victory,
                                            animate_scale=ft.Animation(
                                                200, ft.AnimationCurve.EASE_OUT
                                            ),
                                            disabled=not self.page.client_storage.get(
                                                "supafit.user_id"
                                            ),
                                        ),
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                ),
                                padding=ft.padding.only(top=8),
                                col={"sm": 12, "md": 4, "lg": 6},
                            ),
                        ]
                    ),
                    ft.Text(
                        "Faça login para compartilhar suas vitórias.",
                        size=12,
                        visible=not self.page.client_storage.get("supafit.user_id"),
                    ),
                ],
                spacing=8,
            ),
            col=12,
            padding=ft.padding.all(16),
        )

        return [form]

    def get_form_data(self) -> tuple[str, str]:
        return (
            self.victory_input.current.value.strip(),
            self.category_dropdown.current.value,
        )

    def clear_form(self):
        self.victory_input.current.value = ""
        self.category_dropdown.current.value = None
        self.victory_input.current.update()


class SnackBarHelper:
    """Helper para notificações."""

    @staticmethod
    def show_success(page: ft.Page, message: str):
        CustomSnackBar(
            message, bgcolor=ft.Colors.GREEN_600, color=ft.Colors.WHITE
        ).show(page)

    @staticmethod
    def show_error(page: ft.Page, message: str):
        CustomSnackBar(message, bgcolor=ft.Colors.RED_600, color=ft.Colors.WHITE).show(
            page
        )

    @staticmethod
    def show_warning(page: ft.Page, message: str):
        CustomSnackBar(message, bgcolor=ft.Colors.BLUE_600, color=ft.Colors.WHITE).show(
            page
        )
