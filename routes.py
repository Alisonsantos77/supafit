import flet as ft
from pages.home import Homepage
from pages.treino import Treinopage
from pages.profile_settings import ProfileSettingsPage
from pages.history import HistoryPage
from components.appbar_class import create_appbar
from pages.login import LoginPage
from pages.register import RegisterPage
from pages.community_tab import CommunityTab
from pages.trainer_chat.trainer_main import TrainerTab
from pages.terms_page import TermsPage
from pages.profile_user.create_profile import CreateProfilePage
import logging

logger = logging.getLogger("supafit.routes")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


def setup_routes(page: ft.Page, supabase, anthropic):
    """Configura as rotas do aplicativo SupaFit.

    Args:
        page (ft.Page): Página Flet para gerenciar rotas e visualizações.
        supabase: Instância do serviço Supabase para autenticação e dados.
        anthropic: Instância do serviço Anthropic para funcionalidades de IA.
    """

    def show_snackbar(message: str, color: str = ft.Colors.RED_700):
        """Exibe uma SnackBar com feedback para o usuário.

        Args:
            message (str): Mensagem a ser exibida.
            color (str): Cor da SnackBar (padrão: vermelho para erros).
        """
        page.snack_bar = ft.SnackBar(
            content=ft.Text(message, color=ft.Colors.WHITE),
            bgcolor=color,
            duration=3000,
        )
        page.snack_bar.open = True
        page.update()
        logger.info(f"SnackBar exibida: {message}")

    def validate_session():
        """Valida a sessão ativa com o Supabase.

        Returns:
            bool: True se a sessão é válida, False caso contrário.
        """
        try:
            user = supabase.client.auth.get_user()
            if user and user.user:
                user_id = page.client_storage.get("supafit.user_id")
                if user_id and user_id == user.user.id:
                    return True
                logger.warning(
                    f"User_id no client_storage ({user_id}) não corresponde ao usuário autenticado ({user.user.id})."
                )
            logger.warning("Nenhuma sessão ativa encontrada no Supabase.")
            return False
        except Exception as e:
            logger.error(f"Erro ao validar sessão: {str(e)}")
            return False

    def route_change(route):
        page.views.clear()
        user_id = page.client_storage.get("supafit.user_id")
        profile_created = (
            page.client_storage.get("supafit.profile_created") or False
        )
        logger.info(
            f"Rota solicitada: {page.route}, user_id: {user_id}, profile_created: {profile_created}"
        )

        # Rotas públicas
        if page.route in ["/login", "/register", "/terms"]:
            if page.route == "/login":
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
            elif page.route == "/register":
                page.views.append(
                    ft.View(
                        appbar=create_appbar("Registrar - Supafit"),
                        route="/register",
                        controls=[RegisterPage(page)],
                        vertical_alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        scroll=ft.ScrollMode.AUTO,
                    )
                )
            elif page.route == "/terms":
                page.views.append(
                    ft.View(
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
                    )
                )
        # Rotas protegidas
        elif user_id and validate_session():
            try:
                # Verificar perfil no Supabase
                profile_response = supabase.get_profile(user_id)
                profile_exists = bool(
                    profile_response.data and len(profile_response.data) > 0
                )
                page.client_storage.set("supafit.profile_created", profile_exists)
                if profile_exists:
                    page.client_storage.set(
                        "supafit.level",
                        profile_response.data[0].get("level", "iniciante"),
                    )
                    logger.info(
                        f"Perfil encontrado para user_id: {user_id}, nível: {page.client_storage.get('supafit.level')}"
                    )

                if not profile_exists and page.route not in ["/create_profile"]:
                    logger.info(
                        f"Perfil não encontrado para user_id: {user_id}. Redirecionando para /create_profile."
                    )
                    show_snackbar(
                        "Por favor, crie seu perfil para continuar.", ft.Colors.BLUE_400
                    )
                    page.views.append(
                        ft.View(
                            appbar=create_appbar("Criar Perfil"),
                            route="/create_profile",
                            controls=[CreateProfilePage(page, supabase)],
                            vertical_alignment=ft.MainAxisAlignment.CENTER,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            scroll=ft.ScrollMode.AUTO,
                            padding=20,
                        )
                    )
                    page.go("/create_profile")
                elif page.route == "/create_profile":
                    page.views.append(
                        ft.View(
                            appbar=create_appbar("Criar Perfil"),
                            route="/create_profile",
                            controls=[CreateProfilePage(page, supabase)],
                            vertical_alignment=ft.MainAxisAlignment.CENTER,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            scroll=ft.ScrollMode.AUTO,
                            padding=20,
                        )
                    )
                elif page.route == "/home" or page.route == "/":
                    page.views.append(
                        ft.View(
                            route="/home",
                            appbar=create_appbar("Supafit"),
                            controls=[Homepage(page, supabase)],
                            vertical_alignment=ft.MainAxisAlignment.CENTER,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            scroll=ft.ScrollMode.AUTO,
                            padding=20,
                        )
                    )
                    if page.route == "/":
                        page.go("/home")
                elif page.route == "/community":
                    page.views.append(
                        ft.View(
                            appbar=create_appbar("Comunidade"),
                            route="/community",
                            controls=[CommunityTab(page, supabase)],
                            padding=20,
                            scroll=ft.ScrollMode.AUTO,
                        )
                    )
                elif page.route == "/trainer":
                    page.views.append(
                        ft.View(
                            appbar=create_appbar("Treinador"),
                            route="/trainer",
                            controls=[TrainerTab(page, supabase, anthropic)],
                            vertical_alignment=ft.MainAxisAlignment.CENTER,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            padding=20,
                        )
                    )
                elif page.route == "/profile_settings":
                    page.views.append(
                        ft.View(
                            appbar=create_appbar("Perfil e Configurações"),
                            route="/profile_settings",
                            controls=[ProfileSettingsPage(page)],
                            vertical_alignment=ft.MainAxisAlignment.CENTER,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            scroll=ft.ScrollMode.AUTO,
                            padding=20,
                        )
                    )
                elif page.route == "/history":
                    page.views.append(
                        ft.View(
                            appbar=create_appbar("Histórico"),
                            route="/history",
                            controls=[HistoryPage(page, supabase)],
                            vertical_alignment=ft.MainAxisAlignment.CENTER,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            scroll=ft.ScrollMode.AUTO,
                            padding=20,
                        )
                    )
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
            except Exception as e:
                logger.error(f"Erro ao processar rota {page.route}: {str(e)}")
                show_snackbar(
                    "Erro ao carregar a página. Tente novamente.", ft.Colors.RED_700
                )
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
        else:
            logger.info(
                "Sessão inválida ou nenhum user_id. Redirecionando para /login."
            )
            show_snackbar("Por favor, faça login para continuar.", ft.Colors.BLUE_400)
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

        page.update()
        # logger.info(f"Rota alterada para: {page.route}")

    def view_pop(view):
        if page.views:
            page.views.pop()
            top_view = page.views[-1] if page.views else None
            if top_view:
                page.go(top_view.route)
            else:
                page.go("/login")
        else:
            page.go("/login")

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go(page.route)
