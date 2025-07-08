import flet as ft
import re
from datetime import date
from .base_step import BaseStep, logger
from services.openai import OpenAIService
from utils.alerts import CustomSnackBar


class StepPersonalData(BaseStep):
    """Etapa: Coleta de username, idade e gênero do usuário."""

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
        self.name_input = ft.TextField(
            label="Username",
            width=320,
            border="underline",
            filled=True,
            text_size=16,
            hint_text="Escolha como você será chamado no SupaFit!",
            on_change=self.validate_username,
        )
        self.date_picker = ft.CupertinoDatePicker(
            date_picker_mode=ft.CupertinoDatePickerMode.DATE,
            on_change=self.handle_date_change,
            maximum_year=date.today().year,
        )
        self.age_display = ft.Text(
            "Idade: Não selecionada",
            size=16,
            weight=ft.FontWeight.W_500,
            color=ft.Colors.GREY_600,
        )
        self.gender_dropdown = ft.Dropdown(
            label="Gênero",
            width=320,
            border="underline",
            filled=True,
            options=[
                ft.dropdown.Option("Masculino"),
                ft.dropdown.Option("Feminino"),
                ft.dropdown.Option("Outro"),
            ],
            value="Masculino",
        )
        super().__init__(page, profile_data, current_step, on_next, on_previous)
        logger.info("StepPersonalData inicializado com sucesso.")

    def validate_username(self, e: ft.ControlEvent):
        name = e.control.value.strip()
        if not name:
            self.name_input.error_text = "Digite seu username."
        elif len(name) < 2 or len(name) > 50:
            self.name_input.error_text = "Username deve ter entre 2 e 50 caracteres."
        elif not re.match(r"^[a-zA-Z0-9._-]{2,50}$", name):
            self.name_input.error_text = (
                "Use letras, números, pontos, hífens ou sublinhados."
            )
        else:
            self.name_input.error_text = None
        self.name_input.update()

    def handle_date_change(self, e: ft.ControlEvent):
        if e.control.value:
            ano = e.control.value.year
            mes = e.control.value.month
            dia = e.control.value.day
            hoje = date.today()
            idade = hoje.year - ano - ((hoje.month, hoje.day) < (mes, dia))
            self.age_display.value = f"Idade: {idade} anos"
            self.age_display.color = ft.Colors.PRIMARY
            self.profile_data["age"] = idade
            self.profile_data["birth_date"] = f"{ano}-{mes:02d}-{dia:02d}"
            self.page.update()
            logger.info(f"Idade calculada: {idade}")

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
                    "Comece sua transformação!",
                    style=ft.TextThemeStyle.HEADLINE_MEDIUM,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.PRIMARY,
                ),
                ft.Text(
                    "Crie seu perfil para treinos personalizados no SupaFit",
                    style=ft.TextThemeStyle.BODY_MEDIUM,
                    color=ft.Colors.GREY_600,
                    text_align=ft.TextAlign.CENTER,
                ),
                self.build_step_progress(),
                ft.Container(
                    content=ft.Image(
                        src="mascote_supafit/step_username.png",
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
                                "Escolha seu username!",
                                weight=ft.FontWeight.W_500,
                                color=ft.Colors.PRIMARY,
                            ),
                            ft.Text(
                                "Será seu nome no SupaFit, em treinos e rankings",
                                size=12,
                                color=ft.Colors.GREY_600,
                            ),
                            self.name_input,
                        ],
                        spacing=5,
                    ),
                    width=320,
                ),
                ft.Container(
                    content=ft.Image(
                        src="mascote_supafit/step_age.png",
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
                                "Quando você nasceu?",
                                weight=ft.FontWeight.W_500,
                                color=ft.Colors.PRIMARY,
                            ),
                            ft.ElevatedButton(
                                "Selecionar Data de Nascimento",
                                icon=ft.Icons.CALENDAR_TODAY,
                                on_click=lambda e: self.page.open(
                                    ft.CupertinoBottomSheet(
                                        self.date_picker,
                                        height=216,
                                        padding=ft.padding.only(top=6),
                                    )
                                ),
                            ),
                            self.age_display,
                        ],
                        spacing=5,
                    ),
                    width=320,
                ),
                ft.Container(
                    content=ft.Image(
                        src="mascote_supafit/step_gender.png",
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
                                "Qual seu gênero?",
                                weight=ft.FontWeight.W_500,
                                color=ft.Colors.PRIMARY,
                            ),
                            self.gender_dropdown,
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
                            visible=self.current_step[0] > 0,
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
        name = self.name_input.value.strip()
        if not name:
            self.name_input.error_text = "Digite seu username."
            self.name_input.update()
            CustomSnackBar("Digite seu username.", ft.Colors.RED_700).show(self.page)
            logger.warning("Username não preenchido.")
            return False
        if len(name) < 2 or len(name) > 50:
            self.name_input.error_text = "Username deve ter entre 2 e 50 caracteres."
            self.name_input.update()
            CustomSnackBar(
                "Username deve ter entre 2 e 50 caracteres.", ft.Colors.RED_700
            ).show(self.page)
            logger.warning(f"Comprimento do username inválido: {name}")
            return False
        if not re.match(r"^[a-zA-Z0-9._-]{2,50}$", name):
            self.name_input.error_text = (
                "Use letras, números, pontos, hífens ou sublinhados."
            )
            self.name_input.update()
            CustomSnackBar(
                "Username deve conter letras, números, pontos, hífens ou sublinhados.",
                ft.Colors.RED_700,
            ).show(self.page)
            logger.warning(f"Caracteres inválidos no username: {name}")
            return False

        try:
            openai_service = OpenAIService()
            if await openai_service.is_sensitive_name(name):
                self.name_input.error_text = "Username contém conteúdo inadequado."
                self.name_input.update()
                CustomSnackBar(
                    "Escolha um username apropriado.", ft.Colors.RED_700
                ).show(self.page)
                logger.warning(f"Username sensível detectado: {name}")
                return False
        except Exception as e:
            logger.warning(f"Erro ao validar username com OpenAI: {e}")

        self.name_input.error_text = None
        self.profile_data["name"] = name

        if (
            "age" not in self.profile_data
            or self.profile_data["age"] < 10
            or self.profile_data["age"] > 100
        ):
            self.age_display.value = "Idade: Selecione uma data de nascimento válida"
            self.age_display.color = ft.Colors.RED
            self.page.update()
            CustomSnackBar(
                "Selecione uma data de nascimento válida.", ft.Colors.RED_700
            ).show(self.page)
            logger.warning("Idade inválida ou não selecionada.")
            return False

        self.profile_data["gender"] = self.gender_dropdown.value

        logger.info(
            f"Dados coletados - Username: {name}, Idade: {self.profile_data['age']}, Gênero: {self.profile_data['gender']}"
        )
        logger.info(
            f"Após validação em StepPersonalData, profile_data: {self.profile_data}"
        )
        return True
