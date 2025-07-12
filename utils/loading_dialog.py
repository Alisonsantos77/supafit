import flet as ft
import asyncio
from utils.logger import get_logger

logger = get_logger("supafit.components.loading_dialog")


class LoadingDialog:
    """Componente reutilizável para exibir diálogos de carregamento."""

    def __init__(self, page: ft.Page):
        self.page = page
        self.dialog = None

    async def show(self, message: str = "Carregando..."):
        """
        Exibe o diálogo de carregamento.

        Args:
            message (str): Mensagem a ser exibida no diálogo

        Returns:
            ft.AlertDialog: Instância do diálogo criado
        """
        try:
            # Verificar se já existe um diálogo aberto
            if (
                hasattr(self.page, "dialog")
                and self.page.dialog
                and self.page.dialog.open
            ):
                logger.info("Diálogo de carregamento já exibido, ignorando")
                return self.page.dialog

            self.dialog = ft.AlertDialog(
                content=ft.Container(
                    content=ft.Column(
                        [
                            ft.ProgressRing(color=ft.Colors.BLUE_400),
                            ft.Text(message, size=16, text_align=ft.TextAlign.CENTER),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    alignment=ft.alignment.center,
                    width=200,
                    height=100,
                ),
                bgcolor=ft.Colors.TRANSPARENT,
                modal=True,
                disabled=True,
            )

            self.page.dialog = self.dialog
            self.dialog.open = True
            self.page.update()

            # Pequena pausa para garantir que o diálogo seja renderizado
            await asyncio.sleep(0.1)

            logger.info(f"Diálogo de carregamento exibido: {message}")
            return self.dialog
        except Exception as e:
            logger.error(f"Erro ao exibir diálogo de carregamento: {str(e)}")
            return None

    async def hide(self):
        """
        Oculta o diálogo de carregamento atual.
        """
        try:
            if self.dialog and hasattr(self.dialog, "open") and self.dialog.open:
                self.dialog.open = False
                self.page.dialog = None
                self.page.update()
                logger.info("Diálogo de carregamento fechado")
            elif hasattr(self.page, "dialog") and self.page.dialog:
                if hasattr(self.page.dialog, "open") and self.page.dialog.open:
                    self.page.dialog.open = False
                self.page.dialog = None
                self.page.update()
                logger.info("Diálogo de carregamento da página fechado")

            # Pequena pausa para garantir que o diálogo seja removido
            await asyncio.sleep(0.1)
        except Exception as e:
            logger.error(f"Erro ao ocultar diálogo de carregamento: {str(e)}")

    async def update_message(self, new_message: str):
        """
        Atualiza a mensagem do diálogo de carregamento atual.

        Args:
            new_message (str): Nova mensagem a ser exibida
        """
        try:
            if self.dialog and hasattr(self.dialog, "open") and self.dialog.open:
                # Encontra o componente de texto e atualiza
                text_component = self.dialog.content.content.controls[1]
                text_component.value = new_message
                self.page.update()

                # Pequena pausa para garantir que a atualização seja renderizada
                await asyncio.sleep(0.1)

                logger.info(f"Mensagem do diálogo atualizada: {new_message}")
        except Exception as e:
            logger.error(f"Erro ao atualizar mensagem do diálogo: {str(e)}")

    async def show_with_steps(self, steps: list[str], current_step: int = 0):
        """
        Exibe o diálogo com indicador de progresso por etapas.

        Args:
            steps (list[str]): Lista de etapas
            current_step (int): Índice da etapa atual (0-based)
        """
        try:
            if not steps:
                return await self.show()

            # Verificar se já existe um diálogo aberto
            if (
                hasattr(self.page, "dialog")
                and self.page.dialog
                and getattr(self.page.dialog, "open", False)
            ):
                logger.info("Diálogo de carregamento já exibido, atualizando etapas")
                return await self.update_step(steps, current_step)

            progress_value = (current_step + 1) / len(steps)
            current_message = (
                steps[current_step] if current_step < len(steps) else steps[-1]
            )

            self.dialog = ft.AlertDialog(
                content=ft.Container(
                    content=ft.Column(
                        [
                            ft.ProgressBar(
                                value=progress_value,
                                color=ft.Colors.BLUE_400,
                                bgcolor=ft.Colors.GREY_300,
                                height=8,
                            ),
                            ft.Text(
                                f"Etapa {current_step + 1} de {len(steps)}",
                                size=12,
                                text_align=ft.TextAlign.CENTER,
                                color=ft.Colors.GREY_600,
                            ),
                            ft.Text(
                                current_message,
                                size=16,
                                text_align=ft.TextAlign.CENTER,
                                weight=ft.FontWeight.W_500,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10,
                    ),
                    alignment=ft.alignment.center,
                    width=250,
                    height=120,
                ),
                bgcolor=ft.Colors.TRANSPARENT,
                modal=True,
                disabled=True,
            )

            self.page.dialog = self.dialog
            self.dialog.open = True
            self.page.update()

            # Pequena pausa para garantir que o diálogo seja renderizado
            await asyncio.sleep(0.1)

            logger.info(
                f"Diálogo de carregamento com etapas exibido: {current_message}"
            )
            return self.dialog
        except Exception as e:
            logger.error(f"Erro ao exibir diálogo com etapas: {str(e)}")
            return None

    async def update_step(self, steps: list[str], current_step: int):
        """
        Atualiza o progresso das etapas no diálogo atual.

        Args:
            steps (list[str]): Lista de etapas
            current_step (int): Índice da etapa atual (0-based)
        """
        try:
            if not self.dialog or not getattr(self.dialog, "open", False) or not steps:
                return

            progress_value = (current_step + 1) / len(steps)
            current_message = (
                steps[current_step] if current_step < len(steps) else steps[-1]
            )

            # Atualiza os componentes
            column = self.dialog.content.content
            if len(column.controls) >= 3:
                progress_bar = column.controls[0]
                step_text = column.controls[1]
                message_text = column.controls[2]

                progress_bar.value = progress_value
                step_text.value = f"Etapa {current_step + 1} de {len(steps)}"
                message_text.value = current_message

                self.page.update()

                # Pequena pausa para garantir que a atualização seja renderizada
                await asyncio.sleep(0.1)

                logger.info(
                    f"Progresso atualizado - Etapa {current_step + 1}: {current_message}"
                )
        except Exception as e:
            logger.error(f"Erro ao atualizar progresso: {str(e)}")


# Funções auxiliares para compatibilidade com código existente
async def show_loading(page: ft.Page, message: str = "Carregando..."):
    """
    Função auxiliar para mostrar loading (compatibilidade com código existente).

    Args:
        page (ft.Page): Página do Flet
        message (str): Mensagem a ser exibida

    Returns:
        ft.AlertDialog: Instância do diálogo criado
    """
    loading = LoadingDialog(page)
    return await loading.show(message)


async def hide_loading(page: ft.Page, dialog=None):
    """
    Função auxiliar para ocultar loading (compatibilidade com código existente).

    Args:
        page (ft.Page): Página do Flet
        dialog: Diálogo a ser fechado (opcional)
    """
    try:
        if dialog and hasattr(dialog, "open") and dialog.open:
            dialog.open = False
            page.dialog = None
            page.update()
        elif hasattr(page, "dialog") and page.dialog:
            if hasattr(page.dialog, "open") and page.dialog.open:
                page.dialog.open = False
            page.dialog = None
            page.update()

        # Pequena pausa para garantir que o diálogo seja removido
        await asyncio.sleep(0.1)
    except Exception as e:
        logger.error(f"Erro ao ocultar loading: {str(e)}")


# Funções síncronas para compatibilidade com código antigo
def show_loading_sync(page: ft.Page, message: str = "Carregando..."):
    """Versão síncrona para compatibilidade"""
    loading = LoadingDialog(page)
    return asyncio.create_task(loading.show(message))


def hide_loading_sync(page: ft.Page, dialog=None):
    """Versão síncrona para compatibilidade"""
    return asyncio.create_task(hide_loading(page, dialog))
