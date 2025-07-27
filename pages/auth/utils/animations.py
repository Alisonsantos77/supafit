"""
Utilitários de animações para SupaFit
Mantém consistência visual em toda a aplicação
"""

import flet as ft
from time import sleep
from typing import Callable, Optional


class AnimationPresets:
    """Presets de animações padronizadas para a aplicação"""

    # Durações padrões (em milissegundos)
    FAST = 200
    NORMAL = 300
    SLOW = 500
    VERY_SLOW = 800

    # Curvas de animação comuns
    EASE_IN = ft.AnimationCurve.EASE_IN
    EASE_OUT = ft.AnimationCurve.EASE_OUT
    EASE_IN_OUT = ft.AnimationCurve.EASE_IN_OUT
    BOUNCE = ft.AnimationCurve.BOUNCE_OUT
    ELASTIC = ft.AnimationCurve.ELASTIC_OUT

    @classmethod
    def fade_in(cls, duration: int = NORMAL) -> ft.Animation:
        """Animação de fade in suave"""
        return ft.Animation(duration, cls.EASE_OUT)

    @classmethod
    def fade_out(cls, duration: int = NORMAL) -> ft.Animation:
        """Animação de fade out suave"""
        return ft.Animation(duration, cls.EASE_IN)

    @classmethod
    def slide_in(cls, duration: int = NORMAL) -> ft.Animation:
        """Animação de slide in com bounce suave"""
        return ft.Animation(duration, cls.EASE_OUT)

    @classmethod
    def bounce_in(cls, duration: int = SLOW) -> ft.Animation:
        """Animação com efeito bounce"""
        return ft.Animation(duration, cls.BOUNCE)

    @classmethod
    def elastic_in(cls, duration: int = VERY_SLOW) -> ft.Animation:
        """Animação com efeito elástico"""
        return ft.Animation(duration, cls.ELASTIC)

    @classmethod
    def button_hover(cls) -> ft.Animation:
        """Animação padrão para hover de botões"""
        return ft.Animation(cls.FAST, cls.EASE_IN_OUT)


class AnimationHelpers:
    """Helpers para aplicar animações comuns"""

    @staticmethod
    def animate_container_entry(
        container: ft.Container,
        page: ft.Page,
        delay: float = 0.1,
        duration: int = AnimationPresets.SLOW,
    ):
        """
        Anima a entrada de um container com fade in

        Args:
            container: Container a ser animado
            page: Página do Flet
            delay: Delay antes da animação
            duration: Duração da animação
        """
        container.opacity = 0
        container.animate_opacity = AnimationPresets.fade_in(duration)
        page.update()

        if delay > 0:
            sleep(delay)

        container.opacity = 1
        page.update()

    @staticmethod
    def animate_form_error(field: ft.TextField, page: ft.Page):
        """
        Anima um campo com erro (shake effect simulado)

        Args:
            field: Campo de texto com erro
            page: Página do Flet
        """
        original_color = field.border_color
        field.border_color = ft.Colors.RED_400
        field.animate_opacity = AnimationPresets.fade_in(AnimationPresets.FAST)

        # Simular shake com opacity
        for _ in range(3):
            field.opacity = 0.7
            page.update()
            sleep(0.05)
            field.opacity = 1.0
            page.update()
            sleep(0.05)

        # Restaurar cor original após 2 segundos
        def restore_color():
            sleep(2)
            field.border_color = original_color
            page.update()

        import threading

        threading.Thread(target=restore_color, daemon=True).start()

    @staticmethod
    def animate_button_click(button: ft.ElevatedButton, page: ft.Page):
        """
        Anima clique do botão com efeito de escala

        Args:
            button: Botão a ser animado
            page: Página do Flet
        """
        original_elevation = (
            button.style.elevation.get("", 5)
            if button.style and button.style.elevation
            else 5
        )

        # Efeito de "press"
        if not button.style:
            button.style = ft.ButtonStyle()
        button.style.elevation = {"": 2}
        page.update()
        sleep(0.1)

        # Retornar ao normal
        button.style.elevation = {"": original_elevation}
        page.update()

    @staticmethod
    def animate_success_feedback(element: ft.Control, page: ft.Page):
        """
        Anima feedback de sucesso com cor verde temporária

        Args:
            element: Elemento a ser animado
            page: Página do Flet
        """
        if hasattr(element, "bgcolor"):
            original_bg = element.bgcolor
            element.bgcolor = ft.Colors.GREEN_100
            element.animate_opacity = AnimationPresets.fade_in(AnimationPresets.NORMAL)
            page.update()

            # Restaurar cor original
            def restore_bg():
                sleep(1)
                element.bgcolor = original_bg
                page.update()

            import threading

            threading.Thread(target=restore_bg, daemon=True).start()

    @staticmethod
    def animate_loading_dots(text_element: ft.Text, page: ft.Page, stop_event=None):
        """
        Anima texto com pontos de carregamento (Loading...)

        Args:
            text_element: Elemento de texto a ser animado
            page: Página do Flet
            stop_event: Evento para parar a animação
        """
        base_text = text_element.value.rstrip(".")
        dots = ["", ".", "..", "..."]

        def animate():
            i = 0
            while stop_event is None or not stop_event.is_set():
                text_element.value = base_text + dots[i % len(dots)]
                page.update()
                sleep(0.5)
                i += 1

        import threading

        thread = threading.Thread(target=animate, daemon=True)
        thread.start()
        return thread

    @staticmethod
    def animate_progress_bar(
        progress_bar: ft.ProgressBar,
        page: ft.Page,
        target_value: float = 1.0,
        duration: float = 2.0,
    ):
        """
        Anima uma barra de progresso até um valor específico

        Args:
            progress_bar: Barra de progresso a ser animada
            page: Página do Flet
            target_value: Valor final (0.0 a 1.0)
            duration: Duração total da animação em segundos
        """
        steps = 50
        step_value = target_value / steps
        step_delay = duration / steps

        def animate():
            current_value = 0.0
            for _ in range(steps):
                current_value += step_value
                progress_bar.value = min(current_value, target_value)
                page.update()
                sleep(step_delay)

        import threading

        threading.Thread(target=animate, daemon=True).start()


