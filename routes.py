import flet as ft
from pages.home import Homepage
from pages.treino import Treinopage
from components.appbar_class import create_appbar
from pages.login import LoginPage

def setup_routes(page: ft.Page, supabase, anthropic):
    def route_change(route):
        page.views.clear()
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
        if page.route == "/":
            page.window.height = 1920
            page.window.width = 1080
            page.views.append(
                ft.View(
                    route="/",
                    appbar=create_appbar("Supafit"),
                    controls=[Homepage(page, supabase)],
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
