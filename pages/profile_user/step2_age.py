import flet as ft
from .base_step import BaseStep, logger


class Step2Age(BaseStep):
    """Etapa 2: Coleta da idade do usuário.

    Herda de BaseStep e implementa a interface e validação para o campo de idade.
    """

    def __init__(
        self,
        page: ft.Page,
        profile_data: dict,
        current_step: list,
        on_next,
        on_previous,
    ):
        """Inicializa a etapa de coleta de idade.

        Args:
            page (ft.Page): Página Flet para interação com o usuário.
            profile_data (dict): Dados do perfil coletados.
            current_step (list): Lista com a etapa atual.
            on_next (callable): Função para avançar para a próxima etapa.
            on_previous (callable): Função para voltar para a etapa anterior.
        """
        self.age_input = ft.TextField(
            label="Idade",
            width=320,
            border="underline",
            filled=True,
            bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.BLUE_GREY),
            border_color=ft.Colors.BLUE_600,
            focused_border_color=ft.Colors.BLUE_400,
            cursor_color=ft.Colors.BLUE_400,
            text_size=16,
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        super().__init__(page, profile_data, current_step, on_next, on_previous)
        logger.info("Step2Age inicializado com sucesso.")

    def build_view(self) -> ft.Control:
        """Constrói a interface para a etapa de idade.

        Returns:
            ft.Column: Coluna com título, campo de entrada e botões.
        """
        return ft.Column(
            [
                ft.Text("Etapa 2 de 5: Idade", size=20, weight=ft.FontWeight.BOLD),
                self.age_input,
                ft.Row(
                    [
                        ft.ElevatedButton("Voltar", on_click=self.on_previous),
                        ft.ElevatedButton("Próximo", on_click=self.on_next),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def validate(self) -> bool:
        """Valida o campo de idade.

        Returns:
            bool: True se a idade é válida, False caso contrário.
        """
        age = self.age_input.value.strip()
        if not age or not age.isdigit() or int(age) < 10 or int(age) > 100:
            self.age_input.error_text = "Insira uma idade válida (10-100)."
            self.age_input.update()
            self.show_snackbar("Insira uma idade válida (10-100).")
            logger.warning("Idade inválida.")
            return False
        self.age_input.error_text = None
        self.profile_data["age"] = int(age)
        logger.info(f"Idade coletada: {age}")
        return True
