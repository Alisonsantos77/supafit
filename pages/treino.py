import flet as ft
import asyncio
from components.exercise_tile import ExerciseTile
from components.timer_dialog import TimerDialog
from services.images_splash import get_unsplash_image


def Treinopage(page: ft.Page, supabase, day):
    # Estado do treino
    training_started = False
    training_time = 0
    training_running = False
    training_timer_ref = ft.Ref[ft.Text]()

    async def run_training_timer():
        nonlocal training_time, training_running
        while training_running:
            training_time += 1
            minutes, seconds = divmod(training_time, 60)
            training_timer_ref.current.value = f"Tempo: {minutes:02d}:{seconds:02d}"
            training_timer_ref.current.update()
            await asyncio.sleep(1)

    def start_training(e):
        nonlocal training_started, training_running
        training_started = True
        training_running = True
        for exercise_tile in exercise_list.controls:
            exercise_tile.enable_controls()
        start_button.visible = False
        pause_button.visible = True
        resume_button.visible = False
        finish_button.visible = True
        page.run_task(run_training_timer)
        page.update()

    def stop_training(e):
        nonlocal training_running

        def confirm_finish(e):
            if e.control.text == "Sim":
                training_running = False
                page.go("/")
            page.close(confirm_dialog)

        confirm_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Finalizar Treino"),
            content=ft.Text("Deseja realmente finalizar o treino?"),
            actions=[
                ft.TextButton("Sim", on_click=confirm_finish),
                ft.TextButton("Não", on_click=confirm_finish),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.open(confirm_dialog)

    def pause_training(e):
        nonlocal training_running
        training_running = False
        pause_button.visible = False
        resume_button.visible = True
        page.update()

    def resume_training(e):
        nonlocal training_running
        training_running = True
        page.run_task(run_training_timer)
        pause_button.visible = True
        resume_button.visible = False
        page.update()

    def handle_reorder(e):
        print(f"Exercício movido de {e.old_index} para {e.new_index}")
        # Atualizar a ordem no Supabase
        # exercises[e.old_index], exercises[e.new_index] = exercises[e.new_index], exercises[e.old_index]
        # supabase.table("exercises").update({"order": e.new_index}).eq("id", exercises[e.new_index]["id"]).execute()

    def load_exercises(day):
        try:
            response = (
                supabase.table("exercises").select("*").eq("day", day.lower()).execute()
            )
            print("Dados do Supabase (exercises):", response.data)
            if not response.data:
                print(f"Nenhum exercício encontrado para {day}")
            return [
                {
                    **exercise,
                    "image_url": get_unsplash_image(exercise["name"]),
                }
                for exercise in (
                    response.data
                    or [
                        {
                            "id": "1",
                            "name": "Supino Reto",
                            "series": 4,
                            "repetitions": 12,
                            "load": 0,
                            "image_url": "https://picsum.photos/200",
                        },
                        {
                            "id": "2",
                            "name": "Agachamento Livre",
                            "series": 4,
                            "repetitions": 10,
                            "load": 0,
                            "image_url": "https://picsum.photos/200",
                        },
                    ]
                )
            ]
        except Exception as e:
            print(f"Erro ao carregar exercícios para {day}: {str(e)}")
            return [
                {
                    "id": "1",
                    "name": "Supino Reto",
                    "series": 4,
                    "repetitions": 12,
                    "load": 0,
                    "image_url": "https://picsum.photos/200",
                },
                {
                    "id": "2",
                    "name": "Agachamento Livre",
                    "series": 4,
                    "repetitions": 10,
                    "load": 0,
                    "image_url": "https://picsum.photos/200",
                },
            ]

    def update_load(load):
        pass  # Pode ser implementado para atualizar a carga localmente

    def play_exercise(e):
        page.snack_bar = ft.SnackBar(content=ft.Text("Iniciando vídeo do exercício..."))
        page.snack_bar.open = True
        page.update()

    def favorite_exercise(exercise_tile):
        try:
            # Exemplo: Atualizar o status de favorito no Supabase
            # supabase.table("exercises").update({"is_favorited": exercise_tile.is_favorited}).eq("id", exercise_tile.exercise_id).execute()
            page.snack_bar = ft.SnackBar(
                content=ft.Text(
                    "Exercício favoritado!"
                    if exercise_tile.is_favorited
                    else "Exercício desfavoritado!"
                ),
                action="OK",
            )
            page.snack_bar.open = True
            page.update()
        except Exception as e:
            page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Erro ao favoritar: {str(e)}"), action="OK"
            )
            page.snack_bar.open = True

    # Carregar exercícios
    exercises = load_exercises(day)

    # Lista de exercícios com reordenamento
    exercise_list = ft.ReorderableListView(
        controls=[
            ExerciseTile(
                exercise_name=exercise["name"],
                series=exercise["series"],
                repetitions=exercise["repetitions"],
                load=exercise["load"],
                image_url=exercise["image_url"],
                on_play_click=play_exercise,
                on_favorite_click=favorite_exercise,
                on_load_save=update_load,
                supabase=supabase,
                exercise_id=exercise["id"],
                page=page,
            )
            for exercise in exercises
        ],
        expand=True,
        padding=10,
        on_reorder=handle_reorder,
    )

    # Controles no topo (substituindo AppBar)
    start_button = ft.ElevatedButton(
        "Iniciar Treino",
        on_click=start_training,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        ref=ft.Ref[ft.ElevatedButton](),
    )
    pause_button = ft.IconButton(
        ft.Icons.PAUSE,
        on_click=pause_training,
        visible=False,
        ref=ft.Ref[ft.IconButton](),
    )
    resume_button = ft.IconButton(
        ft.Icons.PLAY_ARROW,
        on_click=resume_training,
        visible=False,
        ref=ft.Ref[ft.IconButton](),
    )
    finish_button = ft.ElevatedButton(
        "Finalizar Treino",
        on_click=stop_training,
        visible=False,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        ref=ft.Ref[ft.ElevatedButton](),
    )

    control_bar = ft.Container(
        content=ft.Row(
            [
                ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda e: page.go("/")),
                ft.Text(ref=training_timer_ref, value="Tempo: 00:00", size=16),
                pause_button,
                resume_button,
                finish_button,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10,
        ),
        padding=ft.padding.symmetric(horizontal=10, vertical=5),
        border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.GREY_100)),
    )

    # Layout principal
    return ft.Column(
        [
            control_bar,
            ft.Container(
                content=start_button,
                alignment=ft.alignment.center,
                padding=10,
                visible=not training_started,
            ),
            exercise_list,
        ],
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        alignment=ft.MainAxisAlignment.START,
    )
