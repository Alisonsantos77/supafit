# main.py
import flet as ft
import requests
from routes import setup_routes
import os
from dotenv import load_dotenv
import logging
from services.supabase import SupabaseService
from services.anthropic import AnthropicService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("app.log"), logging.StreamHandler()],
)


def check_internet_connection():
    try:
        response = requests.get("https://www.google.com", timeout=5)
        response.raise_for_status()
        return True
    except requests.RequestException as e:
        logging.error(f"Sem conexão com a internet: {str(e)}")
        return False


def main(page: ft.Page):
    load_dotenv()
    page.title = "SupaFit"

    # Carregar fontes
    page.fonts = {
        "Roboto": "assets/fonts/Roboto-VariableFont_wdth,wght.ttf",
        "Open Sans": "assets/fonts/OpenSans-VariableFont_wdth,wght.ttf",
        "Barlow": "assets/fonts/Barlow-Regular.ttf",
        "Manrope": "assets/fonts/Manrope-VariableFont_wght.ttf",
    }
    # Inicializar serviços
    try:
        supabase = SupabaseService.get_instance(page)
    except Exception as e:
        logging.error(f"Erro ao inicializar Supabase: {str(e)}")
        page.add(ft.Text(f"Erro ao inicializar Supabase: {str(e)}"))
        page.go("/login")
        return

    anthropic = AnthropicService()

    # Carregar perfil
    user_id = page.client_storage.get("supafit.user_id")
    profile = {}
    if user_id:
        try:
            profile_response = supabase.get_profile(user_id)
            if profile_response.data:
                profile = profile_response.data[0]
        except Exception as e:
            logging.error(f"Erro ao carregar perfil: {str(e)}")
            profile = {}

    # Carregar preferências do tema
    font_family = profile.get("font_family", "Roboto")
    theme_mode = (
        ft.ThemeMode.DARK
        if profile.get("theme", "light") == "dark"
        else ft.ThemeMode.LIGHT
    )
    primary_color = getattr(ft.Colors, profile.get("primary_color", "GREEN"))

    # Aplicar tema
    page.theme = ft.Theme(
        color_scheme=ft.ColorScheme(
            primary=primary_color,
            secondary=ft.Colors.BLUE_700,
            on_primary=ft.Colors.WHITE,
            on_secondary=ft.Colors.WHITE,
        ),
        font_family=font_family,
    )
    page.theme_mode = theme_mode

    keys = ["supafit.user_id", "supafit.email", "supafit.level"]
    storage_values = {key: page.client_storage.get(key) for key in keys}
    logging.info(f"Valores recuperados do armazenamento: {storage_values}")

    try:
        setup_routes(page, supabase, anthropic)
    except Exception as e:
        logging.error(f"Erro ao configurar rotas: {str(e)}")
        page.add(ft.Text(f"Erro ao configurar rotas: {str(e)}"))

    page.update()


if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")
