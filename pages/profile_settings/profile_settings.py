from typing import Any, Dict
import flet as ft
from services.supabase import SupabaseService
from utils.logger import get_logger
from .profile_components import (
    ProfileSections,
    ProfileActions,
    ProfileValidation,
    NotificationHelper,
)

logger = get_logger("supafit.profile_settings")


class ProfileSettingsController:
    """Controlador principal da página de configurações de perfil."""

    def __init__(self, page: ft.Page):
        self.page = page
        self.supabase_service = None
        self.user_id = None
        self.email = ""
        self.profile = {}
        self.email_field = ft.Ref[ft.TextField]()
        self.name_field = ft.Ref[ft.TextField]()
        self.age_field = ft.Ref[ft.TextField]()
        self.weight_field = ft.Ref[ft.TextField]()
        self.height_field = ft.Ref[ft.TextField]()
        self.goal_dropdown = ft.Ref[ft.Dropdown]()
        self.level_dropdown = ft.Ref[ft.Dropdown]()
        self.rest_field = ft.Ref[ft.TextField]()
        self.theme_switch = ft.Ref[ft.Switch]()
        self.font_dropdown = ft.Ref[ft.Dropdown]()
        self.color_dropdown = ft.Ref[ft.Dropdown]()

    def initialize(self) -> bool:
        """Inicializa o controlador com dados necessários."""
        try:
            self.supabase_service = SupabaseService(self.page)
        except Exception as e:
            logger.error(f"Falha ao inicializar SupabaseService: {str(e)}")
            self._handle_auth_error("Erro de autenticação. Redirecionando para login.")
            return False

        self.user_id = self.page.client_storage.get("supafit.user_id")
        if not self.user_id:
            logger.warning("Nenhum user_id encontrado no client_storage.")
            self._handle_auth_error("Usuário não autenticado. Faça login novamente.")
            return False

        try:
            user = self.supabase_service.client.auth.get_user()
            self.email = (
                user.user.email
                if user and user.user
                else self.page.client_storage.get("supafit.email", "")
            )
        except Exception as e:
            logger.error(f"Erro ao recuperar email do Supabase Auth: {str(e)}")
            self.email = self.page.client_storage.get("supafit.email", "")

        profile_response = self.supabase_service.get_profile(self.user_id)
        self.profile = profile_response.data[0] if profile_response.data else {}

        return True

    def _handle_auth_error(self, message: str) -> None:
        """Manipula erros de autenticação."""
        self.page.client_storage.clear()
        NotificationHelper.show_error(self.page, message)
        self.page.go("/login")

    def _collect_form_data(self) -> Dict[str, Any]:
        """Coleta dados dos formulários."""
        fields = {
            "name": self.name_field,
            "age": self.age_field,
            "weight": self.weight_field,
            "height": self.height_field,
            "goal": self.goal_dropdown,
            "level": self.level_dropdown,
            "rest_duration": self.rest_field,
            "theme": self.theme_switch,
            "font_family": self.font_dropdown,
            "primary_color": self.color_dropdown,
        }
        form_data = {}
        for field_name, field_ref in fields.items():
            if field_ref.current is None:
                logger.error(f"Campo {field_name} não inicializado.")
                NotificationHelper.show_error(
                    self.page, f"Erro: Campo {field_name} não foi carregado."
                )
                raise ValueError(f"Campo {field_name} não inicializado.")
            form_data[field_name] = field_ref.current.value
        form_data["email"] = (
            self.email_field.current.value if self.email_field.current else self.email
        )
        return form_data

    def validate_and_save(
        self, e, personal_section, fitness_section, appearance_section
    ):
        """Valida e salva as configurações do perfil."""
        try:
            form_data = self._collect_form_data()
            ProfileValidation.validate_profile_data(form_data)
            self.page.theme_mode = (
                ft.ThemeMode.DARK if form_data["theme"] else ft.ThemeMode.LIGHT
            )
            self.page.theme = ft.Theme(
                color_scheme=ft.ColorScheme(
                    primary=getattr(ft.Colors, form_data["primary_color"]),
                    secondary=ft.Colors.BLUE_700,
                    on_primary=ft.Colors.WHITE,
                    on_secondary=ft.Colors.WHITE,
                ),
                font_family=form_data["font_family"],
            )
            profile_data = {
                "user_id": self.user_id,
                "name": form_data["name"].strip(),
                "age": int(form_data["age"]),
                "weight": float(form_data["weight"]),
                "height": int(form_data["height"]),
                "goal": form_data["goal"],
                "level": form_data["level"],
                "theme": "dark" if form_data["theme"] else "light",
                "rest_duration": int(form_data["rest_duration"]),
                "font_family": form_data["font_family"],
                "primary_color": form_data["primary_color"],
            }
            self.supabase_service.client.table("user_profiles").upsert(
                profile_data
            ).execute()
            self.page.client_storage.set("supafit.level", profile_data["level"])
            logger.info(f"Perfil salvo com sucesso para user_id: {self.user_id}")
            NotificationHelper.show_success(
                self.page, "Perfil salvo com sucesso!", form_data["primary_color"]
            )
            self.page.go("/home")
        except ValueError as ve:
            logger.warning(f"Validação falhou: {str(ve)}")
            NotificationHelper.show_error(self.page, str(ve))
        except Exception as e:
            logger.error(f"Erro ao salvar perfil: {str(e)}")
            NotificationHelper.show_error(
                self.page, "Erro ao salvar perfil. Tente novamente."
            )

    def go_back(self, e):
        """Retorna à página inicial sem salvar alterações."""
        self.page.go("/home")


def ProfileSettingsPage(page: ft.Page):
    """Cria a interface de Configurações de Perfil com design moderno e modular."""
    controller = ProfileSettingsController(page)
    if not controller.initialize():
        return ft.Container()
    personal_section = ProfileSections.create_personal_info_section(
        controller.profile, controller.email, controller
    )
    fitness_section = ProfileSections.create_fitness_goals_section(
        controller.profile, controller
    )
    appearance_section = ProfileSections.create_appearance_section(
        controller.profile, controller
    )
    action_buttons = ProfileActions.create_action_buttons(
        lambda e: controller.validate_and_save(
            e, personal_section, fitness_section, appearance_section
        ),
        controller.go_back,
    )
    header = ft.Container(
        content=ft.Column(
            [
                ft.Text(
                    "Configurações",
                    size=28,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.WHITE,
                ),
                ft.Text(
                    "Personalize seu perfil e preferências",
                    size=14,
                    color=ft.Colors.with_opacity(0.8, ft.Colors.WHITE),
                ),
            ],
            spacing=4,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        padding=ft.padding.all(32),
        gradient=ft.LinearGradient(
            colors=[
                ft.Colors.BLUE_600,
                ft.Colors.BLUE_800,
            ],
            begin=ft.alignment.top_left,
            end=ft.alignment.bottom_right,
        ),
        border_radius=ft.border_radius.only(
            bottom_left=24,
            bottom_right=24,
        ),
    )
    main_content = ft.Container(
        content=ft.Column(
            [
                header,
                ft.Container(
                    content=ft.Column(
                        [
                            personal_section,
                            ft.Container(height=24),
                            fitness_section,
                            ft.Container(height=24),
                            appearance_section,
                            action_buttons,
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                    ),
                    padding=ft.padding.all(24),
                ),
            ],
            spacing=0,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        ),
        expand=True,
    )
    return ft.Container(
        content=ft.Column(
            [
                main_content,
            ],
            expand=True,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        ),
        padding=ft.padding.all(0),
    )
