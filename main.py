import flet as ft
import requests
from routes import setup_routes
from dotenv import load_dotenv
from services.supabase import SupabaseService
from services.openai import OpenAIService


def check_internet_connection(page: ft.Page) -> bool:
    try:
        response = requests.get("https://www.google.com", timeout=5)
        response.raise_for_status()
        if response.status_code == 200:
            print("Conexão com a internet está ativa.")
            page.open(
                ft.SnackBar(
                    content=ft.Text(
                        "Conexão com a internet está ativa.", color=ft.Colors.WHITE
                    ),
                    bgcolor=ft.Colors.GREEN_600,
                )
            )
            page.update()
        return True
    except requests.RequestException as e:
        print(
            "ERROR: Sem conexão com a internet. Verifique sua conexão e tente novamente."
        )
        page.open(
            ft.SnackBar(
                content=ft.Text(
                    "Sem conexão com a internet. Verifique sua conexão e tente novamente.",
                    color=ft.Colors.WHITE,
                ),
                bgcolor=ft.Colors.RED,
            )
        )
        page.update()
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

    # Inicializar Supabase
    try:
        supabase = SupabaseService.get_instance(page)
    except Exception as e:
        print(f"ERROR: Não foi possível inicializar o Supabase: {str(e)}")
        page.open(
            ft.SnackBar(
                content=ft.Text(
                    "Erro ao inicializar Supabase: " + str(e), color=ft.Colors.WHITE
                ),
                bgcolor=ft.Colors.RED,
            )
        )
        page.update()
        page.go("/login")
        return

    # Inicializar OpenAI
    openai = OpenAIService()

    # Configurar rotas ANTES de qualquer navegação
    try:
        setup_routes(page, supabase, openai)
    except Exception as e:
        print(f"ERROR: Não foi possível configurar as rotas: {str(e)}")
        page.add(ft.Text(f"Erro ao configurar rotas: {str(e)}"))
        page.go("/login")
        return

    # Carregar perfil do usuário salvo
    user_id = page.client_storage.get("supafit.user_id")
    profile = {}
    if user_id:
        try:
            profile_response = supabase.get_profile(user_id)
            if profile_response.data and len(profile_response.data) > 0:
                profile = profile_response.data[0]
                print(f"Perfil carregado: {profile}")
                page.open(
                    ft.SnackBar(
                        content=ft.Text("Perfil carregado com sucesso!"),
                        bgcolor=ft.Colors.GREEN_600,
                    )
                )
                page.update()
                page.client_storage.set("supafit.profile_created", True)
            else:
                print("Perfil não encontrado, redirecionando para criação de perfil.")
                page.open(
                    ft.SnackBar(
                        content=ft.Text(
                            "Perfil não encontrado. Por favor, crie um perfil."
                        ),
                        bgcolor=ft.Colors.ORANGE_600,
                    )
                )
                page.update()
                page.client_storage.set("supafit.profile_created", False)
                page.go("/create_profile")
                return
        except Exception as e:
            print(f"Erro ao carregar perfil: {str(e)}")
            page.client_storage.set("supafit.profile_created", False)
            page.go("/create_profile")
            page.update()
            return
    else:
        print("Nenhum user_id encontrado, redirecionando para login.")
        page.go("/login")
        page.update()
        return

    # Validar preferências do tema
    valid_fonts = ["Roboto", "Open Sans", "Barlow", "Manrope"]
    valid_colors = ["GREEN", "BLUE", "RED", "PURPLE"]
    font_family = (
        profile.get("font_family", "Roboto")
        if profile.get("font_family") in valid_fonts
        else "Roboto"
    )
    theme = profile.get("theme", "light")
    primary_color = (
        profile.get("primary_color", "GREEN")
        if profile.get("primary_color") in valid_colors
        else "GREEN"
    )

    # Definir tema
    page.theme_mode = ft.ThemeMode.DARK if theme == "dark" else ft.ThemeMode.LIGHT
    page.theme = ft.Theme(
        color_scheme=ft.ColorScheme(
            primary=getattr(ft.Colors, primary_color),
            secondary=ft.Colors.BLUE_700,
            on_primary=ft.Colors.WHITE,
            on_secondary=ft.Colors.WHITE,
        ),
        font_family=font_family,
    )

    # Debug: imprimir valores do client storage
    keys = ["supafit.user_id", "supafit.email", "supafit.level"]
    storage_values = {key: page.client_storage.get(key) for key in keys}
    print(f"Valores recuperados do armazenamento: {storage_values}")

    # Atualiza a página após todas configurações
    page.update()


if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")
