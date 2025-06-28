import flet as ft
from components.components import WorkoutTile
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Mapeamento de título para imagem local
IMAGE_MAP = {
    "peito e tríceps": "mascote_supafit/treino_peito.png",
    "costas e bíceps": "mascote_supafit/treino_costas.png",
    "pernas": "mascote_supafit/treino_perna.png",
    "ombros": "mascote_supafit/treino_ombros.png",
    "descanso": "mascote_supafit/treino_descanso.png",
}

# Ordem fixa dos dias da semana
WEEK_DAYS_ORDER = [
    "segunda",
    "terça",
    "quarta",
    "quinta",
    "sexta",
    "sábado",
    "domingo",
]


def Homepage(page: ft.Page, supabase_service):
    user_id = page.client_storage.get("supafit.user_id")
    if not user_id:
        logger.warning(
            "User ID não encontrado no client_storage. Redirecionando para login."
        )
        page.go("/login")
        return ft.Container()

    def load_workouts():
        try:
            resp = (
                supabase_service.client.table("user_plans")
                .select(
                    "day, title, plan_exercises(order, sets, reps, exercicios(nome))"
                )
                .eq("user_id", user_id)
                .execute()
            )
            data = resp.data or []

            workouts_by_day = {day: None for day in WEEK_DAYS_ORDER}

            for plan in data:
                title = plan.get("title", "")
                exercises = sorted(
                    plan.get("plan_exercises", []), key=lambda x: x.get("order", 0)
                )
                ex_list = [
                    {
                        "name": ex["exercicios"]["nome"],
                        "sets": ex.get("sets"),
                        "reps": ex.get("reps"),
                    }
                    for ex in exercises
                ]
                img = IMAGE_MAP.get(title.lower(), "mascote_supafit/treino_padrao.png")

                workouts_by_day[plan.get("day")] = {
                    "day": plan.get("day"),
                    "name": title,
                    "exercises": ex_list,
                    "image_url": img,
                }

            workouts = [
                workouts_by_day[day] for day in WEEK_DAYS_ORDER if workouts_by_day[day]
            ]
            logger.info(f"{len(workouts)} treinos carregados do Supabase.")
            return workouts

        except Exception as e:
            logger.error(f"Erro ao carregar treinos do Supabase: {e}")
            return []

    workouts = load_workouts()

    # Mapeia dia atual
    today_en = datetime.now().strftime("%A").lower()
    day_map = {
        "monday": "segunda",
        "tuesday": "terça",
        "wednesday": "quarta",
        "thursday": "quinta",
        "friday": "sexta",
        "saturday": "sábado",
        "sunday": "domingo",
    }
    current_day = day_map.get(today_en, "segunda")

    workout_grid = ft.ResponsiveRow(
        controls=[
            ft.Container(
                content=WorkoutTile(
                    workout_name=wk["name"],
                    day=wk["day"],
                    image_url=wk["image_url"],
                    is_current_day=(wk["day"] == current_day),
                    on_view_click=lambda e, day=wk["day"]: page.go(f"/treino/{day}"),
                ),
                col=10,
                padding=10,
            )
            for wk in workouts
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
