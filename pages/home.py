import flet as ft
from components.days_time import DaysTime
from components.avatar_component import AvatarComponent


def Homepage(page: ft.Page, supabase):
    def go_to_workout(e, day):
        page.go(f"/treino/{day.lower()}")

    def load_workouts():
        try:
            response = supabase.table("workouts").select("*").execute()
            return {w["day"].capitalize(): w["name"] for w in response.data} or {
                "Segunda": "Peito e Tríceps",
                "Terça": "Costas e Bíceps",
                "Quarta": "Pernas",
                "Quinta": "Ombros",
                "Sexta": "Peito e Tríceps",
                "Sábado": "Descanso",
                "Domingo": "Descanso",
            }
        except Exception as e:
            print(f"Erro ao carregar treinos: {str(e)}")
            return {
                "Segunda": "Peito e Tríceps",
                "Terça": "Costas e Bíceps",
                "Quarta": "Pernas",
                "Quinta": "Ombros",
                "Sexta": "Peito e Tríceps",
                "Sábado": "Descanso",
                "Domingo": "Descanso",
            }

    workouts = load_workouts()

    days_grid = ft.ResponsiveRow(
        controls=[
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text(
                            day,
                            weight=ft.FontWeight.BOLD,
                            size=16,
                            color=ft.Colors.WHITE,
                        ),
                        ft.Text(
                            workouts.get(day, "Sem treino"),
                            size=14,
                            color=ft.Colors.WHITE70,
                        ),
                        ft.ElevatedButton(
                            "Ver Treino",
                            on_click=lambda e, d=day: go_to_workout(e, d),
                            disabled=workouts.get(day) == "Descanso",
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                padding=15,
                border_radius=8,
                col={"xs": 6, "sm": 4, "md": 3},
            )
            for day in [
                "Segunda",
                "Terça",
                "Quarta",
                "Quinta",
                "Sexta",
                "Sábado",
                "Domingo",
            ]
        ],
        columns=12,
        spacing=10,
        run_spacing=10,
    )

    texto = ft.Text(
        "Bem vindo ao SupaFit",
        size=24,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.BLUE_900,
    )
    avatar = AvatarComponent(image_url="profile_teste.png", radius=100)
    days_time = DaysTime(page)

    return ft.Container(
        content=ft.Column(
            [
                texto,
                avatar,
                ft.Text(
                    "Frequência de Treino",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLUE_900,
                ),
                days_time,
                ft.Text(
                    "Treinos da Semana",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLUE_900,
                ),
                days_grid,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20,
        ),
        padding=20,
    )
