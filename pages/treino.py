import flet as ft
import asyncio
import requests
import logging
from components.exercise_tile import ExerciseTile
from components.components import TimerDialog
import os
from dotenv import load_dotenv

load_dotenv()

RAPID_API_KEY = os.getenv("RAPIDAPI_KEY")
logger = logging.getLogger("supafit.treino")

# Mapeamento de nomes de exercícios (português para inglês)
EXERCISE_NAME_MAPPING = {
    "Supino Reto": "bench press",
    "Crucifixo Inclinado": "incline dumbbell fly",  
    "Agachamento Livre": "squat",
    "Leg Press": "leg press",
    "Remada Curvada": "bent-over row",  
    "Rosca Direta": "bicep curl",  
    "Desenvolvimento de Ombros": "shoulder press",  
    "Supino Inclinado": "incline bench press",  
}


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
        """Função para visualizar os dados brutos retornados pela ExerciseDB API."""
        api_name = EXERCISE_NAME_MAPPING.get(exercise_name, exercise_name).lower()
        logger.debug(f"Mapeando {exercise_name} para {api_name} para a ExerciseDB API")

        url = f"https://exercisedb.p.rapidapi.com/exercises/name/{api_name}"
        headers = {
            "X-RapidAPI-Key": RAPID_API_KEY,
            "X-RapidAPI-Host": "exercisedb.p.rapidapi.com",
        }
        try:
            logger.debug(f"Buscando dados para {api_name} na ExerciseDB API")
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            # logger.info(f"Dados brutos da API para {api_name}: {data}")
            return data
        except Exception as e:
            logger.error(f"Erro ao buscar dados para {api_name}: {str(e)}")
            return None

    def fetch_exercise_animation(exercise_name):
        data = fetch_exercise_data(exercise_name)
        if data and isinstance(data, list) and data:
            # Selecionar o exercício mais relevante
            api_name = EXERCISE_NAME_MAPPING.get(exercise_name, exercise_name).lower()
            for exercise in data:
                exercise_name_lower = exercise["name"].lower()
                if (
                    api_name == "bench press"
                    and "barbell bench press" in exercise_name_lower
                ):
                    return {
                        "animation_url": exercise.get("gifUrl"),
                        "body_part": exercise.get("bodyPart"),
                        "target": exercise.get("target"),
                        "secondary_muscles": exercise.get("secondaryMuscles"),
                        "instructions": exercise.get("instructions"),
                    }
                if (
                    api_name == "incline bench press"
                    and "barbell incline bench press" in exercise_name_lower
                ):
                    return {
                        "animation_url": exercise.get("gifUrl"),
                        "body_part": exercise.get("bodyPart"),
                        "target": exercise.get("target"),
                        "secondary_muscles": exercise.get("secondaryMuscles"),
                        "instructions": exercise.get("instructions"),
                    }
                if api_name == "squat" and "barbell full squat" in exercise_name_lower:
                    return {
                        "animation_url": exercise.get("gifUrl"),
                        "body_part": exercise.get("bodyPart"),
                        "target": exercise.get("target"),
                        "secondary_muscles": exercise.get("secondaryMuscles"),
                        "instructions": exercise.get("instructions"),
                    }
                if (
                    api_name == "leg press"
                    and "sled 45° leg press" in exercise_name_lower
                ):
                    return {
                        "animation_url": exercise.get("gifUrl"),
                        "body_part": exercise.get("bodyPart"),
                        "target": exercise.get("target"),
                        "secondary_muscles": exercise.get("secondaryMuscles"),
                        "instructions": exercise.get("instructions"),
                    }
                if (
                    api_name == "bent-over row"
                    and "barbell bent-over row" in exercise_name_lower
                ):
                    return {
                        "animation_url": exercise.get("gifUrl"),
                        "body_part": exercise.get("bodyPart"),
                        "target": exercise.get("target"),
                        "secondary_muscles": exercise.get("secondaryMuscles"),
                        "instructions": exercise.get("instructions"),
                    }
                if api_name == "bicep curl" and "barbell curl" in exercise_name_lower:
                    return {
                        "animation_url": exercise.get("gifUrl"),
                        "body_part": exercise.get("bodyPart"),
                        "target": exercise.get("target"),
                        "secondary_muscles": exercise.get("secondaryMuscles"),
                        "instructions": exercise.get("instructions"),
                    }
                if (
                    api_name == "shoulder press"
                    and "barbell shoulder press" in exercise_name_lower
                ):
                    return {
                        "animation_url": exercise.get("gifUrl"),
                        "body_part": exercise.get("bodyPart"),
                        "target": exercise.get("target"),
                        "secondary_muscles": exercise.get("secondaryMuscles"),
                        "instructions": exercise.get("instructions"),
                    }
                if exercise.get("gifUrl"):
                    return {
                        "animation_url": exercise.get("gifUrl"),
                        "body_part": exercise.get("bodyPart"),
                        "target": exercise.get("target"),
                        "secondary_muscles": exercise.get("secondaryMuscles"),
                        "instructions": exercise.get("instructions"),
                    }
            logger.warning(f"Nenhum gifUrl encontrado nos dados para {exercise_name}")
        return {
            "animation_url": None,
            "body_part": None,
            "target": None,
            "secondary_muscles": None,
            "instructions": None,
        }

    def load_exercises(day):
        try:
            response = (
                supabase.table("exercises").select("*").eq("day", day.lower()).execute()
            )
            logger.info("Dados do Supabase (exercises): %s", response.data)
            if not response.data:
                logger.warning(f"Nenhum exercício encontrado para {day}")
            return [
                {
                    "id": exercise["id"],
                    "name": exercise["name"],
                    "series": exercise["sets"],
                    "repetitions": exercise["reps"],
                    "load": exercise["load"],
                    "image_url": exercise.get("image_url"),
                    **fetch_exercise_animation(exercise["name"]),
                }
                for exercise in (
                    response.data
                    or [
                        {
                            "id": "1",
                            "name": "Supino Reto",
                            "sets": 4,
                            "reps": 12,
                            "load": 0,
                            "image_url": "https://picsum.photos/200",
                        },
                        {
                            "id": "2",
                            "name": "Agachamento Livre",
                            "sets": 4,
                            "reps": 10,
                            "load": 0,
                            "image_url": "https://picsum.photos/200",
                        },
                    ]
                )
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
                    **fetch_exercise_animation("Supino Reto"),
                },
                {
                    "id": "2",
                    "name": "Agachamento Livre",
                    "series": 4,
                    "repetitions": 10,
                    "load": 0,
                    "image_url": "https://picsum.photos/200",
                    **fetch_exercise_animation("Agachamento Livre"),
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
                image_url=exercise["image_url"],
                body_part=exercise["body_part"],
                target=exercise["target"],
                secondary_muscles=exercise["secondary_muscles"],
                instructions=exercise["instructions"],
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
                    ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda e: page.go("/home")),
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
