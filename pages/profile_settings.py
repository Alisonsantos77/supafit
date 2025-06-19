import flet as ft
from services.services import SupabaseService
import logging

logger = logging.getLogger("supafit.profile_settings")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


def ProfileSettingsPage(page: ft.Page):
    """Cria a interface de Configurações de Perfil para edição de dados do usuário.

    Args:
        page (ft.Page): Instância da página Flet para renderização UI.

    Returns:
        ft.Control: Interface renderizada da página de configurações de perfil.
    """
    # Inicializa SupabaseService com o page passado
    try:
        supabase_service = SupabaseService(page)
    except Exception as e:
        logger.error(f"Falha ao inicializar SupabaseService: {str(e)}")
        page.client_storage.clear()
        page.open(
            ft.SnackBar(
                ft.Text("Erro de autenticação. Redirecionando para login."),
                bgcolor=ft.Colors.RED_700,
            )
        )
        page.go("/login")
        return ft.Container()

    user_id = page.client_storage.get("supafit.user_id") or "supafit_user"
    profile = (
        supabase_service.get_profile(user_id).data[0]
        if supabase_service.get_profile(user_id).data
        else {}
    )

    # Componentes de formulário com estilo consistente
    name_field = ft.TextField(
        label="Nome",
        value=profile.get("name", ""),
        border_color=ft.Colors.GREY_600,
        filled=True,
        bgcolor=ft.Colors.GREY_800,
        color=ft.Colors.WHITE,
        border_radius=5,
        text_size=14,
    )
    age_field = ft.TextField(
        label="Idade",
        value=str(profile.get("age", 0)),
        border_color=ft.Colors.GREY_600,
        filled=True,
        bgcolor=ft.Colors.GREY_800,
        color=ft.Colors.WHITE,
        border_radius=5,
        text_size=14,
        keyboard_type=ft.KeyboardType.NUMBER,
    )
    theme_switch = ft.Switch(
        label="Tema Escuro",
        value=profile.get("theme", "light") == "dark",
        active_color=ft.Colors.BLUE_600,
        inactive_thumb_color=ft.Colors.GREY_600,
    )
    rest_duration = ft.TextField(
        label="Duração do Intervalo (segundos)",
        value=str(profile.get("rest_duration", 60)),
        border_color=ft.Colors.GREY_600,
        filled=True,
        bgcolor=ft.Colors.GREY_800,
        color=ft.Colors.WHITE,
        border_radius=5,
        text_size=14,
        keyboard_type=ft.KeyboardType.NUMBER,
    )

    def validate_and_save(e):
        """Valida e salva as configurações do perfil no Supabase."""
        try:
            if not name_field.value.strip():
                raise ValueError("O nome é obrigatório.")
            if (
                not age_field.value.isdigit()
                or int(age_field.value) <= 0
                or int(age_field.value) > 150
            ):
                raise ValueError("Idade inválida (deve ser entre 1 e 150).")
            if (
                not rest_duration.value.isdigit()
                or int(rest_duration.value) <= 0
                or int(rest_duration.value) > 3600
            ):
                raise ValueError(
                    "Duração do intervalo inválida (máximo 3600 segundos)."
                )

            page.theme_mode = (
                ft.ThemeMode.DARK if theme_switch.value else ft.ThemeMode.LIGHT
            )
            profile_data = {
                "user_id": user_id,
                "name": name_field.value.strip(),
                "age": int(age_field.value),
                "theme": "dark" if theme_switch.value else "light",
                "rest_duration": int(rest_duration.value),
            }
            supabase_service.client.table("user_profiles").upsert(
                profile_data
            ).execute()
            logger.info(f"Perfil salvo com sucesso para user_id: {user_id}")
            page.open(
                ft.SnackBar(
                    ft.Text("Perfil salvo com sucesso!", bgcolor=ft.Colors.GREEN_700)
                )
            )
            page.go("/home")
        except ValueError as ve:
            logger.warning(f"Validação falhou: {str(ve)}")
            page.open(ft.SnackBar(ft.Text(str(ve), bgcolor=ft.Colors.RED_700)))
            page.update()
        except Exception as e:
            logger.error(f"Erro ao salvar perfil: {str(e)}")
            page.open(
                ft.SnackBar(
                    ft.Text(
                        "Erro ao salvar perfil. Tente novamente.",
                        bgcolor=ft.Colors.RED_700,
                    )
                )
            )
            page.update()

    def go_back(e):
        """Retorna à página inicial sem salvar alterações."""
        page.go("/home")

    # Layout com design profissional e responsivo
    return ft.Container(
        content=ft.Column(
            [
                ft.Text(
                    "Perfil e Configurações",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.WHITE,
                ),
                ft.Container(
                    content=name_field,
                    margin=ft.margin.only(bottom=10),
                ),
                ft.Container(
                    content=age_field,
                    margin=ft.margin.only(bottom=10),
                ),
                ft.Container(
                    content=theme_switch,
                    margin=ft.margin.only(bottom=10),
                ),
                ft.Container(
                    content=rest_duration,
                    margin=ft.margin.only(bottom=20),
                ),
                ft.Row(
                    [
                        ft.ElevatedButton(
                            "Salvar",
                            on_click=validate_and_save,
                            style=ft.ButtonStyle(
                                bgcolor=ft.Colors.BLUE_600,
                                color=ft.Colors.WHITE,
                                padding=ft.padding.symmetric(20, 10),
                                shape=ft.RoundedRectangleBorder(radius=5),
                            ),
                        ),
                        ft.ElevatedButton(
                            "Voltar",
                            on_click=go_back,
                            style=ft.ButtonStyle(
                                bgcolor=ft.Colors.GREY_600,
                                color=ft.Colors.WHITE,
                                padding=ft.padding.symmetric(20, 10),
                                shape=ft.RoundedRectangleBorder(radius=5),
                            ),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=20,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=15,
        ),
        alignment=ft.alignment.center,
        padding=20,
        bgcolor=ft.Colors.GREY_900,
        border_radius=10,
        shadow=ft.BoxShadow(
            spread_radius=2,
            blur_radius=10,
            color=ft.Colors.BLACK26,
            offset=ft.Offset(0, 4),
        ),
    )
