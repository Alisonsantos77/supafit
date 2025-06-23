import flet as ft
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger("supafit.profile_user.base_step")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


class BaseStep(ABC):
    """Classe base abstrata para as etapas do processo de criação de perfil.

    Attributes:
        page (ft.Page): Página Flet para interação com o usuário.
        profile_data (dict): Dados do perfil coletados.
        current_step (list): Lista com um único inteiro representando a etapa atual.
        on_next (callable): Função chamada ao avançar para a próxima etapa.
        on_previous (callable): Função chamada ao voltar para a etapa anterior.
    """

    def __init__(
        self,
        page: ft.Page,
        profile_data: dict,
        current_step: list,
        on_next,
        on_previous,
    ):
        """Inicializa a etapa base.

        Args:
            page (ft.Page): Página Flet para interação com o usuário.
            profile_data (dict): Dados do perfil coletados.
            current_step (list): Lista com a etapa atual.
            on_next (callable): Função para avançar para a próxima etapa.
            on_previous (callable): Função para voltar para a etapa anterior.
        """
        self.page = page
        self.profile_data = profile_data
        self.current_step = current_step
        self.on_next = on_next
        self.on_previous = on_previous
        self.view = self.build_view()
        logger.info(f"Inicializando etapa {self.__class__.__name__}")

    @abstractmethod
    def build_view(self) -> ft.Control:
        """Constrói a interface da etapa.

        Returns:
            ft.Control: Componente Flet representando a interface da etapa.
        """
        pass

    @abstractmethod
    def validate(self) -> bool:
        """Valida os dados inseridos na etapa.

        Returns:
            bool: True se os dados são válidos, False caso contrário.
        """
        pass