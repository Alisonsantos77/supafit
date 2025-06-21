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
        self.form_fields = {}

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

    def _collect_form_data(
        self, personal_section, fitness_section, appearance_section
    ) -> Dict[str, Any]:
        """Coleta dados dos formulários."""
        # Extrai campos das seções
        email_field = personal_section.content.controls[1]  
        name_field = personal_section.content.controls[3]  
        age_field = personal_section.content.controls[5].controls[0]  
        weight_field = personal_section.content.controls[5].controls[2]  
        height_field = personal_section.content.controls[7]  

        goal_dropdown = fitness_section.content.controls[1]  
        level_dropdown = fitness_section.content.controls[3]  
        rest_field = fitness_section.content.controls[5]  

        theme_switch = appearance_section.content.controls[1].content.controls[
            1
        ]  
        font_dropdown = appearance_section.content.controls[3]  
        color_dropdown = appearance_section.content.controls[5]  

        return {
            "name": name_field.value,
            "age": age_field.value,
            "weight": weight_field.value,
            "height": height_field.value,
            "goal": goal_dropdown.value,
            "level": level_dropdown.value,
            "rest_duration": rest_field.value,
            "theme": theme_switch.value,
            "font_family": font_dropdown.value,
            "primary_color": color_dropdown.value,
        }

    def validate_and_save(
        self, e, personal_section, fitness_section, appearance_section
    ):
        """Valida e salva as configurações do perfil."""
        try:
            form_data = self._collect_form_data(
                personal_section, fitness_section, appearance_section
            )

            # Valida os dados
            ProfileValidation.validate_profile_data(form_data)

            # Aplica tema na página
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

            # Salva no banco
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

    # Cria as seções do perfil
    personal_section = ProfileSections.create_personal_info_section(
        controller.profile, controller.email
    )

    fitness_section = ProfileSections.create_fitness_goals_section(controller.profile)

    appearance_section = ProfileSections.create_appearance_section(controller.profile)

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
        border_radius=16,
        shadow=ft.BoxShadow(
            spread_radius=0,
            blur_radius=20,
            color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
            offset=ft.Offset(0, 8),
        ),
    )
