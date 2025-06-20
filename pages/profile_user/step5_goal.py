import flet as ft
from .base_step import BaseStep, logger


class Step5Goal(BaseStep):
    """Etapa 5: Coleta do objetivo do usuário.

    Herda de BaseStep e implementa a interface e validação para a seleção de objetivo.
    """

    def __init__(
        self,
        page: ft.Page,
        profile_data: dict,
        current_step: list,
        on_next,
        on_previous,
    ):
        """Inicializa a etapa de coleta de objetivo.

        Args:
            page (ft.Page): Página Flet para interação com o usuário.
            profile_data (dict): Dados do perfil coletados.
            current_step (list): Lista com a etapa atual.
            on_next (callable): Função para avançar para a próxima etapa.
            on_previous (callable): Função para voltar para a etapa anterior.
        """
        self.goal_radio_group = ft.RadioGroup(
            content=ft.Row(
                [
                    ft.Radio(value="Perder peso", label="Perder peso"),
                    ft.Radio(value="Ganhar massa", label="Ganhar massa"),
                    ft.Radio(value="Manter forma", label="Manter forma"),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            value="Manter forma",
        )
        super().__init__(page, profile_data, current_step, on_next, on_previous)
        logger.info("Step5Goal inicializado com sucesso.")

    def build_view(self) -> ft.Control:
        """Constrói a interface para a etapa de objetivo.

        Returns:
            ft.Column: Coluna com título, grupo de opções e botões.
        """
        return ft.Column(
            [
                ft.Text("Etapa 5 de 5: Objetivo", size=20, weight=ft.FontWeight.BOLD),
                self.goal_radio_group,
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
        """Valida a seleção de objetivo.

        Returns:
            bool: True se um objetivo foi selecionado, False caso contrário.
        """
        self.profile_data["goal"] = self.goal_radio_group.value
        logger.info(f"Objetivo coletado: {self.profile_data['goal']}")
        return True
