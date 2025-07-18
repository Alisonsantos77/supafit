import os
import asyncio
import flet as ft
from dotenv import load_dotenv
from supabase import create_client, Client
from components.exercise_tile import ExerciseTile
from components.components import TimerDialog

load_dotenv()

efr_url = os.getenv("SUPABASE_URL")
efr_key = os.getenv("SUPABASE_KEY")
db: Client = create_client(efr_url, efr_key)


def Treinopage(page: ft.Page, supabase: any, day: str, user_id: str):
    """
    Página de treino que carrega exercícios do Supabase para o dia informado,
    com cache local e timer de treino.
    """

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

    # Carrega dados
    rest_duration = load_rest_duration(user_id)
    exercises = load_exercises(day, user_id)

    # Elementos do timer
    training_started = False
    training_time = 0
    training_running = False
    training_timer_ref = ft.Ref[ft.Text]()

    async def run_training_timer():
        nonlocal training_time, training_running
        while training_running:
            training_time += 1
            m, s = divmod(training_time, 60)
            training_timer_ref.current.value = f"Tempo: {m:02d}:{s:02d}"
            training_timer_ref.current.update()
            await asyncio.sleep(1)
            print(f"DEBUG - treino: Tempo de treino atualizado: {m:02d}:{s:02d}")

    # Controles de treino (iniciar, pausar, retomar, finalizar)
    def start_training(e):
        nonlocal training_started, training_running
        training_started = True
        training_running = True
        for tile in exercise_list.controls:
            tile.enable_controls()
        start_btn.visible = False
        pause_btn.visible = True
        finish_btn.visible = True
        page.run_task(run_training_timer)
        print(f"INFO - treino: Treino iniciado para o dia {day} e user_id {user_id}")
        page.update()

    def pause_training(e):
        nonlocal training_running
        training_running = False
        pause_btn.visible = False
        resume_btn.visible = True
        print(f"INFO - treino: Treino pausado para o dia {day} e user_id {user_id}")
        page.update()

    def resume_training(e):
        nonlocal training_running
        training_running = True
        page.run_task(run_training_timer)
        pause_btn.visible = True
        resume_btn.visible = False
        print(f"INFO - treino: Treino retomado para o dia {day} e user_id {user_id}")
        page.update()

    def stop_training(e):
        nonlocal training_running

        def confirm(ev):
            nonlocal training_running
            if ev.control.text == "Sim":
                training_running = False
                print(
                    f"INFO - treino: Treino finalizado para o dia {day} e user_id {user_id}"
                )
                page.go("/home")
            page.close(dlg)
            page.update()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Finalizar Treino"),
            content=ft.Text("Deseja realmente finalizar o treino?"),
            actions=[
                ft.TextButton("Sim", on_click=confirm),
                ft.TextButton("Não", on_click=confirm),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.open(dlg)
        print(f"DEBUG - treino: Diálogo de finalização de treino aberto")

    def favorite_ex(tile):
        msg = (
            "Exercício favoritado!" if tile.is_favorited else "Exercício desfavoritado!"
        )
        page.open(
            ft.SnackBar(
                content=ft.Text(msg),
                bgcolor=ft.Colors.GREEN_700 if tile.is_favorited else ft.Colors.RED_700,
            )
        )
        page.update()
        print(
            f"INFO - treino: Exercício {tile.exercise_name} {'favoritado' if tile.is_favorited else 'desfavoritado'}"
        )
        page.update()

    exercise_list = ft.ListView(
        expand=True,
        spacing=10,
        padding=10,
        controls=[
            ExerciseTile(
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
                page=page,
                supabase=supabase,
                rest_duration=rest_duration,
            )
            for ex in exercises
        ],
    )

    # Botões de controle
    start_btn = ft.ElevatedButton("Iniciar Treino", on_click=start_training)
    pause_btn = ft.IconButton(ft.Icons.PAUSE, on_click=pause_training, visible=False)
    resume_btn = ft.IconButton(
        ft.Icons.PLAY_ARROW, on_click=resume_training, visible=False
    )
    finish_btn = ft.ElevatedButton(
        "Finalizar Treino", on_click=stop_training, visible=False
    )

    # Barra de controle
    control_bar = ft.Container(
        content=ft.ResponsiveRow(
            [
                ft.Text(ref=training_timer_ref, value="Tempo: 00:00", size=16),
                ft.Row(
                    [pause_btn, resume_btn, finish_btn],
                    spacing=5,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            spacing=10,
        ),
        padding=10,
        border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.GREY_300)),
    )

    # Composição final da página
    return ft.Column(
        [
            control_bar,
            ft.Container(
                start_btn,
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