class SnackbarAnimations:
    """Animações específicas para Snackbars"""

    @staticmethod
    def show_animated_snackbar(
        page: ft.Page,
        message: str,
        color: str = "green",
        duration: int = 3000,
        icon: Optional[ft.Icons] = None,
    ):
        """
        Exibe snackbar com animação suave

        Args:
            page: Página do Flet
            message: Mensagem a ser exibida
            color: Cor do snackbar (green, red, orange, blue)
            duration: Duração em milissegundos
            icon: Ícone opcional
        """
        color_map = {
            "green": ft.Colors.GREEN_400,
            "red": ft.Colors.RED_400,
            "orange": ft.Colors.ORANGE_400,
            "blue": ft.Colors.BLUE_400,
            "purple": ft.Colors.PURPLE_400,
        }

        content = (
            ft.Row(
                [
                    ft.Icon(icon, color=ft.Colors.WHITE, size=20) if icon else None,
                    ft.Text(message, color=ft.Colors.WHITE, weight=ft.FontWeight.W_500),
                ],
                spacing=8,
            )
            if icon
            else ft.Text(message, color=ft.Colors.WHITE, weight=ft.FontWeight.W_500)
        )

        snackbar = ft.SnackBar(
            content=content,
            bgcolor=color_map.get(color, ft.Colors.BLUE_400),
            duration=duration,
            behavior=ft.SnackBarBehavior.FLOATING,
            action="OK",
            action_color=ft.Colors.WHITE,
            show_close_icon=True,
            margin=ft.Margin(10, 10, 10, 10),
            padding=ft.Padding(16, 12, 16, 12),
            elevation=8,
        )

        # CORREÇÃO: Usar page.snack_bar e page.open() ao invés de show_snack_bar()
        page.snack_bar = snackbar
        page.open(snackbar)
        page.update()


class DialogAnimations:
    """Animações para diálogos"""

    @staticmethod
    def create_loading_dialog(message: str = "Carregando...") -> ft.AlertDialog:
        """
        Cria diálogo de carregamento animado

        Args:
            message: Mensagem de carregamento

        Returns:
            AlertDialog: Diálogo configurado
        """
        return ft.AlertDialog(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.ProgressRing(
                            color=ft.Colors.BLUE_400,
                            width=50,
                            height=50,
                            stroke_width=4,
                        ),
                        ft.Text(
                            message,
                            text_align=ft.TextAlign.CENTER,
                            color=ft.Colors.WHITE,
                            weight=ft.FontWeight.BOLD,
                            size=16,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=20,
                ),
                alignment=ft.alignment.center,
                padding=40,
            ),
            bgcolor=ft.Colors.with_opacity(0.95, ft.Colors.GREY_900),
            modal=True,
            shape=ft.RoundedRectangleBorder(radius=20),
        )

    @staticmethod
    def create_success_dialog(title: str, message: str) -> ft.AlertDialog:
        """
        Cria diálogo de sucesso animado

        Args:
            title: Título do diálogo
            message: Mensagem de sucesso

        Returns:
            AlertDialog: Diálogo configurado
        """
        return ft.AlertDialog(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(
                            ft.Icons.CHECK_CIRCLE, size=80, color=ft.Colors.GREEN_400
                        ),
                        ft.Text(
                            title,
                            size=20,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.WHITE,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Text(
                            message,
                            size=14,
                            color=ft.Colors.GREY_300,
                            text_align=ft.TextAlign.CENTER,
                            italic=True,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=20,
                ),
                alignment=ft.alignment.center,
                padding=40,
            ),
            bgcolor=ft.Colors.with_opacity(0.95, ft.Colors.GREY_900),
            modal=True,
            shape=ft.RoundedRectangleBorder(radius=20),
        )

    @staticmethod
    def show_dialog_with_animation(page: ft.Page, dialog: ft.AlertDialog):
        """
        Exibe diálogo com animação de entrada

        Args:
            page: Página do Flet
            dialog: Diálogo a ser exibido
        """
        dialog.content.opacity = 0
        dialog.content.animate_opacity = AnimationPresets.fade_in(AnimationPresets.SLOW)

        page.dialog = dialog
        page.open(dialog)
        page.update()

        # Animar entrada
        sleep(0.1)
        dialog.content.opacity = 1
        page.update()


# Exemplo de uso das animações
class AnimationExamples:
    """Exemplos de como usar as animações"""

    @staticmethod
    def example_form_validation_animation(page: ft.Page, field: ft.TextField):
        """Exemplo de animação de validação de formulário"""
        # Simular erro
        AnimationHelpers.animate_form_error(field, page)

        # Mostrar snackbar de erro
        SnackbarAnimations.show_animated_snackbar(
            page, "Campo obrigatório!", "red", icon=ft.Icons.ERROR
        )

    @staticmethod
    def example_success_flow(page: ft.Page, container: ft.Container):
        """Exemplo de fluxo de sucesso completo"""
        # Animar feedback de sucesso
        AnimationHelpers.animate_success_feedback(container, page)

        # Mostrar snackbar de sucesso
        SnackbarAnimations.show_animated_snackbar(
            page, "Operação realizada com sucesso!", "green", icon=ft.Icons.CHECK_CIRCLE
        )
