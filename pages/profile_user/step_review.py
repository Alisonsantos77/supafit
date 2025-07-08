import flet as ft
from .base_step import BaseStep, logger


class StepReview(BaseStep):
    """Etapa: Revisão dos dados do perfil do usuário."""

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
        super().__init__(
            page, profile_data, current_step, on_next, on_previous, on_create
        )
        self.supabase_service = supabase_service
        self.cards_scroll = None
        logger.info("StepReview inicializado com sucesso.")

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

    def create_info_card(
        self, icon_path, title, content, multiline=False, index=0, on_edit=None
    ):
        delay = index * 100
        img = ft.Image(
            src=f"mascote_supafit/{icon_path}",
            width=70,
            height=70,
            border_radius=10,
            animate_scale=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
            scale=1.0,
        )
        text_title = ft.Text(
            title,
            style=ft.TextThemeStyle.TITLE_MEDIUM,
            weight=ft.FontWeight.BOLD,
        )
        text_control = ft.Text(
            str(content),
            style=ft.TextThemeStyle.BODY_MEDIUM,
            max_lines=4 if multiline else 1,
            overflow=ft.TextOverflow.ELLIPSIS,
        )
        edit_button = ft.IconButton(
            icon=ft.Icons.EDIT,
            tooltip=f"Editar {title.lower()}",
            on_click=on_edit,
            visible=bool(on_edit),
        )
        texts = ft.Column([text_title, text_control], expand=True, spacing=5)
        card_content = ft.Row(
            [img, texts, edit_button],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            spacing=10,
        )
        card = ft.Container(
            content=card_content,
            padding=25,
            margin=10,
            border_radius=15,
            border=ft.border.all(1, ft.Colors.PRIMARY),
            animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
            scale=1,
        )

        def on_hover(e):
            if e.data == "true":
                card.scale = 1.03
                card.bgcolor = ft.Colors.PRIMARY
                card.shadow = ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=20,
                    color=ft.Colors.PRIMARY,
                    offset=ft.Offset(0, 4),
                )
                img.scale = 1.1
            else:
                card.scale = 1.0
                card.shadow = ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=10,
                    color=ft.Colors.PRIMARY,
                    offset=ft.Offset(0, 2),
                )
                img.scale = 1.0
            card.update()
            img.update()

        card.on_hover = on_hover
        return card

    def get_current_profile_data(self):
        """Obtém os dados atuais do perfil de forma dinâmica."""
        data = {
            "name": self.profile_data.get("name", "Não informado"),
            "age": self.profile_data.get("age", "Não informado"),
            "weight": self.profile_data.get("weight", "Não informado"),
            "height": self.profile_data.get("height", "Não informado"),
            "gender": self.profile_data.get("gender", "Não informado"),
            "goal": self.profile_data.get("goal", "Não informado"),
            "restrictions": self.profile_data.get("restrictions", "Nenhuma"),
        }
        if any(
            value == "Não informado"
            for key, value in data.items()
            if key != "restrictions"
        ):
            logger.warning("Campos obrigatórios não preenchidos no profile_data")
        logger.info(f"Dados atuais do perfil em get_current_profile_data: {data}")
        return data

    def update_review_data(self):
        """Atualiza dinamicamente os cards com os dados mais recentes."""
        current_data = self.get_current_profile_data()
        if not self.cards_scroll:
            logger.warning("cards_scroll não inicializado em update_review_data")
            return
        if all(
            key in current_data and current_data[key] != "Não informado"
            for key in ["name", "age", "weight", "height", "gender", "goal"]
        ):
            logger.info(f"Atualizando review com dados completos: {current_data}")
        else:
            logger.warning(f"Dados incompletos para review: {current_data}")

        self.cards_scroll.controls = [
            ft.Column(col={"xs": 12, "sm": 6, "md": 4, "lg": 3}, controls=[card])
            for card in [
                self.create_info_card(
                    "step_username.png",
                    "Username",
                    current_data["name"],
                    index=0,
                    on_edit=lambda e: self.on_previous(e, step=0),
                ),
                self.create_info_card(
                    "step_age.png",
                    "Idade",
                    (
                        f"{current_data['age']} anos"
                        if current_data["age"] != "Não informado"
                        else current_data["age"]
                    ),
                    index=1,
                    on_edit=lambda e: self.on_previous(e, step=0),
                ),
                self.create_info_card(
                    "step_weight.png",
                    "Peso",
                    (
                        f"{current_data['weight']} kg"
                        if current_data["weight"] != "Não informado"
                        else current_data["weight"]
                    ),
                    index=2,
                    on_edit=lambda e: self.on_previous(e, step=1),
                ),
                self.create_info_card(
                    "step_height.png",
                    "Altura",
                    (
                        f"{current_data['height']} cm"
                        if current_data["height"] != "Não informado"
                        else current_data["height"]
                    ),
                    index=3,
                    on_edit=lambda e: self.on_previous(e, step=1),
                ),
                self.create_info_card(
                    "step_gender.png",
                    "Gênero",
                    (
                        current_data["gender"].capitalize()
                        if current_data["gender"] != "Não informado"
                        else current_data["gender"]
                    ),
                    index=4,
                    on_edit=lambda e: self.on_previous(e, step=0),
                ),
                self.create_info_card(
                    "step_goal.png",
                    "Objetivo",
                    current_data["goal"],
                    index=5,
                    on_edit=lambda e: self.on_previous(e, step=2),
                ),
                self.create_info_card(
                    "step_restrict.png",
                    "Restrições",
                    current_data["restrictions"],
                    multiline=True,
                    index=6,
                    on_edit=lambda e: self.on_previous(e, step=2),
                ),
            ]
        ]
        self.page.update()
        logger.info(f"Review atualizada com dados: {current_data}")

    def on_previous(self, e, step=None):
        """Sobrescreve on_previous para suportar edição específica."""
        if step is not None:
            self.current_step[0] = step
            for index, s in enumerate(self.page.views[-1].controls[0].content.controls):
                s.view.visible = index == step
            self.page.update()
            logger.info(f"Voltou para a etapa {step} para edição")
        else:
            super().on_previous(e)

    def build_view(self) -> ft.Control:
        current_data = self.get_current_profile_data()
        self.cards_scroll = ft.ResponsiveRow(
            controls=[],
            spacing=15,
            run_spacing=15,
            alignment=ft.MainAxisAlignment.CENTER,
        )
        self.update_review_data()

        cards_container = ft.Container(
            content=ft.Column([self.cards_scroll], scroll=ft.ScrollMode.AUTO),
            height=300,
            padding=ft.padding.all(20),
        )

        header = ft.ResponsiveRow(
            [
                ft.Column(
                    controls=[
                        ft.Container(
                            content=ft.Image(
                                src="mascote_supafit/robo_apontando.png",
                                fit=ft.ImageFit.CONTAIN,
                                width=100,
                                height=100,
                            ),
                            alignment=ft.alignment.center,
                        )
                    ],
                    col={"xs": 12, "sm": 4},
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Column(
                    controls=[
                        ft.Text(
                            "Pronto para dominar seus treinos?",
                            style=ft.TextThemeStyle.TITLE_LARGE,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.ElevatedButton(
                            text="Gerar Treino Personalizado",
                            icon=ft.Icons.FITNESS_CENTER,
                            style=ft.ButtonStyle(
                                bgcolor=ft.Colors.PRIMARY,
                                color=ft.Colors.WHITE,
                                shape=ft.RoundedRectangleBorder(radius=25),
                                padding=ft.padding.symmetric(
                                    horizontal=30, vertical=15
                                ),
                            ),
                            on_click=self.on_create,
                            animate_scale=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
                        ),
                    ],
                    spacing=16,
                    col={"xs": 12, "sm": 8},
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
            ],
            spacing=20,
            run_spacing=20,
            alignment=ft.MainAxisAlignment.CENTER,
        )

        try:
            weight = (
                float(current_data["weight"])
                if current_data["weight"] != "Não informado"
                else 0
            )
            height = (
                float(current_data["height"])
                if current_data["height"] != "Não informado"
                else 0
            )
            bmi = weight / ((height / 100) ** 2) if weight > 0 and height > 0 else 0
        except (ValueError, TypeError):
            bmi = 0

        stats_container = ft.Container(
            content=ft.Row(
                [
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Text(
                                    "BMI",
                                    style=ft.TextThemeStyle.TITLE_SMALL,
                                    color=ft.Colors.PRIMARY,
                                    weight=ft.FontWeight.BOLD,
                                ),
                                ft.Text(
                                    f"{bmi:.1f}" if bmi > 0 else "N/A",
                                    style=ft.TextThemeStyle.HEADLINE_SMALL,
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=5,
                        ),
                        padding=20,
                        border_radius=10,
                        border=ft.border.all(1, "#333333"),
                        expand=True,
                    ),
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Text(
                                    "Status",
                                    style=ft.TextThemeStyle.TITLE_SMALL,
                                    color=ft.Colors.PRIMARY,
                                    weight=ft.FontWeight.BOLD,
                                ),
                                ft.Text(
                                    "Ativo",
                                    style=ft.TextThemeStyle.HEADLINE_SMALL,
                                    color="#00FF88",
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=5,
                        ),
                        padding=20,
                        border_radius=10,
                        border=ft.border.all(1, "#333333"),
                        expand=True,
                    ),
                ],
                spacing=20,
            ),
            padding=ft.padding.symmetric(horizontal=20, vertical=10),
        )

        footer = ft.Container(
            content=ft.Column(
                [
                    ft.Divider(height=1),
                    ft.Row(
                        [
                            ft.Text(
                                "© 2025 SupaFit", style=ft.TextThemeStyle.BODY_SMALL
                            ),
                            ft.Text(
                                "Feito com ❤️ para seu fitness",
                                style=ft.TextThemeStyle.BODY_SMALL,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                ],
                spacing=10,
            ),
            padding=ft.padding.all(20),
        )

        return ft.Column(
            [
                self.build_step_progress(),
                header,
                stats_container,
                cards_container,
                footer,
                ft.Row(
                    [
                        ft.ElevatedButton("Voltar", on_click=self.on_previous),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=10,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=24,
        )

    def validate(self) -> bool:
        current_data = self.get_current_profile_data()
        if any(
            value == "Não informado"
            for key, value in current_data.items()
            if key != "restrictions"
        ):
            self.page.open(
                ft.SnackBar(
                    ft.Text("Por favor, preencha todos os campos obrigatórios.")
                )
            )
            self.page.update()
            logger.warning("Campos obrigatórios não preenchidos na revisão")
            return False
        logger.info("Validate StepReview chamada - todos os campos preenchidos")
        return True
