import flet as ft
from pages.home import Homepage
from pages.treino import Treinopage
from pages.profile_settings import ProfileSettingsPage
from pages.history import HistoryPage
from components.appbar_class import create_appbar
from pages.login import LoginPage
from pages.register import RegisterPage
from pages.community_tab import CommunityTab
from pages.trainer_tab import TrainerTab
from pages.terms_page import TermsPage
from pages.create_profile import CreateProfilePage
import logging

logger = logging.getLogger("supafit.routes")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


def setup_routes(page: ft.Page, supabase, anthropic):
    def route_change(route):
        page.views.clear()
        user_id = page.client_storage.get("supafit.user_id")
        profile_created = page.client_storage.get("supafit.profile_created")
        logger.info(f"Rota solicitada: {page.route}, user_id: {user_id}, profile_created: {profile_created}")

        # Rotas públicas
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
        elif user_id:
            if not profile_created and page.route not in ["/create_profile"]:
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
        else:
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
        logger.info(f"Rota alterada para: {page.route}")

    def view_pop(view):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go(page.route)