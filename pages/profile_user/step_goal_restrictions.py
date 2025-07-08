import flet as ft
from .base_step import BaseStep, logger
from services.openai import OpenAIService
from utils.alerts import CustomSnackBar


class StepGoalRestrictions(BaseStep):
    """Etapa: Coleta de objetivo e restrições do usuário."""

    def __init__(
        self,
        page: ft.Page,
        profile_data: dict,
        current_step: list,
        on_next,
        on_previous,
        supabase_service=None,
        on_create=None,
    ):
        self.goal_dropdown = ft.Dropdown(
            label="Objetivo",
            width=320,
            border="underline",
            filled=True,
            hint_text="Escolha seu foco fitness",
            options=[
                ft.dropdown.Option("Perder peso"),
                ft.dropdown.Option("Hipertrofia"),
                ft.dropdown.Option("Manter forma física"),
                ft.dropdown.Option("Melhorar resistência"),
                ft.dropdown.Option("Melhorar mobilidade"),
            ],
            value="Manter forma física",
        )
        self.restrictions_input = ft.TextField(
            label="Restrições ou limitações",
            width=320,
            border="underline",
            filled=True,
            text_size=16,
            multiline=True,
            max_lines=2,
            max_length=50,
            hint_text="Ex: Dor no joelho, lesão no ombro",
            on_change=self.validate_restrictions,
        )
        self.char_count = ft.Text("0/50 caracteres", size=12, color=ft.Colors.GREY_600)
        super().__init__(page, profile_data, current_step, on_next, on_previous)
        logger.info("StepGoalRestrictions inicializado com sucesso.")

    def validate_restrictions(self, e: ft.ControlEvent):
        restrictions = e.control.value.strip()
        if len(restrictions) > 50:
            self.restrictions_input.error_text = "Máximo 50 caracteres."
            self.char_count.color = ft.Colors.RED
        else:
            self.restrictions_input.error_text = None
            self.char_count.color = ft.Colors.GREY_600
        self.update_char_count(e)
        self.page.update()

    def update_char_count(self, e: ft.ControlEvent):
        count = len(e.control.value)
        self.char_count.value = f"{count}/50 caracteres"
        self.page.update()

    def build_step_progress(self) -> ft.Control:
        steps = []
        for i in range(4):
            is_current = self.current_step[0] == i
            is_completed = self.current_step[0] > i
            steps.append(
                ft.Container(
                    width=30,
                    height=30,
                    border_radius=15,
                    bgcolor=(
                        ft.Colors.PRIMARY
                        if is_current or is_completed
                        else ft.Colors.GREY_300
                    ),
                    content=ft.Icon(
                        (
                            ft.Icons.CHECK
                            if is_completed
                            else (
                                ft.Icons.PERSON
                                if i == 0
                                else (
                                    ft.Icons.FITNESS_CENTER
                                    if i == 1
                                    else (
                                        ft.Icons.FITNESS_CENTER_OUTLINED
                                        if i == 2
                                        else ft.Icons.VISIBILITY
                                    )
                                )
                            )
                        ),
                        color=(
                            ft.Colors.WHITE
                            if (is_current or is_completed)
                            else ft.Colors.GREY_600
                        ),
                        size=16,
                    ),
                    alignment=ft.alignment.center,
                    animate_opacity=300,
                    animate_scale=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
                    scale=1.2 if is_current else 1.0,
                )
            )
        return ft.Row(
            steps,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10,
        )

    def build_view(self) -> ft.Control:
        goal_explanations = ft.ListView(
            controls=[
                ft.Text(
                    "• Perder peso: Reduza gordura com treinos intensos e dieta.",
                    size=12,
                    color=ft.Colors.GREY_600,
                ),
                ft.Text(
                    "• Hipertrofia: Ganhe músculos com treinos de força focados.",
                    size=12,
                    color=ft.Colors.GREY_600,
                ),
                ft.Text(
                    "• Manter forma: Equilibre saúde, força e energia diária.",
                    size=12,
                    color=ft.Colors.GREY_600,
                ),
                ft.Text(
                    "• Resistência: Melhore sua energia para treinos longos.",
                    size=12,
                    color=ft.Colors.GREY_600,
                ),
                ft.Text(
                    "• Mobilidade: Ganhe flexibilidade e movimentos funcionais.",
                    size=12,
                    color=ft.Colors.GREY_600,
                ),
            ],
            spacing=5,
            auto_scroll=False,
            height=100,
        )
        return ft.Column(
            [
                ft.Text(
                    "Defina sua jornada fitness!",
                    style=ft.TextThemeStyle.HEADLINE_MEDIUM,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.PRIMARY,
                ),
                ft.Text(
                    "Escolha o objetivo que move você e personalize seu treino",
                    style=ft.TextThemeStyle.BODY_MEDIUM,
                    color=ft.Colors.GREY_600,
                    text_align=ft.TextAlign.CENTER,
                ),
                self.build_step_progress(),
                ft.Container(
                    content=ft.Image(
                        src="mascote_supafit/step_goal.png",
                        width=150,
                        height=150,
                        fit=ft.ImageFit.CONTAIN,
                    ),
                    alignment=ft.alignment.center,
                    padding=20,
                ),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                "Qual seu foco no SupaFit?",
                                weight=ft.FontWeight.W_500,
                                color=ft.Colors.PRIMARY,
                            ),
                            goal_explanations,
                            self.goal_dropdown,
                        ],
                        spacing=5,
                    ),
                    width=320,
                ),
                ft.Container(height=10),
                ft.Container(
                    content=ft.Image(
                        src="mascote_supafit/step_restrict.png",
                        width=150,
                        height=150,
                        fit=ft.ImageFit.CONTAIN,
                    ),
                    alignment=ft.alignment.center,
                    padding=20,
                ),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                "Alguma limitação física?",
                                weight=ft.FontWeight.W_500,
                                color=ft.Colors.PRIMARY,
                            ),
                            ft.Text(
                                "Descreva lesões ou dores (máx. 50 caracteres)",
                                size=12,
                                color=ft.Colors.GREY_600,
                            ),
                            self.restrictions_input,
                            self.char_count,
                        ],
                        spacing=5,
                    ),
                    width=320,
                ),
                ft.Container(height=20),
                ft.Row(
                    [
                        ft.ElevatedButton(
                            "Voltar",
                            on_click=self.on_previous,
                            icon=ft.Icons.ARROW_BACK,
                        ),
                        ft.ElevatedButton(
                            "Próximo",
                            on_click=self.on_next,
                            icon=ft.Icons.ARROW_FORWARD,
                            style=ft.ButtonStyle(
                                bgcolor=ft.Colors.PRIMARY,
                                color=ft.Colors.WHITE,
                            ),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=10,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=15,
        )

    async def validate(self) -> bool:
        if not self.goal_dropdown.value:
            CustomSnackBar("Selecione seu objetivo!", ft.Colors.RED_700).show(self.page)
            logger.warning("Objetivo não selecionado.")
            return False

        self.profile_data["goal"] = self.goal_dropdown.value
        logger.info(f"Objetivo coletado: {self.profile_data['goal']}")

        restrictions = self.restrictions_input.value.strip()
        if len(restrictions) > 50:
            self.restrictions_input.error_text = "Máximo 50 caracteres."
            self.restrictions_input.update()
            CustomSnackBar(
                "Restrições devem ter até 50 caracteres.", ft.Colors.RED_700
            ).show(self.page)
            logger.warning("Restrições excedem o limite de 50 caracteres.")
            return False

        if restrictions:
            try:
                openai_service = OpenAIService()
                if await openai_service.is_sensitive_restrictions(restrictions):
                    self.restrictions_input.error_text = (
                        "Restrições contêm conteúdo inadequado."
                    )
                    self.restrictions_input.update()
                    CustomSnackBar(
                        "Descreva apenas lesões ou dificuldades apropriadas.",
                        ft.Colors.RED_700,
                    ).show(self.page)
                    logger.warning(
                        f"Conteúdo sensível detectado nas restrições: {restrictions}"
                    )
                    return False
            except Exception as e:
                logger.warning(f"Erro ao validar restrições com OpenAI: {e}")

        self.restrictions_input.error_text = None
        self.profile_data["restrictions"] = restrictions if restrictions else "Nenhuma"
        logger.info(f"Restrições coletadas: {self.profile_data['restrictions']}")
        logger.info(f"Após validação em StepGoalRestrictions, profile_data: {self.profile_data}")
        return True