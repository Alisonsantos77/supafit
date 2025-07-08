import flet as ft
from .base_step import BaseStep, logger


class StepPhysicalData(BaseStep):
    """Etapa: Coleta de peso e altura do usuário."""

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
        self.weight_input = ft.TextField(
            label="Peso (kg)",
            width=320,
            border="underline",
            filled=True,
            text_size=16,
            keyboard_type=ft.KeyboardType.NUMBER,
            hint_text="Ex: 70.5",
            on_change=self.sync_weight_slider,
        )
        self.weight_slider = ft.Slider(
            min=30,
            max=200,
            value=70,
            width=320,
            on_change=self.update_weight_input,
            label="{value} kg",
        )
        self.height_input = ft.TextField(
            label="Altura (cm)",
            width=320,
            border="underline",
            filled=True,
            text_size=16,
            keyboard_type=ft.KeyboardType.NUMBER,
            hint_text="Ex: 175",
            on_change=self.sync_height_slider,
        )
        self.height_slider = ft.Slider(
            min=120,
            max=220,
            value=170,
            width=320,
            on_change=self.update_height_input,
            label="{value} cm",
        )
        super().__init__(page, profile_data, current_step, on_next, on_previous)
        logger.info("StepPhysicalData inicializado com sucesso.")

    def sync_weight_slider(self, e: ft.ControlEvent):
        """Sincroniza o slider com o input do peso"""
        try:
            weight = float(e.control.value or 0)
            if 30 <= weight <= 200:
                self.weight_slider.value = weight
                self.page.update()
        except ValueError:
            pass

    def sync_height_slider(self, e: ft.ControlEvent):
        """Sincroniza o slider com o input da altura"""
        try:
            height = float(e.control.value or 0)
            if 120 <= height <= 220:
                self.height_slider.value = height
                self.page.update()
        except ValueError:
            pass

    def update_weight_input(self, e: ft.ControlEvent):
        self.weight_input.value = f"{e.control.value:.1f}"
        self.page.update()

    def update_height_input(self, e: ft.ControlEvent):
        self.height_input.value = f"{int(e.control.value)}"
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
                        ft.Colors.BLUE_400
                        if is_current
                        else (ft.Colors.GREEN_400 if is_completed else None)
                    ),
                    border=ft.border.all(
                        2,
                        (
                            ft.Colors.BLUE_400
                            if is_current
                            else (
                                ft.Colors.GREEN_400
                                if is_completed
                                else ft.Colors.GREY_400
                            )
                        ),
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
        return ft.Column(
            [
                ft.Text(
                    "Suas medidas corporais",
                    style=ft.TextThemeStyle.HEADLINE_MEDIUM,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.PRIMARY,
                ),
                ft.Text(
                    "Precisamos dessas informações para calcular seu treino ideal",
                    style=ft.TextThemeStyle.BODY_MEDIUM,
                    color=ft.Colors.GREY_600,
                    text_align=ft.TextAlign.CENTER,
                ),
                self.build_step_progress(),
                ft.Container(
                    content=ft.Image(
                        src="mascote_supafit/step_weight.png",
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
                            ft.Text("Qual seu peso atual?", weight=ft.FontWeight.W_500),
                            self.weight_input,
                            ft.Text(
                                "Ou use o controle deslizante:",
                                size=12,
                                color=ft.Colors.GREY_600,
                            ),
                            self.weight_slider,
                        ],
                        spacing=5,
                    ),
                    width=320,
                ),
                ft.Container(height=10),
                ft.Container(
                    content=ft.Image(
                        src="mascote_supafit/step_height.png",
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
                            ft.Text("Qual sua altura?", weight=ft.FontWeight.W_500),
                            self.height_input,
                            ft.Text(
                                "Ou use o controle deslizante:",
                                size=12,
                                color=ft.Colors.GREY_600,
                            ),
                            self.height_slider,
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
        weight_str = self.weight_input.value.strip()
        if not weight_str:
            self.weight_input.error_text = "Por favor, insira seu peso."
            self.weight_input.update()
            self.show_snackbar("Por favor, insira seu peso.")
            logger.warning("Peso não preenchido.")
            return False

        try:
            weight = float(weight_str)
            if weight < 30 or weight > 200:
                self.weight_input.error_text = "Insira um peso válido (30-200 kg)."
                self.weight_input.update()
                self.show_snackbar("Insira um peso válido (30-200 kg).")
                logger.warning(f"Peso inválido: {weight}")
                return False
        except ValueError:
            self.weight_input.error_text = "Insira um número válido."
            self.weight_input.update()
            self.show_snackbar("Insira um número válido para o peso.")
            logger.warning(f"Peso não é um número: {weight_str}")
            return False

        self.weight_input.error_text = None
        self.profile_data["weight"] = weight

        height_str = self.height_input.value.strip()
        if not height_str:
            self.height_input.error_text = "Por favor, insira sua altura."
            self.height_input.update()
            self.show_snackbar("Por favor, insira sua altura.")
            logger.warning("Altura não preenchida.")
            return False

        try:
            height = float(height_str)
            if height < 120 or height > 220:
                self.height_input.error_text = "Insira uma altura válida (120-220 cm)."
                self.height_input.update()
                self.show_snackbar("Insira uma altura válida (120-220 cm).")
                logger.warning(f"Altura inválida: {height}")
                return False
        except ValueError:
            self.height_input.error_text = "Insira um número válido."
            self.height_input.update()
            self.show_snackbar("Insira um número válido para a altura.")
            logger.warning(f"Altura não é um número: {height_str}")
            return False

        self.height_input.error_text = None
        self.profile_data["height"] = int(height)

        logger.info(f"Dados coletados - Peso: {weight} kg, Altura: {height} cm")
        logger.info(
            f"Após validação em StepPhysicalData, profile_data: {self.profile_data}"
        )
        return True
