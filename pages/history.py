import flet as ft
from services.supabase import SupabaseService
from datetime import datetime, timedelta
from collections import defaultdict
import calendar


def HistoryPage(page: ft.Page, supabase):
    """
    Página de histórico que mostra estatísticas de treinos realizados,
    progresso de cargas e frequência de treinos.
    """
    supabase_service = SupabaseService.get_instance(page)
    user_id = page.client_storage.get("supafit.user_id")

    if not user_id:
        page.go("/login")
        return ft.Container()

    # Estados para filtros
    selected_period = ft.Ref[ft.Dropdown]()
    stats_container = ft.Ref[ft.Container]()

    def load_workout_stats(period_days=30):
        """Carrega estatísticas de treinos baseado no período selecionado."""
        try:
            # Carrega planos do usuário
            response = (
                supabase_service.client.table("user_plans")
                .select(
                    "plan_id, day, title, created_at, plan_exercises(exercise_id, sets, reps, exercicios(nome))"
                )
                .eq("user_id", user_id)
                .execute()
            )

            plans_data = response.data or []

            # Simula dados de treinos realizados (você pode implementar uma tabela de workout_sessions)
            # Por enquanto, vamos mostrar os planos disponíveis e suas estatísticas

            stats = {
                "total_plans": len(plans_data),
                "total_exercises": 0,
                "plans_by_day": defaultdict(list),
                "exercises_by_muscle": defaultdict(int),
                "avg_exercises_per_plan": 0,
            }

            for plan in plans_data:
                day = plan.get("day", "").lower()
                title = plan.get("title", "")
                exercises = plan.get("plan_exercises", [])

                stats["total_exercises"] += len(exercises)
                stats["plans_by_day"][day].append(
                    {
                        "title": title,
                        "exercises": len(exercises),
                        "created_at": plan.get("created_at", ""),
                    }
                )

                # Contabiliza exercícios por grupo muscular (baseado no título)
                muscle_group = classify_muscle_group(title)
                stats["exercises_by_muscle"][muscle_group] += len(exercises)

            if stats["total_plans"] > 0:
                stats["avg_exercises_per_plan"] = round(
                    stats["total_exercises"] / stats["total_plans"], 1
                )

            return stats

        except Exception as e:
            print(f"ERROR - history: Erro ao carregar estatísticas: {str(e)}")
            return {
                "total_plans": 0,
                "total_exercises": 0,
                "plans_by_day": {},
                "exercises_by_muscle": {},
                "avg_exercises_per_plan": 0,
            }

    def classify_muscle_group(workout_title):
        """Classifica o grupo muscular baseado no título do treino."""
        title_lower = workout_title.lower()

        if any(
            word in title_lower for word in ["peito", "peitoral", "tríceps", "triceps"]
        ):
            return "Peito e Tríceps"
        elif any(
            word in title_lower for word in ["costas", "dorsal", "bíceps", "biceps"]
        ):
            return "Costas e Bíceps"
        elif any(
            word in title_lower
            for word in ["pernas", "perna", "quadríceps", "glúteos", "panturrilha"]
        ):
            return "Pernas"
        elif any(word in title_lower for word in ["ombros", "ombro", "deltoides"]):
            return "Ombros"
        elif any(word in title_lower for word in ["braço", "braços", "antebraço"]):
            return "Braços"
        elif any(word in title_lower for word in ["core", "abdomen", "abdominal"]):
            return "Core"
        elif any(word in title_lower for word in ["cardio", "aeróbico", "corrida"]):
            return "Cardio"
        elif any(word in title_lower for word in ["full", "corpo", "todo"]):
            return "Full Body"
        else:
            return "Outros"

    def create_stats_cards(stats):
        """Cria cards com estatísticas dos treinos."""
        cards = []

        # Card de estatísticas gerais
        general_stats = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text(
                            "📊 Estatísticas Gerais", size=18, weight=ft.FontWeight.BOLD
                        ),
                        ft.Divider(),
                        ft.Row(
                            [
                                ft.Column(
                                    [
                                        ft.Text(
                                            str(stats["total_plans"]),
                                            size=24,
                                            weight=ft.FontWeight.BOLD,
                                            color=ft.Colors.BLUE,
                                        ),
                                        ft.Text(
                                            "Planos Criados",
                                            size=12,
                                            color=ft.Colors.GREY_700,
                                        ),
                                    ],
                                    alignment=ft.MainAxisAlignment.CENTER,
                                ),
                                ft.Column(
                                    [
                                        ft.Text(
                                            str(stats["total_exercises"]),
                                            size=24,
                                            weight=ft.FontWeight.BOLD,
                                            color=ft.Colors.GREEN,
                                        ),
                                        ft.Text(
                                            "Total Exercícios",
                                            size=12,
                                            color=ft.Colors.GREY_700,
                                        ),
                                    ],
                                    alignment=ft.MainAxisAlignment.CENTER,
                                ),
                                ft.Column(
                                    [
                                        ft.Text(
                                            str(stats["avg_exercises_per_plan"]),
                                            size=24,
                                            weight=ft.FontWeight.BOLD,
                                            color=ft.Colors.ORANGE,
                                        ),
                                        ft.Text(
                                            "Média por Plano",
                                            size=12,
                                            color=ft.Colors.GREY_700,
                                        ),
                                    ],
                                    alignment=ft.MainAxisAlignment.CENTER,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_AROUND,
                        ),
                    ],
                    spacing=10,
                ),
                padding=20,
            )
        )
        cards.append(general_stats)

        # Card de distribuição por dia da semana
        days_order = [
            "segunda",
            "terça",
            "quarta",
            "quinta",
            "sexta",
            "sábado",
            "domingo",
        ]
        days_display = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]

        day_stats = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text(
                            "📅 Distribuição por Dia",
                            size=18,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Divider(),
                        ft.Row(
                            [
                                ft.Column(
                                    [
                                        ft.Text(
                                            days_display[i],
                                            size=12,
                                            weight=ft.FontWeight.BOLD,
                                        ),
                                        ft.Text(
                                            str(
                                                len(stats["plans_by_day"].get(day, []))
                                            ),
                                            size=16,
                                            color=(
                                                ft.Colors.BLUE
                                                if stats["plans_by_day"].get(day)
                                                else ft.Colors.GREY_400
                                            ),
                                        ),
                                    ],
                                    alignment=ft.MainAxisAlignment.CENTER,
                                )
                                for i, day in enumerate(days_order)
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_AROUND,
                        ),
                    ],
                    spacing=10,
                ),
                padding=20,
            )
        )
        cards.append(day_stats)

        # Card de grupos musculares
        if stats["exercises_by_muscle"]:
            muscle_stats = ft.Card(
                content=ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                "💪 Grupos Musculares",
                                size=18,
                                weight=ft.FontWeight.BOLD,
                            ),
                            ft.Divider(),
                            ft.Column(
                                [
                                    ft.Row(
                                        [
                                            ft.Text(muscle, size=14, expand=True),
                                            ft.Text(
                                                str(count),
                                                size=14,
                                                weight=ft.FontWeight.BOLD,
                                                color=ft.Colors.GREEN,
                                            ),
                                        ],
                                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    )
                                    for muscle, count in sorted(
                                        stats["exercises_by_muscle"].items(),
                                        key=lambda x: x[1],
                                        reverse=True,
                                    )
                                ],
                                spacing=8,
                            ),
                        ],
                        spacing=10,
                    ),
                    padding=20,
                )
            )
            cards.append(muscle_stats)

        return cards

    def create_weekly_plan_view(stats):
        """Cria visualização semanal dos planos."""
        days_order = [
            "segunda",
            "terça",
            "quarta",
            "quinta",
            "sexta",
            "sábado",
            "domingo",
        ]
        days_display = [
            "Segunda",
            "Terça",
            "Quarta",
            "Quinta",
            "Sexta",
            "Sábado",
            "Domingo",
        ]

        weekly_cards = []

        for i, day in enumerate(days_order):
            day_plans = stats["plans_by_day"].get(day, [])

            day_card = ft.Card(
                content=ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                days_display[i], size=16, weight=ft.FontWeight.BOLD
                            ),
                            ft.Divider(),
                            (
                                ft.Column(
                                    [
                                        ft.Container(
                                            content=ft.Column(
                                                [
                                                    ft.Text(
                                                        plan["title"],
                                                        size=14,
                                                        weight=ft.FontWeight.BOLD,
                                                    ),
                                                    ft.Text(
                                                        f"{plan['exercises']} exercícios",
                                                        size=12,
                                                        color=ft.Colors.GREY_700,
                                                    ),
                                                ],
                                                spacing=4,
                                            ),
                                            padding=10,
                                            bgcolor=ft.Colors.BLUE_50,
                                            border_radius=8,
                                        )
                                        for plan in day_plans
                                    ],
                                    spacing=8,
                                )
                                if day_plans
                                else ft.Container(
                                    content=ft.Text(
                                        "Nenhum plano",
                                        size=12,
                                        color=ft.Colors.GREY_500,
                                    ),
                                    alignment=ft.alignment.center,
                                    padding=20,
                                )
                            ),
                        ],
                        spacing=10,
                    ),
                    padding=15,
                )
            )
            weekly_cards.append(day_card)

        return weekly_cards

    def on_period_change(e):
        """Atualiza estatísticas quando o período é alterado."""
        period_map = {"7 dias": 7, "30 dias": 30, "90 dias": 90, "Todo período": 365}

        selected_days = period_map.get(e.control.value, 30)
        stats = load_workout_stats(selected_days)

        # Atualiza o container de estatísticas
        stats_cards = create_stats_cards(stats)
        weekly_cards = create_weekly_plan_view(stats)

        stats_container.current.content = ft.Column(
            [
                ft.Text("📈 Estatísticas", size=20, weight=ft.FontWeight.BOLD),
                ft.Column(stats_cards, spacing=10),
                ft.Text("📋 Planos Semanais", size=20, weight=ft.FontWeight.BOLD),
                ft.ResponsiveRow(
                    [
                        ft.Container(card, col={"sm": 12, "md": 6, "lg": 4})
                        for card in weekly_cards
                    ],
                    spacing=10,
                ),
            ],
            spacing=20,
        )

        page.update()

    def go_back(e):
        """Volta para a página inicial."""
        page.go("/home")

    def view_today_workout(e):
        """Vai para o treino de hoje."""
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
        page.go(f"/treino/{current_day}")

    # Carrega estatísticas iniciais
    initial_stats = load_workout_stats(30)

    # Cria componentes da interface
    header = ft.Container(
        content=ft.Row(
            [
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK, on_click=go_back, tooltip="Voltar"
                ),
                ft.Text(
                    "Histórico de Treinos",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    expand=True,
                ),
                ft.IconButton(
                    icon=ft.Icons.FITNESS_CENTER,
                    on_click=view_today_workout,
                    tooltip="Treino de hoje",
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        padding=ft.padding.symmetric(horizontal=10, vertical=5),
    )

    period_selector = ft.Container(
        content=ft.Row(
            [
                ft.Text("Período:", size=16, weight=ft.FontWeight.BOLD),
                ft.Dropdown(
                    ref=selected_period,
                    value="30 dias",
                    options=[
                        ft.dropdown.Option("7 dias"),
                        ft.dropdown.Option("30 dias"),
                        ft.dropdown.Option("90 dias"),
                        ft.dropdown.Option("Todo período"),
                    ],
                    on_change=on_period_change,
                    width=150,
                ),
            ],
            spacing=10,
        ),
        padding=10,
    )

    # Container principal de estatísticas
    stats_cards = create_stats_cards(initial_stats)
    weekly_cards = create_weekly_plan_view(initial_stats)

    main_content = ft.Container(
        ref=stats_container,
        content=ft.Column(
            [
                ft.Text("📈 Estatísticas", size=20, weight=ft.FontWeight.BOLD),
                ft.Column(stats_cards, spacing=10),
                ft.Text("📋 Planos Semanais", size=20, weight=ft.FontWeight.BOLD),
                ft.ResponsiveRow(
                    [
                        ft.Container(card, col={"sm": 12, "md": 6, "lg": 4})
                        for card in weekly_cards
                    ],
                    spacing=10,
                ),
            ],
            spacing=20,
        ),
        padding=10,
    )

    return ft.Container(
        content=ft.Column(
            [header, period_selector, ft.Divider(), main_content],
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
        ),
        padding=10,
        expand=True,
    )
