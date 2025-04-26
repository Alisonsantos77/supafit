import flet as ft
from components.custom_list_tile import CustomListTile
from datetime import datetime


def Homepage(page: ft.Page, supabase):
    def load_workouts():
        try:
            response = supabase.table("workouts").select("*").execute()
            if not response.data:
                print("Nenhum treino encontrado")
            return [
                {
                    **workout,
                    "image_url": workout.get("image_url", "https://picsum.photos/200"),
                }
                for workout in (
                    response.data
                    or [
                        {
                            "day": "segunda",
                            "name": "Peito e Tríceps",
                            "image_url": "https://picsum.photos/200",
                        },
                        {
                            "day": "terça",
                            "name": "Costas e Bíceps",
                            "image_url": "https://picsum.photos/200",
                        },
                        {
                            "day": "quarta",
                            "name": "Pernas",
                            "image_url": "https://picsum.photos/200",
                        },
                        {
                            "day": "quinta",
                            "name": "Ombros",
                            "image_url": "https://picsum.photos/200",
                        },
                        {
                            "day": "sexta",
                            "name": "Peito e Tríceps",
                            "image_url": "https://picsum.photos/200",
                        },
                        {
                            "day": "sábado",
                            "name": "Descanso",
                            "image_url": "https://picsum.photos/200",
                        },
                        {
                            "day": "domingo",
                            "name": "Descanso",
                            "image_url": "https://picsum.photos/200",
                        },
                    ]
                )
            ]
        except Exception as e:
            print(f"Erro ao carregar treinos: {str(e)}")
            return [
                {
                    "day": "segunda",
                    "name": "Peito e Tríceps",
                    "image_url": "https://picsum.photos/200",
                },
                {
                    "day": "terça",
                    "name": "Costas e Bíceps",
                    "image_url": "https://picsum.photos/200",
                },
                {
                    "day": "quarta",
                    "name": "Pernas",
                    "image_url": "https://picsum.photos/200",
                },
                {
                    "day": "quinta",
                    "name": "Ombros",
                    "image_url": "https://picsum.photos/200",
                },
                {
                    "day": "sexta",
                    "name": "Peito e Tríceps",
                    "image_url": "https://picsum.photos/200",
                },
                {
                    "day": "sábado",
                    "name": "Descanso",
                    "image_url": "https://picsum.photos/200",
                },
                {
                    "day": "domingo",
                    "name": "Descanso",
                    "image_url": "https://picsum.photos/200",
                },
            ]

    workouts = load_workouts()
    current_day = datetime.now().strftime("%A").lower()
    day_map = {
        "monday": "segunda",
        "tuesday": "terça",
        "wednesday": "quarta",
        "thursday": "quinta",
        "friday": "sexta",
        "saturday": "sábado",
        "sunday": "domingo",
    }
    current_day = day_map.get(current_day, "segunda")

    workout_grid = ft.ResponsiveRow(
        controls=[
            ft.Card(
                col=10,
                content=ft.Container(
                    content=ft.Column(
                        [
                            CustomListTile(
                                leading=ft.Image(
                                    src=workout["image_url"],
                                    width=64,
                                    height=150,
                                    fit=ft.ImageFit.COVER,
                                    border_radius=ft.border_radius.all(10),
                                    error_content=ft.Icon(ft.Icons.ERROR),
                                ),
                                title=ft.Text(
                                    workout["name"], weight=ft.FontWeight.BOLD
                                ),
                                subtitle=ft.Text(workout["day"].capitalize()),
                                trailing=ft.Stack(
                                    [
                                        ft.Checkbox(
                                            value=workout["day"] == current_day
                                        ),
                                    ]
                                ),
                            ),
                            ft.Text(
                                "Hoje é dia de descanso",
                                theme_style=ft.TextThemeStyle.LABEL_MEDIUM,
                                color=ft.Colors.GREY,
                                italic=True,
                                visible=workout["name"] == "Descanso",
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                            ft.ElevatedButton(
                                "Ver Treino",
                                on_click=lambda e, day=workout["day"]: page.go(
                                    f"/treino/{day}"
                                ),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        expand=False,
                    ),
                    padding=5,
                ),
                elevation=3,
            )
            for workout in workouts
        ],
        columns=12,
        spacing=10,
        run_spacing=10,
    )

    return ft.Container(
        content=ft.Column(
            [
                ft.Text("Frequência de Treino", size=24, weight=ft.FontWeight.BOLD),
                workout_grid,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20,
            scroll=ft.ScrollMode.AUTO,
        ),
        padding=10,
    )
