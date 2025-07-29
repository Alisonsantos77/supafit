import os
import asyncio
import flet as ft
from dotenv import load_dotenv
from supabase import create_client, Client
import logging
from pages.training.exercise_tile import ExerciseTile
from .training_components import (
    TrainingTimer,
    EmptyTrainingState,
    TrainingProgress,
    FinishTrainingDialog,
    RestTimerDialog,
)
logger = logging.getLogger("supafit.treino")
load_dotenv()

efr_url = os.getenv("SUPABASE_URL")
efr_key = os.getenv("SUPABASE_KEY")
db: Client = create_client(efr_url, efr_key)


def Treinopage(page: ft.Page, supabase: any, day: str, user_id: str):
    """Página de treino moderna e responsiva que carrega exercícios do Supabase para o dia informado."""

    # Estado do treino
    training_started = False
    completed_exercises = 0

    # Refs para acessar componentes
    training_timer_ref = ft.Ref[TrainingTimer]()
    progress_ref = ft.Ref[TrainingProgress]()
    exercises_column_ref = ft.Ref[ft.Column]()

    def load_exercises(day: str, user_id: str):
        print(
            f"INFO - treino: Ignorando cache. Carregando exercícios diretamente do Supabase para {day} e user_id {user_id}"
        )
        raw_day = day.capitalize()
        print(
            f"DEBUG - treino: Filtrando exercícios para day = '{raw_day}' (via raw param '{day}')"
        )
        try:
            response = (
                supabase.client.table("user_plans")
                .select(
                    "plan_id, plan_exercises(exercise_id, sets, reps, order, exercicios(nome, url_video))"
                )
                .eq("user_id", user_id)
                .eq("day", raw_day)
                .order("order", desc=False, foreign_table="plan_exercises")
                .execute()
            )
            data = response.data or []
            print(
                f"DEBUG - treino: Dados brutos de user_plans para '{raw_day}':\n{data}"
            )
            exercises = []
            if data and data[0].get("plan_exercises"):
                plan_id = data[0].get("plan_id")
                for plan_ex in data[0]["plan_exercises"]:
                    exercise = plan_ex.get("exercicios", {})
                    exercises.append(
                        {
                            "name": exercise.get("nome", ""),
                            "series": plan_ex.get("sets", 0),
                            "repetitions": plan_ex.get("reps", ""),
                            "load": supabase.get_latest_exercise_load(
                                user_id, plan_ex.get("exercise_id", "")
                            ),
                            "video_url": exercise.get("url_video", None),
                            "exercise_id": plan_ex.get("exercise_id", ""),
                            "plan_id": plan_id,
                        }
                    )
                print(
                    f"INFO - treino: Carregados {len(exercises)} exercícios para {raw_day} e user_id {user_id}"
                )
            else:
                print(
                    f"WARNING - treino: Nenhum exercício encontrado para {raw_day} e user_id {user_id}"
                )
                return []
            return exercises
        except Exception as e:
            print(f"ERROR - treino: Erro ao carregar exercícios do Supabase: {str(e)}")
            return []

    def load_rest_duration(user_id: str):
        try:
            profile_response = (
                supabase.client.table("user_profiles")
                .select("rest_duration")
                .eq("user_id", user_id)
                .execute()
            )
            if profile_response.data and len(profile_response.data) > 0:
                rest_duration = profile_response.data[0].get("rest_duration", 60)
                print(
                    f"INFO - treino: rest_duration carregado para user_id {user_id}: {rest_duration}s"
                )
                return rest_duration
            else:
                print(
                    f"WARNING - treino: Perfil não encontrado para user_id {user_id}, usando rest_duration padrão: 60s"
                )
                return 60
        except Exception as e:
            print(
                f"ERROR - treino: Erro ao carregar rest_duration do Supabase: {str(e)}"
            )
            return 60

    rest_duration = load_rest_duration(user_id)
    exercises = load_exercises(day, user_id)

    if not exercises:
        return EmptyTrainingState(
            day
        )

    exercise_refs = []

    def on_training_start():
        nonlocal training_started
        training_started = True
        for exercise_ref in exercise_refs:
            if exercise_ref.current and hasattr(
                exercise_ref.current, "enable_controls"
            ):
                exercise_ref.current.enable_controls()
        if progress_ref.current:
            progress_ref.current.visible = True
            page.update()
        print(f"INFO - treino: Treino iniciado para o dia {day} e user_id {user_id}")

    def on_training_pause():
        print(f"INFO - treino: Treino pausado para o dia {day} e user_id {user_id}")

    def on_training_resume():
        print(f"INFO - treino: Treino retomado para o dia {day} e user_id {user_id}")

    def on_training_finish():
        nonlocal completed_exercises
        finish_dialog = FinishTrainingDialog(
            training_time=(
                training_timer_ref.current.training_time
                if training_timer_ref.current
                else 0
            ),
            completed_exercises=completed_exercises,
            total_exercises=len(exercises),
            on_confirm=lambda: page.go("/home"),
        )
        page.open(finish_dialog)
        print(f"INFO - treino: Diálogo de finalização aberto para o dia {day}")

    def on_exercise_complete(increment=True):
        """Callback atualizado para lidar com incremento/decremento"""
        nonlocal completed_exercises
        
        if increment:
            completed_exercises += 1
            logger.info(f"Exercício concluído. Total: {completed_exercises}/{len(exercises)}")
        else:
            completed_exercises = max(0, completed_exercises - 1)  # Previne valores negativos
            logger.info(f"Exercício desmarcado. Total: {completed_exercises}/{len(exercises)}")
        
        if progress_ref.current:
            progress_ref.current.update_progress(completed_exercises)
        
        # Verifica se todos os exercícios foram concluídos
        if completed_exercises >= len(exercises):
            page.snack_bar = ft.SnackBar(
                content=ft.Text("🎉 Parabéns! Todos os exercícios foram concluídos!"),
                bgcolor=ft.Colors.GREEN_700,
                duration=5000,
            )
            page.snack_bar.open = True
            page.update()

    def favorite_ex(tile):
        msg = (
            "Exercício favoritado!" if tile.is_favorited else "Exercício desfavoritado!"
        )
        page.snack_bar = ft.SnackBar(
            content=ft.Text(msg),
            bgcolor=ft.Colors.GREEN_700 if tile.is_favorited else ft.Colors.RED_700,
        )
        page.snack_bar.open = True
        page.update()
        print(
            f"INFO - treino: Exercício {tile.exercise_name} {'favoritado' if tile.is_favorited else 'desfavoritado'}"
        )

    training_timer = TrainingTimer(
        ref=training_timer_ref,
        on_start=on_training_start,
        on_pause=on_training_pause,
        on_resume=on_training_resume,
        on_finish=on_training_finish,
    )
    progress_container = TrainingProgress(
        completed_exercises, len(exercises), ref=progress_ref, visible=False
    )
    exercises_column = ft.Column(
        ref=exercises_column_ref,
        spacing=15,
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        controls=[],
    )

    for ex in exercises:
        exercise_ref = ft.Ref[ExerciseTile]()
        exercise_refs.append(exercise_ref)
        exercise_tile = ExerciseTile(
            ref=exercise_ref,
            exercise_name=ex["name"],
            series=ex["series"],
            repetitions=ex["repetitions"],
            load=ex["load"],
            video_url=ex["video_url"],
            exercise_id=ex["exercise_id"],
            plan_id=ex["plan_id"],
            user_id=user_id,
            on_favorite_click=favorite_ex,
            on_load_save=lambda v, name=ex["name"]: print(
                f"INFO - treino: Carga salva para {name}: {v}kg"
            ),
            on_complete=on_exercise_complete,
            page=page,
            supabase=supabase,
            rest_duration=rest_duration,
        )
        exercises_column.controls.append(
            exercise_tile
        )

    return ft.Column(
        [
            ft.Container(height=10),
            training_timer,
            ft.Container(height=10),
            progress_container,
            ft.Container(height=15),
            exercises_column,
        ],
        spacing=0,
        expand=True,
    )


def show_rest_timer(page: ft.Page, duration: int, exercise_name: str):
    """Função utilitária para exibir o timer de descanso"""

    def on_timer_complete():
        print(f"INFO - treino: Timer de descanso concluído para {exercise_name}")

    rest_timer = RestTimerDialog(
        duration=duration,
        exercise_name=exercise_name,
        on_complete=on_timer_complete,
        page=page,
    )
    rest_timer.start_timer(page)
