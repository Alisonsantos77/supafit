import flet as ft
from services.supabase import SupabaseService
from datetime import datetime, timedelta
from collections import defaultdict
import calendar


def HistoryPage(page: ft.Page, supabase):
    """
    Página de histórico que mostra estatísticas de treinos realizados,
    progresso de cargas e frequência de treinos com dados reais do Supabase.
    """
    supabase_service = SupabaseService.get_instance(page)
    user_id = page.client_storage.get("supafit.user_id")

    if not user_id:
        page.go("/login")
        return ft.Container()

    # Estados para filtros e loading
    selected_period = ft.Ref[ft.Dropdown]()
    stats_container = ft.Ref[ft.Container]()
    loading_indicator = ft.Ref[ft.ProgressRing]()

    def show_loading(show: bool = True):
        """Mostra/esconde indicador de carregamento."""
        if loading_indicator.current:
            loading_indicator.current.visible = show
            page.update()

    def load_real_data(period_days=30):
        """Carrega dados reais do Supabase."""
        try:
            show_loading(True)

            # Data limite baseada no período
            end_date = datetime.now()
            start_date = end_date - timedelta(days=period_days)

            # 1. Carrega planos do usuário com exercícios
            plans_response = (
                supabase_service.client.table("user_plans")
                .select("*, plan_exercises(*, exercicios(nome, grupo_muscular))")
                .eq("user_id", user_id)
                .execute()
            )

            # 2. Carrega histórico de progresso
            progress_response = (
                supabase_service.client.table("progress")
                .select("*, exercicios(nome, grupo_muscular)")
                .eq("user_id", user_id)
                .gte("recorded_at", start_date.isoformat())
                .order("recorded_at", desc=False)
                .execute()
            )

            show_loading(False)
            return {
                "plans": plans_response.data or [],
                "progress": progress_response.data or [],
            }

        except Exception as e:
            show_loading(False)
            print(f"ERROR - history: Erro ao carregar dados reais: {str(e)}")
            return {"plans": [], "progress": []}

    def calculate_statistics(data, period_days=30):
        """Calcula estatísticas detalhadas baseadas nos dados reais."""
        plans = data.get("plans", [])
        progress = data.get("progress", [])

        stats = {
            "total_plans": len(plans),
            "total_exercises": 0,
            "total_progress_records": len(progress),
            "plans_by_day": defaultdict(list),
            "exercises_by_muscle": defaultdict(set),
            "progress_by_exercise": defaultdict(list),
            "recent_activities": [],
            "avg_exercises_per_plan": 0,
            "muscle_group_frequency": defaultdict(int),
            "load_progression": {},
            "workout_frequency": defaultdict(int),
        }

        # Processa planos
        for plan in plans:
            day = plan.get("day", "").lower()
            title = plan.get("title", "")
            exercises = plan.get("plan_exercises", [])

            stats["total_exercises"] += len(exercises)
            stats["plans_by_day"][day].append(
                {
                    "title": title,
                    "exercises": len(exercises),
                    "created_at": plan.get("created_at", ""),
                    "plan_id": plan.get("plan_id", ""),
                }
            )

            # Agrupa exercícios por músculo
            for exercise in exercises:
                if exercise.get("exercicios"):
                    muscle_group = exercise["exercicios"].get(
                        "grupo_muscular", "Outros"
                    )
                    exercise_name = exercise["exercicios"].get("nome", "")
                    stats["exercises_by_muscle"][muscle_group].add(exercise_name)

        # Converte sets para contagem
        for muscle, exercises_set in stats["exercises_by_muscle"].items():
            stats["exercises_by_muscle"][muscle] = len(exercises_set)

        # Processa progresso
        for record in progress:
            exercise_id = record.get("exercise_id", "")
            load = record.get("load", 0)
            recorded_at = record.get("recorded_at", "")
            exercise_info = record.get("exercicios", {})
            exercise_name = exercise_info.get("nome", "Exercício")
            muscle_group = exercise_info.get("grupo_muscular", "Outros")

            # Histórico por exercício
            stats["progress_by_exercise"][exercise_name].append(
                {"load": load, "date": recorded_at, "exercise_id": exercise_id}
            )

            # Frequência por grupo muscular
            stats["muscle_group_frequency"][muscle_group] += 1

            # Atividades recentes (últimas 10)
            stats["recent_activities"].append(
                {
                    "exercise_name": exercise_name,
                    "load": load,
                    "date": recorded_at,
                    "muscle_group": muscle_group,
                }
            )

        stats["recent_activities"].sort(key=lambda x: x.get("date", ""), reverse=True)
        stats["recent_activities"] = stats["recent_activities"][:10]

        # Calcula progressão de carga para exercícios principais
        for exercise_name, records in stats["progress_by_exercise"].items():
            if len(records) >= 2:
                sorted_records = sorted(records, key=lambda x: x.get("date", ""))
                first_load = sorted_records[0]["load"]
                last_load = sorted_records[-1]["load"]

                if first_load > 0:
                    progression = ((last_load - first_load) / first_load) * 100
                    stats["load_progression"][exercise_name] = {
                        "progression_percent": round(progression, 1),
                        "first_load": first_load,
                        "last_load": last_load,
                        "records_count": len(records),
                    }

        # Frequência de treino por dia da semana
        days_map = {
            "segunda": "Segunda",
            "terça": "Terça",
            "quarta": "Quarta",
            "quinta": "Quinta",
            "sexta": "Sexta",
            "sábado": "Sábado",
            "domingo": "Domingo",
        }

        for day_key in stats["plans_by_day"]:
            day_name = days_map.get(day_key, day_key.title())
            stats["workout_frequency"][day_name] = len(stats["plans_by_day"][day_key])

        # Média de exercícios por plano
        if stats["total_plans"] > 0:
            stats["avg_exercises_per_plan"] = round(
                stats["total_exercises"] / stats["total_plans"], 1
            )

        return stats

    def create_enhanced_stats_cards(stats):
        """Cria cards aprimorados com estatísticas reais."""
        cards = []

        # Card de estatísticas gerais
        general_stats = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Icon(ft.Icons.ANALYTICS, color=ft.Colors.PRIMARY),
                                ft.Text(
                                    "Estatísticas Gerais",
                                    size=18,
                                    weight=ft.FontWeight.BOLD,
                                ),
                            ]
                        ),
                        ft.Divider(),
                        ft.ResponsiveRow(
                            [
                                ft.Container(
                                    content=ft.Column(
                                        [
                                            ft.Text(
                                                str(stats["total_plans"]),
                                                size=24,
                                                weight=ft.FontWeight.BOLD,
                                                color=ft.Colors.PRIMARY,
                                            ),
                                            ft.Text(
                                                "Planos Criados",
                                                size=12,
                                                color=ft.Colors.GREY_700,
                                            ),
                                        ],
                                        alignment=ft.MainAxisAlignment.CENTER,
                                    ),
                                    col={"sm": 12, "md": 3},
                                ),
                                ft.Container(
                                    content=ft.Column(
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
                                    col={"sm": 12, "md": 3},
                                ),
                                ft.Container(
                                    content=ft.Column(
                                        [
                                            ft.Text(
                                                str(stats["total_progress_records"]),
                                                size=24,
                                                weight=ft.FontWeight.BOLD,
                                                color=ft.Colors.ORANGE,
                                            ),
                                            ft.Text(
                                                "Registros de Progresso",
                                                size=12,
                                                color=ft.Colors.GREY_700,
                                            ),
                                        ],
                                        alignment=ft.MainAxisAlignment.CENTER,
                                    ),
                                    col={"sm": 12, "md": 3},
                                ),
                                ft.Container(
                                    content=ft.Column(
                                        [
                                            ft.Text(
                                                str(stats["avg_exercises_per_plan"]),
                                                size=24,
                                                weight=ft.FontWeight.BOLD,
                                                color=ft.Colors.PURPLE,
                                            ),
                                            ft.Text(
                                                "Média por Plano",
                                                size=12,
                                                color=ft.Colors.GREY_700,
                                            ),
                                        ],
                                        alignment=ft.MainAxisAlignment.CENTER,
                                    ),
                                    col={"sm": 12, "md": 3},
                                ),
                            ]
                        ),
                    ],
                    spacing=10,
                ),
                padding=20,
            )
        )
        cards.append(general_stats)

        # Card de grupos musculares
        if stats["exercises_by_muscle"]:
            muscle_stats = ft.Card(
                content=ft.Container(
                    content=ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Icon(
                                        ft.Icons.FITNESS_CENTER, color=ft.Colors.RED
                                    ),
                                    ft.Text(
                                        "Exercícios por Grupo Muscular",
                                        size=18,
                                        weight=ft.FontWeight.BOLD,
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                    ),
                                ]
                            ),
                            ft.Divider(),
                            ft.Column(
                                [
                                    ft.Container(
                                        content=ft.Row(
                                            [
                                                ft.Text(muscle, size=14, expand=True),
                                                ft.Container(
                                                    content=ft.Text(
                                                        str(count),
                                                        size=12,
                                                        weight=ft.FontWeight.BOLD,
                                                        color=ft.Colors.WHITE,
                                                    ),
                                                    bgcolor=ft.Colors.PRIMARY,
                                                    padding=ft.padding.symmetric(
                                                        horizontal=8, vertical=4
                                                    ),
                                                    border_radius=12,
                                                ),
                                            ],
                                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                        ),
                                        padding=ft.padding.symmetric(vertical=4),
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

        # Card de progressão de carga
        if stats["load_progression"]:
            progression_stats = ft.Card(
                content=ft.Container(
                    content=ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Icon(
                                        ft.Icons.TRENDING_UP, color=ft.Colors.GREEN
                                    ),
                                    ft.Text(
                                        "Progressão de Carga",
                                        size=18,
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                ]
                            ),
                            ft.Divider(),
                            ft.Column(
                                [
                                    ft.Container(
                                        content=ft.Column(
                                            [
                                                ft.Row(
                                                    [
                                                        ft.Text(
                                                            (
                                                                exercise_name[:25]
                                                                + "..."
                                                                if len(exercise_name)
                                                                > 25
                                                                else exercise_name
                                                            ),
                                                            size=14,
                                                            weight=ft.FontWeight.BOLD,
                                                            expand=True,
                                                        ),
                                                        ft.Container(
                                                            content=ft.Text(
                                                                f"{data['progression_percent']:+.1f}%",
                                                                size=12,
                                                                weight=ft.FontWeight.BOLD,
                                                                color=ft.Colors.WHITE,
                                                            ),
                                                            bgcolor=(
                                                                ft.Colors.GREEN
                                                                if data[
                                                                    "progression_percent"
                                                                ]
                                                                >= 0
                                                                else ft.Colors.RED
                                                            ),
                                                            padding=ft.padding.symmetric(
                                                                horizontal=8, vertical=4
                                                            ),
                                                            border_radius=12,
                                                        ),
                                                    ]
                                                ),
                                                ft.Text(
                                                    f"{data['first_load']}kg → {data['last_load']}kg ({data['records_count']} registros)",
                                                    size=12,
                                                    color=ft.Colors.GREY_700,
                                                ),
                                            ],
                                            spacing=4,
                                        ),
                                        padding=ft.padding.symmetric(vertical=8),
                                    )
                                    for exercise_name, data in list(
                                        stats["load_progression"].items()
                                    )[:5]
                                ],
                                spacing=4,
                            ),
                        ],
                        spacing=10,
                    ),
                    padding=20,
                )
            )
            cards.append(progression_stats)

        # Card de atividades recentes
        if stats["recent_activities"]:
            recent_stats = ft.Card(
                content=ft.Container(
                    content=ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Icon(ft.Icons.HISTORY, color=ft.Colors.PURPLE),
                                    ft.Text(
                                        "Atividades Recentes",
                                        size=18,
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                ]
                            ),
                            ft.Divider(),
                            ft.Column(
                                [
                                    ft.ListTile(
                                        leading=ft.Container(
                                            content=ft.Text(
                                                f"{activity['load']}kg",
                                                size=12,
                                                weight=ft.FontWeight.BOLD,
                                                color=ft.Colors.WHITE,
                                            ),
                                            bgcolor=ft.Colors.PRIMARY,
                                            padding=ft.padding.all(8),
                                            border_radius=8,
                                            width=50,
                                            alignment=ft.alignment.center,
                                        ),
                                        title=ft.Text(
                                            (
                                                activity["exercise_name"][:30] + "..."
                                                if len(activity["exercise_name"]) > 30
                                                else activity["exercise_name"]
                                            ),
                                            size=14,
                                            weight=ft.FontWeight.BOLD,
                                        ),
                                        subtitle=ft.Text(
                                            f"{activity['muscle_group']} • {format_date(activity['date'])}",
                                            size=12,
                                            color=ft.Colors.GREY_600,
                                        ),
                                    )
                                    for activity in stats["recent_activities"][:5]
                                ],
                                spacing=4,
                            ),
                        ],
                        spacing=10,
                    ),
                    padding=20,
                )
            )
            cards.append(recent_stats)

        return cards

    def create_weekly_plan_view(stats):
        """Cria visualização semanal dos planos com dados reais."""
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
                            ft.Row(
                                [
                                    ft.Icon(ft.Icons.CALENDAR_TODAY, size=16),
                                    ft.Text(
                                        days_display[i],
                                        size=16,
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                ]
                            ),
                            ft.Divider(),
                            (
                                ft.Column(
                                    [
                                        ft.Container(
                                            content=ft.Column(
                                                [
                                                    ft.Row(
                                                        [
                                                            ft.Text(
                                                                plan["title"],
                                                                size=14,
                                                                weight=ft.FontWeight.BOLD,
                                                                expand=True,
                                                            ),
                                                            ft.Container(
                                                                content=ft.Text(
                                                                    str(
                                                                        plan[
                                                                            "exercises"
                                                                        ]
                                                                    ),
                                                                    size=10,
                                                                    color=ft.Colors.WHITE,
                                                                ),
                                                                bgcolor=ft.Colors.PRIMARY,
                                                                padding=ft.padding.all(
                                                                    4
                                                                ),
                                                                border_radius=8,
                                                                width=24,
                                                                height=24,
                                                                alignment=ft.alignment.center,
                                                            ),
                                                        ]
                                                    ),
                                                    ft.Text(
                                                        f"Criado em {format_date(plan['created_at'])}",
                                                        size=11,
                                                        color=ft.Colors.GREY_600,
                                                    ),
                                                ],
                                                spacing=4,
                                            ),
                                            padding=10,
                                            border_radius=8,
                                        )
                                        for plan in day_plans
                                    ],
                                    spacing=8,
                                )
                                if day_plans
                                else ft.Container(
                                    content=ft.Column(
                                        [
                                            ft.Icon(
                                                ft.Icons.INBOX,
                                                size=32,
                                                color=ft.Colors.GREY_400,
                                            ),
                                            ft.Text(
                                                "Nenhum plano",
                                                size=12,
                                                color=ft.Colors.GREY_500,
                                            ),
                                        ],
                                        alignment=ft.MainAxisAlignment.CENTER,
                                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
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

    def format_date(date_str):
        """Formata data para exibição."""
        try:
            if not date_str:
                return "Data não disponível"
            # Remove informações de timezone se presente
            date_clean = date_str.split("+")[0].split("T")[0]
            date_obj = datetime.strptime(date_clean, "%Y-%m-%d")
            return date_obj.strftime("%d/%m/%Y")
        except:
            return "Data inválida"

    def on_period_change(e):
        """Atualiza estatísticas quando o período é alterado."""
        period_map = {"7 dias": 7, "30 dias": 30, "90 dias": 90, "Todo período": 365}
        selected_days = period_map.get(e.control.value, 30)

        data = load_real_data(selected_days)
        stats = calculate_statistics(data, selected_days)

        # Atualiza o container de estatísticas
        stats_cards = create_enhanced_stats_cards(stats)
        weekly_cards = create_weekly_plan_view(stats)

        stats_container.current.content = ft.Column(
            [
                ft.Text(
                    "📈 Estatísticas do Período", size=20, weight=ft.FontWeight.BOLD
                ),
                ft.Column(stats_cards, spacing=10),
                ft.Text(
                    "📋 Planos por Dia da Semana", size=20, weight=ft.FontWeight.BOLD
                ),
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

    initial_data = load_real_data(30)
    initial_stats = calculate_statistics(initial_data, 30)

    period_selector = ft.Container(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.DATE_RANGE, color=ft.Colors.PRIMARY),
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
                ft.ProgressRing(
                    ref=loading_indicator, visible=False, width=20, height=20
                ),
            ],
            spacing=10,
        ),
        padding=10,
    )

    # Container principal de estatísticas
    stats_cards = create_enhanced_stats_cards(initial_stats)
    weekly_cards = create_weekly_plan_view(initial_stats)

    main_content = ft.Container(
        ref=stats_container,
        content=ft.Column(
            [
                ft.Text(
                    "📈 Estatísticas do Período", size=20, weight=ft.FontWeight.BOLD
                ),
                ft.Column(stats_cards, spacing=10),
                ft.Text(
                    "📋 Planos por Dia da Semana", size=20, weight=ft.FontWeight.BOLD
                ),
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
            [period_selector,
             ft.Divider(),
             main_content,
             ],
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
        ),
        padding=10,
        expand=True,
    )
