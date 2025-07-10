import flet as ft
from components.components import WorkoutTile
from datetime import datetime
import os
from groq import Groq
from dotenv import load_dotenv

# Mapeamento de título para imagem local
IMAGE_MAP = {
    "peito e tríceps": "mascote_supafit/treino_peito.png",
    "costas e bíceps": "mascote_supafit/treino_costas.png",
    "pernas": "mascote_supafit/treino_perna.png",
    "ombros": "mascote_supafit/treino_ombros.png",
    "descanso": "mascote_supafit/treino_descanso.png",
    "alongamento": "mascote_supafit/treino_alongamento.png",
    "braço": "mascote_supafit/treino_braco.png",
    "cardio": "mascote_supafit/treino_cardio.png",
    "core": "mascote_supafit/treino_core.png",
    "full body": "mascote_supafit/treino_full_body.png",
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

load_dotenv()
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def detect_image_key(workout_name: str, exercise_names: list[str]) -> str:
    prompt = (
        f"Analise o treino:\n"
        f"Título: {workout_name}\n"
        f"Exercícios: {', '.join(exercise_names)}\n"
        f"Responda apenas com uma das chaves: {', '.join(IMAGE_MAP.keys())}"
    )
    try:
        response = groq_client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=10,
        )
        key = response.choices[0].message.content.strip().lower()
        return key if key in IMAGE_MAP else "descanso"
    except Exception as e:
        print(f"ERROR — Groq AI: {e}")
        return "descanso"


def Homepage(page: ft.Page, supabase_service):
    user_id = page.client_storage.get("supafit.user_id")
    if not user_id:
        page.go("/login")
        return ft.Container()

    def load_workouts():
        resp = (
            supabase_service.client.table("user_plans")
            .select("day, title, plan_exercises(order, sets, reps, exercicios(nome))")
            .eq("user_id", user_id)
            .order("order", desc=False, foreign_table="plan_exercises")
            .execute()
        )
        data = resp.data or []
        workouts_by_day = {day: None for day in WEEK_DAYS_ORDER}

        for plan in data:
            day_key = plan.get("day", "").strip().lower()
            if day_key not in workouts_by_day:
                continue

            title = plan.get("title", "").strip()
            exercises = sorted(
                plan.get("plan_exercises", []), key=lambda x: x.get("order", 0)
            )
            ex_names = [ex["exercicios"]["nome"] for ex in exercises]

            # aqui usamos IA para escolher a imagem
            img_key = detect_image_key(title, ex_names)
            img = IMAGE_MAP[img_key]

            workouts_by_day[day_key] = {
                "day": day_key,
                "name": title,
                "exercises": [
                    {"name": n, "sets": ex.get("sets"), "reps": ex.get("reps")}
                    for n, ex in zip(ex_names, exercises)
                ],
                "image_url": img,
            }

        return [wk for wk in workouts_by_day.values() if wk]

    workouts = load_workouts()

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
