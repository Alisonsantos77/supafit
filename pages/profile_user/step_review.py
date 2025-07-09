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
        self.supabase_service = supabase_service
        self.cards_scroll = ft.ResponsiveRow(
            controls=[],
            spacing=15,
            run_spacing=15,
            alignment=ft.MainAxisAlignment.CENTER,
        )

        super().__init__(
            page, profile_data, current_step, on_next, on_previous, on_create
        )
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
                    animate_scale=ft.Animation(300, ft.AnimationCurve.EASE_IN_OUT),
                    scale=1.2 if is_current else 1.0,
                )
            )
        return ft.Row(steps, alignment=ft.MainAxisAlignment.CENTER, spacing=10)

    botao_edit = ft.Ref[ft.IconButton]()

    def create_info_card(
        self, icon_path, title, content, multiline=False, index=0, on_edit=None
    ):
        img = ft.Image(
            src=f"mascote_supafit/{icon_path}",
            width=70,
            height=70,
            border_radius=10,
            animate_scale=ft.Animation(300, ft.AnimationCurve.EASE_IN_OUT),
            scale=1.0,
        )
        text_title = ft.Text(
            title, theme_style=ft.TextThemeStyle.TITLE_MEDIUM, weight=ft.FontWeight.BOLD
        )
        text_control = ft.Text(
            str(content),
            theme_style=ft.TextThemeStyle.BODY_MEDIUM,
            max_lines=4 if multiline else 1,
            overflow=ft.TextOverflow.ELLIPSIS,
        )
        edit_button = ft.IconButton(
            icon=ft.Icons.EDIT,
            tooltip=f"Editar {title.lower()}",
            on_click=on_edit,
            visible=bool(on_edit),
            ref=self.botao_edit
        )
        card = ft.Container(
            content=ft.Row(
                [
                    img,
                    ft.Column([text_title, text_control], expand=True, spacing=5),
                    edit_button,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                spacing=10,
            ),
            padding=20,
            margin=10,
            border_radius=15,
            border=ft.border.all(1, ft.Colors.PRIMARY),
            animate=ft.Animation(200, ft.AnimationCurve.EASE_IN_OUT),
            scale=1.0,
        )

        def on_hover(e):
            if e.data == "true":
                card.scale = 1.03
                card.bgcolor = ft.Colors.PRIMARY
                edit_button.icon_color = ft.Colors.WHITE
                card.shadow = ft.BoxShadow(
                    blur_radius=10, color=ft.Colors.PRIMARY, offset=ft.Offset(0, 4)
                )
                img.scale = 1.1
            else:
                card.scale = 1.0
                card.shadow = ft.BoxShadow(
                    blur_radius=10, color=ft.Colors.PRIMARY, offset=ft.Offset(0, 2)
                )
                img.scale = 1.0
            card.update()
            img.update()

        card.on_hover = on_hover
        return card

    def get_current_profile_data(self):
        data = {
            "name": self.profile_data.get("name", "Não informado"),
            "age": self.profile_data.get("age", "Não informado"),
            "weight": self.profile_data.get("weight", "Não informado"),
            "height": self.profile_data.get("height", "Não informado"),
            "gender": self.profile_data.get("gender", "Não informado"),
            "goal": self.profile_data.get("goal", "Não informado"),
            "restrictions": self.profile_data.get("restrictions", "Nenhuma"),
        }
        return data

    def update_review_data(self):
        data = self.get_current_profile_data()
        cards_def = [
            ("step_name.png", "Nome de usuário", data["name"], False, 0),
            (
                "step_age.png",
                "Idade",
                (
                    f"{data['age']} anos"
                    if data["age"] != "Não informado"
                    else data["age"]
                ),
                False,
                0,
            ),
            (
                "step_weight.png",
                "Peso",
                (
                    f"{data['weight']} kg"
                    if data["weight"] != "Não informado"
                    else data["weight"]
                ),
                False,
                1,
            ),
            (
                "step_height.png",
                "Altura",
                (
                    f"{data['height']} cm"
                    if data["height"] != "Não informado"
                    else data["height"]
                ),
                False,
                1,
            ),
            (
                "step_gender.png",
                "Gênero",
                (
                    data["gender"].capitalize()
                    if data["gender"] != "Não informado"
                    else data["gender"]
                ),
                False,
                0,
            ),
            ("step_goal.png", "Objetivo", data["goal"], False, 2),
            ("step_restrict.png", "Restrições", data["restrictions"], True, 2),
        ]

        card_controls = []
        for idx, (icon, title, content, multiline, step) in enumerate(cards_def):
            card = self.create_info_card(
                icon,
                title,
                content,
                multiline,
                idx,
                on_edit=lambda e, s=step: self.on_previous(e, step=s),
            )
            card_controls.append(
                ft.Column(col={"xs": 12, "sm": 6, "md": 4, "lg": 3}, controls=[card])
            )

        self.cards_scroll.controls = card_controls
        self.page.update()

    def build_view(self):
        header = ft.ResponsiveRow(
            [
                ft.Column(
                    controls=[
                        ft.Image(
                            src="mascote_supafit/robo_apontando.png",
                            width=100,
                            height=100,
                        )
                    ],
                    col={"xs": 12, "sm": 4},
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Column(
                    controls=[
                        ft.Text(
                            "Pronto para dominar seus treinos?",
                            theme_style=ft.TextThemeStyle.TITLE_LARGE,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.ElevatedButton(
                            "Gerar Treino Personalizado",
                            icon=ft.Icons.FITNESS_CENTER,
                            on_click=self.on_create,
                        ),
                    ],
                    col={"xs": 12, "sm": 8},
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
            ],
            spacing=20,
            run_spacing=20,
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        self.update_review_data()

        return ft.Column(
            [
                self.build_step_progress(),
                header,
                ft.Container(
                    content=ft.Column([self.cards_scroll], scroll=ft.ScrollMode.AUTO),
                    height=300,
                ),
                ft.Row(
                    [ft.ElevatedButton("Voltar", on_click=self.on_previous)],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=20,
        )

    def validate(self):
        d = self.get_current_profile_data()
        if any(d[k] == "Não informado" for k in d if k != "restrictions"):
            self.page.snack_bar = ft.SnackBar(
                ft.Text("Preencha todos os campos obrigatórios.")
            )
            self.page.snack_bar.open = True
            self.page.update()
            return False
        return True
