import flet as ft
from typing import Dict, Any, Callable
from services.supabase import SupabaseService
from utils.logger import get_logger
from utils.alerts import CustomSnackBar

logger = get_logger("supafit.profile_settings")


class ProfileFieldComponents:
    """Componentes de campos do perfil com estética moderna."""

    @staticmethod
    def create_text_field(
        label: str,
        value: str = "",
        read_only: bool = False,
        keyboard_type: ft.KeyboardType = ft.KeyboardType.TEXT,
        expand: bool = False,
        disabled: bool = False,
    ) -> ft.TextField:
        """Cria um campo de texto com design moderno."""
        return ft.TextField(
            label=label,
            value=value,
            read_only=read_only,
            keyboard_type=keyboard_type,
            border=ft.InputBorder.OUTLINE,
            border_color=ft.Colors.TRANSPARENT,
            focused_border_color=ft.Colors.BLUE_400,
            filled=True,
            fill_color=ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
            color=ft.Colors.ON_SURFACE,
            label_style=ft.TextStyle(color=ft.Colors.ON_SURFACE_VARIANT, size=12),
            text_style=ft.TextStyle(size=14),
            border_radius=12,
            content_padding=ft.padding.all(16),
            expand=expand,
            disabled=disabled,
        )

    @staticmethod
    def create_dropdown(label: str, value: str, options: list) -> ft.Dropdown:
        """Cria um dropdown com design moderno."""
        return ft.Dropdown(
            label=label,
            value=value,
            options=options,
            border=ft.InputBorder.OUTLINE,
            border_color=ft.Colors.TRANSPARENT,
            focused_border_color=ft.Colors.BLUE_400,
            filled=True,
            fill_color=ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
            color=ft.Colors.ON_SURFACE,
            border_radius=12,
            content_padding=ft.padding.all(16),
            text_style=ft.TextStyle(size=14),
        )

    @staticmethod
    def create_switch(label: str, value: bool) -> ft.Switch:
        """Cria um switch com design moderno."""
        return ft.Switch(
            value=value,
            active_color=ft.Colors.BLUE_400,
            inactive_thumb_color=ft.Colors.ON_SURFACE_VARIANT,
            active_track_color=ft.Colors.with_opacity(0.3, ft.Colors.BLUE_400),
            inactive_track_color=ft.Colors.with_opacity(0.12, ft.Colors.ON_SURFACE),
        )


