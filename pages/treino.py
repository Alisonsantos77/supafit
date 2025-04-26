import flet as ft
import threading
import time


def Treinopage(page: ft.Page, supabase, day):
    timer_text_ref = ft.Ref[ft.Text]()

    def load_exercises(day):
        try:
            response = (
                supabase.table("exercises").select("*").eq("day", day.lower()).execute()
            )
            return response.data or [
                {
                    "id": "1",
                    "name": "Supino Reto",
                    "sets": 4,
                    "reps": 12,
                    "load": 0,
                    "image_url": "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/bench_press.jpg",
                },
                {
                    "id": "2",
                    "name": "Agachamento Livre",
                    "sets": 4,
                    "reps": 10,
                    "load": 0,
                    "image_url": "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/squat.jpg",
                },
            ]
        except Exception as e:
            print(f"Erro ao carregar exercícios: {str(e)}")
            return [
                {
                    "id": "1",
                    "name": "Supino Reto",
                    "sets": 4,
                    "reps": 12,
                    "load": 0,
                    "image_url": "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/bench_press.jpg",
                },
                {
                    "id": "2",
                    "name": "Agachamento Livre",
                    "sets": 4,
                    "reps": 10,
                    "load": 0,
                    "image_url": "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/squat.jpg",
                },
            ]

    # iniciar o cronômetro
    def start_timer(e, seconds=60):
        for i in range(seconds, -1, -1):
            timer_text_ref.current.value = f"Intervalo: {i}s"
            timer_text_ref.current.update()
            time.sleep(1)
        page.snack_bar = ft.SnackBar(
            content=ft.Text("Intervalo concluído!"),
            action="OK",
        )
        page.snack_bar.open = True
        page.update()

    # salvar carga no Supabase
    def save_load(e, exercise_id):
        try:
            load = float(e.control.value) if e.control.value else 0
            supabase.table("progress").insert(
                {
                    "exercise_id": exercise_id,
                    "load": load,
                    "date": time.strftime("%Y-%m-%d %H:%M:%S"),
                }
            ).execute()
            page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Carga {load}kg salva!"),
                action="OK",
                action_color=ft.colors.WHITE,
            )
            page.snack_bar.open = True
        except Exception as e:
            page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Erro ao salvar carga: {str(e)}"),
                action="OK",
                action_color=ft.colors.WHITE,
            )
            page.snack_bar.open = True
        page.update()

    # Carregar exercícios para o dia
    exercises = load_exercises(day)

    exercise_list = ft.ListView(
        expand=True,
        spacing=10,
        controls=[
            ft.Card(
                content=ft.Container(
                    content=ft.Column(
                        [
                            ft.ListTile(
                                leading=ft.Image(
                                    src=exercise["image_url"],
                                    width=50,
                                    height=50,
                                    fit=ft.ImageFit.COVER,
                                    error_content=ft.Icon(ft.icons.ERROR),
                                ),
                                title=ft.Text(
                                    exercise["name"],
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.colors.BLUE_900,
                                ),
                                subtitle=ft.Text(
                                    f"{exercise['sets']} séries x {exercise['reps']} repetições",
                                    color=ft.colors.GREY_700,
                                ),
                                trailing=ft.TextField(
                                    label="Carga (kg)",
                                    value=str(exercise["load"]),
                                    width=100,
                                    keyboard_type=ft.KeyboardType.NUMBER,
                                    on_submit=lambda e, eid=exercise["id"]: save_load(
                                        e, eid
                                    ),
                                ),
                            ),
                            ft.ElevatedButton(
                                "Iniciar Intervalo (60s)",
                                on_click=lambda e: threading.Thread(
                                    target=start_timer, args=(e,)
                                ).start(),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    padding=10,
                ),
                elevation=5,
            )
            for exercise in exercises
        ],
    )

    # Texto do cronômetro
    timer_text = ft.Text(
        ref=timer_text_ref, value="Intervalo: --", size=16, color=ft.colors.BLUE_900
    )

    return ft.Container(
        content=ft.Column(
            [
                ft.Text(
                    f"Treino de {day.capitalize()}",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=ft.colors.BLUE_900,
                ),
                timer_text,
                exercise_list,
                ft.ElevatedButton(
                    "Voltar",
                    on_click=lambda _: page.go("/"),
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20,
        ),
        padding=20,
    )
