import flet as ft
from pages.home import Homepage
from pages.training.treino import Treinopage
from pages.profile_settings.profile_settings import ProfileSettingsPage
from pages.history import HistoryPage
from components.appbar_class import MobileAppBar
from pages.auth.login import LoginPage
from pages.auth.register import RegisterPage
from pages.community.community_tab import CommunityTab
from pages.trainer_chat.trainer_main import TrainerTab
from pages.terms_page import TermsPage
from pages.support.support import SupportPageView
from pages.profile_user.create_profile import CreateProfilePage
from utils.alerts import CustomSnackBar


def setup_routes(page: ft.Page, supabase, openai):
    """Sistema de rotas melhorado seguindo as melhores práticas do Flet."""

    # Configurações de rotas
    PUBLIC_ROUTES = [
        "/login",
        "/register",
        "/terms",
        "/support",
    ]
    PROFILE_REQUIRED_ROUTES = [
        "/home",
        "/",
        "/community",
        "/trainer",
        "/profile_settings",
        "/history",
    ]

    mobile_appbar = MobileAppBar(page)

    def show_snackbar(message: str, color: str = ft.Colors.RED_700):
        """Exibe feedback para o usuário com estilo consistente."""
        snackbar = CustomSnackBar(message=message, bgcolor=color)
        page.snack_bar = snackbar
        page.snack_bar.open = True
        page.update()
        print(f"INFO - routes: SnackBar exibida: {message}")

    def is_authenticated():
        """Verifica se o usuário está autenticado."""
        return supabase.is_authenticated()

    def has_profile():
        """Verifica se o usuário tem perfil criado."""
        return page.client_storage.get("supafit.profile_created") or False

    def build_views_for_route(route: str):
        """
        Constrói a lista de views baseada na rota atual.
        Esta é a função central que determina qual view exibir.
        """
        page.views.clear()

        # Sempre adiciona a view raiz
        page.views.append(build_root_view())

        # Rota raiz - redireciona para home ou login
        if route == "/":
            if is_authenticated() and has_profile():
                page.views.append(build_home_view())
            else:
                page.views.append(build_login_view())
                return

        # Rotas públicas
        elif route in PUBLIC_ROUTES:
            if route == "/login":
                page.views.append(build_login_view())
            elif route == "/register":
                page.views.append(build_register_view())
            elif route == "/terms":
                page.views.append(build_terms_view())
            elif route == "/support":
                page.views.append(build_support_view())

        # Rota de criação de perfil (requer autenticação)
        elif route == "/create_profile":
            if not is_authenticated():
                show_snackbar(
                    "Por favor, faça login para continuar.", ft.Colors.BLUE_400
                )
                page.views.append(build_login_view())
                return
            page.views.append(build_create_profile_view())

        # Rotas protegidas (requer autenticação e perfil)
        elif route in PROFILE_REQUIRED_ROUTES or route.startswith("/treino/"):
            if not is_authenticated():
                show_snackbar(
                    "Por favor, faça login para continuar.", ft.Colors.BLUE_400
                )
                page.views.append(build_login_view())
                return

            if not has_profile():
                show_snackbar("Complete seu perfil para continuar.", ft.Colors.BLUE_400)
                page.views.append(build_create_profile_view())
                return

            if route == "/home":
                page.views.append(build_home_view())
            elif route == "/community":
                page.views.append(build_community_view())
            elif route == "/trainer":
                page.views.append(build_trainer_view())
            elif route == "/profile_settings":
                page.views.append(build_profile_settings_view())
            elif route == "/history":
                page.views.append(build_history_view())
            elif route.startswith("/treino/"):
                day = route.split("/")[-1]
                user_id = page.client_storage.get("supafit.user_id")
                if user_id:
                    page.views.append(build_treino_view(day, user_id))
                else:
                    show_snackbar("Erro: Usuário não identificado.", ft.Colors.RED_700)
                    page.views.append(build_login_view())
                    return

        else:
            show_snackbar(
                "Rota não encontrada. Redirecionando para login.", ft.Colors.RED_700
            )
            page.views.append(build_login_view())

    def build_root_view():
        """Constrói a view raiz (sempre presente)."""
        return ft.View(
            route="/",
            controls=[],
            vertical_alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def build_login_view():
        """Constrói a view de login."""
        return ft.View(
            route="/login",
            controls=[LoginPage(page)],
            vertical_alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            padding=20,
        )

    def build_register_view():
        """Constrói a view de registro."""
        return ft.View(
            route="/register",
            controls=[RegisterPage(page)],
            vertical_alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            padding=20,
        )

    def build_terms_view():
        """Constrói a view de termos de uso."""
        return ft.View(
            route="/terms",
            appbar=mobile_appbar.create_appbar("Termos de Uso"),
            controls=[TermsPage(page, supabase, openai)],
            vertical_alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            padding=20,
        )

    def build_support_view():
        """Constrói a view de apoio/suporte."""
        return ft.View(
            route="/support",
            appbar=mobile_appbar.create_appbar("💪 Apoie o SupaFit"),
            controls=[SupportPageView(page, supabase, openai)],
            vertical_alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
        )

    def build_create_profile_view():
        """Constrói a view de criação de perfil."""
        return ft.View(
            route="/create_profile",
            appbar=mobile_appbar.create_appbar("Criar Perfil"),
            controls=[CreateProfilePage(page, supabase)],
            vertical_alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            padding=20,
        )

    def build_home_view():
        """Constrói a view da página inicial."""
        return ft.View(
            route="/home",
            appbar=mobile_appbar.create_appbar("Frequência de Treino"),
            controls=[Homepage(page, supabase)],
            vertical_alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            padding=20,
        )

    def build_community_view():
        """Constrói a view da comunidade."""
        return ft.View(
            route="/community",
            appbar=mobile_appbar.create_appbar("Comunidade"),
            controls=[CommunityTab(page, supabase)],
            scroll=ft.ScrollMode.AUTO,
            padding=20,
        )

    def build_trainer_view():
        """Constrói a view do treinador."""
        return ft.View(
            route="/trainer",
            appbar=mobile_appbar.create_appbar("Treinador"),
            controls=[TrainerTab(page, supabase, openai)],
            vertical_alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            padding=20,
        )

    def build_profile_settings_view():
        """Constrói a view de configurações do perfil."""
        return ft.View(
            route="/profile_settings",
            appbar=mobile_appbar.create_appbar("Perfil"),
            controls=[ProfileSettingsPage(page)],
            vertical_alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            padding=20,
        )

    def build_history_view():
        """Constrói a view do histórico."""
        return ft.View(
            route="/history",
            appbar=mobile_appbar.create_appbar("Histórico"),
            controls=[HistoryPage(page, supabase)],
            vertical_alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            padding=20,
        )

    def build_treino_view(day: str, user_id: str):
        """Constrói a view de treino para um dia específico."""
        return ft.View(
            route=f"/treino/{day}",
            appbar=mobile_appbar.create_appbar(f"Treino - {day.capitalize()}"),
            controls=[Treinopage(page, supabase, day, user_id)],
            vertical_alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            padding=20,
        )

    def route_change(e: ft.RouteChangeEvent):
        """
        Manipulador principal de mudanças de rota.
        Segue o padrão recomendado pela documentação do Flet.
        """
        try:
            print(f"INFO - routes: Navegando para: {e.route}")
            build_views_for_route(e.route)
            page.update()
            print(f"INFO - routes: Página atualizada para rota: {e.route}")
        except Exception as ex:
            print(f"ERROR - routes: Erro ao processar rota {e.route}: {str(ex)}")
            show_snackbar(f"Erro ao carregar página: {str(ex)}")
            # Em caso de erro, redireciona para login
            page.views.clear()
            page.views.append(build_root_view())
            page.views.append(build_login_view())
            page.update()

    def view_pop(e: ft.ViewPopEvent):
        """
        Manipula o evento de voltar das views.
        Segue o padrão recomendado pela documentação do Flet.
        """
        try:
            if len(page.views) > 1:
                page.views.pop()
                top_view = page.views[-1]
                page.go(top_view.route)
                print(f"INFO - routes: View pop, navegando para: {top_view.route}")
            else:
                # Se não há views suficientes, vai para login
                page.go("/login")
                print("INFO - routes: View pop, redirecionando para /login")
        except Exception as ex:
            print(f"ERROR - routes: Erro no view_pop: {str(ex)}")
            page.go("/login")

        page.update()

    # Configuração dos manipuladores de eventos
    page.on_route_change = route_change
    page.on_view_pop = view_pop

    # Inicia a navegação para a rota atual
    page.go(page.route)
