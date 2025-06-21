import flet as ft
from .base_step import BaseStep
from utils.logger import get_logger

logger = get_logger("supabafit.profile_user.step6_review")


class Step6Review(BaseStep):
    """Etapa 6: Revisão dos dados do perfil.

    Herda de BaseStep e implementa a interface para revisão e criação do perfil.
    """

    def __init__(
        self,
        page: ft.Page,
        profile_data: dict,
        current_step: list,
        on_next,
        on_previous,
        supabase_service,
        on_create,
    ):
        """Inicializa a etapa de revisão do perfil.

        Args:
            page (ft.Page): Página Flet para interação com o usuário.
            profile_data (dict): Dados do perfil coletados.
            current_step (list): Lista com a etapa atual.
            on_next (callable): Função para avançar para a próxima etapa.
            on_previous (callable): Função para voltar para a etapa anterior.
            supabase_service: Serviço Supabase para operações de banco de dados.
            on_create (callable): Função para criar o perfil.
        """
        self.supabase_service = supabase_service
        self.on_create = on_create
        self.review_text = ft.Markdown("")
        super().__init__(page, profile_data, current_step, on_next, on_previous)
        logger.info("Step6Review inicializado com sucesso.")

    def build_view(self) -> ft.Control:
        """Constrói a interface para a etapa de revisão.

        Returns:
            ft.Column: Coluna com título, imagem, texto de revisão e botões.
        """
        return ft.Column(
            [
                ft.Text("Revisão", size=20, weight=ft.FontWeight.BOLD),
                ft.Image(src="mascote_supafit/step6.png", width=100, height=100),
                self.review_text,
                ft.Row(
                    [
                        ft.ElevatedButton("Voltar", on_click=self.on_previous),
                        ft.ElevatedButton("Criar Perfil", on_click=self.on_create),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def validate(self) -> bool:
        """Valida os dados revisados (sempre válido, pois é apenas revisão).

        Returns:
            bool: True, pois a revisão não requer validação adicional.
        """
        return True

    def update_review(self):
        """Atualiza o texto de revisão com os dados do perfil."""
        review_content = f"""
        **Revise seus dados:**  
        **Nome:** {self.profile_data.get("name", "Não informado")}  
        **Idade:** {self.profile_data.get("age", "Não informado")}  
        **Peso:** {self.profile_data.get("weight", "Não informado")} kg  
        **Altura:** {self.profile_data.get("height", "Não informado")} cm  
        **Objetivo:** {self.profile_data.get("goal", "Não informado")}
        """
        self.review_text.value = review_content
        if self.review_text.page:
            self.review_text.update()
            logger.info("Conteúdo de revisão atualizado.")
        else:
            logger.debug(
                "update_review chamado, mas review_text ainda não está na página."
            )
