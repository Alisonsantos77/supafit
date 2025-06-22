import flet as ft
import asyncio
import logging
import requests
from components.exercise_tile import ExerciseTile
from components.components import TimerDialog
from dotenv import load_dotenv
import os

load_dotenv()

logger = logging.getLogger("supafit.treino")

GYM_FIT_API_KEY = os.getenv("GYM_FIT_API_KEY")
GYM_FIT_API_HOST = "gymfit-api.p.rapidapi.com"

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
                page.go("/home")
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

    def fetch_exercise_data(exercise_name):
        """Busca dados do exercício na GymFit API."""
        try:
            querystring = {"name": exercise_name.replace(" ", "%20")}
            url = f"https://{GYM_FIT_API_HOST}/v1/exercises/search"  # Endpoint corrigido
            headers = {
                "X-RapidAPI-Key": GYM_FIT_API_KEY,
                "X-RapidAPI-Host": GYM_FIT_API_HOST
            }
            response = requests.get(url, headers=headers, params=querystring)
            response.raise_for_status()
            data = response.json()

            if data and isinstance(data, list) and len(data) > 0:
                exercise = data[0]
                return {
                    "animation_url": exercise.get("image_url", "https://picsum.photos/200"),
                    "video_url": exercise.get("video_url"),
                    "body_part": exercise.get("bodyPart", exercise.get("body_part")),
                    "target": exercise.get("target_muscle", exercise.get("target")),
                    "secondary_muscles": exercise.get("secondary_muscles", []),
                    "instructions": exercise.get("instructions", []),
                    "exercise_tips": exercise.get("tips", []),
                }
            logger.warning(f"Nenhum exercício encontrado na GymFit API para {exercise_name}")
            return {
                "animation_url": "https://picsum.photos/200",
                "video_url": None,
                "body_part": None,
                "target": None,
                "secondary_muscles": [],
                "instructions": [],
                "exercise_tips": [],
            }
        except Exception as e:
            logger.error(f"Erro ao buscar dados para {exercise_name}: {str(e)}")
            return {
                "animation_url": "https://picsum.photos/200",
                "video_url": None,
                "body_part": None,
                "target": None,
                "secondary_muscles": [],
                "instructions": [],
                "exercise_tips": [],
            }

    def load_exercises(day):
        try:
            # Tenta carregar do Supabase primeiro
            response = (
                supabase.client.table("exercises").select("*").eq("day", day.lower()).execute()
            )
            logger.info("Dados do Supabase (exercises): %s", response.data)
            if not response.data:
                logger.warning(f"Nenhum exercício encontrado para {day} no Supabase")
                # Consulta GymFit API como fallback
                querystring = {"day": day.lower(), "limit": "2"}  # Limita a 2 para testes
                url = f"https://{GYM_FIT_API_HOST}/v1/exercises/search"
                headers = {
                    "X-RapidAPI-Key": GYM_FIT_API_KEY,
                    "X-RapidAPI-Host": GYM_FIT_API_HOST
                }
                api_response = requests.get(url, headers=headers, params=querystring)
                api_response.raise_for_status()
                exercises = api_response.json()
                return [
                    {
                        "id": exercise.get("id", f"api_{i}"),
                        "name": exercise.get("name", f"Exercise_{i}"),
                        "series": exercise.get("sets", 4),
                        "repetitions": exercise.get("reps", 12),
                        "load": exercise.get("load", 0),
                        "image_url": exercise.get("image_url", "https://picsum.photos/200"),
                        **fetch_exercise_data(exercise.get("name", f"Exercise_{i}")),
                    }
                    for i, exercise in enumerate(exercises[:2])  # Limita a 2 para testes
                ]
            return [
                {
                    "id": exercise["id"],
                    "name": exercise["name"],
                    "series": exercise["sets"],
                    "repetitions": exercise["reps"],
                    "load": exercise["load"],
                    "image_url": exercise.get("image_url"),
                    **fetch_exercise_data(exercise["name"]),
                }
                for exercise in response.data
            ]
        except Exception as e:
            logger.error(f"Erro ao carregar exercícios para {day}: {str(e)}")
            return [
                {
                    "id": "1",
                    "name": "Supino Reto",
                    "series": 4,
                    "repetitions": 12,
                    "load": 0,
                    "image_url": "https://picsum.photos/200",
                    **fetch_exercise_data("Supino Reto"),
                },
                {
                    "id": "2",
                    "name": "Agachamento Livre",
                    "series": 4,
                    "repetitions": 10,
                    "load": 0,
                    "image_url": "https://picsum.photos/200",
                    **fetch_exercise_data("Agachamento Livre"),
                },
            ]

    def update_load(load):
        pass

    def favorite_exercise(exercise_tile):
        try:
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
            logger.error(f"Erro ao favoritar exercício: {str(e)}")
            page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Erro ao favoritar: {str(e)}"), action="OK"
            )
            page.snack_bar.open = True

    # Carregar exercícios
    exercises = load_exercises(day)

    # Lista de exercícios
    exercise_list = ft.ListView(
        controls=[
            ExerciseTile(
                exercise_name=exercise["name"],
                series=exercise["series"],
                repetitions=exercise["repetitions"],
                load=exercise["load"],
                animation_url=exercise["animation_url"],
                video_url=exercise["video_url"],
                image_url=exercise["image_url"],
                body_part=exercise["body_part"],
                target=exercise["target"],
                secondary_muscles=exercise["secondary_muscles"],
                instructions=exercise["instructions"],
                exercise_tips=exercise["exercise_tips"],
                on_favorite_click=favorite_exercise,
                on_load_save=update_load,
                supabase=supabase,
                exercise_id=exercise["id"],
                page=page,
            )
            for exercise in exercises
        ],
        expand=True,
        spacing=10,
        padding=10,
    )

    # Controles no topo
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
        content=ft.ResponsiveRow(
            [
                ft.Container(
                    ft.IconButton(
                        ft.Icons.ARROW_BACK, on_click=lambda e: page.go("/home")
                    ),
                    col={"sm": 2, "md": 1},
                ),
                ft.Container(
                    ft.Text(ref=training_timer_ref, value="Tempo: 00:00", size=16),
                    col={"sm": 5, "md": 6},
                    alignment=ft.alignment.center,
                ),
                ft.Container(
                    content=ft.Row(
                        [pause_button, resume_button, finish_button],
                        spacing=5,
                        wrap=True,
                    ),
                    col={"sm": 5, "md": 5},
                    alignment=ft.alignment.center,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            spacing=10,
            run_spacing=5,
        ),
        padding=ft.padding.symmetric(horizontal=10, vertical=5),
        border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.GREY_300)),
    )

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