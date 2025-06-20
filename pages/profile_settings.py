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

    Exibe email do Supabase Auth e campos do perfil como nome, idade, peso, altura, objetivo, nível, tema e duração de intervalo.

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
        page.snack_bar = ft.SnackBar(
            content=ft.Text("Erro de autenticação. Redirecionando para login."),
            bgcolor=ft.Colors.RED_700,
        )
        page.snack_bar.open = True
        page.go("/login")
        return ft.Container()

    user_id = page.client_storage.get("supafit.user_id")
    if not user_id:
        logger.warning("Nenhum user_id encontrado no client_storage.")
        page.snack_bar = ft.SnackBar(
            content=ft.Text("Usuário não autenticado. Faça login novamente."),
            bgcolor=ft.Colors.RED_700,
        )
        page.snack_bar.open = True
        page.go("/login")
        return ft.Container()

    # Recupera email do Supabase Auth
    try:
        user = supabase_service.client.auth.get_user()
        email = user.user.email if user and user.user else page.client_storage.get("supafit.email", "")
    except Exception as e:
        logger.error(f"Erro ao recuperar email do Supabase Auth: {str(e)}")
        email = page.client_storage.get("supafit.email", "")

    # Recupera perfil do Supabase
    profile = (
        supabase_service.get_profile(user_id).data[0]
        if supabase_service.get_profile(user_id).data
        else {}
    )

    # Componentes de formulário com estilo consistente
    email_field = ft.TextField(
        label="Email",
        value=email,
        border_color=ft.Colors.GREY_600,
        filled=True,
        bgcolor=ft.Colors.GREY_800,
        color=ft.Colors.WHITE,
        border_radius=5,
        text_size=14,
        read_only=True,  # Email não editável
    )
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
        value=str(profile.get("age", "")),
        border_color=ft.Colors.GREY_600,
        filled=True,
        bgcolor=ft.Colors.GREY_800,
        color=ft.Colors.WHITE,
        border_radius=5,
        text_size=14,
        keyboard_type=ft.KeyboardType.NUMBER,
    )
    weight_field = ft.TextField(
        label="Peso (kg)",
        value=str(profile.get("weight", "")),
        border_color=ft.Colors.GREY_600,
        filled=True,
        bgcolor=ft.Colors.GREY_800,
        color=ft.Colors.WHITE,
        border_radius=5,
        text_size=14,
        keyboard_type=ft.KeyboardType.NUMBER,
    )
    height_field = ft.TextField(
        label="Altura (cm)",
        value=str(profile.get("height", "")),
        border_color=ft.Colors.GREY_600,
        filled=True,
        bgcolor=ft.Colors.GREY_800,
        color=ft.Colors.WHITE,
        border_radius=5,
        text_size=14,
        keyboard_type=ft.KeyboardType.NUMBER,
    )
    goal_dropdown = ft.Dropdown(
        label="Objetivo",
        value=profile.get("goal", "Manter forma"),
        options=[
            ft.dropdown.Option("Perder peso"),
            ft.dropdown.Option("Ganhar massa"),
            ft.dropdown.Option("Manter forma"),
        ],
        border_color=ft.Colors.GREY_600,
        filled=True,
        bgcolor=ft.Colors.GREY_800,
        color=ft.Colors.WHITE,
        border_radius=5,
        text_size=14,
    )
    level_dropdown = ft.Dropdown(
        label="Nível",
        value=profile.get("level", "iniciante"),
        options=[
            ft.dropdown.Option("iniciante"),
            ft.dropdown.Option("intermediário"),
            ft.dropdown.Option("avançado"),
        ],
        border_color=ft.Colors.GREY_600,
        filled=True,
        bgcolor=ft.Colors.GREY_800,
        color=ft.Colors.WHITE,
        border_radius=5,
        text_size=14,
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
            # Validações
            if not name_field.value.strip():
                raise ValueError("O nome é obrigatório.")
            if not age_field.value.strip() or not age_field.value.isdigit() or int(age_field.value) <= 0 or int(age_field.value) > 150:
                raise ValueError("Idade inválida (deve ser entre 1 e 150).")
            if not weight_field.value.strip() or not weight_field.value.replace(".", "").isdigit() or float(weight_field.value) <= 30 or float(weight_field.value) > 300:
                raise ValueError("Peso inválido (deve ser entre 30 e 300 kg).")
            if not height_field.value.strip() or not height_field.value.isdigit() or int(height_field.value) <= 100 or int(height_field.value) > 250:
                raise ValueError("Altura inválida (deve ser entre 100 e 250 cm).")
            if not goal_dropdown.value:
                raise ValueError("Selecione um objetivo.")
            if not level_dropdown.value:
                raise ValueError("Selecione um nível.")
            if not rest_duration.value.strip() or not rest_duration.value.isdigit() or int(rest_duration.value) <= 0 or int(rest_duration.value) > 3600:
                raise ValueError("Duração do intervalo inválida (máximo 3600 segundos).")

            # Aplica tema
            page.theme_mode = ft.ThemeMode.DARK if theme_switch.value else ft.ThemeMode.LIGHT

            # Monta dados do perfil
            profile_data = {
                "user_id": user_id,
                "name": name_field.value.strip(),
                "age": int(age_field.value),
                "weight": float(weight_field.value),
                "height": int(height_field.value),
                "goal": goal_dropdown.value,
                "level": level_dropdown.value,
                "theme": "dark" if theme_switch.value else "light",
                "rest_duration": int(rest_duration.value),
            }

            # Salva no Supabase
            supabase_service.client.table("user_profiles").upsert(profile_data).execute()
            logger.info(f"Perfil salvo com sucesso para user_id: {user_id}")
            page.snack_bar = ft.SnackBar(
                content=ft.Text("Perfil salvo com sucesso!"),
                bgcolor=ft.Colors.GREEN_700,
            )
            page.snack_bar.open = True
            page.go("/home")
            page.update()
        except ValueError as ve:
            logger.warning(f"Validação falhou: {str(ve)}")
            page.snack_bar = ft.SnackBar(
                content=ft.Text(str(ve)),
                bgcolor=ft.Colors.RED_700,
            )
            page.snack_bar.open = True
            page.update()
        except Exception as e:
            logger.error(f"Erro ao salvar perfil: {str(e)}")
            page.snack_bar = ft.SnackBar(
                content=ft.Text("Erro ao salvar perfil. Tente novamente."),
                bgcolor=ft.Colors.RED_700,
            )
            page.snack_bar.open = True
            page.update()

    def go_back(e):
        """Retorna à página inicial sem salvar alterações."""
        page.go("/home")

    # Layout com design profissional e responsivo
    return ft.Card(
        content=ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "Configurações do Perfil",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.WHITE,
                    ),
                    ft.Container(
                        content=email_field,
                        margin=ft.margin.only(bottom=10),
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
                        content=weight_field,
                        margin=ft.margin.only(bottom=10),
                    ),
                    ft.Container(
                        content=height_field,
                        margin=ft.margin.only(bottom=10),
                    ),
                    ft.Container(
                        content=goal_dropdown,
                        margin=ft.margin.only(bottom=10),
                    ),
                    ft.Container(
                        content=level_dropdown,
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
            padding=20,
            bgcolor=ft.Colors.GREY_900,
            border_radius=10,
        ),
        elevation=5,
        shadow_color=ft.Colors.BLACK54,
        margin=ft.margin.all(10),
        shape=ft.RoundedRectangleBorder(radius=10),
    )
