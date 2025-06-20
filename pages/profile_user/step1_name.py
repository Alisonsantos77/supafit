import flet as ft
from .base_step import BaseStep, logger


class Step1Name(BaseStep):
    """Etapa 1: Coleta do nome do usuário.

    Herda de BaseStep e implementa a interface e validação para o campo de nome.
    """

    def __init__(
        self,
        page: ft.Page,
        profile_data: dict,
        current_step: list,
        on_next,
        on_previous,
    ):
        """Inicializa a etapa de coleta de nome.

        Args:
            page (ft.Page): Página Flet para interação com o usuário.
            profile_data (dict): Dados do perfil coletados.
            current_step (list): Lista com a etapa atual.
            on_next (callable): Função para avançar para a próxima etapa.
            on_previous (callable): Função para voltar para a etapa anterior.
        """
        self.name_input = ft.TextField(
            label="Nome",
            width=320,
            border="underline",
            filled=True,
            bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.BLUE_GREY),
            border_color=ft.Colors.BLUE_600,
            focused_border_color=ft.Colors.BLUE_400,
            cursor_color=ft.Colors.BLUE_400,
            text_size=16,
        )
        super().__init__(page, profile_data, current_step, on_next, on_previous)
        logger.info("Step1Name inicializado com sucesso.")

    def build_view(self) -> ft.Control:
        """Constrói a interface para a etapa de nome.

        Returns:
            ft.Column: Coluna com título, campo de entrada e botão.
        """
        return ft.Column(
            [
                ft.Text("Etapa 1 de 5: Nome", size=20, weight=ft.FontWeight.BOLD),
                self.name_input,
                ft.Row(
                    [ft.ElevatedButton("Próximo", on_click=self.on_next)],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def validate(self) -> bool:
        """Valida o campo de nome.

        Returns:
            bool: True se o nome é válido, False caso contrário.
        """
        name = self.name_input.value.strip()
        if not name:
            self.name_input.error_text = "Por favor, insira seu nome."
            self.name_input.update()
            self.show_snackbar("Por favor, insira seu nome.")
            logger.warning("Nome não preenchido.")
            return False
        self.name_input.error_text = None
        self.profile_data["name"] = name
        logger.info(f"Nome coletado: {name}")
        return True
