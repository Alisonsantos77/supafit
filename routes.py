import flet as ft
from pages.home import Homepage
from pages.treino import Treinopage
from pages.profile_settings.profile_settings import ProfileSettingsPage
from pages.history import HistoryPage
from components.appbar_class import create_appbar
from pages.login import LoginPage
from pages.register import RegisterPage
from pages.community.community_tab import CommunityTab
from pages.trainer_chat.trainer_main import TrainerTab
from pages.terms_page import TermsPage
from pages.profile_user.create_profile import CreateProfilePage
from pages.forgot_password import ForgotPasswordPage
from utils.logger import get_logger

logger = get_logger("supafit.routes")


def setup_routes(page: ft.Page, supabase, anthropic):
    """Sistema de rotas melhorado com autenticação simplificada."""

    # Rotas públicas (não precisam de autenticação)
    PUBLIC_ROUTES = ["/login", "/register", "/terms", "/forgot_password"]

    # Rotas que precisam de perfil criado
    PROFILE_REQUIRED_ROUTES = [
        "/home",
        "/",
        "/community",
        "/trainer",
        "/profile_settings",
        "/history",
    ]

    def show_snackbar(message: str, color: str = ft.Colors.RED_700):
        """Exibe feedback para o usuário com estilo consistente."""
        page.snack_bar = ft.SnackBar(
            content=ft.Text(
                message,
                color=ft.Colors.WHITE,
                size=14,
                weight=ft.FontWeight.BOLD,
                text_align=ft.TextAlign.CENTER,
            ),
            bgcolor=color,
            duration=3000,
            padding=10,
            shape=ft.RoundedRectangleBorder(radius=5),
        )
        page.snack_bar.open = True
        page.update()
        logger.info(f"SnackBar: {message}")

    def require_auth(func):
        """Decorator para rotas que precisam de autenticação."""

        def wrapper():
            if not supabase.is_authenticated():
                logger.info("Usuário não autenticado - redirecionando para login")
                show_snackbar(
                    "Por favor, faça login para continuar.", ft.Colors.BLUE_400
                )
                return redirect_to_login()
            return func()

        return wrapper

    def require_profile(func):
        """Decorator para rotas que requerem perfil criado."""

        def wrapper():
            profile_created = (
                page.client_storage.get("supafit.profile_created") or False
            )
            if not profile_created:
                logger.info("Perfil não criado - redirecionando para criação de perfil")
                show_snackbar("Complete seu perfil para continuar.", ft.Colors.BLUE_400)
                return redirect_to_create_profile()
            return func()

        return wrapper

    def redirect_to_login():
        """Redireciona para página de login."""
        page.views.append(
            ft.View(
                appbar=create_appbar("Login - Supafit"),
                padding=20,
                route="/login",
                controls=[LoginPage(page)],
                vertical_alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO,
            )
        )
        page.go("/login")

    def redirect_to_create_profile():
        """Redireciona para criação de perfil."""
        page.views.append(
            ft.View(
                appbar=create_appbar("Criar Perfil"),
                route="/create_profile",
                controls=[CreateProfilePage(page, supabase)],
                vertical_alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                padding=20,
            )
        )
        page.go("/create_profile")

    def handle_public_routes():
        """Manipula rotas públicas."""
        route_handlers = {
            "/login": lambda: ft.View(
                appbar=create_appbar("Login - Supafit"),
                padding=20,
                route="/login",
                controls=[LoginPage(page)],
                vertical_alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO,
            ),
            "/register": lambda: ft.View(
                appbar=create_appbar("Registrar - Supafit"),
                route="/register",
                controls=[RegisterPage(page)],
                vertical_alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO,
            ),
            "/terms": lambda: ft.View(
                appbar=ft.AppBar(
                    title=ft.Text("Termos de Uso e Política de Privacidade"),
                    center_title=True,
                    actions=[
                        ft.IconButton(
                            icon=ft.Icons.CLOSE,
                            tooltip="Fechar",
                            on_click=lambda _: page.go("/"),
                        )
                    ],
                ),
                route="/terms",
                controls=[TermsPage(page, supabase, anthropic)],
                vertical_alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO,
                padding=20,
            ),
            "/forgot_password": lambda: ft.View(
                appbar=create_appbar("Recuperar Senha - Supafit"),
                padding=20,
                route="/forgot_password",
                controls=[ForgotPasswordPage(page)],
                vertical_alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO,
            ),
        }

        handler = route_handlers.get(page.route)
        if handler:
            page.views.append(handler())

    @require_auth
    @require_profile
    def handle_protected_routes():
        """Manipula rotas protegidas que precisam de perfil."""
        route_handlers = {
            "/home": lambda: ft.View(
                route="/home",
                appbar=create_appbar("Supafit"),
                controls=[Homepage(page, supabase)],
                vertical_alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO,
                padding=20,
            ),
            "/community": lambda: ft.View(
                appbar=create_appbar("Comunidade"),
                route="/community",
                controls=[CommunityTab(page, supabase)],
                padding=20,
                scroll=ft.ScrollMode.AUTO,
            ),
            "/trainer": lambda: ft.View(
                appbar=create_appbar("Treinador"),
                route="/trainer",
                controls=[TrainerTab(page, supabase, anthropic)],
                vertical_alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                padding=20,
            ),
            "/profile_settings": lambda: ft.View(
                appbar=create_appbar("Perfil e Configurações"),
                route="/profile_settings",
                controls=[ProfileSettingsPage(page)],
                vertical_alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO,
                padding=20,
            ),
            "/history": lambda: ft.View(
                appbar=create_appbar("Histórico"),
                route="/history",
                controls=[HistoryPage(page, supabase)],
                vertical_alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO,
                padding=20,
            ),
        }

        if page.route == "/" or page.route == "/home":
            page.views.append(route_handlers["/home"]())
            if page.route == "/":
                page.go("/home")
        elif page.route in route_handlers:
            page.views.append(route_handlers[page.route]())
        elif page.route.startswith("/treino/"):
            day = page.route.split("/")[-1]
            page.views.append(
                ft.View(
                    appbar=create_appbar(f"Treino - {day.capitalize()}"),
                    route=f"/treino/{day}",
                    controls=[Treinopage(page, supabase, day)],
                    vertical_alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    scroll=ft.ScrollMode.AUTO,
                )
            )

    @require_auth
    def handle_create_profile():
        """Manipula a rota de criação de perfil."""
        page.views.append(
            ft.View(
                appbar=create_appbar("Criar Perfil"),
                route="/create_profile",
                controls=[CreateProfilePage(page, supabase)],
                vertical_alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                padding=20,
            )
        )

    def route_change(route):
        """Manipulador principal de mudanças de rota."""
        page.views.clear()
        logger.info(f"Navegando para: {page.route}")

        try:
            # Rotas públicas
            if page.route in PUBLIC_ROUTES:
                handle_public_routes()

            # Rota de criação de perfil
            elif page.route == "/create_profile":
                handle_create_profile()

            # Rotas protegidas
            elif page.route in PROFILE_REQUIRED_ROUTES or page.route.startswith(
                "/treino/"
            ):
                handle_protected_routes()

            else:
                logger.warning(f"Rota não encontrada: {page.route}")
                redirect_to_login()

        except Exception as e:
            logger.error(f"Erro ao processar rota {page.route}: {e}")
            show_snackbar("Erro ao carregar página.", ft.Colors.RED_700)
            redirect_to_login()

        page.update()

    def view_pop(view):
        """Manipula o voltar das views."""
        if page.views:
            page.views.pop()
            top_view = page.views[-1] if page.views else None
            if top_view:
                page.go(top_view.route)
            else:
                page.go("/login")
        else:
            page.go("/login")

    # Manipuladores de evento
    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go(page.route)
