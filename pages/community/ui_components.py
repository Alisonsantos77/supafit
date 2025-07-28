import flet as ft
from datetime import datetime
from .models import Victory
from components.components import AvatarComponent
from utils.alerts import CustomSnackBar
from pages.auth.utils.animations import (
    AnimationPresets,
    AnimationHelpers,
    SnackbarAnimations,
    DialogAnimations,
)

category_Colors = {
    "Força": ft.Colors.RED_500,
    "Resistência": ft.Colors.BLUE_500,
    "Disciplina": ft.Colors.PURPLE_500,
    "Nutrição": ft.Colors.GREEN_500,
}

category_text_Colors = {
    "Força": ft.Colors.RED_700,
    "Resistência": ft.Colors.BLUE_700,
    "Disciplina": ft.Colors.PURPLE_700,
    "Nutrição": ft.Colors.GREEN_700,
}


class VictoryCard:
    """Card de vitória com animações profissionais e design minimalista."""

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

    def build(self) -> ft.Dismissible:
        like_icon = ft.IconButton(
            icon=ft.Icons.FAVORITE_BORDER,
            selected_icon=ft.Icons.FAVORITE,
            selected=self.victory.liked,
            style=ft.ButtonStyle(
                color={
                    "selected": ft.Colors.RED_500,
                    "": ft.Colors.GREY_500,
                },
            ),
            icon_size=18,
            animate_scale=AnimationPresets.elastic_in(),
            on_click=lambda e: self._handle_like_with_animation(e),
        )

        content = ft.Container(
            content=ft.Column(
                [
                    ft.ListTile(
                        leading=AvatarComponent(
                            user_id=self.victory.user_id,
                            radius=18,
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
                            size=11,
                            color=ft.Colors.GREY_600,
                        ),
                        trailing=ft.Container(
                            content=ft.Text(
                                self.victory.category,
                                size=11,
                                weight=ft.FontWeight.W_500,
                                color=category_text_Colors.get(
                                    self.victory.category, ft.Colors.GREY_700
                                ),
                            ),
                            border=ft.border.all(
                                1,
                                category_Colors.get(
                                    self.victory.category, ft.Colors.GREY_400
                                ),
                            ),
                            border_radius=12,
                            padding=ft.padding.symmetric(horizontal=8, vertical=4),
                            animate_scale=AnimationPresets.button_hover(),
                        ),
                        content_padding=ft.padding.symmetric(horizontal=16, vertical=8),
                    ),
                    ft.Container(
                        content=ft.Text(
                            self.victory.content,
                            size=14,
                            max_lines=3,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                        padding=ft.padding.symmetric(horizontal=16, vertical=8),
                    ),
                    ft.Container(
                        content=ft.Row(
                            [
                                like_icon,
                                ft.Text(
                                    str(self.victory.likes),
                                    size=12,
                                    color=ft.Colors.GREY_600,
                                ),
                                ft.Container(width=16),
                                ft.IconButton(
                                    icon=ft.Icons.VISIBILITY,
                                    icon_size=18,
                                    tooltip="Ver detalhes",
                                    animate_scale=AnimationPresets.button_hover(),
                                    on_click=lambda e: self.on_details_click(
                                        self.victory
                                    ),
                                ),
                                ft.Text(
                                    "Ver mais",
                                    size=12,
                                    color=ft.Colors.GREY_600,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.START,
                        ),
                        padding=ft.padding.symmetric(horizontal=16, vertical=8),
                    ),
                ],
                spacing=0,
            ),
            border=ft.border.all(1, ft.Colors.GREY_200),
            border_radius=8,
            animate_scale=AnimationPresets.slide_in(),
            animate_opacity=AnimationPresets.fade_in(),
            on_hover=self._handle_hover,
        )

        def handle_confirm_dismiss(e: ft.DismissibleDismissEvent):
            if (
                e.direction == ft.DismissDirection.END_TO_START
                and self.victory.user_id == self.user_id
            ):
                self._show_delete_dialog()
                return False
            else:
                self._show_unauthorized_dialog()
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
                content=ft.Row(
                    [
                        ft.Icon(ft.Icons.DELETE_OUTLINE, color=ft.Colors.RED_600),
                        ft.Text(
                            "Excluir",
                            color=ft.Colors.RED_600,
                            weight=ft.FontWeight.W_500,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.END,
                    spacing=8,
                ),
                padding=ft.padding.all(16),
                animate_opacity=AnimationPresets.fade_in(AnimationPresets.FAST),
            ),
            on_confirm_dismiss=handle_confirm_dismiss,
            dismiss_thresholds={ft.DismissDirection.END_TO_START: 0.2},
        )

    def _handle_like_with_animation(self, e):
        """Manipula o clique do like com animação de feedback"""
        AnimationHelpers.animate_button_click(e.control, self.page)
        self.on_like_click(self.victory.id, e.control.selected)

    def _handle_hover(self, e):
        """Aplica efeito hover com animação suave"""
        e.control.scale = 1.02 if e.data == "true" else 1.0
        e.control.update()

    def _show_delete_dialog(self):
        """Exibe diálogo de confirmação de exclusão com animação"""
        dialog = ft.AlertDialog(
            title=ft.Text("Confirmar Exclusão"),
            content=ft.Text("Deseja realmente excluir esta vitória?"),
            actions=[
                ft.TextButton(
                    "Cancelar",
                    on_click=lambda e: self.page.close(dialog),
                    animate_scale=AnimationPresets.button_hover(),
                ),
                ft.FilledButton(
                    "Excluir",
                    on_click=lambda e: self._handle_delete_confirm(dialog),
                    animate_scale=AnimationPresets.button_hover(),
                ),
            ],
        )
        DialogAnimations.show_dialog_with_animation(self.page, dialog)

    def _show_unauthorized_dialog(self):
        """Exibe diálogo de ação não permitida com animação"""
        dialog = ft.AlertDialog(
            title=ft.Text("Ação Não Permitida"),
            content=ft.Text("Você só pode excluir suas próprias vitórias."),
            actions=[
                ft.TextButton(
                    "OK",
                    on_click=lambda e: self.page.close(dialog),
                    animate_scale=AnimationPresets.button_hover(),
                ),
            ],
        )
        DialogAnimations.show_dialog_with_animation(self.page, dialog)

    def _handle_delete_confirm(self, dialog):
        """Confirma a exclusão da vitória com feedback visual"""
        AnimationHelpers.animate_success_feedback(dialog.content, self.page)
        self.on_delete_click(self.victory.id)
        self.page.close(dialog)


class VictoryDetailsDialog:
    """Diálogo de detalhes da vitória com design limpo e animações."""

    def __init__(self, victory: Victory, page: ft.Page):
        self.victory = victory
        self.page = page

    def show(self):
        """Exibe o diálogo com animação de entrada"""
        dialog = ft.AlertDialog(
            title=ft.Row(
                [
                    AvatarComponent(
                        self.victory.user_id,
                        radius=16,
                        is_trainer=False,
                        user_name=self.victory.author_name,
                    ),
                    ft.Column(
                        [
                            ft.Text(
                                self.victory.author_name,
                                weight=ft.FontWeight.W_500,
                            ),
                            ft.Text(
                                self.victory.get_formatted_date(),
                                size=12,
                                color=ft.Colors.GREY_600,
                            ),
                        ],
                        spacing=2,
                    ),
                ],
                spacing=12,
            ),
            content=ft.Column(
                [
                    ft.Container(
                        content=ft.Text(
                            self.victory.category,
                            size=11,
                            weight=ft.FontWeight.W_500,
                            color=category_text_Colors.get(
                                self.victory.category, ft.Colors.GREY_700
                            ),
                        ),
                        border=ft.border.all(
                            1,
                            category_Colors.get(
                                self.victory.category, ft.Colors.GREY_400
                            ),
                        ),
                        border_radius=12,
                        padding=ft.padding.symmetric(horizontal=8, vertical=4),
                        alignment=ft.alignment.center,
                        animate_scale=AnimationPresets.bounce_in(),
                    ),
                    ft.Text(
                        self.victory.content,
                        size=14,
                        selectable=True,
                    ),
                ],
                spacing=16,
                tight=True,
            ),
            actions=[
                ft.TextButton(
                    "Fechar",
                    on_click=lambda e: self.page.close(dialog),
                    animate_scale=AnimationPresets.button_hover(),
                ),
            ],
        )
        DialogAnimations.show_dialog_with_animation(self.page, dialog)


class CategoryFilter:
    """Filtros de categoria com design minimalista e animações."""

    def __init__(self, categories: list, selected_category: str, on_category_select):
        self.categories = categories
        self.selected_category = selected_category
        self.on_category_select = on_category_select

    def build(self) -> ft.Container:
        """Constrói os chips de filtro com animações"""
        chips = []
        for category in self.categories:
            is_selected = category == self.selected_category
            chip = ft.Container(
                content=ft.Text(
                    category,
                    size=12,
                    weight=ft.FontWeight.W_500,
                    color=(
                        ft.Colors.WHITE
                        if is_selected
                        else category_text_Colors.get(category, ft.Colors.GREY_700)
                    ),
                ),
                bgcolor=(
                    category_Colors.get(category, ft.Colors.GREY_400)
                    if is_selected
                    else ft.Colors.GREY_50
                ),
                border=(
                    None
                    if is_selected
                    else ft.border.all(
                        1, category_Colors.get(category, ft.Colors.GREY_400)
                    )
                ),
                border_radius=16,
                padding=ft.padding.symmetric(horizontal=16, vertical=8),
                animate_scale=AnimationPresets.bounce_in(AnimationPresets.FAST),
                ink=True,
                on_click=lambda e, cat=category: self._handle_select(cat),
            )
            chips.append(chip)

        return ft.Container(
            content=ft.Row(
                controls=chips,
                wrap=True,
                spacing=8,
                run_spacing=8,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            alignment=ft.alignment.center,
            animate_opacity=AnimationPresets.fade_in(),
        )

    def _handle_select(self, category):
        """Manipula a seleção de categoria com feedback visual"""

        class MockEvent:
            def __init__(self, category):
                self.control = MockControl(category)

        class MockControl:
            def __init__(self, category):
                self.label = MockLabel(category)

        class MockLabel:
            def __init__(self, category):
                self.value = category

        self.on_category_select(MockEvent(category))


class VictoryForm:
    """Formulário moderno para postar vitórias com animações."""

    def __init__(self, categories: list, on_post_victory, page: ft.Page):
        self.categories = categories[:-1]
        self.on_post_victory = on_post_victory
        self.page = page
        self.victory_input = ft.Ref[ft.TextField]()
        self.category_dropdown = ft.Ref[ft.Dropdown]()
        self.post_button = ft.Ref[ft.ElevatedButton]()
        self.char_counter = ft.Ref[ft.Text]()

    def build_form_layout(self) -> list:
        """Constrói o layout do formulário com animações"""

        def update_character_count(e=None):
            if self.victory_input.current and self.char_counter.current:
                current_length = len(self.victory_input.current.value or "")
                self.char_counter.current.value = f"{current_length}/50"
                self.char_counter.current.color = (
                    ft.Colors.RED_500 if current_length > 40 else ft.Colors.GREY_600
                )
                if current_length > 40:
                    AnimationHelpers.animate_form_error(
                        self.victory_input.current, self.page
                    )
                self.char_counter.current.update()
            self._update_button_state()

        def update_button_state(e=None):
            self._update_button_state()

        form_container = ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "Compartilhe sua vitória",
                        size=18,
                        weight=ft.FontWeight.W_600,
                    ),
                    ft.Column(
                        [
                            ft.TextField(
                                ref=self.victory_input,
                                label="Conte sobre sua conquista...",
                                multiline=True,
                                max_lines=3,
                                max_length=50,
                                border_radius=8,
                                filled=True,
                                on_change=update_character_count,
                                disabled=not self._is_authenticated(),
                                expand=True,
                                animate_opacity=AnimationPresets.fade_in(),
                            ),
                            ft.Row(
                                [
                                    ft.Text(
                                        ref=self.char_counter,
                                        value="0/50",
                                        size=11,
                                        color=ft.Colors.GREY_600,
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.END,
                            ),
                        ],
                        spacing=4,
                    ),
                    ft.Row(
                        [
                            ft.Dropdown(
                                ref=self.category_dropdown,
                                label="Categoria",
                                options=[
                                    ft.dropdown.Option(
                                        text=cat,
                                        key=cat,
                                    )
                                    for cat in self.categories
                                ],
                                border_radius=8,
                                filled=True,
                                width=150,
                                disabled=not self._is_authenticated(),
                                on_change=update_button_state,
                                animate_opacity=AnimationPresets.fade_in(
                                    AnimationPresets.SLOW
                                ),
                            ),
                            ft.ElevatedButton(
                                ref=self.post_button,
                                text="Publicar",
                                icon=ft.Icons.SEND,
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=8),
                                ),
                                on_click=self._handle_post_with_animation,
                                disabled=not self._is_authenticated(),
                                animate_scale=AnimationPresets.elastic_in(
                                    AnimationPresets.FAST
                                ),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Text(
                        "Faça login para compartilhar suas vitórias.",
                        size=12,
                        color=ft.Colors.GREY_600,
                        visible=not self._is_authenticated(),
                    ),
                ],
                spacing=16,
            ),
            border=ft.border.all(1, ft.Colors.GREY_200),
            border_radius=12,
            padding=ft.padding.all(20),
            animate_opacity=AnimationPresets.slide_in(),
        )

        AnimationHelpers.animate_container_entry(form_container, self.page, 0.2)
        return [form_container]

    def _handle_post_with_animation(self, e):
        """Manipula o envio do post com animações de feedback"""
        AnimationHelpers.animate_button_click(self.post_button.current, self.page)
        self.on_post_victory(e)

    def _update_button_state(self):
        """Atualiza o estado do botão com animações suaves"""
        if not all(
            [
                self.post_button.current,
                self.victory_input.current,
                self.category_dropdown.current,
            ]
        ):
            return

        is_authenticated = self._is_authenticated()
        has_content = bool(
            self.victory_input.current.value
            and self.victory_input.current.value.strip()
        )
        has_category = bool(self.category_dropdown.current.value)

        self.post_button.current.disabled = not (
            is_authenticated and has_content and has_category
        )
        self.victory_input.current.disabled = not is_authenticated
        self.category_dropdown.current.disabled = not is_authenticated

        self.post_button.current.update()
        self.victory_input.current.update()
        self.category_dropdown.current.update()

    def _is_authenticated(self) -> bool:
        """Verifica se o usuário está autenticado"""
        return bool(self.page.client_storage.get("supafit.user_id"))

    def get_form_data(self) -> tuple[str, str]:
        """Retorna os dados do formulário"""
        return (
            (
                self.victory_input.current.value.strip()
                if self.victory_input.current.value
                else ""
            ),
            self.category_dropdown.current.value or "",
        )

    def clear_form(self):
        """Limpa o formulário com feedback visual"""
        if self.victory_input.current:
            self.victory_input.current.value = ""
            AnimationHelpers.animate_success_feedback(
                self.victory_input.current, self.page
            )
            self.victory_input.current.update()
        if self.category_dropdown.current:
            self.category_dropdown.current.value = None
            self.category_dropdown.current.update()
        if self.char_counter.current:
            self.char_counter.current.value = "0/50"
            self.char_counter.current.color = ft.Colors.GREY_600
            self.char_counter.current.update()


class SnackBarHelper:
    """Helper para notificações com animações do SupaFit."""

    @staticmethod
    def show_success(page: ft.Page, message: str):
        """Exibe notificação de sucesso com animação"""
        SnackbarAnimations.show_animated_snackbar(
            page, message, "green", icon=ft.Icons.CHECK_CIRCLE
        )

    @staticmethod
    def show_error(page: ft.Page, message: str):
        """Exibe notificação de erro com animação"""
        SnackbarAnimations.show_animated_snackbar(
            page, message, "red", icon=ft.Icons.ERROR
        )

    @staticmethod
    def show_warning(page: ft.Page, message: str):
        """Exibe notificação de aviso com animação"""
        SnackbarAnimations.show_animated_snackbar(
            page, message, "orange", icon=ft.Icons.WARNING
        )
