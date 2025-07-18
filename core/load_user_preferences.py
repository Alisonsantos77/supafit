import flet as ft


def apply_user_preferences(page: ft.Page, profile: dict):
    """
    Aplica as preferências visuais do usuário à página, com base no perfil carregado.
    """
    try:
        # Definir tema escuro ou claro
        page.theme_mode = (
            ft.ThemeMode.DARK
            if profile.get("theme", "light") == "dark"
            else ft.ThemeMode.LIGHT
        )

        # Aplicar tema personalizado com cor primária e fonte
        page.theme = ft.Theme(
            color_scheme=ft.ColorScheme(
                primary=getattr(
                    ft.Colors, profile.get("primary_color", "BLUE"), ft.Colors.BLUE
                ),
                secondary=ft.Colors.BLUE_700,
                on_primary=ft.Colors.WHITE,
                on_secondary=ft.Colors.WHITE,
            ),
            font_family=profile.get("font_family", "Roboto"),
        )

        print("[PREFERENCES] Preferências visuais aplicadas com sucesso.")

    except Exception as e:
        print(f"[PREFERENCES] Erro ao aplicar preferências do usuário: {e}")
