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
    def load_exercises(day: str, user_id: str):
        cache_key = f"exercises_{user_id}_{day}"
        try:
            cached = page.client_storage.get(cache_key)
            if cached:
                print(
                    f"INFO - treino: Carregando exercícios de {day} para user_id {user_id} do cache"
                )
                return cached
        except Exception as e:
            print(f"WARNING - treino: Erro ao verificar cache para {day}: {str(e)}")

        try:
            response = (
            supabase.client.table("user_plans")
            .select(
                "plan_id, plan_exercises(exercise_id, sets, reps, order, exercicios(nome, url_video))"
            )
            .eq("user_id", user_id)
            .eq("day", day.lower())
            .order("order", desc=False, foreign_table="plan_exercises")
            .execute()
        )

            exercises = []
            if response.data and response.data[0].get("plan_exercises"):
                for plan_ex in response.data[0]["plan_exercises"]:
                    exercise = plan_ex.get("exercicios", {})
                    exercises.append(
                        {
                            "name": exercise.get("nome", ""),
                            "series": plan_ex.get("sets", 0),
                            "repetitions": plan_ex.get("reps", ""),
                            "load": 0,
                            "video_url": exercise.get("url_video", None),
                        }
                    )
                print(
                    f"INFO - treino: Carregados {len(exercises)} exercícios para {day} e user_id {user_id}"
                )
            else:
                print(
                    f"WARNING - treino: Nenhum exercício encontrado para {day} e user_id {user_id}"
                )
                return []

            try:
                page.client_storage.set(cache_key, exercises)
                print(
                    f"INFO - treino: Exercícios de {day} salvos no cache: {len(exercises)}"
                )
            except Exception as e:
                print(f"ERROR - treino: Erro ao salvar exercícios no cache: {str(e)}")

            return exercises
        except Exception as e:
            print(f"ERROR - treino: Erro ao carregar exercícios do Supabase: {str(e)}")
            return []

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

    exercises = load_exercises(day, user_id)
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
                on_favorite_click=favorite_ex,
                on_load_save=lambda v: print(
                    f"INFO - treino: Carga salva para {ex['name']}: {v}kg"
                ),
                page=page,
            )
            for ex in exercises
        ],
    )

    start_btn = ft.ElevatedButton(
        "Iniciar Treino", on_click=start_training, ref=ft.Ref()
    )
    pause_btn = ft.IconButton(
        ft.Icons.PAUSE, on_click=pause_training, visible=False, ref=ft.Ref()
    )
    resume_btn = ft.IconButton(
        ft.Icons.PLAY_ARROW, on_click=resume_training, visible=False, ref=ft.Ref()
    )
    finish_btn = ft.ElevatedButton(
        "Finalizar Treino", on_click=stop_training, visible=False, ref=ft.Ref()
    )

    control_bar = ft.Container(
        content=ft.ResponsiveRow(
            [
                ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda e: page.go("/home")),
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
