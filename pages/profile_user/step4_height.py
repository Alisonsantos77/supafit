import flet as ft
from .base_step import BaseStep, logger


class Step4Height(BaseStep):
    """Etapa 4: Coleta da altura do usuário.

    Herda de BaseStep e implementa a interface e validação para o campo de altura.
    """

    def __init__(
        self,
        page: ft.Page,
        profile_data: dict,
        current_step: list,
        on_next,
        on_previous,
    ):
        """Inicializa a etapa de coleta de altura.

        Args:
            page (ft.Page): Página Flet para interação com o usuário.
            profile_data (dict): Dados do perfil coletados.
            current_step (list): Lista com a etapa atual.
            on_next (callable): Função para avançar para a próxima etapa.
            on_previous (callable): Função para voltar para a etapa anterior.
        """
        self.height_input = ft.TextField(
            label="Altura (cm)",
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
        logger.info("Step4Height inicializado com sucesso.")

    def build_view(self) -> ft.Control:
        """Constrói a interface para a etapa de altura.

        Returns:
            ft.Column: Coluna com título, campo de entrada e botões.
        """
        return ft.Column(
            [
                ft.Text("Etapa 4 de 5: Altura", size=20, weight=ft.FontWeight.BOLD),
                self.height_input,
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
        """Valida o campo de altura.

        Returns:
            bool: True se a altura é válida, False caso contrário.
        """
        height = self.height_input.value.strip()
        try:
            height = float(height)
            if height < 100 or height > 250:
                self.height_input.error_text = "Insira uma altura válida (100-250 cm)."
                self.height_input.update()
                self.show_snackbar("Insira uma altura válida (100-250 cm).")
                logger.warning("Altura inválida.")
                return False
        except ValueError:
            self.height_input.error_text = "Insira um número válido."
            self.height_input.update()
            self.show_snackbar("Insira um número válido para a altura.")
            logger.warning("Altura não é um número.")
            return False
        self.height_input.error_text = None
        self.profile_data["height"] = int(height)
        logger.info(f"Altura coletada: {height}")
        return True