class ProfileSections:
    """Seções organizadas do perfil."""

    @staticmethod
    def create_personal_info_section(
        profile: Dict[str, Any], email: str, controller
    ) -> ft.Container:
        """Cria a seção de informações pessoais."""
        fields = ProfileFieldComponents()
        controller.email_field.current = fields.create_text_field(
            "Email", email, read_only=True, disabled=True
        )
        controller.name_field.current = fields.create_text_field(
            "Nome", profile.get("name", "")
        )
        controller.age_field.current = fields.create_text_field(
            "Idade",
            str(profile.get("age", "")),
            keyboard_type=ft.KeyboardType.NUMBER,
            expand=True,
        )
        controller.weight_field.current = fields.create_text_field(
            "Peso (kg)",
            str(profile.get("weight", "")),
            keyboard_type=ft.KeyboardType.NUMBER,
            expand=True,
        )
        controller.height_field.current = fields.create_text_field(
            "Altura (cm)",
            str(profile.get("height", "")),
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        return ft.Container(
            content=ft.Column(
                [
                    ft.Container(
                        content=ft.Text(
                            "Informações Pessoais",
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.ON_SURFACE,
                        ),
                        margin=ft.margin.only(bottom=16),
                    ),
                    controller.email_field.current,
                    ft.Container(height=12),
                    controller.name_field.current,
                    ft.Container(height=12),
                    ft.Row(
                        [
                            controller.age_field.current,
                            ft.Container(width=12),
                            controller.weight_field.current,
                        ]
                    ),
                    ft.Container(height=12),
                    controller.height_field.current,
                ]
            ),
            padding=ft.padding.all(20),
            border=ft.border.all(1, ft.Colors.with_opacity(0.12, ft.Colors.ON_SURFACE)),
            border_radius=16,
        )

    @staticmethod
    def create_fitness_goals_section(
        profile: Dict[str, Any], controller
    ) -> ft.Container:
        """Cria a seção de objetivos fitness."""
        fields = ProfileFieldComponents()
        goal_options = [
            ft.dropdown.Option("Perder peso"),
            ft.dropdown.Option("Ganhar massa"),
            ft.dropdown.Option("Manter forma"),
        ]
        level_options = [
            ft.dropdown.Option("iniciante"),
            ft.dropdown.Option("intermediário"),
            ft.dropdown.Option("avançado"),
        ]
        controller.goal_dropdown.current = fields.create_dropdown(
            "Objetivo", profile.get("goal", "Manter forma"), goal_options
        )
        controller.level_dropdown.current = fields.create_dropdown(
            "Nível", profile.get("level", "iniciante"), level_options
        )
        controller.rest_field.current = fields.create_text_field(
            "Duração do Intervalo (segundos)",
            str(profile.get("rest_duration", 60)),
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        return ft.Container(
            content=ft.Column(
                [
                    ft.Container(
                        content=ft.Text(
                            "Objetivos & Nível",
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.ON_SURFACE,
                        ),
                        margin=ft.margin.only(bottom=16),
                    ),
                    controller.goal_dropdown.current,
                    ft.Container(height=12),
                    controller.level_dropdown.current,
                    ft.Container(height=12),
                    controller.rest_field.current,
                ]
            ),
            padding=ft.padding.all(20),
            border=ft.border.all(1, ft.Colors.with_opacity(0.12, ft.Colors.ON_SURFACE)),
            border_radius=16,
        )

    @staticmethod
    def create_appearance_section(profile: Dict[str, Any], controller) -> ft.Container:
        """Cria a seção de aparência."""
        fields = ProfileFieldComponents()
        font_options = [
            ft.dropdown.Option("Roboto"),
            ft.dropdown.Option("Open Sans"),
            ft.dropdown.Option("Barlow"),
            ft.dropdown.Option("Manrope"),
        ]
        color_options = [
            ft.dropdown.Option("GREEN", text="Verde"),
            ft.dropdown.Option("BLUE", text="Azul"),
            ft.dropdown.Option("RED", text="Vermelho"),
            ft.dropdown.Option("PURPLE", text="Roxo"),
        ]
        controller.theme_switch.current = fields.create_switch(
            "Tema Escuro", profile.get("theme", "light") == "dark"
        )
        controller.font_dropdown.current = fields.create_dropdown(
            "Fonte", profile.get("font_family", "Roboto"), font_options
        )
        controller.color_dropdown.current = fields.create_dropdown(
            "Cor Primária", profile.get("primary_color", "GREEN"), color_options
        )
        return ft.Container(
            content=ft.Column(
                [
                    ft.Container(
                        content=ft.Text(
                            "Aparência & Tema",
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.ON_SURFACE,
                        ),
                        margin=ft.margin.only(bottom=16),
                    ),
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Text(
                                    "Tema Escuro",
                                    size=14,
                                    color=ft.Colors.ON_SURFACE,
                                    weight=ft.FontWeight.W_500,
                                ),
                                controller.theme_switch.current,
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        padding=ft.padding.all(16),
                        border=ft.border.all(
                            1, ft.Colors.with_opacity(0.12, ft.Colors.ON_SURFACE)
                        ),
                        border_radius=12,
                    ),
                    ft.Container(height=12),
                    controller.font_dropdown.current,
                    ft.Container(height=12),
                    controller.color_dropdown.current,
                ]
            ),
            padding=ft.padding.all(20),
            border=ft.border.all(1, ft.Colors.with_opacity(0.12, ft.Colors.ON_SURFACE)),
            border_radius=16,
        )


class ProfileActions:
    """Ações do perfil (salvar, voltar, etc.)."""

    @staticmethod
    def create_action_buttons(
        save_callback: Callable, back_callback: Callable
    ) -> ft.Container:
        """Cria os botões de ação com design moderno."""
        return ft.Container(
            content=ft.ResponsiveRow(
                [
                    ft.ElevatedButton(
                        content=ft.Row(
                            [
                                ft.Icon(ft.Icons.SAVE, size=18),
                                ft.Container(width=8),
                                ft.Text(
                                    "Salvar Alterações",
                                    size=14,
                                    weight=ft.FontWeight.W_600,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            tight=True,
                            col={"sm": 12, "md": 6},
                        ),
                        on_click=save_callback,
                        style=ft.ButtonStyle(
                            overlay_color=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
                            elevation=0,
                            shadow_color=ft.Colors.TRANSPARENT,
                            surface_tint_color=ft.Colors.TRANSPARENT,
                            padding=ft.padding.symmetric(horizontal=24, vertical=16),
                            shape=ft.RoundedRectangleBorder(radius=12),
                        ),
                        height=56,
                        expand=True,
                    ),
                    ft.Container(width=16),
                    ft.OutlinedButton(
                        content=ft.Row(
                            [
                                ft.Icon(ft.Icons.ARROW_BACK, size=18),
                                ft.Container(width=8),
                                ft.Text("Voltar", size=14, weight=ft.FontWeight.W_600),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            tight=True,
                            col={"sm": 12, "md": 6},
                        ),
                        on_click=back_callback,
                        style=ft.ButtonStyle(
                            overlay_color=ft.Colors.with_opacity(
                                0.08, ft.Colors.ON_SURFACE
                            ),
                            side=ft.BorderSide(
                                width=1,
                                color=ft.Colors.with_opacity(
                                    0.12, ft.Colors.ON_SURFACE
                                ),
                            ),
                            padding=ft.padding.symmetric(horizontal=24, vertical=16),
                            shape=ft.RoundedRectangleBorder(radius=12),
                        ),
                        height=56,
                        expand=True,
                    ),
                ]
            ),
            margin=ft.margin.only(top=32),
        )


class ProfileValidation:
    """Validação dos dados do perfil."""

    @staticmethod
    def validate_profile_data(fields: Dict[str, Any]) -> None:
        """Valida os dados do perfil."""
        if not fields["name"].strip():
            raise ValueError("O nome é obrigatório.")
        if (
            not fields["age"].strip()
            or not fields["age"].isdigit()
            or int(fields["age"]) <= 0
            or int(fields["age"]) > 150
        ):
            raise ValueError("Idade inválida (deve ser entre 1 e 150).")
        if (
            not fields["weight"].strip()
            or not fields["weight"].replace(".", "").isdigit()
            or float(fields["weight"]) <= 30
            or float(fields["weight"]) > 300
        ):
            raise ValueError("Peso inválido (deve ser entre 30 e 300 kg).")
        if (
            not fields["height"].strip()
            or not fields["height"].isdigit()
            or int(fields["height"]) <= 100
            or int(fields["height"]) > 250
        ):
            raise ValueError("Altura inválida (deve ser entre 100 e 250 cm).")
        if not fields["goal"]:
            raise ValueError("Selecione um objetivo.")
        if not fields["level"]:
            raise ValueError("Selecione um nível.")
        if (
            not fields["rest_duration"].strip()
            or not fields["rest_duration"].isdigit()
            or int(fields["rest_duration"]) <= 0
            or int(fields["rest_duration"]) > 3600
        ):
            raise ValueError("Duração do intervalo inválida (máximo 3600 segundos).")


class NotificationHelper:
    """Helper para notificações/snackbars."""

    @staticmethod
    def show_success(page: ft.Page, message: str, color: str = "GREEN") -> None:
        """Mostra notificação de sucesso."""
        snackbar = CustomSnackBar(
            message=message, bgcolor=getattr(ft.Colors, color, ft.Colors.GREEN_700)
        )
        snackbar.show(page)
        logger.info(f"Notificação de sucesso: {message}")

    @staticmethod
    def show_error(page: ft.Page, message: str) -> None:
        """Mostra notificação de erro."""
        snackbar = CustomSnackBar(message=message, bgcolor=ft.Colors.RED_700)
        snackbar.show(page)
        logger.info(f"Notificação de erro: {message}")
