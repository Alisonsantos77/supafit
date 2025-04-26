import flet as ft
from pages.home import Homepage
from pages.treino import Treinopage
from components.appbar_class import create_appbar


def setup_routes(page: ft.Page, supabase):
    page.title = "SupaFit"

    def route_change(route):
        page.views.clear()
        page.views.append(
            ft.View(
                route="/",
                appbar=create_appbar("SupaFit"),
                vertical_alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[Homepage(page, supabase)],
            )
        )
        if page.route.startswith("/treino/"):
            day = page.route.split("/")[-1].capitalize()
            page.views.append(
                ft.View(
                    route=page.route,
                    appbar=create_appbar(f"Treino de {day}"),
                    vertical_alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[Treinopage(page, supabase, day)],
                )
            )
        elif page.route == "/perfil":
            page.views.append(
                ft.View(
                    route="/perfil",
                    appbar=create_appbar("Perfil"),
                    controls=[
                        ft.Text("Perfil"),
                        ft.ElevatedButton(
                            text="Voltar", on_click=lambda _: page.go("/")
                        ),
                    ],
                )
            )
        elif page.route == "/historico":
            page.views.append(
                ft.View(
                    route="/historico",
                    appbar=create_appbar("Histórico"),
                    controls=[
                        ft.Text("Histórico"),
                        ft.ElevatedButton(
                            text="Voltar", on_click=lambda _: page.go("/")
                        ),
                    ],
                )
            )
        elif page.route == "/configuracoes":
            page.views.append(
                ft.View(
                    route="/configuracoes",
                    appbar=create_appbar("Configurações"),
                    controls=[
                        ft.Text("Configurações"),
                        ft.ElevatedButton(
                            text="Voltar", on_click=lambda _: page.go("/")
                        ),
                    ],
                )
            )

        print(f"Rota alterada para: {page.route}")
        page.update()

    def view_pop(view):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go(page.route)
