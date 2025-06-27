import flet as ft
from components.components import WorkoutTile
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def Homepage(page: ft.Page, supabase):
    user_id = page.client_storage.get("supafit.user_id")

    def load_workouts():
        try:
            # Dados mock com imagens locais
            workouts = [
                {
                    "day": "segunda",
                    "name": "Peito e Tríceps",
                    "image_url": "mascote_supafit/treino_peito.png",
                },
                {
                    "day": "terça",
                    "name": "Costas e Bíceps",
                    "image_url": "mascote_supafit/treino_costas.png",
                },
                {
                    "day": "quarta",
                    "name": "Pernas",
                    "image_url": "mascote_supafit/treino_perna.png", 
                },
                {
                    "day": "quinta",
                    "name": "Ombros",
                    "image_url": "mascote_supafit/treino_braco.png", 
                },
                {
                    "day": "sexta",
                    "name": "Peito e Tríceps",
                    "image_url": "mascote_supafit/treino_peito.png",
                },
                {
                    "day": "sábado",
                    "name": "Descanso",
                    "image_url": "mascote_supafit/treino_descanso.png", 
                },
                {
                    "day": "domingo",
                    "name": "Descanso",
                    "image_url": "mascote_supafit/treino_descanso.png", 
                },
            ]
            logger.info("Treinos mock carregados com imagens locais.")
            return workouts
        except Exception as e:
            logger.error(f"Erro ao carregar treinos mock: {str(e)}")
            return workouts  # Retorna a mesma lista mock em caso de erro

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
            ft.Container(
                content=WorkoutTile(
                    workout_name=workout["name"],
                    day=workout["day"],
                    image_url=workout["image_url"],
                    is_current_day=workout["day"] == current_day,
                    on_view_click=lambda e, day=workout["day"]: page.go(
                        f"/treino/{day}"
                    ),
                ),
                col=10,
                padding=10,
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
