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


def setup_routes(page: ft.Page, supabase, anthropic):
    def route_change(route):
        page.views.clear()
        user_id = page.client_storage.get("user_id")
        print(f"Rota solicitada: {page.route}, user_id: {user_id}")

        # Redirecionar para /home se já autenticado e rota é /
        if user_id and page.route == "/":
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
            page.go("/home")
        # Redirecionar para login se não houver user_id, exceto para /login e /register
        elif not user_id and page.route not in ["/login", "/register"]:
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
        elif page.route == "/login":
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
                    scroll=ft.ScrollMode.AUTO,
                    padding=20,
                )
            )
        elif page.route == "/home":
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
        page.update()
        print(f"Rota alterada para: {page.route}")

    def view_pop(view):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go(page.route)
